# Prompt comparison analysis
## Scope and evidence

This analysis report compares the three prompting approaches selected in Task 1 and evaluated in Task 2: CRISP, ICIO, and Tree of Thoughts (ToT).

The Task 2 benchmark contains 155 natural language questions about a restaurant database. The three saved prediction files were reevaluated against the supplied labels and SQL database using the provided evaluation logic. A prediction counts as correct when executing its SQL returns the same result rows as the expected result. The evaluator disregards row ordering, but not selected columns, values, or duplicate rows.

## What differed between the prompts

| Framework | Prompt structure used | Intended benefit for this task | Main trade-off |
|---|---|---|---|
| **CRISP** | Supplies context, assigns a SQL-specialist role, gives the instruction to produce a query per question, limits the style to the provided schema/database and no explanations, and specifies a CSV filename. | Gives the model a concise role and output contract; the role and constraints should orient it toward SQL generation. | It does not explicitly require a question-by-question coverage check, schema validation, or evaluation of alternative interpretations. |
| **ICIO** | Separates the instruction, context, input file and headers, ordering/preservation requirements, and exact output format. | Its explicit input/output contract is well matched to producing a machine-readable predictions file. | It emphasizes data handling and formatting more than the reasoning needed to map question intent to the correct query and result shape. |
| **Tree of Thoughts (ToT)** | Requires the model to parse the request, sketch three candidates, score them against correctness/SQL/schema criteria, prune one, inspect the remaining two and edge cases, and choose one final query. It then constrains the final CSV output. | Forces explicit consideration of intent, filters, joins, aggregation, limits, schema support, and competing interpretations before choosing a query. | It is substantially longer and more demanding, and the saved run took longer and used more agent steps. Its multi-candidate process could be unnecessary for simple questions. |

The selected frameworks therefore differed in more than labels: CRISP foregrounded a role and response constraints; ICIO gave the clearest input/output workflow; ToT added an explicit query-planning and selection procedure. That last difference is especially relevant because the benchmark tests semantic interpretation and executable result equivalence, not merely whether the output is valid CSV or syntactically plausible SQL.

## Prediction results

| Prompt | Correct | Incorrect | Accuracy |
|---|---:|---:|---:|
| CRISP | 43 / 155 | 112 | 27.74% |
| ICIO | 31 / 155 | 124 | 20.00% |
| ToT | 154 / 155 | 1 | 99.35% |

The measured accuracy gap is large. ToT achieved 3.58 times CRISP's accuracy and 4.97 times ICIO's accuracy on this benchmark. CRISP exceeded ICIO by 7.74 percentage points (12 additional correct questions).

```text
Accuracy (each bar is approximately 2 percentage points)
CRISP  27.74% | ██████████████□□□□□□□□□□□□□□□□□□□□□□□□□□□□□□□□□□□□
ICIO   20.00% | ██████████□□□□□□□□□□□□□□□□□□□□□□□□□□□□□□□□□□□□□□□□
ToT    99.35% | ██████████████████████████████████████████████████
```

The scores indicate that having the model explicitly explore and evaluate possible query approaches was much more effective here than relying on a short output contract alone.
## Runtime and execution cost

| Prompt | Recorded completion time | Recorded steps | Approx. seconds per question | Correct outputs per recorded minute |
|---|---:|---:|---:|---:|
| CRISP | 5 min 13 sec | 32 | 2.02 | 8.2 |
| ICIO | 4 min 6 sec | 36 | 1.59 | 7.6 |
| ToT | 10 min 46 sec | 57 | 4.17 | 14.3 |

```text
Elapsed time (approximately; one block represents 15 seconds)
CRISP | █████████████████████
ICIO  | ████████████████
ToT   | ███████████████████████████████████████████
```

ToT took about 2.06 times as long as CRISP and 2.63 times as long as ICIO. Its time per question was higher, but its much higher accuracy also meant more correct outputs per recorded minute in this run. ICIO was fastest overall; CRISP produced more correct outputs than ICIO despite taking longer.
## Interpreting the difference

### Prompt design

The result is consistent with the ToT prompt supplying a useful process for a task where the correct query is not always a direct transcription of the question. It explicitly asks the model to identify entities, filters, relationships, aggregation, ordering, and limits; compare plausible candidates; check candidates against the schema and records; and select a final query. The simpler prompts define the desired artifact and constraints, but do not provide the same explicit procedure for checking semantic and schema-level choices.

The benchmark's exact result comparison makes query output shape important as well as query intent. For example, a query that finds the right restaurant but selects a different set of columns can still fail. Differences in joins, filter interpretation, or output columns can therefore lower accuracy even when a query looks reasonable to a human. The score alone does not categorize all 112 CRISP or 124 ICIO errors, so the report does not claim that one specific error type explains all of their failures.


## Conclusion 

For the Task 2 evaluate_retrieval_predictions benchmark, ToT is the clear accuracy winner (154/155), CRISP is second (43/155), and ICIO is third (31/155). The additional accuracy of ToT came with increased elapsed time and more recorded steps; nevertheless, its observed correct output was the highest in this run.

What presumably brought the ToT framework such a clear addvantage in accuracy was asking the model to try and evaluate different ways of solving the problem at hand. Also quite interestingly, the CRISP framework worked a bit better than ICIO with the main difference between the two being the use of a role.