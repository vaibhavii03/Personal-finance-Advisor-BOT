import os
import json
import logging
from config import Config
from models.models import db, AIRecommendation
from services.finance_service import get_monthly_summary, get_budget_status

logger = logging.getLogger(__name__)

DISCLAIMER_TEXT = "AI-generated insights are for educational and planning purposes only and should not be considered professional financial advice."

def generate_financial_advice(user, month=None, year=None):
    """
    Generates personalized financial recommendations for the user.
    Uses Google Gemini AI if GEMINI_API_KEY is configured and working;
    otherwise smoothly falls back to a deterministic rule-based analysis.
    """
    summary = get_monthly_summary(user.id, month, year)
    budget_data = get_budget_status(user.id, month, year)
    goals = user.savings_goals

    # Build financial context
    income = summary['total_income']
    expenses = summary['total_expenses']
    savings = summary['total_savings']
    savings_rate = summary['savings_rate']
    category_list = summary['category_list']
    top_cat = summary['top_category']
    top_cat_amt = summary['top_category_amount']

    # Check for empty data
    if income == 0 and expenses == 0:
        return {
            'is_ai': False,
            'source': 'Rule-Based Engine',
            'summary': "No financial records found for this period. Add your income, expenses, or load demo data to receive personalized insights.",
            'top_concern': "No data available yet.",
            'suggestions': [
                "Start by recording your primary monthly income source in the Income tab.",
                "Log your daily essential expenses (Rent, Food, Transport).",
                "Set monthly budget thresholds to track your spending limits."
            ],
            'budget_recommendation': "A classic rule of thumb is the 50/30/20 budget: 50% for Needs, 30% for Wants, and 20% for Savings.",
            'emergency_fund_guidance': "Aim to accumulate 3 to 6 months worth of essential living expenses in an accessible, low-risk account as an emergency cushion.",
            'health_summary': "Begin tracking transactions today to build an accurate financial profile.",
            'disclaimer': DISCLAIMER_TEXT
        }

    # Attempt Gemini AI generation if API key is present
    api_key = Config.GEMINI_API_KEY
    if api_key and api_key != 'your_gemini_api_key_here' and len(api_key) > 5:
        try:
            ai_result = _call_gemini_api(api_key, user.name, summary, budget_data, goals)
            if ai_result:
                # Store AI recommendation record
                try:
                    rec_entry = AIRecommendation(
                        user_id=user.id,
                        recommendation=json.dumps(ai_result)
                    )
                    db.session.add(rec_entry)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    logger.warning(f"Could not persist AI recommendation: {e}")
                return ai_result
        except Exception as e:
            logger.warning(f"Gemini API request failed: {e}. Falling back to rule-based engine.")

    # Rule-based fallback system
    fallback_result = _generate_rule_based_advice(user.name, summary, budget_data, goals)
    
    # Store fallback recommendation record
    try:
        rec_entry = AIRecommendation(
            user_id=user.id,
            recommendation=json.dumps(fallback_result)
        )
        db.session.add(rec_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.warning(f"Could not persist fallback recommendation: {e}")

    return fallback_result

def _call_gemini_api(api_key, user_name, summary, budget_data, goals):
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Prepare structured user prompt
    categories_str = "\n".join([f"- {c['category']}: ₹{c['amount']:,.2f} ({c['percentage']}%)" for c in summary['category_list']])
    budgets_str = "\n".join([f"- {b['category']}: Limit ₹{b['limit']:,.2f}, Spent ₹{b['spent']:,.2f} ({b['status']})" for b in budget_data['items']])
    goals_str = "\n".join([f"- {g.name}: Target ₹{g.target_amount:,.2f}, Saved ₹{g.current_amount:,.2f} ({g.progress_percentage}% completed)" for g in goals])

    prompt = f"""You are a personal financial advisor assistant for {user_name}.
Analyze the user's REAL financial data for this month:

Monthly Income: ₹{summary['total_income']:,.2f}
Monthly Expenses: ₹{summary['total_expenses']:,.2f}
Net Savings: ₹{summary['total_savings']:,.2f}
Savings Rate: {summary['savings_rate']}%

Expense Breakdown:
{categories_str or 'No specific category recorded'}

Budget Status:
{budgets_str or 'No budget limits configured'}

Savings Goals:
{goals_str or 'No active savings goals'}

CRITICAL RULES:
1. ONLY analyze the exact data supplied above. Do NOT invent transactions or hypothetical numbers.
2. Provide practical, supportive, realistic fintech recommendations.
3. Return your response in STRICT JSON format with the following keys:
{{
  "spending_summary": "1-2 sentences summarizing income vs spending",
  "top_concern": "The single most notable spending or budget concern",
  "suggestions": ["Practical saving suggestion 1", "Practical saving suggestion 2", "Practical saving suggestion 3"],
  "budget_recommendation": "Specific recommendations for adjusting or setting category budgets",
  "emergency_fund_guidance": "Educational guidance on building an emergency reserve based on their expense level",
  "health_summary": "A concise assessment of their overall financial posture"
}}
"""

    response = model.generate_content(prompt)
    raw_text = response.text.strip()
    
    # Strip markdown code blocks if Gemini returns ```json ... ```
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
    raw_text = raw_text.strip()

    parsed = json.loads(raw_text)

    return {
        'is_ai': True,
        'source': 'Gemini AI (1.5 Flash)',
        'summary': parsed.get('spending_summary', 'Spending analysis complete.'),
        'top_concern': parsed.get('top_concern', 'Maintain mindful spending across discretionary categories.'),
        'suggestions': parsed.get('suggestions', [
            'Track recurring subscriptions and trim unused memberships.',
            'Plan weekly grocery lists to limit dining out.',
            'Direct savings into a separate account on salary day.'
        ]),
        'budget_recommendation': parsed.get('budget_recommendation', 'Align budgets with 50/30/20 guidelines.'),
        'emergency_fund_guidance': parsed.get('emergency_fund_guidance', 'Build an emergency fund covering 3-6 months of expenses.'),
        'health_summary': parsed.get('health_summary', 'Good overall trajectory with steady discipline.'),
        'disclaimer': DISCLAIMER_TEXT
    }

def _generate_rule_based_advice(user_name, summary, budget_data, goals):
    income = summary['total_income']
    expenses = summary['total_expenses']
    savings = summary['total_savings']
    savings_rate = summary['savings_rate']
    top_cat = summary['top_category']
    top_amt = summary['top_category_amount']
    top_pct = round((top_amt / expenses * 100.0), 1) if expenses > 0 else 0.0

    # 1. Spending Summary
    if expenses > income:
        summary_text = f"Your expenses (₹{expenses:,.2f}) exceed your monthly income (₹{income:,.2f}) by ₹{abs(savings):,.2f}. Reviewing your largest spending categories is strongly recommended."
    elif savings_rate >= 25:
        summary_text = f"You are doing exceptionally well! You saved ₹{savings:,.2f} this month, achieving a high {savings_rate}% savings rate."
    elif savings_rate >= 10:
        summary_text = f"You recorded a positive net savings of ₹{savings:,.2f} ({savings_rate}% savings rate) out of your ₹{income:,.2f} income."
    else:
        summary_text = f"Your total expenses reached ₹{expenses:,.2f}, leaving ₹{savings:,.2f} ({savings_rate}%) in net savings. Tightening variable expenses will give you more breathing room."

    # 2. Top Concern & Overspending Detection
    over_budget_items = [b for b in budget_data['items'] if b['status'] == 'Over Budget']
    near_budget_items = [b for b in budget_data['items'] if b['status'] == 'Near Budget Limit']

    if over_budget_items:
        first_ob = over_budget_items[0]
        over_by = first_ob['spent'] - first_ob['limit']
        top_concern = f"You have exceeded your {first_ob['category']} budget by ₹{over_by:,.2f} (Spent ₹{first_ob['spent']:,.2f} vs Limit ₹{first_ob['limit']:,.2f})."
    elif expenses > income:
        top_concern = f"Your spending is currently outpacing your income by ₹{abs(savings):,.2f}."
    elif top_cat:
        top_concern = f"Your largest expense category is {top_cat}, representing {top_pct}% (₹{top_amt:,.2f}) of your total monthly expenditures."
    else:
        top_concern = "No major spending bottlenecks detected this period."

    # 3. Three Practical Saving Suggestions
    suggestions = []
    if top_cat:
        suggestions.append(f"Reducing {top_cat} spending by 10% (approx. ₹{round(top_amt * 0.1, 0):,.0f}) would boost your monthly savings directly.")
    else:
        suggestions.append("Keep a strict record of recurring incidental purchases to identify hidden leaks.")

    if near_budget_items:
        nb = near_budget_items[0]
        suggestions.append(f"Your {nb['category']} spending is at {nb['percentage']}% of limit. Pause non-essential purchases here until next month.")
    elif savings_rate < 15:
        suggestions.append("Apply the 24-hour rule before making non-essential purchases over ₹1,000 to eliminate impulse buying.")
    else:
        suggestions.append("Automate a transfer of 15% of your income into savings right when you receive your earnings.")

    if goals:
        closest_goal = min(goals, key=lambda g: g.remaining_amount)
        if closest_goal.remaining_amount > 0:
            suggestions.append(f"Allocate an extra ₹{min(1500, int(closest_goal.remaining_amount))} this month toward your '{closest_goal.name}' goal to reach it faster.")
        else:
            suggestions.append("Celebrate reaching your savings milestone and create a new long-term financial goal.")
    else:
        suggestions.append("Create a dedicated Savings Goal in the app (e.g., Emergency Fund or Tech Upgrade) to stay motivated.")

    # 4. Budget Recommendation
    if income > 0:
        recommended_needs = round(income * 0.50, 0)
        recommended_wants = round(income * 0.30, 0)
        recommended_savings = round(income * 0.20, 0)
        budget_rec = f"Based on your ₹{income:,.2f} income, an ideal 50/30/20 allocation is ₹{recommended_needs:,.2f} for Essentials, ₹{recommended_wants:,.2f} for Lifestyle, and ₹{recommended_savings:,.2f} for Savings."
    else:
        budget_rec = "Set realistic monthly limits for your top 3 expense categories once income is added."

    # 5. Emergency Fund Guidance
    target_emergency = expenses * 3 if expenses > 0 else 30000.0
    emergency_guidance = (
        f"A sound financial foundation starts with an emergency reserve of 3 to 6 months of expenses (approximately ₹{target_emergency:,.2f}). "
        "Keep this fund in a secure, liquid bank account separate from your daily checking account."
    )

    # 6. Health Summary
    if savings_rate >= 20 and not over_budget_items:
        health_summary = "Healthy financial discipline! You have strong savings and spend within planned limits."
    elif savings_rate >= 10:
        health_summary = "Stable financial trajectory. Addressing any near-limit categories will secure higher savings."
    else:
        health_summary = "Caution advised. Reducing discretionary expenses will help improve your savings margin."

    return {
        'is_ai': False,
        'source': 'Automated Financial Rule Engine',
        'notice': 'AI service unavailable — showing automated financial insights instead.',
        'summary': summary_text,
        'top_concern': top_concern,
        'suggestions': suggestions,
        'budget_recommendation': budget_rec,
        'emergency_fund_guidance': emergency_guidance,
        'health_summary': health_summary,
        'disclaimer': DISCLAIMER_TEXT
    }
