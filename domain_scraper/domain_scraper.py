import json
import os
import re

from collections import defaultdict


class DomainScraper:
    def __init__(self):
        separators = 'from|by|via|with|id|for|;'
        self.regex_from = re.compile(f'from\s+(.+?)\s+({separators})')
        self.regex_by = re.compile(f'by\s+(.+?)\s+({separators})')
        self.domains = dict()

    def scrape_from_emails(self, emails):
        for email in emails:
            email_domains = self.get_domains_for_email(email)
            self.domains.update(email_domains)

    def get_domains_for_email(self, email):
        """Returns dict with single element; Message-ID: [domains]"""
        received_headers = email.get_all('Received')
        email_domains = set() # use set to avoid duplicates
        for received_header in received_headers:
            if domain := self.regex_from.search(received_header):
                email_domains.add(domain.group(1))
            if domain := self.regex_by.search(received_header):
                email_domains.add(domain.group(1))
        message_id = email['Message-ID'].strip('\t<>')
        return {message_id: list(email_domains)}
    
    @staticmethod
    def make_sure_dirname_exists(file):
        dirname = os.path.dirname(file)
        if not os.path.exists(dirname):
            print(f"DBFILE PATH DOES not exists, creating {dirname}")
            os.makedirs(dirname)
    
    def save(self, dbfile):
        if not self.domains:
            print("No new emails parsed, please check INPUT_DIR")
            return False

        try:
            with open(dbfile, 'r') as f:
                dbfile_dict = json.load(f)
        except FileNotFoundError:
            dbfile_dict = defaultdict(dict)

        dbfile_dict['domains'].update(self.domains)
        self.make_sure_dirname_exists(dbfile)

        with open(dbfile, 'w') as f:
            json.dump(dbfile_dict, f, indent=2)
