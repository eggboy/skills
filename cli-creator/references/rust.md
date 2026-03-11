# Rust CLI Patterns

Rust implementations of clig.dev guidelines using Clap, structopt (deprecated), and other tools.

## Table of Contents

- [Recommended Libraries](#recommended-libraries)
- [Clap Examples (Derive API)](#clap-examples-derive-api): Basic CLI, Subcommands, Colors and Progress, Reading from Stdin, JSON Output, Environment Variables
- [Clap Builder API](#clap-builder-api): Basic CLI
- [Error Handling with Anyhow](#error-handling-with-anyhow)
- [Common Patterns](#common-patterns): SIGINT Handling, Configuration Loading, TTY Detection, Dry Run
- [Testing](#testing)
- [Cargo Configuration](#cargo-configuration)
- [Build and Distribution](#build-and-distribution)

## Recommended Libraries

**clap** - Most popular, derive or builder API
**colored** - Terminal colors
**indicatif** - Progress bars and spinners
**dialoguer** - Interactive prompts
**anyhow** - Error handling
**serde** - JSON/YAML serialization

## Clap Examples (Derive API)

### Basic CLI

```rust
use clap::Parser;
use std::fs;
use std::io::{self, Write};
use std::path::PathBuf;

/// Process INPUT file and transform it
#[derive(Parser)]
#[command(name = "mycli")]
#[command(version = "1.0.0")]
#[command(about = "Process INPUT file and transform it", long_about = None)]
#[command(after_help = "Examples:\n  mycli data.txt\n  mycli data.txt -o result.txt\n  mycli data.txt --verbose --force")]
struct Cli {
    /// Input file to process
    input: PathBuf,

    /// Output file
    #[arg(short, long)]
    output: Option<PathBuf>,

    /// Verbose output
    #[arg(short, long)]
    verbose: bool,

    /// Overwrite existing files
    #[arg(short, long)]
    force: bool,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();

    if !cli.input.exists() {
        eprintln!("Error: {:?} not found", cli.input);
        std::process::exit(1);
    }

    if cli.verbose {
        eprintln!("Processing {:?}...", cli.input);
    }

    let content = fs::read_to_string(&cli.input)?;
    let result = content.to_uppercase();

    if let Some(output) = cli.output {
        if output.exists() && !cli.force {
            eprintln!("Error: {:?} exists. Use --force", output);
            std::process::exit(1);
        }

        fs::write(&output, result)?;

        if cli.verbose {
            eprintln!("Written to {:?}", output);
        }
    } else {
        print!("{}", result);
    }

    Ok(())
}
```

### Subcommands

```rust
use clap::{Parser, Subcommand};
use dialoguer::Confirm;

#[derive(Parser)]
#[command(name = "mycli")]
#[command(version = "1.0.0")]
#[command(about = "My awesome CLI tool")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Initialize a new project
    Init {
        /// Project name
        #[arg(long)]
        name: String,
    },
    /// Build the project
    Build {
        /// Build in release mode
        #[arg(long)]
        release: bool,
    },
    /// Deploy to environment
    Deploy {
        /// Environment (dev, staging, prod)
        #[arg(value_enum)]
        environment: Environment,

        /// Skip confirmation
        #[arg(short, long)]
        yes: bool,
    },
}

#[derive(clap::ValueEnum, Clone)]
enum Environment {
    Dev,
    Staging,
    Prod,
}

fn main() {
    let cli = Cli::parse();

    match cli.command {
        Commands::Init { name } => {
            println!("Initializing {}...", name);
            // Implementation
        }
        Commands::Build { release } => {
            let mode = if release { "release" } else { "debug" };
            println!("Building in {} mode...", mode);
            // Implementation
        }
        Commands::Deploy { environment, yes } => {
            let env_name = match environment {
                Environment::Dev => "dev",
                Environment::Staging => "staging",
                Environment::Prod => "prod",
            };

            if !yes {
                if !Confirm::new()
                    .with_prompt(format!("Deploy to {}?", env_name))
                    .interact()
                    .unwrap()
                {
                    println!("Cancelled");
                    return;
                }
            }

            println!("Deploying to {}...", env_name);
            // Implementation
        }
    }
}
```

### Colors and Progress

```rust
use colored::*;
use indicatif::{ProgressBar, ProgressStyle};
use std::thread;
use std::time::Duration;

fn show_colors() {
    println!("{}", "✓ Success".green());
    println!("{}", "⚠ Warning".yellow());
    println!("{}", "✗ Error".red().bold());
    println!("{}", "Info".cyan());

    // Respect NO_COLOR
    if std::env::var("NO_COLOR").is_ok() {
        colored::control::set_override(false);
    }
}

fn show_progress() {
    let pb = ProgressBar::new(100);
    pb.set_style(
        ProgressStyle::default_bar()
            .template("[{elapsed_precise}] {bar:40.cyan/blue} {pos:>7}/{len:7} {msg}")
            .unwrap()
            .progress_chars("##-"),
    );

    for i in 0..100 {
        pb.set_position(i);
        thread::sleep(Duration::from_millis(10));
    }

    pb.finish_with_message("Done!");
}

fn show_spinner() {
    let pb = ProgressBar::new_spinner();
    pb.set_message("Loading...");

    for _ in 0..100 {
        pb.tick();
        thread::sleep(Duration::from_millis(20));
    }

    pb.finish_with_message("Done!");
}
```

### Reading from Stdin

```rust
use std::fs;
use std::io::{self, Read};
use std::path::Path;

fn read_input(filename: Option<&Path>) -> io::Result<String> {
    match filename {
        Some(path) if path.to_str() != Some("-") => {
            fs::read_to_string(path)
        }
        _ => {
            let mut buffer = String::new();
            io::stdin().read_to_string(&mut buffer)?;
            Ok(buffer)
        }
    }
}

// Usage in Clap
#[derive(Parser)]
struct Cli {
    /// Input file (or stdin if omitted or -)
    input: Option<PathBuf>,
}

fn main() -> io::Result<()> {
    let cli = Cli::parse();
    let content = read_input(cli.input.as_deref())?;
    println!("{}", content.to_uppercase());
    Ok(())
}
```

### JSON Output with Serde

```rust
use clap::Parser;
use serde::Serialize;
use serde_json;

#[derive(Serialize)]
struct Stats {
    files: u32,
    size: u64,
    duration: f64,
}

#[derive(Parser)]
struct Cli {
    /// Output as JSON
    #[arg(long)]
    json: bool,
}

fn main() {
    let cli = Cli::parse();

    let stats = Stats {
        files: 42,
        size: 1024,
        duration: 2.5,
    };

    if cli.json {
        println!("{}", serde_json::to_string(&stats).unwrap());
    } else {
        println!("Files: {}", stats.files);
        println!("Size: {} bytes", stats.size);
        println!("Duration: {}s", stats.duration);
    }
}
```

### Environment Variables

```rust
use clap::Parser;

#[derive(Parser)]
struct Cli {
    /// API key
    #[arg(long, env = "MYCLI_API_KEY")]
    api_key: Option<String>,

    /// Debug mode
    #[arg(long, env = "MYCLI_DEBUG")]
    debug: bool,
}

fn main() {
    let cli = Cli::parse();

    let api_key = match cli.api_key {
        Some(key) => key,
        None => {
            eprintln!("Error: API key required");
            eprintln!("Set MYCLI_API_KEY or use --api-key");
            std::process::exit(1);
        }
    };

    if cli.debug {
        eprintln!("Using API key: {}...", &api_key[..8.min(api_key.len())]);
    }
}
```

## Clap Builder API

### Basic CLI

```rust
use clap::{Arg, Command};
use std::fs;
use std::path::PathBuf;

fn main() {
    let matches = Command::new("mycli")
        .version("1.0.0")
        .about("Process INPUT file and transform it")
        .arg(
            Arg::new("input")
                .help("Input file to process")
                .required(true)
                .index(1),
        )
        .arg(
            Arg::new("output")
                .short('o')
                .long("output")
                .value_name("FILE")
                .help("Output file"),
        )
        .arg(
            Arg::new("verbose")
                .short('v')
                .long("verbose")
                .action(clap::ArgAction::SetTrue)
                .help("Verbose output"),
        )
        .arg(
            Arg::new("force")
                .short('f')
                .long("force")
                .action(clap::ArgAction::SetTrue)
                .help("Overwrite existing files"),
        )
        .get_matches();

    let input = PathBuf::from(matches.get_one::<String>("input").unwrap());
    let output = matches.get_one::<String>("output").map(PathBuf::from);
    let verbose = matches.get_flag("verbose");
    let force = matches.get_flag("force");

    if !input.exists() {
        eprintln!("Error: {:?} not found", input);
        std::process::exit(1);
    }

    if verbose {
        eprintln!("Processing {:?}...", input);
    }

    let content = fs::read_to_string(&input).unwrap();
    let result = content.to_uppercase();

    if let Some(output) = output {
        if output.exists() && !force {
            eprintln!("Error: {:?} exists. Use --force", output);
            std::process::exit(1);
        }

        fs::write(&output, result).unwrap();

        if verbose {
            eprintln!("Written to {:?}", output);
        }
    } else {
        print!("{}", result);
    }
}
```

## Error Handling with Anyhow

### Using anyhow for Better Errors

```rust
use anyhow::{Context, Result};
use clap::Parser;
use std::fs;
use std::path::PathBuf;

#[derive(Parser)]
struct Cli {
    input: PathBuf,
    #[arg(short, long)]
    output: Option<PathBuf>,
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    let content = fs::read_to_string(&cli.input)
        .with_context(|| format!("Failed to read {:?}", cli.input))?;

    let result = content.to_uppercase();

    if let Some(output) = cli.output {
        fs::write(&output, result)
            .with_context(|| format!("Failed to write {:?}", output))?;
    } else {
        print!("{}", result);
    }

    Ok(())
}
```

## Common Patterns

### Graceful SIGINT Handling

```rust
use ctrlc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

fn main() {
    let running = Arc::new(AtomicBool::new(true));
    let r = running.clone();

    ctrlc::set_handler(move || {
        eprintln!("\nInterrupted. Cleaning up...");
        r.store(false, Ordering::SeqCst);
        // Cleanup code here
        std::process::exit(130); // 128 + SIGINT (2)
    })
    .expect("Error setting Ctrl-C handler");

    while running.load(Ordering::SeqCst) {
        // Main program logic
    }
}
```

### Configuration Loading

```rust
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Serialize, Deserialize, Default)]
struct Config {
    api_key: Option<String>,
    timeout: u64,
    verbose: bool,
}

fn load_config() -> Config {
    let mut config = Config {
        timeout: 30,
        verbose: false,
        ..Default::default()
    };

    // 1. Load from config file
    if let Some(home) = dirs::home_dir() {
        let config_path = home.join(".config/mycli/config.json");
        if let Ok(data) = fs::read_to_string(config_path) {
            if let Ok(file_config) = serde_json::from_str::<Config>(&data) {
                config = file_config;
            }
        }
    }

    // 2. Load from environment
    if let Ok(api_key) = std::env::var("MYCLI_API_KEY") {
        config.api_key = Some(api_key);
    }
    if let Ok(timeout) = std::env::var("MYCLI_TIMEOUT") {
        if let Ok(t) = timeout.parse() {
            config.timeout = t;
        }
    }

    config
}
```

### TTY Detection

```rust
use atty::Stream;

fn is_terminal() -> bool {
    atty::is(Stream::Stdout)
}

fn supports_color() -> bool {
    if std::env::var("NO_COLOR").is_ok() {
        return false;
    }
    is_terminal()
}
```

### Dry Run Pattern

```rust
#[derive(Parser)]
struct Cli {
    /// Show what would happen
    #[arg(long)]
    dry_run: bool,
}

fn main() {
    let cli = Cli::parse();

    println!("Would deploy:");
    println!("  - api-server (v1.2.3)");
    println!("  - web-frontend (v2.1.0)");

    if cli.dry_run {
        println!("\nDry run complete. No changes made.");
        return;
    }

    // Actual implementation
}
```

## Testing

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use assert_cmd::Command;
    use predicates::prelude::*;

    #[test]
    fn test_version() {
        let mut cmd = Command::cargo_bin("mycli").unwrap();
        cmd.arg("--version")
            .assert()
            .success()
            .stdout(predicate::str::contains("1.0.0"));
    }

    #[test]
    fn test_help() {
        let mut cmd = Command::cargo_bin("mycli").unwrap();
        cmd.arg("--help")
            .assert()
            .success()
            .stdout(predicate::str::contains("Usage:"));
    }

    #[test]
    fn test_missing_input() {
        let mut cmd = Command::cargo_bin("mycli").unwrap();
        cmd.assert()
            .failure()
            .stderr(predicate::str::contains("required"));
    }
}
```

## Cargo Configuration

### Cargo.toml

```toml
[package]
name = "mycli"
version = "1.0.0"
edition = "2021"

[[bin]]
name = "mycli"
path = "src/main.rs"

[dependencies]
clap = { version = "4.4", features = ["derive"] }
anyhow = "1.0"
colored = "2.0"
indicatif = "0.17"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
dialoguer = "0.11"
dirs = "5.0"
atty = "0.2"
ctrlc = "3.4"

[dev-dependencies]
assert_cmd = "2.0"
predicates = "3.0"
```

## Build and Distribution

### Build Binary

```bash
cargo build --release
```

### Install Locally

```bash
cargo install --path .
```

### Cross-compilation with cross

```bash
cargo install cross
cross build --target x86_64-unknown-linux-gnu
cross build --target x86_64-apple-darwin
cross build --target x86_64-pc-windows-gnu
```

### Publish to crates.io

```bash
cargo publish
```
