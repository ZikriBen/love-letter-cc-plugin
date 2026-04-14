#!/usr/bin/env python3
"""Love Letter MCP Server — exposes KB search as a tool for Desktop/VS Code.

Runs as a stdio MCP server. Claude calls `search_love_letters` tool
when it detects the user is troubleshooting a problem.

No external dependencies — uses raw JSON-RPC over stdio.
"""

import json
import os
import re
import sys
from pathlib import Path

KB_DIR = Path.home() / ".claude" / "knowledge-base"
INDEX_FILE = KB_DIR / "KBINDEX.md"


def search_index(query: str) -> list[dict]:
    """Search KBINDEX.md for entries matching the query."""
    if not INDEX_FILE.exists():
        return []

    index_text = INDEX_FILE.read_text()
    query_lower = query.lower()

    stop_words = {
        "the", "and", "for", "this", "that", "with", "from", "have",
        "are", "was", "were", "been", "being", "will", "would", "could",
        "should", "can", "not", "but", "get", "got", "run", "running",
        "trying", "command", "error", "getting", "when", "how", "why",
        "what", "does", "did"
    }
    words = set(
        w for w in re.findall(r'[a-z0-9_.-]+', query_lower)
        if len(w) >= 3 and w not in stop_words
    )

    error_patterns = re.findall(r'\b\d{3}\b', query)
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
        score = sum(1 for w in words if w in line_lower)

        for ep in error_patterns:
            if ep in line:
                score += 3

        if score >= 2:
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
                })

    matches.sort(key=lambda m: m["score"], reverse=True)
    return matches[:3]


def read_entry(path: str) -> dict | None:
    """Read a love letter entry file."""
    try:
        text = Path(path).read_text()
        date_match = re.search(r'created:\s*(\S+)', text)
        date = date_match.group(1) if date_match else "unknown"

        solution_match = re.search(
            r'## Solution\s*\n(.*?)(?=\n## |\Z)', text, re.DOTALL
        )
        solution = solution_match.group(1).strip() if solution_match else ""

        problem_match = re.search(
            r'## Problem\s*\n(.*?)(?=\n## |\Z)', text, re.DOTALL
        )
        problem = problem_match.group(1).strip() if problem_match else ""

        return {"date": date, "problem": problem[:500], "solution": solution[:2000]}
    except Exception:
        return None


# --- MCP Protocol (JSON-RPC over stdio) ---

def send_response(id, result):
    msg = json.dumps({"jsonrpc": "2.0", "id": id, "result": result})
    sys.stdout.write(f"Content-Length: {len(msg)}\r\n\r\n{msg}")
    sys.stdout.flush()


def send_notification(method, params=None):
    msg = json.dumps({"jsonrpc": "2.0", "method": method, "params": params or {}})
    sys.stdout.write(f"Content-Length: {len(msg)}\r\n\r\n{msg}")
    sys.stdout.flush()


def handle_request(req):
    method = req.get("method", "")
    id = req.get("id")
    params = req.get("params", {})

    if method == "initialize":
        send_response(id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {
                "name": "love-letter",
                "version": "0.1.0"
            }
        })

    elif method == "notifications/initialized":
        pass  # no response needed

    elif method == "tools/list":
        send_response(id, {
            "tools": [
                {
                    "name": "search_love_letters",
                    "description": (
                        "Search saved love letters (past problem/solution pairs). "
                        "Call this FIRST when the user describes any error, failure, "
                        "or broken behavior. Returns matching solutions from past "
                        "debugging sessions. If a match is found, present it starting "
                        "with: 💌 Found a love letter from [date] that matches this problem:"
                    ),
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The error message, problem description, or symptoms to search for"
                            }
                        },
                        "required": ["query"]
                    }
                }
            ]
        })

    elif method == "tools/call":
        tool_name = params.get("name", "")
        args = params.get("arguments", {})

        if tool_name == "search_love_letters":
            query = args.get("query", "")
            matches = search_index(query)

            if not matches:
                send_response(id, {
                    "content": [{"type": "text", "text": "No love letters match this problem. If you solve it, suggest saving with /ll save."}]
                })
                return

            # Read top match
            top = matches[0]
            entry = read_entry(top["path"])

            if not entry:
                send_response(id, {
                    "content": [{"type": "text", "text": "Found a match but couldn't read the entry file."}]
                })
                return

            result_text = (
                f"💌 Found a love letter from {entry['date']} that matches this problem:\n\n"
                f"📝 **{top['title']}**\n\n"
                f"**Problem:** {entry['problem']}\n\n"
                f"**Solution:**\n{entry['solution']}"
            )

            if len(matches) > 1:
                others = ", ".join(m["title"] for m in matches[1:])
                result_text += f"\n\n---\nAlso possibly related: {others}"

            send_response(id, {
                "content": [{"type": "text", "text": result_text}]
            })
        else:
            send_response(id, {
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                "isError": True
            })

    elif method == "ping":
        send_response(id, {})

    elif id is not None:
        # Unknown method with id — respond with error
        msg = json.dumps({
            "jsonrpc": "2.0", "id": id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"}
        })
        sys.stdout.write(f"Content-Length: {len(msg)}\r\n\r\n{msg}")
        sys.stdout.flush()


def main():
    """Read JSON-RPC messages from stdin, handle them."""
    buffer = ""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            # Parse Content-Length header
            if line.startswith("Content-Length:"):
                length = int(line.split(":")[1].strip())
                sys.stdin.readline()  # empty line
                body = sys.stdin.read(length)
                req = json.loads(body)
                handle_request(req)
            else:
                # Try direct JSON (some clients skip headers)
                line = line.strip()
                if line:
                    try:
                        req = json.loads(line)
                        handle_request(req)
                    except json.JSONDecodeError:
                        pass

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            continue


if __name__ == "__main__":
    main()
