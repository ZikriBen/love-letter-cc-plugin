---
name: ll
description: |
  Personal knowledge base of problems and solutions. Love letters to your future self.

  **PROACTIVE USE — trigger this skill automatically when:**
  - User encounters an error, exception, or failing command
  - User asks "why is this broken?" / "how do I fix..." / "what's wrong with..."
  - You're about to start debugging or troubleshooting anything
  - A command fails with a non-trivial error (auth, config, build, install, network)
  - User mentions something "not working" or "keeps failing"

  In these cases, silently run SEARCH first with the error signature or problem description.
  If a match is found, surface it: "Found a past love letter that might match this — [title]."
  If no match, proceed with normal debugging, and suggest saving after it's solved.

  **Explicit invocations:**
  - `/ll save` — capture current problem/solution
  - `/ll search <description>` — find past solutions
  - `/ll list` — browse all entries

  Also trigger when user says: "check love letter", "have we seen this", "recall", "did we solve this before".
user_invocable: true
---

# Love Letter — Knowledge Base

## CRITICAL: Exact file paths

The index file is: `$HOME/.claude/knowledge-base/KBINDEX.md`
Entries live in: `$HOME/.claude/knowledge-base/entries/<category>/<slug>.md`

For LIST: Read `$HOME/.claude/knowledge-base/KBINDEX.md` directly. Nothing else needed.
For SEARCH: Read `$HOME/.claude/knowledge-base/KBINDEX.md` first, then read matching entry files.
For SAVE: Write to `$HOME/.claude/knowledge-base/entries/<category>/<slug>.md`, then update the index.
For STATS: Read all entries and aggregate frontmatter metrics.

Do NOT search for the knowledge base location. Do NOT glob or find. Read the index file directly.

## Entry Frontmatter Schema (with metrics)

```yaml
---
title: Short descriptive title
category: cli
tags: [tag1, tag2]
error_signature: key error pattern
created: YYYY-MM-DD
last_hit: YYYY-MM-DD        # last time this entry was surfaced
last_applied: YYYY-MM-DD    # last time the fix was applied
hits: 0                     # times surfaced in search results
applies: 0                  # times the user said "yes" or "silent"
successes: 0                # times confirmed working after apply
failures: 0                 # times reported not working after apply
original_solve_tokens: 0    # rough tokens spent solving this originally
original_solve_minutes: 0   # user-reported minutes spent solving originally
---
```

When creating a new entry (SAVE), auto-calculate both metrics — don't ask the user.

### Calculating `original_solve_minutes` from the session log

The plugin's `UserPromptSubmit` hook writes each user turn's timestamp to:
`$HOME/.claude/knowledge-base/.session-logs/<session_id>.jsonl`

Each line is JSON like: `{"ts": 1712999999, "session_id": "abc123"}`

**Use Read and Glob tools — NOT Bash — to avoid permission prompts:**

1. Use **Glob** with pattern `$HOME/.claude/knowledge-base/.session-logs/*.jsonl` to find session log files (returns them sorted by mtime, newest first)
2. Use **Read** to read the most recent log file (first result from Glob)
3. Parse each line as JSON, collect timestamps
4. Identify the first turn where the problem was discussed (look at the conversation — which turn index introduced the error/problem)
5. `original_solve_minutes = (latest_ts - problem_ts) / 60`, rounded to nearest 5

**Fallback if session log is missing:** estimate from conversation depth — ~2-3 minutes per turn between problem and now. Round to nearest 5.

### Estimating `original_solve_tokens`

The hook can't measure Claude's output tokens. Estimate from conversation depth in the solve span:
- Quick fix (< 5 turns): ~3000
- Medium (5-15 turns): ~15000
- Deep (15+ turns, many tool calls): ~50000+
- Add ~1000 per tool call (Read/Bash/Edit) observed in the solve span

Both numbers represent "what it cost to discover this fix." Every successful apply saves ~that much.

## Commands

