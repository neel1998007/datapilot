import pandas as pd
from datetime import datetime, timedelta


class MetricsCalculator:
    """
    The brain of DataPilot.
    Takes raw Shopify order data and calculates 
    everything a D2C founder needs to know.
    """

    def __init__(self, df, ad_spend=0, cogs_percent=0, 
                 avg_shipping=0, payment_fee_percent=2, 
                 meta_percent=70):
        """
        Initialize with order dataframe and cost inputs.
        
        df: pandas DataFrame of Shopify orders
        ad_spend: total ad spend for the period
        cogs_percent: cost of goods as percentage
        avg_shipping: average shipping cost per order
        payment_fee_percent: payment gateway fee percentage
        meta_percent: percentage of ad spend on Meta
        """
        self.df = df.copy()
        self.ad_spend = ad_spend
        self.cogs_percent = cogs_percent
        self.avg_shipping = avg_shipping
        self.payment_fee_percent = payment_fee_percent
        self.meta_percent = meta_percent
        self.google_percent = 100 - meta_percent

        # Clean the data first
        self._clean_data()

    def _clean_data(self):
        """Clean and prepare the raw data"""

        # Find and standardize revenue column
        revenue_cols = ["Total", "total", "Total Price", 
                       "total_price", "Subtotal", "subtotal"]
        
        self.revenue_col = None
        for col in revenue_cols:
            if col in self.df.columns:
                self.revenue_col = col
                break

        if self.revenue_col is None:
            raise ValueError("Could not find revenue column in data")

        # Find and standardize refund column
        refund_cols = ["Refund", "refund", "Refunded Amount", 
                      "refunded_amount"]
        
        self.refund_col = None
        for col in refund_cols:
            if col in self.df.columns:
                self.refund_col = col
                break

        # Convert to numeric
        self.df[self.revenue_col] = pd.to_numeric(
            self.df[self.revenue_col], errors="coerce"
        ).fillna(0)

        if self.refund_col:
            self.df[self.refund_col] = pd.to_numeric(
                self.df[self.refund_col], errors="coerce"
            ).fillna(0)

        # Parse dates
        date_cols = ["Created at", "created_at", "Date", 
                    "Order Date", "Created At"]
        
        self.date_col = None
        for col in date_cols:
            if col in self.df.columns:
                self.date_col = col
                break

        if self.date_col:
            self.df[self.date_col] = pd.to_datetime(
                self.df[self.date_col], errors="coerce", dayfirst=True
            )
            self.df["order_date"] = self.df[self.date_col].dt.date

    def calculate_revenue_metrics(self):
        """Calculate all revenue-related metrics"""

        total_revenue = self.df[self.revenue_col].sum()

        total_refunds = 0
        if self.refund_col:
            total_refunds = self.df[self.refund_col].sum()

        net_revenue = total_revenue - total_refunds

        total_orders = len(self.df)

        refund_count = 0
        if self.refund_col:
            refund_count = len(
                self.df[self.df[self.refund_col] > 0]
            )

        refund_rate = total_refunds / total_revenue if total_revenue > 0 else 0

        aov = total_revenue / total_orders if total_orders > 0 else 0

        return {
            "total_revenue": round(total_revenue, 2),
            "total_refunds": round(total_refunds, 2),
            "net_revenue": round(net_revenue, 2),
            "total_orders": total_orders,
            "refund_count": refund_count,
            "refund_rate": round(refund_rate, 4),
            "aov": round(aov, 2)
        }

    def calculate_cost_metrics(self):
        """Calculate all cost-related metrics"""

        rev = self.calculate_revenue_metrics()
        net_revenue = rev["net_revenue"]
        total_orders = rev["total_orders"]

        cogs_amount = net_revenue * (self.cogs_percent / 100)
        shipping_total = self.avg_shipping * total_orders
        payment_fees = net_revenue * (self.payment_fee_percent / 100)
        total_costs = cogs_amount + shipping_total + payment_fees + self.ad_spend

        net_profit = net_revenue - cogs_amount - shipping_total - payment_fees

        contribution_margin = net_profit / net_revenue if net_revenue > 0 else 0

        profit_per_order = net_profit / total_orders if total_orders > 0 else 0

        cost_per_order = total_costs / total_orders if total_orders > 0 else 0

        return {
            "cogs_amount": round(cogs_amount, 2),
            "shipping_total": round(shipping_total, 2),
            "payment_fees": round(payment_fees, 2),
            "total_costs": round(total_costs, 2),
            "ad_spend": round(self.ad_spend, 2),
            "net_profit": round(net_profit, 2),
            "contribution_margin": round(contribution_margin, 4),
            "profit_per_order": round(profit_per_order, 2),
            "cost_per_order": round(cost_per_order, 2)
        }

    def calculate_scaling_metrics(self):
        """Calculate scaling-related metrics"""

        costs = self.calculate_cost_metrics()
        rev = self.calculate_revenue_metrics()

        contribution_margin = costs["contribution_margin"]

        break_even_roas = 1 / contribution_margin if contribution_margin > 0 else 0

        current_roas = rev["total_revenue"] / self.ad_spend if self.ad_spend > 0 else 0

        meta_spend = self.ad_spend * (self.meta_percent / 100)
        google_spend = self.ad_spend * (self.google_percent / 100)

        # Scaling status
        if current_roas > break_even_roas:
            scaling_status = "Safe"
        elif current_roas > break_even_roas * 0.9:
            scaling_status = "Risk"
        else:
            scaling_status = "Burn"

        # Sensitivity analysis
        roas_drop_10 = current_roas * 0.9
        can_absorb_roas_drop = roas_drop_10 > break_even_roas

        new_refund_rate = rev["refund_rate"] + 0.05
        new_net_rev = rev["total_revenue"] * (1 - new_refund_rate)
        new_cogs = new_net_rev * (self.cogs_percent / 100)
        new_payment = new_net_rev * (self.payment_fee_percent / 100)
        new_profit = new_net_rev - new_cogs - costs["shipping_total"] - new_payment
        new_margin = new_profit / new_net_rev if new_net_rev > 0 else 0
        new_be_roas = 1 / new_margin if new_margin > 0 else 0
        can_absorb_return_increase = current_roas > new_be_roas

        return {
            "break_even_roas": round(break_even_roas, 2),
            "current_roas": round(current_roas, 2),
            "scaling_status": scaling_status,
            "meta_spend": round(meta_spend, 2),
            "google_spend": round(google_spend, 2),
            "roas_after_10_drop": round(roas_drop_10, 2),
            "can_absorb_roas_drop": can_absorb_roas_drop,
            "be_roas_after_return_increase": round(new_be_roas, 2),
            "can_absorb_return_increase": can_absorb_return_increase
        }

    def calculate_product_metrics(self):
        """Calculate product-level performance"""

        product_col = None
        product_cols = ["Lineitem name", "lineitem_name", 
                       "Product", "product", "Product Title"]

        for col in product_cols:
            if col in self.df.columns:
                product_col = col
                break

        if product_col is None:
            return {"error": "No product column found"}

        quantity_col = None
        quantity_cols = ["Lineitem quantity", "lineitem_quantity", 
                        "Quantity", "quantity"]

        for col in quantity_cols:
            if col in self.df.columns:
                quantity_col = col
                break

        price_col = None
        price_cols = ["Lineitem price", "lineitem_price", 
                     "Price", "price"]

        for col in price_cols:
            if col in self.df.columns:
                price_col = col
                break

        if quantity_col:
            self.df[quantity_col] = pd.to_numeric(
                self.df[quantity_col], errors="coerce"
            ).fillna(0)

        if price_col:
            self.df[price_col] = pd.to_numeric(
                self.df[price_col], errors="coerce"
            ).fillna(0)

        products = []

        for product_name in self.df[product_col].unique():
            if pd.isna(product_name):
                continue

            product_df = self.df[self.df[product_col] == product_name]

            product_orders = len(product_df)

            product_revenue = 0
            if price_col and quantity_col:
                product_revenue = (
                    product_df[price_col] * product_df[quantity_col]
                ).sum()
            elif price_col:
                product_revenue = product_df[price_col].sum()

            product_units = 0
            if quantity_col:
                product_units = int(product_df[quantity_col].sum())
            else:
                product_units = product_orders

            product_refunds = 0
            if self.refund_col:
                product_refunds = product_df[self.refund_col].sum()

            product_return_rate = (
                product_refunds / product_revenue 
                if product_revenue > 0 else 0
            )

            products.append({
                "product_name": product_name,
                "orders": product_orders,
                "units_sold": product_units,
                "revenue": round(product_revenue, 2),
                "refunds": round(product_refunds, 2),
                "return_rate": round(product_return_rate, 4)
            })

        products.sort(key=lambda x: x["revenue"], reverse=True)

        return products

    def calculate_daily_trend(self):
        """Calculate daily revenue trend"""

        if self.date_col is None:
            return {"error": "No date column found"}

        daily = self.df.groupby("order_date").agg(
            daily_revenue=(self.revenue_col, "sum"),
            daily_orders=(self.revenue_col, "count")
        ).reset_index()

        daily["daily_aov"] = (
            daily["daily_revenue"] / daily["daily_orders"]
        )

        daily = daily.sort_values("order_date")

        trend = []
        for _, row in daily.iterrows():
            trend.append({
                "date": str(row["order_date"]),
                "revenue": round(row["daily_revenue"], 2),
                "orders": int(row["daily_orders"]),
                "aov": round(row["daily_aov"], 2)
            })

        return trend

    def calculate_city_metrics(self):
        """Calculate city-wise performance"""

        city_col = None
        city_cols = ["Shipping City", "shipping_city", 
                    "City", "city"]

        for col in city_cols:
            if col in self.df.columns:
                city_col = col
                break

        if city_col is None:
            return {"error": "No city column found"}

        city_data = self.df.groupby(city_col).agg(
            orders=(self.revenue_col, "count"),
            revenue=(self.revenue_col, "sum")
        ).reset_index()

        city_data = city_data.sort_values("revenue", ascending=False)

        cities = []
        for _, row in city_data.iterrows():
            cities.append({
                "city": row[city_col],
                "orders": int(row["orders"]),
                "revenue": round(row["revenue"], 2)
            })

        return cities[:10]

    def calculate_payment_metrics(self):
        """Calculate payment method breakdown"""

        payment_col = None
        payment_cols = ["Payment Method", "payment_method", 
                       "Gateway", "gateway"]

        for col in payment_cols:
            if col in self.df.columns:
                payment_col = col
                break

        if payment_col is None:
            return {"error": "No payment column found"}

        payment_data = self.df.groupby(payment_col).agg(
            orders=(self.revenue_col, "count"),
            revenue=(self.revenue_col, "sum")
        ).reset_index()

        payment_data = payment_data.sort_values(
            "revenue", ascending=False
        )

        payments = []
        for _, row in payment_data.iterrows():
            payments.append({
                "method": row[payment_col],
                "orders": int(row["orders"]),
                "revenue": round(row["revenue"], 2)
            })

        return payments

    def generate_full_report(self):
        """Generate complete analysis report"""

        report = {
            "revenue_metrics": self.calculate_revenue_metrics(),
            "cost_metrics": self.calculate_cost_metrics(),
            "scaling_metrics": self.calculate_scaling_metrics(),
            "product_metrics": self.calculate_product_metrics(),
            "daily_trend": self.calculate_daily_trend(),
            "city_metrics": self.calculate_city_metrics(),
            "payment_metrics": self.calculate_payment_metrics()
        }

        return report


