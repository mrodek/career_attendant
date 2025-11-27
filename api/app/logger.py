import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger("api")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
