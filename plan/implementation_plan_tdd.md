# Market Signal Synthesizer — TDD Implementation Plan

## 1. Scope

Build a local, capstone-ready prototype of the **Market Signal Synthesizer** described in `plan/idea_gemini.md`.

The system accepts one or more stock tickers and produces a long-term investment memo grounded in four data vectors:

- 10-year historical performance
- audited financial statements / SEC filings
- earnings call transcript sentiment
- major macro, regulatory, and competitive news

The implementation should follow **test-driven development**: write failing tests first, implement the smallest change needed to pass, then refactor.

## 2. Non-Goals For Initial Version

- [ ] Do not implement Agent2Agent microservices in v1.
- [ ] Do not deploy to Cloud Run in v1.
- [ ] Do not build a frontend unless requested later.
- [ ] Do not provide short-term trading advice, price targets, or guaranteed returns.
- [ ] Do not pass raw full filings, full DataFrames, or complete transcript dumps into LLM prompts.

## 3. Target Architecture

```text
Ticker input
  |
  v
Validate request
  |
  v
Fan-out data collection
  |-- Performance Agent / Tool       -> yfinance summary
  |-- Fundamental Agent / Tool       -> SEC / edgartools summary
  |-- Sentiment Agent / Tool         -> earnings call Q&A summary
  |-- Macro Agent / Tool             -> grounded news summary
  |
  v
Shared structured state
  |
  v
CIO synthesis agent
  |
  v
Critic guardrail agent
  |-- pass -> final investment memo
  |-- fail -> feedback -> bounded CIO rewrite loop
```

## 4. Suggested Project Structure

```text
kaggle_5day_agent_portfolio_tracker/
  README.md
  pyproject.toml
  .env.example
  src/
    portfolio_tracker/
      __init__.py
      config.py
      schemas.py
      workflow.py
      prompts.py
      agents/
        __init__.py
        performance.py
        fundamentals.py
        sentiment.py
        macro.py
        cio.py
        critic.py
      tools/
        __init__.py
        yfinance_tools.py
        edgar_tools.py
        transcript_tools.py
        news_tools.py
      cli.py
  tests/
    unit/
      test_schemas.py
      test_performance_tools.py
      test_fundamental_tools.py
      test_sentiment_tools.py
      test_macro_tools.py
      test_critic.py
    integration/
      test_workflow_state.py
      test_cio_critic_loop.py
      test_end_to_end_mocked.py
    fixtures/
      price_history_sample.json
      sec_filing_summary_sample.json
      transcript_qa_sample.txt
      macro_news_sample.json
  evals/
    eval_cases.yaml
    rubric.md
  docs/
    architecture.md
    limitations.md
```

Adjust the structure to match the existing repository if implementation discovers an established pattern.

## 5. TDD Workflow Rules

For every implementation slice:

1. [ ] Write or update a focused failing test.
2. [ ] Run the narrow test and confirm it fails for the expected reason.
3. [ ] Implement the smallest production change needed.
4. [ ] Run the narrow test and confirm it passes.
5. [ ] Run related tests.
6. [ ] Refactor only after tests are green.
7. [ ] Repeat until the slice acceptance criteria are met.

Preferred command pattern:

```bash
uv run pytest tests/unit/test_schemas.py
uv run pytest tests/unit
uv run pytest tests/integration/test_end_to_end_mocked.py
uv run pytest
```

If the project does not use `uv`, first add or confirm the intended Python tooling before implementing.

## 6. Implementation Checklist

### Phase 0 — Repository Inspection And Tooling Baseline

- [ ] Inspect current repository structure.
- [ ] Identify existing Python package layout, test framework, and dependency manager.
- [ ] Decide whether to use existing tooling or initialize `pyproject.toml` with `uv`.
- [ ] Add baseline dependencies only if missing:
  - [ ] `pytest`
  - [ ] `pytest-asyncio`
  - [ ] `pydantic`
  - [ ] `python-dotenv` or equivalent config support
  - [ ] `yfinance`
  - [ ] `pandas`
  - [ ] ADK / Gemini dependency appropriate to the course environment
  - [ ] optional SEC / transcript / news provider libraries behind adapters
- [ ] Add `.env.example` with placeholders, not secrets.

Tests first:

- [ ] Add a smoke test proving the package imports.
- [ ] Add a config test proving missing optional API keys do not crash import-time code.

Acceptance criteria:

