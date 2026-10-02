from datetime import datetime, date, timedelta, timezone
from sqlalchemy import func, extract
from models.models import db, Income, Expense, Budget, SavingsGoal, AIRecommendation

CATEGORIES = [
    'Food',
    'Transport',
    'Rent',
    'Education',
    'Shopping',
    'Entertainment',
    'Healthcare',
    'Bills',
    'Travel',
    'Other'
]

INCOME_SOURCES = [
    'Salary',
    'Freelance',
    'Allowance',
    'Scholarship',
    'Part-time work',
    'Investments',
    'Other'
]

def get_current_period():
    now = datetime.now(timezone.utc)
    return now.month, now.year

def get_monthly_summary(user_id, month=None, year=None):
    current_m, current_y = get_current_period()
    month = int(month) if month else current_m
    year = int(year) if year else current_y

    # Calculate Total Income for the month
    income_query = db.session.query(func.coalesce(func.sum(Income.amount), 0.0)).filter(
        Income.user_id == user_id,
        extract('month', Income.date) == month,
        extract('year', Income.date) == year
    ).scalar()
    total_income = float(income_query)

    # Calculate Total Expenses for the month
    expense_query = db.session.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
        Expense.user_id == user_id,
        extract('month', Expense.date) == month,
        extract('year', Expense.date) == year
    ).scalar()
    total_expenses = float(expense_query)

    # Total Savings and Savings Rate
    total_savings = total_income - total_expenses
    savings_rate = (total_savings / total_income * 100.0) if total_income > 0 else 0.0
    savings_rate = max(0.0, round(savings_rate, 1))

    # Category breakdown for the month
    category_rows = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('cat_total')
    ).filter(
        Expense.user_id == user_id,
        extract('month', Expense.date) == month,
        extract('year', Expense.date) == year
    ).group_by(Expense.category).order_by(func.sum(Expense.amount).desc()).all()

    category_breakdown = {}
    category_list = []
    top_category = None
    top_category_amount = 0.0

    for cat, amt in category_rows:
        amount = float(amt)
        category_breakdown[cat] = amount
        pct = (amount / total_expenses * 100.0) if total_expenses > 0 else 0.0
        category_list.append({
            'category': cat,
            'amount': amount,
            'percentage': round(pct, 1)
        })
        if amount > top_category_amount:
            top_category = cat
            top_category_amount = amount

    # Daily spending trend for current month
    daily_rows = db.session.query(
        Expense.date,
        func.sum(Expense.amount)
    ).filter(
        Expense.user_id == user_id,
        extract('month', Expense.date) == month,
        extract('year', Expense.date) == year
    ).group_by(Expense.date).order_by(Expense.date).all()

    daily_trend = [{'date': d.strftime('%d %b'), 'amount': float(amt)} for d, amt in daily_rows]

    # Past 6 months income vs expenses for bar chart
    six_months_data = []
    today = date.today()
    for i in range(5, -1, -1):
        target_date = today.replace(day=1) - timedelta(days=i * 28)
        m = target_date.month
        y = target_date.year
        month_label = target_date.strftime('%b %Y')

        m_inc = db.session.query(func.coalesce(func.sum(Income.amount), 0.0)).filter(
            Income.user_id == user_id,
            extract('month', Income.date) == m,
            extract('year', Income.date) == y
        ).scalar()

        m_exp = db.session.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(
            Expense.user_id == user_id,
            extract('month', Expense.date) == m,
            extract('year', Expense.date) == y
        ).scalar()

        six_months_data.append({
            'label': month_label,
            'month': m,
            'year': y,
            'income': float(m_inc),
            'expense': float(m_exp)
        })

    return {
        'month': month,
        'year': year,
        'month_name': date(year, month, 1).strftime('%B %Y'),
        'total_income': total_income,
        'total_expenses': total_expenses,
        'total_savings': total_savings,
        'savings_rate': savings_rate,
        'category_breakdown': category_breakdown,
        'category_list': category_list,
        'top_category': top_category,
        'top_category_amount': top_category_amount,
        'daily_trend': daily_trend,
        'six_months_data': six_months_data
    }

