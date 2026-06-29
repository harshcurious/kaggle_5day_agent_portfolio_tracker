# Phase 7 — Workflow Orchestration

## Completed plan steps

- Defined the workflow assembly interface in `src/portfolio_tracker/workflow.py`.
- Added failsafe vector node wrappers for Performance, Fundamental, Sentiment, and Macro branches.
- Added a `JoinNode` collector marker and execution edge metadata for the fan-out/join graph.
- Added a deterministic `aggregate_outputs` node that builds `SynthesizerInput` from joined vector events.

## High-level code changes

- Added lightweight local workflow primitives: `Event`, `JoinNode`, `Workflow`, and `NodeInterruptedError`.
- Added `build_workflow(...)` to assemble the Phase 7 fan-out and join stage.
- Added `failsafe_vector_node(...)` to convert terminal provider failures into schema-valid failed vector outputs while re-raising cancellations and framework interruptions.
- Added `aggregate_outputs(...)` to validate four vector payloads into a single `SynthesizerInput` event.

## Additional implementation decisions

- Kept Phase 7 independent of a live ADK dependency so unit tests remain offline and deterministic.
- Modeled the ADK concepts locally with the same event-oriented boundaries needed by later phases.
- Preserved framework control-flow semantics by re-raising `asyncio.CancelledError` and interruption-class exceptions.

## Tests created

- `tests/unit/test_workflow.py`
  - Verifies aggregation of four distinct vector payloads into `SynthesizerInput`.
  - Verifies one failed vector branch does not hang or block workflow completion.
  - Verifies cancellations and framework interruptions are not swallowed by failsafe wrappers.

## Commit message

`feat: add workflow fan-out and join aggregation`
