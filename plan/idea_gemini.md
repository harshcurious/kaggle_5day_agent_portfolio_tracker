# Market Signal Synthesizer: Agentic Workflow Architecture for Long-Term Portfolio Analysis

## 1. Architectural Overview and Engineering Context

The transition from deterministic software engineering to agentic workflows represents a fundamental shift in application design. For software engineers (SWEs), this requires adopting natural language as a primary programming interface.

This document serves as the technical blueprint for the "Market Signal Synthesizer," a multi-agent system designed to evaluate long-term investment portfolios.

This project is architected specifically as a capstone submission for the Kaggle "5-Day AI Agents: Intensive Vibe Coding Course With Google".

The system architecture utilizes Google's Agent Development Kit (ADK 2.0), moving away from monolithic LLM prompts toward a distributed, graph-based execution model.

By defining strict system boundaries, the application focuses exclusively on four vectors critical to long-term investing:

- Historical long-term performance metrics.

- Audited financial statements and SEC filings.

- Quarterly earnings call transcripts.

- Major market news and macroeconomic headlines.

### 1.1 The Agentic Development Paradigm (Vibe Coding)

"Vibe coding" shifts the developer's role from writing syntax to orchestrating intent.

In this paradigm, the AI handles the boilerplate, while the engineer focuses on system design, state management, and failover states.

Key tools in this ecosystem include:

- **Google Antigravity IDE:** Acts as "Mission Control" for orchestrating autonomous agents across the editor and terminal.

- **Agents CLI (`agents-cli`):** The programmatic backbone for scaffolding, testing, and deploying ADK agents to Google Cloud.

- **Gemini Models:** The reasoning engines, specifically utilizing `gemini-2.5-flash` for rapid sub-agent tasks and `gemini-1.5-pro` for complex synthesis.

## 2. System Architecture: The Directed Acyclic Graph (DAG)

ADK 2.0 introduces a graph-based execution engine (`Workflow`) that fundamentally changes how agents are orchestrated.

Previous iterations relied on linear constructs like `SequentialAgent` or `LoopAgent`. ADK 2.0 deprecates these in favor of a deterministic Directed Acyclic Graph (DAG).

For the Market Signal Synthesizer, a fan-out/fan-in graph pattern is required. This allows multiple agents to query data silos concurrently before aggregating the results.

### 2.1 Core Components of the ADK 2.0 Graph

Engineers must define three primary components to build this workflow:

- **Nodes:** Python functions decorated with `@node`. These execute business logic, trigger tools, or invoke sub-agents.

- **Edges:** An array defining the execution flow, chaining nodes from `START` to completion. Conditional routing determines the path based on node outputs.

- **State (`ToolContext.state`):** A shared dictionary that all sub-agents read from and write to. This replaces the anti-pattern of passing massive string payloads between functions.

### 2.2 System Execution Flow Diagram

I apologize for the formatting issues in the previous diagram. Let's break down the execution flow of the Market Signal Synthesizer using clearer structural logic.

In Google's Agent Development Kit (ADK 2.0), applications are orchestrated as a Directed Acyclic Graph (DAG) using the `Workflow` class and an `edges` array to define the exact routing between nodes.

Here is a clearer, step-by-step breakdown of how the data moves through the graph:

- **1. Initialization (`START` Node):** The `Workflow` begins execution and triggers the initial data retrieval phase.

- **2. The Fan-Out (Parallel Execution):** To minimize latency, the graph routes the request to run concurrently. Four independent sub-agents query their respective APIs simultaneously:
  
  - Performance Agent (`yfinance`)
  
  - Fundamental Agent (`edgartools`)
  
  - Sentiment Agent (`EarningsCall API`)
  
  - Macro Agent (Google Search)

- **3. State Aggregation:** Instead of passing massive strings between functions, the parallel agents write their structured JSON outputs directly to a shared dictionary called `ToolContext.state`.

