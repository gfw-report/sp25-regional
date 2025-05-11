package main

import (
	"crypto/tls"
	"crypto/x509"
	"encoding/csv"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/url"
	"os"
	"runtime"
	"runtime/pprof"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"

	"common/parseipportargs"
	"common/readfiles"

	"golang.org/x/net/proxy"
)

func usage() {
	fmt.Fprintf(os.Stderr, `Usage:
    %[1]s [OPTION]... [FILE]...

Description:
    Test if SNI values in FILE(s) are censored. With no FILE, or when FILE is -, read standard input. By default, print results to stdout and log to stderr.

Examples:
    Make a TLS connection, whose SNI is www.youtube.com, to the port 1000 of 1.1.1.1
	echo "www.youtube.com" | %[1]s -dip 1.1.1.1 -p 1000
    Make TLS connections, whose SNIs are in domains_1.txt and domains_2.txt. Each connection uses one of the port 1000, 2000, 2001, and 2002 of 1.1.1.1 and 2.2.2.2
	%[1]s -dip 1.1.1.1,2.2.2.2 -p 1000,2000-2002 domains_1.txt domains_2.txt
    Do not flush after every output, to be more efficient in long run. Usually used in a script.
	%[1]s -flush=false -dip 1.1.1.1,2.2.2.2 -p 1000,2000-2002 domains_1.txt domains_2.txt

Options:
`, os.Args[0])
	flag.PrintDefaults()
}

func worker(id int, jobs chan string, addrs chan string, results chan<- []string, dialer *proxy.Dialer, ws []chan int) {
	state := Paused // Begin in the paused state.

	// for j := range jobs {
	// 	// skip empty domain names
	// 	if len(j) == 0 {
	// 		continue
	// 	}

	for {
		select {
		case state = <-ws[id]:
			switch state {
			case Stopped:
				log.Printf("Worker %d: Stopped\n", id)
				return
			case Running:
				log.Printf("Worker %d: Running\n", id)
			case Paused:
				log.Printf("Worker %d: Paused\n", id)
			}

		default:
			// We use runtime.Gosched() to prevent a deadlock in this case.
			// It will not be needed of work is performed here which yields
			// to the scheduler.
			runtime.Gosched()

			if state == Paused {
				break
			}

			j, ok := <-jobs
			if !ok {
				log.Println("Jobs is closed, returning worker", id)
				return
			}
			if len(j) == 0 {
				continue
			}

			log.Println("worker", id, "got the job:", j)

			// Do actual work here.
			var stage string
			var code string
			var addr string
			var startTime time.Time
			for addr = range addrs {
				startTime = time.Now()
				reuseAddr := true
				delay := 0 * time.Second
				// TCP handshake
				stage = "TCP"
				conn, err := (*dialer).Dial("tcp", addr)
				if err != nil {
					code := checkError(err)
					log.Println(addr, stage, code)
					if code == "Timeout" {
						// TCP handshake timeout usually indicates congestion.
						// It is better to lower down maxNumWorkers to avoid congestion in the first place.

						// TODO: Implementing a good congestion control is not easy.
						// The current approach that stops sending probes to one port of a host
						// may not effectively mitigate a congestion,
						// especially when a server opens a huge number of ports.
						// We want to stop sending probes to *all* ports of a host for a few seconds,
						// when a non trivial number of TCP handshakes timeout.
						delay = 30 * time.Second
					} else if code == "Refused" {
						// do not use this closed ip:port anymore
						// by not adding it back to the addrs pool
						reuseAddr = false
						log.Println("Closed ip:port detected:", addr, "The program will not use it again.")
					} else if code == "EOF" {
						log.Println("TCP,EOF")
					} else if code == "UNREACHABLE" {
						log.Println("TCP,UNREACHABLE")
						// TODO: when unreachable, should stop using the IP, not just a port
						// time.Sleep(5 * time.Second)
						delay = 30 * time.Second
						// reuseAddr = false
					}
					go func(a string, reuse bool, d time.Duration) {
						time.Sleep(d)
						if reuse {
							addrs <- a
						}
					}(addr, reuseAddr, delay)
					continue
				}

				// TLS Handshake
				// hello(conn, j) should return codeesult, err
				// err is any case where it is not TLS,Timeout or TLS,RST
				stage = "TLS"
				success := false
				err = hello(conn, j)
				if err != nil {
					code = checkError(err)
				} else {
					code = "Success"
					log.Println("TLS handshake has completed. Unless this request was sent to the actual TLS server, this shouldn't happen.", addr, j)
				}
				if code == "Timeout" {
					success = true
				} else if code == "RST" {
					// When resodual censorship happens, the GFW may send forged SYN/ACK to SYN or forged RST.
					// Prior work observed that the residual censorship could be 120s or 180s,
					// or sometimes no residual censorship at all.
					// We thus use the maximum observed residual censorship.
					success = true
					delay = *residual
				} else if code == "Success" {
					// as long as it's not TLS Timeout or TLS RST, or TLS Success, we need to retest
					success = true
				} else if code == "TLSRecordHeaderError" || code == "X509HostnameError" {
					// do not use a non-sink port
					success = false
					reuseAddr = false
				} else if code == "EOF" {
					success = true

					eofErrorsLock.Lock()
					now := time.Now()
					// Add the current timestamp
					eofErrorsTimestamps = append(eofErrorsTimestamps, now)
					// Keep only the last 10 timestamps
					if len(eofErrorsTimestamps) > 10 {
						eofErrorsTimestamps = eofErrorsTimestamps[len(eofErrorsTimestamps)-10:]
					}

					// Check for 10 EOFs within 100ms
					if len(eofErrorsTimestamps) == 10 && eofErrorsTimestamps[9].Sub(eofErrorsTimestamps[0]) <= 100*time.Millisecond {
						go func() {
							log.Println("Pausing workers...")
							setState(ws, Paused)
							pauseDuration := 120 * time.Second
							time.AfterFunc(pauseDuration, func() {
								log.Println("Resuming workers")
								setState(ws, Running)
							})
						}()
					}

					eofErrorsLock.Unlock()

				} else {
					success = false
				}
				go func(a string, d time.Duration) {
					time.Sleep(d)
					if reuseAddr {
						addrs <- a
					}
				}(addr, delay)

				if success {
					break
				}
			}

			// only a successful test reaches below
			endTime := time.Now()
			duration := endTime.Sub(startTime)
			durationMillis := duration.Milliseconds()

			results <- []string{strconv.FormatInt(startTime.UnixMilli(), 10), j, stage, code, addr, fmt.Sprintf("%v", durationMillis)}
			log.Println("worker", id, "finished sending", j, "to", addr)

		}
	}

}

