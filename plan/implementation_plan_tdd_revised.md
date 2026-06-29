# Market Signal Synthesizer — TDD Implementation Plan (Revised)

This document is a revised, capstone-ready implementation blueprint for the **Market Signal Synthesizer** (originally specified in `plan/idea_gemini.md` and planned in `plan/implementation_plan_tdd.md`). It incorporates corrections for critical engineering pitfalls related to Google's Agent Development Kit (ADK 2.0) graph execution, state limits, and error handling.

## 2. Scope & Boundaries

The system accepts a stock ticker symbol and generates a structured long-term investment memo based on four data vectors:
1. **10-Year Historical Performance** (via `yfinance`)
2. **Audited Financial Reports** (via `edgartools` / SEC 10-K)
3. **Earnings Call Transcript Q&A Sentiment** (via `EarningsCall` API)
4. **Macro & Regulatory News** (via `Google Search` Grounding)

### Non-Goals
* No Agent2Agent (A2A) microservices in v1 (reserved for future scaling).
* No Cloud Run deployment in v1 (local execution only).
* No frontend UI (CLI interface is the capstone entrypoint).
* No short-term trading recommendations or price targets.
* No raw file dumps passed to the LLM (summarization/filtering happens at the tool/node boundary).
---

## 3. Corrected Target Architecture

```text
       Ticker Input
             │
             ▼
      Validate Request (Node)
             │
             ├───────────────────────┬───────────────────────┬───────────────────────┐ (Fan-Out)
             ▼                       ▼                       ▼                       ▼
      Performance Node       Fundamental Node        Sentiment Node          Macro Node
      (yfinance adapter)    (edgartools adapter)    (EarningsCall API)    (Search Grounding)
             │                       │                       │                       │
       [Yields Event(output)   [Yields Event(output)   [Yields Event(output)   [Yields Event(output)
       or Failsafe Event]      or Failsafe Event]      or Failsafe Event]      or Failsafe Event]
             │                       │                       │                       │
             └───────────────────────┼───────────────────────┼───────────────────────┘
                                     ▼
                              JoinNode (ADK 2.0)
                                     │
                                     ▼
                            AggregatorNode (Deterministic Code)
                                     │ (Builds SynthesizerInput)
                                     ▼
                            CIO Synthesis Node (LlmAgent - gemini-1.5-pro)
                                     │
                                     ▼
                            Critic Node (LlmAgent + Check Code)
                                     ├────────────────────────┐
                                     ▼ (fail)                 ▼ (pass)
                              Feedback Loop              Final Memo (END)
                            (Max 2 iterations)
```

---

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

---

## 5. TDD Workflow Rules

For every implementation step:
1. Write a focused failing test in `tests/`.
2. Confirm the test fails with the expected assertion error.
3. Write the minimum code in `src/` to make it pass.
4. Run pytest (`uv run pytest <test_path>`) to confirm the test is green.
5. Refactor only when tests are green.
6. Verify no live HTTP requests are triggered during unit tests.

---

## 5.1 Additional Implementation Instructions

* Use parallel subagents where work can be split safely.
* At the end of each phase, provide a concise commit message.
* Keep this plan's checkboxes updated as phase tasks are completed.
* Maintain `plan/implementation/phaseXX.md` notes for each phase.
* Each phase note must summarize completed plan steps, high-level codebase changes, additional implementation decisions, and tests created.
* Name test files to clearly match the module under test where practical.

---

## 6. Implementation Checklist

### Phase 0 — Repository Inspection, Tooling & Mocking Setup
* [x] Inspect repository structure.
* [x] Inspect existing Python tooling. If no `pyproject.toml` or equivalent project configuration exists, initialize one with `uv` and set up `pyproject.toml`.
* [x] Add core dependencies: `pytest`, `pytest-asyncio`, `pytest-mock`, `pydantic`, `python-dotenv`, `yfinance`, `pandas`.
* [x] Create `tests/fixtures/` and populate it with sample JSON/txt data for yfinance history, SEC filings, transcript Q&A, and news search results.
* [x] Write a test fixture helper that intercepts socket connections or patches HTTP requests to prevent live network calls during test execution.
* [x] Write a package import smoke test.
* [x] Add a `.env.example` file with configuration placeholders.

