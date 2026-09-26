#!/usr/bin/env python3
"""Harvest a window of research and development activity into one Markdown digest.

The digest is raw material for the /kb-secbrain collect step: Claude reads it
and distils the learnings into an inbox note. Nothing here writes to the vault.

    collect.py [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--out PATH]

Sources, all local or via the already-authenticated `gh` CLI:
  - Claude Code sessions in ~/.claude/projects/*/*.jsonl (titles, human prompts,
    closing assistant replies, linked PRs and artifacts)
  - Claude memory files (~/.claude/projects/*/memory/*.md) changed in the window
  - commits on every git repo under ~/Desktop/Projects (and Markdown docs they touched)
  - PRs authored by the gh user and merged in the window, with review verdicts
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys

HOME = pathlib.Path.home()
PROJECTS_DIRS = [HOME / "Desktop" / "Projects"]
CLAUDE_PROJECTS = HOME / ".claude" / "projects"
VAULT = pathlib.Path(os.environ.get("KB_SECBRAIN_VAULT", HOME / "Documents" / "SecondBrain"))

MAX_PROMPT = 600       # chars kept per human prompt
MAX_REPLY = 900        # chars kept per closing assistant reply
MAX_TURNS = 12         # human turns kept per session
MAX_BODY = 400         # chars kept per commit/PR body


def run(cmd, cwd=None):
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def clip(text, n):
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def parse_ts(s):
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None


def in_window(ts, since, until):
    return ts is not None and since <= ts < until


# ---------------------------------------------------------------- sessions

def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def is_human_prompt(d):
    if d.get("isSidechain") or d.get("isMeta"):
        return False
    origin = d.get("origin") or {}
    if isinstance(origin, dict) and origin.get("kind") not in (None, "human"):
        return False
    msg = d.get("message") or {}
    content = msg.get("content")
    if isinstance(content, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
        return False
    text = text_of(content).strip()
    return bool(text) and not text.startswith("<")


def sessions(since, until):
    out = []
    for f in sorted(CLAUDE_PROJECTS.glob("*/*.jsonl")):
        mtime = dt.datetime.fromtimestamp(f.stat().st_mtime, dt.timezone.utc)
        if mtime < since:
            continue
        title, cwd, turns, prs, artifacts = None, None, [], {}, {}
        last_reply = None
        try:
            lines = f.open(encoding="utf-8", errors="replace")
        except OSError:
            continue
        with lines:
            for line in lines:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                t = d.get("type")
                if t == "custom-title":
                    title = d.get("customTitle") or title
                elif t == "pr-link" and d.get("prUrl"):
                    prs[d["prUrl"]] = True
                elif t == "frame-link" and d.get("frameUrl"):
                    artifacts[d["frameUrl"]] = d.get("title") or ""
                elif t == "user" and is_human_prompt(d):
                    ts = parse_ts(d.get("timestamp"))
                    if not in_window(ts, since, until):
                        continue
                    if turns and last_reply:
                        turns[-1]["reply"] = last_reply
                    last_reply = None
                    cwd = d.get("cwd") or cwd
                    turns.append({"ts": ts, "prompt": text_of(d["message"].get("content")), "reply": None})
                elif t == "assistant" and turns and not d.get("isSidechain"):
                    txt = text_of((d.get("message") or {}).get("content")).strip()
                    if txt:
                        last_reply = txt
        if not turns:
            continue
        if last_reply:
            turns[-1]["reply"] = last_reply
        out.append({
            "file": f, "title": title or clip(turns[0]["prompt"], 80), "cwd": cwd,
            "start": turns[0]["ts"], "turns": turns, "prs": list(prs), "artifacts": artifacts,
        })
    out.sort(key=lambda s: s["start"])
    return out


# ---------------------------------------------------------------- memory

def memories(since, until):
    rows = []
    for f in sorted(CLAUDE_PROJECTS.glob("*/memory/*.md")):
        if f.name == "MEMORY.md":
            continue
        mtime = dt.datetime.fromtimestamp(f.stat().st_mtime, dt.timezone.utc)
        if in_window(mtime, since, until):
            rows.append((f, f.read_text(encoding="utf-8", errors="replace")))
    return rows


# ---------------------------------------------------------------- git

def repos():
    for base in PROJECTS_DIRS:
        if not base.is_dir():
            continue
        for p in sorted(base.iterdir()):
            if (p / ".git").exists():
                yield p


def commits(repo, since, until):
    fmt = "%x1e%H%x1f%an%x1f%aI%x1f%s%x1f%b"
    raw = run(["git", "log", "--all", "--no-merges", f"--since={since.isoformat()}",
               f"--until={until.isoformat()}", f"--pretty=format:{fmt}", "--name-only"], cwd=repo)
    rows = []
    for chunk in raw.split("\x1e"):
        if not chunk.strip():
            continue
        head, _, files = chunk.partition("\n")
        parts = head.split("\x1f")
        if len(parts) < 5:
            continue
        sha, author, date, subject, body = parts
        docs = [x for x in files.splitlines() if x.lower().endswith((".md", ".mdx"))]
        rows.append({"sha": sha[:8], "date": date[:10], "subject": subject, "body": body, "docs": sorted(set(docs))})
    return rows


# ---------------------------------------------------------------- GitHub

def merged_prs(since, until):
    q = f"merged:{since.date().isoformat()}..{(until - dt.timedelta(seconds=1)).date().isoformat()}"
    raw = run(["gh", "search", "prs", "--author", "@me", "--merged", q, "--limit", "200",
               "--json", "repository,number,title,url,closedAt,body"])
    try:
        prs = json.loads(raw or "[]")
    except ValueError:
        return []
    for pr in prs:
        repo = pr["repository"]["nameWithOwner"]
        rv = run(["gh", "pr", "view", str(pr["number"]), "-R", repo, "--json", "reviews,labels"])
        try:
            info = json.loads(rv or "{}")
        except ValueError:
            info = {}
        pr["repo"] = repo
        pr["labels"] = [l["name"] for l in info.get("labels", [])]
        pr["reviews"] = [
            {"state": r.get("state"), "author": (r.get("author") or {}).get("login"), "body": r.get("body", "")}
            for r in info.get("reviews", []) if r.get("body") or r.get("state") in ("APPROVED", "CHANGES_REQUESTED")
        ]
    prs.sort(key=lambda p: (p["repo"], p["number"]))
    return prs


# ---------------------------------------------------------------- render

def render(since, until):
    w = []
    add = w.append
    add(f"# Raw activity digest {since.date()} → {(until - dt.timedelta(seconds=1)).date()}\n")
    add("Machine-harvested. Distil; do not copy verbatim.\n")

    ss = sessions(since, until)
    add(f"\n## Claude Code sessions ({len(ss)})\n")
    for s in ss:
        where = s["cwd"].replace(str(HOME), "~") if s["cwd"] else "?"
        add(f"\n### {s['title']}\n")
        add(f"- when: {s['start']:%Y-%m-%d %H:%M} UTC · cwd: `{where}` · turns in window: {len(s['turns'])}")
        add(f"- transcript: `{str(s['file']).replace(str(HOME), '~')}`")
        for url in s["prs"]:
            add(f"- PR: {url}")
        for url, title in s["artifacts"].items():
            add(f"- artifact: [{title or 'artifact'}]({url})")
        turns = s["turns"]
        keep = turns if len(turns) <= MAX_TURNS else turns[:3] + turns[-(MAX_TURNS - 3):]
        for t in keep:
            add(f"\n> **KB:** {clip(t['prompt'], MAX_PROMPT)}")
            if t["reply"]:
                add(f">\n> **Claude:** {clip(t['reply'], MAX_REPLY)}")
        if len(turns) > MAX_TURNS:
            add(f"\n_({len(turns) - MAX_TURNS} middle turns omitted)_")

    mem = memories(since, until)
    add(f"\n## Claude memory files changed ({len(mem)})\n")
    for f, body in mem:
        add(f"\n### `{str(f).replace(str(HOME), '~')}`\n\n{body.strip()}\n")

    prs = merged_prs(since, until)
    add(f"\n## Merged PRs ({len(prs)})\n")
    for pr in prs:
        labels = f" [{', '.join(pr['labels'])}]" if pr["labels"] else ""
        add(f"\n- **{pr['repo']}#{pr['number']}** {pr['title']}{labels} — {pr['url']} (merged {pr['closedAt'][:10]})")
        if pr.get("body"):
            add(f"  - body: {clip(pr['body'], MAX_BODY)}")
        for r in pr["reviews"]:
            add(f"  - review {r['state']} by {r['author']}: {clip(r['body'], MAX_BODY)}")

    add("\n## Commits by repo\n")
    for repo in repos():
        rows = commits(repo, since, until)
        if not rows:
            continue
        remote = run(["git", "remote", "get-url", "origin"], cwd=repo).strip()
        add(f"\n### {repo.name} ({len(rows)} commits) {remote}\n")
        docs = sorted({d for r in rows for d in r["docs"]})
        for r in rows:
            add(f"- {r['date']} `{r['sha']}` {r['subject']}" + (f" — {clip(r['body'], 200)}" if r["body"].strip() else ""))
        if docs:
            add(f"- Markdown docs touched: " + ", ".join(f"`{d}`" for d in docs[:40]))

    return "\n".join(w) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", help="YYYY-MM-DD, inclusive (default: 7 days before --until)")
    ap.add_argument("--until", help="YYYY-MM-DD, exclusive (default: tomorrow)")
    ap.add_argument("--out", help="write here instead of stdout")
    a = ap.parse_args()
    tz = dt.timezone.utc
    until = dt.datetime.fromisoformat(a.until).replace(tzinfo=tz) if a.until else \
        dt.datetime.combine(dt.date.today() + dt.timedelta(days=1), dt.time(), tz)
    since = dt.datetime.fromisoformat(a.since).replace(tzinfo=tz) if a.since else until - dt.timedelta(days=7)
    text = render(since, until)
    if a.out:
        pathlib.Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out} ({len(text):,} chars)")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
