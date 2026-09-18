'''
Parses a Venmo account statement CSV export and returns a list of
Venmo transactions.

The exported CSV has a few metadata lines before the real header row,
and a disclaimer block after the transactions, so the header row is
located by searching for the row that contains "Datetime" rather than
assuming a fixed line number.

Input:
- file_path: path to the exported Venmo statement .csv file.

Returns:
A list of transactions with the following format:
{
    "Date": date as string ("MM/DD/YYYY"),
    "Description": string (the transaction's Note, falling back to Type),
    "Amount": float,
    "Type": string,
    "Funding Source": string,
    "Destination": string,
    "Account Type": string
}
'''

import csv

from datetime import datetime


def parse_venmo(file_path):

    result = []

    with open(file_path, newline='', encoding='utf-8') as file:
        rows = list(csv.reader(file))

    header_index = next(i for i, row in enumerate(rows) if 'Datetime' in row)
    header = rows[header_index]

    for row in rows[header_index + 1:]:

        if len(row) < len(header):
            continue

        record = dict(zip(header, row))

        datetime_text = record.get('Datetime', '').strip()
        amount_text = record.get('Amount (total)', '').strip()

        if not datetime_text or not amount_text:
            continue

        date = datetime.strptime(
            datetime_text, '%Y-%m-%dT%H:%M:%S').strftime('%m/%d/%Y')

        amount = float(amount_text.replace(
            '$', '').replace(',', '').replace(' ', ''))

        note = record.get('Note', '').strip()
        txn_type = record.get('Type', '').strip()

        result.append({
            'Date': date,
            'Description': note if note else txn_type,
            'Amount': amount,
            'Type': txn_type,
            'Funding Source': record.get('Funding Source', '').strip(),
            'Destination': record.get('Destination', '').strip(),
            'Account Type': 'venmo',
        })

    return result
