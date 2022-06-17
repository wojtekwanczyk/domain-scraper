import json
import re

from collections import defaultdict
from pprint import pprint


class DomainScraper:
    def __init__(self):
        separators = 'from|by|via|with|id|for|;'
        self.from_regex = re.compile(f'from\s+(.+?)\s+({separators})')
        self.by_regex = re.compile(f'by\s+(.+?)\s+({separators})')
        self.domains = dict()

    def scrape_from_emails(self, emails):
        for email in emails:
            email_domains = self.get_domains_for_email(email)
            self.domains.update(email_domains)

    def get_domains_for_email(self, email):
        received_headers = email.get_all('Received')
        email_domains = set()
        for received in received_headers:
            if domain := self.from_regex.search(received):
                email_domains.add(domain.group(1))
            if domain := self.by_regex.search(received):
                email_domains.add(domain.group(1))
        message_id = email['Message-ID'].strip('\t<>')
        return {message_id: list(email_domains)}
    
    def save(self, dbfile):
        try:
            with open(dbfile, 'r') as f:
                dbfile_dict = json.load(f)
        except FileNotFoundError:
            dbfile_dict = defaultdict(dict)
        dbfile_dict['domains'] = self.domains
        pprint(dbfile_dict)
        with open(dbfile, 'w') as f:
            json.dump(dbfile_dict, f, indent=2)
