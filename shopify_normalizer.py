import pandas as pd


def normalize_shopify_orders(raw_orders):
    """
    Convert Shopify REST API orders JSON
    into a clean DataFrame that MetricsCalculator understands.
    """

    rows = []

    for order in raw_orders:

        # Get basic order info
        total_price = float(order.get("total_price", 0))
        created_at = order.get("created_at", "")
        order_name = order.get("name", "")
        currency = order.get("currency", "INR")
        financial_status = order.get("financial_status", "")

        # Calculate total refund for this order
        refund_total = 0
        refunds = order.get("refunds", [])
        for refund in refunds:
            for item in refund.get("refund_line_items", []):
                refund_total += float(item.get("subtotal", 0))

        # Get shipping city
        shipping_address = order.get("shipping_address")
        if shipping_address and isinstance(shipping_address, dict):
            shipping_city = shipping_address.get("city", "Unknown")
        else:
            shipping_city = "Unknown"

        # Get payment method
        payment_methods = order.get("payment_gateway_names", [])
        if payment_methods:
            payment_method = payment_methods[0]
        else:
            payment_method = "Unknown"

        # Get shipping cost
        shipping_lines = order.get("shipping_lines", [])
        shipping_cost = 0
        for line in shipping_lines:
            shipping_cost += float(line.get("price", 0))

        # Get discount
        total_discount = float(order.get("total_discounts", 0))

        # Extract each line item as a row
        line_items = order.get("line_items", [])

        if line_items:
            for item in line_items:
                rows.append({
                    "Name": order_name,
                    "Created at": created_at,
                    "Total": total_price,
                    "Refund": refund_total,
                    "Lineitem name": item.get("title", "Unknown Product"),
                    "Lineitem quantity": int(item.get("quantity", 1)),
                    "Lineitem price": float(item.get("price", 0)),
                    "Shipping City": shipping_city,
                    "Payment Method": payment_method,
                    "Shipping": shipping_cost,
                    "Discount Amount": total_discount,
                    "Financial Status": financial_status,
                    "Currency": currency
                })
        else:
            # Order with no line items
            rows.append({
                "Name": order_name,
                "Created at": created_at,
                "Total": total_price,
                "Refund": refund_total,
                "Lineitem name": "Unknown Product",
                "Lineitem quantity": 1,
                "Lineitem price": total_price,
                "Shipping City": shipping_city,
                "Payment Method": payment_method,
                "Shipping": shipping_cost,
                "Discount Amount": total_discount,
                "Financial Status": financial_status,
                "Currency": currency
            })

    df = pd.DataFrame(rows)

    # Clean numeric columns
    numeric_cols = ["Total", "Refund", "Lineitem price",
                    "Lineitem quantity", "Shipping", "Discount Amount"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


# Test the normalizer
if __name__ == "__main__":
    from shopify_connector import fetch_orders
    import json

    print("Fetching orders from Shopify...")
    orders = fetch_orders(limit=10)

    if orders:
        print(f"Raw orders: {len(orders)}")

        df = normalize_shopify_orders(orders)

        print(f"\nNormalized DataFrame:")
        print(f"Rows: {len(df)}")
        print(f"Columns: {list(df.columns)}")
        print(f"\nSample data:")
        print(df.head())
        print(f"\nTotal Revenue: Rs.{df['Total'].sum():,.0f}")
        print(f"Total Refunds: Rs.{df['Refund'].sum():,.0f}")
    else:
        print("No orders found.")