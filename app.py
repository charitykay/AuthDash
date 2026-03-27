# app.py — Flask Application (Main Entry Point) — IMPROVED VERSION
# ============================================================================
# IMPROVEMENTS IN THIS VERSION:
# 1. Added Flask-Limiter for rate limiting on /login and /register
# 2. Added /security-settings POST handler that actually updates password
# 3. Integrated change_password() function from auth.py
# 
# Note: Copy only the MODIFIED sections from this file to your existing app.py
# This file shows: imports, rate limiter setup, and new/modified routes
# ============================================================================

import os
import logging
import flask
from flask_wtf import CSRFProtect
from flask_limiter import Limiter  # NEW: Import rate limiter
from flask_limiter.util import get_remote_address  # NEW: Get client IP for rate limiting
from database import create_table, get_profile, save_profile, get_settings, save_settings
from auth import register_user, login_user, change_password  

# ────────────────────────────────────────────────────────────────────────────
# LOGGING SETUP
# ────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────────────
# FLASK APP FACTORY
# ────────────────────────────────────────────────────────────────────────────

app = flask.Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or "secret123"

# ────────────────────────────────────────────────────────────────────────────
# SECURITY CONFIGURATION
# ────────────────────────────────────────────────────────────────────────────

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
    PERMANENT_SESSION_LIFETIME=1800,
    WTF_CSRF_TIME_LIMIT=3600,
)

# ────────────────────────────────────────────────────────────────────────────
# RATE LIMITING SETUP — NEW IMPROVEMENT #2
# ────────────────────────────────────────────────────────────────────────────
# Rate limiting prevents brute force attacks by limiting request frequency
# per IP address. For example:
#   - /login: Max 5 attempts per minute
#   - /register: Max 3 attempts per minute
#
# How it works:
#   1. get_remote_address() extracts client IP from request
#   2. Limiter tracks requests per IP address
#   3. If limit exceeded, returns 429 error automatically
#   4. Limit resets after specified time window
#
# Configuration:
#   - default_limits: Global limits for all routes not explicitly limited
#   - storage_uri: In-memory storage (good for single-server development)
#   - key_func: Function to identify client (by IP address)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,  # Limit by IP address
    default_limits=["200 per day", "50 per hour"],  # Global limits
    storage_uri="memory://"  # Store in memory (single process)
)

# For production with multiple servers, use Redis:
# storage_uri="redis://localhost:6379"

# ────────────────────────────────────────────────────────────────────────────
# CSRF PROTECTION (Currently Disabled)
# ────────────────────────────────────────────────────────────────────────────

# csrf = CSRFProtect(app)

# ────────────────────────────────────────────────────────────────────────────
# DATABASE INITIALIZATION
# ────────────────────────────────────────────────────────────────────────────

try:
    create_table()
    logger.info("Database initialized successfully.")
except Exception as e:
    logger.critical("Database initialization failed: %s", e)
    raise

# ────────────────────────────────────────────────────────────────────────────
# LOGIN_REQUIRED DECORATOR (Same as before)
# ────────────────────────────────────────────────────────────────────────────

def login_required(f):
    """Decorator to protect routes requiring logged-in user."""
    from functools import wraps
    
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in flask.session:
            return flask.redirect(flask.url_for("login"))
        return f(*args, **kwargs)
    
    return decorated

# ════════════════════════════════════════════════════════════════════════════
# ROUTES — KEY SECTIONS TO MODIFY IN YOUR app.py
# ════════════════════════════════════════════════════════════════════════════

# ────────────────────────────────────────────────────────────────────────────
# HOME ROUTE (No changes)
# ────────────────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    """Redirect home to login page."""
    return flask.redirect(flask.url_for("login"))


# ────────────────────────────────────────────────────────────────────────────
# REGISTRATION ROUTE — ADD RATE LIMITING
# ────────────────────────────────────────────────────────────────────────────
# CHANGE THIS LINE (around line 201 in your app.py):
#   FROM: @app.route("/register", methods=["GET", "POST"])
#   TO:   @app.route("/register", methods=["GET", "POST"])
#         @limiter.limit("3 per minute")  # Add this line

@app.route("/register", methods=["GET", "POST"])
@limiter.limit("3 per minute")  # NEW: Max 3 registration attempts per minute
def register():
    """
    Registration route with rate limiting.
    
    GET: Show registration form
    POST: Process registration (with rate limiting)
    
    Rate Limiting:
        - Max 3 registration attempts per minute per IP
        - After 3 attempts: Returns 429 Too Many Requests
        - Prevents spam and automated account creation
    
    Security:
        - Passwords validated (8+ chars, 1 uppercase, 1 digit)
        - Usernames must be 3-30 characters
        - Duplicate usernames prevented by database UNIQUE constraint
    """
    if flask.request.method == "GET":
        return flask.render_template("register.html")
    
    # POST: Process registration
    username = flask.request.form.get("username", "").strip()
    password = flask.request.form.get("password", "").strip()
    confirm = flask.request.form.get("confirm_password", "").strip()
    
    # Validation (same as before)
    if not username or not password or not confirm:
        flask.flash("All fields required", "error")
        return flask.redirect(flask.url_for("register"))
    
    if password != confirm:
        flask.flash("Passwords do not match", "error")
        return flask.redirect(flask.url_for("register"))
    
    # Attempt registration
    if register_user(username, password):
        flask.flash("Registration successful! Please log in.", "success")
        return flask.redirect(flask.url_for("login"))
    else:
        flask.flash("Username already taken", "error")
        return flask.redirect(flask.url_for("register"))


