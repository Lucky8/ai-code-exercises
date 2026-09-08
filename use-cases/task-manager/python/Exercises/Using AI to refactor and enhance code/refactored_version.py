def validate_order(order, inventory, customer_data):
    item_id = order['item_id']
    quantity = order['quantity']
    customer_id = order['customer_id']

    if item_id not in inventory:
        return 'Item not in inventory'

    if inventory[item_id]['quantity'] < quantity:
        return 'Insufficient quantity'

    if customer_id not in customer_data:
        return 'Customer not found'

    return None


def calculate_price(order, inventory, customer_data):
    item_id = order['item_id']
    quantity = order['quantity']
    customer_id = order['customer_id']

    price = inventory[item_id]['price'] * quantity

    if customer_data[customer_id]['premium']:
        price *= 0.9

    return price


def calculate_shipping(price, customer):
    if customer['location'] == 'domestic':
        return 5.99 if price < 50 else 0

    return 15.99


def calculate_tax(price):
    return price * 0.08


def update_inventory(order, inventory):
    item_id = order['item_id']
    quantity = order['quantity']

    inventory[item_id]['quantity'] -= quantity


def build_order_result(order, price, shipping, tax):
    final_price = price + shipping + tax

    return {
        'order_id': order['order_id'],
        'item_id': order['item_id'],
        'quantity': order['quantity'],
        'customer_id': order['customer_id'],
        'price': price,
        'shipping': shipping,
        'tax': tax,
        'final_price': final_price
    }


def process_single_order(order, inventory, customer_data):
    error = validate_order(order, inventory, customer_data)

    if error:
        return None, {
            'order_id': order['order_id'],
            'error': error
        }

    customer = customer_data[order['customer_id']]

    price = calculate_price(order, inventory, customer_data)
    shipping = calculate_shipping(price, customer)
    tax = calculate_tax(price)

    update_inventory(order, inventory)

    result = build_order_result(
        order,
        price,
        shipping,
        tax
    )

    return result, None


def process_orders(orders, inventory, customer_data):
    results = []
    error_orders = []
    total_revenue = 0

    for order in orders:
        result, error = process_single_order(
            order,
            inventory,
            customer_data
        )

        if error:
            error_orders.append(error)
            continue

        results.append(result)
        total_revenue += result['final_price']

    return {
        'processed_orders': results,
        'error_orders': error_orders,
        'total_revenue': total_revenue
    }