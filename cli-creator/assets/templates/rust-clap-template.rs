// CLI template following clig.dev guidelines.
// Rename this file and customize for your use case.

use anyhow::{Context, Result};
use clap::Parser;
use colored::*;
use serde::Serialize;
use std::fs;
use std::io::{self, Read};
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

/// Process INPUT file and transform it.
///
/// If INPUT is omitted or -, read from stdin.
#[derive(Parser)]
#[command(name = "mycli")]
#[command(version = "1.0.0")]
#[command(about = "Process INPUT file and transform it")]
#[command(after_help = "Examples:\n  \
    mycli data.txt\n  \
    mycli data.txt -o result.txt\n  \
    cat data.txt | mycli -\n  \
    mycli --json < data.txt")]
struct Cli {
    /// Input file (or stdin if omitted or -)
    input: Option<PathBuf>,

    /// Output file (default: stdout)
    #[arg(short, long)]
    output: Option<PathBuf>,

    /// Show detailed output
    #[arg(short, long)]
    verbose: bool,

    /// Output as JSON
    #[arg(long)]
    json: bool,
}

#[derive(Serialize)]
struct Output {
    result: String,
    length: usize,
}

fn read_input(filename: Option<&PathBuf>) -> Result<String> {
    match filename {
        Some(path) if path.to_str() != Some("-") => {
            fs::read_to_string(path).with_context(|| format!("Failed to read {:?}", path))
        }
        _ => {
            let mut buffer = String::new();
            io::stdin()
                .read_to_string(&mut buffer)
                .context("Failed to read from stdin")?;
            Ok(buffer)
        }
    }
}

fn setup_signal_handler() {
    let running = Arc::new(AtomicBool::new(true));
    let r = running.clone();

    ctrlc::set_handler(move || {
        eprintln!("{}", "\nInterrupted. Cleaning up...".yellow());
        r.store(false, Ordering::SeqCst);
        std::process::exit(130);
    })
    .expect("Error setting Ctrl-C handler");
}

fn main() -> Result<()> {
    setup_signal_handler();

    // Respect NO_COLOR environment variable
    if std::env::var("NO_COLOR").is_ok() {
        colored::control::set_override(false);
    }

    let cli = Cli::parse();

    // Read input
    let content = read_input(cli.input.as_ref())?;

    if cli.verbose {
        eprintln!("{}", "Processing...".cyan());
    }

    // Process (customize this)
    let result = content.to_uppercase();

    // Output
    let output_text = if cli.json {
        let output = Output {
            length: result.len(),
            result,
        };
        serde_json::to_string(&output)?
    } else {
        result
    };

    if let Some(output_path) = cli.output {
        fs::write(&output_path, output_text)
            .with_context(|| format!("Failed to write {:?}", output_path))?;

        if cli.verbose {
            eprintln!("{}", format!("✓ Written to {:?}", output_path).green());
        }
    } else {
        print!("{}", output_text);
    }

    Ok(())
}
