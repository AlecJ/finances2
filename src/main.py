'''
This script takes Bank of America and USAA bank statements, and
processes them into a standardized list of transactions which
can be copy and pasted into Google Sheets.

All files to be consumed must be placed in the `files_to_process`
directory in this repo.
'''

import os

from pathlib import Path

from PyPDF2 import PdfReader

from parsers import parse_boa, parse_usaa

from helpers import get_account_type, convert_common_transactions, process_account_transfers


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

    transactions = process_account_transfers(transactions)

    # Sort transactions by date

    sorted_transactions = sorted(
        transactions, key=lambda x: x["Date"])

    # Format (for google sheets)

    formatted_transactions = []

    # Only include the first occurrence of each date in the output file

    prev_date = None

    for txn in sorted_transactions:

        date = txn.get('Date')

        if prev_date and prev_date == date:
            date = ''

        # This is income
        if txn.get('Amount', 1) > 0:
            formatted_row = [
                f"{date}\t\t",
                f"{txn.get('Description', '')}\t",
                "\t" if not 'Amount' in txn else f"${txn.get('Amount'):.2f}\t",
                "\t\t\t\t\t",
                f"{txn.get('Account Type', '')}\t",
                f"{txn.get('Account Transfer To', '')}\t",
                f"{txn.get('Transfer Amount', '')}\t",
            ]

        # This is out-go
        else:
            formatted_row = [
                f"{date}\t\t\t\t\t",
                f"{txn.get('Category', '')}\t"
                f"{txn.get('Description')}\t",
                f"${-1 * txn.get('Amount'):.2f}\t\t",
                f"{txn.get('Account Type', '')}\t",
                f"{txn.get('Account Transfer To', '')}\t",
                f"{txn.get('Transfer Amount', '')}\t",
            ]

        formatted_transactions.append(formatted_row)

        prev_date = txn.get('Date')

    # Output transactions to a tsv

    # Get the path of the project root

    project_root = Path(__file__).resolve().parent.parent

    output_file = os.path.join(project_root, "transactions_output.tsv")

    with open(output_file, mode="w", newline="", encoding="utf-8") as file:

        file.write(
            "Date\t\t\t\t\tCategory\tDescription\tAmount\t\tAccount\n")

        for txn in formatted_transactions:
            file.write("".join(txn) + '\n')

    print(f"Formatted transactions saved to {output_file}")
