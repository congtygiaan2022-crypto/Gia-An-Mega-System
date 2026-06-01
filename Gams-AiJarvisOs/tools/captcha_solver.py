"""
tools/captcha_solver.py — Auto captcha solver using 2Captcha API.

Supports:
  - reCAPTCHA v2 / v3
  - hCaptcha
  - Image captcha
  - Cloudflare Turnstile

Setup:
  1. Đăng ký tài khoản tại https://2captcha.com
  2. Nạp tiền (tối thiểu $3)
  3. Thêm API key vào .env:
       TWOCAPTCHA_API_KEY=your_key_here

Usage in browser_tool.py:
  from tools.captcha_solver import captcha_solver
  token = captcha_solver.solve_recaptcha(sitekey, page_url)
  captcha_solver.inject_recaptcha_token(page, token)
"""

import os
import time
from core.logger import get_module_logger

logger = get_module_logger("CaptchaSolver")

try:
    from twocaptcha import TwoCaptcha
    _TWOCAPTCHA_AVAILABLE = True
except ImportError:
    _TWOCAPTCHA_AVAILABLE = False


class CaptchaSolver:
    """
    Unified captcha solver using 2Captcha as backend.
    Gracefully disabled when API key not configured.
    """

    def __init__(self):
        self.api_key = os.getenv("TWOCAPTCHA_API_KEY", "")
        self._solver = None

    def _get_solver(self):
        if not _TWOCAPTCHA_AVAILABLE:
            logger.error("2captcha-python not installed. Run: pip install 2captcha-python")
            return None
        if not self.api_key:
            logger.warning("[CaptchaSolver] No TWOCAPTCHA_API_KEY in .env — captcha solving disabled.")
            return None
        if self._solver is None:
            self._solver = TwoCaptcha(self.api_key)
        return self._solver

    # ------------------------------------------------------------------
    # Detectors
    # ------------------------------------------------------------------

    def detect_captcha_type(self, page) -> str | None:
        """Scan the current page for known captcha types. Returns type string or None."""
        try:
            html = page.content()
        except Exception:
            return None

        if "recaptcha" in html.lower() or "grecaptcha" in html.lower():
            return "recaptcha"
        if "hcaptcha" in html.lower():
            return "hcaptcha"
        if "cf-turnstile" in html.lower() or "challenges.cloudflare.com" in html.lower():
            return "turnstile"
        if page.query_selector("img[src*='captcha']"):
            return "image"
        return None

    def get_recaptcha_sitekey(self, page) -> str | None:
        """Extract reCAPTCHA sitekey from the page DOM."""
        try:
            return page.evaluate(
                "() => {"
                "  const el = document.querySelector('[data-sitekey]');"
                "  return el ? el.getAttribute('data-sitekey') : null;"
                "}"
            )
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Solvers
    # ------------------------------------------------------------------

    def solve_recaptcha(self, sitekey: str, page_url: str) -> str | None:
        """Solve reCAPTCHA v2 via 2Captcha. Returns token string."""
        solver = self._get_solver()
        if not solver:
            return None
        try:
            logger.info(f"[CaptchaSolver] Solving reCAPTCHA for {page_url}...")
            result = solver.recaptcha(sitekey=sitekey, url=page_url)
            token = result.get("code")
            logger.info("[CaptchaSolver] reCAPTCHA solved.")
            return token
        except Exception as e:
            logger.error(f"[CaptchaSolver] reCAPTCHA solve failed: {e}")
            return None

    def solve_hcaptcha(self, sitekey: str, page_url: str) -> str | None:
        """Solve hCaptcha via 2Captcha."""
        solver = self._get_solver()
        if not solver:
            return None
        try:
            logger.info(f"[CaptchaSolver] Solving hCaptcha for {page_url}...")
            result = solver.hcaptcha(sitekey=sitekey, url=page_url)
            return result.get("code")
        except Exception as e:
            logger.error(f"[CaptchaSolver] hCaptcha solve failed: {e}")
            return None

    def solve_turnstile(self, sitekey: str, page_url: str) -> str | None:
        """Solve Cloudflare Turnstile via 2Captcha."""
        solver = self._get_solver()
        if not solver:
            return None
        try:
            logger.info(f"[CaptchaSolver] Solving Cloudflare Turnstile for {page_url}...")
            result = solver.turnstile(sitekey=sitekey, url=page_url)
            return result.get("code")
        except Exception as e:
            logger.error(f"[CaptchaSolver] Turnstile solve failed: {e}")
            return None

    # ------------------------------------------------------------------
    # Injection
    # ------------------------------------------------------------------

    def inject_recaptcha_token(self, page, token: str) -> bool:
        """Inject solved reCAPTCHA token into page and trigger callback."""
        try:
            page.evaluate(
                f"""
                (function() {{
                    // Inject token into hidden textarea
                    var el = document.getElementById('g-recaptcha-response');
                    if (el) {{ el.value = '{token}'; el.style.display = 'block'; }}

                    // Also set all recaptcha response textareas
                    var all = document.querySelectorAll('textarea[name="g-recaptcha-response"]');
                    all.forEach(function(t) {{ t.value = '{token}'; }});

                    // Fire callback if available
                    if (typeof ___grecaptcha_cfg !== 'undefined') {{
                        var clients = ___grecaptcha_cfg.clients;
                        if (clients) {{
                            Object.keys(clients).forEach(function(k) {{
                                var client = clients[k];
                                if (client && client.callback) client.callback('{token}');
                            }});
                        }}
                    }}
                }})();
                """
            )
            return True
        except Exception as e:
            logger.error(f"[CaptchaSolver] Token injection failed: {e}")
            return False

    # ------------------------------------------------------------------
    # Auto-solve (main entry point)
    # ------------------------------------------------------------------

    def auto_solve(self, page) -> bool:
        """
        Detect captcha type on current page and auto-solve it.
        Returns True if solved successfully, False otherwise.
        """
        captcha_type = self.detect_captcha_type(page)
        if not captcha_type:
            return True  # No captcha found — all good

        logger.warning(f"[CaptchaSolver] Captcha detected: {captcha_type}")
        page_url = page.url

        if captcha_type in ("recaptcha",):
            sitekey = self.get_recaptcha_sitekey(page)
            if not sitekey:
                logger.error("[CaptchaSolver] Could not extract sitekey.")
                return False
            token = self.solve_recaptcha(sitekey, page_url)
            if token:
                return self.inject_recaptcha_token(page, token)

        elif captcha_type == "hcaptcha":
            sitekey = self.get_recaptcha_sitekey(page)
            if not sitekey:
                return False
            token = self.solve_hcaptcha(sitekey, page_url)
            if token:
                return self.inject_recaptcha_token(page, token)

        elif captcha_type == "turnstile":
            sitekey = self.get_recaptcha_sitekey(page)
            if not sitekey:
                return False
            token = self.solve_turnstile(sitekey, page_url)
            if token:
                return self.inject_recaptcha_token(page, token)

        return False

    def is_configured(self) -> bool:
        return bool(self.api_key) and _TWOCAPTCHA_AVAILABLE


# Global singleton
captcha_solver = CaptchaSolver()
