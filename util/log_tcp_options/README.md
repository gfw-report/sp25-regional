# TLS Logger

Demonstrates logging TLS handshakes to a file.

### Build and run
```
cargo build --release --bin log_tcp_options
sudo env LD_LIBRARY_PATH=$LD_LIBRARY_PATH RUST_LOG=error ./target/release/log_tcp_options -c <path/to/config.toml>
```