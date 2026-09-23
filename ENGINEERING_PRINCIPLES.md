# Engineering Principles

These rules are mandatory for Job Tracker development and operations.

The operating model is:

```text
DESIGN FOR SCALE
-> TEST SMALL
-> VERIFY OUTPUT PARITY
-> TECHNICAL ACCEPTANCE
-> SCALE OUT
-> AUTOMATE
```

## 1. Explore fast, engineer before scaling

Fast experiments are allowed for discovery, debugging, API exploration, and proof-of-concept work.

Exploratory code is not automatically production code. Before scaling or automation, successful experiments must be converted into clear, maintainable, tested implementation.

## 2. Design for scale, prove with a small MVP

Architecture may target dozens of sources, but implementation must first prove itself on a small representative set.

Do not integrate a large source pack before the reusable path has passed real-data verification.

## 3. Configuration over company-specific code

Adding a compatible source should normally require a registry/configuration change only.

Prefer:

```text
source registry -> reusable adapter -> normalization -> history/change detection -> ranking -> publication
```

Avoid creating one scraper per company unless a reusable acquisition path cannot reasonably support the source.

## 4. Reuse adapters before adding special cases

Prefer shared API, ATS, structured-web, and generic acquisition adapters.

A new company-specific provider is justified only after the reusable paths have been tested and shown insufficient.

Shared pipeline code must not accumulate company-specific branching without a documented reason.

## 5. Stable contracts between stages

Each stage must have a clear input/output contract.

Acquisition must not leak provider-specific behavior into ranking or publication. Normalization is the boundary between source-specific acquisition and shared downstream processing.

## 6. Preserve working behavior

A new source or feature must not silently break an existing provider, dataset, feed, or history path.

Backward compatibility and regression coverage are required unless a breaking migration is explicitly approved.

## 7. Output parity is required

New acquisition paths must produce the same normalized Job Tracker contract where applicable.

Core outputs include:

- `jobs_latest.csv`
- `job_details.csv`
- `job_history.csv`
- `job_changes.csv`
- `department_summary.csv`
- `location_summary.csv`
- approved Patrick Target Feed outputs

CSV and JSON schemas are interfaces. Change them deliberately.

## 8. Never fake completeness

A source failure must remain visible.

Use explicit states such as:

- success
- incomplete
- failed
- unavailable
- manual_discovery

Never mark `coverage_complete=true` to obtain a green pipeline when acquisition was incomplete.

Counts and metadata must match the actual dataset.

## 9. Tests before scale-out

Before expanding a proven design to more sources, require:

- deterministic tests,
- regression tests,
- normalized output verification,
- real-source verification for representative sources,
- technical acceptance.

A large registry is not proof that acquisition works.

## 10. Private and public data stay separated

Private profile evidence, credentials, tokens, cookies, sessions, personal documents, and other sensitive material must never enter the public repository.

Public outputs may contain only explicitly approved derived information.

Secrets must remain in approved secret storage or ignored private runtime paths.

## 11. Manual proof before unattended automation

The sequence is:

```text
manual successful run
-> repeatability check
-> failure behavior check
-> scheduler installation
-> unattended verification
```

Do not automate an unverified pipeline.

## 12. Observability is part of the product

Every run must make it possible to determine:

- which sources were attempted,
- which succeeded,
- which failed or were incomplete,
- job counts,
- whether data changed,
- whether ranking changed,
- why publication was blocked.

A valid no-change run must still produce a clear status.

## 13. Git is the source of truth for code and approved public outputs

Normal delivery is:

```text
branch -> tests -> PR -> review -> merge
```

Do not make untracked production changes that cannot be reproduced from Git.

Do not force-push production publication history.

## 14. Fix the narrowest layer that is actually broken

Do not modify host, Docker, kernel, security, scheduler, or repository architecture merely because one helper tool fails.

Prefer the smallest scoped workaround or supported execution path.

Infrastructure changes require evidence that infrastructure is the real blocker.

## 15. One blocker, one owner, one task

Avoid recovery-task chains.

Ownership:

- Builder: implementation, tests, feature branch, PR
- CTO: architecture, scope, technical acceptance
- Engineering Operations: runtime, deployment, scheduler, production verification
- Human operator: only authorization or access that agents genuinely cannot perform

A blocker should be assigned to the owner capable of resolving it.

## 16. Complexity must earn its place

Do not add queues, microservices, caches, event buses, new frameworks, or additional services because they appear more sophisticated.

Add complexity only when a measured requirement justifies it.

Prefer a modular monolith until operational evidence requires otherwise.

## 17. Correctness and maintainability before optimization

First make acquisition, normalization, history, ranking, and publication correct and understandable.

Optimize performance, parallelism, and caching only after measurement identifies a real bottleneck.

## 18. Every architectural change must prove value

A change should produce at least one concrete benefit:

- less code per new source,
- less manual work,
- better reliability,
- better data quality,
- clearer failure handling,
- lower operating cost,
- easier maintenance.

If the benefit cannot be demonstrated, do not add the abstraction.

## 19. Stop at acceptance gates

When a phase is scoped as an MVP or proof, stop after its acceptance criteria pass.

Do not automatically continue into scale-out, deployment, or scheduler changes unless that next phase is explicitly approved.

## 20. Definition of done requires evidence

"Implemented" is not the same as "verified" or "production ready."

Use these meanings consistently:

- Implemented: code and deterministic tests exist.
- Verified: required real-data/runtime evidence passed.
- Production ready: verified implementation is deployed with required operational controls.
- Automated: production-ready path has completed unattended runs successfully.

## Decision rule

When uncertain, choose the simpler path that preserves correctness, traceability, privacy, and future extensibility.

Move fast during discovery. Engineer before scaling. Automate only after verification.
