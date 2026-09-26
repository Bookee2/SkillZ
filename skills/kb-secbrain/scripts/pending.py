#!/usr/bin/env python3
"""List inbox files the vault has not ingested yet.

A file counts as ingested once its SHA-256 appears in `.raw/.manifest.json`
or the source ledger; that is the vault's own dedupe key, so nothing is ever
ingested twice and the inbox itself stays untouched.

    pending.py [--vault PATH] [--json]

Output is grouped by kind (note, document, notebook, data, asset), newest
first within each, so a bounded run takes this week's notes before older
backlog. Assets (images, video, archives) are supporting files for a note, not
sources in their own right.
"""
import argparse
import hashlib
import json
import os
import pathlib

SKIP_NAMES = {".DS_Store", "Thumbs.db"}
SKIP_DIRS = {".git", ".obsidian", "node_modules"}
KINDS = {
    "note": {".md", ".txt"},
    "document": {".pdf", ".docx", ".pptx", ".html"},
    "notebook": {".ipynb"},
    "data": {".csv", ".xlsx", ".json"},
}


def kind_of(path):
    ext = path.suffix.lower()
    return next((k for k, exts in KINDS.items() if ext in exts), "asset")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def known_hashes(vault):
    hashes = set()
    manifest = vault / ".raw" / ".manifest.json"
    if manifest.exists():
        for rec in json.loads(manifest.read_text()).get("sources", {}).values():
            if rec.get("hash"):
                hashes.add(rec["hash"])
    ledger = vault / "wiki" / "meta" / "ledgers" / "source-ledger.json"
    if ledger.exists():
        data = json.loads(ledger.read_text()).get("sources", [])
        for rec in data.values() if isinstance(data, dict) else data:
            if rec.get("content_sha256"):
                hashes.add(rec["content_sha256"])
    return hashes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default=os.environ.get("KB_SECBRAIN_VAULT", pathlib.Path.home() / "Documents" / "SecondBrain"))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    vault = pathlib.Path(a.vault).expanduser()
    inbox = vault / json.loads((vault / ".claude-obsidian.json").read_text()).get("source_inbox", "inbox")
    known = known_hashes(vault)

    rows = []
    for root, dirs, files in os.walk(inbox):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            if name in SKIP_NAMES or name.startswith("."):
                continue
            p = pathlib.Path(root) / name
            digest = sha256(p)
            if digest in known:
                continue
            st = p.stat()
            rows.append({"path": str(p.relative_to(vault)), "kind": kind_of(p), "sha256": digest, "bytes": st.st_size, "mtime": st.st_mtime})
    order = list(KINDS) + ["asset"]
    rows.sort(key=lambda r: (order.index(r["kind"]), -r["mtime"]))

    if a.json:
        print(json.dumps(rows, indent=1))
        return
    counts = {k: sum(r["kind"] == k for r in rows) for k in order}
    print(f"{len(rows)} un-ingested file(s) in {inbox.relative_to(vault)}/: "
          + ", ".join(f"{n} {k}" for k, n in counts.items() if n))
    for r in rows:
        print(f"  {r['kind']:<9} {r['bytes']:>11,}  {r['path']}")


if __name__ == "__main__":
    main()
