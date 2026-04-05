---
name: team-reset
description: Transparent team teardown and recreation — handles unresponsive agents, reports roster changes
---

Handle the team teardown/create lifecycle for the noorinalabs-isnad-graph project.

## Instructions

### 1. Report current team state

Read the current team roster from `.claude/team/roster/` and report to the user:

```
**Current team: noorinalabs-isnad-graph**
| Role | Name | Status |
|------|------|--------|
| Manager | Fatima Okonkwo | Active |
| ... | ... | ... |
```

List all active roster members with their roles and status.

### 2. Send shutdown requests

Send a `shutdown_request` message to ALL active agents:

```json
{"type": "shutdown_request", "reason": "Team reset initiated"}
```

Wait 5 seconds for agents to acknowledge.

### 3. Force teardown if needed

If `TeamDelete` fails with "Cannot cleanup team with N active members":

1. Report to user: "Force teardown required — {N} agents unresponsive"
2. Manually edit the config file to remove stale members:
   ```bash
   # Read current config
   cat ~/.claude/teams/noorinalabs-isnad-graph/config.json
   # Keep only team-lead entry, remove all others
   ```
3. Retry `TeamDelete`

### 4. Delete the team

Call `TeamDelete` for team `noorinalabs-isnad-graph`. Report success or failure to user.

```
**Team deleted:** noorinalabs-isnad-graph
- Agents terminated: {count}
- Force removal required: {yes/no}
```

### 5. Create new team

Read all roster files in `.claude/team/roster/` to build the new roster. Call `TeamCreate` for team `noorinalabs-isnad-graph`.

Report to user:

```
**Team created:** noorinalabs-isnad-graph
| Role | Name | Status |
|------|------|--------|
| Manager | Fatima Okonkwo | Active |
| ... | ... | ... |
```

### 6. Highlight roster changes

If there are differences between the old and new team (hires, departures, role changes), explicitly report them:

```
**Roster changes:**
- DEPARTED: {name} ({role}) — {reason}
- HIRED: {name} ({role}) — replacing {departed name}
- ROLE CHANGE: {name} — {old role} → {new role}
```

If no changes: "Roster unchanged from previous team."

### 7. Ready confirmation

Confirm the team is ready for work:

```
Team `noorinalabs-isnad-graph` is ready. {N} members active.
Proceed with agent spawning when ready.
```

## What remains manual

- The orchestrating Claude instance must still spawn individual agents (agents cannot self-spawn)
- Roster file changes (hires/fires) must be committed separately
- The user may override the roster before TeamCreate if desired

## Emergency override

If the skill fails entirely, the manual fallback is:

```bash
# Remove stale config
rm ~/.claude/teams/noorinalabs-isnad-graph/config.json
# Recreate via TeamCreate
```