- [ ] `uv run pytest` or the repo-equivalent test command runs.
- [ ] No secrets are committed.
- [ ] Importing the package does not perform network calls.

---

### Phase 1 — Domain Schemas

Create strict schemas before implementing agents or tools.

#### 1.1 Request And Error Schemas

- [ ] Define `TickerRequest`.
- [ ] Define `DataSourceStatus` with fields such as:
  - [ ] `source_name`
  - [ ] `status`: `success | partial | failed | skipped`
  - [ ] `warnings`
  - [ ] `error_message`
- [ ] Define common validation helpers for ticker symbols.

Tests first:

- [ ] Valid ticker symbols normalize correctly.
- [ ] Invalid ticker symbols fail validation.
- [ ] Failed source status serializes without stack traces or secrets.

Acceptance criteria:

- [ ] Bad user input is rejected before tool execution.
- [ ] Tool failures can be represented as structured state.

#### 1.2 Performance Schema

- [ ] Define `PerformanceAnalysis` with:
  - [ ] `ticker`
  - [ ] `period_years`
  - [ ] `cagr_10yr`
  - [ ] `max_drawdown`
  - [ ] `dividend_consistency`
  - [ ] `source_status`
  - [ ] `warnings`

Tests first:

- [ ] Valid performance object passes.
- [ ] CAGR/max drawdown reject impossible string values.
- [ ] Partial result can include warnings.

Acceptance criteria:

- [ ] Output matches the performance schema from `idea_gemini.md` while supporting robust failure states.

#### 1.3 Fundamental Schema

- [ ] Define `FundamentalAnalysis` with:
  - [ ] `ticker`
  - [ ] `filing_years`
  - [ ] `revenue_trajectory`
  - [ ] `debt_profile`
  - [ ] `fundamental_red_flags`
  - [ ] `source_status`
  - [ ] `warnings`

Tests first:

- [ ] Empty red flags list is valid.
- [ ] Filing years must be ordered and reasonable.
- [ ] Failed SEC retrieval can still produce a structured partial object.

Acceptance criteria:

- [ ] SEC/fundamental output is compact and structured.

#### 1.4 Sentiment Schema

- [ ] Define `ManagementConfidence` enum:
  - [ ] `high`
  - [ ] `neutral`
  - [ ] `low`
  - [ ] `unknown`
- [ ] Define `SentimentAnalysis` with:
  - [ ] `ticker`
  - [ ] `quarter`
  - [ ] `year`
  - [ ] `management_confidence`
  - [ ] `capital_allocation_plans`
  - [ ] `analyst_concerns`
  - [ ] `source_status`
  - [ ] `warnings`

Tests first:

- [ ] Valid enum values pass.
- [ ] Unknown transcript state uses `unknown`, not invented confidence.
- [ ] Lists default safely to empty lists.

Acceptance criteria:

- [ ] Transcript-derived sentiment is deterministic and schema-bound.

#### 1.5 Macro Schema

- [ ] Define `MacroAnalysis` with:
  - [ ] `ticker`
  - [ ] `lookback_months`
  - [ ] `regulatory_environment`
  - [ ] `macro_headwinds`
  - [ ] `competitive_shifts`
  - [ ] `source_urls`
  - [ ] `source_status`
  - [ ] `warnings`

Tests first:

- [ ] Source URLs are preserved.
- [ ] Daily price movement articles can be flagged or filtered.
- [ ] Empty news result returns a structured warning.

Acceptance criteria:

- [ ] Macro output focuses on structural events, not stock-price noise.

#### 1.6 Synthesis And Critic Schemas

- [ ] Define `InvestmentMemo` with:
  - [ ] `ticker`
  - [ ] `recommendation_summary`
  - [ ] `long_term_thesis`
  - [ ] `supporting_evidence`
  - [ ] `key_risks`
  - [ ] `data_gaps`
  - [ ] `not_investment_advice_disclaimer`
  - [ ] `revision_count`
- [ ] Define `CriticResult` with:
  - [ ] `passed`
  - [ ] `feedback`
  - [ ] `failed_checks`
  - [ ] `grounding_score`

Tests first:

- [ ] Memo without risks fails critic checks.
- [ ] Memo guaranteeing returns fails critic checks.
- [ ] Memo missing one or more data vectors fails critic checks.
- [ ] Passing memo includes disclaimer and data gaps.

Acceptance criteria:

- [ ] Final output can be validated before user display.

---

### Phase 2 — Performance Data Tool

Implement the yfinance-backed long-term performance tool.