def get_budget_status(user_id, month=None, year=None):
    current_m, current_y = get_current_period()
    month = int(month) if month else current_m
    year = int(year) if year else current_y

    budgets = Budget.query.filter_by(user_id=user_id, month=month, year=year).all()

    # Get actual spending grouped by category for this month
    expenses = db.session.query(
        Expense.category,
        func.coalesce(func.sum(Expense.amount), 0.0).label('spent')
    ).filter(
        Expense.user_id == user_id,
        extract('month', Expense.date) == month,
        extract('year', Expense.date) == year
    ).group_by(Expense.category).all()

    spent_map = {cat: float(amt) for cat, amt in expenses}

    budget_items = []
    total_budgeted = 0.0
    total_budget_spent = 0.0
    over_budget_count = 0

    for b in budgets:
        spent = spent_map.get(b.category, 0.0)
        limit = b.limit_amount
        remaining = max(0.0, limit - spent)
        pct = (spent / limit * 100.0) if limit > 0 else 0.0

        total_budgeted += limit
        total_budget_spent += spent

        if spent > limit:
            status = 'Over Budget'
            status_class = 'danger'
            badge_icon = 'bi-exclamation-triangle-fill'
            over_budget_count += 1
        elif spent >= 0.85 * limit:
            status = 'Near Budget Limit'
            status_class = 'warning'
            badge_icon = 'bi-exclamation-circle-fill'
        else:
            status = 'Within Budget'
            status_class = 'success'
            badge_icon = 'bi-check-circle-fill'

        budget_items.append({
            'id': b.id,
            'category': b.category,
            'limit': limit,
            'spent': spent,
            'remaining': remaining,
            'percentage': round(pct, 1),
            'progress_bar_pct': min(round(pct, 1), 100.0),
            'status': status,
            'status_class': status_class,
            'badge_icon': badge_icon
        })

    budget_items.sort(key=lambda x: x['percentage'], reverse=True)

    return {
        'budget_list': budget_items,
        'items': budget_items,
        'total_budgeted': total_budgeted,
        'total_budget_spent': total_budget_spent,
        'over_budget_count': over_budget_count,
        'month': month,
        'year': year
    }

def calculate_financial_health_score(user_id, month=None, year=None):
    summary = get_monthly_summary(user_id, month, year)
    budget_data = get_budget_status(user_id, month, year)
    goals = SavingsGoal.query.filter_by(user_id=user_id).all()

    income = summary['total_income']
    expenses = summary['total_expenses']
    savings_rate = summary['savings_rate']

    # 1. Savings Rate Score (Max 35 pts)
    if savings_rate >= 25:
        score_savings = 35
    elif savings_rate >= 20:
        score_savings = 30
    elif savings_rate >= 10:
        score_savings = 22
    elif savings_rate > 0:
        score_savings = 12
    else:
        score_savings = 0

    # 2. Budget Adherence Score (Max 30 pts)
    items = budget_data['items']
    if not items:
        budget_adherence_pct = 75.0
        score_budget = 20  # Neutral if no budgets configured yet
    else:
        within_count = sum(1 for item in items if item['status'] == 'Within Budget')
        near_count = sum(1 for item in items if item['status'] == 'Near Budget Limit')
        budget_adherence_pct = round(((within_count + 0.5 * near_count) / len(items)) * 100.0, 1)
        score_budget = int(30 * (budget_adherence_pct / 100.0))

    # 3. Expense-to-Income Ratio Score (Max 25 pts)
    if income > 0:
        expense_ratio_pct = round((expenses / income) * 100.0, 1)
        if expense_ratio_pct <= 50:
            score_expense = 25
        elif expense_ratio_pct <= 70:
            score_expense = 20
        elif expense_ratio_pct <= 85:
            score_expense = 15
        elif expense_ratio_pct <= 100:
            score_expense = 8
        else:
            score_expense = 0
    else:
        expense_ratio_pct = 100.0 if expenses > 0 else 0.0
        score_expense = 10 if expenses == 0 else 0

    # 4. Savings Goals Progress Score (Max 10 pts)
    if goals:
        avg_progress = sum(g.progress_percentage for g in goals) / len(goals)
        score_goals = min(10, int(10 * (avg_progress / 100.0)))
    else:
        score_goals = 5

    total_score = max(5, min(100, score_savings + score_budget + score_expense + score_goals))

    if total_score >= 80:
        rating = 'Excellent'
        badge_class = 'success'
        summary_text = 'Strong financial health with solid savings habits and healthy budgeting.'
    elif total_score >= 65:
        rating = 'Good'
        badge_class = 'info'
        summary_text = 'Good financial balance. Minor adjustments to spending can boost your savings.'
    elif total_score >= 50:
        rating = 'Fair'
        badge_class = 'warning'
        summary_text = 'Moderate financial stability. Watch overspending in variable categories.'
    else:
        rating = 'Needs Attention'
        badge_class = 'danger'
        summary_text = 'Expenses are close to or exceeding income. Consider tightening discretionary budgets.'

    return {
        'score': total_score,
        'rating': rating,
        'badge_class': badge_class,
        'summary_text': summary_text,
        'savings_rate': savings_rate,
        'budget_adherence_pct': budget_adherence_pct,
        'expense_ratio_pct': expense_ratio_pct,
        'score_savings': score_savings,
        'score_budget': score_budget,
        'score_expense': score_expense,
        'score_goals': score_goals
    }

