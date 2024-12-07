'''
Parses USAA Bank Statements and returns a list of transactions.

Input:
- reader: A PDF reader that can iterate through the document's text line by line.

Returns:
A list of transactions with the following format:
{
    "Date": date as string,
    "Description": string,
    "Amount": float,
    "Account Type": string
}
'''

import re


def parse_usaa(reader):

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

                    result.append({
                        'Date': current_transaction[0][:5],
                        'Description': current_transaction[3].strip(),
                        'Amount': -1 * float(amount),
                        'Account Type': 'usaa'
                    })
                    current_transaction = []

    return result


'''
Parses Bank of America Bank Statements and returns a list of transactions.

Input:
- reader: A PDF reader that can iterate through the document's text line by line.

Returns:
A list of transactions with the following format:
{
    "Date": date as string,
    "Description": string,
    "Amount": float,
    "Account Type": string
}
'''


def parse_boa(reader):

    result = []

    transaction_pattern = r"(\d{2}\/\d{2}\/\d{2})([\s\S]*?)(-?\d+\.\d{2})"

    for page in reader.pages:

        page_text = page.extract_text()
        lines = page_text.splitlines()

        # some transactions can be split across two lines
        # iterate through the current and next line in tandem

        for line, next_line in zip(lines, lines[1:]):

            # regex match for transaction data

            match = re.match(transaction_pattern, line)

            # double check the match with the current and next lines

            if not match and next_line:
                match = re.match(transaction_pattern, line + next_line)

            if match:
                date, description, amount = match.groups()
                result.append({
                    'Date': date[:5],
                    'Description': description.strip(),
                    'Amount': float(amount),
                    'Account Type': 'boac'
                })

    return result
