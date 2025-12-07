---
name: prevent-search-tool-usage
enabled: true
event: all
pattern: Search|search
action: block
---

⚠️ **SEARCH TOOL DETECTED - BLOCKED**

You attempted to use the Search tool, but it's currently broken and should not be used.

**Why this is blocked:**
- The Search tool is not functioning correctly
- You explicitly requested: "Search tool is broken, use alternative search methods"
- This restriction applies globally to all Claude Code instances and subagents

**Alternative Search Methods to Use:**
- **morph-mcp edit_file** - For code search and file operations
- **desktop-commander start_search** - For file system searches
- **grep commands** - Traditional pattern matching via terminal
- **Glob tool** - For file pattern matching
- **Read/Grep/MCP search tools** - For code analysis

**Example Alternatives:**
Instead of: Search("pattern", file_path)
Use: Grep("pattern", file_path) or desktop-commander search

Instead of: Find files via Search
Use: Glob("*.py") or desktop-commander list_directory

**This rule applies to:**
- All tool usage in this session
- All subagent operations
- All future Claude Code interactions

Please use the alternative search methods listed above.
