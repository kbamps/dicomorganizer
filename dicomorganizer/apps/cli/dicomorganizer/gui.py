import logging
import threading
import tkinter as tk
from tkinter import scrolledtext

from dicomorganizer.apps.cli.dicomorganizer.log_config import get_log_queue, set_queue_logging

class LogDisplay(tk.Frame):
    """
    A scrollable text field UI block that displays logs from a queue.
    It polls the logger queue every 100ms and updates itself.
    """
    def __init__(self, parent, poll_interval=100, height=10, width=50):
        super().__init__(parent)        
        self.log_queue = set_queue_logging()
        self.poll_interval = poll_interval

        self.text_widget = scrolledtext.ScrolledText(self, height=height, width=width, state=tk.NORMAL)
        self.text_widget.pack(expand=True, fill='both')

        self.update_logs()

    def update_logs(self):
        """Poll the logger queue and update the text widget."""
        if self.log_queue:
            while not self.log_queue.empty():
                message = self.log_queue.get()
                self.text_widget.insert(tk.END, message)
                self.text_widget.see(tk.END)
        self.after(self.poll_interval, self.update_logs)


def create_log_display(function):
    # Create the GUI window

    def run_function(root):
        function()
        root.after(0, root.quit)  # Close the GUI after the function completes

    root = tk.Tk()
    root.title("Dicom Organizer Logs")
    root.geometry("800x600")

    log_frame = LogDisplay(root)
    log_frame.pack(expand=True, fill="both")

    t = threading.Thread(target=run_function, args=(root,), daemon=True)
    t.start()

    def check_thread():
        if not t.is_alive():
            root.quit()
        else:
            root.after(500, check_thread)

    root.after(500, check_thread)
    root.mainloop()       




if __name__ == "__main__":

    # Simulate logging from any code
    import time
    logger = logging.getLogger("simulated_logger")
    def log_writer():
        count = 0
        while True:
            logger.info(f"Simulated log message #{count}")
            count += 1
            time.sleep(1)

    threading.Thread(target=log_writer, daemon=True).start()

    create_log_display()