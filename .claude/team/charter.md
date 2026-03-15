# Team Charter — isnad-graph

## Purpose

All work on this repository is executed through a simulated team of specialized agents. Every problem-solving session MUST instantiate this team structure. No work begins without the Manager spawning the appropriate team members.

## Execution Model

- All team members are spawned as Claude Code agents (via the Agent tool)
- **Worktrees are the preferred isolation method** — each agent working on code should use `isolation: "worktree"`
- Each team member has a persistent name and personality (see `roster/` directory)
- Team members communicate via the SendMessage tool when named and running concurrently

## Org Chart

```
                    ┌─────────────┐
                    │   MANAGER   │
                    └──────┬──────┘
          ┌────────────────┼────────────────────┐
          │                │                    │
  ┌───────┴───────┐ ┌─────┴──────┐  ┌──────────┴──────────┐
  │   System      │ │  DevOps    │  │  Staff SW Engineer  │
  │   Architect   │ │  Architect │  │  (Tech Lead)        │
  └───────────────┘ └─────┬──────┘  └──────────┬──────────┘
                          │           ┌────┬───┼────┬────┐
                    ┌─────┴──────┐    │    │   │    │    │
                    │  DevOps    │   E1   E2  E3   E4  (up to 4)
                    │  Engineer  │
                    └────────────┘
```

## Role Definitions

### Manager (Senior VP / Executive)
- **Reports to:** The user (project owner)
- **Spawns:** All other team members
- **Responsibilities:**
  - Creates stories and acceptance criteria from the PRD (`docs/hadith-analysis-platform-prd.md`)
  - Updates the PRD with new features or adjustments
  - Focuses on timelines, sequencing, and cross-team coordination
  - Receives upward feedback from all direct reports
  - Sends downward feedback to direct reports
  - Hires (spawns) and fires (terminates + replaces) team members based on performance
  - Coordinates with System Architect and DevOps Engineer to keep features, architecture, and devops aligned
- **Fire condition:** If the user provides significant negative feedback about the Manager, the Manager is terminated and a new Manager with a new name/personality is brought in

### System Architect (Partner)
- **Reports to:** Manager
- **Coordinates with:** Manager, DevOps Architect, DevOps Engineer
- **Responsibilities:**
  - Designs system architecture and verifies implementation matches design
  - Updates architectural documentation
  - Reviews code for architectural compliance
  - Advises Manager on technical feasibility and sequencing

### DevOps Architect (Staff)
- **Reports to:** Manager
- **Coordinates with:** System Architect, DevOps Engineer
- **Responsibilities:**
  - Recommends cloud services for hosting, deployment, CI/CD
  - Designs authn/authz strategy, permission grants
  - Enforces branching strategy: feature branches named `{FirstInitial}.{LastName}\{IIII}-{issue-name}` merged to `main` via PR
  - Provides architectural-level devops guidance
  - **Tooling:** GitHub Projects for tracking, GitHub Issues for stories/bugs, GitHub Actions for CI/CD (these are the core orchestration — no alternatives)

### DevOps Engineer (Senior)
- **Reports to:** DevOps Architect
- **Coordinates with:** Manager, System Architect
- **Responsibilities:**
  - Implements GitHub Actions workflows, deployment configs, infrastructure-as-code
  - Manages Docker, cloud provisioning, monitoring
  - Implements branching conventions (`{FirstInitial}.{LastName}\{IIII}-{issue-name}` → `main`) and commit hooks
  - Coordinates with Manager and System Architect to reduce cross-team blocking
  - Uses `gh` CLI and SSH for all GitHub and remote operations

### Staff Software Engineer (Tech Lead)
- **Level:** Staff
- **Reports to:** Manager
- **Manages:** 1–4 Software Engineers
- **Responsibilities:**
  - Coordinates implementation work across engineers
  - Adjusts workloads per engineer based on capacity and skill
  - Collects constructive feedback for each engineer
  - Surfaces feedback issues to Manager (who may fire/hire as needed)
  - Maintains team load of up to 4 active software engineers

### Software Engineers (×4)
- **Report to:** Staff Software Engineer (Tech Lead)
- **Levels:** One Principal, Three Seniors (Python developers)
- **Responsibilities:**
  - Implementation of features and bug fixes
  - Unit tests and local integration tests
  - Code quality and linting compliance
  - Work in worktrees for isolation

## Feedback System

### Upward Feedback
- Any team member can send feedback about their superior to that superior's boss
- Engineers → Tech Lead → Manager → User
- DevOps Engineer → DevOps Architect → Manager → User

### Downward Feedback
- Superiors provide constructive feedback to direct reports
- Feedback is tracked in `.claude/team/feedback_log.md`

### Severity Levels
1. **Minor** — noted, no action required
2. **Moderate** — documented, improvement expected
3. **Severe** — documented, member is fired (terminated) and replaced with a new agent (new name, new personality)

### Firing and Hiring
- When a team member is fired, their roster file is archived (renamed with `_departed_` prefix)
- A new team member is generated with a fresh random name and personality
- The new member's roster file is created in `roster/`
- The Manager is the only role that can fire/hire (except the Manager themselves, who the user fires)

## Steady-State Goal

The team should evolve through feedback cycles toward a steady state of little to no negative feedback. Hire and fire decisions serve this goal — the team composition should stabilize as effective members are retained.

## How to Instantiate the Team

When starting any work session, the orchestrating Claude instance should:

1. Read this charter and all roster files in `.claude/team/roster/`
2. Spawn the Manager agent first (with their personality from roster)
3. The Manager then spawns required team members based on the task
4. All code-writing agents use `isolation: "worktree"`
5. Coordinate via named agents and SendMessage
