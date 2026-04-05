# Retrospective: Phase 7 Wave 1 (Pre-Wave)
**Date:** 2026-03-16
**Covering:** Phase 6 delivery (Testing & Quality)
**Facilitator:** Fatima Okonkwo (Manager)

---

## Context

Phase 6 was the testing and quality phase. The team went from having no integration tests and no real data validation to having testcontainers infrastructure, Playwright browser automation, hypothesis-based fuzz testing, and a documentation audit. Four waves shipped. This retro covers what worked, what didn't, and what we carry into Phase 7 — the final stretch before the platform is deployable.

---

## Team Conversations

### Engineering Team (Dmitri -> Kwame, Amara, Hiro, Carolina)

**Dmitri's summary:** "Phase 6 was different from every phase before it. For the first time, the primary deliverables were tests, not features. That changes how the team works — you're validating assumptions instead of building on them, and that surfaced real problems.

Wave 0 was the wake-up call. We ran a 6-reviewer comprehensive review of the existing codebase and found 7 critical bugs: frontend type contract mismatches, incorrect API URLs, Docker configuration errors, and CORS issues. These were real blockers — not style nits, not minor edge cases. If we had shipped the Phase 5 output to users without Wave 0, they would have hit these bugs immediately. That review format worked and I want to acknowledge that directly: Priya and Yara finally got real review roles, and they caught things the engineering team missed.

Wave 1 introduced the testcontainers framework. We wrote 18 integration tests that run against real Neo4j and PostgreSQL instances instead of mocks. This was the first time we validated that our Cypher queries and SQL statements actually work against real databases. The coverage gate was set at 60% — below the 90% target, but realistic for where we are. We also landed the Apache 2.0 license and tracked 8 new tech-debt items.

Wave 2 was the heaviest wave. Real data flow testing validated the pipeline end-to-end — something we'd been deferring since the Phase 5 retro. Hiro's Playwright test suite delivered 11 browser automation tests covering the React frontend. Carolina and the team wrote 57 negative, boundary, and fuzz tests using hypothesis. That's a meaningful test surface.

Wave 3 was cleanup: documentation audit and removal of .coverage/.hypothesis artifacts that were polluting the repo.

The honest assessment: we did not reach 90% coverage. We're at 60%. That's a 30-point gap. Some of that is expected — the resolve module with CAMeLBERT and FAISS is hard to cover without real model inference, and the frontend React code isn't counted in Python coverage. But some of it is just incomplete work. We need to be honest about that gap rather than rationalizing it.

The process improvement that mattered most: branch protection enforcement. After the #153-155 incident in Phase 5 where PRs merged with failing CI, we enabled required status checks. In Phase 6, zero PRs merged with failing CI. The gate works when you actually use it."

**What went well:**
- Wave 0 comprehensive review caught 7 critical bugs before any Phase 6 implementation — the 6-reviewer format proved its value
- Branch protection enforced for the first time — zero PRs merged with failing CI, a complete reversal from the Phase 5 incident
- 18 integration tests against real databases via testcontainers replaced mock-based testing assumptions with real validation
- 57 negative/boundary/fuzz tests (hypothesis) and 11 Playwright browser tests added meaningful coverage to previously untested surfaces
- Priya and Yara had substantive roles for the first time — QA and security reviews caught bugs the engineering team missed
- Real data flow testing was finally executed after being deferred for two consecutive retros

**What didn't go well:**
- Coverage is at 60%, target was 90% — a 30-point gap that was not closed during the phase
- The 7 critical bugs found in Wave 0 should have been caught during Phase 5 reviews. Their existence means Phase 5 review quality was insufficient for frontend and integration concerns
- Worktree cleanup was not part of the process until the user got blocked by stale worktrees. We added it reactively, not proactively

**What to improve:**
- Coverage gap needs a concrete plan: identify the specific modules below target and assign owners. Don't treat 90% as an aspirational number — treat it as a backlog with line items
- Extend the Wave 0 comprehensive review format to future phases. It caught real bugs and should be standard practice, not a one-time experiment
- Worktree lifecycle management: create, use, clean up. Add this to the team charter as an explicit step

### Architecture (Renaud)

**Renaud's summary:** "Phase 6 validated what I've been saying since Phase 3: the architecture is sound but the assumptions were untested. Testcontainers proved the Neo4j Cypher queries work. Real data flow testing proved the pipeline stages connect. Playwright proved the frontend renders and interacts correctly. These are not new features — they're evidence that what we built actually works.

