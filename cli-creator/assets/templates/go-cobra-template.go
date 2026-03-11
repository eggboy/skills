package main

// CLI template following clig.dev guidelines.
// Rename this file and customize for your use case.

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/signal"
	"strings"
	"syscall"

	"github.com/fatih/color"
	"github.com/spf13/cobra"
)

var (
	output  string
	verbose bool
	asJSON  bool
)

// Handle Ctrl+C gracefully
func setupSignalHandler() {
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-c
		fmt.Fprintln(os.Stderr, "\nInterrupted. Cleaning up...")
		os.Exit(130)
	}()
}

// Read from file or stdin
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

var rootCmd = &cobra.Command{
	Use:   "mycli [input]",
	Short: "Process INPUT file and transform it",
	Long: `Process INPUT file and transform it.

If INPUT is omitted or -, read from stdin.`,
	Example: `  mycli data.txt
  mycli data.txt -o result.txt
  cat data.txt | mycli -
  mycli --json < data.txt`,
	Args: cobra.MaximumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		// Respect NO_COLOR
		if os.Getenv("NO_COLOR") != "" {
			color.NoColor = true
		}

		var input string
		if len(args) > 0 {
			input = args[0]
		}

		// Read input
		content, err := readInput(input)
		if err != nil {
			color.Red("Error reading input: %v", err)
			os.Exit(1)
		}

		if verbose {
			color.Cyan("Processing...")
		}

		// Process (customize this)
		result := strings.ToUpper(content)

		// Output
		var outputText string
		if asJSON {
			data := map[string]interface{}{
				"result": result,
				"length": len(result),
			}
			jsonData, _ := json.Marshal(data)
			outputText = string(jsonData)
		} else {
			outputText = result
		}

		if output != "" {
			err := os.WriteFile(output, []byte(outputText), 0644)
			if err != nil {
				color.Red("Error writing output: %v", err)
				os.Exit(1)
			}
			if verbose {
				color.Green("✓ Written to %s", output)
			}
		} else {
			fmt.Print(outputText)
		}
	},
}

func init() {
	rootCmd.Flags().StringVarP(&output, "output", "o", "", "Output file (default: stdout)")
	rootCmd.Flags().BoolVarP(&verbose, "verbose", "v", false, "Show detailed output")
	rootCmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	rootCmd.Version = "1.0.0"
}

func main() {
	setupSignalHandler()

	if err := rootCmd.Execute(); err != nil {
		os.Exit(1)
	}
}
