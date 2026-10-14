Problem and why the path is not obvious
You need to translate each natural language question about a restaurant database into one SQL query. A question can be ambiguous about which tables to join, how to interpret a condition, or whether to aggregate, sort, or limit results.

Branch: generate genuinely different candidates
First identify what the question asks for, including relevant entities, filters, relationships, aggregation, ordering, and result limits. Then generate three genuinely different candidate query approaches where the question allows meaningful alternatives. Sketch each candidate in a few sentences or as a query outline before evaluating any of them.

Evaluate: score each against stated criteria
Score each candidate from 1 to 5, with a brief reason for each score, against all of these criteria: does it correctly represent every requested condition and intended result, SQL correctness, does it only use tables, columns and relationships supported by the supplied schema?

Prune: drop one, and say what would bring it back
Name the weakest candidate and state why it is being discarded. Also state what new evidence or change in the question/schema could make it worth reconsidering. Develop the remaining two candidates one level deeper, checking their joins, predicates, and edge cases against the available schema and records.

Decide, with the evidence that would change it
Select one final candidate for the question. Briefly identify the evidence that would change the choice, such as a different schema relationship, a clarified interpretation, or a database constraint that contradicts an assumption. Do not return “it depends” instead of selecting a query. 

Return a CSV file restaurants_dataset_predictions.csv with exactly these headers:question,predicted_sql. The output file should only contain the original question and the best fit SQL query for it for every question in the original CSV file.
