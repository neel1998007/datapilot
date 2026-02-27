import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from clients import CLIENTS
from datetime import datetime

def check_subscription(store_url):
    for client in CLIENTS.values():
        if client["store_url"] == store_url:

            if client.get("subscription_status") != "active":
                return False

            end_date = datetime.strptime(
                client["subscription_end_date"],
                "%Y-%m-%d"
            )

            return datetime.now() <= end_date

    return False

load_dotenv()

st.set_page_config(
    page_title="DataPilot - Scaling Clarity Engine",
    page_icon="📊",
    layout="wide"
)

st.title("📊 DataPilot")
st.subheader("Scaling Clarity Engine for Indian D2C Brands")
st.caption("Know exactly when to scale — and when to stop.")

st.markdown("---")

# Input method selection
input_method = st.radio(
    "How would you like to input data?",
    ["Manual Input", "Upload Shopify CSV", "Connect Shopify Store"],
    horizontal=True
)

# Variables
revenue = 0
refunds = 0
orders = 1
ad_spend = 0
cogs_percent = 0
shipping_cost = 0
payment_fee_percent = 2
meta_percent = 70
df = None

if input_method == "Manual Input":

    st.header("📥 Enter Your Last 30 Days Data")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("💰 Revenue")
        revenue = st.number_input("Total Revenue (₹)", min_value=0.0, step=10000.0)
        refunds = st.number_input("Total Refunds (₹)", min_value=0.0, step=1000.0)
        orders = st.number_input("Total Orders", min_value=1.0, step=10.0)

    with col2:
        st.subheader("📢 Marketing")
        ad_spend = st.number_input("Total Ad Spend (₹)", min_value=0.0, step=5000.0)
        meta_percent = st.number_input("Meta Ads Share (%)", min_value=0.0, max_value=100.0, value=70.0)

    with col3:
        st.subheader("📦 Costs")
        cogs_percent = st.number_input("COGS (%)", min_value=0.0, step=1.0)
        shipping_cost = st.number_input("Avg Shipping/Order (₹)", min_value=0.0, step=10.0)
        payment_fee_percent = st.number_input("Payment Fee (%)", min_value=0.0, value=2.0)

elif input_method == "Upload Shopify CSV":

    st.header("📤 Upload Your Shopify Orders Export")

    st.markdown("""
    **How to export:**
    1. Shopify Admin → Orders → Export
    2. Select "All Orders" and "CSV for Excel"
    3. Upload below
    """)

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.success(f"✅ Uploaded! {len(df)} rows found.")

        revenue_cols = ["Total", "total", "Total Price", "Subtotal"]
        refund_cols = ["Refund", "refund", "Refunded Amount"]

        rev_col = None
        ref_col = None

        for col in revenue_cols:
            if col in df.columns:
                rev_col = col
                break

        for col in refund_cols:
            if col in df.columns:
                ref_col = col
                break

        if rev_col:
            df[rev_col] = pd.to_numeric(df[rev_col], errors="coerce").fillna(0)
            revenue = df[rev_col].sum()
            orders = len(df)

        if ref_col:
            df[ref_col] = pd.to_numeric(df[ref_col], errors="coerce").fillna(0)
            refunds = df[ref_col].sum()

        st.write(f"Revenue: **₹{revenue:,.0f}**")
        st.write(f"Refunds: **₹{refunds:,.0f}**")
        st.write(f"Orders: **{orders}**")

        st.markdown("---")
        st.subheader("Enter Cost Details")

        c1, c2 = st.columns(2)
        with c1:
            ad_spend = st.number_input("Total Ad Spend (₹)", min_value=0.0, step=5000.0, key="csv_ad")
            meta_percent = st.number_input("Meta Share (%)", min_value=0.0, max_value=100.0, value=70.0, key="csv_meta")
        with c2:
            cogs_percent = st.number_input("COGS (%)", min_value=0.0, step=1.0, key="csv_cogs")
            shipping_cost = st.number_input("Avg Shipping/Order (₹)", min_value=0.0, step=10.0, key="csv_ship")
            payment_fee_percent = st.number_input("Payment Fee (%)", min_value=0.0, value=2.0, key="csv_pay")
    else:
        st.info("Please upload a CSV to continue.")
        st.stop()

