import re
import csv

'''
This helper function uses regex to matche file names to
a bank type, which dictates which parser to use.
'''

match_file_name_to_account_type = [
    {"expression": "eStmt_\d{4}-\d{2}-\d{2}.pdf", "type": "boa"},
    {"expression": "\d{8}_BANK.pdf", "type": "usaa"}
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
    common_transactions = []

    # if the common_transactions json file is not present, raise an error
    try:
        with open(common_transactions_file_path, 'r') as file:
            # Create a CSV reader object
            csv_reader = csv.DictReader(file)

            # Iterate through the rows and load them into the list as dictionaries
            for row in csv_reader:
                # Each row is already a dictionary, so you can append it directly
                common_transactions.append(row)
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
