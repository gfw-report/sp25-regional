# snicensor

## Build

* build binary

```sh
make
```

* build docker images

```sh
make docker
```

## Intro

```sh
./snicensor -h
```

```txt
Usage:
    ./snicensor [OPTION]... [FILE]...

Description:
    Test if SNI values in FILE(s) are censored. With no FILE, or when FILE is -, read standard input. By default, print results to stdout and log to stderr.

Examples:
    Make a TLS connection, whose SNI is www.youtube.com, to the port 1000 of 1.1.1.1
	echo "www.youtube.com" | ./snicensor -dip 1.1.1.1 -p 1000
    Make TLS connections, whose SNIs are in domains_1.txt and domains_2.txt. Each connection uses one of the port 1000, 2000, 2001, and 2002 of 1.1.1.1 and 2.2.2.2
	./snicensor -dip 1.1.1.1,2.2.2.2 -p 1000,2000-2002 domains_1.txt domains_2.txt

Options:
  -cpuprofile string
    	write cpu profile to file.
  -dip string
    	comma-separated list of destination IP addresses to which the program sends TLS ClientHellos. eg. 1.1.1.1,2.2.2.2 (default "127.0.0.1")
  -log string
    	log to file.  (default stderr)
  -out string
    	output csv file.  (default stdout)
  -p string
    	comma-separated list of ports to which the program sends TLS ClientHellos. eg. 3000,4000-4002 (default "10000-65000")
  -residual duration
    	redisual censorship duration of the GFW. (default 3m0s)
  -timeout duration
    	timeout value of TLS connections. (default 3s)
  -worker int
    	number of workers in parallel. (default 20000)
```
