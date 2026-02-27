import os
import json
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def convert_to_serializable(obj):
    import numpy as np
    if isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, bool):
        return bool(obj)
    else:
        return obj


def generate_insights(report_data, language="English"):
    
    """
    Generate AI insights in selected language.
    Supported: English, Hindi, Gujarati
    """
    
    safe_data = convert_to_serializable(report_data)
    
    # Language instruction
    if language.lower() == "hindi":
        language_instruction = """
    Write the ENTIRE report in Hindi.
    Use simple Hindi business language.
    DO NOT write in English.
    """
    
    elif language.lower() == "gujarati":
        language_instruction = """
    Write the ENTIRE report in Gujarati.
    Use simple Gujarati business language.
    DO NOT write in Hindi.
    DO NOT write in English.
    All headings and content must be Gujarati.
    """
    else:
        language_instruction = """
    Write in simple, clear English.
    Avoid corporate jargon.
    Use short sentences.
    """

    prompt = f"""

You are DataPilot — an expert AI analyst for Indian D2C brands.

A founder just uploaded their last 30 days of business data.
Your job is to analyze and generate a practical, actionable report.
IMPORTANT: Follow the language instruction strictly.

Here is their data:

REVENUE METRICS:
{json.dumps(safe_data['revenue_metrics'], indent=2)}

COST METRICS:
{json.dumps(safe_data['cost_metrics'], indent=2)}

SCALING METRICS:
{json.dumps(safe_data['scaling_metrics'], indent=2)}

TOP PRODUCTS:
{json.dumps(safe_data.get('product_metrics', []), indent=2)}

TOP CITIES:
{json.dumps(safe_data.get('city_metrics', []), indent=2)}

PAYMENT METHODS:
{json.dumps(safe_data['payment_metrics'], indent=2)}

Now generate a report with these sections:

1. BUSINESS HEALTH SUMMARY (2-3 lines)
   - Overall assessment of the business

2. KEY WINS (2-3 bullet points)
   - What is going well

3. CRITICAL WARNINGS (2-3 bullet points)
   - What needs attention immediately

4. PRODUCT INSIGHTS (2-3 bullet points)
   - Which products are stars vs problems
   - Flag any product with return rate above 15%

5. SCALING RECOMMENDATION (2-3 lines)
   - Can they scale? By how much?
   - What should they do this week?

6. TOP 3 ACTION ITEMS
   - Specific things to do THIS WEEK
   - Prioritized by impact

RULES:
- Use Indian Rupees (Rs.)
- Use Indian number format
- Use simple business English.
- Use short sentences.
- Avoid technical words like "robust", "sustainable", "optimization".
- Speak like a practical business advisor.
- Be direct.
- Keep total response under 350 words.
- Every insight must mention actual numbers.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are DataPilot, an expert D2C business analyst for Indian brands. You give clear, actionable, data-backed insights."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        max_tokens=1000
    )

    return response.choices[0].message.content


def generate_whatsapp_report(report_data, brand_name="Your Brand", language="English"):

    rev = convert_to_serializable(report_data.get("revenue_metrics", {}))
    costs = convert_to_serializable(report_data.get("cost_metrics", {}))
    scaling = convert_to_serializable(report_data.get("scaling_metrics", {}))

    if scaling.get("scaling_status") == "Safe":
        status_emoji = "✅"
        status_text = "SAFE TO SCALE"
    elif scaling.get("scaling_status") == "Risk":
        status_emoji = "⚠️"
        status_text = "RISK ZONE"
    else:
        status_emoji = "❌"
        status_text = "REDUCE SPEND"

    header = f"""📊 *DataPilot Report*
_{brand_name}_
━━━━━━━━━━━━━━━━━━

💰 Revenue: Rs.{rev.get('total_revenue', 0):,.0f}
📦 Orders: {rev.get('total_orders', 0)}
🔄 Refund Rate: {rev.get('refund_rate', 0):.1%}
📈 AOV: Rs.{rev.get('aov', 0):,.0f}

💸 Margin: {costs.get('contribution_margin', 0):.1%}
💵 Profit/Order: Rs.{costs.get('profit_per_order', 0):,.0f}

🎯 Break-even ROAS: {scaling.get('break_even_roas', 0):.2f}x
📊 Current ROAS: {scaling.get('current_roas', 0):.2f}x

{status_emoji} *{status_text}*

━━━━━━━━━━━━━━━━━━"""

    insights = generate_insights(report_data, language=language)

    full_report = header + "\n\n🧠 *Insights:*\n\n" + insights
    full_report += "\n\n━━━━━━━━━━━━━━━━━━\n_Powered by DataPilot_"

    return full_report


if __name__ == "__main__":
    from metrics_calculator import MetricsCalculator
    import pandas as pd

    print("Loading test data...")
    df = pd.read_csv("test_shopify_export.csv")

    calc = MetricsCalculator(
        df=df,
        ad_spend=350000,
        cogs_percent=35,
        avg_shipping=100,
        payment_fee_percent=2,
        meta_percent=70
    )

    print("Calculating metrics...")
    report_data = calc.generate_full_report()

    print("Generating AI insights...")
    print("\n" + "=" * 50)

    whatsapp_report = generate_whatsapp_report(
        report_data,
        brand_name="Test D2C Brand",
        language="English"
    )

    print(whatsapp_report)
    print("\n" + "=" * 50)
    print("AI Report generation complete!")