# ────────────────────────────────────────────────────────────────────────────
# LOGIN ROUTE — ADD RATE LIMITING
# ────────────────────────────────────────────────────────────────────────────
# CHANGE THIS LINE (around line 234 in your app.py):
#   FROM: @app.route("/login", methods=["GET", "POST"])
#   TO:   @app.route("/login", methods=["GET", "POST"])
#         @limiter.limit("5 per minute")  # Add this line

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")  # NEW: Max 5 login attempts per minute
def login():
    """
    Login route with rate limiting.
    
    GET: Show login form
    POST: Process login attempt (with rate limiting)
    
    Rate Limiting:
        - Max 5 login attempts per minute per IP
        - After 5 attempts: Returns 429 Too Many Requests
        - Prevents brute force password guessing attacks
    
    Attack Scenario Prevented:
        Attacker tries to guess password by attempting 100 logins per minute
        With rate limiting: Limited to 5 attempts, effectively slows brute force
    
    Session Management:
        - On successful login: Creates session lasting 30 minutes
        - Session survives page refreshes, browser tabs, etc.
        - Session expires after 30 minutes of inactivity
    """
    if flask.request.method == "GET":
        return flask.render_template("login.html")
    
    # POST: Process login
    username = flask.request.form.get("username", "").strip()
    password = flask.request.form.get("password", "").strip()
    
    if not username or not password:
        flask.flash("Username and password required", "error")
        return flask.redirect(flask.url_for("login"))
    
    # Verify credentials
    user = login_user(username, password)
    
    if user:
        # Login successful - create session
        flask.session["user_id"] = user[0]
        flask.session["username"] = username
        flask.session.permanent = True
        app.permanent_session_lifetime = 1800  # 30 minutes
        
        logger.info(f"User {username} logged in successfully")
        flask.flash(f"Welcome, {username}!", "success")
        return flask.redirect(flask.url_for("dashboard"))
    else:
        # Login failed - generic error message (security: don't reveal if user exists)
        logger.warning(f"Failed login attempt for username: {username}")
        flask.flash("Invalid username or password", "error")
        return flask.redirect(flask.url_for("login"))


# ────────────────────────────────────────────────────────────────────────────
# SIGNOUT ROUTE (No changes needed)
# ────────────────────────────────────────────────────────────────────────────
@app.route("/signout")
@login_required
def signout():
    """Sign out user and clear session."""
    username = flask.session.get("username", "User")
    flask.session.clear()
    logger.info(f"User {username} signed out")
    flask.flash("Signed out successfully", "success")
    return flask.redirect(flask.url_for("login"))
# ────────────────────────────────────────────────────────────────────────────
# DASHBOARD ROUTE (No changes needed)
# ────────────────────────────────────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    """Show user dashboard."""
    username = flask.session["username"]
    user_id = flask.session["user_id"]
    
    profile = get_profile(user_id)
    
    return flask.render_template(
        "dashboard.html",
        username=username,
        profile=profile
    )


# ────────────────────────────────────────────────────────────────────────────
# SECURITY SETTINGS ROUTE — NEW IMPROVEMENT #1 (Password Change Implementation)
# ────────────────────────────────────────────────────────────────────────────
# REPLACE YOUR EXISTING /security-settings route with this version
# This version ACTUALLY changes the password instead of just accepting the form