# Test the calculator
if __name__ == "__main__":
    
    # Load test data
    print("Loading test data...")
    df = pd.read_csv("test_shopify_export.csv")
    print(f"Loaded {len(df)} orders")

    # Create calculator
    calc = MetricsCalculator(
        df=df,
        ad_spend=350000,
        cogs_percent=35,
        avg_shipping=100,
        payment_fee_percent=2,
        meta_percent=70
    )

    # Generate full report
    print("\n" + "=" * 50)
    print("DATAPILOT FULL ANALYSIS REPORT")
    print("=" * 50)

    # Revenue
    rev = calc.calculate_revenue_metrics()
    print(f"\n📈 REVENUE METRICS")
    print(f"Total Revenue: Rs.{rev['total_revenue']:,.0f}")
    print(f"Total Refunds: Rs.{rev['total_refunds']:,.0f}")
    print(f"Net Revenue: Rs.{rev['net_revenue']:,.0f}")
    print(f"Total Orders: {rev['total_orders']}")
    print(f"Refund Rate: {rev['refund_rate']:.1%}")
    print(f"AOV: Rs.{rev['aov']:,.0f}")

    # Costs
    costs = calc.calculate_cost_metrics()
    print(f"\n💸 COST METRICS")
    print(f"COGS: Rs.{costs['cogs_amount']:,.0f}")
    print(f"Shipping: Rs.{costs['shipping_total']:,.0f}")
    print(f"Payment Fees: Rs.{costs['payment_fees']:,.0f}")
    print(f"Ad Spend: Rs.{costs['ad_spend']:,.0f}")
    print(f"Net Profit: Rs.{costs['net_profit']:,.0f}")
    print(f"Contribution Margin: {costs['contribution_margin']:.1%}")
    print(f"Profit per Order: Rs.{costs['profit_per_order']:,.0f}")

    # Scaling
    scaling = calc.calculate_scaling_metrics()
    print(f"\n🚦 SCALING METRICS")
    print(f"Break-even ROAS: {scaling['break_even_roas']:.2f}x")
    print(f"Current ROAS: {scaling['current_roas']:.2f}x")
    print(f"Scaling Status: {scaling['scaling_status']}")
    print(f"Can Absorb 10% ROAS Drop: {scaling['can_absorb_roas_drop']}")
    print(f"Can Absorb 5% Return Increase: {scaling['can_absorb_return_increase']}")

    # Products
    products = calc.calculate_product_metrics()
    print(f"\n📦 TOP PRODUCTS")
    if isinstance(products, list):
        for p in products[:5]:
            print(f"  {p['product_name']}: Rs.{p['revenue']:,.0f} "
                  f"({p['units_sold']} units, "
                  f"return rate: {p['return_rate']:.1%})")

    # Cities
    cities = calc.calculate_city_metrics()
    print(f"\n🏙️ TOP CITIES")
    if isinstance(cities, list):
        for c in cities[:5]:
            print(f"  {c['city']}: Rs.{c['revenue']:,.0f} "
                  f"({c['orders']} orders)")

    # Payment
    payments = calc.calculate_payment_metrics()
    print(f"\n💳 PAYMENT METHODS")
    if isinstance(payments, list):
        for p in payments:
            print(f"  {p['method']}: Rs.{p['revenue']:,.0f} "
                  f"({p['orders']} orders)")

    print(f"\n{'=' * 50}")
    print("Report generation complete!")