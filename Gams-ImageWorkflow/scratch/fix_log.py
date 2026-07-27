import os

def main():
    filepath = "worker_process.py"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    old = (
        "                                try:\n"
        "                                    continue_btn.click(timeout=4000)\n"
        "                                except:\n"
        "                                    try:\n"
        "                                        continue_btn.click(force=True, timeout=2000)\n"
        "                                    except:\n"
        "                                        page.evaluate(\"el => el.click()\", continue_btn.element_handle())"
    )
    
    new = (
        "                                try:\n"
        "                                    continue_btn.click(timeout=4000)\n"
        "                                except:\n"
        "                                    try:\n"
        "                                        continue_btn.click(force=True, timeout=2000)\n"
        "                                    except:\n"
        "                                        page.evaluate(\"el => el.click()\", continue_btn.element_handle())\n"
        "                                p_log(profile_name, f\"[{profile_name}] Đã click 'Tiếp tục' sau khi chọn App xác thực\")\n"
        "                                page.wait_for_timeout(3000)"
    )
    
    if old in content:
        content = content.replace(old, new)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print("Successfully updated worker_process.py")
    else:
        print("Target substring not found!")

if __name__ == "__main__":
    main()
