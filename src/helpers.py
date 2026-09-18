import re
import csv

from datetime import datetime

'''
This helper function uses regex to matche file names to
a bank type, which dictates which parser to use.
'''

match_file_name_to_account_type = [
    {"expression": r"eStmt_\d{4}-\d{2}-\d{2}.pdf", "type": "boa"},
    {"expression": r"\d{8}_BANK.*\.pdf", "type": "usaa"},
    {"expression": r"\d{4}-\d{2}-\d{2}_AMERICAN_EXPRESS_.*_STATEMENT.*\.pdf", "type": "usaa"},
    {"expression": r"amazon-\d{1,2}-\d{1,2}-\d{2}\.html", "type": "amazon"},
    {"expression": r"VenmoStatement_[A-Za-z]+_\d{4}\.csv", "type": "venmo"},
]


def get_account_type(file_name):
    for pattern in match_file_name_to_account_type:
        if re.fullmatch(pattern["expression"], file_name):
            return pattern["type"]
    return None  # Return None if no match is found


'''
USAA statement transactions are only dated "MM/DD", with no year, so
the year has to be inferred from the statement's closing date. Both
USAA file name patterns start with that closing date, just in
different formats, so it's pulled from the file name rather than the
PDF contents.
'''


def get_usaa_statement_closing_date(file_name):

    match = re.match(r"(\d{8})_BANK", file_name)

    if match:
        return datetime.strptime(match.group(1), '%Y%m%d')

    match = re.match(r"(\d{4}-\d{2}-\d{2})_AMERICAN_EXPRESS", file_name)

    if match:
        return datetime.strptime(match.group(1), '%Y-%m-%d')

    return None


'''
Iterate through all current transactions and see if they match any of the
configured list of common transactions, using a simple substring match.

Any transactions that are matched, are updated with a cleaned description string
and a category is added to the transaction.
'''


def convert_common_transactions(transactions):

    result = []

    # load common_transactions into memory
    common_transactions_file_path = '../common_transactions.csv'

    # if the common_transactions csv file is not present, raise an error
    try:
        with open(common_transactions_file_path, 'r') as file:
            # Load all rows directly into a list using list comprehension
            common_transactions = list(csv.DictReader(file))
    except FileNotFoundError:
        raise FileNotFoundError(
            "common_transactions.csv is missing from the PROJECT ROOT. Add this file to continue.")

    for transaction in transactions:

        for common_transaction in common_transactions:

            # check if a transaction's description contains a substring
            # this matches a common transaction

            if common_transaction.get('substring_match') in transaction.get('Description'):

                # replace the description and add the associated category to the row

                transaction['Description'] = common_transaction.get(
                    'cleaned_description')
                transaction['Category'] = common_transaction.get('category')

        result.append(transaction)

    return result


def process_account_transfers(transactions):
    result = []

    boac_to_boas = ["BOA KeepTheChange",]
    boas_to_boac = ["Online Banking transfer from SAV 2908",]
    boac_to_usaa = ["USAA CREDIT CARD PAYMENT SAN ANTONIO  TX",
                    "AUTOMATIC PAYMENT - THANK YOU",]
    boas_to_usaa = []
    always_delete = ["Online Banking transfer to CHK 8628",
                     "KEEP THE CHANGE TRANSFER TO ACCT 2908",
                     "USAA.COM PAYMNT  DES:CREDIT CRD",
                     "USAA CREDIT CARD DES:PAYMENT",
                     "USAA FSB CC",]

    for transaction in transactions:
        desc = transaction.get('Description', '')

        if any(substring in desc for substring in boac_to_boas):
            transaction['Account Type'] = 'boac'
            transaction['Account Transfer To'] = 'boas'
            transaction['Transfer Amount'] = transaction['Amount']
            del transaction['Amount']
            del transaction['Description']

        elif any(substring in desc for substring in boas_to_boac):
            transaction['Account Type'] = 'boas'
            transaction['Account Transfer To'] = 'boac'
            transaction['Transfer Amount'] = transaction['Amount']
            del transaction['Amount']
            del transaction['Description']

        elif any(substring in desc for substring in boac_to_usaa):
            transaction['Account Type'] = 'boac'
            transaction['Account Transfer To'] = 'usaa'
            transaction['Transfer Amount'] = transaction['Amount']
            del transaction['Amount']
            del transaction['Description']

        elif any(substring in desc for substring in boas_to_usaa):
            transaction['Account Type'] = 'boas'
            transaction['Account Transfer To'] = 'usaa'
            transaction['Transfer Amount'] = transaction['Amount']
            del transaction['Amount']
            del transaction['Description']

        elif any(substring in desc for substring in always_delete):
            continue

        result.append(transaction)

    return result


'''
Matches generic "AMAZON.COM..." transactions against parsed Amazon
orders, and replaces the transaction's description with the order's
item names.

Amazon's order-placed date doesn't always match the date the card is
actually charged (it's often 1-2 days later), so orders are matched by
amount and allowed to be up to `max_days_after` days after the order
was placed. Each order can only be matched to one transaction.
'''


