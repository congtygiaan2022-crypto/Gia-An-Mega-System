import sys
import os
import importlib

# Bỏ qua lỗi Unicode khi in ra màn hình console Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

def trigger_image_workflow():
    print("--- Triggering ImageWorkflow Bug ---")
    sys.path.insert(0, r"E:\Gams-ImageWorkflow")
    try:
        if 'main' in sys.modules:
            del sys.modules['main']
        import main as iw_main
        # Đưa object {} thay vì config hoàn chỉnh sẽ gây ra KeyError khi truy cập config["profiles_dir"]
        iw_main.worker_thread("TestProfile", {}, "dummy.png", "test prompt", "test status")
    except Exception as e:
        print(f"Expected Exception in ImageWorkflow: {e}")
    finally:
        sys.path.pop(0)

def trigger_tiktok():
    print("--- Triggering TiktokDownloader Bug ---")
    sys.path.insert(0, os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')), 'Gams-TiktokDownloader'))
    try:
        if 'main' in sys.modules:
            del sys.modules['main']
        import main as tk_main
        # Truyền None vào tham số driver sẽ gây ra lỗi AttributeError khi scrape_channel gọi driver.get()
        tk_main.scrape_channel(None, "https://www.tiktok.com/@dummy")
    except Exception as e:
        print(f"Expected Exception in TiktokDownloader: {e}")
    finally:
        sys.path.pop(0)

def trigger_youtube():
    print("--- Triggering YoutubeDownloader Bug ---")
    sys.path.insert(0, os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')), 'Gams-YoutubeDownloader'))
    try:
        if 'main' in sys.modules:
            del sys.modules['main']
        import main as yt_main
        # Tương tự Tiktok, None cho driver
        yt_main.scrape_channel(None, "https://www.youtube.com/@dummy")
    except Exception as e:
        print(f"Expected Exception in YoutubeDownloader: {e}")
    finally:
        sys.path.pop(0)

def trigger_bcgame():
    print("--- Triggering ToolAutoBcgame Bug ---")
    sys.path.insert(0, os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')), 'Gams-ToolAutoBcgame'))
    try:
        from core.bug_tracker import report_bug
        # Giả lập một lỗi
        raise ValueError("Simulated logic crash in Bcgame SessionManager")
    except Exception as e:
        try:
            report_bug(exc=e, module="core.session", task="simulated_task", severity="ERROR")
        except:
            pass # ignore print errors
    finally:
        sys.path.pop(0)

def main():
    trigger_image_workflow()
    trigger_tiktok()
    trigger_youtube()
    trigger_bcgame()
    print("Hoàn tất tạo lỗi! Hãy kiểm tra file E:\\Gams Ai Jarvis Os\\logs\\find_bug.json")

if __name__ == "__main__":
    main()
