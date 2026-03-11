#!/usr/bin/env node
/**
 * CLI template following clig.dev guidelines.
 * Rename this file and customize for your use case.
 */

import { program } from 'commander';
import { readFileSync, writeFileSync } from 'fs';
import { stdin } from 'process';
import chalk from 'chalk';

// Handle Ctrl+C gracefully
process.on('SIGINT', () => {
    console.error(chalk.yellow('\nInterrupted. Cleaning up...'));
    process.exit(130);
});

// Helper: Read from file or stdin
async function readInput(filename) {
    if (filename && filename !== '-') {
        return readFileSync(filename, 'utf-8');
    } else {
        const chunks = [];
        for await (const chunk of stdin) {
            chunks.push(chunk);
        }
        return Buffer.concat(chunks).toString('utf-8');
    }
}

// Respect NO_COLOR environment variable
const hasColor = !process.env.NO_COLOR && process.stdout.isTTY;
const colorize = hasColor ? chalk : new Proxy({}, {
    get: () => (text) => text
});

program
    .name('mycli')
    .description('Process INPUT file and transform it')
    .version('1.0.0')
    .argument('[input]', 'Input file (or stdin if omitted or -)')
    .option('-o, --output <file>', 'Output file (default: stdout)')
    .option('-v, --verbose', 'Show detailed output')
    .option('--json', 'Output as JSON')
    .addHelpText('after', `
Examples:
  $ mycli data.txt
  $ mycli data.txt -o result.txt
  $ cat data.txt | mycli -
  $ mycli --json < data.txt
  `)
    .action(async (input, options) => {
        try {
            // Read input
            const content = await readInput(input);

            if (options.verbose) {
                console.error(colorize.cyan('Processing...'));
            }

            // Process (customize this)
            const result = content.toUpperCase();

            // Output
            let outputText;
            if (options.json) {
                outputText = JSON.stringify({
                    result: result,
                    length: result.length
                });
            } else {
                outputText = result;
            }

            if (options.output) {
                writeFileSync(options.output, outputText);
                if (options.verbose) {
                    console.error(colorize.green(`✓ Written to ${options.output}`));
                }
            } else {
                console.log(outputText);
            }
        } catch (error) {
            console.error(colorize.red(`Error: ${error.message}`));
            process.exit(1);
        }
    });

program.parse();
