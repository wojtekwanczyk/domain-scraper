"""Default configuration for domain-scraper"""

import os


DEFAULT = {
    "INPUT_DIR": os.environ.get("INPUT_DIR", "emails/input"),
    "ARCHIVE_DIR": os.environ.get("ARCHIVE_DIR", "emails/archive"),
    "DB_FILE": os.environ.get("DB_FILE", "db/email_database.json"),
    "LOG_LEVEL": "INFO",
}

DEVELOPMENT = DEFAULT | {
    "LOG_LEVEL": "DEBUG",
}