// global variables
var cpuprofile = flag.String("cpuprofile", "", "write cpu profile to file.")
var timeout = flag.Duration("timeout", 3*time.Second, "timeout value of TLS connections.")
var residual = flag.Duration("residual", 180*time.Second, "redisual censorship duration of the GFW.")

var eofErrorsLock sync.Mutex
var eofErrorsTimestamps []time.Time = make([]time.Time, 0)

// Possible worker states.
const (
	Stopped = 0
	Paused  = 1
	Running = 2
)

func main() {
	flag.Usage = usage
	var maxNumWorkers int
	argIP := flag.String("dip", "127.0.0.1", "comma-separated list of destination IP addresses to which the program sends TLS ClientHellos. eg. 1.1.1.1,2.2.2.2")
	argPort := flag.String("p", "10000-65000", "comma-separated list of ports to which the program sends TLS ClientHellos. eg. 3000,4000-4002")
	flag.IntVar(&maxNumWorkers, "worker", 10000*2, fmt.Sprintf("number of workers in parallel."))
	outputFile := flag.String("out", "", "output csv file.  (default stdout)")
	logFile := flag.String("log", "", "log to file.  (default stderr)")
	flush := flag.Bool("flush", true, "flush after every output.")
	socksProxy := flag.String("socksProxy", "", "SOCKS5 proxy address. Format: host:port")

	flag.Parse()

	// log, intentionally make it blocking to make sure it got
	// initiliazed before other parts using it
	if *logFile != "" {
		f, err := os.Create(*logFile)
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
		f, err = os.Create(*outputFile)
		if err != nil {
			log.Panicln("failed to open output file", err)
		}
	}
	defer f.Close()
	w := csv.NewWriter(f)

	if *cpuprofile != "" {
		f, err := os.Create(*cpuprofile)
		if err != nil {
			log.Panicln(err)
		}
		pprof.StartCPUProfile(f)
		defer pprof.StopCPUProfile()
	}

	ips, err := parseipportargs.ParseIPArgs(*argIP)
	if err != nil {
		log.Panic(err)
	}

	ports, err := parseipportargs.ParsePortArgs(*argPort)
	if err != nil {
		log.Panic(err)
	}
	maxNumAddrs := len(ports) * len(ips)
	addrs := make(chan string, maxNumAddrs)

	// The channel capacity does not have to be equal to the
	// number of workers. It can be much smaller.
	jobs := make(chan string, 100)
	results := make(chan []string, 100)

	lines := readfiles.ReadFiles(flag.Args())

	go func() {
		for line := range lines {
			jobs <- line
		}
		close(jobs)
	}()

	go func() {
		for _, port := range ports {
			// Create a pool of ip-port pairs to which we send ClientHellos.
			// It is important to loop port then ip, to send to different servers evenly.
			for _, ip := range ips {
				addrs <- net.JoinHostPort(ip.String(), strconv.Itoa(port))
			}
		}
		// do not close(addrs) as we still need to pop and push
	}()

	baseDialer := &net.Dialer{
		Timeout: *timeout,
	}

	var dialer proxy.Dialer = baseDialer // Use proxy.Dialer as the common interface

	if *socksProxy != "" {
		prox, _ := url.Parse(*socksProxy)

		// dialer, err = proxy.SOCKS5("tcp", *socksProxy, nil, proxy.Direct)
		dialer, err = proxy.FromURL(prox, proxy.Direct)
		if err != nil {
			log.Fatalf("Failed to create SOCKS4 dialer: %v", err)
		}
	}

	var wg sync.WaitGroup
	wg.Add(maxNumWorkers + 1)

	workers := make([]chan int, maxNumWorkers)

	for i := 0; i < maxNumWorkers; i++ {
		workers[i] = make(chan int, 1)

		go func(id int) {
			defer wg.Done()
			worker(id, jobs, addrs, results, &dialer, workers)
		}(i)
	}

	// Launch controller routine.
	go func() {
		controller(workers)
		wg.Done()
	}()

	go func() {
		wg.Wait()
		close(results)
	}()
	for r := range results {
		// comment out to measure and decide a proper capacity of the chan
		// log.Println("Number of Element in results chan:", len(results))
		if err := w.Write(r); err != nil {
			log.Panicln("error writing results to file", err)
		}
		if *flush {
			w.Flush()
		}
	}
	w.Flush()
}

