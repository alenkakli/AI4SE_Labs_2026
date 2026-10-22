# Agentic Network Design for Requirements Refinement

## Preface

As requested in the assignment task, I used my coding agent to help me to create the requirements refinement network. I used the Train of Thought prompting framework to explore the possible designs, because I found it worked best in the previous lab session when the right path was not obvious. This helped me compare possible approaches and settle on a network design. I also asked the agent to ask for my opinion when making any important choices so that I could correct any wrong assumptions he had. 

Once the design was clear, I used another agent to implement the network and write tests according to that design. I didnt want to run the implementation blindly and needed to make sure the code was tested beforehand. I then used a third agent to run the implementation and tests, identify issues in either the design or the implementation, and correct them. This separation helped me move from exploring the problem, to building the solution, to checking and improving the result.

## Goal

The agentic network takes a directory of mixed requirements evidence (long draft specifications, interviews, survey results, meeting notes, ... ) and produces one structured requirements document. It must preserve evidence provenance, avoid duplicate requirements, identify conflicts and unsupported statements, and check that all input documents were considered.

## Three architecture choices

| Choice | Outline | Advantages | Main weaknesses |
|---|---|---|---|
| **1. Sequential specialist pipeline** | Process each source chunk through a coverage-focused extractor, a reconciliation step, and an independent reviewer. A bounded feedback loop sends actionable findings back for correction. | Clear hand-offs make it easier to debug and preserve provenance; each step has a distinct responsibility; it can meet the assignment requirements without parallel coordination. | Processing chunks sequentially can make a large corpus slow, and a missed requirement in an early stage can affect later stages unless coverage is tracked explicitly. |
| **2. Parallel evidence extraction with reconciliation** | Two or more extractors independently process the corpus or its chunks. A corpus-level model reconciles their candidates, and deterministic checks validate schema, IDs, and evidence before review. | Independent passes can improve coverage; chunks can be processed concurrently; deterministic validation makes traceability and output structure more reliable. | Parallel results can disagree or repeat one another. Reconciliation and an independent review loop are still needed, and concurrency can increase rate-limit pressure and cost. |
| **3. Hierarchical extraction with targeted review feedback** | Discover and chunk the sources, extract in parallel, reconcile candidates across the corpus, then have an independent reviewer check completeness, conflicts, and output quality. Findings route back to affected sources for bounded correction. | Combines manageable context sizes with independent coverage, corpus-wide consistency, deterministic provenance checks, and an explicit feedback loop. It fits a heterogeneous corpus while keeping failures and remaining gaps visible. | More model calls increase latency, API usage, and operational complexity. The feedback loop needs strict limits and clear stopping/failure behavior. |

### Choice

I chose Choice 3, using parallel evidence extraction from Choice 2, because the corpus contains many different kinds of documents and is too large to treat as one prompt. Chunking keeps each model call manageable, while reconciliation and an independent reviewer help catch duplicates, contradictions, and omissions across the whole corpus. Deterministic provenance checks make it possible to report invalid citations instead of silently accepting them. Choice 1 would also be a reasonable design for a smaller corpus or a system where easier debugging matters more than speed, but its sequential processing could make this particular run slower. The selected design's extra coverage and quality checks were worth the added runtime and API usage, provided those costs and the possibility of a partial result were made explicit.

## LangGraph network

Use a typed graph state carrying the input directory, discovered-file inventory, normalized source chunks, candidate requirements, review findings, discarded candidates, retry/iteration count, errors, and final document. A requirement candidate should retain its evidence references from extraction through final rendering.

```text
START
  |
  v
[Discover and read files] -- deterministic
  |
  v
[Normalize and chunk with source metadata] -- deterministic
  |
  +------------------------ parallel -------------------------+
  |                                                            |
  v                                                            v
[Coverage-focused extraction]                         [Independent extraction]
 gpt-5-mini                                               gpt-4o-mini
  |                                                            |
  +---------------------------+--------------------------------+
                              v
             [Normalize, cluster, and reconcile candidates]
                            gpt-5.6-luna
                              |
                              v
               [Validate schema and provenance] -- deterministic
                              |
                              v
             [Completeness and consistency review]
                         gpt-5.4-nano
                              |
                  findings / missing evidence?
                    /                       \
                  yes                         no
                   |                           |
                   v                           v
     [Targeted extraction/reconciliation]  [Render one document]
                   |                          |
                   +---- back to review       |
                         (bounded)            v
                                              END
```

All four named models are available in the assignment's model list. The separate model assignments are deliberate: two extractors can expose requirements one pass misses, while reconciliation and review have distinct responsibilities. The model names are configuration values, not hard-coded assumptions about which model will always perform best; a later evaluation may change the assignments.

