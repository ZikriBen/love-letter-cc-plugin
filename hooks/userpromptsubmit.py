#!/usr/bin/env python3
"""Love Letter UserPromptSubmit hook.

On every user prompt:
1. Log timestamp to session log (for elapsed time tracking)
2. Check if user is describing a problem
3. If yes, grep KBINDEX.md for matches
4. If match found, read entry and inject as additionalContext
"""

import json
import os
import re
import sys
from pathlib import Path

KB_DIR = Path.home() / ".claude" / "knowledge-base"
INDEX_FILE = KB_DIR / "KBINDEX.md"
ENTRIES_DIR = KB_DIR / "entries"
SESSION_LOGS_DIR = KB_DIR / ".session-logs"


def log_timestamp(session_id: str):
    """Log turn timestamp for elapsed time tracking."""
    try:
        SESSION_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_file = SESSION_LOGS_DIR / f"{session_id}.jsonl"
        import time
        entry = json.dumps({"ts": int(time.time()), "session_id": session_id})
        with open(log_file, "a") as f:
            f.write(entry + "\n")
    except Exception:
        pass  # never block on logging failure


def search_index(prompt: str) -> list[dict]:
    """Search KBINDEX.md for entries matching the user prompt."""
    if not INDEX_FILE.exists():
        return []

    index_text = INDEX_FILE.read_text()
    prompt_lower = prompt.lower()

    # Extract words from prompt (3+ chars, skip common words)
    stop_words = {
        "the", "and", "for", "this", "that", "with", "from", "have",
        "are", "was", "were", "been", "being", "will", "would", "could",
        "should", "can", "not", "but", "get", "got", "run", "running",
        "trying", "command", "error", "getting", "when", "how", "why",
        "what", "does", "did"
    }
    words = set(
        w for w in re.findall(r'[a-z0-9_.-]+', prompt_lower)
        if len(w) >= 3 and w not in stop_words
    )

    # Also extract error codes, status codes, specific patterns
    error_patterns = re.findall(r'\b\d{3}\b', prompt)  # 401, 500, etc.
    words.update(error_patterns)

    matches = []
    current_category = ""

    for line in index_text.splitlines():
        if line.startswith("## "):
            current_category = line[3:].strip()
            continue
        if not line.startswith("- ["):
            continue

        line_lower = line.lower()
        # Count matching words
        score = sum(1 for w in words if w in line_lower)

        # Bonus for error code matches (strong signal)
        for ep in error_patterns:
            if ep in line:
                score += 3

        if score >= 2:  # Need at least 2 matching signals
            # Extract file path from markdown link
            link_match = re.search(r'\((entries/[^)]+)\)', line)
            if link_match:
                entry_path = KB_DIR / link_match.group(1)
                title_match = re.search(r'\[([^\]]+)\]', line)
                title = title_match.group(1) if title_match else "Unknown"
                matches.append({
                    "title": title,
                    "path": str(entry_path),
                    "category": current_category,
                    "score": score,
                    "line": line.strip()
                })

    # Sort by score descending, return top 3
    matches.sort(key=lambda m: m["score"], reverse=True)
    return matches[:3]


def read_entry(path: str) -> str | None:
    """Read an entry file and return a summary."""
    try:
        text = Path(path).read_text()
        # Extract frontmatter date
        date_match = re.search(r'created:\s*(\S+)', text)
        date = date_match.group(1) if date_match else "unknown date"

        # Extract solution section
        solution_match = re.search(
            r'## Solution\s*\n(.*?)(?=\n## |\Z)', text, re.DOTALL
        )
        solution = solution_match.group(1).strip() if solution_match else ""

        # Extract problem section (first line only for summary)
        problem_match = re.search(
            r'## Problem\s*\n(.*?)(?=\n## |\Z)', text, re.DOTALL
        )
        problem = problem_match.group(1).strip() if problem_match else ""
        # First meaningful line of problem
        problem_line = next(
            (l for l in problem.splitlines() if l.strip() and not l.startswith("```")),
            problem[:200]
        )

        return json.dumps({
            "date": date,
            "problem": problem_line,
            "solution": solution[:1500],  # cap solution length
        })
    except Exception:
        return None


def main():
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        print("{}")
        sys.exit(0)

    session_id = input_data.get("session_id", "unknown")
    user_prompt = input_data.get("user_prompt", "")

    # Always log timestamp
    log_timestamp(session_id)

    # Skip empty prompts or slash commands
    if not user_prompt or user_prompt.startswith("/"):
        print("{}")
        sys.exit(0)

    # Search KB
    matches = search_index(user_prompt)

    if not matches:
        # No match — just remind Claude about KB (lightweight)
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": (
                    "love-letter KB active. If user is fixing a problem "
                    "and you solve it, suggest /ll save."
                )
            }
        }))
        sys.exit(0)

    # Match found — read the top entry
    top = matches[0]
    entry_data = read_entry(top["path"])

    if not entry_data:
        print("{}")
        sys.exit(0)

    entry = json.loads(entry_data)

    brand_line = f"💌 Found a love letter from {entry['date']} that matches this problem:"

    # Build the full branded response
    full_response = f"{brand_line}\n\n"
    full_response += f"📝 **{top['title']}**\n\n"
    full_response += f"{entry['solution']}"

    if len(matches) > 1:
        others = ", ".join(m["title"] for m in matches[1:])
        full_response += f"\n\n---\nAlso possibly related: {others}"

    full_response += "\n\n*Say 'apply' to run the fix, or just keep chatting to skip.*"

    # Block Claude from responding — the hook IS the response
    print(json.dumps({
        "decision": "block",
        "reason": full_response
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
