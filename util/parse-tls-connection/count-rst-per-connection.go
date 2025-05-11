package main

import (
	"common/readfiles"
	"encoding/binary"
	"encoding/csv"
	"flag"
	"fmt"
	"log"
	"os"
	"strconv"
	"sync"

	"github.com/google/gopacket"
	"github.com/google/gopacket/layers"
	"github.com/google/gopacket/pcap"
)

func usage() {
	fmt.Fprintf(os.Stderr, `Usage:
    %[1]s [OPTION]... [FILE]...

Description:
    This program reads pcap files and writes the SNI in a connection and the number of RSTs received in total in CSV. With no FILE, or when FILE is -, read standard input.

Examples:
    Extract the leaked data in each pcap file under the current directory:
        %[1]s *.pcap

    Use -filter option to select packets whose src port is 53:
        %[1]s -filter "src port 53" *.pcap

    Use tcpdump to capture live UDP packets on interface eth0:
        tcpdump -i eth0 "port 53" -w - | %[1]s

Options:`, os.Args[0])
	flag.PrintDefaults()
}

type fourTuple struct {
	IP1, IP2     string
	Port1, Port2 string
}

func (c *fourTuple) normalize() {
	if c.IP1 > c.IP2 || (c.IP1 == c.IP2 && c.Port1 > c.Port2) {
		c.IP1, c.IP2 = c.IP2, c.IP1
		c.Port1, c.Port2 = c.Port2, c.Port1
	}
}

func (c fourTuple) Key() string {
	c.normalize()
	return c.IP1 + ":" + c.Port1 + "->" + c.IP2 + ":" + c.Port2
}

type connInfo struct {
	connTuple fourTuple
	sni       string
	rstCount  int
}

func NewConnectionInfo(ip1, ip2, port1, port2 string) *connInfo {
	t := fourTuple{
		IP1:   ip1,
		IP2:   ip2,
		Port1: port1,
		Port2: port2,
	}

	t.normalize()

	c := &connInfo{
		connTuple: t,
		sni:       "",
		rstCount:  0,
	}

	return c
}

func (c *connInfo) updateSNI(sniData string) {
	c.sni = sniData
}

func (c *connInfo) increaseRSTCount() {
	c.connTuple.normalize()
	c.rstCount++
}

func extractSNI(payload []byte) string {
	log.Println("extractSNI:", payload)

	// Check if payload length is at least 5 bytes (to check for handshake)
	if len(payload) < 5 {
		return ""
	}

	// Check for TLS handshake (0x16)
	if payload[0] != 0x16 {
		return ""
	}

	// Parse length of the handshake message
	length := binary.BigEndian.Uint16(payload[3:5])

	// Check if payload length is consistent with handshake message
	if len(payload) < int(length)+5 {
		return ""
	}

	// Check for ClientHello message (0x01)
	if payload[5] != 0x01 {
		return ""
	}

	// Get the session id length
	sessionIDLength := int(payload[43])

	// Calculate the start of the cipher suites section
	cipherSuitesStart := 44 + sessionIDLength

	// Get the length of the cipher suites
	cipherSuitesLength := binary.BigEndian.Uint16(payload[cipherSuitesStart : cipherSuitesStart+2])

	// Calculate the start of the compression methods section
	compressionMethodsStart := cipherSuitesStart + 2 + int(cipherSuitesLength)

	// Get the length of the compression methods
	compressionMethodsLength := int(payload[compressionMethodsStart])

	// Calculate the start of the extensions section
	extensionsStart := compressionMethodsStart + 1 + compressionMethodsLength

	// Parse each extension until we find the SNI (0x00, 0x00)
	for extensionsStart < len(payload)-4 {
		extensionType := payload[extensionsStart : extensionsStart+2]
		extensionLength := binary.BigEndian.Uint16(payload[extensionsStart+2 : extensionsStart+4])

		// Check if the extension is SNI
		if extensionType[0] == 0x00 && extensionType[1] == 0x00 {
			sniLength := binary.BigEndian.Uint16(payload[extensionsStart+7 : extensionsStart+9])
			return string(payload[extensionsStart+9 : extensionsStart+9+int(sniLength)])
		}

		// Move to the next extension
		extensionsStart += 4 + int(extensionLength)
	}

	return ""
}