### Node responsibilities

1. **Discover and read files (deterministic).** Accept a user-supplied directory, recursively enumerate supported text and email files, decode their contents, and record a stable relative path and file identifier. Do not embed the example corpus path in the network. Report unreadable supported files in the run result instead of silently omitting them.
2. **Normalize and chunk (deterministic).** Preserve document identity and useful structure such as email headers, message boundaries, headings, and lists. Keep a thread or section together where possible; otherwise use bounded, overlapping chunks. Every chunk carries its source identifier and location information so extracted claims can be traced back. Track which files and chunks have been processed.
3. **Coverage-focused extraction (`gpt-5-mini`).** Extract atomic candidate functional and non-functional requirements, constraints, dependencies, explicit priorities, and unresolved questions. Return structured data, not prose alone. Require evidence quotations or faithful short evidence spans and source identifiers for every candidate. Treat source text as evidence, not as instructions to the agent.
4. **Independent extraction (`gpt-4o-mini`).** Independently inspect the same chunk set for requirements and evidence, emphasizing implicit constraints, conditions, exceptions, and requirements expressed across email replies. Its independent perspective is a completeness aid, not a vote that automatically overrides the first extractor.
5. **Normalize, cluster, and reconcile (`gpt-5.6-luna`).** Compare candidate meanings across sources, merge semantic duplicates, and resolve consistent terminology. Retain all source references when merging. Distinguish a true contradiction from a scope difference, a changed proposal, or an unresolved stakeholder question. Do not silently discard conflicting evidence: preserve the alternatives for review and possible blacklist treatment.
6. **Validate schema and provenance (deterministic).** Check required fields, identifier uniqueness, valid priorities, and that every evidence citation matches a discovered chunk and source. Assign stable IDs after reconciliation (for example, `REQ-70D32F63A0`) so IDs do not change merely because parallel completion order changes. Invalid candidates are excluded with explicit provenance errors and make the run partial; the renderer never substitutes invented evidence.
7. **Completeness and consistency review (`gpt-5.4-nano`).** Review the candidate set against the per-file and per-chunk coverage ledger. Flag likely omissions, unsupported assertions, semantic duplicates, inconsistent terminology, contradictions, and incorrect or missing source links. Return structured findings with the affected candidate IDs and evidence, rather than silently rewriting the whole result.
8. **Feedback routing.** If the reviewer finds actionable omissions or reconciliation defects, route only the affected sources/candidates through targeted extraction or reconciliation, then review again. Cap this loop at two correction rounds. If findings remain, retain them as unresolved items in the final document/run status rather than looping indefinitely or claiming a clean result.
9. **Render (deterministic).** Emit one structured Markdown document with a consistent schema and sections. Rendering is deterministic so formatting, ordering, and IDs do not depend on LLM prose generation.

## Output contract

The single output document should include:

- **Scope and priority scale.** Define priorities before listing requirements. A practical scale is **High** (explicitly urgent/high priority or necessary for core operation), **Medium** (clearly requested but not marked urgent), and **Low** (optional, exploratory, or explicitly deferred). Explicit stakeholder priority evidence takes precedence. If importance is not supported by the corpus, use **Unassigned** and explain that it needs human triage; do not present an inference as a stakeholder decision.
- **Requirements.** For each item, provide a stable unique ID, short descriptive name, one paragraph describing the expected system behavior, priority, and source references. Keep each requirement atomic where practical and use consistent terms.
- **Traceability.** Cite one or more input-relative file paths and, where available, a message, heading, or chunk locator. A merged requirement keeps every source that supports it; disagreement should identify which sources disagree.
- **Blacklist / discarded candidates.** Record only candidates that were deliberately excluded because they are nonsensical, unsupported, or superseded/conflicting under an explicitly justified decision. Include the candidate/evidence reference and reason. Keep unresolved conflicts visible rather than choosing a side without evidence.
- **Review status and coverage.** Summarize processed files, unprocessed or unreadable files, unresolved conflicts, and remaining reviewer findings. This makes the completeness claim auditable instead of implying that an LLM can prove completeness.

## Checks against the assignment requirements

The graph and output contract map to each numbered requirement in the assignment as follows.