**Acceptance Criteria:**
* `uv run pytest` runs successfully.
* Unit tests fail cleanly when attempting network access.

---

### Phase 1 — Domain Schemas
Create Pydantic models in `src/portfolio_tracker/schemas.py`.

#### 1.1 Request, Status & Shared Structures
* [x] Define `TickerRequest` (validates ticker structure, length, uppercase).
* [x] Define `DataSourceStatus` (Enum: `SUCCESS`, `PARTIAL`, `FAILED`, `SKIPPED`).
* [x] Define `BaseVectorAnalysis` containing shared status/warning fields:
  * `ticker: str`
  * `status: DataSourceStatus`
  * `warnings: list[str]`
  * `error_message: Optional[str] = None`

#### 1.2 Vector-Specific Schemas (Inherit from `BaseVectorAnalysis`)
* [x] Define `PerformanceAnalysis`:
  * `period_years: int`
  * `cagr_10yr: Optional[float] = None`
  * `max_drawdown: Optional[float] = None`
  * `dividend_consistency: Optional[str] = None`
* [x] Define `FundamentalAnalysis`:
  * `filing_years: list[int]`
  * `revenue_trajectory: Optional[str] = None`
  * `debt_profile: Optional[str] = None`
  * `fundamental_red_flags: list[str] = Field(default_factory=list)`
* [x] Define `SentimentAnalysis`:
  * `quarter: Optional[str] = None`
  * `year: Optional[int] = None`
  * `management_confidence: str` (e.g. `High`, `Neutral`, `Low`, `Unknown`)
  * `capital_allocation_plans: list[str] = Field(default_factory=list)`
  * `analyst_concerns: list[str] = Field(default_factory=list)`
* [x] Define `MacroAnalysis`:
  * `regulatory_environment: Optional[str] = None`
  * `macro_headwinds: list[str] = Field(default_factory=list)`
  * `competitive_shifts: list[str] = Field(default_factory=list)`
  * `source_urls: list[str] = Field(default_factory=list)`

#### 1.3 Synthesis, Aggregator & Critic Schemas
* [x] Define `SynthesizerInput` (Aggregated structure combining the outputs of all 4 vectors, used to feed the CIO Agent deterministically).
* [x] Define `InvestmentMemo`:
  * `ticker: str`
  * `recommendation_summary: str`
  * `long_term_thesis: str`
  * `supporting_evidence: dict = Field(default_factory=dict)` (mapped to vectors)
  * `key_risks: list[str] = Field(default_factory=list)`
  * `data_gaps: list[str] = Field(default_factory=list)`
  * `not_investment_advice_disclaimer: str`
  * `revision_count: int`
* [x] Define `CriticResult`:
  * `passed: bool`
  * `feedback: list[str] = Field(default_factory=list)`
  * `failed_checks: list[str] = Field(default_factory=list)`
  * `grounding_score: float`

**Acceptance Criteria:**
* Tests prove schemas reject impossible values (e.g., max drawdown > 0%, CAGR as string, invalid ticker requests).
* Failed status payloads serialize cleanly without secrets or tracebacks.

---

### Phase 2 — Performance Data Tool
Implement the yfinance-backed quantitative metrics tool in `src/portfolio_tracker/tools/yfinance_tools.py`.

* [x] Implement quantitative helper functions to calculate CAGR and max drawdown from a price Series (no LLM involved).
* [x] Wrap yfinance API calls behind an adapter class `YFinanceAdapter`.
* [x] Ensure transient HTTP/network exceptions propagate up to allow ADK retries.
* [x] Implement tool-level validation: if data is returned empty or truncated, return a structured warning.

