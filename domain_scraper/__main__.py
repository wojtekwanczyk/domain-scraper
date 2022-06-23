"""Argument parser for domain-scraper module"""

import logging
import sys
from typing import Optional

from .parser import parse_arguments
from .parser import scrape_and_send


logger = logging.getLogger(__name__)


def main() -> Optional[int | None]:
    """Configure logging, parse arguments and invoke proper function"""

    args = parse_arguments()
    if not hasattr(args, "func"):
        args.func = scrape_and_send

    logging.basicConfig(level=args.logging_level)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
