package main

import (
	"encoding/csv"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
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
)

func usage() {
	fmt.Fprintf(os.Stderr, `Usage:
        %[1]s [OPTION]... [FILE]...

    Description:
        Test if Host values in FILE(s) are censored by sending HTTP requests. With no FILE, or when FILE is -, read standard input. By default, print results to stdout and log to stderr.

    Examples:
        Make an HTTP request with Host header www.youtube.com to port 80 of 1.1.1.1
    	echo "www.youtube.com" | %[1]s -dip 1.1.1.1 -p 80
        Make HTTP requests with Host headers from domains_1.txt and domains_2.txt. Each request uses one of the ports 80, 8080 of 1.1.1.1 and 2.2.2.2
    	%[1]s -dip 1.1.1.1,2.2.2.2 -p 80,8080 domains_1.txt domains_2.txt
        Do not flush after every output, to be more efficient in long run. Usually used in a script.
    	%[1]s -flush=false -dip 1.1.1.1,2.2.2.2 -p 80,8080 domains_1.txt domains_2.txt

    Options:
    `, os.Args[0])
	flag.PrintDefaults()
}

func worker(id int, jobs chan string, addrs chan string, results chan<- []string, ws []chan int) {
	state := Paused // Begin in the paused state.

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
				conn, err := net.DialTimeout("tcp", addr, *timeout)
				if err != nil {
					code := checkError(err)
					log.Println(addr, stage, code)
					if code == "Timeout" {
						delay = 30 * time.Second
					} else if code == "Refused" {
						reuseAddr = false
						log.Println("Closed ip:port detected:", addr, "The program will not use it again.")
					} else if code == "EOF" {
						log.Println("TCP,EOF")
					} else if code == "UNREACHABLE" {
						log.Println("TCP,UNREACHABLE")
						delay = 30 * time.Second
					}
					go func(a string, reuse bool, d time.Duration) {
						time.Sleep(d)
						if reuse {
							addrs <- a
						}
					}(addr, reuseAddr, delay)
					continue
				}

				// HTTP Request
				stage = "HTTP"
				success := false
				err = hello(conn, j)
				if err != nil {
					code = checkError(err)
				} else {
					code = "Success"
					log.Println("HTTP request has completed. Unless this request was sent to the actual HTTP server, this shouldn't happen.", addr, j)
				}
				if code == "Timeout" {
					success = true
				} else if code == "RST" {
					success = true
					delay = *residual
				} else if code == "Success" {
					success = true
				} else if code == "EOF" {
					success = true

					eofErrorsLock.Lock()
					now := time.Now()
					eofErrorsTimestamps = append(eofErrorsTimestamps, now)
					if len(eofErrorsTimestamps) > 10 {
						eofErrorsTimestamps = eofErrorsTimestamps[len(eofErrorsTimestamps)-10:]
					}

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
var timeout = flag.Duration("timeout", 3*time.Second, "timeout value of HTTP connections.")
var residual = flag.Duration("residual", 180*time.Second, "residual censorship duration.")

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
	argIP := flag.String("dip", "127.0.0.1", "comma-separated list of destination IP addresses to which the program sends HTTP requests. e.g., 1.1.1.1,2.2.2.2")
	argPort := flag.String("p", "80", "comma-separated list of ports to which the program sends HTTP requests. e.g., 80,8080")
	flag.IntVar(&maxNumWorkers, "worker", 20000, fmt.Sprintf("number of workers in parallel."))
	outputFile := flag.String("out", "", "output CSV file. (default stdout)")
	logFile := flag.String("log", "", "log to file. (default stderr)")
	flush := flag.Bool("flush", true, "flush after every output.")

	flag.Parse()

	// Initialize logging
	if *logFile != "" {
		f, err := os.Create(*logFile)
		if err != nil {
			log.Panicln("failed to open log file", err)
		}
		defer f.Close()
		log.SetOutput(f)
	}

	// Output setup
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

	// The channel capacity does not have to be equal to the number of workers.
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
			// Create a pool of ip-port pairs to which we send HTTP requests.
			for _, ip := range ips {
				addrs <- net.JoinHostPort(ip.String(), strconv.Itoa(port))
			}
		}
		// Do not close(addrs) as we still need to pop and push
	}()

	var wg sync.WaitGroup
	wg.Add(maxNumWorkers + 1)

	workers := make([]chan int, maxNumWorkers)

	for i := 0; i < maxNumWorkers; i++ {
		workers[i] = make(chan int, 1)

		go func(id int) {
			defer wg.Done()
			worker(id, jobs, addrs, results, workers)
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
		if err := w.Write(r); err != nil {
			log.Panicln("error writing results to file", err)
		}
		if *flush {
			w.Flush()
		}
	}
	w.Flush()
}

func hello(conn net.Conn, host string) error {
	defer conn.Close()

	err := conn.SetDeadline(time.Now().Add(*timeout))
	if err != nil {
		log.Println("SetDeadline failed: ", err)
	}

	// Build the HTTP request
	request := fmt.Sprintf("GET / HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n", host)

	// Send the HTTP request
	_, err = conn.Write([]byte(request))
	if err != nil {
		return err
	}

	// Read the response
	buff := make([]byte, 4096)
	for {
		n, err := conn.Read(buff)
		if err != nil {
			if err == io.EOF {
				// Connection closed by server
				break
			}
			return err
		}
		// Optionally, process the response data
		log.Println(string(buff[:n]))
		_ = n
	}

	return nil
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
					log.Panic(err)
				} else if strings.Contains(err.Error(), "connect: network is unreachable") {
					code = "UNREACHABLE"
				} else {
					code = "Unexpected"
					log.Println("Unexpected error when dial: ", err.Error())
				}
			} else if t.Op == "read" {
				if t.Timeout() {
					code = "Timeout"
				} else if strings.Contains(err.Error(), "read: connection reset by peer") {
					code = "RST"
				} else {
					code = "Unexpected"
					log.Println("Unexpected error when read: ", err.Error())
				}
			}
		case syscall.Errno:
			if t == syscall.ECONNREFUSED {
				code = "Timeout"
			} else {
				code = "Unexpected"
				log.Println("Unexpected error in syscall.Errno: ", err.Error())
			}
		default:
			if err.Error() == "EOF" || err.Error() == "unexpected EOF" {
				code = "EOF"
			} else {
				code = "Unexpected"
				log.Println("Unexpected error type: ", t, err.Error(), err)
			}
		}
	}
	return code
}

// controller handles the current state of all workers. They can be
// instructed to be either running, paused, or stopped entirely.
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