def load_demo_data(user_id):
    current_m, current_y = get_current_period()
    today = date.today()

    # Clear existing demo records for this user to make it idempotent
    Income.query.filter_by(user_id=user_id).delete()
    Expense.query.filter_by(user_id=user_id).delete()
    Budget.query.filter_by(user_id=user_id).delete()
    SavingsGoal.query.filter_by(user_id=user_id).delete()
    AIRecommendation.query.filter_by(user_id=user_id).delete()

    # Add Demo Incomes (Total: ₹30,000)
    incomes = [
        Income(user_id=user_id, source='Salary', amount=27000.0, date=today.replace(day=1), description='Monthly Tech Internship / Job Stipend'),
        Income(user_id=user_id, source='Freelance', amount=3000.0, date=today.replace(day=5), description='Web Design & Tutoring Project')
    ]

    # Add Demo Expenses (Total: ₹22,000)
    # Rent: 8000, Food: 4500, Transport: 2500, Education: 2000, Entertainment: 1500, Shopping: 1500, Healthcare: 1000, Other: 1000
    expenses = [
        Expense(user_id=user_id, category='Rent', amount=8000.0, date=today.replace(day=2), description='Monthly Apartment Share & Utilities'),
        Expense(user_id=user_id, category='Food', amount=3000.0, date=today.replace(day=4), description='Weekly Groceries & Meal Prep'),
        Expense(user_id=user_id, category='Food', amount=1500.0, date=today.replace(day=12), description='Campus Dining & Weekend Meals'),
        Expense(user_id=user_id, category='Transport', amount=2500.0, date=today.replace(day=6), description='Monthly Metro & Bus Transit Pass'),
        Expense(user_id=user_id, category='Education', amount=2000.0, date=today.replace(day=8), description='Online Certification Course & Books'),
        Expense(user_id=user_id, category='Entertainment', amount=1500.0, date=today.replace(day=10), description='Cinema & Streaming Subscriptions'),
        Expense(user_id=user_id, category='Shopping', amount=1500.0, date=today.replace(day=14), description='Clothing & Desk Accessories'),
        Expense(user_id=user_id, category='Healthcare', amount=1000.0, date=today.replace(day=16), description='Pharmacy & Health Checkup'),
        Expense(user_id=user_id, category='Other', amount=1000.0, date=today.replace(day=18), description='Household Sundries & Miscellaneous'),
    ]

    # Add Demo Budgets
    budgets = [
        Budget(user_id=user_id, category='Rent', limit_amount=8000.0, month=current_m, year=current_y),
        Budget(user_id=user_id, category='Food', limit_amount=5000.0, month=current_m, year=current_y),
        Budget(user_id=user_id, category='Transport', limit_amount=2500.0, month=current_m, year=current_y),
        Budget(user_id=user_id, category='Education', limit_amount=2500.0, month=current_m, year=current_y),
        Budget(user_id=user_id, category='Entertainment', limit_amount=1500.0, month=current_m, year=current_y),
        Budget(user_id=user_id, category='Shopping', limit_amount=2000.0, month=current_m, year=current_y),
        Budget(user_id=user_id, category='Healthcare', limit_amount=1500.0, month=current_m, year=current_y),
        Budget(user_id=user_id, category='Other', limit_amount=1200.0, month=current_m, year=current_y),
    ]

    # Add Demo Savings Goals
    savings_goals = [
        SavingsGoal(
            user_id=user_id,
            name='New Laptop',
            target_amount=50000.0,
            current_amount=30000.0,
            deadline=today + timedelta(days=120)
        ),
        SavingsGoal(
            user_id=user_id,
            name='Emergency Fund',
            target_amount=60000.0,
            current_amount=25000.0,
            deadline=today + timedelta(days=240)
        ),
        SavingsGoal(
            user_id=user_id,
            name='Summer Vacation Trip',
            target_amount=15000.0,
            current_amount=6000.0,
            deadline=today + timedelta(days=180)
        )
    ]

    for item in incomes + expenses + budgets + savings_goals:
        db.session.add(item)

    db.session.commit()
    return True
