use retina_core::config::load_config;
use retina_core::subscription::TlsHandshake;
use retina_core::Runtime;
use retina_filtergen::filter;

use std::fs::File;
use std::io::{BufWriter, Write};
use std::path::PathBuf;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Mutex;

use anyhow::Result;
use clap::Parser;

// Define command-line arguments.
#[derive(Parser, Debug)]
struct Args {
    #[clap(short, long, parse(from_os_str), value_name = "FILE")]
    config: PathBuf,
    #[clap(
        short,
        long,
        parse(from_os_str),
        value_name = "FILE",
        default_value = "tcp_options.jsonl"
    )]
    outfile: PathBuf,
}

#[filter("tcp.syn == 1 and tcp.ack == 0")]
fn main() -> Result<()> {
    env_logger::init();
    let args = Args::parse();
    let config = load_config(&args.config);

    // Use `BufWriter` to improve the speed of repeated write calls to the same file.
    let file = Mutex::new(BufWriter::new(File::create(&args.outfile)?));
    let cnt = AtomicUsize::new(0);

    let callback = |pkt: ZcFrame| {
        let opts_slice = pkt.tcp.mbuf.get_data_slice(

            pkt.tcp.offset + 20, pkt.tcp.header.header_len - 20);

        let mut wtr = file.lock().unwrap();
        wtr.write_all(opts_slice.as_bytes()).unwrap();
        wtr.write_all(b"\n").unwrap();
        cnt.fetch_add(1, Ordering::Relaxed);

        //let opts_slice = tcp.mbuf.get_data_slice(tcp.offset + sizeof(TcpHeader), tcp.header_len() - sizeof(TcpHeader)); // pseudocode
        // write raw bytes to file
    };

    let mut runtime = Runtime::new(config, filter, callback)?;
    runtime.run();

    let mut wtr = file.lock().unwrap();
    wtr.flush()?;
    println!(
        "Done. Logged {:?} TCP Options to {:?}",
        cnt, &args.outfile
    );
    Ok(())
}
