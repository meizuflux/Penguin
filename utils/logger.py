"""
Copyright (C) 2021 kal-byte + ppotatoo
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.
You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import logging


# this is from kal#1806
# Here's the repo link: https://github.com/platform-discord/travis-bott/blob/master/utils/logger.py#L22
class Formatter(logging.Formatter):
    """Logging Formatter that adds colors"""

    grey = "\x1b[38m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    red = "\x1b[31m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    _format = (
        "%(levelname)s (%(name)s) |:| %(message)s |:| %(pathname)s LINE %(lineno)d"
    )

    FORMATS = {
        logging.DEBUG: grey + _format + reset,
        logging.INFO: green + _format + reset,
        logging.WARNING: yellow + _format + reset,
        logging.ERROR: red + _format + reset,
        logging.CRITICAL: bold_red + _format + reset,
    }

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, "%m/%d/%Y %-I:%M:%S")
        return formatter.format(record)


def create_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setFormatter(Formatter())

    logger.addHandler(ch)

    return logger
