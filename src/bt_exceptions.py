from bt_logger import _logger
from requests import Session

class BadResolution(Exception):
    # Sample: 1920x1080 to 800x600 works, 620x465 not. Same goes for
    # vertical images

    feole = Session
