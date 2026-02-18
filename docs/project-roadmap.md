# PR Risk Scorer - Project Roadmap

## Current Status (v0.1.0 - Beta)

**Release Date**: 2026-02-18
**Status**: Feature Complete, Production Ready
**Coverage**: 100% test coverage, 111 tests passing

### v0.1.0 Completion Checklist

- [x] Core scoring engine with 6 analyzers
- [x] GitHub API integration (PyGithub)
- [x] CLI with 3 commands (analyze, report, config)
- [x] Multiple output formats (terminal, JSON, Markdown)
- [x] YAML configuration system
- [x] Full test suite (100% coverage)
- [x] Code standards documentation
- [x] Architecture documentation
- [x] Comprehensive README

**Release Notes**:
- Initial beta release
- All core features implemented
- Stable API (subject to feedback)
- Ready for team adoption

---

## Planned Features & Roadmap

### Phase 1: v0.2.0 (Q1 2026) - Performance & Caching

**Goal**: Reduce repeated analysis latency, improve scalability

**Features**:
- [ ] Redis caching layer for PR analysis results
  - Cache key: `{owner}/{repo}#{pr_number}`
  - TTL: 24 hours (configurable)
  - Estimated 90% reduction in re-analysis latency
- [ ] Parallel analyzer execution via ThreadPoolExecutor
  - Run all 6 analyzers concurrently
  - Estimated 5-6x speedup for single PR analysis
- [ ] GitHub GraphQL support (batch queries)
  - Replace REST API calls with single GraphQL query
  - Reduce API calls from ~5 to 1 per PR
- [ ] Batch analysis optimization
  - Cache intermediate results
  - Detect common patterns across PRs

**Success Metrics**:
- Single PR analysis: <200ms (vs current 200-500ms)
- Batch report (10 PRs): <2s (vs current 5-10s)
- Repeat analysis: <100ms (cached)

**Implementation Effort**: 40-50 hours

---

### Phase 2: v0.3.0 (Q2 2026) - Advanced Analysis

**Goal**: Improve risk prediction accuracy with multi-language support and historical trends

**Features**:
- [ ] Multi-language complexity detection
  - Python, JavaScript/TypeScript, Java, Go, Rust
  - Language-agnostic AST analysis
  - Nesting depth, cyclomatic complexity per language
- [ ] Historical trend tracking
  - Store analysis results in SQLite/PostgreSQL
  - Track score trends per repository
  - Identify regression patterns (PRs that pass review but cause incidents)
- [ ] ML-based threshold tuning
  - Collect post-merge incident data
  - Adjust risk thresholds based on actual outcomes
  - Per-repository threshold customization
- [ ] Author pattern detection
  - Track individual contributor risk profiles
  - Flag new contributors or unfamiliar authors
  - Team-based risk adjustment

**Success Metrics**:
- Risk prediction accuracy: 80%+ incident correlation
- False positive reduction: <10%
- Repository-specific threshold accuracy: +15% over global

**Implementation Effort**: 60-80 hours

---

### Phase 3: v0.4.0 (Q3 2026) - Integrations & Automation

**Goal**: Seamless CI/CD integration and automated decision-making

**Features**:
- [ ] GitHub Actions integration
  - Official action in GitHub Marketplace
  - Auto-comment on PR with risk assessment
  - Block merge if score exceeds threshold
  - Example workflow template
- [ ] Slack integration
  - Daily/weekly risk reports to Slack
  - Real-time alerts for HIGH/CRITICAL PRs
  - Interactive scoring details via Slack blocks
- [ ] Webhook support
  - Expose HTTP endpoint for PR events
  - Trigger analysis on PR open/update
  - Deliver results to external systems
- [ ] Web dashboard (optional)
  - Visualize PR risk trends
  - Repository-level risk metrics
  - Team performance analytics

**Success Metrics**:
- GitHub Actions action: 100+ installs
- Slack integration adoption: 5+ teams
- Dashboard user engagement: 10+ active teams

**Implementation Effort**: 70-100 hours

---

### Phase 4: v0.5.0 (Q4 2026) - Enterprise Features

**Goal**: Team-wide governance, audit, and compliance

**Features**:
- [ ] Role-based access control (RBAC)
  - Admin (full access)
  - Reviewer (read all, config review only)
  - Developer (self-PR analysis only)
- [ ] Audit logging
  - Who analyzed which PR, when
  - Configuration changes tracked
  - Score history per PR
- [ ] Compliance reporting
  - Export risk metrics for compliance audits
  - Risk policy enforcement per team
  - SLA tracking (e.g., HIGH PRs reviewed within 4h)
- [ ] Custom analyzer plugin system
  - Allow teams to define custom analyzers
  - Entry point-based plugin loading
  - Sandboxed execution (optional)

**Success Metrics**:
- Enterprise trial adoption: 3+ organizations
- Audit log completeness: 100% of actions tracked
- Plugin ecosystem: 5+ community plugins

**Implementation Effort**: 80-120 hours

---

## Known Issues & Technical Debt

| Issue | Impact | Planned Fix | Priority |
|-------|--------|---|---|
| No caching of API results | Slow batch reports | Redis cache (v0.2) | High |
| Python-biased complexity | Limited polyglot support | Multi-language AST (v0.3) | Medium |
| No trend tracking | Can't detect regressions | Time-series DB (v0.3) | High |
| Static thresholds | One-size-fits-all model | ML tuning (v0.3) | Medium |
| No authorization | Single-user CLI only | RBAC (v0.5) | Low |
| Limited integrations | Siloed tool | CI/CD integ (v0.4) | Medium |

---

## Milestone Timeline