def match_amazon_orders(transactions, amazon_orders, max_days_after=5, max_description_length=60):

    unmatched_orders = list(amazon_orders)

    for transaction in transactions:
        desc = transaction.get('Description', '')

        if 'AMAZON' not in desc.upper():
            continue

        amount = transaction.get('Amount')

        if amount is None:
            continue

        transaction_date = datetime.strptime(transaction['Date'], '%m/%d/%Y')

        best_match = None
        best_day_diff = None

        for order in unmatched_orders:

            if abs(order['Amount'] - amount) > 0.01:
                continue

            order_date = datetime.strptime(order['Date'], '%m/%d/%Y')
            day_diff = (transaction_date - order_date).days

            if not (0 <= day_diff <= max_days_after):
                continue

            if best_day_diff is None or day_diff < best_day_diff:
                best_match = order
                best_day_diff = day_diff

        if best_match is None:
            continue

        unmatched_orders.remove(best_match)

        summary = '; '.join(best_match['Items'])

        if len(summary) > max_description_length:
            summary = summary[:max_description_length - 3].rstrip() + '...'

        transaction['Description'] = f"Amazon: {summary}"

    return transactions


'''
Matches generic "VENMO..." transactions against parsed Venmo
transactions, and replaces the bank transaction's description with a
"VENMO: " prefix followed by the Venmo transaction's description (its
Note, or its Type if there's no Note).

Not every Venmo transaction hits the bank -- one funded by or settled
into the Venmo balance never shows up on a bank statement at all, so
only rows whose Funding Source or Destination reference the bank
account are eligible to match. A payment funded directly from the bank
keeps the same sign on both sides; a "Standard Transfer" (a cash out
from Venmo balance to the bank) is a debit in Venmo but shows up as a
credit on the bank side, so its amount is sign-flipped before matching.

As with Amazon orders, the bank transaction date doesn't always match
the Venmo transaction's date (it's often a day or two later), so
matches are allowed to be up to `max_days_after` days after the Venmo
transaction. Each Venmo transaction can only be matched once.
'''


def match_venmo_transactions(transactions, venmo_transactions, max_days_after=5):

    unmatched_venmo_transactions = list(venmo_transactions)

    for transaction in transactions:
        desc = transaction.get('Description', '')

        if 'VENMO' not in desc.upper():
            continue

        amount = transaction.get('Amount')

        if amount is None:
            continue

        transaction_date = datetime.strptime(transaction['Date'], '%m/%d/%Y')

        best_match = None
        best_day_diff = None

        for venmo_transaction in unmatched_venmo_transactions:

            funding_source = venmo_transaction.get('Funding Source', '')
            destination = venmo_transaction.get('Destination', '')

            if 'BANK OF AMERICA' in funding_source:
                expected_amount = venmo_transaction['Amount']
            elif 'BANK OF AMERICA' in destination:
                expected_amount = -1 * venmo_transaction['Amount']
            else:
                # Funded by / settled into the Venmo balance -- no bank
                # transaction exists for this one.
                continue

            if abs(expected_amount - amount) > 0.01:
                continue

            venmo_date = datetime.strptime(venmo_transaction['Date'], '%m/%d/%Y')
            day_diff = (transaction_date - venmo_date).days

            if not (0 <= day_diff <= max_days_after):
                continue

            if best_day_diff is None or day_diff < best_day_diff:
                best_match = venmo_transaction
                best_day_diff = day_diff

        if best_match is None:
            continue

        unmatched_venmo_transactions.remove(best_match)
        transaction['Description'] = f"VENMO: {best_match['Description']}"

    return transactions


'''
Matches a refund/credit transaction against the original purchase it
refunded, and attaches it to that purchase as its 'Refund' entry
instead of leaving it as its own, separately-dated transaction.

USAA and BOA statements flag a credit/return by appending "CREDIT" to
the end of the merchant's description (e.g. "UNIQLO BRYANT PARK NEW
YORK  NY   CREDIT"). That trailing marker is what identifies a refund
candidate -- checking for the word "CREDIT" anywhere in the description
would also catch unrelated things like "USAA CREDIT CARD PAYMENT...".

The matching purchase is found by amount sign (negative) and by the
refund's merchant name (the description with "CREDIT" stripped off)
appearing in the purchase's description, within `max_days_after` days
of the purchase -- returns can take a while to process, so this window
is wider than the Amazon/Venmo billing-cycle one. Each purchase can
only have one refund attached, and a matched refund is removed from
the main list; main.py renders it directly under its purchase,
ignoring the refund's own date entirely.
'''


def match_refunds(transactions, max_days_after=30):

    claimed_purchase_indices = set()
    refund_indices = set()

    for refund_index, transaction in enumerate(transactions):
        desc = transaction.get('Description', '')
        amount = transaction.get('Amount')

        if amount is None or amount <= 0:
            continue

        if not desc.strip().upper().endswith('CREDIT'):
            continue

        merchant_name = desc.strip()[:-len('CREDIT')].strip()

        if not merchant_name:
            continue

        refund_date = datetime.strptime(transaction['Date'], '%m/%d/%Y')

        best_index = None
        best_day_diff = None

        for purchase_index, purchase in enumerate(transactions):

            if purchase_index == refund_index or purchase_index in claimed_purchase_indices:
                continue

            purchase_amount = purchase.get('Amount')
            purchase_desc = purchase.get('Description', '')

            if purchase_amount is None or purchase_amount >= 0:
                continue

            if merchant_name not in purchase_desc:
                continue

            purchase_date = datetime.strptime(purchase['Date'], '%m/%d/%Y')
            day_diff = (refund_date - purchase_date).days

            if not (0 <= day_diff <= max_days_after):
                continue

            if best_day_diff is None or day_diff < best_day_diff:
                best_index = purchase_index
                best_day_diff = day_diff

        if best_index is None:
            continue

        claimed_purchase_indices.add(best_index)
        refund_indices.add(refund_index)

        transactions[best_index]['Refund'] = {
            'Description': f"Refund: {merchant_name}",
            'Amount': amount,
        }

    return [transaction for index, transaction in enumerate(transactions) if index not in refund_indices]
