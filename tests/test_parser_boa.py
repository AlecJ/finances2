from conftest import FakeReader

from parsers.boa import parse_boa


def test_parses_single_line_transaction():
    reader = FakeReader(["07/15/26COFFEE SHOP PURCHASE-4.50"])

    result = parse_boa(reader)

    assert result == [{
        'Date': '07/15/2026',
        'Description': 'COFFEE SHOP PURCHASE',
        'Amount': -4.50,
        'Account Type': 'boac',
    }]


def test_parses_the_last_line_of_a_page():
    # Regression test: parse_boa used to pair each line with the one
    # after it (zip(lines, lines[1:])), which meant a page's very last
    # line was never checked as a transaction on its own.
    reader = FakeReader(["\n".join([
        "07/15/26COFFEE SHOP PURCHASE-4.50",
        "07/16/26LAST TRANSACTION ON PAGE-1.00",
    ])])

    result = parse_boa(reader)

    assert result[-1] == {
        'Date': '07/16/2026',
        'Description': 'LAST TRANSACTION ON PAGE',
        'Amount': -1.00,
        'Account Type': 'boac',
    }


def test_parses_incoming_deposit_as_positive_amount():
    reader = FakeReader(["07/17/26PAYROLL DEPOSIT1500.00"])

    result = parse_boa(reader)

    assert result[0]['Amount'] == 1500.00


def test_parses_transaction_split_across_two_lines():
    reader = FakeReader(["\n".join([
        "07/16/26GROCERY STORE",
        "PURCHASE-32.10",
    ])])

    result = parse_boa(reader)

    assert result == [{
        'Date': '07/16/2026',
        'Description': 'GROCERY STOREPURCHASE',
        'Amount': -32.10,
        'Account Type': 'boac',
    }]


def test_handles_amounts_with_thousands_separator():
    reader = FakeReader(["07/31/26USAA FSB CC DES:CC PAYMENT-1,240.00"])

    result = parse_boa(reader)

    assert result[0]['Amount'] == -1240.00


def test_ignores_lines_without_a_transaction():
    reader = FakeReader(["\n".join([
        "Statement Period 07/01/26 - 07/31/26",
        "Some other text",
    ])])

    result = parse_boa(reader)

    assert result == []
