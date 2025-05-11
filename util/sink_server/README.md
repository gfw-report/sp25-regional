
=== intro

**go version is significantly more efficient, compared to tcpserver:**

50% of a single core + 100 MB (300 - 200) is enough to handle 1 Million TCP connections per minute.

While the 100% of a single core + 1000 MB is enough to handle 0.3 MIllion TCP connections per minute

=== Run

```sh
ulimit -n 655350
./sink
```

=== firewall rules rationale

We need firewall rules to suppress outgoing RST.

This is because the program cannot guarantee not to send RSTs. As introduced in [this post](https://github.com/net4people/bbs/issues/26), "[i]f a user-space process closes a socket without draining the kernel socket buffer, the kernel sends a RST instead of a FIN".

The best a program can do is to try reading from buffer as fast and as possible; however, as long as the server actively close a connection, it is sometimes unavoidable that some bytes are still left in the buffer.

This is especially likely to happen when the client sends data to server at a very high speed. For example, the following example will cause the server to send a RST when timeout:

````sh
./sink -ip 0.0.0.0 -p 12345
```

```sh
nc -nv 127.0.0.1 12345 </dev/random
```

This is because, when the server timeout and calls close(), there is a chance the that more data has arrived at the server but haven't been read.

Even if we let the program read forever without timing out, there are still other cases where the server has to actively close the connection. For example, when a "too many open files" error occurs.

===

One command to setup a server:

```sh
./to_digitalocean.sh
```
