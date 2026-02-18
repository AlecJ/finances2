import re
import csv

'''
This helper function uses regex to matche file names to
a bank type, which dictates which parser to use.
'''

match_file_name_to_account_type = [
    {"expression": "eStmt_\d{4}-\d{2}-\d{2}.pdf", "type": "boa"},
    {"expression": "\d{8}_BANK.*\.pdf", "type": "usaa"},
    {"expression": "\d{4}-\d{2}-\d{2}_AMERICAN_EXPRESS_.*_STATEMENT.*\.pdf", "type": "usaa"},
]


def get_account_type(file_name):
    for pattern in match_file_name_to_account_type:
        if re.fullmatch(pattern["expression"], file_name):
            return pattern["type"]
    return None  # Return None if no match is found


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
    except:
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
                     "USAA CREDIT CARD DES:PAYMENT",]

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
