# CSV to Something

A script that converts CSV to SQLite and JSON and vice versa.


## Rationale

This project in fact was started from an old script written in 2014.
The problem was to do some advanced calculation over the spreadsheet file contains the student data, such as student scores.
Creating the grade and do the averaging some how is too troublesome, especially when I need to have a simple form of table.
Meaning, I need to create a simple summary table from the raw data.
Using the pivot table is not satisfying though. Using macro from spreadsheet software is impractical (BASIC programming language is exhaustive).

Therefore, the best solution is to use SQL to query what I want and create the table from the query. That is why I created csv2sqlite and with the "reverse" feature.

Then recently, because I need some generated JSON data for software development, then I think it will be good that I can add in the CSV to JSON feature and vice versa.
And, I feel that JavaScript to manipulate the array will be much more easier than SQL.
As a result, I turn the script into this project.
