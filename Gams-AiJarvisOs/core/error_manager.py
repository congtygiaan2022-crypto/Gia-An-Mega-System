"""
core/error_manager.py — Simple retry counter to stop infinite repair loops.
Delegates details to core/error_registry.py (which has cooldown & timestamps).
This file provides the minimal v2 interface described in the architecture spec.
"""
import time

MAX_RETRIES = 3
COOLDOWN_SECONDS = 300


class ErrorManager:
    def __init__(self):
        self.retry: dict = {}          # { error_name: count }
        self._blocked_until: dict = {} # { error_name: timestamp }

    def check(self, error: str) -> bool:
        """
        Returns True if the error is allowed to be handled (retry < MAX_RETRIES).
        Returns False when retry limit exceeded (triggers cooldown).
        """
        now = time.time()

        # Still in cooldown?
        if self._blocked_until.get(error, 0) > now:
            return False

        if error not in self.retry:
            self.retry[error] = 0

        self.retry[error] += 1

        if self.retry[error] > MAX_RETRIES:
            self._blocked_until[error] = now + COOLDOWN_SECONDS
            print(f"[ErrorManager] '{error}' exceeded {MAX_RETRIES} retries. Cooldown {COOLDOWN_SECONDS}s.")
            return False

        print(f"[ErrorManager] '{error}' retry {self.retry[error]}/{MAX_RETRIES}")
        return True

    def clear(self, error: str):
        """Call after a successful fix."""
        self.retry.pop(error, None)
        self._blocked_until.pop(error, None)
        print(f"[ErrorManager] '{error}' cleared after successful fix.")

    def is_blocked(self, error: str) -> bool:
        return self._blocked_until.get(error, 0) > time.time()


# Global singleton
error_manager = ErrorManager()
