---
title: "PR Risk Scorer Bootstrap"
description: "Python CLI tool analyzing GitHub PRs for failure risk prediction"
status: completed
priority: P1
effort: "10h"
branch: main
tags: [python, cli, github, risk-scoring]
created: 2026-02-18
---

# PR Risk Scorer - Implementation Plan

## Dependency Graph & Parallel Execution Strategy

```
Phase 01 (Foundation) ──┬──> Phase 02 (GitHub Client)    ──┐
                        ├──> Phase 03 (Analyzers A)       ──┤
                        ├──> Phase 04 (Analyzers B)       ──┤──> Phase 07 (CLI + E2E)
                        ├──> Phase 05 (Scoring Engine)    ──┤
                        └──> Phase 06 (Output Formatters) ──┘

Parallel Groups:
  Group 1: [Phase 01]              -- sequential, must complete first
  Group 2: [Phase 02, 03, 04, 05, 06]  -- all parallel after Phase 01
  Group 3: [Phase 07]              -- sequential, after all Group 2 complete
```

## File Ownership Matrix

| Phase | Exclusive Files |
|-------|----------------|
| 01 | `pyproject.toml`, `src/pr_risk_scorer/__init__.py`, `models.py`, `config.py`, `base_analyzer.py`, `.pr-risk-scorer.yaml` |
| 02 | `github_client.py`, `tests/test_github_client.py` |
| 03 | `blast_radius.py`, `hot_path.py`, `ownership.py`, `tests/test_analyzers/test_blast_radius.py`, `test_hot_path.py`, `test_ownership.py` |
| 04 | `dependency.py`, `review.py`, `complexity.py`, `analyzers/__init__.py`, `tests/test_analyzers/test_dependency.py`, `test_review.py`, `test_complexity.py` |
| 05 | `scoring/__init__.py`, `weighted_scorer.py`, `tests/test_scoring/test_weighted_scorer.py` |
| 06 | `output/__init__.py`, `terminal_reporter.py`, `json_reporter.py`, `markdown_reporter.py`, `tests/test_output/*` |
| 07 | `cli.py`, `tests/conftest.py`, `tests/test_cli.py`, `README.md`, `.github/workflows/ci.yml` |

## Phase Summary

| Phase | Name | Effort | Depends On | Status |
|-------|------|--------|------------|--------|
| 01 | [Project Setup & Foundation](./phase-01-project-setup-and-foundation.md) | 1.5h | none | completed |
| 02 | [GitHub Client](./phase-02-github-client.md) | 1h | 01 | completed |
| 03 | [Analyzers Group A](./phase-03-analyzers-group-a.md) | 1.5h | 01 | completed |
| 04 | [Analyzers Group B](./phase-04-analyzers-group-b.md) | 1.5h | 01 | completed |
| 05 | [Scoring Engine (Hybrid)](./phase-05-scoring-engine.md) | 0.5h | 01 | completed |
| 06 | [Output Formatters](./phase-06-output-formatters.md) | 1h | 01 | completed |
| 07 | [CLI Integration & E2E](./phase-07-cli-integration-and-e2e.md) | 2.5h | 01-06 | completed |

## Execution Strategy

1. **Phase 01** runs first -- establishes all shared contracts (models, config, base class)
2. **Phases 02-06** run in parallel -- each owns exclusive files, no conflicts possible
3. **Phase 07** integrates everything -- wires CLI, creates conftest fixtures, runs E2E
4. Each phase includes its own unit tests; Phase 07 adds integration tests

## Key Architectural Decisions

- **Hybrid Scoring Model**: Linear weighted baseline + amplification multiplier when 2+ analyzers > 70
- **Strategy/Plugin pattern** for analyzers: `BaseAnalyzer` ABC with `analyze(pr_data) -> AnalyzerResult`
- **Pydantic v2** for all data models: validation, serialization, config loading
- **Rich** for terminal output: tables, color-coded risk levels, progress bars
- **PAT-based auth** for GitHub API: simplest for CLI, env var `GITHUB_TOKEN`
- **CI/CD**: GitHub Actions (lint + test + publish to PyPI on tag)

---

## Validation Log

### Session 1 — 2026-02-18
**Trigger:** Initial plan validation before implementation
**Questions asked:** 7

#### Questions & Answers

1. **[Architecture]** Plan sử dụng Weighted Linear Model. Research cũng gợi ý Multiplicative. Approach nào?
   - Options: Weighted Linear | Multiplicative | Hybrid
   - **Answer:** Hybrid
   - **Rationale:** Combines interpretability of linear with risk amplification of multiplicative

2. **[Scope]** MVP dùng heuristics cho HotPath (confidence=0.6) và Ownership (confidence=0.5)?
   - Options: OK heuristics | Implement git-blame now | Drop from MVP
   - **Answer:** OK, heuristics for MVP
   - **Rationale:** Ship fast, improve later with real git-blame data

3. **[Architecture]** Build system preference?
   - Options: Hatchling | Poetry | uv + hatchling
   - **Answer:** Hatchling
   - **Rationale:** Minimal, standard PEP 517/518

4. **[Scope]** Output formats for MVP?
   - Options: All 3 | Terminal + JSON | Terminal only
   - **Answer:** All 3 (Terminal, JSON, Markdown)
   - **Rationale:** ~1h total, covers interactive/CI/PR comment use cases

5. **[Architecture]** Hybrid scoring multiplier logic?
   - Options: 0.15/analyzer | 0.10 conservative | 0.20 aggressive
   - **Answer:** Agent-defined (user defers to implementation)
   - **Rationale:** Use 0.15 as reasonable default, configurable

6. **[Scope]** Report command scope?
   - Options: Keep as stub | Basic implementation | Remove
   - **Answer:** Basic implementation
   - **Rationale:** Fetch recent PRs, analyze each, output summary. +1.5h

7. **[DevOps]** GitHub Actions CI/CD?
   - Options: Basic CI | No CI | CI + PyPI publish
   - **Answer:** CI + publish to PyPI
   - **Rationale:** Full pipeline: lint, test, publish on tag. +30min

#### Confirmed Decisions
- Hybrid scoring: linear baseline + amplification when 2+ analyzers > 70
- Heuristics OK for HotPath/Ownership in MVP
- Hatchling build system
- All 3 output formats (terminal, JSON, markdown)
- Report command: basic implementation (not stub)
- CI/CD: GitHub Actions + PyPI publish on tag

#### Action Items
- [ ] Update Phase 05: Hybrid scoring model instead of pure weighted linear
- [ ] Update Phase 07: Implement basic `report` command, add CI/CD workflow
- [ ] Update Phase 07 file ownership: add `.github/workflows/ci.yml`

#### Impact on Phases
- Phase 05: Scoring algorithm changes from pure linear to hybrid (add amplification logic)
- Phase 07: Report command needs real implementation (+1.5h); CI/CD workflow added (+30min)
