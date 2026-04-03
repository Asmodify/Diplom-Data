"""
Cookie Helper v2.0
==================
Cookie management for browser session persistence.

Features:
- Save/load cookies
- Cookie validation
- Multiple profiles
"""

import json
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class CookieHelper:
    """
    Manages browser cookies for session persistence.
    
    Features:
    - Save cookies to file
    - Load cookies from file
    - Validate cookies
    - Multiple profiles support
    """
    
    def __init__(self, cookie_dir: Optional[str] = None):
        """
        Initialize CookieHelper.
        
        Args:
            cookie_dir: Directory to store cookies (default: ./data/cookies)
        """
        if cookie_dir is None:
            base_dir = Path(__file__).parent.parent
            cookie_dir = base_dir / "data" / "cookies"
            
        self.cookie_dir = Path(cookie_dir)
        self.cookie_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_cookie_path(self, profile: str = "default") -> Path:
        """Get cookie file path for profile."""
        return self.cookie_dir / f"{profile}_cookies.json"
        
    def save_cookies(
        self,
        driver,
        profile: str = "default",
        domain_filter: Optional[str] = None
    ) -> bool:
        """
        Save cookies from browser.
        
        Args:
            driver: Selenium WebDriver instance
            profile: Profile name
            domain_filter: Optional domain to filter cookies
            
        Returns:
            True if successful
        """
        try:
            cookies = driver.get_cookies()
            
            # Filter by domain if specified
            if domain_filter:
                cookies = [
                    c for c in cookies
                    if domain_filter in c.get('domain', '')
                ]
                
            if not cookies:
                logger.warning("No cookies to save")
                return False
                
            cookie_data = {
                'cookies': cookies,
                'saved_at': datetime.now().isoformat(),
                'profile': profile,
                'count': len(cookies),
            }
            
            cookie_path = self._get_cookie_path(profile)
            with open(cookie_path, 'w', encoding='utf-8') as f:
                json.dump(cookie_data, f, indent=2)
                
            logger.info(f"Saved {len(cookies)} cookies to {cookie_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
            return False
            
    def load_cookies(
        self,
        driver,
        profile: str = "default",
        check_expiry: bool = True
    ) -> bool:
        """
        Load cookies into browser.
        
        Args:
            driver: Selenium WebDriver instance
            profile: Profile name
            check_expiry: Skip expired cookies
            
        Returns:
            True if successful
        """
        cookie_path = self._get_cookie_path(profile)
        
        if not cookie_path.exists():
            logger.warning(f"Cookie file not found: {cookie_path}")
            return False
            
        try:
            with open(cookie_path, 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)
                
            cookies = cookie_data.get('cookies', [])
            current_time = datetime.now().timestamp()
            loaded = 0
            
            for cookie in cookies:
                # Check expiry
                if check_expiry:
                    expiry = cookie.get('expiry')
                    if expiry and expiry < current_time:
                        continue
                        
                # Remove problematic keys
                cookie_clean = {
                    k: v for k, v in cookie.items()
                    if k not in ['sameSite', 'storeId', 'hostOnly']
                }
                
                try:
                    driver.add_cookie(cookie_clean)
                    loaded += 1
                except Exception as e:
                    logger.debug(f"Skip cookie: {e}")
                    
            logger.info(f"Loaded {loaded}/{len(cookies)} cookies")
            return loaded > 0
            
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return False
            
    def has_cookies(self, profile: str = "default") -> bool:
        """Check if cookies exist for profile."""
        return self._get_cookie_path(profile).exists()
        
    def get_cookie_info(self, profile: str = "default") -> Optional[Dict[str, Any]]:
        """
        Get information about saved cookies.
        
        Args:
            profile: Profile name
            
        Returns:
            Cookie metadata or None
        """
        cookie_path = self._get_cookie_path(profile)
        
        if not cookie_path.exists():
            return None
            
        try:
            with open(cookie_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            return {
                'profile': profile,
                'saved_at': data.get('saved_at'),
                'count': data.get('count', len(data.get('cookies', []))),
                'file_path': str(cookie_path),
            }
        except Exception:
            return None
            
    def delete_cookies(self, profile: str = "default") -> bool:
        """
        Delete saved cookies.
        
        Args:
            profile: Profile name
            
        Returns:
            True if deleted
        """
        cookie_path = self._get_cookie_path(profile)
        
        if cookie_path.exists():
            try:
                cookie_path.unlink()
                logger.info(f"Deleted cookies for profile: {profile}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete cookies: {e}")
                return False
        return False
        
    def list_profiles(self) -> List[str]:
        """
        List all cookie profiles.
        
        Returns:
            List of profile names
        """
        profiles = []
        for path in self.cookie_dir.glob("*_cookies.json"):
            profile = path.stem.replace("_cookies", "")
            profiles.append(profile)
        return profiles
        
    def validate_cookies(
        self,
        driver,
        validation_url: str = "https://www.facebook.com",
        logged_in_indicator: str = "c_user"
    ) -> bool:
        """
        Validate if cookies provide logged-in state.
        
        Args:
            driver: Selenium WebDriver
            validation_url: URL to check
            logged_in_indicator: Cookie name that indicates login
            
        Returns:
            True if cookies are valid
        """
        try:
            driver.get(validation_url)
            
            import time
            time.sleep(2)
            
            cookies = driver.get_cookies()
            cookie_names = [c['name'] for c in cookies]
            
            if logged_in_indicator in cookie_names:
                logger.info("Cookies are valid - logged in")
                return True
            else:
                logger.warning("Cookies invalid - not logged in")
                return False
                
        except Exception as e:
            logger.error(f"Cookie validation failed: {e}")
            return False
            
    def export_cookies_netscape(
        self,
        profile: str = "default",
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Export cookies in Netscape format.
        
        Args:
            profile: Profile name
            output_path: Output file path
            
        Returns:
            Output file path or None
        """
        cookie_path = self._get_cookie_path(profile)
        
        if not cookie_path.exists():
            return None
            
        try:
            with open(cookie_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            cookies = data.get('cookies', [])
            
            if output_path is None:
                output_path = self.cookie_dir / f"{profile}_cookies.txt"
                
            lines = ["# Netscape HTTP Cookie File"]
            
            for cookie in cookies:
                domain = cookie.get('domain', '')
                flag = "TRUE" if domain.startswith('.') else "FALSE"
                path = cookie.get('path', '/')
                secure = "TRUE" if cookie.get('secure') else "FALSE"
                expiry = str(int(cookie.get('expiry', 0)))
                name = cookie.get('name', '')
                value = cookie.get('value', '')
                
                lines.append(f"{domain}\t{flag}\t{path}\t{secure}\t{expiry}\t{name}\t{value}")
                
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
                
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return None
