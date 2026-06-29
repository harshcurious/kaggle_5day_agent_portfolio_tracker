# Codebase Structure

This document details the architecture of the **Market Signal Synthesizer** codebase. It outlines the file/folder layout, the logical runtime dataflow (based on the Google ADK 2.0 Workflow), and the domain schemas.

---

## 1. Directory & Module Layout

The workspace is organized into code sources (`src/portfolio_tracker`), test suites (`tests`), design specification plans (`plan`), and metadata files. Planned or suggested components are noted accordingly.

```mermaid
graph TD
    Root["kaggle_5day_agent_portfolio_tracker/"]
    Root --> Src["src/"]
    Root --> Tests["tests/"]
    Root --> Plan["plan/"]
    Root --> PyProject["pyproject.toml"]

    Src --> PT["portfolio_tracker/"]
    PT --> PT_Init["__init__.py"]
    PT --> Schemas["schemas.py (Domain models)"]
    PT --> AgentsDir["agents/"]
    PT --> ToolsDir["tools/"]

    AgentsDir --> AgentsInit["__init__.py"]
    AgentsDir --> PerfAgent["performance.py (Planned)"]
    AgentsDir --> FundAgent["fundamentals.py (Planned)"]
    AgentsDir --> SentAgent["sentiment.py (Planned)"]
    AgentsDir --> MacroAgent["macro.py (Planned)"]
    AgentsDir --> CIOAgent["cio.py (Planned)"]
    AgentsDir --> CriticAgent["critic.py (Planned)"]

    ToolsDir --> ToolsInit["__init__.py"]
    ToolsDir --> YF_Tools["yfinance_tools.py (Planned)"]
    ToolsDir --> Edgar_Tools["edgar_tools.py (Planned)"]
    ToolsDir --> Trans_Tools["transcript_tools.py (Planned)"]
    ToolsDir --> News_Tools["news_tools.py (Planned)"]

    Tests --> UnitTests["unit/"]
    Tests --> IntegrationTests["integration/ (Planned)"]
    Tests --> Fixtures["fixtures/"]
    Tests --> Conftest["conftest.py (Offline execution mock)"]

    UnitTests --> TTestSchemas["test_schemas.py"]
    UnitTests --> TTestNetGuard["test_network_guard.py"]
    UnitTests --> TTestPkg["test_package_import.py"]

    Fixtures --> F1["macro_news_sample.json"]
    Fixtures --> F2["price_history_sample.json"]
    Fixtures --> F3["sec_filing_summary_sample.json"]
    Fixtures --> F4["transcript_qa_sample.txt"]

    Plan --> PlanIdea["idea_gemini.md"]
    Plan --> PlanTDD["implementation_plan_tdd_revised.md"]
    
    style Root fill:#1d2021,stroke:#3c3836,stroke-width:2px,color:#ebdbb2
    style Src fill:#458588,stroke:#458588,color:#fbf1c7
    style Tests fill:#cc241d,stroke:#cc241d,color:#fbf1c7
    style Plan fill:#98971a,stroke:#98971a,color:#fbf1c7
```

---

## 2. Execution Flow Directed Acyclic Graph (DAG)

The logical execution flow runs concurrently during data collection (Fan-Out) and aggregates the outputs (Fan-In) to feed the LLM analysis and verification loops.