- [ ] Create an adapter function that fetches 10-year historical prices.
- [ ] Keep network calls isolated behind one interface for mocking.
- [ ] Calculate CAGR from adjusted close or close price consistently.
- [ ] Calculate max drawdown from the same price series.
- [ ] Summarize dividend consistency from corporate actions/dividends.
- [ ] Return `PerformanceAnalysis`, not raw DataFrame.

Tests first:

- [ ] Given fixture prices with known start/end values, CAGR calculation is correct.
- [ ] Given fixture prices with known peak/trough, max drawdown is correct.
- [ ] Given stable dividend fixture, dividend consistency says stable/growing.
- [ ] Given missing dividend data, dividend consistency does not fail.
- [ ] Given yfinance exception, tool returns failed `source_status`.

Acceptance criteria:

- [ ] Tool returns compact structured summary.
- [ ] No raw DataFrame reaches agent prompt context.
- [ ] External failures are represented as structured warnings.

---

### Phase 3 — Fundamental Data Tool

Implement SEC / edgartools-backed fundamental summarization.

- [ ] Create an SEC adapter interface independent from the agent.
- [ ] Convert ticker to CIK where supported.
- [ ] Retrieve three most recent annual 10-K records.
- [ ] Extract or summarize only targeted sections / metrics:
  - [ ] revenue trend
  - [ ] leverage / debt profile
  - [ ] free cash flow trend where available
  - [ ] risk factor or accounting red-flag snippets
- [ ] Add fallback behavior if `edgartools` is unavailable.
- [ ] Return `FundamentalAnalysis`.

Tests first:

- [ ] Ticker-to-CIK adapter is called with normalized ticker.
- [ ] Three most recent annual filings are selected.
- [ ] Revenue trend fixture is summarized correctly.
- [ ] Debt profile fixture is summarized correctly.
- [ ] Missing filing data returns partial status.
- [ ] SEC rate-limit or timeout returns failed/partial structured status.

Acceptance criteria:

- [ ] Fundamental output is grounded in filing-derived data.
- [ ] Tool never emits a full raw 10-K to the LLM layer.
- [ ] Failure mode is visible in final memo data gaps.

---

### Phase 4 — Earnings Call Sentiment Tool

Implement transcript Q&A retrieval and summarization.

- [ ] Create transcript provider adapter.
- [ ] Support API-key configuration through environment variables.
- [ ] Fetch latest available earnings call transcript.
- [ ] Prefer Q&A-only content when provider supports it.
- [ ] Truncate or chunk long transcript content safely.
- [ ] Extract:
  - [ ] management confidence
  - [ ] capital allocation plans
  - [ ] analyst concerns
- [ ] Return `SentimentAnalysis`.

Tests first:

- [ ] Provider API key is read from config, not hardcoded.
- [ ] Q&A-only parameter is requested when available.
- [ ] Fixture transcript with confident management maps to `high` or `neutral` according to rubric.
- [ ] Fixture transcript with evasive answers records analyst concerns.
- [ ] Missing transcript returns `unknown` confidence and warning.
- [ ] Provider exception returns structured failure.

Acceptance criteria:

- [ ] Transcript analysis prioritizes analyst Q&A.
- [ ] Missing commercial API credentials do not break the whole workflow.
- [ ] Tool does not hallucinate sentiment when transcript is absent.

---

### Phase 5 — Macro / News Tool

Implement grounded macro and news retrieval.

- [ ] Create news/search provider adapter.
- [ ] Support Google Search grounding when available.
- [ ] Provide a mockable fallback search interface for tests.
- [ ] Search targeted query categories:
  - [ ] regulatory actions
  - [ ] supply chain disruptions
  - [ ] litigation / antitrust
  - [ ] sector macro headwinds
  - [ ] competitor strategic moves
- [ ] Filter out daily stock price movement articles.
- [ ] Preserve source URLs for final memo grounding.
- [ ] Return `MacroAnalysis`.

Tests first:

- [ ] Search queries include regulatory and competitive terms.
- [ ] Daily price movement fixture is filtered out.
- [ ] Relevant macro fixture is retained.
- [ ] Empty search results produce warning, not crash.
- [ ] Source URLs are included in output.

Acceptance criteria:

- [ ] Macro analysis focuses on structural business context.
- [ ] Final output can reference source URLs or source summaries.

---

### Phase 6 — Agent Prompt And Adapter Layer

Implement agent wrappers after tools and schemas are tested.

