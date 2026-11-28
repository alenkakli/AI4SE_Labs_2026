# Assessment by laguna-s-2.1

# Week 03 Prompting
- Awarded: 3b out of 5b
- Commentary: The student completed Task 1 (three prompting frameworks with prompts and rationale) and Task 2 (three prediction CSVs, an evaluation report with accuracy comparison, inference times, and a visualization) fully. Task 3 produced no deliverables beyond the assignment description file (Task_3.md) — no metric implementation code, no report, and no alternative guide were submitted. Task 4 contains a well-structured report with tables and charts analyzing accuracy differences and explaining prompt design trade-offs, but it omits the required statistical significance test and does not analyze the model or coding agent as factors.

## Task 1
- Awarded: 1b   (max 1b)
- Commentary: The student selected three distinct prompting frameworks from frompting.com/frameworks: CRISP, ICIO, and Tree of Thoughts (ToT). None of the frameworks are ROSES or zero-shot. Each framework has a corresponding prompt file (Task_1/prompts/CRISP.md, ICIO.md, ToT.md) containing a formulated prompt. The report (Task_1/report.md) cites the source URL for each framework and explains the rationale for choosing it, including why it is expected to perform well for the SQL generation task. All required outputs (data file with formulated prompts and a report on framework choice) are present and match the assignment specification.

## Task 2
- Awarded: 1b   (max 1b)
- Commentary: The student produced three prediction CSV files (ToT_output.csv, ICIO_output.csv, CRISP_output.csv) under Task_2/prompt_outputs/ with the required headers (question,predicted_sql). The report (Task_2/report.md) compares how well the model solved the problems with each framework, presenting accuracy (ToT 99.35%, CRISP 27.74%, ICIO 20.00%), correct counts, steps, and completion time as an inference-time proxy. Model identification metadata is provided (Github Copilot, gpt-6-luna) and prompt identification is conveyed via the framework-specific filenames and report content. A text-based accuracy visualization (ASCII bar chart) is included as required.

## Task 3
- Awarded: 0b   (max 1b)
- Commentary: Task 3 requires proposing a new metric, arguing why it is suitable, implementing the metric calculation, computing metric values for the Task 2 predictions, and creating a report comparing metric values across prompts. No such deliverables exist. The only file in the Task_3 directory is Task_3.md, which is the assignment description itself. There is no source code file implementing a metric, no report comparing metric values, and no alternative implementation guide. As explicitly noted, Task 3 has no deliverables beyond Task_3.md, so this task is incomplete.

## Task 4
- Awarded: 1b   (max 2b)
- Commentary: The Task 4 report (Task_4/report.md) is a detailed analysis comparing the three prompts. It includes tables (framework structure comparison, prediction results, runtime and execution cost) and two ASCII visualizations (accuracy bars and elapsed-time bars). It interprets the large accuracy gap between ToT and the other frameworks, discusses prompt design trade-offs, and provides a conclusion. However, it does not perform or mention any statistical significance test (e.g., chi-squared or proportion test) despite the assignment explicitly requesting this. It also does not reference Task 3 deliverables (which do not exist) and does not analyze the model (gpt-6-luna) or the coding agent (GitHub Copilot) as factors influencing the differences. These omissions justify partial credit.
