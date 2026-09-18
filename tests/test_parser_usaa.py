from datetime import datetime

from conftest import FakeReader

from parsers.usaa import parse_usaa

CLOSING_DATE = datetime(2026, 8, 10)


def test_parses_a_purchase_as_negative_amount():
    reader = FakeReader(["\n".join([
        "07/09",
        "07/09",
        "REF12345",
        "Parkside Deli",
        "$3.63",
    ])])

    result = parse_usaa(reader, CLOSING_DATE)

    assert result == [{
        'Date': '07/09/2026',
        'Description': 'Parkside Deli',
        'Amount': -3.63,
        'Account Type': 'usaa',
    }]


def test_parses_a_credit_with_trailing_minus_as_positive_amount():
    # USAA statements format credits (e.g. payments received) with a
    # trailing "-" instead of a leading one.
    reader = FakeReader(["\n".join([
        "07/29",
        "07/29",
        "P634005XGEH011JXG",
        "USAA CREDIT CARD PAYMENT SAN ANTONIO  TX",
        "$1,240.00-",
    ])])

    result = parse_usaa(reader, CLOSING_DATE)

    assert result == [{
        'Date': '07/29/2026',
        'Description': 'USAA CREDIT CARD PAYMENT SAN ANTONIO  TX',
        'Amount': 1240.00,
        'Account Type': 'usaa',
    }]


def test_parses_entries_without_a_reference_number_line():
    # Interest/fee line items only have 4 lines (no reference number),
    # so the description must be read relative to the amount line, not
    # a hardcoded index.
    reader = FakeReader(["\n".join([
        "08/10",
        "08/10",
        "Interest Charge on Purchases",
        "$94.09",
    ])])

    result = parse_usaa(reader, CLOSING_DATE)

    assert result == [{
        'Date': '08/10/2026',
        'Description': 'Interest Charge on Purchases',
        'Amount': -94.09,
        'Account Type': 'usaa',
    }]


def test_parses_multiple_transactions_on_one_page():
    reader = FakeReader(["\n".join([
        "07/09",
        "07/09",
        "REF1",
        "Parkside Deli",
        "$3.63",
        "07/10",
        "07/10",
        "REF2",
        "NYC OMNY",
        "$3.00",
    ])])

    result = parse_usaa(reader, CLOSING_DATE)

    assert [t['Description'] for t in result] == ['Parkside Deli', 'NYC OMNY']
    assert [t['Amount'] for t in result] == [-3.63, -3.00]


def test_resolves_year_across_a_year_boundary():
    # A statement closing in January can cover a period that started in
    # December of the previous year -- a transaction dated later in the
    # year than the closing date must belong to the year before it.
    closing_date = datetime(2027, 1, 10)
    reader = FakeReader(["\n".join([
        "12/28",
        "12/28",
        "REF1",
        "Holiday Shopping",
        "$50.00",
        "01/05",
        "01/05",
        "REF2",
        "New Year Purchase",
        "$10.00",
    ])])

    result = parse_usaa(reader, closing_date)

    assert result[0]['Date'] == '12/28/2026'
    assert result[1]['Date'] == '01/05/2027'
