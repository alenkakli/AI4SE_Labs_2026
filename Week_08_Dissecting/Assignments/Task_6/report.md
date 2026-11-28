# Conversation Notes

**Topic:** Delegating the Week 3 assignment review to subagents and recording the resulting grading notes.

## User requests and agent responses

### Exchange 1

**The user asked:**
*The user instructed the coding agent to spawn subagents and inspect every assignment and solution in `Week_03_Prompting/Assignments/`. The work required reading the Task 1–4 specifications and submissions, reporting expected points, missing deliverables, and file evidence for each task, and avoiding full credit without explicit evidence.*

**Agent responded:**
The agent divided the work into four subagent tasks, assigning one subagent to each Week 3 task. Each subagent was told to inspect only its assigned task, cite exact file paths and line numbers or quotations, assess missing deliverables, and avoid modifying files.

The subagents returned the following task-level findings:

- **Task 1:** The agent found the requested 1b outcome satisfied. It identified the CRISP, ICIO, and ToT prompt files and matching source-and-reason evidence in the report.
- **Task 2:** The agent estimated 0/1b because the CSV prediction files contained only `question,predicted_sql`, while the specification required model and prompt identification metadata in the prediction data. Accuracy, comparison, visualization, inference-time evidence, and 155 prediction records were otherwise found.
- **Task 3:** The agent estimated 0/1b. The folder contained only `Task_3.md`; no metric implementation or report was present.
- **Task 4:** The agent estimated approximately 1b/2b. The report contained a detailed prompt comparison, tables, graphs, runtime analysis, and interpretation, but it did not provide a statistical-significance determination or substantive model/coding-agent factor analysis.

**Outcome:**
The agent directly verified the Task 1–4 specifications and key submission files, including the prompt files and Task 2 prediction CSV headers. It consolidated the evidence into an estimated grading table and stated that no files had been modified.

### Exchange 2

**The user asked:**
The user requested that conversation notes be created from the preceding discussion and placed in the Week 08 Task 6 folder.

**Agent responded:**
The agent loaded the conversation-notes instructions, inspected [Task_6.md](/C:/Users/alzbe/Documents/tazky%20hacking/Softverove%20inzinierstvo%20s%20AI/github_clone/AI4SE_Labs_2026/Week_08_Dissecting/Assignments/Task_6/Task_6.md) to confirm the submission format, and prepared this textual record.

**Outcome:**
This report records the subagent-led grading conversation and its verified results.

## Decisions and completed actions

- A coding-agent subagent was used for each of Tasks 1–4.
- The subagents' evidence was cross-checked against the actual specification and submission files.
- No repository files were modified during the grading review.
- These conversation notes were created in the Week 08 Task 6 submission folder.
