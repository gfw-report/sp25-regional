package main

import (
	"common/readfiles"
	"encoding/binary"
	"encoding/csv"
	"encoding/hex"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"regexp"
	"strconv"
	"sync"

	"sync/atomic"

	"github.com/google/gopacket"
	"github.com/google/gopacket/layers"
	"github.com/google/gopacket/pcap"
)

func usage() {
	fmt.Fprintf(os.Stderr, `Usage:
    %[1]s [OPTION]... [FILE]...

Description:
    This program will read in pcap files, look for the SNI and corresponding RSTs in a connection. It will outoupt a CSV with sni,rst_fingerprint. With no FILE, or when FILE is -, read standard input.

Examples:
    Extract the leaked data in each pcap file under the current directory:
        %[1]s *.pcap

    Use -filter option to select only TLS packets or TCP packets with RST flag set (including RST, RST+ACK etc.):
        %[1]s -filter "(tcp[((tcp[12] & 0xf0) >> 2)] = 0x16) or (tcp[tcpflags] & tcp-rst != 0)" *.pcap

	Sometimes the gopacket library would fail to parse the pcap file, use tcpdump:
		tcpdump -r input.pcap -w - | %[1]s

	Sometimes the gopacket library would fail to parse the pcap file, use tshark to convert it to pcapng:

    Use tcpdump to capture live UDP packets on interface eth0:
        tcpdump -i eth0 "port 53" -w - | %[1]s

    When there are too many files that exceeds the maximum number of arguments for shell, do not use find or xargs as they will split the arguments into multiple commands and each command overwrites the previous output files. Instead, let the program handle the globbing by quoting the glob pattern:
		%[1]s "*.pcap"

Options:
`, os.Args[0])
	flag.PrintDefaults()
}

// Define a struct for the 4-tuple
type FourTuple struct {
	IP1   string // Lower IP
	Port1 int    // Port associated with lower IP
	IP2   string // Higher IP
	Port2 int    // Port associated with higher IP
}

// Define a struct for packet details
type PacketDetail struct {
	Timestamp string
	Flag      string
	SNI       string // This field is optional
	Payload   []byte // This field is optional
	Delta     int64  // This field is optional
}

// Function to create a normalized 4-tuple
func NewFourTuple(srcIP string, srcPort int, dstIP string, dstPort int) FourTuple {
	if srcIP > dstIP || (srcIP == dstIP && srcPort > dstPort) {
		return FourTuple{dstIP, dstPort, srcIP, srcPort}
	}
	return FourTuple{srcIP, srcPort, dstIP, dstPort}
}

func getFiveTuple(packet gopacket.Packet) (net.IP, net.IP, int, int, bool) {
	// Extract IP layer information
	ipLayer := packet.Layer(layers.LayerTypeIPv4)

	if ipLayer != nil {
		ip, _ := ipLayer.(*layers.IPv4)
		// Extract TCP layer information
		tcpLayer := packet.Layer(layers.LayerTypeTCP)
		if tcpLayer != nil {
			tcp, _ := tcpLayer.(*layers.TCP)
			return ip.SrcIP, ip.DstIP, int(tcp.SrcPort), int(tcp.DstPort), tcp.RST
		}
	}

	return nil, nil, 0, 0, false
}

func getSNI(packet gopacket.Packet) (sni string) {
	// Extract TLS information and specifically the SNI
	tcpLayer := packet.Layer(layers.LayerTypeTCP)

	if tcpLayer != nil {
		tcp, ok := tcpLayer.(*layers.TCP)
		if !ok {
			log.Println("Error decoding TCP layer")
			return ""
		}
		payload := tcp.Payload
		if len(payload) > 0 {
			sni := extractSNI(payload)
			if sni != "" {
				return sni
			}

		} else {
			log.Printf("TCP packet from %s to %s has no payload\n", tcp.SrcPort, tcp.DstPort)
		}
	}

	return ""
}

