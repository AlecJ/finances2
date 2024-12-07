# finances

Process finances from Bank of America and USAA Bank Statments into
a single output TSV file with standardized formatting to allow easy
pasting into Google Sheets.

## Setup

Install Python3.11.9

Install Libraries:
`virtualenv venv`
`source venv/bin/activate`
`pip install freeze.txt`

Place USAA and Bank of America Bank Statements into the
`files_to_process` directory.

Copy `common_transactions.csv.EXAMPLE` and rename it to:
`common_transactions.csv`

This file is where you can set frequent transactions so the script
can automatically replace the noisy bank statement details with
a cleaner replacement, as well as automatically add a category to
the transaction.

## Running the Script

Run with:
`cd src`
`python main.py`

## To Do

-   CC payments and bank transfers
-   only include the first date for multiple transactions on the same day
-   payments received (venmo)
-   remove trailing empty transactions
-   add unit tests

-   check parsed as:
    `	123 -1,	-$502.00		boac`
    should be -1502.00
