import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="DataPilot - Scaling Clarity Engine",
    page_icon="📊",
    layout="wide"
)

st.title("📊 DataPilot")
st.subheader("Scaling Clarity Engine for Indian D2C Brands")
st.caption("Know exactly when to scale — and when to stop.")

st.markdown("---")

input_method = st.radio(
    "How would you like to input data?",
    ["Manual Input", "Upload Shopify CSV"],
    horizontal=True
)

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
        google_percent = 100 - meta_percent

    with col3:
        st.subheader("📦 Costs")
        cogs_percent = st.number_input("COGS (%)", min_value=0.0, step=1.0)
        shipping_cost = st.number_input("Avg Shipping per Order (₹)", min_value=0.0, step=10.0)
        payment_fee_percent = st.number_input("Payment Gateway Fee (%)", min_value=0.0, value=2.0)

elif input_method == "Upload Shopify CSV":

    st.header("📤 Upload Your Shopify Orders Export")

    st.markdown("""
    **How to export from Shopify:**
    1. Go to Shopify Admin → Orders
    2. Click Export → Export Orders
    3. Choose "All Orders" and "CSV for Excel"
    4. Upload that file below
    """)

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        st.success(f"✅ Uploaded successfully! {len(df)} rows found.")

        st.subheader("Preview of Your Data")
        st.dataframe(df.head(10))

        possible_revenue_cols = ["Total", "total", "Subtotal", "subtotal", "Total Price", "total_price"]
        possible_refund_cols = ["Refund", "refund", "Refunded Amount", "refunded_amount"]

        revenue_col = None
        refund_col = None

        for col in possible_revenue_cols:
            if col in df.columns:
                revenue_col = col
                break

        for col in possible_refund_cols:
            if col in df.columns:
                refund_col = col
                break

        if revenue_col:
            df[revenue_col] = pd.to_numeric(df[revenue_col], errors="coerce").fillna(0)
            revenue = df[revenue_col].sum()
            orders = len(df)
        else:
            st.warning("⚠️ Could not find revenue column. Please use Manual Input.")
            st.stop()

        if refund_col:
            df[refund_col] = pd.to_numeric(df[refund_col], errors="coerce").fillna(0)
            refunds = df[refund_col].sum()
        else:
            refunds = 0.0
            st.info("No refund column found. Setting refunds to ₹0.")

        st.write(f"Detected Revenue: **₹{revenue:,.0f}**")
        st.write(f"Detected Refunds: **₹{refunds:,.0f}**")
        st.write(f"Detected Orders: **{orders}**")

        st.markdown("---")
        st.subheader("Enter Remaining Details")

        r1, r2 = st.columns(2)

        with r1:
            ad_spend = st.number_input("Total Ad Spend (₹)", min_value=0.0, step=5000.0, key="csv_ad")
            meta_percent = st.number_input("Meta Ads Share (%)", min_value=0.0, max_value=100.0, value=70.0, key="csv_meta")
            google_percent = 100 - meta_percent

        with r2:
            cogs_percent = st.number_input("COGS (%)", min_value=0.0, step=1.0, key="csv_cogs")
            shipping_cost = st.number_input("Avg Shipping per Order (₹)", min_value=0.0, step=10.0, key="csv_ship")
            payment_fee_percent = st.number_input("Payment Gateway Fee (%)", min_value=0.0, value=2.0, key="csv_pay")
    else:
        st.info("Please upload a CSV file to continue.")
        st.stop()

st.markdown("---")