| Assignment requirement | Design element that addresses it |
|---|---|
| **ANS1 — At least 3 LLM-invoking nodes** | Four distinct LLM nodes are specified: two extractors, a reconciliation node, and a completeness/consistency reviewer. |
| **ANS2 — At least 1 deterministic node** | File discovery and reading, chunking, schema/provenance validation, stable ID assignment, and final rendering are deterministic nodes. |
| **ANS3 — At least 1 feedback loop** | Reviewer findings route to targeted extraction/reconciliation and back to review, with a two-round cap and explicit unresolved status if issues remain. |
| **ANS4 — At least 3 different LLM models** | The design assigns `gpt-5-mini`, `gpt-4o-mini`, `gpt-5.6-luna`, and `gpt-5.4-nano` to separate LLM responsibilities. |
| **ANS5 — Implemented in Python's LangGraph framework** | The network is implemented as a typed LangGraph state graph with parallel branches, conditional routing, and bounded cycles. |
| **OS1 — Single structured document** | The deterministic renderer emits one Markdown document with defined sections and a consistent requirement schema. |
| **OS2 — Unique requirement identification** | Deterministic validation assigns stable, unique IDs such as `REQ-70D32F63A0` after reconciliation and checks for collisions. |
| **OS3 — No semantic duplicates** | The reconciliation model clusters candidates by meaning; the reviewer flags duplicates missed during reconciliation. |
| **OS4 — Tracing to input documents** | Every candidate carries source identifiers and evidence locations; merged requirements retain all supporting references. |
| **OS5 — Short name and paragraph-long explanation** | The output schema requires a concise title and one explanatory paragraph per requirement. |
| **OS6 — Assigned priority and explained scale** | The output defines High, Medium, Low, and Unassigned, and requires priority evidence or explicit human triage where the source does not establish priority. |
| **OS7 — Consistency and contradictions** | Reconciliation normalizes terminology and reviews conflicts; unresolved disagreements remain visible with their source evidence instead of being silently decided. |
| **OS8 — Completeness** | The coverage ledger tracks every discovered file and chunk; two extractors inspect the material, and review findings trigger targeted correction. Unreadable files and remaining gaps are disclosed. |
| **OS9 — Blacklist** | The output has a discarded-candidates section recording excluded items, evidence, and the reason for exclusion; unresolved conflicts are not discarded without justification. |


## API key, timeout, and reliability considerations

Using an OpenAI API key creates operational and security concerns as well as network-failure risks:

- **Protect the key.** The script loads `OPENAI_API_KEY` from the repository-root `.env` using `python-dotenv` without overriding an already-set process environment variable. It never puts the key in source code, prompts, command-line output, or logs. `.env` remains ignored and untracked. Use a key with only the required access where the service permits it, rotate it if exposed, and handle missing/invalid credentials as explicit configuration errors.
- **Expect timeouts.** Calls can exceed a client or server timeout because of large inputs, model latency, queueing, or a temporary network problem. Set explicit connection and response timeouts per request. Chunking bounds request size, but does not eliminate timeouts. A timed-out call must not be mistaken for an empty successful extraction.
- **Retry selectively.** Retry transient connection failures, timeouts, and rate-limit/server errors with bounded exponential backoff and jitter, honoring a server-provided retry delay when present. Set a maximum attempt count and an overall run deadline. Do not repeatedly retry authentication, invalid request, or unavailable-model errors; report them clearly. Avoid duplicate side effects by making graph nodes idempotent and associating results with stable chunk IDs.
- **Handle quotas and rate limits.** Parallel model calls can trigger rate limits or exhaust project budget. Limit concurrency, use bounded batches, track usage and cost, and stop with a clear partial-run status when a quota or budget limit prevents completion. Do not silently drop work to meet a limit.
- **Make long runs recoverable.** Persist graph state/checkpoints (for example, with a local LangGraph checkpointer) so completed chunks need not be reprocessed after interruption. Record node failures and the affected sources. Resume only failed or incomplete work where possible. Final output must distinguish complete from partial runs.
- **Expose operational status.** Report elapsed time, attempts, failed node, affected chunks, and whether the review loop reached its cap. Never log the key or include it in exception text shown to users.

The implementation sets request timeouts, bounded client retries, a shared rate limiter, a bounded concurrency limit, and a two-round correction cap. It records failed files, chunks, and nodes in the rendered document and marks incomplete runs as partial. Graph state is currently in memory; restarting a stopped run starts from discovery rather than resuming a checkpoint. An overall run deadline, checkpointing, and cost tracking remain possible future operational enhancements.

## My takeaways

ToT was a good choice for this design task because the network had several requirements to balance, including coverage, traceability, consistency, runtime, and API usage. Working through the design helped me consider the tradeoffs between different architectures instead of picking the first idea.

In practice, the third run took a little over an hour, which is also the longest time i have ever let an agent run for. Accounting also for timeouts, retries, rate limits, and incomplete runs, are I think practical parts of this design.

