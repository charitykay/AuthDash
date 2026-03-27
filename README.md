# 🔐 AuthDash - User Authentication Dashboard

A beginner-friendly full-stack web application demonstrating user authentication, profile management, and responsive design using Flask, SQLite, and modern web technologies.

## 🎯 Technology Stack

- **Backend:** Flask 3.1.3 (Python Web Framework)
- **Database:** SQLite3
- **Frontend:** HTML5, CSS3, Jinja2 templating
- **Security:** Session-based authentication, SHA-256 password hashing

## 🚀 Quick Start

### System Requirements

- **OS:** Windows, macOS, or Linux
- **Python:** 3.8+
- **Package Manager:** pip (comes with Python)
- **Editor:** VS Code or any text editor
- **Browser:** Chrome, Firefox, Safari, or Edge

### Installation

1. **Clone or download the project:**
   ```bash
   cd "c:\Users\hkoech\Desktop\My Project"
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install flask==3.1.3
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Access the app:**
   - Open browser and go to `http://127.0.0.1:5000`
   - You'll be redirected to the login page

## 📋 Features

### User Authentication
- **Register:** Create a new account with username validation (3-30 chars)
- **Login:** Secure login with session management
- **Logout:** Clear session and return to login

### Dashboard
- Display user stats (sessions, account age, status)
- Recent activity timeline
- Current session information

### Feature Pages
- **Edit Profile:** Update full name, email, and bio
- **Security Settings:** Change password, 2FA toggle, see login activity
- **Notifications:** Configure email/push/marketing preferences
- **Help & Support:** FAQ, contact info, help categories

### Data Persistence
- User profiles stored in SQLite database
- Notification preferences saved
- All data persists between sessions

## 🧪 Minimal Working Example

### Create Your First User

1. Go to `http://127.0.0.1:5000/register`
2. Enter credentials:
   - Username: `testuser`
   - Password: `SecurePass123`
3. Click "Create Account" → Success! ✓

### Login & Explore

1. Go to `http://127.0.0.1:5000/login`
2. Enter your credentials
3. Click "Sign In" → Dashboard loads
4. Click menu buttons to explore features

### Expected Output

- ✅ Registration succeeds if username is unique and password meets requirements
- ✅ Login succeeds with correct credentials
- ✅ Dashboard displays welcome message and user stats
- ✅ Profile changes save to database
- ✅ All pages render with responsive design (works on mobile/tablet/desktop)

## 📁 Project Structure

```
AuthDash/
├── app.py                 # Main Flask application & routes
├── auth.py               # Authentication logic
├── database.py           # Database connection & schema
├── utils.py              # Helper functions (validation, hashing)
├── users.db              # SQLite database file
├── templates/
│   ├── base.html         # Master template (extended by all pages)
│   ├── register.html     # Registration form
│   ├── login.html        # Login form
│   ├── dashboard.html    # User dashboard
│   ├── edit-profile.html # Profile editing
│   ├── security-settings.html
│   ├── notifications.html
│   ├── help-support.html
│   ├── 404.html          # Error page
│   └── 500.html          # Error page
├── documentation/        # Complete guides and API reference
│   ├── INDEX.md          # Guide hub and navigation
│   ├── LOGIN_GUIDE.md    # Step-by-step login guide
│   ├── REGISTRATION_GUIDE.md
│   ├── API_GUIDE.md      # Developer API reference
│   └── TOOLKIT_GUIDE.md  # Capstone requirements
└── README.md             # This file
```

## 📖 Documentation

All guides, tutorials, and API documentation are located in the `documentation/` folder:

- **[INDEX.md](documentation/INDEX.md)** — Start here! Hub for all guides and tutorials
- **[LOGIN_GUIDE.md](documentation/LOGIN_GUIDE.md)** — Step-by-step user login guide with screenshots & troubleshooting
- **[REGISTRATION_GUIDE.md](documentation/REGISTRATION_GUIDE.md)** — Complete registration walkthrough
- **[API_GUIDE.md](documentation/API_GUIDE.md)** — Comprehensive API reference for developers with Python/Requests examples
- **[TOOLKIT_GUIDE.md](documentation/TOOLKIT_GUIDE.md)** — Capstone project requirements and implementation details

## 🔐 Security Features

- **Password Hashing:** SHA-256 encryption with salt
- **Session Management:** Secure HTTPOnly cookies
- **Access Control:** `@login_required` decorator protecting routes
- **Input Validation:** Username & password validation
- **Error Pages:** Custom 404 and 500 error handlers

## 🐛 Common Issues & Fixes

### Issue 1: "Address already in use" error
**Error:** `OSError: [Errno 48] Address already in use`

**Solution:**
```bash
# Find process using port 5000
netstat -ano | findstr :5000
# Kill the process (Windows)
taskkill /PID <PID> /F
# Then restart: python app.py
```

### Issue 2: "ModuleNotFoundError: No module named 'flask'"
**Solution:**
```bash
pip install flask==3.1.3
```

### Issue 3: "jinja2.exceptions.TemplateSyntaxError"
**Solution:** Ensure all Jinja2 blocks are properly closed:
- `{% extends "base.html" %}` at the top
- `{% block content %}...{% endblock %}` wrapping content
- All `{%` have matching `%}`

### Issue 4: Database locked error
**Solution:**
```bash
# Delete users.db if needed (starts fresh)
del users.db
# Restart: python app.py
```

### Issue 5: Password hashing inconsistency
**Solution:** Verify `utils.py` uses consistent SHA-256:
```python
import hashlib
hashlib.sha256(password.encode("utf-8")).hexdigest()
```

## 📚 References

### Official Documentation
- [Flask Official Docs](https://flask.palletsprojects.com/)
- [Python Built-in modules](https://docs.python.org/3/library/)
- [SQLite3 Documentation](https://www.sqlite.org/docs.html)
- [Jinja2 Template Engine](https://jinja.palletsprojects.com/)

### Related Resources
- [OWASP: Authentication Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [Password Security](https://owasp.org/www-community/attacks/Password_cracking)
- [HTTP Sessions](https://developer.mozilla.org/en-US/docs/Web/HTTP/Session)

### Learning Resources
- [Flask Mega-Tutorial by Miguel Grinberg](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)
- [Python Web Development with Flask (Real Python)](https://realpython.com/tutorials/flask/)

## 🤝 How to Test with Peers

1. Share the ZIP file or GitHub repo
2. Peer follows **Installation** steps above
3. Peer creates test account and explores features
4. Peer reports if all pages load correctly
5. Peer attempts different inputs (invalid usernames, weak passwords) to test validation

## 📝 Notes for Developers

- The app uses development mode with debug enabled
- Production deployment requires:
  - Stronger SECRET_KEY (use `os.urandom(24)`)
  - HTTPS/SSL certificates
  - Database migrations with Alembic
  - Environment variables for sensitive data

## 🧠 Learning Insights

This project demonstrates:
- **MVC Architecture:** Models (auth/database), Views (templates), Controllers (routes)
- **State Management:** Session-based user tracking
- **Database Design:** Normalization, relationships
- **Full-Stack Development:** Backend logic + frontend rendering
- **Security:** Input validation, password hashing, session management

---

**Last Updated:** March 2025  
**Python Version:** 3.14.3  
**Flask Version:** 3.1.3