```
2026
├── Q1 (Jan-Mar)
│   ├── Jan 18: v0.1.0 Release (Beta) ✓
│   ├── Feb: Documentation & user feedback
│   ├── Mar: v0.2.0 Planning
│   └── Late Mar: v0.2.0 Development Start
│
├── Q2 (Apr-Jun)
│   ├── May: v0.2.0 Release (Performance)
│   ├── May: v0.3.0 Planning (Multi-language)
│   └── Jun: v0.3.0 Development Start
│
├── Q3 (Jul-Sep)
│   ├── Aug: v0.3.0 Release (Advanced Analysis)
│   ├── Aug: v0.4.0 Planning (Integrations)
│   └── Sep: v0.4.0 Development Start
│
└── Q4 (Oct-Dec)
    ├── Oct: Early access (Integrations)
    ├── Nov: v0.4.0 Release (Integrations)
    ├── Nov: v0.5.0 Planning (Enterprise)
    └── Dec: v0.5.0 Development Start
```

---

## Feature Dependency Graph

```
v0.1.0 (Base)
    ↓
    ├─→ v0.2.0 (Caching) ← Low-hanging fruit, 5x speedup
    │       ├─→ v0.3.0 (Trends, ML tuning)
    │       │       └─→ v0.5.0 (Enterprise, RBAC)
    │       └─→ v0.4.0 (Integrations)
    │
    └─→ v0.3.0 (Multi-language) ← Independent, can run in parallel with v0.2.0
            ├─→ Trend analysis
            ├─→ ML-based tuning
            └─→ Better accuracy for polyglot repos
```

---

## Success Metrics (v0.1.0 - v1.0.0)

### Adoption
| Metric | v0.1 | v0.4 | v1.0 |
|--------|------|------|------|
| Teams using | 5 | 50 | 200+ |
| Monthly active users | 50 | 500 | 2,000+ |
| PyPI downloads | 100 | 5,000 | 50,000+ |
| GitHub stars | 50 | 500 | 2,000+ |

### Quality & Reliability
| Metric | Target | Current |
|--------|--------|---------|
| Test coverage | 100% | 100% ✓ |
| Production issues | <1% of PRs analyzed | 0 (beta) |
| Response time (single PR) | <500ms | 200-500ms ✓ |
| API availability | 99.9% | 99.9%+ (depends on GitHub) ✓ |

### Risk Prediction Accuracy
| Metric | Target | Status |
|--------|--------|--------|
| Detect risky PRs | 80%+ | TBD (collecting data) |
| False positives | <10% | TBD (collecting data) |
| Post-merge incidents from analyzed PRs | <20% | TBD (collecting data) |

---

## Contributing & Community

### How to Contribute

1. **Report Issues**: [GitHub Issues](https://github.com/your-org/pr-risk-scorer/issues)
2. **Feature Requests**: Label `enhancement`, describe use case
3. **Code Contributions**: Fork, create feature branch, submit PR
4. **Documentation**: Improve docs, add examples, translate

### Development Setup

```bash
git clone https://github.com/your-org/pr-risk-scorer.git
cd pr-risk-scorer
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -v --cov
```

### PR Review Checklist

Before merging:
- [ ] Tests pass (100% coverage)
- [ ] Linting passes (`ruff check`)
- [ ] Docstrings & type hints
- [ ] CHANGELOG.md updated
- [ ] README updated if needed
- [ ] Security review (if API changes)

---

## Funding & Support

### Open Source Maintenance

Currently maintained by: [@tranhoangtu](https://github.com/tranhoangtu)

### Sponsorship Options (Future)

- GitHub Sponsors (when available)
- Commercial support tier (v0.4+)
- Enterprise licensing (v1.0+)

### Code of Conduct

Be respectful, inclusive, and constructive. [Full CoC](../CODE_OF_CONDUCT.md)

---

## Version Strategy

### Semantic Versioning

- **MAJOR** (X.0.0): Breaking changes, new product tier
- **MINOR** (0.X.0): New features, backward compatible
- **PATCH** (0.0.X): Bug fixes, no API changes

**Current**: v0.1.0 (Beta, active development)
**Stability**: All APIs subject to change until v1.0.0

### Release Cycle

- Estimated: Every 6-8 weeks
- Security patches: ASAP
- LTS version: TBD after v1.0.0

---

## Long-Term Vision (v1.0+)

**Goal**: Become the industry standard for PR risk assessment

### Products (Possible Future)

1. **Community Edition** (Open Source)
   - CLI tool, GitHub integration
   - Free, self-hosted
   - Community support via GitHub Discussions

2. **Team Edition** (SaaS)
   - Web dashboard with trends
   - Slack/Teams integration
   - Role-based access control
   - $X/month per team

3. **Enterprise Edition**
   - On-premise deployment
   - Custom analyzers
   - Advanced audit logging
   - SSO/SAML
   - SLA support

### Integration Roadmap

```
GitHub ✓ → GitLab → Bitbucket → Gitea → Forgejo
```

### Analyzer Expansion

```
Current (6): Blast Radius, Hot Path, Complexity, Ownership, Dependency, Review
Future (+6):
  - Security (CVE detection, dependency vulnerabilities)
  - Performance (metrics, benchmarks)
  - Test Coverage (coverage changes, test quality)
  - Documentation (doc changes, completeness)
  - Maintainability (code smells, technical debt)
  - Author Reputation (contributor history, team knowledge)
```

---

**Last Updated**: 2026-02-18
**Current Version**: v0.1.0 (Beta)
**Next Review**: 2026-05-18 (post v0.2.0)
**Status**: Actively Maintained
