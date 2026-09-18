'''
Parses an Amazon "Your Orders" page saved as a webpage (.html) and
returns a list of orders.

Amazon's order history page only shows a Total per order, not a price
per item, so each order is returned as a single record with all of its
item names and the order's total price. These are matched later against
the generic "AMAZON.COM" transactions pulled from USAA statements, using
the order Date/Amount to give those transactions more detail.

Input:
- file_path: path to the saved Amazon order history .html file.

Returns:
A list of orders with the following format:
{
    "Date": date as string ("MM/DD/YYYY"),
    "Description": string (item names joined with ", "),
    "Amount": float,
    "Items": list of item name strings,
    "Order Number": string,
    "Account Type": string
}
'''

import re

from datetime import datetime

from bs4 import BeautifulSoup


def parse_amazon(file_path):

    result = []

    with open(file_path, encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    order_cards = soup.find_all(
        'div', attrs={'data-csa-c-content-id': 'amzn1.yourorders.order-card'})

    for card in order_cards:

        header = card.find('div', class_='order-header')

        if not header:
            continue

        header_text = header.get_text('|', strip=True)

        date_match = re.search(r'Order placed\|([^|]+)', header_text)
        total_match = re.search(r'Total\|\$([\d,]+\.\d{2})', header_text)

        if not date_match or not total_match:
            continue

        date = datetime.strptime(
            date_match.group(1), '%B %d, %Y').strftime('%m/%d/%Y')

        amount = -1 * float(total_match.group(1).replace(',', ''))

        order_id_element = header.find('div', class_='yohtmlc-order-id')
        order_number = order_id_element.get_text(
            strip=True).removeprefix('Order #') if order_id_element else ''

        items = [title.get_text(strip=True) for title in card.find_all(
            'div', class_='yohtmlc-product-title')]

        result.append({
            'Date': date,
            'Description': ', '.join(items),
            'Amount': amount,
            'Items': items,
            'Order Number': order_number,
            'Account Type': 'amazon'
        })

    return result
