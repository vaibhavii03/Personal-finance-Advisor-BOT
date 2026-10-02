import os
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"

import unittest
from datetime import date
from app import create_app
from config import Config
from models.models import db, User, Income, Expense, Budget, SavingsGoal, AIRecommendation
from services.finance_service import load_demo_data, get_monthly_summary, get_budget_status, calculate_financial_health_score
from services.ai_service import generate_financial_advice

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'

class FinanceAdvisorTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def register_and_login(self, name="Alex Student", email="alex@example.com", password="password123"):
        self.client.post('/register', data={
            'name': name,
            'email': email,
            'password': password,
            'confirm_password': password
        }, follow_redirects=True)
        return self.client.post('/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)

    def test_landing_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Your Personal AI Finance Advisor', response.data)
        self.assertIn(b'Income Tracking', response.data)
        self.assertIn(b'Smart Budgeting', response.data)

    def test_auth_workflow(self):
        # Register user
        reg_res = self.client.post('/register', data={
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'secretpassword',
            'confirm_password': 'secretpassword'
        }, follow_redirects=True)
        self.assertEqual(reg_res.status_code, 200)
        self.assertIn(b'Test User', reg_res.data)

        # Logout
        logout_res = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(logout_res.status_code, 200)

        # Login
        login_res = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'secretpassword'
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b'Good', login_res.data)

    def test_demo_data_loading(self):
        self.register_and_login()
        user = User.query.filter_by(email="alex@example.com").first()
        self.assertIsNotNone(user)

        # Load demo data
        resp = self.client.post('/dashboard/load-demo', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # Verify database entities populated
        incomes = Income.query.filter_by(user_id=user.id).all()
        expenses = Expense.query.filter_by(user_id=user.id).all()
        budgets = Budget.query.filter_by(user_id=user.id).all()
        goals = SavingsGoal.query.filter_by(user_id=user.id).all()

        total_income = sum(i.amount for i in incomes)
        total_expense = sum(e.amount for e in expenses)

        self.assertEqual(total_income, 30000.0)
        self.assertEqual(total_expense, 22000.0)
        self.assertEqual(len(budgets), 8)
        self.assertEqual(len(goals), 3)

        # Test monthly summary calculation
        summary = get_monthly_summary(user.id)
        self.assertEqual(summary['total_income'], 30000.0)
        self.assertEqual(summary['total_expenses'], 22000.0)
        self.assertEqual(summary['total_savings'], 8000.0)
        self.assertEqual(summary['savings_rate'], 26.7)

        # Test health score calculation
        score = calculate_financial_health_score(user.id)
        self.assertGreater(score['score'], 60)

    def test_income_crud(self):
        self.register_and_login()
        user = User.query.filter_by(email="alex@example.com").first()

        # Add Income
        add_res = self.client.post('/income/add', data={
            'source': 'Salary',
            'amount': '35000.00',
            'date': date.today().strftime('%Y-%m-%d'),
            'description': 'Main salary paycheck'
        }, follow_redirects=True)
        self.assertEqual(add_res.status_code, 200)

        inc = Income.query.filter_by(user_id=user.id).first()
        self.assertIsNotNone(inc)
        self.assertEqual(inc.amount, 35000.00)

        # Edit Income
        edit_res = self.client.post(f'/income/edit/{inc.id}', data={
            'source': 'Salary',
            'amount': '40000.00',
            'date': date.today().strftime('%Y-%m-%d'),
            'description': 'Updated salary with bonus'
        }, follow_redirects=True)
        self.assertEqual(edit_res.status_code, 200)

        db.session.refresh(inc)
        self.assertEqual(inc.amount, 40000.00)

        # Delete Income
        del_res = self.client.post(f'/income/delete/{inc.id}', follow_redirects=True)
        self.assertEqual(del_res.status_code, 200)
        self.assertIsNone(Income.query.get(inc.id))

    def test_expenses_crud_and_filters(self):
        self.register_and_login()
        user = User.query.filter_by(email="alex@example.com").first()

        # Add Expense
        add_res = self.client.post('/expenses/add', data={
            'category': 'Food',
            'amount': '450.00',
            'date': date.today().strftime('%Y-%m-%d'),
            'description': 'Campus cafeteria lunch'
        }, follow_redirects=True)
        self.assertEqual(add_res.status_code, 200)

        exp = Expense.query.filter_by(user_id=user.id).first()
        self.assertIsNotNone(exp)
        self.assertEqual(exp.amount, 450.00)

        # Filter expenses
        filter_res = self.client.get('/expenses?category=Food')
        self.assertEqual(filter_res.status_code, 200)
        self.assertIn(b'Campus cafeteria lunch', filter_res.data)

        # Edit Expense
        edit_res = self.client.post(f'/expenses/edit/{exp.id}', data={
            'category': 'Food',
            'amount': '500.00',
            'date': date.today().strftime('%Y-%m-%d'),
            'description': 'Campus cafeteria lunch + snack'
        }, follow_redirects=True)
        self.assertEqual(edit_res.status_code, 200)

        db.session.refresh(exp)
        self.assertEqual(exp.amount, 500.00)

        # Delete Expense
        del_res = self.client.post(f'/expenses/delete/{exp.id}', follow_redirects=True)
        self.assertEqual(del_res.status_code, 200)
        self.assertIsNone(Expense.query.get(exp.id))

    def test_budget_workflow(self):
        self.register_and_login()
        user = User.query.filter_by(email="alex@example.com").first()

        # Set Budget
        res = self.client.post('/budget/set', data={
            'category': 'Food',
            'limit_amount': '3000.00',
            'month': date.today().month,
            'year': date.today().year
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        b = Budget.query.filter_by(user_id=user.id, category='Food').first()
        self.assertIsNotNone(b)
        self.assertEqual(b.limit_amount, 3000.00)

        # Add expense exceeding budget
        self.client.post('/expenses/add', data={
            'category': 'Food',
            'amount': '3500.00',
            'date': date.today().strftime('%Y-%m-%d'),
            'description': 'Bulk grocery run'
        }, follow_redirects=True)

        budget_status = get_budget_status(user.id)
        food_item = next(item for item in budget_status['items'] if item['category'] == 'Food')
        self.assertEqual(food_item['status'], 'Over Budget')

    def test_savings_goals(self):
        self.register_and_login()
        user = User.query.filter_by(email="alex@example.com").first()

        # Create Goal
        self.client.post('/savings/add', data={
            'name': 'New Laptop',
            'target_amount': '50000.00',
            'current_amount': '15000.00',
            'deadline': date.today().strftime('%Y-%m-%d')
        }, follow_redirects=True)

        goal = SavingsGoal.query.filter_by(user_id=user.id).first()
        self.assertIsNotNone(goal)
        self.assertEqual(goal.progress_percentage, 30.0)
        self.assertEqual(goal.remaining_amount, 35000.0)

        # Add funds
        self.client.post(f'/savings/add-funds/{goal.id}', data={
            'amount': '5000.00'
        }, follow_redirects=True)

        db.session.refresh(goal)
        self.assertEqual(goal.current_amount, 20000.00)
        self.assertEqual(goal.progress_percentage, 40.0)

    def test_ai_advisor_fallback(self):
        self.register_and_login()
        user = User.query.filter_by(email="alex@example.com").first()
        load_demo_data(user.id)

        # Generate advice (should use rule-based fallback without crash if no API key)
        advice = generate_financial_advice(user)
        self.assertIn('summary', advice)
        self.assertIn('suggestions', advice)
        self.assertIn('disclaimer', advice)
        self.assertGreaterEqual(len(advice['suggestions']), 3)

        # Check advisor page loads
        adv_res = self.client.get('/advisor')
        self.assertEqual(adv_res.status_code, 200)
        self.assertIn(b'AI Financial Advisor', adv_res.data)

    def test_reports_and_transactions(self):
        self.register_and_login()
        user = User.query.filter_by(email="alex@example.com").first()
        load_demo_data(user.id)

        rep_res = self.client.get('/reports')
        self.assertEqual(rep_res.status_code, 200)
        self.assertIn(b'Monthly Financial Report', rep_res.data)
        self.assertIn(b'Personal Finance Statement', rep_res.data)

        tx_res = self.client.get('/transactions')
        self.assertEqual(tx_res.status_code, 200)
        self.assertIn(b'Unified Transaction History', tx_res.data)

if __name__ == '__main__':
    unittest.main()
