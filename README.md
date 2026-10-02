# Personal Finance Advisor

> **"Understand your money. Plan smarter. Save better."**

An AI-powered full-stack personal finance management web application designed for students and young professionals to record income, track expenses, establish category budgets, track savings goals, inspect spending analytics, and receive personalized AI financial advice.

---

## 📌 Main Features

1. **Dashboard & Analytics:** Real-time calculation of Monthly Income, Monthly Expenses, Net Savings, and Savings Rate. Visual Chart.js charts (Category Breakdown Doughnut, 6-Month Income vs Expense Bar, Daily Spending Trend Line) and category budget progress bars.
2. **Financial Health Score:** An educational indicator (0–100) assessing savings rate, budget adherence, and expense-to-income ratio.
3. **Income Tracking:** Record earnings from Salary, Freelance, Allowance, Scholarships, or Part-time jobs with full CRUD capabilities.
4. **Expense Management:** Multi-category expense logging (Food, Transport, Rent, Education, Shopping, Entertainment, Healthcare, Bills, Travel, Other) with instant filtering by category, date range, amount, and search keywords.
5. **Smart Budgeting:** Set monthly category spending caps with dynamic status badges (**✓ Within Budget**, **⚠ Near Budget Limit**, and **⚠ Over Budget**).
6. **Savings Goals:** Create milestone targets (e.g. "Emergency Fund", "New Laptop", "Summer Vacation") with visual completion percentages, remaining amount tracking, and quick deposit functionality.
7. **AI Financial Advisor:** Powered by **Google Gemini AI** (with an automated rule-based engine fallback when an API key is absent or unreachable). Provides spending analysis, overspending detection, 3 practical saving suggestions, suggested budget adjustments, and emergency fund guidance.
8. **Monthly Reports & Transactions:** Detailed executive monthly statements with printable styling (`Ctrl+P` or "Print / Save PDF") and a unified chronological transaction history with color-coded inflow/outflow badges.
9. **One-Click Demo Data:** A built-in "Load Demo Data" button immediately seeds realistic sample data (Income: ₹30,000, Expenses: ₹22,000, Budgets, and Goals) for instant presentation and evaluation.
10. **Security & Authentication:** Session-based authentication via Flask-Login, Werkzeug password hashing, protected routes, and isolated user records.

---

## 🛠 Technology Stack

### Backend
- **Python 3.10+ / 3.14**
- **Flask** (Modular architecture with Blueprints)
- **SQLAlchemy & Flask-SQLAlchemy** (ORM)
- **SQLite** (Local database)
- **Flask-Login** (Session authentication & route protection)
- **python-dotenv** (Environment variable isolation)
- **Werkzeug** (Cryptographic security)

### Frontend
- **HTML5 & CSS3**
- **JavaScript (ES6+)**
- **Bootstrap 5.3** (Responsive design system)
- **Bootstrap Icons**
- **Chart.js 4.4** (Interactive financial visualizations)

### AI
- **Google Gemini API** (`google-generativeai`)
- Deterministic **Rule-Based Fallback Engine** ensuring 100% uptime even without an API key

---

## 📁 Project Structure

