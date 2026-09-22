#!/usr/bin/env python3
"""Run a prepared TrailGoat flythrough manifest sequentially, with resumable logs."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

OUTPUTS = ("hero.mp4", "hero.webm", "hero-phone.mp4", "poster.webp", "contact-sheet.png")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def atomic_json(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    tmp.replace(path)


def load_queue(path, repo):
    data = json.loads(path.read_text())
    entries = data.get("courses")
    if not isinstance(entries, list) or not entries:
        raise ValueError("manifest must contain a nonempty courses list")
    seen = set()
    queue = []
    for entry in entries:
        cid = entry.get("id")
        name = entry.get("name")
        raw_out = entry.get("out")
        if not isinstance(cid, int) or cid <= 0 or not isinstance(name, str) or not name.strip():
            raise ValueError(f"invalid course id or name: {entry!r}")
        if not isinstance(raw_out, str) or not raw_out.strip():
            raise ValueError(f"missing output for course {cid}")
        out = Path(raw_out)
        if not out.is_absolute():
            out = repo / out
        out = out.resolve()
        if out == repo or repo not in out.parents:
            raise ValueError(f"output must be inside TrailGoat checkout: {out}")
        if out in seen:
            raise ValueError(f"duplicate output directory: {out}")
        seen.add(out)
        queue.append((cid, name.strip(), out))
    return queue


def complete(out):
    return all((out / filename).is_file() and (out / filename).stat().st_size > 0 for filename in OUTPUTS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    run = repo / "scripts/flythrough/run.sh"
    if not run.is_file():
        parser.error(f"TrailGoat renderer not found: {run}")
    if not (repo / ".venv/bin/python").is_file():
        parser.error(f"TrailGoat encoder environment missing: {repo / '.venv/bin/python'}")
    queue = load_queue(args.manifest.resolve(), repo)
    for cid, name, out in queue:
        print(f"{cid}: {name} -> {out}", flush=True)
    if args.dry_run:
        return 0
    failures = 0
    for cid, name, out in queue:
        out.mkdir(parents=True, exist_ok=True)
        status_path = out / "batch-status.json"
        log_path = out / "batch-render.log"
        status = {"id": cid, "name": name, "out": str(out), "started_at": now(), "state": "running", "log": str(log_path)}
        if complete(out):
            status["state"] = "complete"
            status["finished_at"] = now()
            status["note"] = "already encoded; skipped"
            atomic_json(status_path, status)
            print(f"SKIP {cid}: outputs already complete", flush=True)
            continue
        atomic_json(status_path, status)
        print(f"START {cid}: {name}", flush=True)
        with log_path.open("a") as log:
            log.write(f"\n=== {now()} course {cid}: {name} ===\n")
            log.flush()
            result = subprocess.run([str(run), str(cid), str(out)], cwd=repo, stdout=log, stderr=subprocess.STDOUT, check=False)
        status["finished_at"] = now()
        status["exit_code"] = result.returncode
        status["state"] = "complete" if result.returncode == 0 and complete(out) else "failed"
        atomic_json(status_path, status)
        print(f"{status['state'].upper()} {cid}: {log_path}", flush=True)
        failures += status["state"] == "failed"
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"batch render: {exc}", file=sys.stderr)
        sys.exit(2)
