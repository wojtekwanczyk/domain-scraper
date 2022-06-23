"""Read emails from input_dir, move them to archive_dir"""

import logging
import os
import shutil
from time import time
from email.message import Message
from email.parser import BytesHeaderParser
from email.policy import default


logger = logging.getLogger(__name__)


class EmailParser:
    """Parse emails and move them to archive_dir"""

    def __init__(self, archive_dir: str) -> None:
        self.parser = BytesHeaderParser(policy=default)
        self.archive_dir = archive_dir
        if not os.path.isdir(self.archive_dir):
            os.mkdir(self.archive_dir)

    def parse_emails_from_dir(self, input_dir: str) -> list[Message]:
        """Parse emails from input_dir, move them to archive_dir"""
        emails_list: list[Message] = []
        if not os.path.isdir(input_dir):
            logger.warning("INPUT_DIR (%s) does not exist!", input_dir)
            return emails_list  # empty list

        for email_filename in os.listdir(input_dir):
            email_file = os.path.join(input_dir, email_filename)
            parsed_email = self.parse_email(email_file)
            emails_list.append(parsed_email)

        return emails_list

    def parse_email(self, email_file: str) -> Message:
        """
        Read email from filesystem, parse and move to archive_dir with timestamp
        to avoid OSError when file with the same name is parsed
        """
        with open(email_file, "rb") as file:
            email: Message = self.parser.parse(file)

        email_name = os.path.basename(email_file)
        new_email_name = email_name + "_{}".format(int(time()))
        new_email_file = os.path.join(self.archive_dir, new_email_name)
        shutil.move(email_file, new_email_file)

        return email