func hello(conn net.Conn, sni string) error {
	conf := &tls.Config{
		ServerName: sni,
	}
	connt := tls.Client(conn, conf)

	err := connt.SetDeadline(time.Now().Add(*timeout))
	if err != nil {
		log.Println("SetDeadline failed: ", err)
	}
	err = connt.Handshake()
	if conn != nil {
		buff := make([]byte, 10)
		var length int
		for {
			log.Println("conn is not nil")

			length, err = io.ReadFull(conn, buff)

			if err != nil {
				log.Println(checkError(err))
				break
			}

			log.Printf("Recv:  %v <-- %v: %q (%x), %v bytes\n", conn.LocalAddr(), conn.RemoteAddr(), string(buff[:length]), buff[:length], length)
		}
	}
	return err
}

type result struct {
	stage string
	code  string
}

func checkError(err error) string {
	code := ""
	if err != nil {
		switch t := err.(type) {
		case *net.OpError:
			if t.Op == "dial" {
				if t.Timeout() {
					code = "Timeout"
				} else if strings.Contains(err.Error(), "connect: connection refused") {
					code = "Refused"
				} else if strings.Contains(err.Error(), "socket: too many open files") {
					code = "TOOMANYFILES"
					// fail fast
					log.Panic(err)
				} else if strings.Contains(err.Error(), "connect: network is unreachable") {
					code = "UNREACHABLE"
				} else {
					code = "Unexpected"
					log.Println("Unexptected error when dial: ", err.Error())
				}
			} else if t.Op == "read" {
				if t.Timeout() {
					code = "Timeout"
				} else if strings.Contains(err.Error(), "read: connection reset by peer") {
					code = "RST"
				} else {
					code = "Unexpected"
					log.Println("Unexptected error when read: ", err.Error())
				}
			} else if t.Op == "socks connect" {
				code = "UNREACHABLE"
				log.Println("Unexpected error when socks dial: ", err.Error())
			}
		case syscall.Errno:
			if t == syscall.ECONNREFUSED {
				// log.Println(stage, "Connection refused")
				code = "Timeout"
			} else {
				code = "Unexpected"
				log.Println("Unexptected error when in syscall.Errono: ", err.Error())
			}
		case tls.RecordHeaderError:
			{
				// This could happen when the port is not a sink and reponds non-TLS data back
				code = "TLSRecordHeaderError"
				log.Println(fmt.Sprintf("Server responded non-TLS data: %T, %v", err, err.Error()))
			}
		case x509.HostnameError:
			{
				// This could happen when the port is not a sink and reponds a mismatched TLS certificate
				code = "X509HostnameError"
				log.Println(fmt.Sprintf("Server responded a mismatched TLS certificate: %T, %v", err, err.Error()))
			}
		default:
			// TODO: handle TCP,EOF
			if err.Error() == "EOF" || err.Error() == "unexpected EOF" {
				// TODO remove debugging info
				code = "EOF"
				log.Println(fmt.Sprintf("Finally I got you type: %v,%v,%T", t, err.Error(), err))
			} else {
				code = "Unexpected"
				log.Println(fmt.Sprintf("Unexptected error type: %v,%v,%T", t, err.Error(), err))
			}
		}
	}
	return code
}

// controller handles the current state of all workers. They can be
// instructed to be either running, paused or stopped entirely.
func controller(workers []chan int) {
	// Start workers
	setState(workers, Running)
}

// setState changes the state of all given workers.
func setState(workers []chan int, state int) {
	for _, w := range workers {
		w <- state
	}
}
