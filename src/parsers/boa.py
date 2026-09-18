'''
Parses Bank of America Bank Statements and returns a list of transactions.

Input:
- reader: A PDF reader that can iterate through the document's text line by line.

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

from datetime import datetime
from itertools import zip_longest


def parse_boa(reader):

    result = []

    transaction_pattern = r"(\d{2}\/\d{2}\/\d{2})([\s\S]*?)(-?(?:\d{1,3}(?:,\d{3})+|\d+)\.\d{2})"

    for page in reader.pages:

        page_text = page.extract_text()
        lines = page_text.splitlines()

        # some transactions can be split across two lines
        # iterate through the current and next line in tandem
        #
        # zip_longest (instead of zip(lines, lines[1:])) makes sure the
        # last line of the page is still checked on its own -- zip alone
        # would silently drop it, since it's never paired as the first
        # element of a pair

        for line, next_line in zip_longest(lines, lines[1:], fillvalue=''):

            # regex match for transaction data

            match = re.match(transaction_pattern, line)

            # double check the match with the current and next lines

            if not match and next_line:
                match = re.match(transaction_pattern, line + next_line)

            if match:
                date, description, amount = match.groups()
                result.append({
                    'Date': datetime.strptime(date, '%m/%d/%y').strftime('%m/%d/%Y'),
                    'Description': description.strip(),
                    'Amount': float(amount.replace(',', '')),
                    'Account Type': 'boac'
                })

    return result
