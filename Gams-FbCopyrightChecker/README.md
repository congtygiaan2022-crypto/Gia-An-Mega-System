# FB Copyright Checker

A modular Python tool that logs into Facebook with Selenium, scans your profile posts for copyright-related keywords, logs everything to SQLite, and can automatically delete flagged posts.

## Project Structure

```
fb_copyright_checker/
├── main.py                  # Entry point
├── config.json              # All settings
├── requirements.txt
├── db/                      # SQLite database (auto-created)
├── logs/                    # Rotating log files (auto-created)
└── modules/
    ├── config_loader.py     # Loads config.json
    ├── logger.py            # Colored console + rotating file logger
    ├── database.py          # SQLite: posts, deletions, scan log
    ├── fb_login.py          # Selenium driver + Facebook login
    ├── post_scanner.py      # Scans profile timeline for keywords
    └── delete_post.py       # Deletes individual or bulk flagged posts
```

## Setup

```bash
cd fb_copyright_checker
pip install -r requirements.txt
```

## Configuration

Edit `config.json`:

| Key | Description |
|-----|-------------|
| `facebook.email` | Your Facebook login email |
| `facebook.password` | Your Facebook password |
| `facebook.profile_url` | URL of the profile/page to scan |
| `selenium.headless` | Run Chrome without a window (`true`/`false`) |
| `checker.keywords` | Words that flag a post as copyright-related |
| `checker.auto_delete_flagged` | If `true`, flagged posts are deleted automatically |
| `checker.scan_interval_seconds` | Seconds between scan cycles |

## Run

```bash
python main.py
```

## Database Tables

- **posts** — all scanned posts with flag/status
- **deleted_posts** — audit trail of every deletion
- **scan_log** — per-cycle summary (total / flagged / deleted)

## Notes

- Facebook's DOM changes frequently; XPath selectors in `delete_post.py` and `post_scanner.py` may need updating.
- Use responsibly and in accordance with Facebook's Terms of Service.
