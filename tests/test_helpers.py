from datetime import datetime

import pytest

from helpers import get_account_type, get_usaa_statement_closing_date, convert_common_transactions, process_account_transfers, match_amazon_orders, match_venmo_transactions, match_refunds


@pytest.mark.parametrize("file_name,expected_type", [
    ("eStmt_2026-08-10.pdf", "boa"),
    ("20260810_BANK_STATEMENT.pdf", "usaa"),
    ("2026-08-11_AMERICAN_EXPRESS_374355_6480_AUG_2026_STATEMENT.pdf", "usaa"),
    ("amazon-9-17-26.html", "amazon"),
    ("VenmoStatement_August_2026.csv", "venmo"),
    ("some_random_file.pdf", None),
    ("amazon-9-17-26_files", None),
])
def test_get_account_type(file_name, expected_type):
    assert get_account_type(file_name) == expected_type


@pytest.mark.parametrize("file_name,expected_date", [
    ("20260810_BANK_STATEMENT.pdf", datetime(2026, 8, 10)),
    ("2026-08-11_AMERICAN_EXPRESS_374355_6480_AUG_2026_STATEMENT.pdf", datetime(2026, 8, 11)),
    ("eStmt_2026-08-10.pdf", None),
    ("some_random_file.pdf", None),
])
def test_get_usaa_statement_closing_date(file_name, expected_date):
    assert get_usaa_statement_closing_date(file_name) == expected_date


def test_convert_common_transactions_replaces_matching_description(tmp_path, monkeypatch):
    project_root = tmp_path
    src_dir = project_root / "src"
    src_dir.mkdir()
    (project_root / "common_transactions.csv").write_text(
        "substring_match,cleaned_description,category\n"
        "LINCOLN MARKET,Lincoln Market,grocery\n",
        encoding='utf-8',
    )
    monkeypatch.chdir(src_dir)

    transactions = [
        {'Date': '07/30', 'Description': 'LINCOLN MARKET 12345', 'Amount': -10.07},
        {'Date': '07/31', 'Description': 'Some Other Store', 'Amount': -5.00},
    ]

    result = convert_common_transactions(transactions)

    assert result[0]['Description'] == 'Lincoln Market'
    assert result[0]['Category'] == 'grocery'
    assert result[1]['Description'] == 'Some Other Store'
    assert 'Category' not in result[1]


def test_convert_common_transactions_raises_when_csv_missing(tmp_path, monkeypatch):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    monkeypatch.chdir(src_dir)

    with pytest.raises(FileNotFoundError):
        convert_common_transactions([])


def test_boac_to_boas_transfer_becomes_a_single_transfer_row():
    transactions = [
        {'Date': '07/13', 'Description': 'BOA KeepTheChange', 'Amount': -0.51, 'Account Type': 'boac'},
    ]

    result = process_account_transfers(transactions)

    assert result == [{
        'Date': '07/13',
        'Account Type': 'boac',
        'Account Transfer To': 'boas',
        'Transfer Amount': -0.51,
    }]


def test_boas_to_boac_transfer_becomes_a_single_transfer_row():
    transactions = [
        {'Date': '07/13', 'Description': 'Online Banking transfer from SAV 2908', 'Amount': 0.51, 'Account Type': 'boac'},
        {'Date': '07/13', 'Description': 'Online Banking transfer to CHK 8628', 'Amount': -0.51, 'Account Type': 'boas'},
    ]

    result = process_account_transfers(transactions)

    assert len(result) == 1
    assert result[0]['Account Type'] == 'boas'
    assert result[0]['Account Transfer To'] == 'boac'
    assert result[0]['Transfer Amount'] == 0.51


def test_boac_to_usaa_card_payoff_is_not_double_counted():
    # Regression test: the payment shows up on both statements -- once as
    # a credit on the USAA/card statement, once as a debit on the BOA
    # statement -- and only one transfer row should be produced.
    transactions = [
        {
            'Date': '07/31',
            'Description': 'USAA FSB CC      DES:CC PAYMENT ID:983967376282801  INDN:Alec Jordan             COID:9USAAFSBCC WEB',
            'Amount': -1240.0,
            'Account Type': 'boac',
        },
        {
            'Date': '07/29',
            'Description': 'USAA CREDIT CARD PAYMENT SAN ANTONIO  TX',
            'Amount': 1240.0,
            'Account Type': 'usaa',
        },
    ]

    result = process_account_transfers(transactions)

    assert len(result) == 1
    assert result[0]['Account Type'] == 'boac'
    assert result[0]['Account Transfer To'] == 'usaa'
    assert result[0]['Transfer Amount'] == 1240.0


def test_always_delete_drops_transaction_entirely():
    transactions = [
        {'Date': '07/13', 'Description': 'KEEP THE CHANGE TRANSFER TO ACCT 2908', 'Amount': -0.51, 'Account Type': 'boas'},
    ]

    result = process_account_transfers(transactions)

    assert result == []