@app.route("/security-settings", methods=["GET", "POST"])
@login_required
@limiter.limit("5 per minute")  # NEW: Rate limit password change attempts
def security_settings():
    """
    Security settings page with password change functionality.
    
    GET: Show security settings form
    POST: Process password change request
    
    Features:
        1. Change password (with old password verification)
        2. View 2FA status (demo - not fully functional)
        3. See login activity (demo - not functional)
    
    Password Change Flow (NEW):
        1. User enters current password, new password, confirm password
        2. Route validates fields are filled
        3. Route validates new passwords match
        4. Route calls change_password() function
        5. change_password() verifies old password and updates database
        6. User sees success/error message
    
    Security:
        - Old password must match (prevents account takeover)
        - New password must meet requirements (8+ chars, 1 upper, 1 digit)
        - New password must differ from old (prevents accidental reuse)
        - All operations logged
        - Rate limited to 5 attempts per minute (prevent brute force)
    
    Rate Limiting Purpose:
        If password change route not limited, attacker could try thousands
        of old passwords in short time. With rate limiting, slows attack
        significantly.
    """
    if flask.request.method == "GET":
        # Show security settings form
        username = flask.session["username"]
        return flask.render_template(
            "security-settings.html",
            username=username
        )
    
    # POST: Process password change
    user_id = flask.session.get("user_id")
    
    # Step 1: Get form data
    old_password = flask.request.form.get("current_password", "").strip()
    new_password = flask.request.form.get("new_password", "").strip()
    confirm_password = flask.request.form.get("confirm_password", "").strip()
    
    # Step 2: Validate form data exists
    if not old_password or not new_password or not confirm_password:
        flask.flash("All password fields are required", "error")
        return flask.redirect(flask.url_for("security_settings"))
    
    # Step 3: Verify new passwords match
    if new_password != confirm_password:
        flask.flash("New passwords do not match", "error")
        return flask.redirect(flask.url_for("security_settings"))
    
    # Step 4: Call password change function from auth.py
    # This function handles all the security validation
    result = change_password(user_id, old_password, new_password)
    
    # Step 5: Flash result message and redirect
    if result['success']:
        flask.flash(result['message'], "success")
        logger.info(f"User {flask.session['username']} changed password successfully")
    else:
        flask.flash(result['message'], "error")
        logger.warning(f"Failed password change for user {flask.session['username']}: {result['message']}")
    
    return flask.redirect(flask.url_for("security_settings"))


# ────────────────────────────────────────────────────────────────────────────
# OTHER ROUTES (EDIT PROFILE, NOTIFICATIONS, HELP) — No changes for rate limiting
# ────────────────────────────────────────────────────────────────────────────
# Your existing routes continue to work. Copy the relevant ones from your
# current app.py if you need them (edit-profile, notifications, help-support)

@app.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    """Edit user profile page."""
    user_id = flask.session["user_id"]
    username = flask.session["username"]
    
    if flask.request.method == "GET":
        profile = get_profile(user_id)
        return flask.render_template(
            "edit-profile.html",
            username=username,
            profile=profile
        )
    
    # POST: Update profile
    full_name = flask.request.form.get("full_name", "").strip()
    email = flask.request.form.get("email", "").strip()
    bio = flask.request.form.get("bio", "").strip()
    
    # Pass arguments individually, not as dictionary
    if save_profile(user_id, full_name, email, bio):
        flask.flash("Profile updated successfully!", "success")
    else:
        flask.flash("Failed to update profile", "error")
    
    return flask.redirect(flask.url_for("edit_profile"))


@app.route("/notifications", methods=["GET", "POST"])
@login_required
def notifications():
    """Notification preferences page."""
    user_id = flask.session["user_id"]
    username = flask.session["username"]
    
    if flask.request.method == "GET":
        settings = get_settings(user_id)
        return flask.render_template(
            "notifications.html",
            username=username,
            settings=settings
        )
    
    # POST: Update settings
    email_notifications = flask.request.form.get("email_notifications") == "on"
    push_notifications = flask.request.form.get("push_notifications") == "on"
    marketing_emails = flask.request.form.get("marketing_emails") == "on"
    
    settings_data = {
        "email_notifications": email_notifications,
        "push_notifications": push_notifications,
        "marketing_emails": marketing_emails
    }
    
    if save_settings(user_id, settings_data):
        flask.flash("Notification settings updated!", "success")
    else:
        flask.flash("Failed to update settings", "error")
    
    return flask.redirect(flask.url_for("notifications"))


@app.route("/help-support")
@login_required
def help_support():
    """Help and support page."""
    faq_items = [
        {
            "question": "How do I reset my password?",
            "answer": "Go to Security Settings and click 'Change Password'. Follow the instructions to set a new password."
        },
        {
            "question": "How can I enable two-factor authentication?",
            "answer": "Visit Security Settings and enable 2FA. You'll receive a code via email or authenticator app."
        },
        {
            "question": "How do I delete my account?",
            "answer": "Contact our support team at support@example.com with your request."
        },
        {
            "question": "Where can I view my activity logs?",
            "answer": "Go to Security Settings to view your recent login activity and device history."
        },
    ]
    
    return flask.render_template(
        "help-support.html",
        username=flask.session["username"],
        faq=faq_items
    )


# ────────────────────────────────────────────────────────────────────────────
# ERROR HANDLERS (No changes)
# ────────────────────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    """Handle 404 Not Found errors."""
    return flask.render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 Internal Server Error."""
    logger.error("Internal server error: %s", e)
    return flask.render_template("500.html"), 500


@app.errorhandler(429)
def ratelimit_handler(e):
    """
    Handle rate limit exceeded errors (NEW).
    
    When a user exceeds rate limit (e.g., too many login attempts),
    Flask-Limiter triggers this handler.
    
    Shows friendly error message instead of bare 429 status code.
    """
    flask.flash("Too many requests. Please wait a moment and try again.", "error")
    return flask.redirect(flask.url_for("login")), 429


# ────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_ENV") != "production"
    logger.info("Starting Flask app (debug=%s)...", debug_mode)
    app.run(debug=debug_mode)
