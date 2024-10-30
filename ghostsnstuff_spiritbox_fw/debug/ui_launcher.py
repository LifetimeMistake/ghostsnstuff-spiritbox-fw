import subprocess
import time
from .. import logging

class DebugUI:
    def __init__(self, port: int = 8501):
        self.port = port
        self.process = None

    def start_server(self):
        if self.process is None:
            self.process = subprocess.Popen(
                [
                    "streamlit", "run", "ghostsnstuff_spiritbox_fw/debug/ui.py",
                    "--server.port", str(self.port),
                    "--server.headless", "true"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logging.print(f"Streamlit server started on port {self.port}")

    def stop_server(self):
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
                logging.print("Streamlit server stopped gracefully")
            except subprocess.TimeoutExpired:
                self.process.kill()
                logging.print("Streamlit server forcefully stopped")
            self.process = None

    def restart_server(self):
        self.stop_server()
        time.sleep(1)
        self.start_server()