"""Scrape domains from raw emails and save them to dbfile"""

import json
import logging
import os
import re
from collections import defaultdict
from email.message import Message

logger = logging.getLogger(__name__)


class DomainScraper:
    """Scrape domains from raw emails and save them to dbfile"""

    def __init__(self) -> None:
        separators = r"from|by|via|with|id|for|;"
        regex_from_str = r"from\s+(.+?)\s+(" + separators + r")"
        regex_by_str = r"by\s+(.+?)\s+(" + separators + r")"
        self.regex_from = re.compile(regex_from_str)
        self.regex_by = re.compile(regex_by_str)
        self.domains: dict = {}

    def scrape_from_emails(self, emails: list[Message]) -> None:
        """Iterate over emails and scrape domains from them"""
        for email in emails:
            message_id = email["Message-ID"].strip("\t<>")
            email_domains = self.get_domains_for_email(email)
            self.domains[message_id] = email_domains

    def get_domains_for_email(self, email: Message) -> list[str]:
        """Returns dict with single element; Message-ID: [domains]"""
        received_headers = email.get_all("Received")
        email_domains: set[str] = set()  # use set to avoid duplicates
        for received_header in received_headers:
            if domain := self.regex_from.search(received_header):
                email_domains.add(domain.group(1))
            if domain := self.regex_by.search(received_header):
                email_domains.add(domain.group(1))
        return list(email_domains)

    @staticmethod
    def make_sure_dirname_exists(file: str) -> None:
        """Make sure base directory from file exists to avoid exception"""
        dirname = os.path.dirname(file)
        if not os.path.exists(dirname):
            logger.debug("DBFILE PATH DOES not exists, creating %s", dirname)
            os.makedirs(dirname)

    def save(self, dbfile: str) -> bool:
        """
        Save scraped domains to dbfile.
        If no domains are parsed, returns False
        """
        if not self.domains:
            logger.info("No new emails parsed, please check INPUT_DIR")
            return False

        try:
            with open(dbfile, "r", encoding="utf-8") as file:
                dbfile_dict = json.load(file)
        except FileNotFoundError:
            dbfile_dict = defaultdict(dict)

        dbfile_dict["domains"].update(self.domains)
        self.make_sure_dirname_exists(dbfile)

        with open(dbfile, "w", encoding="utf-8") as file:
            json.dump(dbfile_dict, file, indent=2)
        return True
