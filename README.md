# love-letter

A Claude Code plugin that builds a personal knowledge base from your troubleshooting sessions. Love letters to your future self.

## What it does

When you solve a problem — a CLI quirk, an auth issue, a config gotcha — save it with `/ll save`. Next time you hit the same wall, `/ll search` finds the answer.

## Commands

| Command | What it does |
|---------|-------------|
| `/ll save` | Save a problem/solution from the current conversation |
| `/ll search <description>` | Search the knowledge base for past solutions |
| `/ll list` | Browse all saved entries |

## Install

```bash
/plugin marketplace add ZikriBen/love-letter-cc-plugin
/plugin install love-letter@love-letter
/reload-plugins
```

### Optional: Auto-allow permissions

To skip permission prompts every session, add these to your `~/.claude/settings.json` under `permissions.allow`:

```json
"Read($HOME/.claude/knowledge-base/**)",
"Edit($HOME/.claude/knowledge-base/**)",
"Write($HOME/.claude/knowledge-base/**)",
"Bash(mkdir -p $HOME/.claude/knowledge-base:*)"
```

And add `"$HOME/.claude/knowledge-base"` to `permissions.additionalDirectories`.

## Storage

Everything lives locally at `~/.claude/knowledge-base/`:

```
~/.claude/knowledge-base/
  KBINDEX.md              # Index with one-line summaries
  entries/
    python/               # Categorized entries
    cli/
    infra/
    ...
```

## License

MIT
