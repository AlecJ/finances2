'''
Parses USAA Bank Statements and returns a list of dictionaries in the form of:

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

    # Extract text from each page

    for page in reader.pages:

        page_text = page.extract_text()
        lines = page_text.splitlines()

        date_pattern = r"^\d{2}/\d{2}$"

        current_transaction = []
        adding_transaction = False

        for line in lines:

            if re.match(date_pattern, line) and not adding_transaction:
                adding_transaction = True

            # add the next 4 lines
            if adding_transaction:
                current_transaction.append(line)

                if '$' in line:
                    adding_transaction = False

                if not adding_transaction:

                    # remove dollar sign from amount
                    amount = current_transaction[-1][1:]

                    # remove commas
                    amount = amount.replace(",", "")

                    # usaa formats negatives at the end
                    # move it to the front
                    if amount[-1] == '-':
                        amount = '-' + amount[:-1]

                    result.append({
                        'Date': current_transaction[0],
                        'Description': current_transaction[3].strip(),
                        'Amount': -1 * float(amount),
                        'Account Type': 'usaa'
                    })
                    current_transaction = []

    return result


'''
Parses Bank of America Bank Statements and returns a list of dictionaries
in the form of:

{
    "Date": date as string,
    "Description": string,
    "Amount": float,
    "Account Type": string
}
'''


def parse_boa(reader):

    result = []

    for page in reader.pages:

        page_text = page.extract_text()
        lines = page_text.splitlines()

        for line in lines:
            # regex match for transaction data
            # match = re.match(transaction_regex, line)
            match = re.match(
                r"(\d{2}\/\d{2}\/\d{2})([^-]+)(-?\d+\.\d{2})", line)

            if match:
                date, description, amount = match.groups()
                result.append({
                    'Date': date,
                    'Description': description.strip(),
                    'Amount': float(amount),
                    'Account Type': 'boac'
                })

    return result
