"""
Facebook Credentials Configuration

THIS FILE CONTAINS SENSITIVE DATA - DO NOT COMMIT TO VERSION CONTROL!

Add this file to .gitignore:
    echo "fb_credentials.py" >> .gitignore

Usage:
    1. Fill in your credentials below
    2. Or use environment variables (see config.py)
    
For cookies, you can:
    1. Log in to Facebook manually
    2. Use browser dev tools (F12) -> Application -> Cookies
    3. Copy the 'c_user' and 'xs' cookie values
"""

# Facebook Login Credentials
# ==========================
FB_EMAIL = ""  # Your Facebook email
FB_PASSWORD = ""  # Your Facebook password

# Facebook Cookies (alternative to login)
# =======================================
# These cookies allow login without username/password
# Get them from your browser after logging in manually
FB_COOKIES = {
    "c_user": "",  # Your user ID (numbers)
    "xs": "",      # Session token (long string)
    # Optional additional cookies:
    # "datr": "",
    # "sb": "",
}

# Database Configuration (optional overrides)
# ==========================================
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = ""
POSTGRES_DATABASE = "facebook_scraper"
