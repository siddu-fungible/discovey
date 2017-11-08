import logging, sys

scheduler_logger = logging.getLogger("main_scheduler_log")
scheduler_logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
scheduler_logger.addHandler(hdlr=handler)


scheduler_logger.