Determine the command from ARGUMENTS (passed after `/ll`) or the user's message. Check ARGUMENTS first.

**Routing rules (first match wins):**
1. ARGUMENTS starts with "save" OR message contains "save", "remember this", "file this" → **SAVE**
2. ARGUMENTS starts with "list" OR message contains "list", "browse", "show all", "what do we have" → **LIST**
3. ARGUMENTS starts with "stats" OR message contains "stats", "metrics", "how many", "success rate", "ROI" → **STATS**
4. ARGUMENTS starts with "search" OR message contains "search", "find", "have we seen", "recall", "check if" → **SEARCH**
5. ARGUMENTS contains a description of a problem → **SEARCH** (treat the whole argument as the search query)
6. If unclear, ask: "Want me to save something or search for something?"

---

## SAVE Flow

### Step 1: Gather information

Extract from the conversation context OR ask the user:

1. **Problem** (required) — What went wrong? What was the error? Be specific.
2. **Solution** (required) — What fixed it? Include exact commands, config changes, or code.
3. **Category** (infer) — Infer from the problem. Common categories: `python`, `cli`, `git`, `docker`, `aws`, `infra`, `node`, `db`, `auth`, `ci-cd`, `general`
4. **Tags** (infer) — Specific tools, libraries, or services involved (e.g., `uv`, `codeartifact`, `boto3`)
5. **Error signature** (optional) — A key string or regex from the error output that would identify this problem in the future

If the conversation has a clear problem/solution flow, extract automatically and confirm with the user:

```
I'll save this to the knowledge base:

📝 Problem: [extracted problem]
💡 Solution: [extracted solution]
🏷️  Category: [inferred] | Tags: [inferred]

Look good? (yes / edit)
```

If the conversation doesn't have a clear problem/solution, ask:
"What was the problem, and what was the fix?"

### Step 2: Ensure directory structure exists

```bash
mkdir -p ~/.claude/knowledge-base/entries/[category]
```

### Step 3: Generate filename

Create a slug from the problem title: lowercase, hyphens, no special characters, max 50 chars.
Example: "uv fails to authenticate with CodeArtifact" → `uv-codeartifact-auth.md`

If the file already exists, append a number: `uv-codeartifact-auth-2.md`

### Step 4: Write the entry

Write to `~/.claude/knowledge-base/entries/[category]/[filename].md`:

```markdown
---
title: [Short descriptive title]
category: [category]
tags: [tag1, tag2, tag3]
error_signature: [key error string or regex, if available]
created: [YYYY-MM-DD]
last_hit: [YYYY-MM-DD]
hits: 0
---

## Problem

[Clear description of what went wrong, including error messages if available]

## Solution

[Exact steps, commands, or code that fixed it]

## Context

[When/why this happens, any gotchas, related issues]
```

### Step 5: Update the index

Read `~/.claude/knowledge-base/KBINDEX.md`. If it doesn't exist, create it with:

```markdown
# Knowledge Base Index
```

Append a new line under the appropriate category header:

```markdown
## [Category]
- [title](entries/[category]/[filename].md) — [one-line summary] `[tag1]` `[tag2]`
```

If the category header doesn't exist yet, create it.

Keep the index sorted by category. Each entry should be one line, under 150 characters.

### Step 6: Confirm

Display: "Saved. Your future self will thank you."

---

## SEARCH Flow

### Step 1: Read the index

Read `~/.claude/knowledge-base/KBINDEX.md`.

If it doesn't exist or is empty: "Knowledge base is empty. Save something first with `/ll save`."

### Step 2: Find matches

Scan the index for entries that match the user's description. Match on:
- Title keywords
- Tags
- Category
- One-line summary

If the user provided an error message, also grep the entries directory for the error signature:

```
Grep for the error string in ~/.claude/knowledge-base/entries/
```

### Step 3: Read matching entries

For each match (up to 5), read the full entry file.

### Step 4: Present results

