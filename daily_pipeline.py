import os
import pandas as pd
from dotenv import load_dotenv
from shopify_connector import fetch_orders
from shopify_normalizer import normalize_shopify_orders
from metrics_calculator import MetricsCalculator
from ai_insights import generate_whatsapp_report
from whatsapp_sender import send_whatsapp_message
from datetime import datetime
import json

load_dotenv()

MY_PHONE = os.getenv("MY_PHONE")
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")


def run_pipeline(store_url=None, brand_name="D2C Brand",
                 ad_spend=0, cogs_percent=0,
                 avg_shipping=0, payment_fee_percent=2,
                 meta_percent=70, phone_number=None,
                 language="English"):

    if phone_number is None:
        phone_number = MY_PHONE

    if store_url is None:
        store_url = SHOPIFY_STORE_URL

    print("=" * 50)
    print("📊 DATAPILOT AUTOMATED PIPELINE")
    print("=" * 50)

    # STEP 1 — Fetch Orders
    try:
        print("\n[1/4] Fetching orders from Shopify...")
        raw_orders = fetch_orders(limit=100)

        if not raw_orders:
            print("❌ No orders found. Pipeline stopped.")
            return None

        print(f"✅ Fetched {len(raw_orders)} raw orders")
    except Exception as e:
        print(f"❌ Error fetching orders: {e}")
        return None

    # STEP 2 — Normalize and Calculate
    try:
        print("\n[2/4] Processing and calculating metrics...")

        df = normalize_shopify_orders(raw_orders)
        print(f"✅ Normalized into {len(df)} line items")

        calc = MetricsCalculator(
            df=df,
            ad_spend=ad_spend,
            cogs_percent=cogs_percent,
            avg_shipping=avg_shipping,
            payment_fee_percent=payment_fee_percent,
            meta_percent=meta_percent
        )

        report_data = calc.generate_full_report()

        rev = report_data.get("revenue_metrics", {})
        costs = report_data.get("cost_metrics", {})
        scaling = report_data.get("scaling_metrics", {})

        print(f"   Revenue: Rs.{rev.get('total_revenue', 0):,.0f}")
        print(f"   Orders: {rev.get('total_orders', 0)}")
        print(f"   Margin: {costs.get('contribution_margin', 0):.1%}")
        print(f"   ROAS: {scaling.get('current_roas', 0):.2f}x")
        print(f"   Status: {scaling.get('scaling_status', 'Unknown')}")
        print("✅ Metrics calculated")
    except Exception as e:
        print(f"❌ Error calculating metrics: {e}")
        return None

    # STEP 3 — Generate AI Report
    try:
        print("\n[3/4] Generating AI insights...")

        whatsapp_report = generate_whatsapp_report(
            report_data,
            brand_name=brand_name,
            language=language
        )

        print("✅ AI report generated")
    except Exception as e:
        print(f"❌ Error generating AI report: {e}")
        return None

    # STEP 4 — Send WhatsApp
    try:
        print(f"\n[4/4] Sending report to {phone_number}...")

        send_whatsapp_message(phone_number, whatsapp_report)

        print("✅ Report sent!")
    except Exception as e:
        print(f"❌ Error sending WhatsApp: {e}")
        return None

    print("\n" + "=" * 50)
    print("✅ PIPELINE COMPLETE")
    print("=" * 50)

    return report_data


if __name__ == "__main__":

    run_pipeline(
        brand_name="DataPilot Test Store",
        ad_spend=350000,
        cogs_percent=35,
        avg_shipping=100,
        payment_fee_percent=2,
        meta_percent=70
    )