# ADR-001: Attribution Strategy

**Status:** Accepted
**Date:** 2026-04-20
**Deciders:** @DDay-FG

## Context

This repository is a maintained fork of `trevin-creator/autoresearch-mlx`. At the point of forking, the entire production code surface (`train.py`, `prepare.py`, `program.md`, `pyproject.toml`) and the initial `README.md` were authored by the upstream author. The fork's initial public state attributed none of this work.

Two pressures conflict:

1. This repository should present clear intellectual ownership of the downstream work done in it (reporting tooling, Rust CLI, tests, documentation, configuration layer, and empirical run notes).
2. The upstream author's authorship must not be erased. The project license (MIT) requires preservation of copyright notices. Independent of license, scrubbing attribution of work one did not write is dishonest and, to any reader willing to inspect the git history, detectable.

## Decision

Keep the full git history as-is. Do not rewrite or force-push. Add explicit attribution via three mechanisms:

1. A `NOTICE` file at the repository root, listing the upstream author, the conceptual lineage (Karpathy's autoresearch, scasella's MLX GPT patterns, Apple's MLX team), and the downstream contributions made in this fork.
2. A rewritten `README.md` in the downstream maintainer's voice that names the upstream fork in its opening prose and links to `NOTICE` for full detail.
3. A `CITATION.cff` file listing only the downstream maintainer's handle (`DDay-FG`) for citation of *this fork specifically*, with the understanding that citation of the autoresearch concept itself should be directed at Karpathy's upstream.

## Options Considered

### Option A: Force-push to remove upstream commits

| Dimension | Assessment |
|-----------|------------|
| Feasibility | Blocked by local `permissions.deny` policy |
| Honesty | Low — scrubs authorship of work not done by the maintainer |
| License compliance | Risks MIT copyright-notice preservation requirement |
| Detectability | High — GitHub fork graph, archive.org, anyone who cloned earlier |

### Option B: Keep history + add NOTICE + rewrite README (chosen)

| Dimension | Assessment |
|-----------|------------|
| Feasibility | Straightforward additive work |
| Honesty | High — every contributor is named |
| License compliance | Clean |
| Detectability | N/A; nothing is hidden |

### Option C: Keep history, do nothing more

| Dimension | Assessment |
|-----------|------------|
| Effort | Zero |
| Reader experience | Ambiguous — the repo reads as an unattributed copy |

## Trade-off Analysis

Option A was rejected on honesty grounds even before feasibility ruled it out. Option C was rejected because the status quo produces a worse signal to a careful reader than honest attribution does. Option B preserves license compliance, preserves lineage, and makes downstream work legible as downstream work — which is what accurately describes it.

## Consequences

- The `git log` of this repository will always show the upstream author's commits at its base. That is a feature, not a defect.
- Future contributors (agents or humans) should not force-push `main`.
- Downstream work accumulates on top of the preserved base; the `NOTICE` file is updated when new external contributions arrive.

## Action Items

- [x] Create `NOTICE`
- [x] Rewrite `README.md`
- [x] Author `CITATION.cff` with handle-only attribution
- [ ] Tag the upstream tip as `v0.1-upstream` and the first downstream release as `v0.2-DDay-FG` (optional, can be done anytime)