elif input_method == "Connect Shopify Store":

    st.header("🔗 Connect Your Shopify Store")

    st.markdown("""
    **How it works:**
    1. Create a custom app in your Shopify admin
    2. Give it read-only access to orders
    3. Enter the details below
    """)

    store_url = st.text_input("Store URL (e.g., yourstore.myshopify.com)")
    access_token = st.text_input("Admin API Access Token", type="password")
        
    if store_url:
        if not check_subscription(store_url):
            st.error("❌ Your subscription has expired. Please renew to continue.")
            st.stop()


    if store_url and access_token:

        if st.button("🔗 Fetch Orders"):
            import requests

            url = f"https://{store_url}/admin/api/2024-01/orders.json?limit=100"
            headers = {
                "X-Shopify-Access-Token": access_token,
                "Content-Type": "application/json"
            }

            with st.spinner("Fetching orders from Shopify..."):
                response = requests.get(url, headers=headers)

            if response.status_code == 200:
                raw_orders = response.json().get("orders", [])
                st.success(f"✅ Fetched {len(raw_orders)} orders!")

                if raw_orders:
                    from shopify_normalizer import normalize_shopify_orders
                    df = normalize_shopify_orders(raw_orders)
                    revenue = df["Total"].sum()
                    refunds = df["Refund"].sum()
                    orders = len(raw_orders)

                    st.write(f"Revenue: **₹{revenue:,.0f}**")
                    st.write(f"Refunds: **₹{refunds:,.0f}**")
                    st.write(f"Orders: **{orders}**")

                    st.session_state["shopify_df"] = df
                    st.session_state["shopify_connected"] = True
                else:
                    st.warning("No orders found in the store.")
                    st.stop()
            else:
                st.error(f"❌ Failed: {response.text}")
                st.stop()

        if st.session_state.get("shopify_connected"):
            df = st.session_state.get("shopify_df")
            revenue = df["Total"].sum()
            refunds = df["Refund"].sum()
            orders = len(df)

            st.markdown("---")
            st.subheader("Enter Cost Details")

            c1, c2 = st.columns(2)
            with c1:
                ad_spend = st.number_input("Total Ad Spend (₹)", min_value=0.0, step=5000.0, key="shop_ad")
                meta_percent = st.number_input("Meta Share (%)", min_value=0.0, max_value=100.0, value=70.0, key="shop_meta")
            with c2:
                cogs_percent = st.number_input("COGS (%)", min_value=0.0, step=1.0, key="shop_cogs")
                shipping_cost = st.number_input("Avg Shipping/Order (₹)", min_value=0.0, step=10.0, key="shop_ship")
                payment_fee_percent = st.number_input("Payment Fee (%)", min_value=0.0, value=2.0, key="shop_pay")
        else:
            st.info("Enter store details and click Fetch Orders.")
            st.stop()

st.markdown("---")

