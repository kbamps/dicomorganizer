import logging
import os
import sys
from datetime import datetime
import queue

class QueueHandler(logging.Handler):
    """Custom logging handler to send logs to a queue."""
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        try:
            # Use the formatter to format the record
            if self.formatter:
                msg = self.format(record) + "\n"
            else:
                # Use a default format if no formatter is set
                msg = f"{record.levelname}: {record.getMessage()}" + "\n"
            self.log_queue.put(msg)
        except Exception:
            self.handleError(record)


def set_queue_logging():
    log_queue = queue.Queue()
    logger = logging.getLogger()
    # Prevent duplicate handlers
    if not any(isinstance(h, QueueHandler) for h in logger.handlers):
        queue_handler = QueueHandler(log_queue)
        queue_handler.setLevel(logging.INFO)
        queue_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s'))
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
    return log_queue

def set_logging():
    stream_handler = logging.StreamHandler(sys.stdout)
    queue_handler = QueueHandler(queue.Queue())
    
    stream_handler.setLevel(logging.INFO)
    queue_handler.setLevel(logging.INFO)

    stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    queue_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    logger = logging.getLogger()
    logger.addHandler(stream_handler)
    logger.addHandler(queue_handler)

    return logger


def set_file_logging(log_directory=None):    
    if log_directory is None:
        if getattr(sys, 'frozen', False):  # Check if the app is run as a frozen executable
            log_directory = os.path.dirname(sys.executable)  # Get the directory of the executable
        else:
            log_directory = os.path.dirname(sys.argv[0])  # Get the directory of the executable script

    log_directory = os.path.join(log_directory, "logs")  # Create a 'logs' directory in the script directory
    os.makedirs(log_directory, exist_ok=True)  # Create the directory if it doesn't exist


    # Create a timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_filename = os.path.join(log_directory, f"{timestamp}.log")


    # Configure logging
    handler = logging.FileHandler(log_filename)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s'))
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger



def get_log_queue(logger):
    for handler in get_all_handlers(logger):
        if isinstance(handler, QueueHandler):
            return handler.log_queue
    return None


def get_all_handlers(logger):
    """Retrieve all handlers attached to the logger and its parents."""
    handlers = []
    current_logger = logger
    while current_logger:
        handlers.extend(current_logger.handlers)
        current_logger = current_logger.parent
    return handlers

