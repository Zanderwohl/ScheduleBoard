#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path
from shutil import which


def find_mpremote_command(project_dir: Path) -> str:
    """Return the best mpremote command path available.

    Preference order:
      1) MPREMOTE env var if set
      2) .venv/bin/mpremote inside the project
      3) mpremote found on PATH
    """
    env_override = os.environ.get("MPREMOTE")
    if env_override:
        return env_override

    venv_candidate = project_dir / ".venv" / "bin" / "mpremote"
    if venv_candidate.exists() and os.access(venv_candidate, os.X_OK):
        return str(venv_candidate)

    path_cmd = which("mpremote")
    if path_cmd:
        return path_cmd

    raise FileNotFoundError(
        "mpremote not found. Install with 'python3 -m pip install mpremote' (ideally inside .venv)."
    )


def gather_project_files(project_dir: Path, self_name: str) -> list[Path]:
    """Return a list of files in project root to upload.

    Excludes README.md and the script itself. Only files at project root.
    Only include files with extensions: .py, .toml, .properties
    """
    allowed_suffixes = {".py", ".toml", ".properties"}
    files: list[Path] = []
    for entry in project_dir.iterdir():
        if not entry.is_file():
            continue
        name = entry.name
        if name == "README.md":
            continue
        if name == ".gitignore":
            continue
        if name == self_name:
            continue
        if entry.suffix.lower() not in allowed_suffixes:
            continue
        files.append(entry)
    return files


def upload_files_to_pico(files: list[Path], mpremote_cmd: str, device: str | None) -> None:
    """Upload each file to Pico using mpremote cp <src> :<dest>."""
    if not files:
        print("No files to upload.")
        return

    base_cmd = [mpremote_cmd]
    if device:
        base_cmd += ["--device", device]

    # Soft reset first to clear state (best effort)
    try:
        subprocess.run(base_cmd + ["soft-reset"], check=False, capture_output=True)
    except Exception:
        pass

    for path in files:
        dest = f":{path.name}"
        cmd = base_cmd + ["cp", str(path), dest]
        print(f"Uploading {path.name} -> {dest} ...")
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as exc:
            print(f"ERROR uploading {path.name}: {exc}", file=sys.stderr)
            sys.exit(exc.returncode or 1)

    # Optionally soft reset again so new code runs immediately
    try:
        subprocess.run(base_cmd + ["soft-reset"], check=False)
    except Exception:
        pass


def main() -> None:
    project_dir = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(description="Upload project files to Raspberry Pi Pico (MicroPython) using mpremote.")
    parser.add_argument(
        "--device",
        help="Serial device path for the Pico (e.g., /dev/tty.usbmodemXXXX). If omitted, mpremote auto-detects.",
        default=None,
    )
    args = parser.parse_args()

    try:
        mpremote_cmd = find_mpremote_command(project_dir)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    self_name = Path(__file__).name
    files = gather_project_files(project_dir, self_name)
    upload_files_to_pico(files, mpremote_cmd, args.device)
    print("Done.")


if __name__ == "__main__":
    main()


