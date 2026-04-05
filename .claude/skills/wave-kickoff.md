---
name: wave-kickoff
description: Automated wave planning — branch creation, label management, issue labeling, kickoff comments, and execution plan
args: Phase number, Wave number
---

Automate the wave kickoff process for the noorinalabs-isnad-graph project.

## Instructions

### 1. Create the deployments branch

```bash
git fetch origin
git checkout main && git pull origin main
git checkout -b deployments/phase{N}/wave-{M}
git push -u origin deployments/phase{N}/wave-{M}
```

If the branch already exists, check it out and pull latest instead.

### 2. Create wave label

Check if label `p{N}-wave-{M}` exists:

```bash
gh label list --search "p{N}-wave-{M}"
```

If missing, create it:

```bash
gh label create "p{N}-wave-{M}" --description "Phase {N} Wave {M}" --color "8B5CF6"
```

### 3. Collect issue list and assignments

Prompt the user for:
- List of issue numbers for this wave
- Assignee for each issue (FIRSTNAME_LASTNAME label)
- Peer review pairings (reviewer for each engineer)

Validate all assignee labels exist before proceeding:

```bash
gh label list --search "FIRSTNAME"
```

Create any missing labels before applying.

### 4. Label all issues

For each issue, apply the wave label and assignee label:

```bash
gh issue edit {NUMBER} --add-label "p{N}-wave-{M}" --add-label "{FIRSTNAME_LASTNAME}"
```

### 5. Post kickoff comments

Post a kickoff comment on each issue using charter format:

```
Requestor: Fatima.Okonkwo
Requestee: {Assignee.Name}
RequestOrReplied: Request

**Wave {M} Kickoff — Phase {N}**

This issue is assigned to you for p{N}-wave-{M}.
- Peer reviewer: {reviewer name}
- Branch from: `deployments/phase{N}/wave-{M}`
- Branch naming: `{FirstInitial}.{LastName}/{IIII}-{issue-slug}`
- Priority: {hotfix|security|bug|feature} (per charter § Wave Planning & Priority)

Please begin implementation.
```

### 6. Output execution plan

Generate and display a structured execution plan with:
- **Priority ordering:** hotfixes first, then security fixes, then bugs, then features (per charter § Wave Planning & Priority)
- **Issue table:** number, title, assignee, reviewer, priority tier
- **Dependencies:** any cross-PR dependencies identified
- **Estimated parallelism:** which issues can run concurrently

### 7. Report

Present the full plan to the user. Do NOT begin implementation until the user approves.

## What remains manual

- User must approve the execution plan before implementation starts
- User decides which issues to include in the wave
- Cross-team dependency resolution still requires lead coordination
