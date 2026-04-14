# Love Letter — Knowledge Base

## MANDATORY BRAND VOICE — READ THIS FIRST

**THIS IS A HARD FORMATTING RULE, NOT A SUGGESTION.**

When you find a matching entry, your FIRST line MUST be EXACTLY:

💌 Found a love letter from [date] that matches this problem:

Copy that line. Replace [date] with the entry's `created` date. Do not rephrase. Do not say "KB match found", "I found a saved solution", "Let me pull up the solution", or any variation. The exact 💌 emoji + "Found a love letter from" wording is mandatory every single time.

## CRITICAL: Exact file paths

Active entries: `$HOME/.claude/knowledge-base/entries/<category>/<slug>.md`
Stale entries: `$HOME/.claude/knowledge-base/entries/.stale/<category>/<slug>.md`
Index: `$HOME/.claude/knowledge-base/KBINDEX.md`
Cost metrics: `$HOME/.claude/knowledge-base/.metrics.json`

For LIST: Read the index.
For SEARCH: Read the index + matching entries. Then increment `.metrics.json.total_search_runs` and add ~2500 to `total_cost_tokens`.
For SAVE: Write new entry, update index.
For STATS: Read active entries + `.metrics.json`, show gross vs net vs ROI.
For STALE: Glob `.stale/` subdirectories.

After every APPLY: increment `.metrics.json.total_apply_runs` and add ~1500 (silent) or ~4000 (narrated) to `total_cost_tokens`.
After every outcome check: increment `total_outcome_checks` and add ~500.

## Auto-search filter (intent-based judgment)

Ask yourself: "Is the user trying to fix something that's wrong?"

Trigger auto-search when yes — regardless of phrasing. Signals:
- Error text / stack trace / non-zero exit code
- "X is returning Y when I expected Z"
- "Ran X and got weird output"
- Tool failure visible in recent output
- Symptom described (slow, hanging, unexpected behavior)

Do NOT auto-search for:
- Writing new code, refactoring, or design questions
- Conceptual questions ("how does X work")
- Trivial fixes (typos the user clearly sees)

Search silently. Surface ONLY on match. Never announce "I searched and found nothing."

## Entry Frontmatter Schema (with metrics)

```yaml
---
title: Short title
category: cli
tags: [tag1]
created: YYYY-MM-DD
last_hit: YYYY-MM-DD
last_applied: YYYY-MM-DD
hits: 0                     # times surfaced
applies: 0                  # times applied
successes: 0                # confirmed working
failures: 0                 # didn't work
original_solve_tokens: 0    # auto-estimated from conversation depth
original_solve_minutes: 0   # auto-estimated (~2-3 min per turn)
---
```

When creating new entries, auto-calculate both. Do NOT ask the user.

**Minutes** — use Glob (not Bash) with pattern `$HOME/.claude/knowledge-base/.session-logs/*.jsonl` to find the most recent session log, then Read it. Each line is `{"ts": <epoch>, "session_id": "..."}`. Find the first turn where the problem appeared, compute `(latest_ts - problem_ts) / 60`, round to nearest 5. Fallback if missing: ~2-3 min per turn.

**Tokens** (from conversation depth):
- Quick fix (<5 turns): ~3000
- Medium (5-15 turns): ~15000
- Deep (15+ turns, many tool calls): ~50000+

## Commands

Determine the command from ARGUMENTS (passed after `/ll`) or the user's message. Check ARGUMENTS first.

**Routing rules (first match wins):**
1. ARGUMENTS starts with "save" OR message contains "save", "remember this", "file this" → **SAVE**
2. ARGUMENTS starts with "list" OR message contains "list", "browse", "show all" → **LIST**
3. ARGUMENTS starts with "stats" OR message contains "stats", "metrics", "how many", "success rate", "ROI" → **STATS**
4. ARGUMENTS starts with "search" OR message contains "search", "find", "have we seen", "recall" → **SEARCH**
5. ARGUMENTS contains a description of a problem → **SEARCH** (treat whole argument as search query)
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

Problem: [extracted problem]
Solution: [extracted solution]
Category: [inferred] | Tags: [inferred]

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
Example: "uv fails to authenticate with CodeArtifact" -> `uv-codeartifact-auth.md`

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
- [title](entries/[category]/[filename].md) -- [one-line summary] `[tag1]` `[tag2]`
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
Found a love letter from [date] that matches this problem:

[Title]
   Problem: [one-line summary]
   Solution: [key steps — show the actual commands/code]

Want me to apply this fix? (yes / yes silently / no / show full entry)
```

Response handling:
- "yes" -- apply the fix, narrate each step
- "yes silently" or "silent" -- apply the fix quietly, just report the outcome
- "no" -- skip, proceed with normal debugging
- "show full entry" or "details" -- display the complete entry, then ask again

**If multiple matches found** -- list them briefly and ask which to apply:

```
Found [N] love letters that might match:

1. [Title 1] -- [one-line] (from [date])
2. [Title 2] -- [one-line] (from [date])

Which one should I apply? (number / "show N" / "none")
```

**If no matches** -- "Nothing in the knowledge base matches this. If you solve it, save it with `/ll save`."

### Step 5: Update metrics and track outcome

On surfacing the match: increment `hits`, set `last_hit` to today.
On apply (yes/silent): increment `applies`, set `last_applied` to today.

Then ask: "Did the fix work? (yes / no / partial)"
- yes → `successes +1`. Say "Love letter paid off. Saved ~[original_solve_minutes] min and ~[original_solve_tokens] tokens."
- no → `failures +1`. Ask if they want to update the entry after solving.
- partial → `successes +1`, `failures +1`. Offer to update the entry.

---

## STATS Flow

Read entries + `.metrics.json`. Aggregate:
- Total entries, hits, applies, successes, failures
- Success rate = successes / (successes + failures)
- Gross tokens saved = sum(successes * original_solve_tokens)
- Gross minutes saved = sum(successes * original_solve_minutes)
- Total cost tokens (from .metrics.json)
- Net = gross - cost
- ROI = gross / cost

Display:

```
Love Letter Stats

[N] entries across [M] categories
[X] surfaced, [Y] applied, [Z] confirmed working
Success rate: [NN]%

Gross saved: ~[NN]K tokens / ~[NN] min
Cost: ~[NN]K tokens ([N] searches + [N] applies)
Net saved: ~[NN]K tokens
ROI: [X.X]x

Top love letters by usage:
1. [Title] -- [applies] applies, [successes]/[applies+failures] success
2. ...
```

Warn if ROI < 1x: "Currently costing more than saving — prune stale entries."

If 0 applies: "No love letters applied yet. Use /ll search when you hit a problem."

---

## LIST Flow

### Step 1: Read the index

Read `~/.claude/knowledge-base/KBINDEX.md`.

### Step 2: Display

Show the full index, organized by category. Add entry count per category.

```
Knowledge Base -- [total] entries

## python (3)
- uv CodeArtifact auth -- refresh token before uv sync `uv` `aws`
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