- **4. The Fan-In (Synthesis):** Once the parallel tasks complete, the graph routes execution to the CIO Agent. This agent reads the aggregated data from the shared state and drafts the initial investment memo.

- **5. The Guardrail Loop (Conditional Routing):** The draft is passed to the Critic Agent. This creates a conditional edge (a branching path) in the workflow :
  
  - *Path A (Pass):* If the memo meets all long-term investing criteria, it routes to the `END` node.
  
  - *Path B (Fail):* If the memo is flawed (e.g., hallucinated data or short-term focus), the Critic generates a feedback event, and the graph routes execution back to the CIO Agent for a rewrite, creating an iterative refinement loop.

### Updated Execution Flow Diagram

step-by-step breakdown of how the data moves through the graph:

- **1. Initialization (`START` Node):** The `Workflow` begins execution and triggers the initial data retrieval phase.

- **2. The Fan-Out (Parallel Execution):** To minimize latency, the graph routes the request to run concurrently. Four independent sub-agents query their respective APIs simultaneously:
  
  - Performance Agent (`yfinance`)
  
  - Fundamental Agent (`edgartools`)
  
  - Sentiment Agent (`EarningsCall API`)
  
  - Macro Agent (Google Search)

- **3. State Aggregation:** Instead of passing massive strings between functions, the parallel agents write their structured JSON outputs directly to a shared dictionary called `ToolContext.state`.

- **4. The Fan-In (Synthesis):** Once the parallel tasks complete, the graph routes execution to the CIO Agent. This agent reads the aggregated data from the shared state and drafts the initial investment memo.

- **5. The Guardrail Loop (Conditional Routing):** The draft is passed to the Critic Agent. This creates a conditional edge (a branching path) in the workflow :
  
  - *Path A (Pass):* If the memo meets all long-term investing criteria, it routes to the `END` node.
  
  - *Path B (Fail):* If the memo is flawed (e.g., hallucinated data or short-term focus), the Critic generates a feedback event, and the graph routes execution back to the CIO Agent for a rewrite, creating an iterative refinement loop.

```
│

▼

├──> Performance Agent (yfinance API)

├──> Fundamental Agent (SEC EDGAR API)

├──> Sentiment Agent (EarningsCall API)

└──> Macro Agent (Google Search Grounding)

│

▼

---> (Data saved to ToolContext.state)

│

▼

[CIO Agent] <─────────────────────────────────────┐

│ (Drafts Investment Memo) │

▼ │

[Critic Agent] │

│ (Evaluates Memo against guardrails) │

│ │

├──> ──> (Feedback Generated) ─────────┘

│ ^ Iterative Loop ^

▼

│

▼
```



```

```

### 2.3 Parallel Execution Strategy

While ADK offers a `ParallelAgent` class , modern ADK 2.0 implementations often achieve better concurrency control using standard Python asynchronous programming.

- Within a single execution node, SWEs can utilize `asyncio.gather`.

- This allows the root workflow to dispatch API calls to the Performance, Fundamental, and Sentiment agents simultaneously.

- This approach significantly reduces total inference and data retrieval time.

- It provides finer control over exception handling if one specific API (e.g., the SEC EDGAR database) experiences a timeout.

## 3. Data Vector 1: Long-Term Past Performance

The first constraint of the Market Signal Synthesizer is evaluating long-term historical performance. Short-term volatility and daily price action are explicitly ignored.

To achieve this, the system integrates the `yfinance` Python library.

### 3.1 Tool Selection: Why `yfinance`?

For SWEs, selecting the right dependency is critical for minimizing technical debt. `yfinance` is optimal for several reasons:

- **Open Source:** It is completely free and distributed under the Apache Software License.

- **No Authentication:** It bypasses the need for API keys, simplifying local development and deployment.

- **Pythonic Design:** It returns structured Pandas DataFrames, making it immediately compatible with ADK tool wrappers.

### 3.2 Performance Agent Design

