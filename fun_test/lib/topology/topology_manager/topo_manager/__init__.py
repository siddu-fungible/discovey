from os import path, remove
import json
import logging
import logging.config
from topo import *

PKG_DIR=path.dirname(path.abspath(__file__))
LOG_CFG=os.path.join(PKG_DIR, 'logging.json')

if path.isfile("info.log"):
    remove("info.log")
if path.isfile("errors.log"):
    remove("errors.log")

with open(LOG_CFG, 'r') as logging_configuration_file:
    config_dict = json.load(logging_configuration_file)

logging.config.dictConfig(config_dict)

# Log that the logger was configured
logger = logging.getLogger(__name__)
logger.info('Completed configuring logger()!')
