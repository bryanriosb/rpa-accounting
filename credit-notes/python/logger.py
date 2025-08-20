
from datetime import datetime, timezone
from eventbridge_reporter import send_event

class Logger:
    def __init__(self, portal_name: str, execution_id: str):
        self.portal_name = portal_name
        self.execution_id = execution_id

    def _log(self, level: str, message: str):
        """Imprime el log y envía el evento."""
        timestamp = datetime.now(timezone.utc).isoformat()
        log_message = f"[{timestamp}] [{self.portal_name}] [{level}] {message}"
        print(log_message)

        event_details = {
            'portalName': self.portal_name,
            'executionId': self.execution_id,
            'level': level,
            'message': message,
            'timestamp': timestamp
        }
        send_event(event_details)

    def info(self, message: str):
        self._log("INFO", message)

    def warn(self, message: str):
        self._log("WARN", message)

    def error(self, message: str):
        self._log("ERROR", message)