The Performance Agent is an `LlmAgent` node in the ADK graph responsible for historical quantitative analysis.

- **Model:** `gemini-2.5-flash`.

- **Instruction:** "Act as a quantitative analyst. Analyze the 10-year historical performance of the provided ticker. Calculate compound annual growth rate (CAGR) and summarize dividend consistency. Ignore short-term price fluctuations."

- **Tool Binding:** `yfinance_history_tool`, `yfinance_dividend_tool`.

### 3.3 Tool Implementation Details

The underlying tools are standard Python functions wrapped with the ADK `@tool` decorator.

- **Historical Data:** The agent invokes `Ticker("TICKER").history(period='10y')`. This returns a decade of open, high, low, close, and volume data.

- **Corporate Actions:** The agent invokes `Ticker("TICKER").actions` to retrieve a historical log of dividends and stock splits.

- **Data Aggregation:** The Python tool does not return the raw DataFrame to the LLM. Doing so would exhaust the context window.

- Instead, the Python tool calculates the CAGR and max drawdowns mathematically, returning only the summary statistics to the agent's context.

### 3.4 Output Schema

To ensure deterministic behavior, the Performance Agent is bound to a strict Pydantic output schema.

| **Field Name**         | **Data Type** | **Description**                                 |
| ---------------------- | ------------- | ----------------------------------------------- |
| `cagr_10yr`            | Float         | Compound Annual Growth Rate over 10 years.      |
| `dividend_consistency` | String        | Qualitative summary of dividend growth or cuts. |
| `max_drawdown`         | Float         | The largest historical peak-to-trough drop.     |

## 4. Data Vector 2: Audited Financial Reports

The second vector requires deep fundamental analysis of SEC filings. LLMs cannot hallucinate financial health; they must be grounded in audited 10-K and 10-Q reports.

### 4.1 Tool Selection: `edgartools` vs. SEC REST API

Engineers have two primary paths for SEC data: the raw `data.sec.gov` REST API or the `edgartools` Python library. This architecture strongly prefers `edgartools`.

- **Data Format:** The SEC REST API returns raw JSON and requires complex XBRL (eXtensible Business Reporting Language) parsing. `edgartools` natively parses over 20 form types into typed Python objects and DataFrames.

- **Rate Limiting and Headers:** The SEC API requires strict User-Agent headers and enforces rate limits. `edgartools` handles connection pooling and headers internally.

- **AI Integration:** `edgartools` is explicitly designed with AI-native outputs and Model Context Protocol (MCP) compatibility in mind.

### 4.2 Fundamental Agent Design

The Fundamental Agent extracts critical health metrics from the balance sheet, income statement, and cash flow statement.

- **Model:** `gemini-2.5-flash`.

- **Instruction:** "Act as a fundamental credit analyst. Review the last three annual 10-K reports. Identify the trajectory of free cash flow, debt-to-equity ratios, and highlight any accounting risk factors mentioned in the footnotes."

- **Tool Binding:** `edgar_10k_extractor`.

### 4.3 Tool Implementation Details

The `edgartools` implementation requires specific querying strategies to minimize token consumption.

- **CIK Lookup:** The tool first converts the ticker symbol to a Central Index Key (CIK).

- **Form Filtering:** The tool queries the SEC index for `form_type="10-K"` and limits the return to the three most recent filings.

- **Targeted Extraction:** Rather than passing the entire 10-K (which spans hundreds of pages) to the agent, the Python tool utilizes `edgartools` to extract specific XBRL sections:
  
  - Item 7: Management's Discussion and Analysis (MD&A).
  
  - Item 8: Financial Statements and Supplementary Data.

### 4.4 Output Schema

The Fundamental Agent standardizes its findings into the following Pydantic model:

| **Field Name**          | **Data Type** | **Description**                             |
| ----------------------- | ------------- | ------------------------------------------- |
| `revenue_trajectory`    | String        | Summary of top-line growth over 3 years.    |
| `debt_profile`          | String        | Analysis of leverage and maturity risks.    |
| `fundamental_red_flags` | List          | Any anomalies found in the audited reports. |

## 5. Data Vector 3: Earnings Call Transcripts

Quantitative data reveals what happened; earnings calls reveal why it happened and what management expects next. This vector analyzes the forward-looking statements of corporate executives.

### 5.1 Tool Selection: EarningsCall API and FMP

Unlike SEC filings, earnings transcripts are not easily accessible via free government APIs. The architecture requires a commercial data provider.

- **Financial Modeling Prep (FMP):** Offers a REST API delivering structured JSON transcripts for over 8,200 companies.

- **EarningsCall API:** Provides a dedicated Python library (`earningscall`) and granular endpoints, including a `qa_only` parameter.

This architecture favors the EarningsCall API due to its ability to isolate the Q&A session.

### 5.2 The Value of Q&A Isolation

Earnings calls are divided into two sections:

1. **Prepared Remarks:** Highly scripted statements drafted by legal and PR teams.

2. **Analyst Q&A:** Unscripted responses to direct analyst scrutiny.

For long-term investing, the Q&A section contains significantly more signal and less noise. The `qa_only=true` parameter in the EarningsCall API reduces context window bloat and improves LLM focus.

### 5.3 Sentiment Agent Design

The Sentiment Agent applies natural language processing (NLP) to the extracted transcripts.

- **Model:** `gemini-2.5-flash`.

- **Instruction:** "Analyze the provided Q&A transcript from the most recent earnings call. Identify management's tone regarding macroeconomic headwinds. Extract any discussion regarding long-term capital allocation, share buybacks, or R&D investment."

- **Tool Binding:** `transcript_qa_fetcher`.

### 5.4 Tool Implementation Details

The Python implementation utilizes the `earningscall` library.

- **Initialization:** `company = get_company("TICKER")`.

- **Retrieval:** The tool fetches the latest quarter's transcript: `transcript = company.get_transcript(year=YYYY, quarter=Q)`.

- **NLP Constraints:** Standard NLP techniques often rely on rigid dictionaries (e.g., counting positive vs. negative words). By utilizing a Gemini agent, the system achieves semantic understanding, recognizing when an executive is deflecting a question rather than answering it directly.

### 5.5 Output Schema

The Sentiment Agent standardizes the unstructured text into:

| **Field Name**             | **Data Type**             | **Description**                                 |
| -------------------------- | ------------------------- | ----------------------------------------------- |
| `management_confidence`    | Enum [High, Neutral, Low] | Overall assessment of management's tone.        |
| `capital_allocation_plans` | List                      | Identified long-term investments or buybacks.   |
| `analyst_concerns`         | List                      | The primary friction points raised by analysts. |

## 6. Data Vector 4: Major News and Macroeconomic Headlines

A company does not operate in a vacuum. The final data vector contextualizes the asset within the broader economic and regulatory environment.

### 6.1 Tool Selection: Google Search Grounding

To prevent hallucinations regarding recent events, the agent requires access to the live internet.

- The ADK supports native `google_search` tools.

- This tool leverages Gemini's built-in Search Grounding capabilities, providing factual, cited access to recent news.

### 6.2 Macro News Agent Design

This agent must filter out daily stock price movement articles ("noise") and focus on structural shifts ("signal").

- **Model:** `gemini-2.5-flash`.

- **Instruction:** "Search for major news headlines concerning the provided company over the past 12 months. Explicitly ignore articles discussing daily stock price movements or short-term earnings beats. Focus exclusively on macro-sector disruptions, regulatory actions, and major mergers or acquisitions."

- **Tool Binding:** `google_search`.

### 6.3 Execution and Output Schema

The agent executes multiple targeted search queries (e.g., "Company X regulatory fines", "Company X supply chain disruptions") and synthesizes the findings.

