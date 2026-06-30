import sys
import os
import logging
import asyncio
import json
import time
import psutil
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# Add parent dir to path for inner imports if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load env from javis-agent root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

# Setup logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    filename=os.path.join(log_dir, "telegram_bot.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("TelegramBotService")

PID_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "telegram_bot.pid")
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "plugin_settings.json")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = os.getenv("TELEGRAM_CHAT_ID")

import platform
import ctypes
from ctypes import wintypes
import io
import csv

def get_settings():
    """Tải cài đặt động từ plugin_settings.json hoặc fallback về env."""
    settings = {
        "TOKEN": TOKEN,
        "OWNERS": [ALLOWED_USER_ID] if ALLOWED_USER_ID else [],
        "COMMANDS": {}
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                p_settings = data.get("jarvis_telegram_report_assistant", {})
                if p_settings.get("token"): settings["TOKEN"] = p_settings["token"]
                if p_settings.get("owners"): 
                    owners = p_settings["owners"]
                    if isinstance(owners, list):
                        settings["OWNERS"] = [str(o) for o in owners]
                    else:
                        settings["OWNERS"] = [str(owners)]
                if p_settings.get("commands"):
                    settings["COMMANDS"] = p_settings["commands"]
        except Exception as e:
            logger.error(f"Lỗi đọc file settings: {e}")
    return settings

def is_owner(update: Update) -> bool:
    s = get_settings()
    owner_ids = s["OWNERS"]
    if not owner_ids:
        return True
    try:
        return str(update.effective_user.id) in [str(o) for o in owner_ids]
    except:
        return False

def list_desktop_apps():
    """Trích xuất thuật toán từ desktop_utils.py cũ."""
    if platform.system() != "Windows":
        return []

    user32 = ctypes.windll.user32
    apps = []
    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def _enum(hwnd, lParam):
        try:
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            try:
                p = psutil.Process(pid.value)
                exe = p.name()
                try: cpu = p.cpu_percent(interval=0.01)
                except: cpu = 0.0
                try: mem = round(p.memory_info().rss / (1024 ** 2), 1)
                except: mem = 0.0
            except:
                exe = None
                cpu = 0.0
                mem = 0.0
            apps.append({"title": title, "pid": pid.value, "exe": exe, "cpu": cpu, "mem_mb": mem})
        except:
            pass
        return True

    user32.EnumWindows(EnumWindowsProc(_enum), 0)
    seen = set()
    out = []
    for a in apps:
        key = (a.get("pid"), a.get("title"))
        if key not in seen:
            seen.add(key)
            out.append(a)
    return out

def bar(percent, length=18):
    """Vẽ thanh biểu đồ trạng thái."""
    filled = int(length * percent / 100)
    return "█" * filled + "░" * (length - filled)

def color_icon(percent):
    if percent < 40: return "🟢"
    if percent < 80: return "🟡"
    return "🔴"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("⛔ Jarvis không phục vụ bạn.")
        return
    await update.message.reply_text(
        "🤖 Jarvis Telegram Report Assistant đã sẵn sàng.\n\n"
        "🛠 NHÓM LỆNH HỆ THỐNG:\n"
        "/status - Tình trạng máy chủ (với biểu đồ)\n"
        "/analyze - Phân tích hệ thống bằng GPT\n"
        "/desktop_apps - Xem các cửa sổ Windows đang mở\n"
        "/apps_csv - Xuất CSV danh sách tiến trình\n"
        "/kill <PID/Name> - Tắt tiến trình\n\n"
        "📊 NHÓM LỆNH BÁO CÁO:\n"
        "/baocaofanpage - Báo cáo Insight Facebook\n"
        "/ping - Kiểm tra bot còn sống không\n"
        "/help - Xem chi tiết lệnh"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    s = get_settings()
    cmds = s.get("COMMANDS", {})
    
    msg = "📋 DANH SÁCH LỆNH JARVIS:\n━━━━━━━━━━━━━━━━━━\n"
    
    # Priority commands
    priority = ["baocaofanpage", "status", "analyze", "desktop_apps", "apps_csv", "kill", "adduser", "restart", "ping", "help"]
    
    for c in priority:
        if c in cmds:
            desc = cmds[c].replace("📊 ", "").replace("🔍 ", "").replace("📋 ", "").replace("📄 ", "").replace("🏓 ", "").replace("🔄 ", "").replace("👤 ", "").replace("❓ ", "").replace("🔪 ", "")
            msg += f"🔹 /{c}: {desc}\n"
        else:
            # Fallback for standard commands if not in JSON
            standard = {
                "baocaofanpage": "Báo cáo Insight Facebook",
                "status": "Tình trạng máy chủ (với biểu đồ)",
                "analyze": "Phân tích sức khỏe hệ thống",
                "desktop_apps": "Xem các cửa sổ Windows đang mở",
                "apps_csv": "Xuất CSV danh sách tiến trình",
                "kill": "Tắt một ứng dụng theo PID hoặc tên",
                "adduser": "Thêm người dùng quản trị",
                "restart": "Khởi động lại hệ thống",
                "ping": "Kiểm tra bot còn sống không",
                "help": "Hiển thị menu này"
            }
            if c in standard:
                msg += f"🔹 /{c}: {standard[c]}\n"

    # Add any other custom commands
    for c, desc in cmds.items():
        if c not in priority:
            msg += f"🔸 /{c}: {desc}\n"

    await update.message.reply_text(msg)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    
    # Lấy thông tin tất cả các ổ cứng
    disk_lines = []
    seen_mountpoints = set()
    
    # Hàm lấy tên/nhãn của ổ đĩa
    def get_volume_label(mountpoint):
        if platform.system() == "Windows":
            try:
                buf = ctypes.create_unicode_buffer(1024)
                res = ctypes.windll.kernel32.GetVolumeInformationW(mountpoint, buf, 1024, None, None, None, None, 0)
                if res and buf.value:
                    return buf.value
            except:
                pass
        return "Ổ đĩa cục bộ" if os.name == 'nt' else "Local Disk"
        
    try:
        partitions = psutil.disk_partitions(all=False)
    except:
        partitions = []
        
    for p in partitions:
        if p.mountpoint in seen_mountpoints:
            continue
        if os.name == 'nt' and 'cdrom' in p.opts.lower():
            continue
        try:
            usage = psutil.disk_usage(p.mountpoint)
            if usage.total > 0:
                label = get_volume_label(p.mountpoint)
                pct = usage.percent
                drive_name = p.mountpoint
                disk_lines.append(
                    f"{color_icon(pct)} DISK {drive_name} ({label}): `{bar(pct)}` {pct}%"
                )
                seen_mountpoints.add(p.mountpoint)
        except:
            pass
            
    # Dự phòng nếu không lấy được thông tin ổ đĩa nào
    if not disk_lines:
        try:
            default_path = 'C:\\' if os.name == 'nt' else '/'
            usage = psutil.disk_usage(default_path)
            pct = usage.percent
            label = "Ổ đĩa cục bộ" if os.name == 'nt' else "Local Disk"
            disk_lines.append(
                f"{color_icon(pct)} DISK {default_path} ({label}): `{bar(pct)}` {pct}%"
            )
        except:
            pass
            
    disk_status_str = "\n".join(disk_lines)
    
    msg = (
        "📊 **TRẠNG THÁI HỆ THỐNG**\n"
        f"⏱ {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}\n\n"
        f"{color_icon(cpu)} CPU: `{bar(cpu)}` {cpu}%\n"
        f"{color_icon(ram)} RAM: `{bar(ram)}` {ram}%\n"
        f"{disk_status_str}"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')


async def analyze_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    await update.message.reply_text("🔍 Đang phân tích hệ thống bằng AI, vui lòng chờ...")
    try:
        from core.agent import JavisAgent
        agent = JavisAgent()
        response = agent.run("Hãy phân tích trạng thái hệ thống hiện tại (CPU, RAM, Disk) và đưa ra lời khuyên ngắn gọn.")
        msg = response.get("result", str(response)) if isinstance(response, dict) else response
        await update.message.reply_text(f"🧠 **PHÂN TÍCH AI:**\n\n{msg}", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi phân tích: {e}")

async def desktop_apps_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    try:
        apps = list_desktop_apps()
        if not apps:
            await update.message.reply_text("Không phát hiện ứng dụng desktop nào.")
            return

        header = f"📋 **DANH SÁCH ỨNG DỤNG** ({len(apps)})\n━━━━━━━━━━━━━━━━━━\n"
        lines = [header]
        for i, a in enumerate(apps[:25], start=1): # Limit to 25 to avoid message length issues
            lines.append(f"{i}. **{a['title'][:50]}**")
            lines.append(f"   └ `{a['exe']}` | PID: `{a['pid']}` | {a['mem_mb']}MB\n")
        
        await update.message.reply_text("\n".join(lines), parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {e}")

async def apps_csv_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    try:
        apps = list_desktop_apps()
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["pid", "title", "exe", "cpu", "mem_mb"])
        writer.writeheader()
        writer.writerows(apps)
        output.seek(0)
        
        bio = io.BytesIO(output.read().encode('utf-8-sig'))
        bio.name = f"apps_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        await update.message.reply_document(document=bio, filename=bio.name, caption="📄 Danh sách ứng dụng đang chạy.")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi xuất CSV: {e}")

async def kill_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    if not context.args:
        await update.message.reply_text("Sử dụng: `/kill <PID hoặc Tên tiến trình>`")
        return
    
    target = context.args[0]
    try:
        count = 0
        if target.isdigit():
            p = psutil.Process(int(target))
            name = p.name()
            p.kill()
            count = 1
            await update.message.reply_text(f"✅ Đã tắt tiến trình: {name} (PID: {target})")
        else:
            for p in psutil.process_iter(['name']):
                if p.info['name'].lower() == target.lower():
                    p.kill()
                    count += 1
            if count > 0:
                await update.message.reply_text(f"✅ Đã tắt {count} tiến trình có tên: {target}")
            else:
                await update.message.reply_text(f"❌ Không tìm thấy tiến trình nào tên: {target}")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi khi tắt: {e}")

async def adduser_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    if not context.args:
        await update.message.reply_text("Sử dụng: `/adduser <TELEGRAM_ID>`")
        return
    
    new_id = context.args[0]
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        p_settings = data.get("jarvis_telegram_report_assistant", {})
        owners = p_settings.get("owners", [])
        if not isinstance(owners, list): owners = [str(owners)]
        
        if str(new_id) not in owners:
            owners.append(str(new_id))
            p_settings["owners"] = owners
            data["jarvis_telegram_report_assistant"] = p_settings
            
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            await update.message.reply_text(f"✅ Đã thêm ID `{new_id}` vào danh sách quản trị.")
        else:
            await update.message.reply_text(f"ℹ️ ID `{new_id}` đã có trong danh sách.")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {e}")

async def restart_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    await update.message.reply_text("🔄 Đang khởi động lại hệ thống...")
    try:
        from ui.server import restart_server
        restart_server()
    except:
        # Fallback if UI is not connected
        os.utime(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "main.py"), None)

async def baocaofanpage_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    
    # Path to Gams_ViewInsight links.json
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "gams_insight", "links.json")
    
    if not os.path.exists(file_path):
        await update.message.reply_text(f"❌ Không tìm thấy file báo cáo tại:\n`{file_path}`")
        return

    def escape_markdown(text):
        if not isinstance(text, str): text = str(text)
        return text.replace("*", "").replace("_", "").replace("`", "")

    def parse_metric(text):
        if not text or not isinstance(text, str): return 0.0
        import re
        val_str = text.split('(')[0].strip().lower()
        
        multiplier = 1.0
        if 'tỷ' in val_str or 'b' in val_str:
            multiplier = 1_000_000_000.0
        elif 'triệu' in val_str or 'tr' in val_str or 'm' in val_str:
            multiplier = 1_000_000.0
        elif 'k' in val_str or 'nghìn' in val_str or 'ngàn' in val_str:
            multiplier = 1_000.0
            
        match = re.search(r'([\d\.,]+)', val_str)
        if not match:
            return 0.0
        num_str = match.group(1)
        
        if ',' in num_str and '.' in num_str:
            if num_str.find('.') < num_str.find(','):
                num_str = num_str.replace('.', '').replace(',', '.')
            else:
                num_str = num_str.replace(',', '')
        elif ',' in num_str:
            parts = num_str.split(',')
            if len(parts) == 2:
                decimal_part = parts[1]
                if len(decimal_part) == 3 and multiplier == 1.0:
                    num_str = num_str.replace(',', '')
                else:
                    num_str = num_str.replace(',', '.')
            else:
                num_str = num_str.replace(',', '')
        elif '.' in num_str:
            parts = num_str.split('.')
            if len(parts) == 2:
                decimal_part = parts[1]
                if len(decimal_part) == 3 and multiplier == 1.0:
                    num_str = num_str.replace('.', '')
                else:
                    pass
            else:
                num_str = num_str.replace('.', '')
                
        try:
            return float(num_str) * multiplier
        except:
            return 0.0


    def format_metric(val):
        if val >= 1_000_000: return f"{val/1_000_000:.1f}M".replace(".0M", "M")
        if val >= 1_000: return f"{val/1_000:.1f}K".replace(".0K", "K")
        return f"{int(val)}"

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            await update.message.reply_text("📭 File báo cáo trống.")
            return

        items = data if isinstance(data, list) else [data]
        header = f"📊 **BÁO CÁO FANPAGE INSIGHT**\n📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n━━━━━━━━━━━━━━━━━━\n"

        current_message = header
        messages_to_send = []

        total_pages = len(items)
        sum_total_followers = sum_new_followers = sum_interactions = sum_views = 0.0
        periods = set()

        for item in items:
            page_name = escape_markdown(item.get("page_name", "N/A"))
            inner_data = item.get("data", {})
            
            raw_followers = inner_data.get("Theo dõi", inner_data.get("Lượt theo dõi", "0"))
            raw_interactions = inner_data.get("Tương tác", inner_data.get("Lượt tương tác", "0"))
            raw_views = inner_data.get("Xem", inner_data.get("Lượt xem", "0"))
            raw_period = inner_data.get("Thời gian", "N/A")
            raw_total_followers = item.get("total_followers", "0")
            
            sum_total_followers += parse_metric(raw_total_followers)
            sum_new_followers += parse_metric(raw_followers)
            sum_interactions += parse_metric(raw_interactions)
            sum_views += parse_metric(raw_views)
            if raw_period != "N/A": periods.add(raw_period)

            item_text = (
                f"🚩 **{page_name}**\n"
                f"👤 Follow: `{raw_total_followers}` | 📈 Mới: `{raw_followers}`\n"
                f"🤝 Tương tác: `{raw_interactions}` | 👁️ Xem: `{raw_views}`\n"
                f"📅 `{raw_period}`\n"
                "──────────────────\n"
            )

            if len(current_message) + len(item_text) > 3000:
                messages_to_send.append(current_message)
                current_message = header + item_text
            else:
                current_message += item_text

        summary_period = ", ".join(sorted(list(periods))) if periods else "N/A"
        summary_text = (
            "🎯 **TỔNG KẾT HỆ THỐNG**\n"
            f"📑 Số Fanpage: `{total_pages}`\n"
            f"👥 Tổng Follow: `{format_metric(sum_total_followers)}`\n"
            f"📈 Theo dõi mới: `{format_metric(sum_new_followers)}`\n"
            f"🤝 Tương tác: `{format_metric(sum_interactions)}`\n"
            f"👁️ Lượt xem: `{format_metric(sum_views)}`\n"
            "━━━━━━━━━━━━━━━━━━\n"
        )

        current_message += summary_text
        messages_to_send.append(current_message)

        for msg in messages_to_send:
            await update.message.reply_text(msg, parse_mode='Markdown')
            
    except Exception as e:
        logger.exception("Error in baocaofanpage_cmd")
        await update.message.reply_text(f"❌ Lỗi đọc báo cáo: {e}")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("pong 🏓")

async def unknown_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    text = update.message.text
    if not text: return

    # Check custom commands first
    if text.startswith('/'):
        cmd_name = text.split()[0][1:].lower()
        s = get_settings()
        custom_cmds = s.get("COMMANDS", {})
        if cmd_name in custom_cmds:
            await update.message.reply_text(custom_cmds[cmd_name])
            return

    # Fallback to Javis AI
    try:
        from core.agent import JavisAgent
        agent = JavisAgent()
        prompt = text[1:] if text.startswith('/') else text
        response = agent.run(prompt)
        msg = response.get("result", str(response)) if isinstance(response, dict) else response
        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"Error AI fallback: {e}")
        if text.startswith('/'):
            await update.message.reply_text(f"❓ Lệnh không xác định: {text}")

