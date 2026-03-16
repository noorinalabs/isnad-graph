# Agent Teams Improvements

This document captures lessons learned, proposed tooling improvements, and a genericization plan based on 7 phases of operation of the isnad-graph simulated team. It is written by Fatima Okonkwo (Manager) as a retrospective analysis of team process and tooling gaps.

---

## Table of Contents

1. [Skills to Create](#skills-to-create)
2. [Hooks to Create](#hooks-to-create)
3. [Deterministic Tooling (Scripts > AI)](#deterministic-tooling-scripts--ai)
4. [Agent Naming Convention](#agent-naming-convention)
5. [Persona Utilization Audit](#persona-utilization-audit)
6. [Team Reorganization Recommendations](#team-reorganization-recommendations)
7. [Genericization Plan](#genericization-plan)

---

## Skills to Create

Skills are reusable Claude Code slash commands (`.claude/skills/`) that encode repeatable multi-step workflows. Each skill below replaces a pattern that was performed ad-hoc by agents across Phases 0-7, often inconsistently.

### `/retro` -- Wave Retrospective Automation

**Trigger:** Invoked by the Manager at the end of each wave, after all PRs are merged into the deployments branch.

**Inputs:**
- Phase number
- Wave number
- (Optional) list of PR numbers to include (defaults to all PRs targeting `deployments/phase{N}/wave-{M}`)

**Outputs:**
- A markdown retrospective document at `docs/retros/phase{N}-wave{M}-retro.md`
- Structured sections: What Went Well, What Went Poorly, Action Items, Metrics (PRs merged, issues closed, tech debt created vs resolved)
- Each team member who contributed to the wave gets a summary of their work

**What it automates:**
- Collects all PRs merged into the wave's deployments branch via `gh pr list`
- Collects all issues closed during the wave
- Collects all tech debt issues created during the wave
- Counts CI failures per PR (via `gh run list`)
- Generates the retro template pre-filled with data
- The Manager then edits/supplements with qualitative observations before finalizing

**Why:** Retros were performed in Phases 5, 6, and 7 but the process was manual each time. The Manager had to re-discover the PR list, issue list, and format each time. This led to inconsistent retro depth and occasional omissions. Phase 0-4 had no retros at all.

---

### `/wave-start` -- Wave Initialization

**Trigger:** Invoked by the Manager when beginning a new wave of work.

**Inputs:**
- Phase number
- Wave number
- Base branch (defaults to `main`)

**Outputs:**
- Creates `deployments/phase{N}/wave-{M}` branch from latest base
- Runs `git worktree prune` to clean up stale worktrees from prior waves
- Lists any open issues from prior waves that were not closed (stale issue check)
- If this is Wave 1 of a new phase, checks that the prior phase's deployments branch has been merged to main

**What it automates:**
- Branch creation (previously done manually by the Manager or Tomasz, sometimes with merge conflicts because the base was stale)
- Worktree cleanup (frequently forgotten -- see Phase 4 Wave 2 where branch locks from Phase 3 worktrees blocked checkouts)
- Stale issue detection (issues from prior waves that should have been closed on merge but were not)

**Why:** Wave startup was the most error-prone manual step. In Phase 3, the deployments branch was created from a stale main. In Phase 5, worktree pruning was skipped and caused branch lock errors for 3 agents. This skill makes wave startup deterministic.

---

### `/wave-end` -- Wave Completion

**Trigger:** Invoked by the Manager when all PRs for a wave are merged into the deployments branch.

**Inputs:**
- Phase number
- Wave number

**Outputs:**
- Runs `/retro` for the wave
- Verifies all issues referenced in merged PRs are closed; closes any that are not
- Runs `git worktree prune`
- If this is the final wave of a phase: creates a PR from the deployments branch to `main` for user review
- Scans docs/ for any files that reference outdated phase information

**What it automates:**
- The full wave completion checklist that the Manager currently performs manually
- Issue closure verification (a persistent gap -- see `.claude/projects/-home-parameterization-code-isnad-graph/memory/feedback_close_issues.md`)
- Worktree cleanup
- Phase-end PR creation

**Why:** Wave-end was inconsistently executed. Issues were frequently left open after merges (the user had to remind us to close them). Worktree pruning was forgotten in 4 out of 7 phases. The phase-end PR was sometimes created by Fatima, sometimes by Tomasz, with different formats.

---

### `/review-pr {number}` -- Charter-Format PR Review

**Trigger:** Invoked by any team member assigned to review a PR.

**Inputs:**
- PR number
- Reviewer name (persona from roster)

**Outputs:**
- Posts a structured review comment on the PR with sections:
  - **Must-fix items** (blocks merge)
  - **Tech debt items** (does not block merge)
  - **Observations** (informational)
- For each tech debt item: creates a GitHub Issue with labels `tech-debt` + the submitter's `FIRSTNAME_LASTNAME` label + `found-in-phase-{N}` label
- Review comment follows the charter format (Requestor/Requestee/RequestOrReplied)

**What it automates:**
- Consistent review format (reviews in Phases 0-3 had no standard structure; the charter format was adopted in Phase 4 but still inconsistently applied)
- Automatic tech debt issue creation (previously done manually after review, often forgotten -- the user had to institute a policy that every review MUST produce tech debt issues)
- Ensures tech debt issues have correct labels

**Why:** Tech debt tracking was the single most-corrected process item. The user gave explicit feedback that every code review must produce GitHub Issues for tech-debt items. Despite this, multiple waves had tech debt comments on PRs that were never filed as issues. Automating the filing eliminates this gap.

---

### `/plan-phase {number}` -- Phase Planning

**Trigger:** Invoked by the Manager at the start of a new phase.

**Inputs:**
- Phase number
- Path to the phase's instruction document (e.g., `docs/phase{N}-claude-code-instructions.md`)

**Outputs:**
- Decomposes the phase document into GitHub Issues with:
  - Titles following the pattern `Phase {N}: {description}`
  - Acceptance criteria extracted from the spec
  - Labels: `phase-{N}`, priority label, assignee label
  - Dependencies noted in issue body
- Presents the issue list to the Manager for review before creation
- After Manager approval, creates all issues
- Triggers the review process (notifies Renaud, Sunita, Elena, Dmitri, Priya)

**What it automates:**
- The phase decomposition step that currently takes 30+ minutes of the Manager's time
- Ensures consistent issue format and labeling
- Ensures the review gate (charter requirement: all issues must be reviewed before implementation begins)

**Why:** Phase planning quality varied significantly. Phase 0 had well-structured issues; Phase 4 had issues created mid-wave when scope was discovered late. Automating decomposition from the spec document ensures completeness.

---

### `/close-stale-issues` -- Stale Issue Audit

**Trigger:** Invoked by the Manager on-demand, recommended at wave boundaries.

**Inputs:**
- (Optional) phase number to scope the audit

**Outputs:**
- Lists all open issues whose referenced PR has been merged
- Lists all open issues with no activity in the last 2 waves
- For merged-PR issues: closes them with a comment noting the closing PR
- For stale issues: flags them for Manager review (does not auto-close)

**What it automates:**
- The issue hygiene check that was frequently skipped
- Cross-references merged PRs with their `Closes #N` references to find issues that should have been closed

**Why:** As of Phase 7, there are 30+ open issues, many of which reference work that has been completed. Issue #220 is a "tech debt batch" that was partially addressed but never updated. Multiple Phase 6 tech debt issues were carried forward to Phase 7 without updating labels. This skill prevents issue rot.

---

## Hooks to Create

Hooks are shell commands that execute automatically in response to Claude Code events. They enforce process without requiring agent memory or discipline.

### Post-Commit Hook: Auto Ruff Format

**Trigger:** After every `git commit`

**Action:**
```bash
#!/usr/bin/env bash
# Run ruff format on staged Python files
changed_files=$(git diff --name-only HEAD~1 HEAD -- '*.py')
if [ -n "$changed_files" ]; then
    uv run ruff format $changed_files
    uv run ruff check --fix $changed_files
    git add $changed_files
    # Amend the commit silently if formatting changed anything
    if ! git diff --cached --quiet; then
        git commit --amend --no-edit
    fi
fi
```

**Why:** Formatting was the single most common CI failure across all phases. PRs #49, #68, #99, #105, #131, #199, and #219 all had at least one "fix formatting" commit. The commit `528af07` (Phase 6) was titled "Fix CI: merge base + ruff format" -- a formatting fix that blocked a wave. An auto-format hook eliminates this entire class of failure.

**Note:** This should be a Claude Code hook (`.claude/settings.json` `hooks` section), not a git hook, because agents run in worktrees where git hooks may not be inherited.

### Pre-PR Hook: Verify Format + Merge Latest Base

**Trigger:** Before `gh pr create`

**Action:**
```bash
#!/usr/bin/env bash
# 1. Run ruff format check
uv run ruff format --check src/ tests/
if [ $? -ne 0 ]; then
    echo "ERROR: Code is not formatted. Run 'make format' first."
    exit 1
fi

# 2. Merge latest from base branch
base_branch=$(gh pr view --json baseRefName -q .baseRefName 2>/dev/null || echo "main")
git fetch origin "$base_branch"
git merge "origin/$base_branch" --no-edit
if [ $? -ne 0 ]; then
    echo "ERROR: Merge conflicts with base branch. Resolve before creating PR."
    exit 1
fi
```

**Why:** Multiple PRs were created against stale base branches, leading to merge conflicts that blocked other PRs in the same wave. PR #154 had to resolve merge conflicts with PR #153's changes. PR #528af07 was an entire commit dedicated to merge conflict resolution. Catching this before PR creation prevents cascading delays.

### Existing Hook: Pre-Push Branch Verification

**Status:** Documented in Phase 5 Wave 0 (PR #143, Tomasz), intended to verify branch naming conventions.

**Current state:** The hook script was created as part of the CI pipeline work but is NOT installed in the repo's `.git/hooks/` directory. It exists only as a GitHub Action check. It should be promoted to a local pre-push hook as well, so violations are caught before push rather than after CI runs.

---

## Deterministic Tooling (Scripts > AI)

The following table identifies tasks currently performed by AI agents that should instead be deterministic scripts. The principle: if a task has no judgment calls and the same inputs always produce the same outputs, it should be a script.

| Task | Current Approach | Proposed Approach | Effort |
|------|-----------------|-------------------|--------|
| **Issue creation from templates** | Manager agent writes issue body from scratch each time, inconsistent format | `scripts/create-issue.sh` with templates in `.github/ISSUE_TEMPLATE/` for feature, bug, tech-debt. Pre-fills labels, assignee fields. | Small (1-2 hours) |
| **PR review comment templates** | Reviewers write review structure from memory, format varies | `.github/PULL_REQUEST_TEMPLATE.md` with Must-fix / Tech-debt / Observations sections pre-filled | Small (30 min) |
| **Tech debt issue filing** | Reviewer manually creates issue after review, often forgotten | `scripts/file-tech-debt.sh --pr {N} --title "..." --assignee {label}` that creates issue with correct labels | Small (1 hour) |
| **Auto-format GitHub Action** | Engineers push, CI fails on format, engineer fixes and pushes again | GitHub Action that runs `ruff format` on PR branches and commits back (like `prettier-action`) | Small (1 hour) |
| **Auto-close issues on PR merge** | Manager or engineer manually closes issues after merge, frequently forgotten | GitHub Action triggered on PR merge that parses `Closes #N` from PR body and closes referenced issues | Small (1 hour) |
| **Worktree cleanup** | Manager remembers (or forgets) to run `git worktree prune` | `make worktree-clean` target in Makefile; also called by `/wave-start` and `/wave-end` skills | Tiny (15 min) |
| **Deployments branch creation** | Manager or Tomasz manually creates branch, sometimes from stale base | `scripts/create-deployments-branch.sh {phase} {wave}` that pulls latest main, creates branch, pushes | Small (30 min) |
| **Issue label management** | Labels created ad-hoc as needed, inconsistent naming | `scripts/sync-labels.sh` that ensures all standard labels exist (phase-N, FIRSTNAME_LASTNAME, tech-debt, priority-*, bug, enhancement, documentation) | Small (1 hour) |
| **Stale branch cleanup** | Never done -- 30+ remote branches from Phases 0-7 still exist | `scripts/cleanup-branches.sh` that deletes remote branches whose PR is merged and which are older than 2 weeks | Small (1 hour) |

**Total estimated effort:** ~8-10 hours of scripting work (one engineer, one wave).

---

## Agent Naming Convention

### Problem

Throughout Phases 0-7, agents were spawned with functional names that did not map to roster members:

- `ci-fixer` -- who is this? Tomasz? Kwame? No one knows.
- `issue-closer` -- an anonymous agent closing issues with no persona accountability.
- `issue-creator` -- same problem.
- `ci-fix-wave2`, `ci-fix-auth` -- functional names with no team member identity.
- `wave1-p7-launcher`, `wave2-p7-setup` -- orchestration tasks with no persona.

This undermines the charter's accountability model. When `ci-fixer` makes a mistake, there is no persona to give feedback to, no trust matrix entry to update, and no track record to evaluate.

### Rule

**Every spawned agent MUST map to a roster member.** No anonymous functional agents.

### Naming Format

```
{firstname}-{task-description}
```

Examples:
- `tomasz-ci-fix` (not `ci-fixer`)
- `fatima-issue-audit` (not `issue-closer`)
- `kwame-oauth-impl` (not `wave2-p7-setup`)
- `renaud-arch-review` (not `review-agent`)
- `priya-test-validation` (not `qa-check`)

### Mapping Process

Before spawning an agent, the orchestrator (Manager) must:

1. Identify the task type (implementation, review, devops, security, data, QA).
2. Map the task to the most appropriate team member based on the org chart and role definitions.
3. Spawn the agent with `{firstname}-{task-description}` naming.
4. Record the mapping in the task system so utilization can be tracked.

### Enforcement

The `/wave-start` skill should output a reminder of this convention. The Manager's spawn logic should validate that every agent name starts with a roster member's first name (lowercase).

---

## Persona Utilization Audit

This table tracks how each team member has been utilized across Phases 0-7, based on actual agent spawns, PR authorship, issue comments, and review activity.

| Person | Role | Level | Utilization | Evidence | Recommendations |
|--------|------|-------|-------------|----------|-----------------|
| **Fatima Okonkwo** | Manager | Senior VP | **HIGH** | Spawned every phase. Created issues, ran retros (Phases 5-7), coordinated waves, created phase PRs to main, managed tech debt batches (PRs #148, #191, #224). Authored PR #206 (doc audit). | Continue as-is. Add `/wave-start` and `/wave-end` skills to reduce manual coordination overhead. |
| **Renaud Tremblay** | System Architect | Partner | **LOW** | Reviewed issues in Phases 0-2 (comment format). Authored PR #214 (diagram updates, Phase 7). Reviewed some PRs. Never spawned as an implementation agent. | Should own ADR documents and architectural decision records. Should review every phase-end PR for architectural coherence. Should be spawned to evaluate cross-module coupling at phase boundaries. |
| **Sunita Krishnamurthy** | DevOps Architect | Staff | **LOW** | Reviewed issues (comment format). Never authored a PR. Never spawned as an implementation agent. All DevOps implementation was done by Tomasz. | Either merge with Tomasz (Sunita advises, Tomasz implements) more explicitly, or give Sunita ownership of infrastructure design docs and cloud architecture decisions. Currently a review-only persona. |
| **Tomasz Wojcik** | DevOps Engineer | Senior | **MEDIUM** | Authored PRs #13 (Docker Compose), #143 (CI pipeline), #189 (coverage/license), #184 (Docker fixes), #219 (CI optimization). Spawned for CI fix tasks. | Good utilization for DevOps work. Should also own the scripting improvements from the "Deterministic Tooling" section. Could be higher if he owned hook and GitHub Action creation. |
| **Dmitri Volkov** | Tech Lead | Staff | **LOW** | Never spawned as an agent. His role was absorbed by Fatima (Manager) who directly coordinated engineers. Issue comments exist but are formulaic. Never made a tech lead decision as an actual running agent. | Must be spawned as an actual agent for tech lead decisions: workload balancing, tech debt allocation, engineer feedback. Currently a phantom role. |
| **Kwame Asante** | Engineer | Principal | **HIGH** | Most prolific implementer. Authored PRs #14, #33, #34, #49, #65, #83, #95, #97, #118, #124, #131, #146, #168, #190, #229. Implementation work across every phase. | Continue as-is. Consider having Kwame mentor newer engineers or take on more architectural implementation work given Principal level. |
| **Amara Diallo** | Engineer | Senior | **HIGH** | Authored PRs #15, #18, #41, #66, #72, #73, #98, #101, #117, #125, #153, #221. Strong implementation presence in every phase. | Continue as-is. Consistently reliable. |
| **Hiro Tanaka** | Engineer | Senior | **HIGH** | Authored PRs #17, #19, #35, #40, #48, #69, #74, #96, #104, #119, #126, #147, #154, #185, #198, #223. Most diverse work: backend, frontend, parsers, visualization. | Continue as-is. Hiro has been the most versatile engineer. Consider formalizing as the go-to for frontend + visualization work. |
| **Carolina Mendez-Rios** | Engineer | Senior | **HIGH** | Authored PRs #16, #20, #37, #38, #39, #50, #68, #84, #87, #99, #105, #116, #132, #155, #199, #222. Strong test authorship. | Continue as-is. Carolina has naturally gravitated toward test suites and validation work. Consider formalizing as the QA-engineer hybrid. |
| **Yara Hadid** | Security Engineer | Senior | **LOW -> MEDIUM** | Minimal involvement Phases 0-5. Phase 6: security review comments. Phase 7: authored PR #230 (OWASP hardening, 2FA design, gitleaks, pip-audit). | Phase 7 was the inflection point. Phase 8+ should have Yara reviewing every PR for security concerns, not just dedicated security PRs. Should own the security-audit CI job configuration. |
| **Priya Nair** | QA Engineer | Senior | **VERY LOW** | Reviewed issues (comment format) in early phases. Never spawned as an implementation agent. Never authored a PR. Never wrote a test. Carolina has been the de facto QA engineer. | Critical gap. Priya should be spawned to: write E2E test plans, execute exploratory testing, validate acceptance criteria post-merge, maintain test infrastructure. Currently a name on the roster with no actual work output. |
| **Elena Petrova** | Data Lead | Staff | **LOW** | Authored PR #144 (data validation framework, Phase 5 Wave 0). Reviewed data-related issues (comment format). Not spawned for data quality analysis or pipeline validation. | Should own data quality SLAs and validation. Should be spawned after each pipeline phase to validate output quality. The data validation framework she created (PR #144) is underutilized. |
| **Tariq Al-Rashidi** | Data Engineer | Principal | **NEVER** | Zero PRs, zero agent spawns, zero substantive issue comments. A Principal-level engineer who has never been activated. | Either activate with specific data engineering work (pipeline optimization, data profiling, schema evolution) or remove from roster. A Principal doing nothing is worse than no Principal at all. |
| **Mei-Lin Chang** | Data Scientist | Principal | **NEVER** | Zero PRs, zero agent spawns, zero substantive issue comments. Same as Tariq. | Either activate with data science work (entity resolution accuracy analysis, topic model evaluation, graph metric validation) or remove from roster. Phase 2 (entity resolution) and Phase 4 (enrichment) were natural opportunities that were missed. |

### Summary Statistics

| Utilization Level | Count | Members |
|-------------------|-------|---------|
| HIGH | 5 | Fatima, Kwame, Amara, Hiro, Carolina |
| MEDIUM | 1 | Tomasz |
| LOW | 4 | Renaud, Sunita, Dmitri, Elena |
| LOW -> MEDIUM | 1 | Yara |
| VERY LOW | 1 | Priya |
| NEVER | 2 | Tariq, Mei-Lin |

**5 of 14 team members (36%) produced the vast majority of work output.** The remaining 9 members range from occasional to nonexistent contribution. This is not a healthy team distribution.

---

## Team Reorganization Recommendations

### 1. Merge Sunita + Tomasz or Give Sunita Implementation Tasks

**Problem:** Sunita (DevOps Architect, Staff) and Tomasz (DevOps Engineer, Senior) have overlapping domains, but only Tomasz does implementation. Sunita reviews issues and provides architectural DevOps guidance, but this guidance is often generic and could be handled by Tomasz alone.

**Options:**
- **Option A (merge):** Sunita becomes the "voice" of DevOps in issue reviews. Tomasz is the sole DevOps agent spawned for implementation. Sunita is not spawned as a separate agent but her review perspective is encoded into Tomasz's persona.
- **Option B (activate):** Give Sunita concrete deliverables: infrastructure design docs, Terraform/IaC specs, monitoring dashboards, deployment runbooks. She should author PRs, not just review issues.

**Recommendation:** Option B. Sunita's Staff level justifies dedicated work products. Phase 8+ should include infrastructure design work that Sunita owns.

### 2. Activate Priya as QA Implementer

**Problem:** Priya (QA Engineer, Senior) has never been spawned as an implementation agent. Her charter role includes designing automated test suites, performing exploratory testing, and writing bug reports. None of this has happened. Carolina has absorbed all testing work.

**Action:**
- Phase 8+: Priya owns the test plan for each wave.
- Priya writes E2E tests and integration tests (not Carolina).
- Priya validates acceptance criteria post-merge before wave sign-off.
- Priya should be spawned after each wave's PRs are merged to run validation.

### 3. Activate or Remove Tariq + Mei-Lin

**Problem:** Two Principal-level team members with zero contributions across 7 phases. This is a waste of roster space and creates the illusion of a larger team than actually operates.

**Options:**
- **Activate:** Phase 8+ includes data quality validation, pipeline profiling, entity resolution accuracy measurement, and topic model evaluation. These are natural tasks for Tariq (Data Engineer) and Mei-Lin (Data Scientist).
- **Remove:** If the project does not need dedicated data analysis agents, remove them from the roster. This is honest and reduces cognitive overhead when planning.

**Recommendation:** Activate for Phase 8+. The data pipeline has never been validated by a data specialist. Elena's validation framework (PR #144) was a start but has not been followed up. Tariq and Mei-Lin should analyze pipeline output quality and file findings as issues.

### 4. Spawn Dmitri as an Actual Agent

**Problem:** Dmitri (Tech Lead, Staff) was defined in the charter to coordinate implementation, adjust workloads, collect feedback, and track tech debt. In practice, Fatima (Manager) absorbed all of these responsibilities. Dmitri was never spawned as a running agent.

**Action:**
- Dmitri should be spawned at wave boundaries to:
  - Review workload distribution across engineers
  - Collect 1-2 sentences of feedback per engineer
  - Triage tech debt issues and assign to engineers (respecting the 20% cap)
  - Make tech lead decisions (library choices, refactoring scope, code organization)
- Dmitri's feedback should flow to Fatima, who consolidates for the user.

### 5. Renaud Owns ADRs and Architectural Docs

**Problem:** Renaud (System Architect, Partner) is the highest-level technical role but has minimal output. His single PR was a diagram update (PR #214). The charter says he "designs system architecture and verifies implementation matches design" -- neither has been done systematically.

**Action:**
- Renaud should author ADRs (Architecture Decision Records) for significant technical choices.
- Renaud should review each phase-end PR for architectural coherence.
- Renaud should produce a system architecture document that evolves with each phase.
- Renaud should be spawned at phase boundaries, not wave boundaries (his work is higher-level).

---

## Genericization Plan

### Vision

Extract the team simulation framework from isnad-graph into a standalone, reusable package: `claude-team-framework/`. Any project using Claude Code can bootstrap a simulated team with a single script.

### Package Structure

```
claude-team-framework/
  bootstrap.sh                    # Interactive setup script
  README.md                       # Usage documentation
  presets/                        # Project type presets
    fullstack-monorepo.yml
    data-pipeline.yml
    backend-api.yml
    frontend-spa.yml
    library.yml
    mobile.yml
    desktop.yml
  templates/
    charter.md.j2                 # Jinja2 template for team charter
    trust_matrix.md.j2            # Trust matrix template
    feedback_log.md.j2            # Feedback log template
    CLAUDE.md.j2                  # Project CLAUDE.md template
    roster/                       # Role templates
      manager.md.j2
      architect.md.j2
      tech_lead.md.j2
      engineer.md.j2
      devops.md.j2
      security.md.j2
      qa.md.j2
      data_lead.md.j2
      data_engineer.md.j2
  skills/
    retro.md                      # /retro skill definition
    wave-start.md                 # /wave-start skill definition
    wave-end.md                   # /wave-end skill definition
    review-pr.md                  # /review-pr skill definition
    plan-phase.md                 # /plan-phase skill definition
    close-stale-issues.md         # /close-stale-issues skill definition
  hooks/
    post-commit-format.sh         # Auto-format hook
    pre-pr-verify.sh              # Pre-PR verification hook
    pre-push-branch-check.sh      # Branch naming verification
  scripts/
    create-issue.sh               # Issue creation from templates
    file-tech-debt.sh             # Tech debt issue filing
    create-deployments-branch.sh  # Deployments branch creation
    sync-labels.sh                # Label synchronization
    cleanup-branches.sh           # Stale branch cleanup
  github/
    PULL_REQUEST_TEMPLATE.md      # PR template
    ISSUE_TEMPLATE/
      feature.md
      bug.md
      tech-debt.md
    workflows/
      auto-format.yml             # Auto-format on PR
      auto-close-issues.yml       # Close issues on PR merge
```

### `bootstrap.sh` Interactive Script

The bootstrap script walks the user through team setup:

```
$ ./bootstrap.sh

Welcome to Claude Team Framework!

1. Project name: _______
2. Project type:
   [ ] fullstack-monorepo    (Frontend + Backend + DB + DevOps)
   [ ] data-pipeline         (ETL/ELT + DB + Analytics)
   [ ] backend-api           (API + DB + DevOps)
   [ ] frontend-spa          (React/Vue/Svelte + API client)
   [ ] library               (Package/SDK + Tests + CI)
   [ ] mobile                (iOS/Android + Backend)
   [ ] desktop               (Electron/Tauri + Backend)
   [ ] custom                (Build your own)

3. Team size:
   [ ] Small (4-6)    Manager + Tech Lead + 2-4 Engineers
   [ ] Medium (8-10)  + Architect + DevOps + QA
   [ ] Large (12-16)  + Security + Data Team + Specialist roles

4. Branching strategy:
   [ ] Deployments branches (recommended for teams)
   [ ] Feature branches to main (simple)
   [ ] GitFlow (release branches)

5. CI/CD platform:
   [ ] GitHub Actions (recommended)
   [ ] GitLab CI
   [ ] None (manual)

6. Generate team member names?
   [ ] Random diverse names (recommended)
   [ ] Provide custom names
   [ ] Use generic role names (Engineer 1, Engineer 2...)

Generating your team structure...
```

### Project Type Presets

Each preset defines:
- **Roles included** (which roster templates to use)
- **Default team size** (how many of each role)
- **Skills enabled** (which skills are relevant)
- **Hooks enabled** (which hooks to install)
- **Workflow templates** (CI/CD for that project type)
- **Tech stack assumptions** (language, framework, package manager)

| Preset | Roles | Default Size | Key Skills | Key Hooks |
|--------|-------|-------------|------------|-----------|
| `fullstack-monorepo` | Manager, Architect, Tech Lead, 4 Engineers, DevOps, QA, Security | 10 | All | All |
| `data-pipeline` | Manager, Data Lead, 2 Data Engineers, Tech Lead, 2 Engineers, DevOps | 8 | retro, wave-start, wave-end, plan-phase | format, branch-check |
| `backend-api` | Manager, Tech Lead, 3 Engineers, DevOps, QA | 7 | retro, wave-start, wave-end, review-pr | All |
| `frontend-spa` | Manager, Tech Lead, 3 Engineers, QA | 6 | retro, wave-start, review-pr | format, pre-pr |
| `library` | Manager, Tech Lead, 2 Engineers, QA | 5 | retro, review-pr | format, pre-pr |
| `mobile` | Manager, Tech Lead, 2 Engineers (iOS/Android), Backend Engineer, QA | 6 | retro, wave-start, review-pr | format |
| `desktop` | Manager, Tech Lead, 2 Engineers, QA | 5 | retro, review-pr | format |

### What is Configurable at Bootstrap Time

| Setting | Default | Configurable? |
|---------|---------|---------------|
| Team member names | Random diverse | Yes -- custom or generic |
| Team size per role | Preset-defined | Yes -- add/remove roles |
| Branching strategy | Deployments branches | Yes -- 3 options |
| CI/CD platform | GitHub Actions | Yes -- GH Actions, GitLab CI, None |
| Feedback system enabled | Yes | Yes -- can disable trust matrix, fire/hire |
| Tech debt tracking | GitHub Issues | Yes -- can use Linear, Jira labels |
| Phase/wave structure | Enabled | Yes -- can use sprints, kanban, or freeform |
| Review process | Peer review + tech debt | Yes -- can simplify to approve/request-changes |
| Skills installed | Preset-dependent | Yes -- pick and choose |
| Hooks installed | Preset-dependent | Yes -- pick and choose |
| Formatter | ruff (Python) | Yes -- prettier, eslint, rustfmt, gofmt, etc. |
| Issue templates | Included | Yes -- customize or skip |
| PR template | Included | Yes -- customize or skip |

### Template Variables

All templates use Jinja2 syntax. Key variables available:

```yaml
project:
  name: "isnad-graph"
  type: "data-pipeline"
  language: "python"
  formatter: "ruff"
  package_manager: "uv"

team:
  size: "large"
  members:
    - name: "Fatima Okonkwo"
      role: "manager"
      level: "Senior VP"
      email: "parametrization+Fatima.Okonkwo@gmail.com"
    # ... etc

branching:
  strategy: "deployments"
  base_branch: "main"
  pattern: "deployments/phase{N}/wave-{M}"

workflow:
  ci_platform: "github-actions"
  feedback_enabled: true
  trust_matrix_enabled: true
  fire_hire_enabled: true
```

### Migration Path from isnad-graph

1. Extract charter.md into `charter.md.j2` with template variables replacing project-specific references.
2. Extract roster cards into role templates (manager.md.j2, engineer.md.j2, etc.) with name/personality as variables.
3. Extract the trust matrix into a template.
4. Package skills as standalone .md files with clear trigger/input/output documentation.
5. Package hooks as standalone shell scripts with configurable formatter/linter.
6. Package scripts with configurable GitHub org/repo references.
7. Write bootstrap.sh that renders templates and copies files into `.claude/team/`.
8. Write presets as YAML files that set default template variable values.

### Non-Goals

- The framework does NOT include project-specific code (no isnad-graph business logic).
- The framework does NOT manage cloud infrastructure or deployment.
- The framework does NOT replace Claude Code itself -- it configures the team simulation layer on top of it.
- The framework does NOT enforce a specific programming language -- templates are language-agnostic with configurable formatter/linter hooks.

---

## Appendix: Task Name Audit

The following task names from the current project violated the naming convention (functional names instead of persona names):

| Task ID | Current Name | Should Be | Reason |
|---------|-------------|-----------|--------|
| #72 | `ci-fixer` | `tomasz-ci-fix` | DevOps task, belongs to Tomasz |
| #66 | `issue-closer` | `fatima-issue-close` | Manager responsibility |
| #100 | `issue-creator` | `fatima-issue-create` | Manager responsibility |
| #81 | `ci-fix-wave2` | `tomasz-ci-fix-wave2` | DevOps task |
| #114 | `ci-fix-auth` | `tomasz-ci-fix-auth` | DevOps/CI task |
| #104 | `wave1-p7-launcher` | `fatima-wave1-p7` | Manager responsibility |
| #110 | `wave2-p7-setup` | `fatima-wave2-p7-setup` | Manager responsibility |
| #101 | `issue-docs-diagrams` | `renaud-docs-diagrams` | Architect responsibility |
| #99 | `data-gap-analysis` | `elena-data-gap-analysis` | Data Lead responsibility |
| #115 | `wave3-p7-all` | `fatima-wave3-p7` | Manager orchestration |
