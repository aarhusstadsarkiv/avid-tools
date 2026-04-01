import logging
import sys


def configure_logging():
    logging.basicConfig(
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("validation.log"),
        ],
        format="%(asctime)s (%(levelname)s) %(message)s",
        datefmt="%H:%M:%S",
        level=logging.INFO,
    )
