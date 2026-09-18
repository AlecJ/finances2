from parsers.amazon import parse_amazon

AMAZON_ORDERS_HTML = """
<html><body>
<div data-csa-c-content-id="amzn1.yourorders.order-card">
    <div class="order-header">
        <span>Order placed</span>
        <span>January 5, 2026</span>
        <span>Total</span>
        <span>$29.99</span>
        <div class="yohtmlc-order-id">
            <span>Order #</span>
            <span>111-2222222-3333333</span>
        </div>
    </div>
    <div class="yohtmlc-product-title">
        <a href="#">Widget Thing</a>
    </div>
</div>

<div data-csa-c-content-id="amzn1.yourorders.order-card">
    <div class="order-header">
        <span>Order placed</span>
        <span>February 10, 2026</span>
        <span>Total</span>
        <span>$1,045.67</span>
        <div class="yohtmlc-order-id">
            <span>Order #</span>
            <span>444-5555555-6666666</span>
        </div>
    </div>
    <div class="yohtmlc-product-title">
        <a href="#">Item One</a>
    </div>
    <div class="yohtmlc-product-title">
        <a href="#">Item Two</a>
    </div>
</div>
</body></html>
"""


def write_html(tmp_path, content):
    file_path = tmp_path / "amazon-1-1-26.html"
    file_path.write_text(content, encoding='utf-8')
    return str(file_path)


def test_parses_single_item_order(tmp_path):
    file_path = write_html(tmp_path, AMAZON_ORDERS_HTML)

    result = parse_amazon(file_path)

    single_item_order = result[0]
    assert single_item_order['Date'] == '01/05/2026'
    assert single_item_order['Amount'] == -29.99
    assert single_item_order['Items'] == ['Widget Thing']
    assert single_item_order['Description'] == 'Widget Thing'
    assert single_item_order['Order Number'] == '111-2222222-3333333'
    assert single_item_order['Account Type'] == 'amazon'


def test_parses_multi_item_order_total_and_all_item_names(tmp_path):
    file_path = write_html(tmp_path, AMAZON_ORDERS_HTML)

    result = parse_amazon(file_path)

    multi_item_order = result[1]
    assert multi_item_order['Date'] == '02/10/2026'
    assert multi_item_order['Amount'] == -1045.67
    assert multi_item_order['Items'] == ['Item One', 'Item Two']
    assert multi_item_order['Description'] == 'Item One, Item Two'


def test_ignores_cards_missing_a_header(tmp_path):
    html = """
    <div data-csa-c-content-id="amzn1.yourorders.order-card">
        <div class="yohtmlc-product-title"><a>Orphan Item</a></div>
    </div>
    """
    file_path = write_html(tmp_path, html)

    result = parse_amazon(file_path)

    assert result == []
