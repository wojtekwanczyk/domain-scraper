"""Default configuration for domain-scraper."""

import os


PERSONAL_SETTINGS = {
    "DOMAINS_SUBSCRIBERS": os.environ.get("DOMAINS_SUBSCRIBERS", ""),
    "GMAIL_APP_USERNAME": os.environ.get("GMAIL_APP_USERNAME", ""),
    "GMAIL_APP_PASSWORD": os.environ.get("GMAIL_APP_PASSWORD", ""),
}


DEFAULT = PERSONAL_SETTINGS | {
    "ARCHIVE_DIR": os.environ.get("ARCHIVE_DIR", "emails/archive"),
    "DB_FILE": os.environ.get("DB_FILE", "db/email_database.json"),
    "EMAIL_HOST": "smtp.gmail.com",
    "EMAIL_PORT": 465,
    "INPUT_DIR": os.environ.get("INPUT_DIR", "emails/input"),
    "LOG_LEVEL": "INFO",
}

DEVELOPMENT = DEFAULT | {
    "LOG_LEVEL": "DEBUG",
}