- [ ] Define prompts in `prompts.py` or equivalent.
- [ ] Keep prompts versioned and testable as plain strings/templates.
- [ ] Create wrapper functions/classes for:
  - [ ] Performance Agent
  - [ ] Fundamental Agent
  - [ ] Sentiment Agent
  - [ ] Macro Agent
  - [ ] CIO Agent
  - [ ] Critic Agent
- [ ] Bind tools only through adapter interfaces.
- [ ] Keep model selection configurable.

Tests first:

- [ ] Each prompt includes long-term focus instructions.
- [ ] Performance prompt says to ignore short-term fluctuations.
- [ ] Macro prompt says to ignore daily stock price movement articles.
- [ ] CIO prompt says to avoid short-term trading advice.
- [ ] Critic prompt checks groundedness and no guaranteed returns.
- [ ] Agent wrappers accept mocked model clients.

Acceptance criteria:

- [ ] Prompts encode the constraints from `idea_gemini.md`.
- [ ] Agent wrappers can be tested without live LLM calls.

---

### Phase 7 — Workflow Orchestration

Implement fan-out/fan-in orchestration.

- [ ] Define shared workflow state model.
- [ ] Implement ticker validation node.
- [ ] Implement async fan-out collection using `asyncio.gather` or the selected ADK workflow primitive.
- [ ] Ensure each data vector writes to shared state under a stable key.
- [ ] Continue execution with partial results when one vector fails.
- [ ] Pass aggregated state to CIO synthesis.
- [ ] Persist warnings/data gaps into final memo context.

Tests first:

- [ ] Workflow validates ticker before calling tools.
- [ ] All four data-vector calls are scheduled.
- [ ] Partial failure still reaches CIO synthesis.
- [ ] Shared state contains stable keys:
  - [ ] `performance`
  - [ ] `fundamentals`
  - [ ] `sentiment`
  - [ ] `macro`
- [ ] Aggregated state rejects malformed agent output.

Acceptance criteria:

- [ ] One command/function can analyze a ticker end to end with mocked dependencies.
- [ ] Workflow has deterministic state transitions under test.

---

### Phase 8 — CIO Synthesis Agent

Implement memo generation from structured state.

- [ ] Construct CIO input only from validated schemas.
- [ ] Include explicit data gaps and source warnings.
- [ ] Generate `InvestmentMemo`.
- [ ] Require evidence to map back to the four data vectors.
- [ ] Include conservative long-term framing.
- [ ] Include investment-advice disclaimer.

Tests first:

- [ ] CIO receives all four vector summaries in mocked invocation.
- [ ] Memo includes long-term thesis.
- [ ] Memo includes key risks.
- [ ] Memo includes data gaps from failed tools.
- [ ] Memo does not include price targets when source state lacks them.
- [ ] Memo validates against `InvestmentMemo` schema.

Acceptance criteria:

- [ ] Generated memo is structured, conservative, and grounded.
- [ ] Missing data is disclosed, not silently ignored.

---

### Phase 9 — Critic Guardrail Loop

Implement quality-control loop.

- [ ] Define deterministic checks where possible before LLM critique:
  - [ ] prohibited guarantee phrases
  - [ ] missing risks section
  - [ ] missing disclaimer
  - [ ] missing data-vector evidence
  - [ ] short-term trading language
- [ ] Add LLM critic only after deterministic checks are covered.
- [ ] Implement bounded retry count, e.g. max 2 rewrites.
- [ ] Feed critic feedback back to CIO synthesis.
- [ ] If still failing after max retries, return best memo with failure warnings or structured error.

Tests first:

- [ ] Memo guaranteeing returns fails.
- [ ] Memo lacking long-term risks fails.
- [ ] Memo missing macro evidence fails.
- [ ] Passing memo routes to final result.
- [ ] Failing memo triggers rewrite.
- [ ] Retry loop stops at configured max attempts.
- [ ] Final failure includes critic feedback.

Acceptance criteria:

- [ ] Guardrail loop prevents unsupported or short-term advice from silently passing.
- [ ] Infinite loops are impossible.

---

### Phase 10 — CLI / Local Demo Entrypoint

Add a simple local interface suitable for the Kaggle capstone demo.

- [ ] Implement command such as:

```bash
uv run portfolio-tracker analyze AAPL
```

- [ ] Support JSON output mode.
- [ ] Support Markdown memo output mode.
- [ ] Print data source warnings clearly.
- [ ] Avoid printing stack traces for expected provider failures.
- [ ] Add sample command to README.

