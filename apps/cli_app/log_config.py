import logging
import os
import sys
from datetime import datetime

def setup_logging():
    # Check if logging is already configured
    if logging.getLogger().hasHandlers():
        return logging.getLogger()  # Return the existing logger

    if getattr(sys, 'frozen', False):  # Check if the app is run as a frozen executable
        log_directory = os.path.dirname(sys.executable)  # Get the directory of the executable
    else:
        log_directory = os.path.dirname(sys.argv[0])  # Get the directory of the executable script
    
    log_directory = os.path.join(log_directory, "logs")  # Create a 'logs' directory in the script directory
    os.makedirs(log_directory, exist_ok=True)  # Create the directory if it doesn't exist

    # Create a timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_filename = os.path.join(log_directory, f"dicom_anonymization_{timestamp}.log")

    # Configure logging
    handlers = [logging.FileHandler(log_filename), logging.StreamHandler(sys.stdout)] if (sys.gettrace() is not None) else [logging.FileHandler(log_filename)]
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s - [File: %(filename)s, Line: %(lineno)d]',
        handlers=handlers
    )

    return logging.getLogger(__name__)