def test_unrelated_transaction_passes_through_unchanged():
    transaction = {'Date': '07/22', 'Description': "Trader Joe's", 'Amount': -43.26, 'Account Type': 'usaa'}

    result = process_account_transfers([transaction])

    assert result == [transaction]


def test_amazon_order_matches_a_transaction_a_few_days_later():
    # Amazon charges the card a day or two after the order is placed, so
    # matching needs date wiggle room rather than an exact-day match.
    transactions = [
        {'Date': '08/01/2026', 'Description': 'AMAZON.COM*5N4543IH1 AMZN.COM/BILL WA', 'Amount': -15.72, 'Account Type': 'usaa'},
    ]
    amazon_orders = [
        {'Date': '07/31/2026', 'Amount': -15.72, 'Items': ['CeraVe Eye Repair Cream'], 'Order Number': '114-3453595-6566658'},
    ]

    result = match_amazon_orders(transactions, amazon_orders)

    assert result[0]['Description'] == 'Amazon: CeraVe Eye Repair Cream'


def test_amazon_order_description_is_truncated_when_too_long():
    long_item_name = 'A' * 100
    transactions = [
        {'Date': '08/01/2026', 'Description': 'AMAZON.COM*ABC123', 'Amount': -9.99, 'Account Type': 'usaa'},
    ]
    amazon_orders = [
        {'Date': '08/01/2026', 'Amount': -9.99, 'Items': [long_item_name], 'Order Number': '111'},
    ]

    result = match_amazon_orders(transactions, amazon_orders, max_description_length=20)

    assert result[0]['Description'] == f"Amazon: {'A' * 17}..."


def test_amazon_order_is_not_matched_if_amount_differs():
    transactions = [
        {'Date': '08/01/2026', 'Description': 'AMAZON.COM*ABC123', 'Amount': -9.99, 'Account Type': 'usaa'},
    ]
    amazon_orders = [
        {'Date': '08/01/2026', 'Amount': -5.00, 'Items': ['Unrelated Item'], 'Order Number': '111'},
    ]

    result = match_amazon_orders(transactions, amazon_orders)

    assert result[0]['Description'] == 'AMAZON.COM*ABC123'


def test_amazon_order_is_not_matched_if_too_far_in_the_future():
    transactions = [
        {'Date': '08/10/2026', 'Description': 'AMAZON.COM*ABC123', 'Amount': -9.99, 'Account Type': 'usaa'},
    ]
    amazon_orders = [
        {'Date': '08/01/2026', 'Amount': -9.99, 'Items': ['Old Order'], 'Order Number': '111'},
    ]

    result = match_amazon_orders(transactions, amazon_orders, max_days_after=5)

    assert result[0]['Description'] == 'AMAZON.COM*ABC123'


def test_each_amazon_order_is_only_matched_once():
    transactions = [
        {'Date': '08/01/2026', 'Description': 'AMAZON.COM*ABC123', 'Amount': -9.99, 'Account Type': 'usaa'},
        {'Date': '08/02/2026', 'Description': 'AMAZON.COM*DEF456', 'Amount': -9.99, 'Account Type': 'usaa'},
    ]
    amazon_orders = [
        {'Date': '08/01/2026', 'Amount': -9.99, 'Items': ['Only Order'], 'Order Number': '111'},
    ]

    result = match_amazon_orders(transactions, amazon_orders)

    matched = [t for t in result if t['Description'].startswith('Amazon:')]
    assert len(matched) == 1


def test_non_amazon_transaction_is_left_unchanged():
    transaction = {'Date': '08/01/2026', 'Description': "Trader Joe's", 'Amount': -43.26, 'Account Type': 'usaa'}

    result = match_amazon_orders([transaction], [])

    assert result == [transaction]


def test_bank_funded_venmo_payment_matches_with_same_sign():
    transactions = [
        {'Date': '08/03/2026', 'Description': 'VENMO            DES:PAYMENT    ID:1052061175011  INDN:ALEC JORDAN             COID:3264681992 WEB', 'Amount': -9.87, 'Account Type': 'boac'},
    ]
    venmo_transactions = [
        {'Date': '08/01/2026', 'Description': 'Empower', 'Amount': -9.87, 'Type': 'Payment',
         'Funding Source': 'BANK OF AMERICA, N.A. Personal Checking *8628', 'Destination': ''},
    ]

    result = match_venmo_transactions(transactions, venmo_transactions)

    assert result[0]['Description'] == 'VENMO: Empower'


def test_standard_transfer_cashout_matches_with_flipped_sign():
    # A Standard Transfer is a debit from the Venmo balance (negative)
    # but shows up as a deposit (positive) on the bank statement.
    transactions = [
        {'Date': '08/15/2026', 'Description': 'VENMO DES:CASHOUT ID:1051958063199', 'Amount': 1001.00, 'Account Type': 'boac'},
    ]
    venmo_transactions = [
        {'Date': '08/13/2026', 'Description': 'Standard Transfer', 'Amount': -1001.00, 'Type': 'Standard Transfer',
         'Funding Source': '', 'Destination': 'BANK OF AMERICA, N.A. *8628'},
    ]

    result = match_venmo_transactions(transactions, venmo_transactions)

    assert result[0]['Description'] == 'VENMO: Standard Transfer'


