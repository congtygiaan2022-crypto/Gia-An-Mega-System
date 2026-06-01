# FB Copyright Checker - Comprehensive Codebase Analysis

## Project Overview

FB Copyright Checker is a modular Python automation tool that monitors Facebook accounts for copyright-related issues. It logs into Facebook via Selenium, scans posts for copyright violations, stores results in SQLite, and can automatically delete flagged content. Supports multi-account management with both CLI and GUI interfaces.

## What the Tool Does

1. **Multi-Account Management** — Store & manage multiple Facebook accounts with credentials, 2FA, metadata
2. **Facebook Automation** — Automated login via Selenium WebDriver with 2FA support
3. **Copyright Scanning** — Monitor personal profile and fanpages for copyright violations
4. **Content Deletion** — Automatically or manually delete posts flagged for copyright
5. **Data Logging** — SQLite tracks scans, posts, deletions, appeals
6. **GUI Dashboard** — CustomTkinter interface (7 pages: accounts, login, profile, fanpage, checker, logs, settings)
7. **CLI Mode** — Headless operation for automated workflows

## Tech Stack

- **Selenium 4.20.0** — Browser automation via ChromeDriver
- **CustomTkinter 5.2.2** — Modern dark-theme GUI
- **PyOTP 2.9.0** — TOTP/2FA generation
- **SQLite3** — Local database
- **Python 3.9+**
- **Platform**: Windows-specific (hardcoded Chrome path)

## Key Modules

1. **main.py** — Entry point (GUI/CLI/2FA setup)
2. **config_loader.py** — Load config.json
3. **logger.py** — Colored console + rotating file logging
4. **database.py** — SQLite wrapper (posts, deleted_posts, scan_log tables)
5. **fb_login.py** — Selenium driver, Facebook login, 2FA handling
6. **fb_profile.py** — Extract profile info, scrape fanpages
7. **post_scanner.py** — Scan timeline for copyright keywords
8. **delete_post.py** — Delete individual or bulk posts
9. **copyright_checker.py** — Full copyright appeal workflow
10. **two_factor.py** — TOTP code generation
11. **account_manager.py** — Multi-account CRUD, simple encryption
12. **gui/dashboard.py** — Main GUI (948 lines, 7 pages, queue-based threading)

## Database Schema

**posts**: post_id, url, content, status, flagged, created_at, checked_at
**deleted_posts**: post_id, url, reason, deleted_at
**scan_log**: scanned_at, total, flagged, deleted

## CRITICAL ISSUES

### 1. WEAK CREDENTIAL ENCRYPTION (account_manager.py:22-25)
- XOR + Base64 obfuscation (trivially reversible, NOT encryption)
- Hardcoded key: "fbcopyright2025" (visible in source)
- Impact: File access = full password compromise
- Fix: Use cryptography.fernet or OS keyring

### 2. 2FA SECRET IN PLAINTEXT (config.json, two_factor.py)
- Base32 TOTP secret stored unencrypted
- Anyone with file access can generate valid 6-digit codes
- Fix: Use OS keyring or encrypted file

### 3. WINDOWS-ONLY HARDCODED PATHS (fb_login.py:19-20)
- Chrome binary: C:\Program Files\Google\Chrome\Application\chrome.exe
- Crashes on macOS/Linux
- Fix: Detect OS or use webdriver-manager

### 4. FRAGILE WEB SCRAPING (high break risk)
- Post XPath (post_scanner.py:37): //div[@data-pagelet='ProfileTimeline']//div[@role='article']
- Menu XPath (delete_post.py:27): //div[@aria-label='Actions for this post' ...]
- Appeals XPath (copyright_checker.py:84): //div[@role='article'] | //div[contains(@class,'x1qjc9v5')]
- Problem: Facebook changes DOM weekly; selectors break frequently
- Fix: Use Facebook Graph API or add intelligent fallbacks/retries

### 5. NO INPUT VALIDATION
- Missing config keys crash app with KeyError
- No validation of emails, URLs, keywords
- Fix: Validate config on load with clear error messages

### 6. RACE CONDITIONS IN THREADING (logger.py:14-16, copyright_checker.py:254-269)
- Check-then-act race: multiple threads pass handler check before any adds
- Context switching uses time.sleep(3) without verification
- Fix: Use threading.Lock() for initialization; add explicit waits

### 7. NO RETRY LOGIC
- Single Selenium failure stops entire bulk delete
- No exponential backoff or recovery
- Fix: Add retry decorator with backoff

### 8. SHARED CHROME PROFILE ACROSS ACCOUNTS (fb_login.py:36)
- All accounts use ./chrome_profile
- Cookie/session conflicts between accounts
- Fix: Use per-account profiles or clear cookies between logins

## HIGH-PRIORITY ISSUES

- **No exception recovery in scan loop** (main.py:63-68) — single crash exits app
- **Implicit vs explicit waits inconsistent** — time.sleep() mixed with WebDriverWait
- **No rate limiting** — rapid requests may trigger bot detection
- **No timeout for long-running operations** — scans can hang indefinitely
- **Fanpage switch failures ignored silently** (copyright_checker.py:254-256)
- **Queue polling too aggressive** (dashboard.py:763) — polls every 120ms

## MEDIUM-PRIORITY ISSUES

- Hardcoded Vietnamese text throughout (not i18n-friendly)
- Magic numbers scattered everywhere (time.sleep(2/3/4))
- Account.active flag unused despite existing in dataclass
- Import format detection ambiguous (uid vs email detection)
- Unused code and imports

## Security Assessment

| Risk | Severity |
|------|----------|
| Weak password storage | CRITICAL |
| 2FA secret plaintext | CRITICAL |
| Windows-only code | HIGH |
| Fragile selectors | HIGH |
| Race conditions | HIGH |
| No input validation | MEDIUM |
| No retry logic | MEDIUM |
| No rate limiting | MEDIUM |
| Shared profiles | MEDIUM |

## Conclusion

FB Copyright Checker is a well-structured but insecure automation tool with polished GUI and multi-account support. Critical flaws in credential storage, high maintenance burden from web scraping, and platform-specific code limit production readiness. For production use: (1) immediately fix encryption/keyring issues, (2) add OS detection, (3) migrate to Facebook Graph API instead of scraping.
