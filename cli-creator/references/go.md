# Go CLI Patterns

Go implementations of clig.dev guidelines using Cobra, urfave/cli, and the flag package.

## Table of Contents

- [Recommended Libraries](#recommended-libraries)
- [Cobra Examples](#cobra-examples): Basic CLI, Subcommands, Colors and Progress, Reading from Stdin, JSON Output, Environment Variables
- [urfave/cli Examples](#urfavecli-examples): Basic CLI
- [Standard Library flag Package](#standard-library-flag-package): Basic CLI
- [Common Patterns](#common-patterns): SIGINT Handling, Configuration Loading, TTY Detection
- [Build and Distribution](#build-and-distribution): Build Binary, Cross-compilation, Go Module Setup, Install Locally

## Recommended Libraries

**Cobra** - Most popular, used by kubectl, hugo, github CLI
**urfave/cli** - Expressive, simple API
**flag** - Standard library, simple CLIs
**color** - Terminal colors (fatih/color)
**progressbar** - Progress bars (schollz/progressbar)

## Cobra Examples

### Basic CLI

```go
package main

import (
    "fmt"
    "os"
    "strings"
    
    "github.com/spf13/cobra"
)

var (
    output  string
    verbose bool
    force   bool
)

var rootCmd = &cobra.Command{
    Use:   "mycli <input>",
    Short: "Process INPUT file and transform it",
    Long: `Process INPUT file and transform it.

Examples:
  mycli data.txt
  mycli data.txt -o result.txt
  mycli data.txt --verbose --force`,
    Args: cobra.ExactArgs(1),
    Run: func(cmd *cobra.Command, args []string) {
        input := args[0]
        
        if _, err := os.Stat(input); os.IsNotExist(err) {
            fmt.Fprintf(os.Stderr, "Error: %s not found\n", input)
            os.Exit(1)
        }

        if verbose {
            fmt.Fprintf(os.Stderr, "Processing %s...\n", input)
        }

        content, err := os.ReadFile(input)
        if err != nil {
            fmt.Fprintf(os.Stderr, "Error: %v\n", err)
            os.Exit(1)
        }

        result := strings.ToUpper(string(content))

        if output != "" {
            if _, err := os.Stat(output); err == nil && !force {
                fmt.Fprintf(os.Stderr, "Error: %s exists. Use --force\n", output)
                os.Exit(1)
            }
            
            if err := os.WriteFile(output, []byte(result), 0644); err != nil {
                fmt.Fprintf(os.Stderr, "Error: %v\n", err)
                os.Exit(1)
            }
            
            if verbose {
                fmt.Fprintf(os.Stderr, "Written to %s\n", output)
            }
        } else {
            fmt.Print(result)
        }
    },
}

func init() {
    rootCmd.Flags().StringVarP(&output, "output", "o", "", "Output file")
    rootCmd.Flags().BoolVarP(&verbose, "verbose", "v", false, "Verbose output")
    rootCmd.Flags().BoolVarP(&force, "force", "f", false, "Overwrite existing files")
    rootCmd.Version = "1.0.0"
}

func main() {
    if err := rootCmd.Execute(); err != nil {
        os.Exit(1)
    }
}
```

### Subcommands

```go
package main

import (
    "fmt"
    "os"
    "bufio"
    "strings"
    
    "github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
    Use:   "mycli",
    Short: "My awesome CLI tool",
    Version: "1.0.0",
}

var initCmd = &cobra.Command{
    Use:   "init",
    Short: "Initialize a new project",
    Run: func(cmd *cobra.Command, args []string) {
        name, _ := cmd.Flags().GetString("name")
        if name == "" {
            fmt.Print("Project name: ")
            reader := bufio.NewReader(os.Stdin)
            name, _ = reader.ReadString('\n')
            name = strings.TrimSpace(name)
        }
        
        fmt.Printf("Initializing %s...\n", name)
        // Implementation
    },
}

var buildCmd = &cobra.Command{
    Use:   "build",
    Short: "Build the project",
    Run: func(cmd *cobra.Command, args []string) {
        release, _ := cmd.Flags().GetBool("release")
        mode := "debug"
        if release {
            mode = "release"
        }
        fmt.Printf("Building in %s mode...\n", mode)
        // Implementation
    },
}

var deployCmd = &cobra.Command{
    Use:   "deploy <environment>",
    Short: "Deploy to environment",
    Args:  cobra.ExactArgs(1),
    ValidArgs: []string{"dev", "staging", "prod"},
    Run: func(cmd *cobra.Command, args []string) {
        environment := args[0]
        yes, _ := cmd.Flags().GetBool("yes")
        
        if !yes {
            fmt.Printf("Deploy to %s? [y/N]: ", environment)
            reader := bufio.NewReader(os.Stdin)
            response, _ := reader.ReadString('\n')
            response = strings.TrimSpace(strings.ToLower(response))
            
            if response != "y" {
                fmt.Println("Cancelled")
                return
            }
        }
        
        fmt.Printf("Deploying to %s...\n", environment)
        // Implementation
    },
}

func init() {
    initCmd.Flags().String("name", "", "Project name")
    buildCmd.Flags().Bool("release", false, "Build in release mode")
    deployCmd.Flags().BoolP("yes", "y", false, "Skip confirmation")
    
    rootCmd.AddCommand(initCmd)
    rootCmd.AddCommand(buildCmd)
    rootCmd.AddCommand(deployCmd)
}

func main() {
    if err := rootCmd.Execute(); err != nil {
        os.Exit(1)
    }
}
```

### Colors and Progress

```go
import (
    "github.com/fatih/color"
    "github.com/schollz/progressbar/v3"
    "time"
)

func showColors() {
    color.Green("✓ Success")
    color.Yellow("⚠ Warning")
    color.Red("✗ Error")
    color.Cyan("Info")
    
    // Respect NO_COLOR
    if os.Getenv("NO_COLOR") != "" {
        color.NoColor = true
    }
}

func showProgress() {
    bar := progressbar.Default(100)
    for i := 0; i < 100; i++ {
        bar.Add(1)
        time.Sleep(10 * time.Millisecond)
    }
}
```

### Reading from Stdin

```go
import (
    "io"
    "os"
)

func readInput(filename string) (string, error) {
    var reader io.Reader
    
    if filename == "" || filename == "-" {
        reader = os.Stdin
    } else {
        file, err := os.Open(filename)
        if err != nil {
            return "", err
        }
        defer file.Close()
        reader = file
    }
    
    content, err := io.ReadAll(reader)
    if err != nil {
        return "", err
    }
    
    return string(content), nil
}
```

### JSON Output

```go
import (
    "encoding/json"
    "fmt"
)

func showStats(asJSON bool) {
    data := map[string]interface{}{
        "files":    42,
        "size":     1024,
        "duration": 2.5,
    }
    
    if asJSON {
        jsonData, _ := json.MarshalIndent(data, "", "  ")
        fmt.Println(string(jsonData))
    } else {
        fmt.Printf("Files: %d\n", data["files"])
        fmt.Printf("Size: %d bytes\n", data["size"])
        fmt.Printf("Duration: %.1fs\n", data["duration"])
    }
}
```

### Environment Variables

```go
func getAPIKey() string {
    // Check command-line flag first
    apiKey, _ := cmd.Flags().GetString("api-key")
    if apiKey != "" {
        return apiKey
    }
    
    // Fall back to environment variable
    return os.Getenv("MYCLI_API_KEY")
}
```

## urfave/cli Examples

### Basic CLI

```go
package main

import (
    "fmt"
    "os"
    "strings"
    
    "github.com/urfave/cli/v2"
)

func main() {
    app := &cli.App{
        Name:    "mycli",
        Usage:   "Process INPUT file and transform it",
        Version: "1.0.0",
        Flags: []cli.Flag{
            &cli.StringFlag{
                Name:    "output",
                Aliases: []string{"o"},
                Usage:   "Output file",
            },
            &cli.BoolFlag{
                Name:    "verbose",
                Aliases: []string{"v"},
                Usage:   "Verbose output",
            },
            &cli.BoolFlag{
                Name:    "force",
                Aliases: []string{"f"},
                Usage:   "Overwrite existing files",
            },
        },
        Action: func(c *cli.Context) error {
            if c.NArg() == 0 {
                return fmt.Errorf("input file required")
            }
            
            input := c.Args().Get(0)
            
            if _, err := os.Stat(input); os.IsNotExist(err) {
                return fmt.Errorf("%s not found", input)
            }
            
            if c.Bool("verbose") {
                fmt.Fprintf(os.Stderr, "Processing %s...\n", input)
            }
            
            content, err := os.ReadFile(input)
            if err != nil {
                return err
            }
            
            result := strings.ToUpper(string(content))
            
            if output := c.String("output"); output != "" {
                if _, err := os.Stat(output); err == nil && !c.Bool("force") {
                    return fmt.Errorf("%s exists. Use --force", output)
                }
                
                if err := os.WriteFile(output, []byte(result), 0644); err != nil {
                    return err
                }
                
                if c.Bool("verbose") {
                    fmt.Fprintf(os.Stderr, "Written to %s\n", output)
                }
            } else {
                fmt.Print(result)
            }
            
            return nil
        },
    }
    
    if err := app.Run(os.Args); err != nil {
        fmt.Fprintf(os.Stderr, "Error: %v\n", err)
        os.Exit(1)
    }
}
```

## Standard Library flag Package

### Basic CLI

```go
package main

import (
    "flag"
    "fmt"
    "os"
    "strings"
)

func main() {
    output := flag.String("output", "", "Output file")
    outputShort := flag.String("o", "", "Output file (shorthand)")
    verbose := flag.Bool("verbose", false, "Verbose output")
    verboseShort := flag.Bool("v", false, "Verbose output (shorthand)")
    force := flag.Bool("force", false, "Overwrite existing files")
    forceShort := flag.Bool("f", false, "Overwrite existing files (shorthand)")
    version := flag.Bool("version", false, "Show version")
    
    flag.Usage = func() {
        fmt.Fprintf(os.Stderr, "Usage: mycli [OPTIONS] <input>\n\n")
        fmt.Fprintf(os.Stderr, "Process INPUT file and transform it\n\n")
        fmt.Fprintf(os.Stderr, "Options:\n")
        flag.PrintDefaults()
        fmt.Fprintf(os.Stderr, "\nExamples:\n")
        fmt.Fprintf(os.Stderr, "  mycli data.txt\n")
        fmt.Fprintf(os.Stderr, "  mycli data.txt -o result.txt\n")
    }
    
    flag.Parse()
    
    if *version {
        fmt.Println("1.0.0")
        return
    }
    
    if flag.NArg() == 0 {
        fmt.Fprintln(os.Stderr, "Error: input file required")
        flag.Usage()
        os.Exit(1)
    }
    
    input := flag.Arg(0)
    
    // Merge short and long flags
    out := *output
    if *outputShort != "" {
        out = *outputShort
    }
    verb := *verbose || *verboseShort
    frc := *force || *forceShort
    
    if _, err := os.Stat(input); os.IsNotExist(err) {
        fmt.Fprintf(os.Stderr, "Error: %s not found\n", input)
        os.Exit(1)
    }
    
    if verb {
        fmt.Fprintf(os.Stderr, "Processing %s...\n", input)
    }
    
    content, err := os.ReadFile(input)
    if err != nil {
        fmt.Fprintf(os.Stderr, "Error: %v\n", err)
        os.Exit(1)
    }
    
    result := strings.ToUpper(string(content))
    
    if out != "" {
        if _, err := os.Stat(out); err == nil && !frc {
            fmt.Fprintf(os.Stderr, "Error: %s exists. Use --force\n", out)
            os.Exit(1)
        }
        
        if err := os.WriteFile(out, []byte(result), 0644); err != nil {
            fmt.Fprintf(os.Stderr, "Error: %v\n", err)
            os.Exit(1)
        }
        
        if verb {
            fmt.Fprintf(os.Stderr, "Written to %s\n", out)
        }
    } else {
        fmt.Print(result)
    }
}
```

## Common Patterns

### Graceful SIGINT Handling

```go
import (
    "os"
    "os/signal"
    "syscall"
)

func main() {
    sigChan := make(chan os.Signal, 1)
    signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)
    
    go func() {
        <-sigChan
        fmt.Fprintln(os.Stderr, "\nInterrupted. Cleaning up...")
        // Cleanup code here
        os.Exit(130) // 128 + SIGINT (2)
    }()
    
    // Main program logic
}
```

### Configuration Loading

```go
import (
    "encoding/json"
    "os"
    "path/filepath"
)

type Config struct {
    APIKey  string `json:"api_key"`
    Timeout int    `json:"timeout"`
    Verbose bool   `json:"verbose"`
}

func loadConfig() (*Config, error) {
    config := &Config{
        Timeout: 30,
        Verbose: false,
    }
    
    // 1. Load from config file
    homeDir, _ := os.UserHomeDir()
    configPath := filepath.Join(homeDir, ".config", "mycli", "config.json")
    
    if data, err := os.ReadFile(configPath); err == nil {
        json.Unmarshal(data, config)
    }
    
    // 2. Load from environment
    if apiKey := os.Getenv("MYCLI_API_KEY"); apiKey != "" {
        config.APIKey = apiKey
    }
    if os.Getenv("MYCLI_DEBUG") == "1" {
        config.Verbose = true
    }
    
    return config, nil
}
```

### TTY Detection

```go
import (
    "os"
    "golang.org/x/term"
)

func isTerminal() bool {
    return term.IsTerminal(int(os.Stdout.Fd()))
}

func supportsColor() bool {
    if os.Getenv("NO_COLOR") != "" {
        return false
    }
    return isTerminal()
}
```

## Build and Distribution

### Build Binary

```bash
go build -o mycli main.go
```

### Cross-compilation

```bash
GOOS=linux GOARCH=amd64 go build -o mycli-linux-amd64
GOOS=darwin GOARCH=amd64 go build -o mycli-darwin-amd64
GOOS=windows GOARCH=amd64 go build -o mycli-windows-amd64.exe
```

### Go Module Setup

```bash
go mod init github.com/user/mycli
go mod tidy
```

### Install Locally

```bash
go install
```
