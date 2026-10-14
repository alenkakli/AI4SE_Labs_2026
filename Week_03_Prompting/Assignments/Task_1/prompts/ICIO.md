Instruction
For each restaurant related natural language question, write one SQL query that answers it.

Context
You are generating SQL predictions for questions about a restaurant database. You will be given the database schema, database records and the questions.

Input
Input is a CSV file "restaurants_dataset.csv" with these headers: question,result. Process every question in the original order and preserve each question.

Output
Create a CSV file "restaurants_dataset_predictions.csv" with headers: question,predicted_sql. Do not provide any explanations or query results in the output file.