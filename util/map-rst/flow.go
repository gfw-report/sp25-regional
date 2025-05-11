package main

import (
	"fmt"
)

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
}

// Function to create a normalized 4-tuple
func NewFourTuple(srcIP string, srcPort int, dstIP string, dstPort int) FourTuple {
	if srcIP > dstIP || (srcIP == dstIP && srcPort > dstPort) {
		return FourTuple{dstIP, dstPort, srcIP, srcPort}
	}
	return FourTuple{srcIP, srcPort, dstIP, dstPort}
}

func main() {
	// Map to store packets grouped by 4-tuple
	packetsByFourTuple := make(map[FourTuple][]PacketDetail)

	// Example packets (add your packets here)
	packetList := []struct {
		srcIP, dstIP, timestamp, flag, sni string
		srcPort, dstPort                   int
	}{
		{"192.168.1.1", "10.0.0.1", "2023-01-01T12:00:00", "SYN", "", 12345, 80},
		{"192.168.1.1", "10.0.0.1", "2023-01-01T12:00:00", "SYN", "", 12345, 80},
		{"10.0.0.1", "192.168.1.1", "2023-01-01T12:00:05", "ACK", "", 80, 12345},
		{"192.168.1.2", "10.0.0.2", "2023-01-01T12:01:00", "SYN", "www.example.com", 54321, 443},
		{"10.0.0.2", "192.168.1.2", "2023-01-01T12:01:05", "ACK", "", 443, 54321},
		{"192.168.1.2", "10.0.0.3", "2023-01-01T12:02:00", "SYN", "www.anotherexample.com", 54322, 443},

		// Add more packets here
	}

	// Group packets
	for _, p := range packetList {
		key := NewFourTuple(p.srcIP, p.srcPort, p.dstIP, p.dstPort)
		detail := PacketDetail{p.timestamp, p.flag, p.sni}
		packetsByFourTuple[key] = append(packetsByFourTuple[key], detail)
	}

	// Print the grouped packets (for demonstration)
	for key, packets := range packetsByFourTuple {
		fmt.Printf("4-Tuple: [%s:%d <-> %s:%d]\n", key.IP1, key.Port1, key.IP2, key.Port2)
		for _, packet := range packets {
			fmt.Printf("\tTimestamp: %s, Flag: %s, SNI: %s\n", packet.Timestamp, packet.Flag, packet.SNI)
		}
	}
}