**TDD Tests:**
* Mock yfinance history call with a 10-year stable/rising price fixture and assert CAGR calculation is mathematically correct.
* Mock yfinance with a price drop fixture and assert Max Drawdown is correct.
* Mock missing dividend events and assert dividend consistency defaults safely to "No dividends recorded" rather than throwing an exception.

---

### Phase 3 — Fundamental Data Tool
Implement SEC 10-K extraction in `src/portfolio_tracker/tools/edgar_tools.py`.

* [x] Implement `EdgarAdapter` to query filings using `edgartools`.
* [x] Map ticker symbols to CIK and query the 3 most recent 10-Ks.
* [x] Implement programmatic extraction of MD&A (Item 7) and Financial Statements (Item 8) summaries.
* [x] Keep raw text length bounded: extract key financial metrics and summary paragraphs, rather than dumping full chapters to prompt context.
* [x] Ensure Rate Limit errors or temporary SEC blocks propagate to trigger retries.

**TDD Tests:**
* Mock `edgartools` responses using standard 10-K fixtures.
* Verify extraction limits: assert extracted context size is kept under 15,000 characters.
* Verify missing filings generate a `DataSourceStatus.PARTIAL` status with a structured warning instead of a process crash.

---

### Phase 4 — Earnings Call Sentiment Tool
Implement transcript processing in `src/portfolio_tracker/tools/transcript_tools.py`.

* [x] Implement `TranscriptAdapter` with support for optional API keys loaded from `config.py`.
* [x] Implement a toggle or preference for `qa_only` retrieval to filter out boilerplate corporate remarks.
* [x] Implement text chunking/summarization to keep transcript size bounded (under 10,000 characters).
* [x] Let authentication or connection exceptions propagate to the framework for retry.

**TDD Tests:**
* Verify that a missing API key results in a `DataSourceStatus.SKIPPED` status with an explicit warning "EarningsCall API credentials missing".
* Test with a transcript Q&A mock containing defensive executive remarks, verifying the agent extracts the analyst concerns.

---

### Phase 5 — Macro / News Grounding Tool
Implement competitive and macroeconomic search in `src/portfolio_tracker/tools/news_tools.py`.

* [ ] Implement `MacroNewsAdapter` behind a provider interface.
* [ ] Support Google Search Grounding as the preferred live provider when available.
* [ ] Support a mock fixture provider for offline tests and capstone demo mode.
* [ ] Optionally support a fallback search provider if Google Search Grounding is unavailable in the local environment.
* [ ] Define targeted search queries (e.g. `"<Ticker> antitrust litigation"`, `"<Ticker> supply chain risk"`).
* [ ] Filter out daily stock market ticker price commentary using negative search terms (e.g., `-stock -shares -"price action"`).
* [ ] Capture and format source URLs for final memo citations.

**TDD Tests:**
* Verify search queries contain long-term risk and regulatory keywords.
* Test news filtering logic using a mock containing both stock-price noise and regulatory news, confirming the stock price articles are successfully excluded.

---

### Phase 6 — Agent Prompt and Node Wrapper Layer
Define the prompts in `src/portfolio_tracker/prompts.py` and wrap agents in `src/portfolio_tracker/agents/`.

* [ ] Implement LLM Agents for the 4 data vectors using `gemini-2.5-flash`.
* [ ] Write strict instructions directing the sub-agents to output strictly schema-bound JSON corresponding to their respective `Analysis` schemas.
* [ ] Write the CIO Agent instruction (requires `gemini-1.5-pro` for deep reasoning) focusing on long-term capital preservation, risk identification, and data gaps.
* [ ] Write the Critic Agent instruction (using `gemini-2.5-flash`) checking against short-term speculation, guaranteed returns, and grounding correctness.

**TDD Tests:**
* Verify prompts contain explicit constraints: no price targets, no short-term speculation, explicit inclusion of risk sections and the disclaimer.
* Mock the Gemini client responses and verify agent wrapper classes correctly parse LLM outputs into Pydantic models.

