#!/usr/bin/env python3
"""Run a prepared TrailGoat flythrough manifest sequentially, with resumable logs."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

OUTPUTS = ("hero.mp4", "hero.webm", "hero-phone.mp4", "poster.webp", "contact-sheet.png")
FPS = 24
# kb/s ceilings: Perpetua Coast (the reference film) plus 15 % headroom
BUDGET_KBPS = {"hero-phone.mp4": 770, "hero.webm": 1240, "hero.mp4": 1875}


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


def frame_count(out):
    frames = out / "frames"
    return sum(1 for f in frames.glob("f_*.png")) if frames.is_dir() else 0


def budget(out):
    """{file: {"mb", "kbps"}} plus the files over their bitrate ceiling."""
    secs = frame_count(out) / FPS
    sizes, over = {}, []
    for name, ceiling in BUDGET_KBPS.items():
        path = out / name
        if not path.is_file() or not secs:
            continue
        kbps = path.stat().st_size * 8 / 1000 / secs
        sizes[name] = {"mb": round(path.stat().st_size / 1e6, 1), "kbps": round(kbps)}
        if kbps > ceiling:
            over.append(f"{name} {kbps:.0f} kb/s > {ceiling}")
    return sizes, over


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--reencode", action="store_true", help="re-run encode.py on rendered frames; never renders")
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
        if args.reencode:
            if not frame_count(out):
                status.update(state="failed", finished_at=now(), note="no rendered frames to re-encode")
                atomic_json(status_path, status)
                print(f"FAILED {cid}: no frames under {out / 'frames'}", flush=True)
                failures += 1
                continue
            cmd = [str(repo / ".venv/bin/python"), str(repo / "scripts/flythrough/encode.py"), str(out)]
        elif complete(out):
            status["state"] = "complete"
            status["finished_at"] = now()
            status["note"] = "already encoded; skipped"
            status["files"], status["over_budget"] = budget(out)
            atomic_json(status_path, status)
            print(f"SKIP {cid}: outputs already complete", flush=True)
            continue
        else:
            cmd = [str(run), str(cid), str(out)]
        atomic_json(status_path, status)
        print(f"START {cid}: {name}", flush=True)
        with log_path.open("a") as log:
            log.write(f"\n=== {now()} course {cid}: {name} ===\n")
            log.flush()
            result = subprocess.run(cmd, cwd=repo, stdout=log, stderr=subprocess.STDOUT, check=False)
        status["finished_at"] = now()
        status["exit_code"] = result.returncode
        status["state"] = "complete" if result.returncode == 0 and complete(out) else "failed"
        status["files"], status["over_budget"] = budget(out)
        atomic_json(status_path, status)
        print(f"{status['state'].upper()} {cid}: {log_path}", flush=True)
        for line in status["over_budget"]:
            print(f"  OVER BUDGET {cid}: {line}", flush=True)
        failures += status["state"] == "failed"
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"batch render: {exc}", file=sys.stderr)
        sys.exit(2)