def write_pid():
    pid = os.getpid()
    with open(PID_FILE, 'w') as f:
        f.write(str(pid))
    logger.info(f"Đã bắt đầu dịch vụ bot với PID: {pid}")

def run_bot():
    s = get_settings()
    bot_token = s["TOKEN"]
    
    if not bot_token or bot_token == "YOUR_TELEGRAM_BOT_TOKEN":
        logger.error("Không tìm thấy TELEGRAM_BOT_TOKEN hợp lệ!")
        return

    # PID is now handled by isolated_runner.py
    write_pid()
    
    app = ApplicationBuilder().token(bot_token).build()
    # Register builtin commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("analyze", analyze_cmd))
    app.add_handler(CommandHandler("desktop_apps", desktop_apps_cmd))
    app.add_handler(CommandHandler("apps", desktop_apps_cmd))
    app.add_handler(CommandHandler("apps_csv", apps_csv_cmd))
    app.add_handler(CommandHandler("kill", kill_cmd))
    app.add_handler(CommandHandler("adduser", adduser_cmd))
    app.add_handler(CommandHandler("restart", restart_cmd))
    app.add_handler(CommandHandler("baocaofanpage", baocaofanpage_cmd))
    app.add_handler(CommandHandler("ping", ping))
    
    # Register custom commands from UI
    custom_cmds = s.get("COMMANDS", {})
    builtin_names = ["start", "help", "status", "analyze", "desktop_apps", "apps", "apps_csv", "kill", "adduser", "restart", "baocaofanpage", "ping"]
    for cmd_name in custom_cmds:
        if cmd_name not in builtin_names:
            app.add_handler(CommandHandler(cmd_name, unknown_handler))
            logger.info(f"Registered custom command: /{cmd_name}")
    
    # Global handler for other things
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), unknown_handler))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_handler))

    logger.info("Bot đang chạy với cấu hình mới...")
    app.run_polling()

if __name__ == "__main__":
    run_bot()

if __name__ == "__main__":
    run_bot()
