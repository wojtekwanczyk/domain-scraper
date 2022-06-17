# domain-scraper :mag:

## Configure domain-scraper by setting variables to make send-summary work
 - DOMAINS_SUBSCRIBERS - comma separated vaild email addresses
 - GMAIL_APP_USERNAME - gmail username
 - GMAIL_APP_PASSWORD - gmail password

## Usage
Usage: main.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  scrape-domains  Scrape domains from emails from input_dir and print them
  send-summary    Read domains from file and send email with update to DOMAIN_SUBSCRIBERS

## TODO:
 - [x] move scanned emails to separate dir to avoid duplication
 - [ ] add html alternative message template + use it
 - [ ] add setup.py, entrypoint and test building
 - [ ] create separate config file (INPUT_DIR, DB_FILE, DOMAINS_SUBSCRIBERS)
 - [ ] add logging and remove all prints
 - [ ] add option for send-summary to send all emails instead of only new emails
 - [ ] write unit tests
 - [ ] add docstrings
 - [ ] add types declarations