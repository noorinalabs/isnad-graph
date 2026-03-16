# Team Interaction Audit

An honest assessment of how the isnad-graph simulated team has operated across Phases 0-7, compared against the charter's specifications. Written by Fatima Okonkwo (Manager).

---

## Table of Contents

1. [What the Charter Specifies](#what-the-charter-specifies)
2. [What Actually Happened](#what-actually-happened)
3. [Gap Analysis](#gap-analysis)
4. [Cross-Team Collaboration Incidents](#cross-team-collaboration-incidents)
5. [Recommendations](#recommendations)
6. [Process Changes for Phase 8+](#process-changes-for-phase-8)

---

## What the Charter Specifies

The charter (`.claude/team/charter.md`) defines a comprehensive team interaction model. Here is what it requires:

### Trust Identity Matrix
- Every team member maintains a directional trust score (1-5) for every other member.
- Default score: 3 (neutral).
- Scores decrease on bad work, increase on reliable delivery.
- The matrix and change log live in `.claude/team/trust_matrix.md` on the `CEO/0000-Trust_Matrix` branch.
- Updates happen "whenever a trust-relevant interaction occurs."

### Feedback System
- **Upward feedback:** Engineers -> Tech Lead -> Manager -> User. DevOps Engineer -> DevOps Architect -> Manager -> User. Security Engineer -> DevOps Architect -> Manager -> User. QA Engineer -> Tech Lead -> Manager -> User. Data team -> Data Lead -> Manager -> User.
- **Downward feedback:** Superiors provide constructive feedback to direct reports.
- **All feedback tracked** in `.claude/team/feedback_log.md`.
- **Three severity levels:** Minor (noted), Moderate (documented, improvement expected), Severe (fired and replaced).

### Fire/Hire
- When a team member is fired, their roster file is archived (renamed with `_departed_` prefix).
- A new member is generated with a fresh name and personality.
- The Manager is the only role that fires/hires (except the Manager, who the user fires).
- The team should evolve toward a steady state of minimal negative feedback.

### Code Review & Tech Debt
- Every software engineering branch reviewed by one other engineer before merging.
- Reviews produce must-fix items (block merge) and tech debt items (filed as GitHub Issues).
- Tech Lead tracks tech debt, allocates to engineers (max 20% of any engineer's capacity).

### Issue Review Process
- Every new issue reviewed by: DevOps Architect (Sunita), System Architect (Renaud), Data Lead (Elena), Tech Lead (Dmitri), and QA Engineer (Priya, software issues only).
- Reviewers speak up only when they have something meaningful to add.

### Comment Format
- All issue comments use Requestor/Requestee/RequestOrReplied format.
- Replies swap Requestor and Requestee.
- After replying, the replier notifies the original Requestor via SendMessage.

### Work Gate
- No implementation begins until ALL issues for the phase are created and reviewed.

---

## What Actually Happened

### Trust Matrix: Created in Phase 0, NEVER Updated

The trust matrix was created as part of PR #2 (`CEO/0000-Trust_Matrix -> main`). It contains the initial template with all scores at 3 (default). The change log reads: "*(no changes yet)*".

Across 7 phases, approximately 240 commits, 100+ PRs, and 158 issues, not a single trust score was ever updated. No trust-relevant interaction was ever recorded despite:
- Multiple CI failures caused by one engineer's work blocking another
- Consistently high-quality output from Kwame, Amara, Hiro, and Carolina
- Zero output from Tariq and Mei-Lin
- Multiple instances of work duplication between PRs

The matrix exists as a pristine, unused artifact.

### Upward Feedback: One-Directional, Retro-Only

Feedback flowed upward only through wave retrospectives, starting in Phase 5. The retro format captured team observations that Fatima consolidated and presented to the user. This is the expected flow (team -> Manager -> user) but:

- **It only started in Phase 5.** Phases 0-4 had no structured feedback mechanism.
- **It was one-directional.** Engineers reported what went well/poorly, but the flow was always upward. There was never a case where an engineer provided feedback specifically about their lead (Dmitri) or the Manager (Fatima) through the charter's upward feedback channel.
- **Dmitri was never in the loop.** The charter specifies Engineers -> Tech Lead -> Manager -> User. In practice, engineers reported directly to Fatima via retros, skipping Dmitri entirely (because Dmitri was never spawned).

### Downward Feedback: NEVER Happened

The charter specifies: "Superiors provide constructive feedback to direct reports." This did not happen once.

- Fatima never gave formal feedback to Renaud, Sunita, Elena, or Dmitri.
- Dmitri never gave feedback to Kwame, Amara, Hiro, Carolina, or Priya (Dmitri was never spawned).
- Sunita never gave feedback to Tomasz or Yara.
- Elena never gave feedback to Tariq or Mei-Lin.

The feedback log at `.claude/team/feedback_log.md` contains only the template header and "*No feedback entries yet.*" -- unchanged from its creation.

### Peer Feedback: NEVER Happened

The charter does not explicitly specify peer feedback, but the trust matrix implies it (directional scores between peers). No engineer ever gave structured feedback about another engineer. The closest approximation was PR review comments, which were code-focused, not person-focused.

### Fire/Hire: Never Triggered

No team member was ever fired or replaced. The charter's steady-state mechanism (fire underperformers, hire replacements) was never exercised despite:
- Two team members (Tariq, Mei-Lin) with zero contributions
- One team member (Priya) with near-zero contributions
- One team member (Dmitri) who was never spawned

The fire/hire mechanism exists in the charter but has never been tested. It is unknown whether the infrastructure (roster archiving, name generation, identity creation) actually works.

### Feedback Log: Exists but Empty

`.claude/team/feedback_log.md` has been in the repository since Phase 0. It has never been written to. It contains only the template format and the placeholder text "*No feedback entries yet.*"

### Comment Format: Implemented Consistently on GitHub Issues

The Requestor/Requestee/RequestOrReplied format was adopted starting in Phase 1 and used consistently across all issue comments from Phase 2 onward. This is one of the charter's most successful specifications.

Example (typical issue comment):
```
Requestor: Renaud.Tremblay
Requestee: Kwame.Asante
RequestOrReplied: Request

Consider whether the staging schema needs a version field for forward compatibility.
```

Followed by:
```
Requestor: Kwame.Asante
Requestee: Renaud.Tremblay
RequestOrReplied: Replied

Added `schema_version` field to the Parquet metadata. Will default to "1.0".
```

This format worked well because:
- It was concrete and unambiguous
- It was enforced at the point of action (writing a comment)
- It had immediate utility (the reply protocol ensured questions got answered)

### Issue Review Process: Worked Well, Substantive Comments

The five-reviewer process (Sunita, Renaud, Elena, Dmitri, Priya) was implemented consistently from Phase 1 onward. Reviewers followed the charter's guidance to "speak up only when they have something meaningful to add" -- many issues have only 2-3 reviewer comments rather than all 5, which is correct behavior.

Substantive review examples:
- Renaud flagged architectural concerns about Neo4j schema normalization in Phase 3 issues
- Sunita flagged Docker networking requirements for testcontainers in Phase 6 issues
- Elena flagged data quality validation gaps in Phase 2 entity resolution issues

However:
- Dmitri's reviews were often generic ("Looks good from tech lead perspective") -- likely because he was never spawned as a real agent with full context
- Priya's reviews were similarly thin, rarely adding QA-specific value

### PR Reviews: Inconsistent Quality

PR reviews happened for most PRs but varied in depth:
- **Strong reviews:** Renaud's architectural reviews on Phase 3-5 PRs caught real issues (e.g., Cypher injection risks, missing pagination)
- **Formulaic reviews:** Many reviews followed a template without deep engagement
- **Missing reviews:** Some PRs in fast-moving waves were merged without substantive review (e.g., several tech debt PRs in Phase 4 Wave 1)

### Tech Debt Tracking: Improved Over Time

- **Phases 0-3:** Tech debt was identified in PR reviews but inconsistently filed as issues. The user gave explicit feedback to always file issues.
- **Phases 4-6:** Tech debt issues were filed more consistently, with proper labels (`tech-debt`, `FIRSTNAME_LASTNAME`).
- **Phase 7:** 13 new tech debt issues were filed with correct labels and `phase-8` tagging for future work.

The 20% capacity cap on tech debt was never formally tracked. Fatima allocated tech debt work intuitively rather than measuring against the charter's 20% guideline.

### Work Gate: Generally Respected

The work gate (all issues created and reviewed before implementation) was respected in most phases:
- **Phases 0-2:** Issues created upfront, reviewed, then implementation started.
- **Phase 3:** Respected.
- **Phase 4:** Partially violated -- some issues were created mid-wave when scope was discovered during implementation.
- **Phases 5-7:** Respected, with the `/plan-phase` pattern becoming more established.

---

## Gap Analysis

| Charter Commitment | Status | Evidence |
|-------------------|--------|----------|
| Trust matrix updated on trust-relevant interactions | **Not Implemented** | Matrix unchanged from creation. All scores remain at default 3. Change log empty. |
| Upward feedback: Engineers -> Tech Lead -> Manager -> User | **Partially Implemented** | Feedback flows upward through retros (Phase 5+) but bypasses Tech Lead (Dmitri never spawned). No formal upward feedback in Phases 0-4. |
| Downward feedback: Superiors -> direct reports | **Not Implemented** | Zero instances of downward feedback. Feedback log empty. No lead has ever given constructive feedback to a report. |
| Peer feedback between team members | **Not Implemented** | No structured peer feedback. PR review comments are code-focused, not person-focused. |
| Feedback severity levels (minor/moderate/severe) | **Not Implemented** | No feedback has been logged, so no severity has been assigned. |
| Fire/hire based on performance | **Not Implemented** | Never triggered despite clear underperformance (Tariq, Mei-Lin, Priya). The mechanism is untested. |
| Feedback tracked in feedback_log.md | **Not Implemented** | File exists, contains only template. Never written to. |
| Comment format (Requestor/Requestee/RequestOrReplied) | **Fully Implemented** | Consistently used on GitHub issues from Phase 2 onward. Reply protocol followed. |
| Issue review by 5 reviewers | **Fully Implemented** | All reviewers engaged per issue. Reviewers appropriately skip when nothing to add. |
| Work gate: issues before implementation | **Mostly Implemented** | Respected in 6 of 7 phases. Phase 4 had partial mid-wave issue creation. |
| Peer code review before merge | **Mostly Implemented** | Most PRs reviewed. Some fast-tracked tech debt PRs merged with minimal review. |
| Tech debt filed as GitHub Issues | **Partially Implemented** | Improved from inconsistent (Phases 0-3) to consistent (Phases 4-7) after user feedback. |
| Tech debt max 20% of engineer capacity | **Not Implemented** | Never formally tracked or measured. Allocation was intuitive. |
| Worktree cleanup after each wave | **Partially Implemented** | Done in some waves, forgotten in others. Caused branch lock issues when skipped. |
| Commit identity per team member | **Fully Implemented** | All commits use per-commit `-c` flags with correct name/email. Co-Authored-By trailers present. |
| Branch naming convention | **Fully Implemented** | All branches follow `{F.Lastname}/{NNNN}-{description}` pattern. |
| PR format with Closes #N | **Fully Implemented** | All PRs reference related issues. PR template followed. |
| Deployments branches per wave | **Fully Implemented** | Consistent from Phase 1 onward. Pattern: `deployments/phase{N}/wave-{M}`. |

### Summary

| Status | Count | Percentage |
|--------|-------|------------|
| Fully Implemented | 6 | 35% |
| Mostly Implemented | 2 | 12% |
| Partially Implemented | 3 | 18% |
| Not Implemented | 6 | 35% |

**The team excels at mechanical, enforceable processes** (commit identity, branch naming, PR format, comment format, issue review) and **fails at social/interpersonal processes** (feedback, trust, performance management). This is consistent with the nature of the system: mechanical processes can be encoded into scripts and templates; social processes require intentional agent spawning and dedicated time.

---

## Cross-Team Collaboration Incidents

### Worktree Branch Collisions (Multiple Incidents)

**Phase 3 Wave 1:** Kwame's worktree for node loading (PR #97) and Amara's worktree for edge loading (PR #101) both modified `src/graph/__init__.py`. When Amara's PR was created, it had merge conflicts with Kwame's already-merged changes. Resolution required a manual merge in Amara's worktree.

**Phase 5 Wave 2:** Three PRs (#153, #154, #155) all modified frontend files in `frontend/src/`. PRs #154 (Hiro - viz pages) and #155 (Carolina - frontend pages) both modified `client.ts`. PR #154 was merged first; PR #155 required conflict resolution (commit `4b14832`: "Resolve merge conflicts with PR #154 in client.ts").

**Phase 6 Wave 1:** Worktrees from Phase 5 were not pruned. When Phase 6 agents attempted to check out branches, they encountered "branch is already checked out" errors because old worktree references still existed. Resolution: manual `git worktree prune` by the orchestrator.

**Root cause:** Agents work in isolation by design (worktrees), but no mechanism exists to detect overlapping file modifications before PR creation. The charter says to merge latest base before PR, but this only catches conflicts at PR time, not at task assignment time.

### Duplicate Work Across PRs (Phase 4 Wave 1)

**Phase 4 Wave 1** had four tech debt PRs (#116, #117, #118, #119) assigned to four different engineers. PR #117 (Amara - edge MERGE idempotency) and PR #118 (Kwame - replace _transpose_pydict) both touched `src/graph/loader.py`. The changes were non-conflicting but overlapping in scope -- both engineers investigated the same module and could have coordinated to reduce review overhead.

**Phase 7 Wave 1:** PRs #221 (Amara - Fawaz Arabic), #222 (Carolina - metadata enrichment), and #223 (Hiro - sunnah scraper) all added new functionality to the data acquisition pipeline. While the PRs did not conflict, they were developed in parallel without cross-awareness. Amara's Arabic edition download and Carolina's metadata enrichment could have been a single coordinated effort.

**Root cause:** Work was decomposed into isolated issues and assigned to individuals without cross-reference. No "dependency map" existed to flag when two issues might touch the same code.

### Cross-PR Dependencies (Phase 7 Wave 2)

**PR #229 (Kwame - OAuth auth)** and **PR #230 (Yara - OWASP security hardening)** had a dependency that was not identified at planning time. PR #230 added a `twofa` module with TOTP and WebAuthn stub interfaces. PR #229 needed to import from this module for the auth flow.

Resolution: Kwame merged the deployments branch (which included Yara's changes from PR #230) into his feature branch (commit `7672c3b`: "merge deployments/phase7/wave-2 and fix mypy no-any-return in tokens"). This worked but was discovered during implementation, not planning.

**Root cause:** The issue review process did not flag the dependency between issue #215 (OAuth) and issue #216 (2FA/OWASP). Both were assigned to Wave 2 but reviewed independently.

### Review Comment Duplication (Renaud Reviewing Overlapping PRs)

In Phase 5 Wave 2, Renaud reviewed PRs #153, #154, and #155 independently. His review of PR #153 (Amara - graph search API) flagged Cypher injection concerns. His review of PR #154 (Hiro - viz pages) flagged the same concern about API queries used on the frontend. The two reviews could have been consolidated if Renaud had reviewed them as a batch rather than independently.

Similarly in Phase 3 Wave 3, Renaud reviewed PR #104 (Hiro - validation + orchestrator) and PR #105 (Carolina - graph tests), both touching the graph module. His architectural feedback on PR #104 about validation query structure was repeated in slightly different form on PR #105.

**Root cause:** Reviews are assigned per-PR, not per-module or per-wave. A reviewer seeing the same module across multiple PRs has no mechanism to cross-reference their own reviews.

### CI Cascade Failures

**Phase 6 Wave 2:** PR #199 (Carolina - negative/fuzz tests) introduced formatting violations that blocked CI. The fix commit `528af07` ("Fix CI: merge base + ruff format, resolve pyproject.toml conflict") was a manual intervention. While this was being fixed, PR #198 (Hiro - Playwright tests) was also waiting on CI, creating a queue.

**Phase 7 Wave 2:** PR #229 (Kwame - OAuth) had multiple CI fix commits:
- `94d7493`: "fix: bypass auth in API tests and ignore ecdsa CVE with no fix"
- `8106fd3`: "fix: bypass auth in security and auth test fixtures"
- `e3cc63c`: "fix: revert auth bypass in test_auth conftest to preserve middleware tests"

Three consecutive fix commits for test configuration issues. Each required a CI run (approximately 3-5 minutes per run on GitHub Actions), creating a 15+ minute feedback loop.

**Root cause:** No local pre-push CI check. Engineers push, wait for CI, see failure, fix, push again. A local lint/format/test check would catch most of these before push.

---

## Recommendations

### 1. Post-Wave Feedback Round

**What:** After each wave completes, the Tech Lead (Dmitri) spawns and gives 1-2 sentences of constructive feedback to each engineer who contributed to the wave. The Manager (Fatima) gives feedback to each lead. All feedback is logged in `feedback_log.md` with severity.

**Format:**
```
## [2026-03-16] -- Dmitri Volkov -> Kwame Asante -- Severity: minor
OAuth implementation in PR #229 was solid but required 3 CI fix commits.
Consider running the full test suite locally before pushing.
Action: None required, noted for future reference.
```

**Why:** The feedback log has been empty for 7 phases. This is the single largest gap between charter and reality. Even brief feedback creates accountability and a historical record.

### 2. Trust Matrix Updates After Each Wave

**What:** After each wave, the Manager updates the trust matrix based on observable signals:
- PR quality (number of must-fix items, CI failures)
- Delivery reliability (on-time, blocked, late)
- Review quality (substantive vs. formulaic)
- Collaboration incidents (helped others, caused conflicts)

**Frequency:** Once per wave, not per interaction. This is pragmatic -- updating per interaction would require spawning agents for every comment.

**Why:** The trust matrix was designed to be a living document. After 7 phases it is still at all-3s, which tells us nothing. Even rough directional updates (Kwame: 3->4 for consistent delivery, Tariq: 3->2 for zero output) would be more useful than the current state.

### 3. Peer Review Pairing

**What:** At wave start, the Manager assigns specific reviewer-author pairs rather than ad-hoc reviewer selection.

**Rules:**
- Each engineer is assigned exactly one reviewer for their primary PR in the wave.
- The reviewer is assigned before work begins, so they can follow the branch development.
- No engineer reviews their own work or the work of someone who is reviewing them (no reciprocal pairing).
- Renaud reviews cross-module PRs (PRs that touch 3+ modules).

**Why:** Ad-hoc review assignment led to inconsistent coverage. Some PRs got deep reviews (Renaud on architectural PRs), others got minimal reviews (tech debt PRs). Explicit pairing ensures every PR gets consistent review depth and eliminates the "who should review this?" delay.

### 4. Quarterly Team Health Check (Every 2 Phases)

**What:** At the end of every 2 phases, the Manager produces a team health report covering:
- Utilization per team member (PRs authored, issues closed, reviews given)
- Trust matrix trajectory (are scores trending up or down?)
- Feedback log analysis (are the same issues recurring?)
- Fire/hire recommendation (should any member be replaced?)
- Role adjustment recommendation (should any member change scope?)

**Why:** Without periodic assessment, underperformance accumulates silently. Tariq and Mei-Lin have contributed nothing for 7 phases. If a health check had been performed after Phase 2, this would have been flagged at Phase 4 instead of Phase 7.

### 5. Feedback Log Actually Maintained

**What:** The feedback log must be written to at least once per wave. If there is no negative feedback, log positive feedback. The log should never be empty after a wave completes.

**Minimum per wave:**
- 1 entry per lead -> their reports (Dmitri -> engineers, Sunita -> Tomasz/Yara, Elena -> Tariq/Mei-Lin)
- 1 entry from Manager -> leads (Fatima -> Dmitri, Renaud, Sunita, Elena)

**Why:** The feedback log is the only historical record of team performance. Git history shows what was done but not how well it was done or what could be improved. An empty feedback log means no learning between waves.

---

## Process Changes for Phase 8+

These are concrete changes to the charter and process based on the findings above. Each change includes the charter section affected and the specific modification.

### Change 1: Mandatory Dmitri Spawn at Wave Boundaries

**Charter section affected:** Role Definitions > Staff Software Engineer (Tech Lead)

**Current:** Dmitri's responsibilities are defined but he is never spawned.

**Change:** Add to the charter:
> The Tech Lead MUST be spawned as an active agent at the start and end of each wave. At wave start: assigns reviewers, distributes work, sets capacity expectations. At wave end: collects feedback, reviews tech debt backlog, reports to Manager.

**Rationale:** The Tech Lead role exists to buffer the Manager from implementation details. Without Dmitri, Fatima coordinates engineers directly, which does not scale and skips the feedback chain.

### Change 2: Trust Matrix Update Cadence

**Charter section affected:** Trust Identity Matrix

**Current:** "Update that file whenever a trust-relevant interaction occurs."

**Change:** Replace with:
> The Manager updates the trust matrix once per wave, after the wave retrospective. Updates are based on observable metrics (PR quality, delivery reliability, review quality, collaboration) rather than subjective impression. At minimum, any team member whose trust score should change by +/-1 or more gets an update.

**Rationale:** "Whenever a trust-relevant interaction occurs" is too vague and was never triggered. A fixed cadence (per-wave) is actionable.

### Change 3: Feedback Log Minimum Entries

**Charter section affected:** Feedback System > Downward Feedback

**Current:** "Feedback is tracked in `.claude/team/feedback_log.md`."

**Change:** Add:
> Each wave MUST produce at least one feedback entry per reporting relationship that was active during the wave. If a lead had reports contributing to the wave, that lead must log feedback for each contributing report. The Manager must log feedback for each lead. Entries may be positive (severity: minor) or negative (severity: minor/moderate/severe). An empty feedback log at wave end is a process failure.

**Rationale:** Making it mandatory with a minimum count ensures the log is maintained. Allowing positive entries prevents the feedback system from being purely punitive.

### Change 4: Dependency Detection at Issue Creation

**Charter section affected:** Work Delegation & Issue Creation

**Current:** Issues are reviewed for individual completeness.

**Change:** Add to the review process:
> Reviewers must flag cross-issue dependencies. When two issues are likely to modify the same module or file, the reviewer adds a `depends-on: #N` line to both issue descriptions. The Manager uses these dependencies to sequence work within a wave (dependent issues go to the same engineer, or one is sequenced before the other).

**Rationale:** Cross-PR dependency issues (PR #229 needing PR #230's module, PRs #154 and #155 conflicting on `client.ts`) were discovered during implementation. Catching them at issue review time prevents blocking.

### Change 5: Reviewer Assignment at Wave Start

**Charter section affected:** Code Review & Tech Debt > Peer Review

**Current:** "Every software engineering branch must be reviewed by one other software engineer before merging."

**Change:** Replace with:
> At wave start, the Tech Lead (Dmitri) assigns a specific reviewer to each issue. The reviewer is notified at assignment time and is expected to follow the branch from first commit. The assignment is recorded on the GitHub Issue as a comment. Cross-module PRs (touching 3+ modules) are additionally reviewed by the System Architect (Renaud).

**Rationale:** Ad-hoc reviewer selection created inconsistent review depth and delays while engineers looked for an available reviewer.

### Change 6: Local Pre-Push Verification

**Charter section affected:** Branching Rules (new subsection)

**Change:** Add:
> Before pushing to remote, engineers must run `make lint` and `make test` locally. A pre-push hook enforcing this will be installed by the DevOps team. CI failures caused by lint/format violations that would have been caught locally are tracked as a negative signal in the trust matrix.

**Rationale:** The CI feedback loop (push -> wait 3-5 min -> see failure -> fix -> push again) consumed significant time across all phases. Commits like `528af07`, `94d7493`, `8106fd3`, and `e3cc63c` are all local-catchable failures.

### Change 7: Data Team Activation

**Charter section affected:** Role Definitions > Principal Data Engineer / Data Scientist

**Current:** Tariq and Mei-Lin's responsibilities are defined but they are never spawned.

**Change:** Add:
> After each pipeline phase (Phases 1-4, and any phase that modifies pipeline code), the Data Lead (Elena) spawns Tariq and/or Mei-Lin to validate pipeline output quality. Validation findings are filed as GitHub Issues. At minimum, the data team produces one data quality report per phase that touches the pipeline.

**Rationale:** The pipeline has never been validated by a data specialist. Entity resolution accuracy, topic classification quality, and graph metric correctness have all been assumed correct based on tests passing, not data analysis.

### Change 8: Fire/Hire Threshold Definition

**Charter section affected:** Feedback System > Firing and Hiring

**Current:** "When a team member is fired, their roster file is archived..."

**Change:** Add concrete thresholds:
> A team member is eligible for termination if ANY of the following are true:
> - Trust matrix average score drops below 2.0
> - Two or more moderate severity feedback entries in the same phase
> - One severe severity feedback entry
> - Zero contributions (PRs, issues, reviews) for 2 consecutive phases
>
> The Manager reviews eligible members at each team health check (every 2 phases) and decides whether to fire or put on improvement plan. An improvement plan lasts one wave; if no improvement, the member is fired.

**Rationale:** The fire/hire mechanism has never been triggered because there are no concrete thresholds. By this definition, Tariq and Mei-Lin would have been eligible after Phase 2 (zero contributions for 2 phases). Priya would have been eligible after Phase 4.

### Change 9: Wave Completion Checklist (Enforced by Skill)

**Charter section affected:** Branching Rules (new subsection)

**Change:** Add:
> Wave completion requires ALL of the following before the next wave begins:
> 1. All PRs merged into deployments branch
> 2. All referenced issues closed
> 3. `git worktree prune` executed
> 4. Retrospective document written
> 5. Feedback log entries added for all active reporting relationships
> 6. Trust matrix updated
> 7. Tech debt issues from reviews filed
>
> The `/wave-end` skill enforces items 1-4 and 7 automatically. Items 5-6 are the Manager and Tech Lead's responsibility.

**Rationale:** Wave transitions were the messiest part of the process. Issues left open, worktrees not pruned, retros skipped (Phases 0-4), feedback never logged. A mandatory checklist prevents items from falling through.

### Change 10: Skills and Hooks Adoption

**Charter section affected:** New section "Automation"

**Change:** Add:
> The following skills and hooks are standard team tooling:
> - `/retro` -- wave retrospective generation
> - `/wave-start` -- deployments branch creation + cleanup
> - `/wave-end` -- completion checklist + retro + issue closure
> - `/review-pr` -- charter-format review + tech debt filing
> - `/plan-phase` -- phase decomposition into issues
> - `/close-stale-issues` -- issue hygiene audit
>
> Hooks:
> - Post-commit: auto ruff format
> - Pre-PR: format check + merge latest base
> - Pre-push: branch naming verification
>
> See `docs/agent-teams-improvements.md` for full specifications.

**Rationale:** These skills and hooks encode the lessons of 7 phases into reusable automation. They prevent regression on process improvements that were hard-won through user feedback.

---

## Appendix A: Phase-by-Phase Interaction Summary

| Phase | Waves | PRs | Issues | Retro? | Feedback Log? | Trust Matrix Updated? | Notable Incidents |
|-------|-------|-----|--------|--------|---------------|----------------------|-------------------|
| 0 | 3 | 9 (#13-#21) | ~15 | No | No | No | Early phase, charter being established. PRs went to main initially, then deployments branches. |
| 1 | 3 | 12 (#33-#57) | ~20 | No | No | No | First full phase with deployments branches. Comment format adopted. Tech debt inconsistently filed. |
| 2 | 3 | 10 (#65-#89) | ~15 | No | No | No | Entity resolution work. Four tech debt PRs in Wave 1. Work gate respected. |
| 3 | 3 | 10 (#95-#109) | ~15 | No | No | No | Graph construction. Worktree collision (Kwame/Amara on `__init__.py`). Branch lock issues from Phase 2 worktrees. |
| 4 | 3 | 10 (#116-#135) | ~15 | No | No | No | Enrichment. Duplicate work in Wave 1 (4 tech debt PRs touching same module). Mid-wave issue creation. |
| 5 | 3+0 | 12 (#143-#172) | ~20 | Yes (first) | No | No | API + Frontend. Three concurrent frontend PRs with merge conflicts (#153-#155). CI pipeline introduced (Wave 0). |
| 6 | 3+0 | 10 (#184-#207) | ~15 | Yes | No | No | Testing + Quality. Bug fix wave (Wave 0) before main work. Formatting CI failures in Wave 2. |
| 7 | 3 | 8 (#221-#240) | ~20 | Yes | No | No | Security + Auth. Cross-PR dependency (#229/#230). Multiple CI fix commits. Open PR #240 for phase merge. |

**Totals:** ~80 PRs, ~135 issues, 3 retros, 0 feedback entries, 0 trust matrix updates.

## Appendix B: Agent Spawn Frequency by Person

Based on task system entries and PR authorship:

| Person | Spawn Count (est.) | Primary Tasks |
|--------|-------------------|---------------|
| Fatima | ~20 | Phase coordination, issue creation, retros, tech debt batches, doc audit |
| Kwame | ~15 | Core implementation across all phases (acquire, parse, resolve, graph, API, OAuth) |
| Hiro | ~14 | Parsers, frontend, visualization, validation, scraper |
| Carolina | ~12 | Tests, parsers, frontend pages, negative/fuzz testing, metadata enrichment |
| Amara | ~10 | Models, Arabic utils, NER, disambiguation, edges, graph search, Fawaz Arabic |
| Tomasz | ~6 | Docker, CI, coverage, CORS fixes |
| Renaud | ~3 | Issue reviews, diagram updates, PR reviews |
| Yara | ~2 | Security review, OWASP hardening |
| Elena | ~2 | Data validation framework, issue reviews |
| Sunita | ~1 | Issue reviews only |
| Dmitri | ~0 | Never spawned (issue review comments were generated without full agent context) |
| Priya | ~0 | Never spawned (issue review comments were generated without full agent context) |
| Tariq | 0 | Never spawned |
| Mei-Lin | 0 | Never spawned |

**Observation:** The top 5 members (Fatima, Kwame, Hiro, Carolina, Amara) account for approximately 90% of all agent spawns and work output. The bottom 5 (Dmitri, Priya, Sunita, Tariq, Mei-Lin) account for approximately 1%.
