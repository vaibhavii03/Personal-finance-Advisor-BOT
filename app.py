import os
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"

from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user
from config import Config
from models.models import db, User
from routes import (
    auth_bp,
    dashboard_bp,
    income_bp,
    expenses_bp,
    budget_bp,
    savings_bp,
    advisor_bp,
    reports_bp
)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(income_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(savings_bp)
    app.register_blueprint(advisor_bp)
    app.register_blueprint(reports_bp)

    # Public Landing Page route
    @app.route('/')
    def landing():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.dashboard_view'))
        return render_template('index.html')

    # Custom Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    # Custom Jinja filters & context processors
    @app.template_filter('currency')
    def currency_filter(val):
        try:
            return f"₹{float(val):,.2f}"
        except (ValueError, TypeError):
            return "₹0.00"

    @app.context_processor
    def inject_global_data():
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return {
            'app_name': Config.APP_NAME,
            'app_subtitle': Config.APP_SUBTITLE,
            'current_year': now.year,
            'current_month': now.month,
            'current_month_name': now.strftime('%B %Y')
        }

    # Ensure tables exist
    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