The testcontainers approach was the right call. Spinning up real Neo4j and PostgreSQL containers for integration tests is slower than mocks but catches an entirely different class of bugs. The Neo4j authentication issue we hit in CI — where testcontainers was trying to connect with default credentials that didn't match the container config — is exactly the kind of thing mocks would never surface.

My concern going into Phase 7: we're about to add authentication, authorization, and security hardening. These are cross-cutting concerns that touch every API endpoint, every frontend route, and the database layer. If the current test infrastructure can support testing authenticated flows end-to-end — testcontainers for the backend, Playwright for the frontend, with real auth tokens — then we're in good shape. If it can't, we'll need to extend the framework before we can validate any Phase 7 work.

The ADR log was still not created. Third retro in a row. I'm going to stop recommending it and just create it myself in Phase 7 Wave 0."

**What went well:**
- Testcontainers validated real database interactions — the Neo4j auth issue caught in CI proved the approach catches bugs mocks cannot
- The architecture supported testing at every layer (unit, integration, browser, fuzz) without requiring structural changes
- Real data flow testing confirmed pipeline stage connections work end-to-end

**What didn't go well:**
- ADR log still does not exist — third consecutive retro where this was recommended and not acted on
- No assessment of whether the test infrastructure can support authenticated flow testing, which is the primary Phase 7 concern

**What to improve:**
- Create the ADR log in Phase 7 Wave 0. No more deferring. Renaud will own this directly
- Audit the testcontainers and Playwright infrastructure for auth-flow readiness before Phase 7 implementation begins. If extensions are needed, they go in Wave 0

### DevOps (Sunita -> Tomasz, Yara)

**Sunita's summary:** "Phase 6 was a validation of the CI investment we made in Phase 5. Branch protection was enabled and enforced — no exceptions, no overrides. Every PR in Phase 6 passed CI before merge. That's the single most important process change we made, and it held.

CI caught real issues during Phase 6. The Neo4j authentication configuration in testcontainers didn't match what CI expected — tests passed locally but failed in the pipeline. Formatting drift showed up again on branches that were created before the latest ruff fixes landed. Both were caught by CI, both were fixed before merge. The system worked as designed.

Tomasz added dependency caching to the CI pipeline, which cut build times. The torch download problem from Phase 5 is less painful now, though we should consider whether torch needs to be in the default test dependencies at all.

Yara's security review in Phase 6 was her most substantive yet. She reviewed the testcontainers configuration for credential leaks, checked that .coverage and .hypothesis files weren't being committed with sensitive data, and reviewed the Playwright test suite for hardcoded credentials. For Phase 7, Yara is going to be central — auth implementation, security hardening, and secrets management are all in scope. She needs to be involved from Wave 0, not brought in for reviews after the fact.

The worktree cleanup issue was embarrassing. The user got blocked because stale worktrees were accumulating and we had no process for cleaning them up. We added cleanup steps after the fact, but this should have been part of our workflow from the beginning. Lesson learned."

**What went well:**
- Branch protection enforced across all of Phase 6 — zero failing-CI merges, a complete fix for the Phase 5 gap
- CI caught real issues: Neo4j testcontainers auth mismatch, formatting drift on stale branches
- Dependency caching reduced CI build times
- Yara conducted substantive security review of test infrastructure (credential leaks, .coverage/.hypothesis data, Playwright hardcoded creds)

**What didn't go well:**
- Worktree cleanup was reactive — user got blocked before we added it to the process
- No automated security scanning (dependency audit, secret detection) despite this being recommended in two prior retros

**What to improve:**
- Yara must be involved in Phase 7 from Wave 0 — auth and security are the core deliverables, not review afterthoughts
- Add automated dependency scanning and secret detection to CI. This has been deferred long enough and Phase 7 (auth, secrets management) makes it non-negotiable
- Formalize worktree lifecycle in the team charter: create, use, clean up after merge

### Data Team (Elena -> Tariq, Mei-Lin)

**Elena's summary:** "Phase 6 finally delivered what I've been asking for since Phase 4: real data through the pipeline. The real data flow tests in Wave 2 validated that our parsers, entity resolution, and graph loaders work with actual data, not just synthetic fixtures. It surfaced issues — encoding edge cases, unexpected null patterns, API response shapes that didn't match our assumptions — and we fixed them. That's exactly what was supposed to happen.

