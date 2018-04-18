# CSV to Something

A script that converts CSV to SQLite and JSON and vice versa.


## Rationale

This project in fact was started from an old script written in 2014.
The problem was to do some advanced calculation over the spreadsheet file contains the student data, such as student scores.
Creating the grade and do the averaging some how is too troublesome, especially when I need to have a simple form of table.
Meaning, I need to create a simple summary table from the raw data.
Using the pivot table is not satisfying though. Using macro from spreadsheet software is impractical (BASIC programming language is exhaustive).

Therefore, the best solution is to use SQL to query what I want and create the table from the query. That is why I created `csv2sqlite` and with the "reverse" feature.

Then recently, because I need some generated JSON data for software development, then I think it will be good that I can add in the CSV to JSON feature and vice versa.
And, I feel that using JavaScript to manipulate the array will be much more easier than SQL.
As a result, I turn the script into this project.

## Example

### Converting CSV to JSON

Let's say you want to mock the data of an array of users in the JSON format for your project, use a spreadsheet software (recommend LibreOffice) to save as CSV format.
Enter the data as following,

```
id | username  | full_name  | age | email          | gender
-----------------------------------------------------------
1  | leonheart | Leon Heart | 17  | leon@heart.com | male
2  | zidane    | Zidane     | 21  | zid@ne.com     | male
3  | tifa      | Tifa       | 18  | tifa@lock.com  | female
```

Save it as `users.csv`. Then run the command

```
./csv_to_something.py --c2j users.csv users.json
```

Then you will get the `users.json` with the following content.

```json
[
  {
    "id": 1,
    "username": "leonheart",
    "full_name": "Leon Heart",
    "age": 17,
    "email": "leon@heart.com",
    "gender": "male"
  },
  {
    "id": 2,
    "username": "zidane",
    "full_name": "Zidane",
    "age": 21,
    "email": "zid@ne.com",
    "gender": "male"
  },
  {
    "id": 3,
    "username": "tifa",
    "full_name": "Tifa",
    "age": 18,
    "email": "tifa@lock.com",
    "gender": "female"
  }
]
```
