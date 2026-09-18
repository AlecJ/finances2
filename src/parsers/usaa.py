'''
Parses USAA Bank Statements and returns a list of transactions.

USAA statement lines only give a "MM/DD" date, with no year, so the
year has to be inferred from the statement's closing date (taken from
the file name -- see helpers.get_usaa_statement_closing_date). A
transaction dated later in the year than the closing date must belong
to the previous year (this only comes up for a statement whose period
crosses a new year, e.g. closing in January for a period that started
in December).

Input:
- reader: A PDF reader that can iterate through the document's text line by line.
- closing_date: a datetime for the statement's closing date, used to
  resolve the year for each "MM/DD" transaction date.

Returns:
A list of transactions with the following format:
{
    "Date": date as string ("MM/DD/YYYY"),
    "Description": string,
    "Amount": float,
    "Account Type": string
}
'''

import re


def parse_usaa(reader, closing_date):

    result = []

    date_pattern = r"^\d{2}/\d{2}$"

    # Extract text from each page

    for page in reader.pages:

        page_text = page.extract_text()
        lines = page_text.splitlines()

        current_transaction = []
        adding_transaction = False

        for line in lines:

            if re.match(date_pattern, line) and not adding_transaction:
                adding_transaction = True

            # add lines until a $ char is found (5 lines typically)

            if adding_transaction:
                current_transaction.append(line)

                if '$' in line:
                    adding_transaction = False

                if not adding_transaction:

                    # remove dollar sign from amount

                    amount = current_transaction[-1][1:]

                    # remove commas

                    amount = amount.replace(",", "")

                    # usaa formats negatives with a - char at the end
                    # move it to the front

                    if amount[-1] == '-':
                        amount = '-' + amount[:-1]

                    month, day = current_transaction[0][:5].split('/')
                    year = closing_date.year

                    if int(month) > closing_date.month:
                        year -= 1

                    result.append({
                        'Date': f"{month}/{day}/{year}",
                        'Description': current_transaction[-2].strip(),
                        'Amount': -1 * float(amount),
                        'Account Type': 'usaa'
                    })
                    current_transaction = []

    return result
