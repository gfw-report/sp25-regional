module parse-pcap-sni-rst

go 1.20

require github.com/google/gopacket v1.1.19

require common v1.0.0

require (
	golang.org/x/net v0.0.0-20190620200207-3b0461eec859 // indirect
	golang.org/x/sys v0.0.0-20190412213103-97732733099d // indirect
)

replace common => ../common