```mermaid
graph TD
    %% Define Nodes
    StartNode(["START"])
    ValidateRequest["Validate Request Node"]
    
    %% Concurrently execute vectors
    subgraph ParallelDataGathering ["Parallel Analysis Vectors (Fan-Out)"]
        PerfNode["Performance Node <br> (yfinance_tools)"]
        FundNode["Fundamental Node <br> (edgar_tools)"]
        SentNode["Sentiment Node <br> (transcript_tools)"]
        MacroNode["Macro Node <br> (news_tools)"]
    end
    
    JoinNode["Join Node <br> (ADK 2.0 Wait-All)"]
    AggregatorNode["Aggregator Node <br> (Deterministic Code)"]
    CIONode["CIO Synthesis Node <br> (LLM Agent: gemini-1.5-pro)"]
    CriticNode["Critic Node <br> (LLM Agent + Validation)"]
    
    %% Branching Decisions
    Decision{"Critic Passed?"}
    EndNode(["END"])
    
    %% Edges
    StartNode --> ValidateRequest
    ValidateRequest -->|Fan-Out| PerfNode
    ValidateRequest -->|Fan-Out| FundNode
    ValidateRequest -->|Fan-Out| SentNode
    ValidateRequest -->|Fan-Out| MacroNode
    
    PerfNode --> JoinNode
    FundNode --> JoinNode
    SentNode --> JoinNode
    MacroNode --> JoinNode
    
    JoinNode --> AggregatorNode
    AggregatorNode -->|"SynthesizerInput (Validated)"| CIONode
    CIONode -->|"Draft InvestmentMemo"| CriticNode
    CriticNode --> Decision
    
    Decision -->|Yes| EndNode
    Decision -->|"No: Feedback Event <br> (Max 2 iterations)"| CIONode

    %% Styling
    style StartNode fill:#353b48,stroke:#2f3542,color:#ffffff
    style EndNode fill:#353b48,stroke:#2f3542,color:#ffffff
    style ParallelDataGathering fill:#f1f2f6,stroke:#ced6e0,color:#2f3542
    style Decision fill:#e1b12c,stroke:#c49000,color:#ffffff
```

---

## 3. Domain Schema Relationships

The Pydantic schemas in [schemas.py](file:///home/hk/Documents/code/kaggle_agent/kaggle_5day_agent_portfolio_tracker/src/portfolio_tracker/schemas.py) define the core data contracts between the data gathering tools, the aggregator, the synthesizer, and the critic.

```mermaid
classDiagram
    class DataSourceStatus {
        <<enumeration>>
        SUCCESS
        PARTIAL
        FAILED
        SKIPPED
    }
    
    class TickerRequest {
        +ticker: str
        +validate_ticker()
    }
    
    class BaseVectorAnalysis {
        +ticker: str
        +status: DataSourceStatus
        +warnings: list~str~
        +error_message: str | None
        +validate_ticker()
        +sanitize_error_message()
        +sanitize_warnings()
    }

    class PerformanceAnalysis {
        +period_years: int
        +cagr_10yr: float | None
        +max_drawdown: float | None
        +dividend_consistency: str | None
        +validate_cagr()
        +validate_max_drawdown()
    }

    class FundamentalAnalysis {
        +filing_years: list~int~
        +revenue_trajectory: str | None
        +debt_profile: str | None
        +fundamental_red_flags: list~str~
    }

    class SentimentAnalysis {
        +quarter: str | None
        +year: int | None
        +management_confidence: str
        +capital_allocation_plans: list~str~
        +analyst_concerns: list~str~
        +validate_management_confidence()
    }

    class MacroAnalysis {
        +regulatory_environment: str | None
        +macro_headwinds: list~str~
        +competitive_shifts: list~str~
        +source_urls: list~str~
    }

    class SynthesizerInput {
        +ticker: str
        +performance: PerformanceAnalysis
        +fundamentals: FundamentalAnalysis
        +sentiment: SentimentAnalysis
        +macro: MacroAnalysis
        +validate_ticker()
        +validate_matching_tickers()
    }

    class InvestmentMemo {
        +ticker: str
        +recommendation_summary: str
        +long_term_thesis: str
        +supporting_evidence: dict
        +key_risks: list~str~
        +data_gaps: list~str~
        +not_investment_advice_disclaimer: str
        +revision_count: int
        +validate_ticker()
        +validate_required_text()
    }

    class CriticResult {
        +passed: bool
        +feedback: list~str~
        +failed_checks: list~str~
        +grounding_score: float
    }

    BaseVectorAnalysis <|-- PerformanceAnalysis
    BaseVectorAnalysis <|-- FundamentalAnalysis
    BaseVectorAnalysis <|-- SentimentAnalysis
    BaseVectorAnalysis <|-- MacroAnalysis

    SynthesizerInput *-- PerformanceAnalysis
    SynthesizerInput *-- FundamentalAnalysis
    SynthesizerInput *-- SentimentAnalysis
    SynthesizerInput *-- MacroAnalysis
```
