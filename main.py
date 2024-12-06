'''
'''
from PyPDF2 import PdfReader
import re

# Files to process

files = [
    {"path": "", "type": "boa"},
    {"path": "", "type": "usaa"}
]

transactions = []


'''
'''


def parse_usaa():

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

                    transactions.append({
                        'Date': current_transaction[0],
                        'Description': current_transaction[3].strip(),
                        'Amount': -1 * float(amount),
                        'Account Name': 'usaa'
                    })
                    current_transaction = []


'''
'''


def parse_boa():
    for file_info in files:

        # Load the PDF file

        reader = PdfReader(file_info.get('path'))
        account = file_info.get('type')

        # Extract text from each page

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
                    transactions.append({
                        'Date': date,
                        'Description': description.strip(),
                        'Amount': float(amount),
                        'Account Name': 'boac'
                    })


'''
'''

for file_info in files:

    # Load the PDF file

    reader = PdfReader(file_info.get('path'))
    account = file_info.get('type')

    if account == 'boa':
        parse_boa()

    elif account == 'usaa':
        parse_usaa()

     # Sort transactions by date
        sorted_transactions = sorted(
            transactions, key=lambda x: x["Date"])

        # Format and output transactions
        formatted_transactions = []
        for txn in sorted_transactions:
            formatted_row = [
                f"{txn.get('Date')}\t\t\t\t\t\t",
                f"{txn.get('Description')}\t",
                f"${-1 * txn.get('Amount'):.2f}\t\t",
                txn.get('Account Name')
            ]
            formatted_transactions.append(formatted_row)

        # Output transactions
        output_file = 'transactions_output.tsv'
        with open(output_file, mode="w", newline="", encoding="utf-8") as file:
            file.write("Date\t\t\t\t\tType\tDescription\tAmount\t\tAccount\n")

            for txn in formatted_transactions:
                file.write("".join(txn) + '\n')

        print(f"Formatted transactions saved to {output_file}")