The hypothesis-based fuzz testing was a good addition. It generated Arabic text edge cases that we never would have written by hand: mixed diacritics, unusual Unicode normalization forms, zero-width characters embedded in narrator names. Some of these caused failures in the normalization utilities, which were fixed. Those are real bugs that would have hit users processing non-standard text.

For Phase 7, the data team's role is smaller — auth, security, and deployment are not our primary domain. But data quality validation should continue. We should be running the validation framework against real pipeline output on a regular basis, not just once during a testing phase. And if Phase 7 introduces any API authentication that gates access to data endpoints, we need to validate that authenticated data flows return the same results as unauthenticated flows did in Phase 6 testing."

**What went well:**
- Real data flow testing finally executed — encoding issues, null patterns, and API response shape mismatches surfaced and were fixed
- Hypothesis fuzz testing caught Arabic text edge cases (mixed diacritics, unusual Unicode forms, zero-width characters) that caused real normalization bugs
- The validation framework built in Phase 5 was actually used against real data for the first time

**What didn't go well:**
- Real data testing was a one-time event, not an ongoing process. No scheduled re-validation exists
- Coverage of the resolve module (CAMeLBERT, FAISS) remains low because real model inference is expensive and slow to test

**What to improve:**
- Establish recurring data validation — even if it's a weekly CI job that runs a subset of the pipeline against real data. One-time validation is a snapshot, not assurance
- When Phase 7 adds auth to data endpoints, validate that authenticated responses match the unauthenticated baseline from Phase 6

---

## Consolidated Themes

### Top 3 Things Going Well
1. **Branch protection works and held.** Zero PRs merged with failing CI in Phase 6. The #153-155 incident from Phase 5 was not repeated. This is the most important process improvement the team has made — automation over discipline.
2. **Testing infrastructure is real.** Testcontainers (18 integration tests), Playwright (11 browser tests), hypothesis (57 fuzz tests), and real data flow validation — the platform now has evidence that it works, not just assertions. CI caught real bugs (Neo4j auth, formatting drift) that would have been invisible without this infrastructure.
3. **The 6-reviewer comprehensive review format works.** Wave 0 caught 7 critical bugs that would have blocked users. Priya and Yara had substantive roles for the first time. This format should be standard, not exceptional.

### Top 3 Pain Points
1. **Coverage is at 60%, target is 90%.** A 30-point gap that was not closed during the testing phase. Some of this is structural (resolve module, frontend code), but some is incomplete work. This is technical debt that compounds — every new feature added in Phase 7 without corresponding tests widens the gap.
2. **Phase 5 review quality was insufficient for frontend and integration concerns.** The 7 critical bugs found in Wave 0 existed because Phase 5 reviews didn't catch them. The team's review expertise is backend-heavy; frontend type contracts, API URL correctness, and Docker integration were blind spots.
3. **Repeated recommendations go unacted.** The ADR log has been recommended for three consecutive retros. Automated security scanning has been recommended for two. Real data validation was recommended for two before it finally happened. The team needs to either act on retro recommendations or explicitly decide not to — carrying them forward indefinitely is not a process, it's a backlog.

### Proposed Process Changes for Phase 7
1. **Yara embedded from Wave 0.** Phase 7 is auth, security, and deployment. Yara is not a reviewer — she is a primary implementer. She should co-own the auth implementation with the engineering team, not review it after the fact. Sunita to coordinate Yara's involvement in Wave 0 planning.
2. **Create the ADR log.** Renaud will own this in Wave 0. Retroactively document decisions from Phases 5-6 (API versioning, pagination format, testcontainers approach, branch protection). Going forward, every architectural decision gets a one-line entry with the PR number.
3. **Add automated security scanning to CI.** Dependency audit and secret detection. Phase 7 introduces OAuth, secrets management, and production deployment — we cannot ship these without automated security checks in the pipeline. Tomasz to implement in Wave 0.
4. **Coverage plan with module-level owners.** Dmitri to identify the specific modules below 60% and the specific modules that need to reach 90%. Assign owners. Track coverage per module, not just as a single aggregate number. The 90% target is a backlog, not a wish.

---

## Final Note

We're entering the final stretch. Phases 0-5 built the platform. Phase 6 proved it works. Phase 7 is what makes it deployable: authentication, security hardening, data quality gates, and operational infrastructure. The remaining work — OAuth providers, Terraform, billing design, admin dashboard, API docs, service health — is the difference between a working prototype and a production system. The team has earned the right to be here. Now we finish.

---

*Next retro scheduled after Phase 7 Wave 1 completes.*
