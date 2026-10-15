'''
This script takes Bank of America and USAA bank statements, and
processes them into a standardized list of transactions which
can be copy and pasted into Google Sheets.

All files to be consumed must be placed in the `files_to_process`
directory in this repo.
'''

import os

from datetime import datetime
from pathlib import Path

from PyPDF2 import PdfReader

from parsers import parse_boa, parse_usaa, parse_amazon, parse_venmo

from helpers import get_account_type, get_usaa_statement_closing_date, convert_common_transactions, process_account_transfers, match_amazon_orders, match_venmo_transactions, match_refunds


if __name__ == '__main__':

    # load all files from files_to_process directory

    file_directory = '../files_to_process'
    transactions = []

    # Amazon orders and Venmo transactions are matched against their
    # corresponding generic bank transactions below and folded into the
    # transaction they matched, rather than being written to the output
    # TSV as their own rows.

    amazon_orders = []
    venmo_transactions = []

    for file_name in os.listdir(file_directory):

        file_path = os.path.join(file_directory, file_name)

        # Check if it's a valid PDF, HTML, or CSV file

        if not file_name.endswith((".pdf", ".html", ".csv")) or not os.path.isfile(file_path):
            display_name = f"{file_name}/" if os.path.isdir(file_path) else file_name
            print(f'Skipping either unsupported or invalid file: {display_name}')
            continue

        # Parse files depending on the source of the bank statement

        account = get_account_type(file_name)

        if account not in ['boa', 'usaa', 'amazon', 'venmo']:
            print(
                f"File {file_name} does not match any known account types. Skipping.")
            continue

        if account == 'boa':
            transactions += parse_boa(PdfReader(file_path))

        elif account == 'usaa':
            closing_date = get_usaa_statement_closing_date(file_name)
            transactions += parse_usaa(PdfReader(file_path), closing_date)

        elif account == 'amazon':
            amazon_orders += parse_amazon(file_path)

        elif account == 'venmo':
            venmo_transactions += parse_venmo(file_path)

    # After accumulating all transactions into a standard format...

    # Match generic "AMAZON.COM" transactions up with parsed Amazon
    # orders, to give them a more detailed description

    transactions = match_amazon_orders(transactions, amazon_orders)

    # Match generic "VENMO" transactions up with parsed Venmo
    # transactions, to give them a more detailed description

    transactions = match_venmo_transactions(transactions, venmo_transactions)

    # Match refund/credit transactions against the purchase they
    # refunded, so they can be rendered directly under it instead of as
    # their own separately-dated transaction

    transactions = match_refunds(transactions)

    # Attempt to add details to any found common transactions

    transactions = convert_common_transactions(transactions)

    transactions = process_account_transfers(transactions)

    # Sort transactions by date. Dates are stored as "MM/DD/YYYY", so
    # they're parsed into real dates rather than sorted as strings --
    # sorting the raw strings would order by month before year.

    sorted_transactions = sorted(
        transactions, key=lambda x: datetime.strptime(x["Date"], '%m/%d/%Y'))

    # Format (for google sheets)

    formatted_transactions = []

    # Only include the first occurrence of each date in the output file

    prev_date = None

    # Track the date range actually written to the output, for the
    # summary printed at the end

    first_date = None
    last_date = None

    for txn in sorted_transactions:

        full_date = txn.get('Date')

        # The year is only tracked internally (for correct sorting and
        # matching); the output stays "MM/DD" to match the spreadsheet's
        # existing format.
        date = full_date[:5] if full_date else ''

        if prev_date and prev_date == full_date:
            date = ''

        # Skip rows where amount is 0
        if txn.get('Amount') == 0:
            continue

        # This is income
        # None is cast as 1 since it represents an account transfer transaction
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

        # A matched refund is rendered as its own row directly under its
        # purchase, with no date of its own -- see match_refunds

        refund = txn.get('Refund')

        if refund:
            formatted_transactions.append([
                f"\t\t\t\t\t",
                f"{txn.get('Category', '')}\t"
                f"{refund['Description']}\t",
                f"-${refund['Amount']:.2f}\t\t",
                f"{txn.get('Account Type', '')}\t",
                f"\t",
                f"\t",
            ])

        if first_date is None:
            first_date = full_date
        last_date = full_date

        prev_date = full_date

    # Output transactions to a tsv

    # Get the path of the project root

    project_root = Path(__file__).resolve().parent.parent

    output_file = os.path.join(project_root, "transactions_output.tsv")

    with open(output_file, mode="w", newline="", encoding="utf-8") as file:

        file.write(
            "Date\t\t\t\t\tCategory\tDescription\tAmount\t\tAccount\n")

        for txn in formatted_transactions:
            file.write("".join(txn) + '\n')

    transaction_count = len(formatted_transactions)

    if transaction_count:
        print(
            f"Processed {transaction_count} transaction(s) from {first_date} to {last_date}. Saved to {output_file}")
    else:
        print(f"No transactions found. Saved empty file to {output_file}")
