# Love Letter — Knowledge Base

## CRITICAL: Exact file paths

The index file is: `$HOME/.claude/knowledge-base/KBINDEX.md`
Entries live in: `$HOME/.claude/knowledge-base/entries/<category>/<slug>.md`

For LIST: Read `$HOME/.claude/knowledge-base/KBINDEX.md` directly. Nothing else needed.
For SEARCH: Read `$HOME/.claude/knowledge-base/KBINDEX.md` first, then read matching entry files.
For SAVE: Write to `$HOME/.claude/knowledge-base/entries/<category>/<slug>.md`, then update the index.

Do NOT search for the knowledge base location. Do NOT glob or find. Read the index file directly.

## Commands

Determine the command from ARGUMENTS (passed after `/ll`) or the user's message. Check ARGUMENTS first.

**Routing rules (first match wins):**
1. ARGUMENTS starts with "save" OR message contains "save", "remember this", "file this" → **SAVE**
2. ARGUMENTS starts with "list" OR message contains "list", "browse", "show all", "what do we have" → **LIST**
3. ARGUMENTS starts with "search" OR message contains "search", "find", "have we seen", "recall", "check if" → **SEARCH**
4. ARGUMENTS contains a description of a problem → **SEARCH** (treat the whole argument as the search query)
5. If unclear, ask: "Want me to save something or search for something?"

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

If matches found:

```
Found [N] match(es):

[Title 1]
   Category: [cat] | Tags: [tags] | Saved: [date] | Hits: [N]
   Problem: [one-line summary]
   Solution: [key steps]

[Title 2]
   ...
```

Then ask: "Want me to apply any of these?"

Update the `last_hit` date and increment `hits` counter in matched entry files.

If no matches: "Nothing in the knowledge base matches this. If you solve it, save it with `/ll save`."

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
