"""
computer/vision_engine.py — Screen OCR + coordinate detection
Dependencies: pytesseract, opencv-python, pyautogui, Pillow
Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
"""
import os
import time

try:
    import pytesseract
    import cv2
    import numpy as np
    import pyautogui
    from PIL import Image
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False

# On Windows, Tesseract may need explicit path
TESSERACT_PATH = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if VISION_AVAILABLE and os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


class VisionEngine:
    """
    Screen capture + OCR-based UI interaction.
    Finds text on screen and clicks it — no CSS selectors needed.
    """

    def _check(self):
        if not VISION_AVAILABLE:
            return "Vision dependencies not installed. Run: pip install pytesseract opencv-python pyautogui"
        return None

    def capture(self, save: bool = True) -> "np.ndarray | None":
        """Take a screenshot and return as OpenCV BGR array."""
        err = self._check()
        if err:
            print(err)
            return None
        img = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        if save:
            os.makedirs("data/screenshots", exist_ok=True)
            path = f"data/screenshots/vision_{int(time.time())}.png"
            cv2.imwrite(path, frame)
        return frame

    def read_screen(self) -> str:
        """OCR the entire screen and return all visible text."""
        err = self._check()
        if err:
            return err
        frame = self.capture(save=False)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray)
        return text.strip()

    def find_text(self, target: str) -> dict | None:
        """
        Scan the screen and find the bounding box of `target` text.
        Returns {"x": cx, "y": cy, "found": True} or None.
        """
        err = self._check()
        if err:
            print(err)
            return None

        frame = self.capture(save=False)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
        words = data["text"]
        for i, word in enumerate(words):
            if target.lower() in word.lower():
                x = data["left"][i]
                y = data["top"][i]
                w = data["width"][i]
                h = data["height"][i]
                cx = x + w // 2
                cy = y + h // 2
                return {"x": cx, "y": cy, "word": word, "found": True}
        return None

    def click_text(self, text: str) -> str:
        """Find text on screen and click its center position."""
        result = self.find_text(text)
        if result and result.get("found"):
            pyautogui.click(result["x"], result["y"])
            return f"Clicked '{text}' at ({result['x']}, {result['y']})"
        return f"Text '{text}' not found on screen"

    def type_text(self, text: str) -> str:
        """Type text using keyboard (into focused element)."""
        err = self._check()
        if err:
            return err
        pyautogui.typewrite(text, interval=0.05)
        return f"Typed: '{text}'"

    def is_available(self) -> bool:
        return VISION_AVAILABLE


# Global singleton
vision_engine = VisionEngine()
