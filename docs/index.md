

<div class="hero-matrix" align="center">
  <h1 class="hero-pixel">
    Your codebase remembers.<br>
    <span class="text-accent">Even when your team forgets.</span>
  </h1>
  <p class="hero-subtitle">
    Extract institutional memory directly from git. Local-first, zero telemetry, and built for terminal workflows.
  </p>
  
  <div style="margin-top: 2rem; display: flex; gap: 1rem; justify-content: center;">
    <a href="cli/" class="md-button md-button--primary">Get Started</a>
    <a href="architecture/" class="md-button">Read the Architecture</a>
  </div>
</div>

---

## The Inspiration

Here is a story every developer knows.

**September.** The auth service goes down for two hours. Someone cached authentication tokens in Redis, and password resets didn't invalidate the cache. Users remained authenticated with revoked credentials for 120 minutes.

The team debates, argues, and learns. The hard rule is set: *"Never cache auth responses."* It gets written in a comment on Merge Request `!42`. Everyone agrees. Everyone moves on.

**Six months later.** A new developer joins. She opens an issue: *"Add Redis caching to auth to improve latency."* Nobody remembers September. Nobody remembers MR `!42`. She ships the exact same bug.

We have all been on these teams. We watch the same decisions get made, forgotten, and repeated. Not because anyone is careless, but because decisions live in pull request threads nobody will ever reopen, or in the heads of engineers who have already left. Every "Architecture Decision Record" (ADR) tool requires someone to manually write things down. Nobody does. 

So we built **LORE-X** (Living Organisational Record Engine).

---

## What is LORE-X?

LORE-X is an autonomous architectural memory engine. It passively monitors Git activity, extracts the intent behind architectural decisions using local or cloud LLMs, and stores them as structured tuples with full lifecycle tracking.

Unlike conventional RAG systems that retrieve documents based solely on semantic text overlap, LORE-X understands that decisions age, fail, and get superseded. Its **Hybrid Retrieval Engine** factors in temporal validity, outcome status, and graph lineage alongside semantic relevance—eliminating temporal hallucination entirely.

### The 5-Layer Engine

Whether running locally in your terminal or hooked into your CI/CD pipeline, LORE-X acts as a slightly haunted senior engineer who has seen things break, performing a 5-layer analysis on your code:

1. **Memory Conflicts:** Semantic analysis against stored decisions. LORE-X recognizes that "in-memory dict caching" *is* "Redis caching on auth tokens" because the failure mode is identical. This is reasoning about equivalence, not keyword matching.
2. **Promise Verification:** Holds developers to their own words. *"You said 30-second TTL in the issue. Your code says 30 minutes."*
3. **Security Sentinel:** Cross-references new code against past security incidents and team-specific vulnerabilities.
4. **Code Intelligence:** Detects new dependencies, architectural patterns, and technology drift directly from the staged diff.
5. **Pattern Enforcement:** Automatically enforces rules captured from past code reviews. Reviewers never have to repeat themselves.

---

## The Experience Tuple

Every architectural decision is captured locally in SQLite as a 7-dimensional tuple $(P, A, C, V, O, T, S)$:

| Dimension | Description |
|-----------|-------------|
| **Problem** ($P$) | The engineering challenge that triggered the decision. |
| **Action** ($A$) | The specific architectural decision applied to solve it. |
| **Conditions** ($C$) | Boundary conditions under which the action remains valid. |
| **Evidence** ($V$) | Concrete artifacts backing the decision (e.g., Commit SHAs, PR links). |
| **Outcome** ($O$) | The empirical result observed after applying the action. |
| **Temporal Validity** ($T$) | The lifespan of the decision (from `valid_from` until `valid_until`). |
| **Status** ($S$) | Current health: `VERIFIED`, `CONDITIONALLY_VALID`, `SUPERSEDED`, or `FAILED`. |

---

## Quick Start

LORE-X is built for the terminal. Install it, ingest your repository, and never lose an architectural decision again.

```bash
# Install globally via uv
uv tool install git+https://github.com/Surydevx/LORE-X.git

# Initialize the SQLite memory ledger in your repo
cd /path/to/your/repo
lorex init

# Ingest your project's commit history and extract decisions
lorex ingest . --limit 20

# Intercept bad decisions before you commit
git add .
lorex check

# Explore your codebase's memory
lorex log
lorex query "database connection pooling"
lorex dashboard
```