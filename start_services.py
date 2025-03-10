#!/usr/bin/env python3
"""
start_services.py

This script starts the Supabase stack first, waits for it to initialize, and then starts
the local AI stack. Both stacks use the same Docker Compose project name ("smart-kit-lm")
so they appear together in Docker Desktop.
"""

import os
import subprocess
import shutil
import time
import argparse

def detect_gpu():
    """Automatically detects the presence of a GPU and returns the appropriate profile."""
    if shutil.which("nvidia-smi"):
        print("✅ NVIDIA GPU detected")
        return "gpu-nvidia"
    elif os.path.exists("/dev/kfd"):
        print("✅ AMD GPU detected")
        return "gpu-amd"
    else:
        print("⚠️ No GPU detected, using CPU")
        return "cpu"

def run_command(cmd, cwd=None):
    """Run a shell command and print it."""
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)

def clone_supabase_repo():
    """Clone the Supabase repository using sparse checkout if not already present."""
    if not os.path.exists("supabase"):
        print("Cloning the Supabase repository...")
        run_command([
            "git", "clone", "--filter=blob:none", "--no-checkout",
            "https://github.com/supabase/supabase.git"
        ])
        os.chdir("supabase")
        run_command(["git", "sparse-checkout", "init", "--cone"])
        run_command(["git", "sparse-checkout", "set", "docker"])
        run_command(["git", "checkout", "master"])
        os.chdir("..")
    else:
        print("Supabase repository already exists, updating...")
        os.chdir("supabase")
        run_command(["git", "pull"])
        os.chdir("..")

def prepare_supabase_env():
    """Copy .env to .env in supabase/docker."""
    env_path = os.path.join("supabase", "docker", ".env")
    env_example_path = os.path.join(".env")
    print("Copying .env in root to .env in supabase/docker...")
    shutil.copyfile(env_example_path, env_path)

def stop_existing_containers():
    """Stop and remove existing containers for our unified project ('smart-kit-lm')."""
    print("Stopping and removing existing containers for the unified project 'smart-kit-lm'...")
    run_command([
        "docker", "compose",
        "-p", "smart-kit-lm",
        "-f", "docker-compose.yml",
        "-f", "supabase/docker/docker-compose.yml",
        "down"
    ])

def start_supabase():
    """Start the Supabase services (using its compose file)."""
    print("Starting Supabase services...")
    run_command([
        "docker", "compose", "-p", "smart-kit-lm", "-f", "supabase/docker/docker-compose.yml", "up", "-d"
    ])

def start_local_ai(profile=None):
    """Start the local AI services (using its compose file)."""
    print("Starting local AI services...")
    cmd = ["docker", "compose", "-p", "smart-kit-lm"]
    if profile and profile != "none":
        cmd.extend(["--profile", profile])
    cmd.extend(["-f", "docker-compose.yml", "up", "-d"])
    run_command(cmd)

def main():
    parser = argparse.ArgumentParser(description='Start the local AI and Supabase services.')
    parser.add_argument('--profile', choices=['cpu', 'gpu-nvidia', 'gpu-amd', 'none'], default=None,
                        help='Profile to use for Docker Compose (default: auto-detect)')
    args = parser.parse_args()

    # Automatic detection if no profile is provided
    profile = args.profile if args.profile else detect_gpu()

    clone_supabase_repo()
    prepare_supabase_env()
    stop_existing_containers()

    # Start Supabase first
    start_supabase()

    # Wait for Supabase to initialize
    print("⌛ Waiting for Supabase to initialize...")
    time.sleep(10)

    # Then, start the AI services
    start_local_ai(profile)

if __name__ == "__main__":
    main()