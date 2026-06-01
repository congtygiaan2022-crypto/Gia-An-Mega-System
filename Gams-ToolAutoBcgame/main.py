from gui.main_window import MainWindow
import os
import sys

# Thêm thư mục gốc vào PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Add Jarvis OS core for global logger
JARVIS_CORE_PATH = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')), 'Gams-AiJarvisOs', 'core')
if JARVIS_CORE_PATH not in sys.path:
    sys.path.insert(0, JARVIS_CORE_PATH)
try:
    import global_logger
except ImportError:
    global_logger = None

def main():
    try:
        app = MainWindow()
        app.run()
    except Exception as e:
        print(f"Lỗi khởi động Dashboard: {e}")
        if global_logger:
            import traceback
            global_logger.report_bug("ToolAutoBcgame", "main", str(e), {"traceback": traceback.format_exc()})

if __name__ == "__main__":
    main()
