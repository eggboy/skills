# Node.js CLI Patterns

Node.js implementations of clig.dev guidelines using Commander, yargs, and other popular tools.

## Table of Contents

- [Recommended Libraries](#recommended-libraries)
- [Commander.js Examples](#commanderjs-examples): Basic CLI, Subcommands, Colors and Progress, Reading from Stdin, JSON Output, Environment Variables
- [yargs Examples](#yargs-examples): Basic CLI, Subcommands
- [Common Patterns](#common-patterns): SIGINT Handling, Configuration Loading, TTY Detection, Dry Run
- [Package Setup](#package-setup): package.json, Make CLI Executable, Shebang
- [Testing](#testing)
- [Publishing](#publishing)

## Recommended Libraries

**Commander.js** - Clean API, most popular
**yargs** - Feature-rich, complex apps
**oclif** - Full framework for complex CLIs
**chalk** - Terminal colors
**ora** - Spinners and progress
**inquirer** - Interactive prompts

## Commander.js Examples

### Basic CLI

```javascript
#!/usr/bin/env node
import { program } from 'commander';
import { readFileSync, writeFileSync, existsSync } from 'fs';

program
  .name('mycli')
  .description('Process INPUT_FILE and transform it')
  .version('1.0.0')
  .argument('<input>', 'Input file to process')
  .option('-o, --output <file>', 'Output file')
  .option('-v, --verbose', 'Verbose output')
  .option('-f, --force', 'Overwrite existing files')
  .addHelpText('after', `
Examples:
  $ mycli data.txt
  $ mycli data.txt -o result.txt
  $ mycli data.txt --verbose --force
  `)
  .action((input, options) => {
    if (!existsSync(input)) {
      console.error(`Error: ${input} not found`);
      process.exit(1);
    }

    if (options.verbose) {
      console.error(`Processing ${input}...`);
    }

    try {
      const content = readFileSync(input, 'utf-8');
      const result = content.toUpperCase();

      if (options.output) {
        if (existsSync(options.output) && !options.force) {
          console.error(`Error: ${options.output} exists. Use --force`);
          process.exit(1);
        }
        writeFileSync(options.output, result);
        if (options.verbose) {
          console.error(`Written to ${options.output}`);
        }
      } else {
        console.log(result);
      }
    } catch (error) {
      console.error(`Error: ${error.message}`);
      process.exit(1);
    }
  });

program.parse();
```

### Subcommands

```javascript
#!/usr/bin/env node
import { program } from 'commander';
import inquirer from 'inquirer';

program
  .name('mycli')
  .description('My awesome CLI tool')
  .version('1.0.0');

program
  .command('init')
  .description('Initialize a new project')
  .option('--name <name>', 'Project name')
  .action(async (options) => {
    let name = options.name;
    
    if (!name) {
      const answers = await inquirer.prompt([
        {
          type: 'input',
          name: 'name',
          message: 'Project name:',
        }
      ]);
      name = answers.name;
    }
    
    console.log(`Initializing ${name}...`);
    // Implementation
  });

program
  .command('build')
  .description('Build the project')
  .option('--release', 'Build in release mode')
  .action((options) => {
    const mode = options.release ? 'release' : 'debug';
    console.log(`Building in ${mode} mode...`);
    // Implementation
  });

program
  .command('deploy')
  .description('Deploy to environment')
  .argument('<environment>', 'Environment (dev, staging, prod)')
  .option('-y, --yes', 'Skip confirmation')
  .action(async (environment, options) => {
    if (!['dev', 'staging', 'prod'].includes(environment)) {
      console.error(`Error: Invalid environment '${environment}'`);
      process.exit(1);
    }

    if (!options.yes) {
      const { confirmed } = await inquirer.prompt([
        {
          type: 'confirm',
          name: 'confirmed',
          message: `Deploy to ${environment}?`,
          default: false
        }
      ]);
      
      if (!confirmed) {
        console.log('Cancelled');
        return;
      }
    }

    console.log(`Deploying to ${environment}...`);
    // Implementation
  });

program.parse();
```

### Colors and Progress

```javascript
import chalk from 'chalk';
import ora from 'ora';

// Colors
console.log(chalk.green('✓ Success'));
console.log(chalk.yellow('⚠ Warning'));
console.log(chalk.red('✗ Error'));
console.log(chalk.cyan('Info'));

// Respect NO_COLOR
const hasColor = !process.env.NO_COLOR && process.stdout.isTTY;
const colorize = hasColor ? chalk : new Proxy({}, {
  get: () => (text) => text
});

// Spinner
const spinner = ora('Loading...').start();
setTimeout(() => {
  spinner.succeed('Done!');
}, 2000);

// Progress bar with cli-progress
import cliProgress from 'cli-progress';

const bar = new cliProgress.SingleBar({}, cliProgress.Presets.shades_classic);
bar.start(100, 0);

for (let i = 0; i <= 100; i++) {
  bar.update(i);
}
bar.stop();
```

### Reading from Stdin

```javascript
import { readFileSync } from 'fs';
import { stdin } from 'process';

async function readInput(filename) {
  if (filename && filename !== '-') {
    return readFileSync(filename, 'utf-8');
  } else {
    // Read from stdin
    const chunks = [];
    for await (const chunk of stdin) {
      chunks.push(chunk);
    }
    return Buffer.concat(chunks).toString('utf-8');
  }
}

// Usage
program
  .argument('[input]', 'Input file (or stdin if omitted)')
  .action(async (input) => {
    const content = await readInput(input);
    console.log(content.toUpperCase());
  });
```

### JSON Output

```javascript
program
  .option('--json', 'Output as JSON')
  .action((options) => {
    const data = {
      files: 42,
      size: 1024,
      duration: 2.5
    };

    if (options.json) {
      console.log(JSON.stringify(data));
    } else {
      console.log(`Files: ${data.files}`);
      console.log(`Size: ${data.size} bytes`);
      console.log(`Duration: ${data.duration}s`);
    }
  });
```

### Environment Variables

```javascript
program
  .option('--api-key <key>', 'API key', process.env.MYCLI_API_KEY)
  .option('--debug', 'Debug mode', process.env.MYCLI_DEBUG === '1')
  .action((options) => {
    if (!options.apiKey) {
      console.error('Error: API key required');
      console.error('Set MYCLI_API_KEY or use --api-key');
      process.exit(1);
    }

    if (options.debug) {
      console.error(`Using API key: ${options.apiKey.slice(0, 8)}...`);
    }
  });
```

## yargs Examples

### Basic CLI

```javascript
#!/usr/bin/env node
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import { readFileSync, writeFileSync, existsSync } from 'fs';

yargs(hideBin(process.argv))
  .command(
    '$0 <input>',
    'Process INPUT file and transform it',
    (yargs) => {
      return yargs
        .positional('input', {
          describe: 'Input file to process',
          type: 'string'
        })
        .option('output', {
          alias: 'o',
          type: 'string',
          description: 'Output file'
        })
        .option('verbose', {
          alias: 'v',
          type: 'boolean',
          description: 'Verbose output'
        })
        .option('force', {
          alias: 'f',
          type: 'boolean',
          description: 'Overwrite existing files'
        })
        .example('$0 data.txt', 'Process data.txt')
        .example('$0 data.txt -o result.txt', 'Save to result.txt');
    },
    (argv) => {
      if (!existsSync(argv.input)) {
        console.error(`Error: ${argv.input} not found`);
        process.exit(1);
      }

      if (argv.verbose) {
        console.error(`Processing ${argv.input}...`);
      }

      const content = readFileSync(argv.input, 'utf-8');
      const result = content.toUpperCase();

      if (argv.output) {
        if (existsSync(argv.output) && !argv.force) {
          console.error(`Error: ${argv.output} exists. Use --force`);
          process.exit(1);
        }
        writeFileSync(argv.output, result);
        if (argv.verbose) {
          console.error(`Written to ${argv.output}`);
        }
      } else {
        console.log(result);
      }
    }
  )
  .version('1.0.0')
  .help()
  .argv;
```

### Subcommands with yargs

```javascript
#!/usr/bin/env node
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';

yargs(hideBin(process.argv))
  .command(
    'init',
    'Initialize a new project',
    (yargs) => {
      return yargs.option('name', {
        type: 'string',
        description: 'Project name',
        demandOption: true
      });
    },
    (argv) => {
      console.log(`Initializing ${argv.name}...`);
    }
  )
  .command(
    'build',
    'Build the project',
    (yargs) => {
      return yargs.option('release', {
        type: 'boolean',
        description: 'Build in release mode'
      });
    },
    (argv) => {
      const mode = argv.release ? 'release' : 'debug';
      console.log(`Building in ${mode} mode...`);
    }
  )
  .command(
    'deploy <environment>',
    'Deploy to environment',
    (yargs) => {
      return yargs
        .positional('environment', {
          describe: 'Environment',
          type: 'string',
          choices: ['dev', 'staging', 'prod']
        })
        .option('yes', {
          alias: 'y',
          type: 'boolean',
          description: 'Skip confirmation'
        });
    },
    async (argv) => {
      if (!argv.yes) {
        const inquirer = (await import('inquirer')).default;
        const { confirmed } = await inquirer.prompt([
          {
            type: 'confirm',
            name: 'confirmed',
            message: `Deploy to ${argv.environment}?`,
            default: false
          }
        ]);

        if (!confirmed) {
          console.log('Cancelled');
          return;
        }
      }

      console.log(`Deploying to ${argv.environment}...`);
    }
  )
  .version('1.0.0')
  .help()
  .demandCommand(1, 'You need to specify a command')
  .strict()
  .argv;
```

## Common Patterns

### Graceful SIGINT Handling

```javascript
process.on('SIGINT', () => {
  console.error('\nInterrupted. Cleaning up...');
  // Cleanup code here
  process.exit(130); // 128 + SIGINT (2)
});
```

### Configuration Loading

```javascript
import { readFileSync } from 'fs';
import { homedir } from 'os';
import { join } from 'path';

function loadConfig() {
  const config = {
    apiKey: null,
    timeout: 30,
    verbose: false
  };

  // 1. Load from config file
  const configPath = join(homedir(), '.config', 'mycli', 'config.json');
  try {
    const fileConfig = JSON.parse(readFileSync(configPath, 'utf-8'));
    Object.assign(config, fileConfig);
  } catch (err) {
    // Config file doesn't exist or is invalid
  }

  // 2. Load from environment
  if (process.env.MYCLI_API_KEY) {
    config.apiKey = process.env.MYCLI_API_KEY;
  }
  if (process.env.MYCLI_TIMEOUT) {
    config.timeout = parseInt(process.env.MYCLI_TIMEOUT);
  }

  return config;
}
```

### TTY Detection

```javascript
function supportsColor() {
  if (process.env.NO_COLOR) {
    return false;
  }
  if (!process.stdout.isTTY) {
    return false;
  }
  return true;
}
```

### Dry Run Pattern

```javascript
program
  .option('--dry-run', 'Show what would happen')
  .action((options) => {
    const dryRun = options.dryRun;

    console.log('Would deploy:');
    console.log('  - api-server (v1.2.3)');
    console.log('  - web-frontend (v2.1.0)');

    if (dryRun) {
      console.log('\nDry run complete. No changes made.');
      return;
    }

    // Actual implementation
  });
```

## Package Setup

### package.json

```json
{
  "name": "mycli",
  "version": "1.0.0",
  "type": "module",
  "bin": {
    "mycli": "./bin/cli.js"
  },
  "files": [
    "bin"
  ],
  "dependencies": {
    "commander": "^11.0.0",
    "chalk": "^5.3.0",
    "ora": "^7.0.0",
    "inquirer": "^9.2.0"
  },
  "engines": {
    "node": ">=18.0.0"
  }
}
```

### Make CLI Executable

```bash
chmod +x bin/cli.js
```

### Shebang

```javascript
#!/usr/bin/env node
```

## Testing

```javascript
import { execSync } from 'child_process';
import { describe, it } from 'node:test';
import assert from 'node:assert';

describe('mycli', () => {
  it('shows version', () => {
    const output = execSync('node bin/cli.js --version', { encoding: 'utf-8' });
    assert.match(output, /1\.0\.0/);
  });

  it('shows help', () => {
    const output = execSync('node bin/cli.js --help', { encoding: 'utf-8' });
    assert.match(output, /Usage:/);
  });

  it('processes file', () => {
    const output = execSync('node bin/cli.js test.txt', { encoding: 'utf-8' });
    assert.ok(output.length > 0);
  });
});
```

## Publishing

### Local Testing

```bash
npm link
mycli --version
```

### Publishing to npm

```bash
npm publish
```

### Installing from npm

```bash
npm install -g mycli
```

### Using npx (no install)

```bash
npx mycli@latest process file.txt
```