```
Personal-finance-Advisor/
│
├── app.py                      # Application factory and entry point
├── config.py                   # Configuration and environment loader
├── requirements.txt            # Python dependencies
├── .env                        # Active environment variables
├── .env.example                # Example environment variable template
├── README.md                   # Documentation and setup instructions
├── test_app.py                 # Automated test suite
│
├── models/
│   ├── __init__.py
│   └── models.py               # User, Income, Expense, Budget, SavingsGoal, AIRecommendation
│
├── routes/
│   ├── __init__.py
│   ├── auth.py                 # Login, Register, Logout, Profile
│   ├── dashboard.py            # Overview metrics, charts API, load demo data
│   ├── income.py               # Income CRUD
│   ├── expenses.py             # Expense CRUD & filtering
│   ├── budget.py               # Budget limit tracking & alerts
│   ├── savings.py              # Goals & fund allocation
│   ├── advisor.py              # AI advisory interface
│   └── reports.py              # Monthly reports & unified transaction ledger
│
├── services/
│   ├── __init__.py
│   ├── ai_service.py           # Gemini API integration & fallback rule engine
│   └── finance_service.py      # Aggregations, health scoring, demo seeder
│
├── templates/
│   ├── base.html               # Main layout with responsive sidebar and navbar
│   ├── index.html              # Public landing page
│   ├── login.html              # Authentication sign-in
│   ├── register.html           # User registration
│   ├── dashboard.html          # Financial KPI overview & charts
│   ├── income.html             # Income management
│   ├── expenses.html           # Expense management
│   ├── budget.html             # Budget management
│   ├── savings.html            # Savings goals
│   ├── advisor.html            # Conversational AI advisor
│   ├── reports.html            # Printable monthly statement
│   ├── transactions.html       # Unified ledger
│   ├── profile.html            # Profile & password updates
│   ├── 404.html                # Friendly Not Found error
│   └── 500.html                # Friendly Server Error
│
├── static/
│   ├── css/
│   │   └── style.css           # Modern FinTech design system
│   ├── js/
│   │   └── dashboard.js        # Chart.js initialization and interactivity
│   └── images/
│       └── logo.svg            # Finance + AI brand logo
│
└── instance/
    └── finance.db              # SQLite database (auto-generated)
```

---

## 🚀 Installation & Local Setup

### 1. Prerequisites
- Python 3.10 or higher installed on your machine.
- Git (optional, if cloning from GitHub).

### 2. Set Up a Virtual Environment (Recommended)

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Required Dependencies
```bash
python -m pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
Inside `.env`, configure your settings:
```ini
SECRET_KEY=financial-advisor-secret-key-2025-dev
FLASK_ENV=development
FLASK_DEBUG=True
DATABASE_URL=sqlite:///finance.db
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

> **Note:** If `GEMINI_API_KEY` is omitted or left empty, the application automatically activates its **Automated Financial Rule Engine**, ensuring all AI advisor features function seamlessly for grading and presentations!

### 5. Initialize Database & Run Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🤖 Configuring Google Gemini AI

1. Obtain a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Open your `.env` file in the project directory.
3. Update the key:
   ```ini
   GEMINI_API_KEY=AIzaSyYourGeneratedGeminiKeyHere...
   ```
4. Restart your Flask application.
5. Visit the **AI Advisor** (`/advisor`) page to receive real-time Gemini AI financial analysis!

---

## ⚡ Loading Demo Data (For Fast Presentations)

To immediately present the application with realistic numbers, charts, and budget limits:
1. Register a new user account at `/register` and sign in.
2. In the top notification banner or sidebar footer, click **"Load Demo Data"**.
3. The database will automatically seed:
   - **Income:** ₹30,000 (Salary: ₹27,000, Freelance: ₹3,000)
   - **Expenses:** ₹22,000 across Rent, Food, Transport, Education, Entertainment, Shopping, Healthcare, and Other
   - **Budgets:** 8 category limits with progress bars and alerts
   - **Savings Goals:** "New Laptop" (60% funded), "Emergency Fund", "Summer Vacation"
   - **Charts & Financial Health:** Instantly computes a 26.7% savings rate and a Financial Health Score.

---

## 🌐 Exposing Application via Ngrok (For Public / Remote Demo)

To share the application publicly or demo it on mobile devices without deploying to a cloud server:

1. Download and install [Ngrok](https://ngrok.com/).
2. Run your Flask app in one terminal:
   ```powershell
   python app.py
   ```
3. In a second terminal, launch Ngrok on port 5000:
   ```powershell
   ngrok http 5000
   ```
4. Copy the public forwarding URL (e.g. `https://xxxx-xx-xx.ngrok-free.app`) and share it with reviewers or test on your mobile device!

---

## 🧪 Running Automated Tests

Run the included unit test suite:
```powershell
python test_app.py
```
All tests verify authentication, income/expense CRUD, budget tracking, savings goals, demo data seeder, report generation, and AI fallback response.

---

## 🔮 Future Enhancements
- Recurring subscription and automatic bill alerts.
- Receipt OCR scanning for instant expense logging.
- Multi-currency conversions (USD, EUR, GBP, INR).
- CSV / Excel export and import for bank statements.

---

## 📄 License & Academic Note
Created for academic evaluation and project demonstration.
AI insights are provided for educational and personal budgeting planning purposes only and should not be considered certified investment advice.