if st.button("🚀 Run Scaling Diagnosis", type="primary"):

    google_percent = 100 - meta_percent
    net_revenue = revenue - refunds
    refund_rate = refunds / revenue if revenue > 0 else 0

    cogs_amount = net_revenue * (cogs_percent / 100)
    shipping_total = shipping_cost * orders
    payment_fees = net_revenue * (payment_fee_percent / 100)

    net_profit = net_revenue - cogs_amount - shipping_total - payment_fees
    contribution_margin = net_profit / net_revenue if net_revenue > 0 else 0

    break_even_roas = 1 / contribution_margin if contribution_margin > 0 else 0
    current_roas = revenue / ad_spend if ad_spend > 0 else 0

    aov = revenue / orders if orders > 0 else 0
    cost_per_order = (cogs_amount + shipping_total + payment_fees + ad_spend) / orders if orders > 0 else 0
    profit_per_order = aov - cost_per_order

    meta_spend = ad_spend * (meta_percent / 100)
    google_spend = ad_spend * (google_percent / 100)

    st.markdown("---")
    st.header("📊 Business Health Snapshot")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Revenue", f"₹{revenue:,.0f}")
    m2.metric("Net Revenue", f"₹{net_revenue:,.0f}")
    m3.metric("Refund Rate", f"{refund_rate:.1%}")
    m4.metric("AOV", f"₹{aov:,.0f}")
    m5.metric("Profit/Order", f"₹{profit_per_order:,.0f}")

    st.markdown("---")
    st.header("💸 Cost Breakdown")

    cc1, cc2 = st.columns(2)

    with cc1:
        st.write(f"COGS: **₹{cogs_amount:,.0f}**")
        st.write(f"Shipping: **₹{shipping_total:,.0f}**")
        st.write(f"Payment Fees: **₹{payment_fees:,.0f}**")
        st.write(f"Ad Spend: **₹{ad_spend:,.0f}**")
        total_costs = cogs_amount + shipping_total + payment_fees + ad_spend
        st.write(f"**Total: ₹{total_costs:,.0f}**")

    with cc2:
        if total_costs > 0:
            import plotly.graph_objects as go
            fig = go.Figure(data=[go.Pie(
                labels=["COGS", "Shipping", "Payment", "Ads"],
                values=[cogs_amount, shipping_total, payment_fees, ad_spend],
                hole=0.4,
                marker_colors=["#FF6B6B", "#FFA500", "#FFD93D", "#6BCB77"]
            )])
            fig.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig, width="stretch")

    st.markdown("---")
    st.header("🚦 Scaling Decision")

    if current_roas > break_even_roas:
        st.success("✅ SAFE TO SCALE")
        scaling_status = "Safe"
    elif current_roas > break_even_roas * 0.9:
        st.warning("⚠️ RISK ZONE")
        scaling_status = "Risk"
    else:
        st.error("❌ REDUCE SPEND")
        scaling_status = "Burn"

    st.write(f"Break-even ROAS: **{break_even_roas:.2f}x**")
    st.write(f"Current ROAS: **{current_roas:.2f}x**")

    st.markdown("---")
    st.header("🧠 AI Insights")

    with st.spinner("Generating AI insights..."):
        try:
            from metrics_calculator import MetricsCalculator
            from ai_insights import generate_insights

            if df is not None:
                calc = MetricsCalculator(
                    df=df,
                    ad_spend=ad_spend,
                    cogs_percent=cogs_percent,
                    avg_shipping=shipping_cost,
                    payment_fee_percent=payment_fee_percent,
                    meta_percent=meta_percent
                )
                report_data = calc.generate_full_report()
            else:
                report_data = {
                    "revenue_metrics": {
                        "total_revenue": revenue,
                        "total_refunds": refunds,
                        "net_revenue": net_revenue,
                        "total_orders": int(orders),
                        "refund_rate": refund_rate,
                        "aov": aov
                    },
                    "cost_metrics": {
                        "cogs_amount": cogs_amount,
                        "shipping_total": shipping_total,
                        "payment_fees": payment_fees,
                        "ad_spend": ad_spend,
                        "net_profit": net_profit,
                        "contribution_margin": contribution_margin,
                        "profit_per_order": profit_per_order,
                        "cost_per_order": cost_per_order
                    },
                    "scaling_metrics": {
                        "break_even_roas": break_even_roas,
                        "current_roas": current_roas,
                        "scaling_status": scaling_status
                    },
                    "product_metrics": [],
                    "city_metrics": []
                }

            insights = generate_insights(report_data)
            st.markdown(insights)

        except Exception as e:
            st.error(f"Could not generate AI insights: {e}")

    st.markdown("---")

    summary = f"""
DATAPILOT SCALING REPORT
========================
Revenue: Rs.{revenue:,.0f}
Net Revenue: Rs.{net_revenue:,.0f}
Refund Rate: {refund_rate:.1%}
AOV: Rs.{aov:,.0f}
Ad Spend: Rs.{ad_spend:,.0f}
ROAS: {current_roas:.2f}x
Break-even ROAS: {break_even_roas:.2f}x
Margin: {contribution_margin:.1%}
Profit/Order: Rs.{profit_per_order:,.0f}
Status: {scaling_status}
"""

    st.download_button(
        label="📥 Download Report",
        data=summary,
        file_name="datapilot_report.txt",
        mime="text/plain"
    )

    st.markdown("---")
    st.caption("DataPilot v1.0 — Scaling Clarity Engine for Indian D2C Brands")