---

### Phase 7 — Workflow Orchestration (Fan-Out & Join Node)
Implement graph assembly in `src/portfolio_tracker/workflow.py`.

* [ ] Define the ADK `Workflow` class instance.
* [ ] **Critical Failsafe Node Wrappers:** Wrap the Performance, Fundamental, Sentiment, and Macro agents in a node function that catches final data/provider exceptions and yields a failsafe event. Do not swallow framework control-flow exceptions such as cancellation or human-in-the-loop interruption:
  ```python
  import asyncio

  def is_framework_interruption(exc: Exception) -> bool:
      # Keep version-specific ADK interruption/HITL errors out of broad
      # data-provider fallback handling. Replace/extend this helper once the
      # selected ADK version exposes its concrete interruption exception path.
      return exc.__class__.__name__ in {"NodeInterruptedError"}

  async def failsafe_sentiment_node(ctx: Context):
      try:
          result = await ctx.run_node(sentiment_agent)
          yield Event(output=result)
      except asyncio.CancelledError:
          raise
      except Exception as e:
          if is_framework_interruption(e):
              raise
          yield Event(
              output=SentimentAnalysis(
                  ticker=ctx.state.get("ticker"),
                  status=DataSourceStatus.FAILED,
                  warnings=[f"Sentiment agent failed: {str(e)}"],
                  management_confidence="Unknown",
              )
          )
  ```
* [ ] Define the `JoinNode` to collect outputs:
  ```python
  from google.adk.workflow import JoinNode
  collector = JoinNode(name="collector")
  ```
* [ ] **Deterministic Aggregator Node:** Implement a function node after `JoinNode` to parse the merged results and construct the `SynthesizerInput` model.
  ```python
  def aggregate_outputs(node_input: dict) -> Event:
      # node_input is the collection of events from collector
      # Extract each vector, validate and build SynthesizerInput
      return Event(output=synthesizer_input)
  ```
* [ ] Set up the execution edges:
  ```python
  edges = [
      ("START", validate_request),
      (validate_request, failsafe_performance_node, collector),
      (validate_request, failsafe_fundamental_node, collector),
      (validate_request, failsafe_sentiment_node, collector),
      (validate_request, failsafe_macro_node, collector),
      (collector, aggregate_outputs, cio_synthesis_node),
      ...
  ]
  ```

**TDD Tests:**
* Mock three vectors passing and one vector throwing an exception, verify that `JoinNode` does not hang and the workflow proceeds to completion.
* Assert that `aggregate_outputs` successfully compiles the four distinct payloads into a single structured `SynthesizerInput` event.

---

### Phase 8 — CIO Synthesis Node
* [ ] Pass the aggregated `SynthesizerInput` from the `AggregatorNode` into the CIO Agent's prompt context.
* [ ] Direct the CIO Agent to produce an `InvestmentMemo` Pydantic model.
* [ ] Ensure any vector with a `FAILED` or `PARTIAL` status is explicitly flagged in the `data_gaps` list of the final memo.

**TDD Tests:**
* Verify that if a data vector failed (e.g. Sentiment), the generated investment memo lists "Sentiment data unavailable" in the `data_gaps` section.
* Assert the CIO output validates successfully against the `InvestmentMemo` Pydantic schema.

---

### Phase 9 — Critic Guardrail Loop
* [ ] Implement deterministic Python rules checking the `InvestmentMemo` content *before* invoking the LLM Critic:
  * Check for the presence of the word "disclaimer" or the required disclosure text.
  * Check that `key_risks` is not empty.
  * Check for prohibited speculatory terms (e.g. "guaranteed return", "no risk").
* [ ] If deterministic checks fail, route directly back to the CIO Agent with specific feedback without invoking the LLM Critic, saving tokens.
* [ ] If deterministic checks pass, invoke the LLM Critic Agent to verify factual grounding.
* [ ] Implement a bounded counter in `ToolContext.state["revision_count"]`. Limit retries to a maximum of 2 iterations.
* [ ] If the memo fails after 2 iterations, return the best-effort memo with a visible header warning about failed guardrails.

