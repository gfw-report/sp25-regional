package main

import (
	"common/readfiles"
	"encoding/csv"
	"encoding/hex"
	"flag"
	"fmt"
	"log"
	"net"
	"os"
	"strconv"
	"sync"

	"github.com/google/gopacket"
	"github.com/google/gopacket/layers"
	"github.com/google/gopacket/pcap"
)

type pinfo struct {
	srcIP         net.IP
	udpPayload    []byte
	udpPayloadLen int
}

func usage() {
	fmt.Fprintf(os.Stderr, `Usage:
    %[1]s [OPTION]... [FILE]...

Description:
    This program reads pcap files and writes src IP, UDP payload, and the length of UDP payloads in CSV. With no FILE, or when FILE is -, read standard input.

Examples:
    Extract the leaked data in each pcap file under the current directory:
        %[1]s *.pcap

    Use -filter option to select packets whose src port is 53:
        %[1]s -filter "src port 53" *.pcap

    Use tcpdump to capture live UDP packets on interface eth0:
        tcpdump -i eth0 "port 53" -w - | %[1]s

Options:
`, os.Args[0])
	flag.PrintDefaults()
}

func getSrcIP(packet gopacket.Packet) (out net.IP) {
	ipLayer := packet.Layer(layers.LayerTypeIPv4)
	if ipLayer != nil {
		ip, _ := ipLayer.(*layers.IPv4)
		return ip.SrcIP
	}
	return
}

func getUdpPayload(packet gopacket.Packet) (out []byte) {
	udpLayer := packet.Layer(layers.LayerTypeUDP)
	if udpLayer != nil {
		udp, _ := udpLayer.(*layers.UDP)
		return udp.Payload
	}
	return
}

func main() {
	flag.Usage = usage
	filter := flag.String("filter", "", "BPF filter syntax.")
	outputFile := flag.String("out", "", "output csv file.  (default stdout)")
	logFile := flag.String("log", "", "log to file.  (default stderr)")
	flush := flag.Bool("flush", true, "flush after every output.")
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
	results := make(chan pinfo, 100)

	var wg sync.WaitGroup
	wg.Add(1)
	// output
	go func(results chan pinfo) {
		defer wg.Done()
		for r := range results {
			data := hex.EncodeToString(r.udpPayload)
			if err := w.Write([]string{
				r.srcIP.String(),
				data,
				strconv.Itoa(r.udpPayloadLen)}); err != nil {
				log.Panicln("error writing results to file:", err)
			}
			if *flush {
				w.Flush()
			}
		}
		w.Flush()
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

		// Use the handle as a packet source to process all packets
		packetSource := gopacket.NewPacketSource(handle, handle.LinkType())
		for packet := range packetSource.Packets() {
			srcIP := getSrcIP(packet)
			udpPayload := getUdpPayload(packet)
			if srcIP == nil || udpPayload == nil {
				continue
			}

			results <- pinfo{srcIP, udpPayload, len(udpPayload)}
		}
	}
	close(results)

	wg.Wait()
}