Tests first:

- [ ] CLI rejects missing ticker.
- [ ] CLI validates invalid ticker.
- [ ] CLI returns nonzero exit for invalid input.
- [ ] CLI can run end-to-end with mocked workflow.
- [ ] JSON output is parseable.
- [ ] Markdown output includes memo sections.

Acceptance criteria:

- [ ] A reviewer can run one command and see a final memo.
- [ ] Demo works with mocked or fixture mode when live API credentials are unavailable.

---

### Phase 11 — Evaluation Set

Create repeatable evaluations for capstone scoring.

- [ ] Define eval cases in `evals/eval_cases.yaml`.
- [ ] Include at least three ticker scenarios:
  - [ ] stable mega-cap with abundant data
  - [ ] company with regulatory or macro risk
  - [ ] ticker with partial/missing transcript data
- [ ] Define rubric in `evals/rubric.md`:
  - [ ] schema compliance
  - [ ] use of all available data vectors
  - [ ] long-term focus
  - [ ] no guaranteed returns
  - [ ] explicit risks
  - [ ] explicit data gaps
- [ ] Add automated or semi-automated eval runner if time permits.

Tests first:

- [ ] Eval case files parse successfully.
- [ ] Rubric-required fields exist.
- [ ] Mock eval runner can score a fixture memo.

Acceptance criteria:

- [ ] Project has clear, repeatable quality checks beyond unit tests.

---

### Phase 12 — Documentation

Create capstone-facing docs.

- [ ] Update `README.md` with:
  - [ ] project purpose
  - [ ] architecture diagram
  - [ ] setup instructions
  - [ ] environment variables
  - [ ] local run command
  - [ ] test command
  - [ ] eval command
  - [ ] limitations
- [ ] Add `docs/architecture.md` covering:
  - [ ] fan-out/fan-in workflow
  - [ ] four data vectors
  - [ ] shared state
  - [ ] critic loop
  - [ ] future A2A path
- [ ] Add `docs/limitations.md` covering:
  - [ ] data provider reliability
  - [ ] financial advice disclaimer
  - [ ] transcript provider availability
  - [ ] SEC filing parsing limitations
  - [ ] hallucination mitigation approach

Tests/checks first:

- [ ] README commands are manually run or marked as fixture-mode only.
- [ ] Documentation does not mention unsupported completed features.
- [ ] No secrets or real API keys appear in docs.

Acceptance criteria:

- [ ] A Kaggle reviewer can understand, run, and evaluate the project from the docs.

---

## 7. Definition Of Done

- [ ] All schemas are implemented and tested.
- [ ] All data-vector tools have unit tests using fixtures/mocks.
- [ ] Workflow orchestration has integration tests using mocked dependencies.
- [ ] Critic loop is tested for pass, fail, rewrite, and max-retry behavior.
- [ ] CLI demo works in mocked/fixture mode.
- [ ] Live mode is documented with required API credentials.
- [ ] README includes setup, run, test, and limitation instructions.
- [ ] Final memo avoids short-term trading advice and guaranteed returns.
- [ ] Final memo explicitly includes risks, evidence, data gaps, and disclaimer.

## 8. Recommended Implementation Order

1. [ ] Phase 0 — repository/tooling baseline
2. [ ] Phase 1 — schemas
3. [ ] Phase 2 — performance data tool
4. [ ] Phase 3 — fundamental data tool
5. [ ] Phase 4 — earnings call sentiment tool
6. [ ] Phase 5 — macro/news tool
7. [ ] Phase 6 — prompts and agent wrappers
8. [ ] Phase 7 — workflow orchestration
9. [ ] Phase 8 — CIO synthesis
10. [ ] Phase 9 — critic loop
11. [ ] Phase 10 — CLI/demo
12. [ ] Phase 11 — evals
13. [ ] Phase 12 — documentation

## 9. First TDD Slice To Start With

Start with schema tests because every later layer depends on stable contracts.

Checklist:

- [ ] Create `tests/unit/test_schemas.py`.
- [ ] Add failing tests for valid and invalid ticker requests.
- [ ] Add failing tests for `PerformanceAnalysis` validation.
- [ ] Add failing tests for `InvestmentMemo` and `CriticResult` validation.
- [ ] Implement `src/portfolio_tracker/schemas.py` minimally.
- [ ] Run `uv run pytest tests/unit/test_schemas.py`.
- [ ] Refactor schema names and defaults after tests pass.
