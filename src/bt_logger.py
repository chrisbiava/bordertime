import logging, sys
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-8s %(module)s:%(lineno)-4d %(message)s",
    datefmt="%d/%b/%Y %H:%M:%S",
    stream=sys.stdout)

_logger = logging.getLogger(__name__)