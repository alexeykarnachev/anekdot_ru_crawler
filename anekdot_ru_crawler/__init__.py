import sys

from anekdot_ru_crawler import log_utils

sys.excepthook = log_utils.handle_unhandled_exception
