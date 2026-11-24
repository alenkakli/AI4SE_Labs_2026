# Assessment by mimo-2.6-flash

# Week 03 Prompting
- Awarded: 3b out of 5b
- Commentary: The student completed Tasks 1 and 2 properly: three non-ROSES, non-zero-shot frameworks (CRISP, ICIO, ToT) were selected with sourced URLs, formulated prompts, run predictions for all 155 questions, measured run times, and produced comparison reports with (ASCII) visualisations. Task 3 has no deliverables beyond Task_3.md, so no points can be awarded there. Task 4 delivers a detailed, well-structured report with tables and graphs, but omits the required statistical significance determination and does not analyse the model and coding agent as factors.

## Task 1
- Awarded: 1b   (max 1b)
- Commentary: Three frameworks (CRISP, ICIO, ToT) were chosen from frompting.com with explicit source links, avoiding the forbidden ROSES and zero-shot approaches. Each prompt is written in its own file following the framework's structure (e.g., Context/Role/Instructions/Style/Parameters for CRISP; Instruction/Context/Input/Output for ICIO; branching/evaluation/pruning/decision for ToT) and is directly usable for Task 2's SQL-generation problem. The report explains where each framework was found and why it was chosen, with stated expectations (e.g., ToT expected to excel because the best path is not obvious). The motivations are somewhat brief and occasionally informal ("heard of it before"), but the required deliverables are all present and correct.

## Task 2
- Awarded: 1b   (max 1b)
- Commentary: All three prompts were executed and the full prediction sets (155 rows each) are stored as CRISP_output.csv, ICIO_output.csv and ToT_output.csv, identified by prompt via file naming, with the model (Copilot / gpt-6-luna) identified in the report. The report compares accuracy (27.74% / 20.00% / 99.35%, apparently from the provided evaluator), records per-run completion times and steps as the inference-time measure (5m13s/4m6s/10m46s), derives time-per-question and correct-outputs-per-minute, and includes bar-chart visualisations. Minor shortfalls: the model/prompt metadata is not embedded inside the data files themselves, the "times" are whole agent-session wall-clock times rather than pure model inference latency, and the visualisations are ASCII rather than graphics.

## Task 3
- Awarded: 0b   (max 1b)
- Commentary: Per the grading instructions, Task 3 has no deliverables beyond Task_3.md - no new metric implementation, no calculation over Task 2 predictions, and no comparison report exist in the Week_03_Prompting directory. Nothing to award.

## Task 4
- Awarded: 1b   (max 2b)
- Commentary: The report provides a solid detailed comparison: a prompt-structure/trade-off table, a results table with accuracy figures, ASCII bar graphs for accuracy and runtime, a runtime/steps table, derived efficiency ratios, and a reasonable interpretation of why ToT outperformed the shorter prompts (explicit exploration of candidates and schema checks, output-shape sensitivity of the evaluator). However, two explicit requirements are missing: (1) no statistical significance test of the between-prompt differences is performed or reported (no McNemar/chi-square, no p-values), and (2) only the prompt factor is analysed - the model and the coding agent as factors are not discussed. Half credit reflects roughly half of the required analysis depth.