func extractSNI(tls []byte) string {

	if len(tls) == 0 || tls[0] != 0x16 {
		return ""
	}

	hsType := tls[5]
	if hsType != 0x01 {
		return ""
	}

	// chelloLength := int(tls[6])<<16 | int(tls[7])<<8 | int(tls[8])
	// chelloVersion := binary.BigEndian.Uint16(tls[9:11])
	offset := 11 + 32 // Skip random bytes

	// Session ID
	sessIDLen := int(tls[offset])
	offset += 1 + sessIDLen

	// Cipher Suites
	csLen := int(binary.BigEndian.Uint16(tls[offset : offset+2]))
	offset += 2 + csLen

	// Compression
	compLen := int(tls[offset])
	offset += 1 + compLen

	// Extensions
	extLen := int(binary.BigEndian.Uint16(tls[offset : offset+2]))
	offset += 2
	end := offset + extLen
	sniHost := ""

	for offset < end {
		extType := binary.BigEndian.Uint16(tls[offset : offset+2])
		offset += 2
		extLength := int(binary.BigEndian.Uint16(tls[offset : offset+2]))
		offset += 2

		if extType == 0x0000 {
			// sniLen := int(binary.BigEndian.Uint16(tls[offset : offset+2]))
			// sniType := tls[offset+2]
			sniLen2 := int(binary.BigEndian.Uint16(tls[offset+3 : offset+5]))
			sniHost = string(tls[offset+5 : offset+5+sniLen2])
		}

		offset += extLength
	}
	return sniHost
}

// processPackets processes packets in a pcap file. Files matching the BPFFilter will be processed by
// more functions and write to the corresponding channel (identified by the index of slice).
//
// It returns the number of packets processed (post-BPF) and the number of packets successfully matched (post-regex).
func processPackets(file *os.File, filter *string, chanResults []chan<- []string) (totalPackets, matchedPackets uint64) {
	filename := file.Name()

	sessions := make(map[FourTuple][]gopacket.Packet)

	log.Println("Started parsing:", filename)

	// There is a weird bug in gopacket, where OpenOfflineFile would fail to parse the pcap file,
	handle, err := pcap.OpenOffline(filename)
	if err != nil {
		log.Println("Failed to open pcap file:", err)
		return
	}
	defer handle.Close()

	err = handle.SetBPFFilter(*filter)
	if err != nil {
		log.Panicln("Failed set BPFFilter:", err)
	}

	// Use the handle as a packet source to process all packets
	packetSource := gopacket.NewPacketSource(handle, handle.LinkType())

	for {
		packet, err := packetSource.NextPacket()

		if err == io.EOF {
			break
		} else if err != nil {
			log.Println("Error while reading packet", filename, ":", err, "number of packets read from the pcap before error:", totalPackets)
			break
		}
		totalPackets++

		tcpLayer := packet.Layer(layers.LayerTypeTCP)
		if tcpLayer == nil {
			log.Println("Not a TCP packet:", filename)
			continue
		}
		tcp, _ := tcpLayer.(*layers.TCP)
		if tcp == nil {
			log.Println("ss")
		}

		srcIP, dstIP, srcPort, dstPort, rst := getFiveTuple(packet)
		// log.Println("srcIP:", srcIP, "dstIP:", dstIP, "srcPort:", srcPort, "dstPort:", dstPort, "rst:", rst)
		if srcIP == nil || dstIP == nil {
			log.Println("Failed to get five tuple:", filename)
			continue
		}
		key := NewFourTuple(srcIP.String(), srcPort, dstIP.String(), dstPort)

		if !rst {
			if _, ok := sessions[key]; !ok {
				sessions[key] = make([]gopacket.Packet, 0)
			}
			// Assuming there are only ClientHellos and RSTs in the pcap file
			sessions[key] = append(sessions[key], packet)
		}

		// Write the SNI, RST fingerprint to the output file once the first RST is received. Ignore the later RSTs.
		if rst {
			if _, ok := sessions[key]; !ok {
				// log.Println("RST packet without clientHello packets or not the first reset", filename)
				continue
			}
			sni := getSNI(sessions[key][0])
			delta := strconv.FormatFloat(packet.Metadata().Timestamp.Sub(sessions[key][0].Metadata().Timestamp).Seconds(), 'f', -1, 64)
			payload := hex.EncodeToString(packet.Layer(layers.LayerTypeTCP).LayerPayload())
			ipid := strconv.Itoa(int(packet.Layer(layers.LayerTypeIPv4).(*layers.IPv4).Id))
			ttl := strconv.Itoa(int(packet.Layer(layers.LayerTypeIPv4).(*layers.IPv4).TTL))
			flags := packet.Layer(layers.LayerTypeIPv4).(*layers.IPv4).Flags.String()

			to_write := []string{sni, delta, payload, ipid, ttl, flags}
			chanResults[0] <- to_write

			delete(sessions, key)
			continue
		}

	}

	log.Println("Finished parsing:", filename)
	return 0, 0
}