func main() {
	flag.Usage = usage
	filter := flag.String("filter", "", "BPF filter syntax.")
	outputFile := flag.String("out", "", "output csv file.  (default stdout)")
	logFile := flag.String("log", "", "log to file.  (default stderr)")
	//flush := flag.Bool("flush", true, "flush after every output.")
	flag.Parse()

	// log, intentionally make it blocking to make sure it got
	// initiliazed before other parts using it
	if *logFile != "" {
		// f, err := os.Create()
		f, err := os.OpenFile(*logFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
		if err != nil {
			log.Panicln("failed to open log file", err)
		}
		defer f.Close()
		log.SetOutput(f)
	}

	// output
	var f *os.File
	var err error
	if *outputFile == "" {
		f = os.Stdout
	} else {
		// f, err = os.Create(*outputFile)
		f, err = os.OpenFile(*outputFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
		if err != nil {
			log.Panicln("failed to open output file", err)
		}
	}
	w := csv.NewWriter(f)

	connections := make(map[string]*connInfo)
	results := make(chan connInfo)

	var wg sync.WaitGroup
	wg.Add(1)

	go func(results chan connInfo) {
		defer wg.Done()
		for r := range results {
			if err := w.Write([]string{
				string(r.sni),
				strconv.Itoa(r.rstCount),
			}); err != nil {
				log.Println("error writing record to csv:", err)
				continue
			}
			w.Flush()
		}
		f.Close()
	}(results)

	files := readfiles.GetFiles(flag.Args())
	for _, file := range files {
		filename := file.Name()

		log.Println("Started parsing:", filename)

		handle, err := pcap.OpenOfflineFile(file)
		if err != nil {
			log.Println("Failed to open pcap file:", err)
			continue
		}
		defer handle.Close()

		err = handle.SetBPFFilter(*filter)
		if err != nil {
			log.Panicln("Failed set BPFFilter:", err)
		}

		packetSource := gopacket.NewPacketSource(handle, handle.LinkType())
		for packet := range packetSource.Packets() {
			netLayer := packet.NetworkLayer()
			transLayer := packet.TransportLayer()

			if netLayer != nil && transLayer != nil {
				srcIP, dstIP := netLayer.NetworkFlow().Endpoints()
				srcPort, dstPort := transLayer.TransportFlow().Endpoints()

				connTuple := fourTuple{
					IP1:   srcIP.String(),
					IP2:   dstIP.String(),
					Port1: srcPort.String(),
					Port2: dstPort.String(),
				}

				if _, exists := connections[connTuple.Key()]; !exists {
					connections[connTuple.Key()] = NewConnectionInfo(srcIP.String(), dstIP.String(), srcPort.String(), dstPort.String())
				}

				cInfo := connections[connTuple.Key()]

				tcpLayer := packet.Layer(layers.LayerTypeTCP)
				if tcpLayer != nil {
					tcp, ok := tcpLayer.(*layers.TCP)
					if !ok {
						fmt.Println("Error decoding TCP layer")
						continue
					}
					payload := tcp.Payload
					if len(payload) > 0 {
						fmt.Println("TCP payload found:", payload)
						sni := extractSNI(payload)
						if sni != "" {
							fmt.Println("Found SNI:", sni)
							cInfo.updateSNI(sni)
						}

					} else {
						fmt.Printf("TCP packet from %s to %s has no payload\n", tcp.SrcPort, tcp.DstPort)
					}
				}

				if tcpLayer, ok := transLayer.(*layers.TCP); ok && tcpLayer.RST {
					cInfo.increaseRSTCount()
				}

				fmt.Println("Finished parsing:", cInfo)
			}
		}

		// print out all connections
		for _, cInfo := range connections {
			results <- *cInfo
		}
		close(results)

		wg.Wait()
	}
}
