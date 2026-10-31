# ui (scaffold only, not in the marketplace yet)

Terminal UI customization for Claude Code, built later as a mod (`hooks/register.ts`).

Planned surfaces (see the mods reference, render sites):

- **Project pane** (`Pane`, docked): active project, phase, open decisions, repo paths, buttons
  to switch project.
- **Gate band** (`AbovePrompt`): last verifier verdict and the wave in progress.
- **Context meter**: `$.session.usage()` context percent and rate limits.
- **Spinner suffix** (`Spinner`): the subagent that is running.
- **Lesson toast** (`$.ui.toast`): a tool call that matches a recorded lesson.
- **Theme** (`themes/`): color theme.

Folders: `hooks/` (the mod), `themes/` (theme JSON). Add `.claude-plugin/plugin.json` and a
marketplace entry when work starts.
