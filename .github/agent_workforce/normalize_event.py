#!/usr/bin/env python3
"""Normalize a GitHub Actions event into a non-secret monitor payload."""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise SystemExit("GITHUB_EVENT_PATH is required")
    with open(event_path, encoding="utf-8") as fh:
        event = json.load(fh)
    raw = json.dumps(event, sort_keys=True, separators=(",", ":")).encode()
    payload = {
        "schema_version": 1,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "event": os.environ.get("GITHUB_EVENT_NAME"),
        "action": event.get("action"),
        "repository": os.environ.get("GITHUB_REPOSITORY"),
        "ref": os.environ.get("GITHUB_REF"),
        "before": event.get("before"),
        "after": event.get("after") or event.get("sha"),
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
        "sender": (event.get("sender") or {}).get("login"),
        "pull_request": None,
        "payload_sha256": hashlib.sha256(raw).hexdigest(),
    }
    pr = event.get("pull_request")
    if pr:
        payload["pull_request"] = {
            "number": pr.get("number") or event.get("number"),
            "title": pr.get("title"),
            "state": pr.get("state"),
            "draft": pr.get("draft"),
            "head_branch": (pr.get("head") or {}).get("ref"),
            "head_sha": (pr.get("head") or {}).get("sha"),
            "base_branch": (pr.get("base") or {}).get("ref"),
            "url": pr.get("html_url"),
        }
    with open(args.output, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


if __name__ == "__main__":
    main()
