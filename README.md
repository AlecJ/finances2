# finances

Process finances from Bank of America and USAA Bank Statments into
a single output TSV file with standardized formatting to allow easy
pasting into Google Sheets.

## Setup

Copy `common_transactions.csv.EXAMPLE` and rename it to:
`common_transactions.csv`

This file is where you can set frequent transactions so the script
can automatically replace the noisy bank statement details with
a cleaner replacement, as well as automatically add a category to
the transaction.

**Important:** Place the following into the `files_to_process` directory:

- USAA Bank Statements
- Bank of America Statements
- Venmo Statements
- Amazon Orders web pag (downloaded)

## Running with Docker

Files placed in `files_to_process` on the host are available inside the
container.

Process the statements currently in `files_to_process`:
`docker compose run --rm finances`
(or explicitly: `docker compose run --rm finances process`)

Output file `transactions_output.tsv` will placed in root directory.

Run the test suite:
`docker compose run --rm finances test`

Drop into a shell in the container:
`docker compose run --rm finances shell`

## Running Locally

Install Python 3.14

Install Libraries:
`virtualenv venv`
`source venv/bin/activate`
`pip install -r freeze.txt`

Active virtualenv if not already done:
`. venv/bin/activate`

Run with:
`cd src`
`python main.py`

Output file `transactions_output.tsv` will placed in root directory.

## Running Tests Locally

Active virtualenv if not already done:
`. venv/bin/activate`

Run with (from the project root):
`pytest`

## To Do

- rent (check payments)
- paypal statement
