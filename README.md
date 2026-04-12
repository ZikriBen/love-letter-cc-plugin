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
/plugin marketplace add <your-username>/love-letter
/plugin install love-letter@love-letter
/reload-plugins
```

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