func worker(fileChan chan *os.File, filter *string, regexps []*regexp.Regexp, chanResults [](chan<- []string)) {
	// println("filech", fileChan)
	for file := range fileChan {
		total, matched := processPackets(file, filter, chanResults)
		// change to update count per file instead so faster without losing ability to check progress
		incrementTotalPackets(total)
		incrementMatchedPackets(matched)
	}
	log.Println("Finished worker, totalPackets:", totalPackets.Load(), "matchedPackets:", matchedPackets.Load())
}

// X: use atomic operations/types rather than mutex protected non-atomic operations
//
// But why use global counters instead of let each worker report after finishing?
var totalPackets *atomic.Uint64 = new(atomic.Uint64)
var matchedPackets *atomic.Uint64 = new(atomic.Uint64)

func incrementTotalPackets(cnt uint64) {
	totalPackets.Add(cnt)
}

func incrementMatchedPackets(cnt uint64) {
	matchedPackets.Add(cnt)
}

func main() {
	flag.Usage = usage
	filter := flag.String("filter", "", "BPF filter syntax.")
	workers := flag.Int("workers", 1, "Number of workers to use")
	outputFile := flag.String("out", "", "output csv file.  (default stdout)")
	logFile := flag.String("log", "", "log to file.  (default stderr)")

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

	var regexps []*regexp.Regexp = make([]*regexp.Regexp, 0)
	var outputFiles []*os.File = make([]*os.File, 0)

	// output
	if len(outputFiles) == 0 {
		if *outputFile == "" {
			outputFiles = []*os.File{os.Stdout}
		} else {
			// f, err = os.Create(*outputFile)
			f, err := os.OpenFile(*outputFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
			if err != nil {
				log.Panicln("failed to open output file", err)
			}
			outputFiles = []*os.File{f}
		}
		defer outputFiles[0].Close()
	}

	chanResults := make([]chan []string, 1)
	for i := range chanResults {
		chanResults[i] = make(chan []string, 100)
	}

	// X: maybe unnecessary, but I will just minimize the change
	chanResultsWriteOnly := make([]chan<- []string, 1)
	for i := range chanResultsWriteOnly {
		chanResultsWriteOnly[i] = chanResults[i]
	}

	files := readfiles.GetFiles(flag.Args())
	log.Println("Total files:", len(files))

	var wgPacketFilter *sync.WaitGroup = new(sync.WaitGroup) // in case copy needed
	// Worker model implementation
	fileChan := make(chan *os.File, len(files))
	for i := 0; i < *workers; i++ {
		wgPacketFilter.Add(1)
		go func() {
			defer wgPacketFilter.Done()
			worker(fileChan, filter, regexps, chanResultsWriteOnly)
		}()
	}

	// X: use this goroutine to write to outputFiles instead.
	var wgOutput *sync.WaitGroup = new(sync.WaitGroup) // in case copy needed
	wgOutput.Add(1)
	go func() {
		defer wgOutput.Done()
		// output
		for idx, f := range outputFiles {
			// Create a pcapgo Writer
			w := csv.NewWriter(f)
			// Write the file header
			err := w.Write([]string{"sni", "delta", "payload", "ip_id", "ttl", "ip_flags"})
			if err != nil {
				log.Fatal(err)
			}

			wgOutput.Add(1)
			go func(idx int, w *csv.Writer) {
				defer wgOutput.Done()

				var debugCntr int = 0
				for res := range chanResults[idx] {
					// Write the packet
					err = w.Write(res)
					if err != nil {
						log.Fatal(err)
					}
					debugCntr++
				}

				log.Println("Finished writing output file", idx, "with", debugCntr, "packets")
			}(idx, w)
		}
	}()

	// in main goroutine we don't do blocking work
	for _, file := range files {
		fileChan <- file
	}
	log.Println("Finished sending files to workers")
	close(fileChan)
	log.Println("Closed fileChan")

	wgPacketFilter.Wait()
	log.Println("All workers finished")
	for _, c := range chanResults {
		close(c)
	}
	log.Println("Closed results")

	wgOutput.Wait()
	log.Println("All output writer finished")

	log.Println("totalPackets:", totalPackets.Load())
	log.Println("matchedPackets:", matchedPackets.Load())
}
