# Facebook credentials - DO NOT SHARE!
# These are your Facebook login credentials for the scraper.

# ============================================================================
# AUTHENTICATION OPTIONS (in order of priority):
# 1. Cookie-based login (fastest, most reliable)
# 2. Email/Password login (may trigger security checks)
# 3. Manual login (fallback - you log in manually in the browser)
# ============================================================================

# Email and password for automated login (optional if using cookies)
FB_EMAIL = "99435793"
FB_PASSWORD = "Keqing17"

# Cookie-based authentication - PREFERRED METHOD
# These cookies enable automatic login without entering credentials.
# To refresh cookies, run: python utils/cookie_helper.py --extract
cookies = {
    "datr": "U9hbaMM4Iw6fuZn0Iz4gRjxW",
    "wd": "1352x675",
    "dpr": "1.25",
    "c_user": "100012029838240",
    "sb": "U9hbaANzQklEK5wqvybhzGZU",
    "xs": "12%3ARK_6XQo5RwyVbw%3A2%3A1750849645%3A-1%3A-1",
    "fr": "0JbzYcn2kEjOricRk.AWfTG4bWmLUCfSuv3altjCOJAGoBDuIMK-98stG-HEJ8lckBgFI.BoW9hT..AAA.0.0.BoW9hv.AWceauSr1slDPs8rNcXTz-m8r7Q"
}

# ============================================================================
# COOKIE NOTES:
# - Cookies typically expire after 30-90 days
# - If scraper fails to log in, refresh cookies using cookie_helper.py
# - Essential cookies: c_user, xs, datr, sb, fr
# ============================================================================
