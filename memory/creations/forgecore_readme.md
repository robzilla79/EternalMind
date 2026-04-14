# ForgeCore CLI

A minimal CLI tool for local GitHub Actions testing and container management.

## Installation

```bash
# Make executable
chmod +x forgecore_cli.py

# Run directly
python forgecore_cli.py --help

# Or install as CLI tool (optional)
pip install click
ln -s $(pwd)/forgecore_cli.py /usr/local/bin/forgecore
```

## Usage

### Run a workflow locally

```bash
# Run all workflows
forgecore run

# Run specific workflow
forgecore run build

# Run with specific event
forgecore run -e pull_request

# Dry run (see what would execute)
forgecore run --dry-run
```

### View cached logs

```bash
# Show recent runs
forgecore logs

# Filter by workflow
forgecore logs build

# Show more runs
forgecore logs -l 10
```

### Cleanup

```bash
# Remove containers and volumes
forgecore clean
```

### Status

```bash
# Show status and dependencies
forgecore status
```

## Architecture

- **Click** for CLI framework (clean subcommands, argument parsing)
- **subprocess** for docker/act calls (no heavy dependencies)
- **JSON cache** for run history (easy to parse later)
- **File-based logging** to `memory/forgecore_logs/`

## Dependencies

- Python 3.7+
- `click` (pip install click)
- `act` (GitHub Actions runner)
- `docker`

## Notes

- Logs are stored in `memory/forgecore_logs/`
- Cache is stored in `memory/forgecore_cache.json`
- Each run gets a unique ID for tracking
