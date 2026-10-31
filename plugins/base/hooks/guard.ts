// Pure check for Bash commands. Returns a reason to deny, or undefined to allow.

type Rule = { pattern: RegExp; reason: string }

const RULES: Rule[] = [
  { pattern: /(?<!git )\brm\s+(-[a-zA-Z]*[rf][a-zA-Z]*\s+)+/, reason: 'rm -r/-f deletes without recovery. Move the files to ~/.Trash instead, or ask Keshav.' },
  { pattern: /\bgit\s+push\b[^|;&]*(\s--force\b|\s-f\b|\s--force-with-lease\b)/, reason: 'Force-push rewrites shared history. Ask Keshav.' },
  { pattern: /\bgit\s+reset\s+--hard\b/, reason: 'git reset --hard discards work. Use git stash, or ask Keshav.' },
  { pattern: /\bgit\s+clean\s+-[a-zA-Z]*f/, reason: 'git clean -f deletes untracked files. Ask Keshav.' },
  { pattern: /\bgit\s+branch\s+-D\b/, reason: 'git branch -D deletes an unmerged branch. Ask Keshav.' },
  { pattern: /\bgit\s+checkout\s+--\s+\./, reason: 'git checkout -- . discards all changes. Ask Keshav.' },
  { pattern: /Co-Authored-By:\s*Claude|Generated with \[?Claude Code/i, reason: 'No Claude attribution in commits or PRs. Keshav is the sole author.' },
]

export function checkBash(command: string): string | undefined {
  for (const rule of RULES) {
    if (rule.pattern.test(command)) return rule.reason
  }
  return undefined
}
