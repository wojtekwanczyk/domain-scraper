"""Read emails from input_dir, move them to archive_dir"""

import logging
import os
import shutil
from time import time
from email.message import Message
from email.parser import BytesHeaderParser
from email.policy import default


logger = logging.getLogger(__name__)


def read_emails_from_dir(input_dir: str, archive_dir: str) -> list[Message]:
    """Parse emails from input_dir, move them to archive_dir"""
    emails_list: list[Message] = []
    if not os.path.isdir(input_dir):
        logger.warning("INPUT_DIR (%s) does not exist!", input_dir)
        return emails_list  # empty list
    if not os.path.isdir(archive_dir):
        os.mkdir(archive_dir)

    parser = BytesHeaderParser(policy=default)
    for email_filename in os.listdir(input_dir):

        # read and parse email
        email_path = os.path.join(input_dir, email_filename)
        with open(email_path, "rb") as file:
            email: Message = parser.parse(file)
            emails_list.append(email)

        # move parsed email to ARCHIVE_DIR
        # timestamp added to avoid OSError during renaming
        new_email_name = email_filename + "_{}".format(int(time()))
        new_email_path = os.path.join(archive_dir, new_email_name)
        shutil.move(email_path, new_email_path)
    return emails_list
