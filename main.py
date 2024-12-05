'''
'''
from PyPDF2 import PdfReader
import re
import csv

#
#
# Set FILENAME to the name of the file you want to process.

FILENAME = "BOA_10.pdf"

#
#
#


# Load the PDF file
reader = PdfReader("BOA_10.pdf")
account = 'boac'

# Extract text from each page

transactions = []

for page in reader.pages:

    page_text = page.extract_text()
    lines = page_text.splitlines()

    for line in lines:

        # regex match for (dd/mm/yy)(one or more any char)(0.00)
        match = re.match(
            r"(\d{2}\/\d{2}\/\d{2})([^-]+)(-?\d+\.\d{2})", line)

        if match:
            date, description, amount = match.groups()
            transactions.append({
                'Date': date,
                'Description': description.strip(),
                'Amount': float(amount),
                'Account Name': account
            })


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