| **Field Name**           | **Data Type** | **Description**                                |
| ------------------------ | ------------- | ---------------------------------------------- |
| `regulatory_environment` | String        | Summary of any antitrust or compliance issues. |
| `macro_headwinds`        | List          | Broad economic challenges facing the sector.   |
| `competitive_shifts`     | List          | Major moves by primary competitors.            |

## 7. Workflow Synthesis and Quality Control

Once the four parallel agents complete their tasks, the DAG routes their standardized JSON outputs to the `ToolContext.state`. The system now shifts from data aggregation to synthesis.

### 7.1 The Chief Investment Officer (CIO) Agent

The CIO Agent acts as the central intelligence node. Because this task requires complex reasoning, nuance, and the synthesis of disparate data types, the architecture dictates a model upgrade.

- **Model:** `gemini-1.5-pro` (or the highest reasoning tier available).

- **Input Context:** The combined JSON outputs from the Performance, Fundamental, Sentiment, and Macro agents.

- **Instruction:** "Act as a conservative, long-term portfolio manager. Synthesize the historical performance, fundamental health, management sentiment, and macro environment data. Produce a comprehensive, risk-adjusted long-term investment recommendation. Ensure the recommendation relies purely on the provided data and explicitly avoids short-term trading advice."

### 7.2 The Critic Agent (Quality Loop)

A fundamental principle of robust agentic systems is that "hope is not a valid error-handling strategy". Linear chains fail when intermediate outputs degrade.

To counter this, the workflow implements a self-correcting loop using a Critic Agent.

- **Function:** The Critic Agent acts as a deterministic guardrail.

- **Execution:** It evaluates the CIO Agent's generated `InvestmentMemo`.

- **Evaluation Criteria:**
  
  1. Does the memo explicitly address long-term risks?
  
  2. Does it refrain from guaranteeing future returns?
  
  3. Is it properly grounded in the four specific data vectors?

- **Routing Logic:**
  
  - If the memo passes, the Critic node yields an event signaling the workflow to proceed to the `END` node.
  
  - If the memo fails, the Critic node generates a `feedback_string` (e.g., "The memo lacks analysis of the regulatory risks identified by the Macro Agent") and routes execution back to the CIO Agent for revision.

This heat-seeking, iterative loop ensures that hallucinations or policy violations are caught before the output reaches the end-user.

## 8. Scaling via Microservices: The Agent2Agent (A2A) Protocol

As the codebase grows, housing all specialized agents within a single monolithic application becomes an architectural bottleneck.

Google's Agent2Agent (A2A) protocol solves this by enabling distributed communication between agents running on separate servers.

### 8.1 A2A Architectural Principles

A2A acts as a universal translator for AI agent ecosystems.

- **Standardized Communication:** It utilizes JSON-RPC 2.0 over HTTP(S).

- **Opacity and Security:** Agents collaborate without exposing their internal memory, proprietary logic, or specific API keys.

- **Framework Agnosticism:** While this system is built on ADK, A2A allows a future team to rewrite the Fundamental Agent in LangGraph or CrewAI without breaking the overarching system.

### 8.2 Implementing A2A with ADK

ADK 2.0 provides native support for exposing agents as A2A microservices.

- **Agent Cards:** The foundation of A2A is discovery. An agent advertises its capabilities via an "Agent Card" formatted as a JSON file. This card details connection info, input/output modes, and skills.

- **The `to_a2a()` Function:** SWEs can convert a local ADK agent into an A2A server with a single line of code.

- **Implementation Example:**
  
  Python
  
  ```
  from google.adk.a2a.utils.agent_to_a2a import to_a2a
  
  # Expose the Fundamental Agent on port 8001
  a2a_app = to_a2a(fundamental_agent, port=8001)
  ```

- Under the hood, `to_a2a` wraps the agent in an asynchronous Starlette application, handles the Agent Card handshake, and manages JSON-RPC network requests.

