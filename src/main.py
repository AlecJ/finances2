'''
This script takes Bank of America and USAA bank statements, and
processes them into a standardized list of transactions which
can be copy and pasted into Google Sheets.

All files to be consumed must be placed in the `files_to_process`
directory in this repo.
'''

import os

from PyPDF2 import PdfReader

from parsers import parse_boa, parse_usaa

from helpers import get_account_type, convert_common_transactions


if __name__ == '__main__':

    # load all files from files_to_process directory

    file_directory = '../files_to_process'
    transactions = []

    for file_name in os.listdir(file_directory):

        file_path = os.path.join(file_directory, file_name)

        # Check if it's a valid PDF file

        if not file_name.endswith(".pdf") or not os.path.isfile(file_path):
            print(f'Skipping either non pdf file or invalid file: {file_name}')
            continue

        # Load the PDF file

        reader = PdfReader(file_path)

        # Parse files depending on the source of the bank statement

        account = get_account_type(file_name)

        if account == 'boa':
            transactions += parse_boa(reader)

        elif account == 'usaa':
            transactions += parse_usaa(reader)

    # After accumulating all transactions into a standard format...

    # Attempt to add details to any found common transactions

    transactions = convert_common_transactions(transactions)

    # Sort transactions by date

    sorted_transactions = sorted(
        transactions, key=lambda x: x["Date"])

    # Format (for google sheets)

    formatted_transactions = []
    for txn in sorted_transactions:
        formatted_row = [
            f"{txn.get('Date')}\t\t\t\t\t",
            f"{txn.get('Category', '')}\t"
            f"{txn.get('Description')}\t",
            f"${-1 * txn.get('Amount'):.2f}\t\t",
            txn.get('Account Type')
        ]
        formatted_transactions.append(formatted_row)

    # Output transactions to a tsv

    output_file = 'transactions_output.tsv'
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        file.write(
            "Date\t\t\t\t\tCategory\tDescription\tAmount\t\tAccount\n")

        for txn in formatted_transactions:
            file.write("".join(txn) + '\n')

    print(f"Formatted transactions saved to {output_file}")