def test_venmo_balance_only_transaction_is_never_matched():
    # No Funding Source or Destination references the bank, so there's
    # no corresponding bank transaction -- it should never be picked,
    # even if the amount happens to line up.
    transactions = [
        {'Date': '08/05/2026', 'Description': 'VENMO DES:PAYMENT ID:999', 'Amount': -1.00, 'Account Type': 'boac'},
    ]
    venmo_transactions = [
        {'Date': '08/05/2026', 'Description': 'Some other purchase', 'Amount': -1.00, 'Type': 'Payment',
         'Funding Source': '', 'Destination': ''},
    ]

    result = match_venmo_transactions(transactions, venmo_transactions)

    assert result[0]['Description'] == 'VENMO DES:PAYMENT ID:999'


def test_non_venmo_transaction_is_left_unchanged():
    transaction = {'Date': '08/01/2026', 'Description': "Trader Joe's", 'Amount': -43.26, 'Account Type': 'usaa'}

    result = match_venmo_transactions([transaction], [])

    assert result == [transaction]


def test_refund_is_attached_to_its_purchase_and_removed_from_the_list():
    transactions = [
        {'Date': '08/30/2026', 'Description': 'UNIQLO BRYANT PARK NEW YORK  NY', 'Amount': -206.51, 'Account Type': 'usaa'},
        {'Date': '09/01/2026', 'Description': 'UNIQLO BRYANT PARK NEW YORK  NY   CREDIT', 'Amount': 47.48, 'Account Type': 'usaa'},
    ]

    result = match_refunds(transactions)

    assert len(result) == 1
    assert result[0]['Description'] == 'UNIQLO BRYANT PARK NEW YORK  NY'
    assert result[0]['Refund'] == {
        'Description': 'Refund: UNIQLO BRYANT PARK NEW YORK  NY',
        'Amount': 47.48,
    }


def test_refund_matches_by_leading_substring_despite_trailing_noise():
    # The purchase's raw description often has extra trailing digits/city
    # text the credit line doesn't repeat.
    transactions = [
        {'Date': '08/17/2026', 'Description': 'PAYPAL *NATIONALRAI      8008727245   DC', 'Amount': -82.0, 'Account Type': 'usaa'},
        {'Date': '08/18/2026', 'Description': 'PAYPAL *NATIONALRAI      80087272 CREDIT', 'Amount': 28.0, 'Account Type': 'usaa'},
    ]

    result = match_refunds(transactions)

    assert len(result) == 1
    assert result[0]['Refund']['Amount'] == 28.0


def test_credit_card_payment_is_not_treated_as_a_refund():
    # "CREDIT" appears mid-description here (CREDIT CARD), not as the
    # trailing marker USAA/BOA use to flag an actual refund.
    transactions = [
        {'Date': '08/29/2026', 'Description': 'USAA CREDIT CARD PAYMENT SAN ANTONIO  TX', 'Amount': 4000.0, 'Account Type': 'usaa'},
    ]

    result = match_refunds(transactions)

    assert result == transactions
    assert 'Refund' not in result[0]


def test_refund_with_no_matching_purchase_is_left_as_its_own_transaction():
    transactions = [
        {'Date': '08/18/2026', 'Description': 'PAYPAL *NATIONALRAI      80087272 CREDIT', 'Amount': 28.0, 'Account Type': 'usaa'},
    ]

    result = match_refunds(transactions)

    assert result == transactions


def test_refund_outside_the_day_window_is_not_matched():
    transactions = [
        {'Date': '01/01/2026', 'Description': 'UNIQLO BRYANT PARK NEW YORK  NY', 'Amount': -206.51, 'Account Type': 'usaa'},
        {'Date': '09/01/2026', 'Description': 'UNIQLO BRYANT PARK NEW YORK  NY   CREDIT', 'Amount': 47.48, 'Account Type': 'usaa'},
    ]

    result = match_refunds(transactions, max_days_after=30)

    assert len(result) == 2
    assert 'Refund' not in result[0]


def test_each_purchase_gets_at_most_one_refund():
    transactions = [
        {'Date': '08/30/2026', 'Description': 'UNIQLO BRYANT PARK NEW YORK  NY', 'Amount': -206.51, 'Account Type': 'usaa'},
        {'Date': '09/01/2026', 'Description': 'UNIQLO BRYANT PARK NEW YORK  NY   CREDIT', 'Amount': 47.48, 'Account Type': 'usaa'},
        {'Date': '09/02/2026', 'Description': 'UNIQLO BRYANT PARK NEW YORK  NY   CREDIT', 'Amount': 30.00, 'Account Type': 'usaa'},
    ]

    result = match_refunds(transactions)

    assert len(result) == 2
    assert result[0]['Refund']['Amount'] == 47.48