### 8.3 The Client/Server Relationship

In a distributed setup, the central DAG acts as the **A2A Client**, while the specialized data vector agents act as **A2A Servers** (Remote Agents).

- **Tasks:** The Client sends a `Message` to the Server containing metadata (e.g., session ID). The Server perceives this as a `Task`.

- **Artifacts:** Upon task completion, the Server sends the resulting JSON output (the `Artifact`) back to the Client.

- **Asynchronous Updates:** For long-running tasks (e.g., a massive SEC XBRL parse), A2A supports push notifications sent to a secure client-supplied webhook, preventing HTTP timeouts.

## 9. Vibe Coding Lifecycle and Deployment

The development and deployment of the Market Signal Synthesizer rely heavily on the unified `agents-cli` toolchain.

This CLI bridges the gap between local prototyping and enterprise-grade cloud deployment.

### 9.1 Phase 1: Bootstrapping and Scaffolding

Instead of manually writing boilerplate, SWEs utilize their preferred coding agent (Gemini CLI, Claude Code, or Codex) infused with ADK skills.

- **Installation:** `uv tool install google-agents-cli`.

- **Setup:** `uvx google-agents-cli setup` installs the necessary skills.

- **Scaffolding:** The SWE prompts the IDE: "Use agents-cli to build an agent that analyzes long-term market signals.".

- **Execution:** The AI activates the `google-agents-cli-scaffold` skill, queries the user for deployment targets, writes a `DESIGN_SPEC.md`, and generates the underlying Python graph structure.

### 9.2 Phase 2: Shift-Left Security and TDD

Security must be integrated at the inception of the code, rather than as a late-stage gate.

- **Context Standards:** A persistent `CONTEXT.md` file enforces secure coding standards across the workspace.

- **Threat Modeling:** Antigravity IDE utilizes automated STRIDE threat modeling to identify Spoofing, Tampering, and Information Disclosure risks during the planning phase.

- **Pre-commit Hooks:** Git hooks automate Semgrep scans, creating local remediation loops within the IDE before code is ever pushed.

### 9.3 Phase 3: Interactive Debugging and Evaluation

ADK provides extensive tools for local testing before incurring cloud costs.

- **Web UI:** Running `adk web` launches a local built-in developer UI.

- **Capabilities:** This UI allows SWEs to visualize the DAG execution flow, inspect tool inputs/outputs, and trace events in real-time.

- **Automated Linting:** The SWE prompts the IDE: "Run linting on my agent project." This executes `agents-cli lint` to verify imports and formatting.

- **Evaluation:** The `agents-cli eval` command runs batch tests against a predefined "evalset". This tests the agent's trajectories against a scoring rubric, verifying that it calls the correct tools and produces the correct schema.

### 9.4 Phase 4: Production Deployment via IaC

Going from local prototype to a globally distributed service is automated via Infrastructure as Code (IaC) embedded within the CLI.

- **API Enablement:** The system requires `aiplatform` (for Gemini models), `run` (for hosting), and `cloudtrace` (for observability).

- **Infrastructure Provisioning:** The command `agents-cli infra single-project` injects IaC and provisions the Google Cloud environment.

- **Deployment:** The command `agents-cli deploy` containerizes the ADK application and deploys it directly to Cloud Run.

- **Cloud Run Advantages:** Deploying to Cloud Run leverages Google's serverless infrastructure, providing massive scale, automatic load balancing, and high reliability for the agentic endpoints.

- **Enterprise Distribution:** Finally, the `agents-cli publish gemini-enterprise` command registers the deployed agent, making it available for broader organizational use with full governance and access controls.

By strictly adhering to this blueprint—leveraging the ADK 2.0 DAG, rigorous tool isolation, iterative critic loops, and the `agents-cli` deployment pipeline—SWEs can rapidly build a production-ready, highly observable Market Signal Synthesizer that fulfills all capstone requirements.
