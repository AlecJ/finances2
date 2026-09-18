from parsers.venmo import parse_venmo

VENMO_CSV = """Account Statement - (@Alec-Jordan) ,,,,,,,,,,,,,,,,,,,,,
Account Activity,,,,,,,,,,,,,,,,,,,,,
,ID,Datetime,Type,Status,Note,From,To,Amount (total),Amount (tip),Amount (tax),Amount (fee),Tax Rate,Tax Exempt,Funding Source,Destination,Beginning Balance,Ending Balance,Statement Period Venmo Fees,Terminal Location,Year to Date Venmo Fees,Disclaimer
,,,,,,,,,,,,,,,,$0.00,,,,,
,4653948258452179389,2026-08-01T05:24:25,Payment,Complete,Empower,Alec Jordan,Christopher Timmons,- $9.87,,0,,0,,"BANK OF AMERICA, N.A. Personal Checking *8628",,,,,Venmo,,
,5HY6837124040981W,2026-08-05T01:41:07,Payment,Complete,Barou cut off an Isagi monologue!!!,Gregory Pepe,Alec Jordan,+ $1.00,,0,,0,,,Venmo balance,,,,Venmo,,
,4662979632660681226,2026-08-13T16:28:09,Standard Transfer,Issued,,,,"- $1,001.00",,,,,,,"BANK OF AMERICA, N.A. *8628",,,,Venmo,,
,,,,,,,,,,,,,,,,,$0.00,$0.00,,$0.00,"In case of errors..."
"""


def write_csv(tmp_path, content):
    file_path = tmp_path / "VenmoStatement_August_2026.csv"
    file_path.write_text(content, encoding='utf-8')
    return str(file_path)


def test_parses_a_bank_funded_payment(tmp_path):
    file_path = write_csv(tmp_path, VENMO_CSV)

    result = parse_venmo(file_path)

    payment = result[0]
    assert payment['Date'] == '08/01/2026'
    assert payment['Description'] == 'Empower'
    assert payment['Amount'] == -9.87
    assert payment['Type'] == 'Payment'
    assert payment['Funding Source'] == 'BANK OF AMERICA, N.A. Personal Checking *8628'
    assert payment['Destination'] == ''
    assert payment['Account Type'] == 'venmo'


def test_parses_amounts_with_thousands_separator_and_plus_sign(tmp_path):
    file_path = write_csv(tmp_path, VENMO_CSV)

    result = parse_venmo(file_path)

    assert result[1]['Amount'] == 1.00


def test_falls_back_to_type_when_note_is_blank(tmp_path):
    file_path = write_csv(tmp_path, VENMO_CSV)

    result = parse_venmo(file_path)

    transfer = result[2]
    assert transfer['Description'] == 'Standard Transfer'
    assert transfer['Amount'] == -1001.00
    assert transfer['Destination'] == 'BANK OF AMERICA, N.A. *8628'


def test_ignores_the_disclaimer_block(tmp_path):
    file_path = write_csv(tmp_path, VENMO_CSV)

    result = parse_venmo(file_path)

    assert len(result) == 3