**TDD Tests:**
* Test memo containing prohibited speculatory language and verify it is rejected and routed back to the CIO Agent.
* Test memo that lacks a risks section and verify it is caught deterministically.
* Mock an infinite rewrite loop and verify execution terminates after exactly 2 revisions.

---

### Phase 10 — CLI Demo Entrypoint
Implement the command line interface in `src/portfolio_tracker/cli.py`.

* [ ] Set up commands using `click` or `argparse`.
* [ ] Support a mock execution flag (`--mock` or `--fixture`) to run the workflow offline using local JSON fixtures, allowing reviewers to test without live API credentials.
* [ ] Support formats: standard markdown memo and raw JSON output.
* [ ] Route warnings and data gaps clearly to `stderr` or as a front-matter alert block in markdown.

**TDD Tests:**
* Test that running the CLI with an invalid ticker code returns a non-zero exit code.
* Test running with `--mock` yields a complete markdown memo and prints data source warning flags.

---

### Phase 11 — Evaluation Set
Create tests in `evals/`.

* [ ] Define evaluation cases in `evals/eval_cases.yaml` (including a Mega-cap, a High-risk macro target, and a company with sparse/missing filings).
* [ ] Implement a rubric in `evals/rubric.md` evaluating the final memo against:
  * Proper schema parsing.
  * Inclusion of all four data vectors (or explicit disclosure of gaps).
  * Presence of risk highlights and investment disclaimer.
* [ ] Write a script `evals/run_evals.py` that executes the mock workflow against the test cases and writes a summary report.

---

### Phase 12 — Documentation
* [ ] Update `README.md` with:
  * System overview, architecture diagram, and prerequisites.
  * Local run commands for live mode and offline mock mode.
  * Testing instructions using pytest.
* [ ] Add `docs/architecture.md` detailing the DAG flow, the failsafe node wrappers, and the critic loop.
* [ ] Add `docs/limitations.md` detailing yfinance data accuracy, SEC filing boundaries, and LLM hallucination containment strategies.

---

## 7. Definition of Done

* [ ] **No network operations during unit testing:** verified by socket patching in the test runner.
* [ ] **No workflow hangs on API failures:** parallel branches are protected by failsafe node wrappers.
* [ ] **No masked retries:** transient exceptions propagate to the framework, while permanent/known states are converted to structured outputs at the node level.
* [ ] **Compliance with state guidance:** large payloads are passed as node outputs/artifacts, while `ToolContext.state` contains only lightweight metadata.
* [ ] **Deterministic Guardrails:** speculatory words and missing sections are checked using code rules before calling the LLM Critic.
* [ ] **Mock execution mode:** CLI demo is runnable completely offline using local fixtures.
* [ ] **Schema Integrity:** Pydantic schemas enforce type-safety and contract boundaries at every transition point.

---

## 8. Recommended Implementation Order

1. **Phase 0 & 1:** Core tooling, mock fixtures, and schema definitions.
2. **Phase 2, 3, 4, 5:** Vector adapters & deterministic calculation modules (yfinance, Edgar, transcripts, news).
3. **Phase 6 & 7:** Prompts, failsafe node wrappers, JoinNode, and AggregatorNode.
4. **Phase 8 & 9:** CIO synthesis and the deterministic + LLM Critic loop.
5. **Phase 10, 11, 12:** CLI entrypoint, Evaluation suite, and final documentation.

---

## 9. Next Immediate Step

Create `tests/unit/test_schemas.py` and fail validations for:
* Invalid stock ticker symbols (e.g. too long, special characters).
* Invalid `PerformanceAnalysis` inputs (e.g. CAGR > 1000% or Max Drawdown > 0%).
* SynthesizerInput compilation validation.
