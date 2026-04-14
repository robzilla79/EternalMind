#!/usr/bin/env python3
"""
ForgeCore CLI — Local development orchestration for Em workflows.

A minimal CLI wrapper around `act` (GitHub Actions runner) and `docker`
for testing workflows locally before pushing to production.

Usage:
    forgecore run <workflow>      Run a GitHub Actions workflow locally
    forgecore logs <workflow>     View cached logs from previous runs
    forgecore clean              Clean up containers and volumes
"""

import subprocess
import json
import sys
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import click

# Configuration
MEMORY_DIR = Path("memory")
LOGS_DIR = MEMORY_DIR / "forgecore_logs"
CACHE_FILE = MEMORY_DIR / "forgecore_cache.json"

# Ensure directories exist
MEMORY_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


def load_cache() -> dict:
    """Load the forgecore cache."""
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {"runs": []}


def save_cache(cache: dict) -> None:
    """Save the forgecore cache."""
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def log_run(run_id: str, workflow: str, status: str, output: str) -> None:
    """Log a run to both cache and file."""
    timestamp = datetime.now().isoformat()
    
    # File log
    log_filename = LOGS_DIR / f"{workflow}_{run_id}.log"
    with open(log_filename, "w") as f:
        f.write(f"# ForgeCore Run Log\n")
        f.write(f"# Workflow: {workflow}\n")
        f.write(f"# Timestamp: {timestamp}\n")
        f.write(f"# Status: {status}\n")
        f.write(f"#\n")
        f.write(output)
    
    # Cache entry
    cache = load_cache()
    cache["runs"].append({
        "id": run_id,
        "workflow": workflow,
        "timestamp": timestamp,
        "status": status,
        "log_file": str(log_filename)
    })
    save_cache(cache)


def generate_run_id(workflow: str, args: str) -> str:
    """Generate a unique run ID."""
    content = f"{workflow}:{args}:{datetime.now().isoformat()}"
    return hashlib.md5(content.encode()).hexdigest()[:12]


def run_command(cmd: List[str], capture: bool = True) -> tuple:
    """Run a shell command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"


@click.group()
def cli():
    """ForgeCore CLI — Local Actions testing and container management."""
    pass


@cli.command()
@click.argument("workflow", required=False, default="all")
@click.option("--event", "-e", default="push", help="GitHub event to simulate")
@click.option("--dry-run", is_flag=True, help="Show what would be run without executing")
@click.option("--container-architecture", "-a", default="linux/amd64", help="Container architecture")
def run(workflow: str, event: str, dry_run: bool, container_architecture: str):
    """Run a GitHub Actions workflow locally using `act`."""
    
    click.echo(f"🔧 ForgeCore: Running workflow '{workflow}' with event '{event}'")
    
    # Build act command
    act_cmd = ["act", event]
    
    if workflow != "all":
        act_cmd.extend(["-j", workflow])
    
    act_cmd.extend(["-a", container_architecture])
    
    # Dry run check
    if dry_run:
        click.echo(f"Would run: {' '.join(act_cmd)}")
        return
    
    # Check if act is available
    check_code, _, _ = run_command(["which", "act"])
    if check_code != 0:
        click.echo("❌ Error: `act` is not installed or not in PATH.")
        click.echo("   Install with: brew install act  (macOS)")
        click.echo("   Or: go install github.com/nektos/act@latest")
        sys.exit(1)
    
    # Run the command
    click.echo(f"🏃 Running: {' '.join(act_cmd)}")
    returncode, stdout, stderr = run_command(act_cmd)
    
    # Combine output
    full_output = stdout + stderr
    
    # Determine status
    status = "success" if returncode == 0 else "failed"
    
    # Generate run ID
    run_id = generate_run_id(workflow, event)
    
    # Log the run
    log_run(run_id, workflow, status, full_output)
    
    # Print summary
    if returncode == 0:
        click.echo(f"✅ Success! Run ID: {run_id}")
    else:
        click.echo(f"❌ Failed with code {returncode}. Run ID: {run_id}")
        click.echo("   Log saved to memory/forgecore_logs/")
    
    sys.exit(returncode)


@cli.command()
@click.argument("workflow", required=False)
@click.option("--limit", "-l", default=5, help="Number of recent runs to show")
def logs(workflow: Optional[str], limit: int):
    """View cached logs from previous runs."""
    
    cache = load_cache()
    
    if not cache["runs"]:
        click.echo("📭 No cached runs found.")
        return
    
    # Filter by workflow if specified
    runs = cache["runs"]
    if workflow:
        runs = [r for r in runs if r["workflow"] == workflow]
    
    if not runs:
        click.echo(f"📭 No cached runs found for workflow '{workflow}'.")
        return
    
    # Show summary
    click.echo(f"📋 Recent runs (limit {limit}):")
    click.echo("-" * 60)
    
    for run in runs[-limit:]:
        status_icon = "✅" if run["status"] == "success" else "❌"
        click.echo(f"{status_icon} {run['id']} | {run['workflow']} | {run['timestamp']}")
    
    click.echo("-" * 60)
    click.echo(f"Full logs in: {LOGS_DIR}/")


@cli.command()
def clean():
    """Clean up containers and volumes created by act."""
    
    click.echo("🧹 Cleaning up act containers and volumes...")
    
    # Stop and remove containers
    run_command(["docker", "container", "prune", "-f"])
    
    # Remove unused volumes
    run_command(["docker", "volume", "prune", "-f"])
    
    click.echo("✅ Cleanup complete.")


@cli.command()
def status():
    """Show forgecore status and cached runs."""
    
    cache = load_cache()
    
    click.echo("📊 ForgeCore Status")
    click.echo("-" * 40)
    click.echo(f"Memory directory: {MEMORY_DIR.absolute()}")
    click.echo(f"Logs directory: {LOGS_DIR.absolute()}")
    click.echo(f"Cached runs: {len(cache.get('runs', []))}")
    
    # Check dependencies
    click.echo("\n🔍 Dependencies:")
    
    check_code, _, _ = run_command(["which", "act"])
    click.echo(f"  act: {'✅' if check_code == 0 else '❌'}")
    
    check_code, _, _ = run_command(["which", "docker"])
    click.echo(f"  docker: {'✅' if check_code == 0 else '❌'}")


if __name__ == "__main__":
    cli()