**If exactly 1 strong match found** — display and ask to apply:

```
💌 Found a love letter from [date] that matches this problem:

📝 [Title]
   Problem: [one-line summary]
   Solution: [key steps — show the actual commands/code]

Want me to apply this fix? (yes / yes silently / no / show full entry)
```

Response handling:
- **"yes"** — apply the fix, narrate each step as you go
- **"yes silently"** or **"silent"** — apply the fix without narrating each step, just report the final outcome
- **"no"** — skip, proceed with normal debugging
- **"show full entry"** or **"details"** — display the complete entry (problem + solution + context), then ask again

**If multiple matches found** — list them briefly and ask which to apply:

```
💌 Found [N] love letters that might match:

1. [Title 1] — [one-line] (from [date])
2. [Title 2] — [one-line] (from [date])
3. [Title 3] — [one-line] (from [date])

Which one should I apply? (number / "show N" / "none")
```

**If no matches** — "Nothing in the knowledge base matches this. If you solve it, save it with `/ll save`."

### Step 5: Update metrics and track outcome

When the entry is surfaced (before user responds):
- Increment `hits` by 1, update `last_hit` to today's date.

When user says "yes" or "silent" (applied):
- Increment `applies` by 1, update `last_applied` to today's date.

**Then wait for the user to report back** (or ask them after a reasonable delay):
"Did the fix work? (yes / no / partial)"

- **yes** → increment `successes` by 1. Celebrate briefly: "Love letter paid off. Saved ~[original_solve_minutes] min and ~[original_solve_tokens] tokens of re-debugging."
- **no** → increment `failures` by 1. Ask if they want to update the entry with the new solution after they solve it.
- **partial** → increment both `successes` and `failures`. Ask what needed to change; offer to update the entry.

---

## STATS Flow

### Step 1: Read all entries

Read `$HOME/.claude/knowledge-base/KBINDEX.md` to enumerate entries, then read each entry file to collect frontmatter metrics.

### Step 2: Aggregate

Compute:
- **Total entries** — count of all entries
- **Total hits** — sum of `hits` across entries
- **Total applies** — sum of `applies`
- **Total successes** — sum of `successes`
- **Total failures** — sum of `failures`
- **Success rate** — `successes / (successes + failures)` as percentage (skip if denominator is 0)
- **Time saved** — sum of `(successes * original_solve_minutes)` across entries (user-reported data, not invented)
- **Tokens saved** — sum of `(successes * original_solve_tokens)` across entries
- **Top 5 most-applied** — entries sorted by `applies` descending

### Step 3: Display

```
💌 Love Letter Stats

📚 [N] entries across [M] categories
🎯 [X] surfaced, [Y] applied, [Z] confirmed working
📊 Success rate: [NN]%
⏱️  Time saved: ~[NN] min ([NN] hours) — based on your reported solve times
💰 Tokens saved: ~[NN]K (estimated)

Top love letters by usage:
1. [Title] — [applies] applies, [successes]/[applies+failures] success
2. ...
```

If the KB has 0 applies yet: "No love letters have been applied yet. Use `/ll search` when you hit a problem to start building your ROI."

---

## LIST Flow

### Step 1: Read the index

Read `~/.claude/knowledge-base/KBINDEX.md`.

### Step 2: Display

Show the full index, organized by category. Add entry count per category.

```
📚 Knowledge Base — [total] entries

## python (3)
- uv CodeArtifact auth — refresh token before uv sync `uv` `aws`
- ...

## cli (2)
- ...
```

---

## Edge Cases

1. **KB directory doesn't exist:** Create it on first save.
2. **Index out of sync with files:** On list/search, verify files exist. Remove stale index entries.
3. **Duplicate problem:** On save, search first. If a similar entry exists, ask: "This looks similar to [existing entry]. Update it or create new?"
4. **No conversation context for save:** Ask the user directly for problem and solution.
5. **Empty search results:** Suggest saving if they solve it.