package main

import (
	"bytes"
	"common/readfiles"
	"encoding/hex"
	"flag"
	"fmt"
	"log"
	"os"
	"sync"

	"github.com/google/gopacket"
	"github.com/google/gopacket/layers"
	"github.com/google/gopacket/pcap"
	"github.com/google/gopacket/pcapgo"
)

func usage() {
	fmt.Fprintf(os.Stderr, `Usage:
    %[1]s [OPTION]... [FILE]...

Description:
    Extract specific DNS traffic contains specific patterns. With no FILE, or when FILE is -, read standard input.
	Ideally, tshark -Y "data contains 48:65:6c:6c:6f:57:6f:72:6c:64" -r input.pcap -w output.pcap should do the work;
	however, tshark would enable DNS dissector for port 53 (or other dissctors for other ports), making the data field empty as the data refers to any data that is not part of the higher layer protocols.

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
	needle := flag.String("needle", "48656c6c6f576f726c64", "Hex string of pattern as filter (default: 48656c6c6f576f726c64)")

	outputFile := flag.String("out", "", "output pcap file.  (default stdout)")
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
	defer f.Close()

	// convert hex string to byte array
	pattern, err := hex.DecodeString(*needle)
	if err != nil {
		log.Fatal(err)
	}

	results := make(chan gopacket.Packet, 100)
	var wg sync.WaitGroup
	wg.Add(1)
	// output
	go func(results chan gopacket.Packet) {
		defer wg.Done()
		// Create a pcapgo Writer
		w := pcapgo.NewWriter(f)
		// Write the file header
		err = w.WriteFileHeader(65536, layers.LinkTypeEthernet)
		if err != nil {
			log.Fatal(err)
		}
		for packet := range results {
			// Write the packet
			err = w.WritePacket(packet.Metadata().CaptureInfo, packet.Data())
			if err != nil {
				log.Fatal(err)
			}
		}
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
			udpPayload := getUdpPayload(packet)
			//log.Println("udpPayload:", udpPayload)
			if bytes.Contains(udpPayload, []byte(pattern)) {
				// save packet to file
				//log.Println("Found packet with payload contains", *needle, "in", filename)
				results <- packet
			}
		}
	}
	close(results)

	wg.Wait()
}
