import logging
import os
from datetime import datetime, timezone

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    logger.addHandler(create_console_handler())
    logger.addHandler(create_file_handler())

def create_console_handler():
    class ConsoleFormatter(logging.Formatter):
        reset = "\033[0m"
        bold = "\033[1m"
        red = "\033[31m"
        yellow = "\033[33m"
        blue = "\033[34m"
        magenta = "\033[35m"
        bright_black= "\033[90m"

        COLORS = {
            logging.DEBUG: bright_black,
            logging.INFO: blue,
            logging.WARNING: yellow,
            logging.ERROR: red,
            logging.CRITICAL: bold + red
        }

        def format(self, record):
            level_color = self.COLORS.get(record.levelno)
            return logging.Formatter(
                fmt=f"{self.bright_black}[%(asctime)s]{self.reset} {level_color}[%(levelname)-8s]{self.reset} {self.magenta}[%(name)s]{self.reset}: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S %z",
                style="%"
            ).format(record)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ConsoleFormatter())
    return console_handler

def create_file_handler():
    filename = create_log_file()

    file_formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)-8s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z",
        style="%"
    )

    try:
        file_handler = logging.FileHandler(filename=filename, mode="w", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        return file_handler
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to initialize file logging at {filename}: {e}")
        return None

def create_log_file():
    os.makedirs(name=".logs", exist_ok=True)

    formatted_utc_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    base_filepath = os.path.join(".logs", formatted_utc_date)

    index = 1
    while True:
        filename = f"{base_filepath}-{index:03d}.log"
        if not os.path.exists(filename):
            return filename
        if index >= 99:
            logging.getLogger(__name__).warning(f"Could not create a new log file, overwriting {filename} instead. You should not see this warning if this is a production environment.")
            return filename
        index += 1