if st.button("🚀 Run Scaling Diagnosis", type="primary"):

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

    cost_col1, cost_col2 = st.columns(2)

    with cost_col1:
        st.write(f"COGS: **₹{cogs_amount:,.0f}**")
        st.write(f"Shipping: **₹{shipping_total:,.0f}**")
        st.write(f"Payment Fees: **₹{payment_fees:,.0f}**")
        st.write(f"Ad Spend: **₹{ad_spend:,.0f}**")
        st.write(f"**Total Costs: ₹{(cogs_amount + shipping_total + payment_fees + ad_spend):,.0f}**")

    with cost_col2:
        total_costs = cogs_amount + shipping_total + payment_fees + ad_spend
        if total_costs > 0:
            import plotly.graph_objects as go

            labels = ["COGS", "Shipping", "Payment Fees", "Ad Spend"]
            values = [cogs_amount, shipping_total, payment_fees, ad_spend]
            colors = ["#FF6B6B", "#FFA500", "#FFD93D", "#6BCB77"]

            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker_colors=colors
            )])
            fig.update_layout(
                title="Cost Distribution",
                height=300,
                margin=dict(t=40, b=0, l=0, r=0)
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.header("📢 Ad Spend Breakdown")

    ad_col1, ad_col2 = st.columns(2)

    with ad_col1:
        st.write(f"Meta Ads: **₹{meta_spend:,.0f}** ({meta_percent:.0f}%)")
        st.write(f"Google Ads: **₹{google_spend:,.0f}** ({google_percent:.0f}%)")

    with ad_col2:
        st.write(f"Blended ROAS: **{current_roas:.2f}x**")
        st.write(f"Break-even ROAS: **{break_even_roas:.2f}x**")

    st.markdown("---")

    st.header("🚦 Scaling Decision")

    if current_roas > break_even_roas:
        scaling_status = "Safe"
        st.success("✅ SAFE TO SCALE")
        st.markdown("""
        **Your current ROAS is above break-even.**

        - You are generating surplus contribution margin.
        - Scaling is financially supported.
        - Monitor return rate for any spikes.
        """)
    elif current_roas > break_even_roas * 0.9:
        scaling_status = "Risk"
        st.warning("⚠️ RISK ZONE — SCALE WITH CAUTION")
        st.markdown("""
        **You are dangerously close to break-even.**

        - A small increase in CPM or returns could push you into loss.
        - Do not increase spend aggressively.
        - Tighten targeting and reduce wasteful spend first.
        """)
    else:
        scaling_status = "Burn"
        st.error("❌ CASH BURN — REDUCE SPEND IMMEDIATELY")
        st.markdown("""
        **You are operating below break-even ROAS.**

        - Every rupee you spend on ads is generating a loss.
        - Reduce spend until margins improve.
        - Investigate: pricing, COGS, return rate, or audience quality.
        """)

    st.markdown("---")

    st.header("🧠 Risk Sensitivity Analysis")

    st.subheader("What If ROAS Drops 10%?")

    roas_drop = current_roas * 0.9
    st.write(f"Projected ROAS: **{roas_drop:.2f}x**")

    if roas_drop < break_even_roas:
        st.error("⚠️ A 10% ROAS drop would push you BELOW break-even.")
    else:
        st.success("✅ You can absorb a 10% ROAS drop safely.")

    st.subheader("What If Return Rate Increases 5%?")

    new_refund_rate = refund_rate + 0.05
    new_net_revenue = revenue * (1 - new_refund_rate)
    new_cogs = new_net_revenue * (cogs_percent / 100)
    new_payment = new_net_revenue * (payment_fee_percent / 100)
    new_profit = new_net_revenue - new_cogs - shipping_total - new_payment
    new_margin = new_profit / new_net_revenue if new_net_revenue > 0 else 0
    new_be_roas = 1 / new_margin if new_margin > 0 else 0

    st.write(f"New Refund Rate: **{new_refund_rate:.1%}**")
    st.write(f"New Break-even ROAS: **{new_be_roas:.2f}x**")

    if current_roas < new_be_roas:
        st.error("⚠️ A 5% return increase would make scaling unprofitable.")
    else:
        st.success("✅ You can absorb a 5% return increase safely.")

    st.markdown("---")

    st.header("📌 Key Recommendations")

    if scaling_status == "Safe":
        st.markdown("""
        1. ✅ You can increase ad spend by 10-20% safely.
        2. 📊 Monitor return rate weekly — it's your biggest margin risk.
        3. 🎯 Test new audiences while maintaining current ROAS.
        4. 💡 Consider increasing AOV through bundling or upsells.
        """)
    elif scaling_status == "Risk":
        st.markdown("""
        1. ⚠️ Do NOT increase ad spend right now.
        2. 🔍 Audit your highest-spend campaigns — cut underperformers.
        3. 📦 Investigate return reasons — reduce RTO.
        4. 💰 Look for ways to reduce COGS or shipping costs.
        5. 🎯 Tighten audience targeting to improve conversion rate.
        """)
    else:
        st.markdown("""
        1. ❌ Reduce ad spend immediately by 30-50%.
        2. 🔍 Identify which campaigns are bleeding money.
        3. 📦 Return rate is likely eating your margins — investigate SKU-level returns.
        4. 💰 Renegotiate COGS with suppliers or find alternatives.
        5. 🏷️ Consider price increases on low-margin products.
        6. 🎯 Pause broad targeting — focus only on proven audiences.
        """)

    st.markdown("---")

    st.header("📅 30-Day Projection")

    if scaling_status == "Safe":
        projected_revenue = revenue * 1.15
        projected_profit = net_profit * 1.15
        st.write("If you scale 15%:")
    elif scaling_status == "Risk":
        projected_revenue = revenue
        projected_profit = net_profit
        st.write("If you maintain current spend:")
    else:
        projected_revenue = revenue * 0.7
        projected_profit = net_profit * 1.3
        st.write("If you reduce spend by 30%:")

    p1, p2 = st.columns(2)
    p1.metric("Projected Revenue", f"₹{projected_revenue:,.0f}")
    p2.metric("Projected Profit", f"₹{projected_profit:,.0f}")

    st.markdown("---")

    st.header("📋 Executive Summary")

    summary = f"""
DATAPILOT SCALING REPORT
========================

Revenue: Rs.{revenue:,.0f}
Net Revenue: Rs.{net_revenue:,.0f}
Refund Rate: {refund_rate:.1%}
AOV: Rs.{aov:,.0f}

Total Ad Spend: Rs.{ad_spend:,.0f}
Current ROAS: {current_roas:.2f}x
Break-even ROAS: {break_even_roas:.2f}x

Contribution Margin: {contribution_margin:.1%}
Profit per Order: Rs.{profit_per_order:,.0f}

Scaling Status: {scaling_status}
    """

    st.text(summary)

    st.download_button(
        label="📥 Download Report",
        data=summary,
        file_name="datapilot_scaling_report.txt",
        mime="text/plain"
    )

    st.markdown("---")
    st.caption("DataPilot v0.5 — Scaling Clarity Engine for Indian D2C Brands")
