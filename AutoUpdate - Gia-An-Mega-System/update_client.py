import os
import re
import sys
import subprocess

def fix_paths_for_client(root_dir, gams_folders):
    mapping = {f: f for f in gams_folders}
    if not mapping:
        return

    print("[*] Updating paths in Python scripts to match client directory structure...")
    pattern = re.compile(
        r'([rRfF]*)([\'"])(?:[a-zA-Z]:[\\/]+(?:Tool_tucode|GitUpload|Auto - Update-Gia-An-Mega-System)[\\/]+)?((?:' + 
        '|'.join(re.escape(k) for k in mapping.keys()) + 
        r'))([\\/]?.*?)\2', 
        re.IGNORECASE
    )

    def get_relative_root_code(file_path, base_dir):
        rel_path = os.path.relpath(base_dir, os.path.dirname(file_path))
        parts = rel_path.split(os.sep)
        if parts == ['.'] or parts == ['']:
            return "os.path.dirname(os.path.abspath(__file__))"
        dots = ", ".join(f"'{p}'" for p in parts)
        return f"os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), {dots}))"

    def process_file(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return False

        original_content = content
        needed_import = False

        def replacer(match):
            nonlocal needed_import
            prefix = match.group(1)
            quote = match.group(2)
            old_name = match.group(3)
            rest = match.group(4)
            
            matched_key = next((k for k in mapping.keys() if k.lower() == old_name.lower()), old_name)
            new_name = mapping.get(matched_key, matched_key)
            
            needed_import = True
            root_code = get_relative_root_code(filepath, root_dir)
            
            if rest:
                rest = rest.lstrip('\\/')
                if rest:
                    rest_repr = repr(rest)
                    return f"os.path.join({root_code}, '{new_name}', {rest_repr})"
            return f"os.path.join({root_code}, '{new_name}')"

        new_content = pattern.sub(replacer, content)

        sys_pattern = re.compile(
            r'sys\.path\.append\([rRfF]*([\'"])(?:[a-zA-Z]:[\\/]+(?:Tool_tucode|GitUpload|Auto - Update-Gia-An-Mega-System)[\\/]+)?([^\'"]+)\1\)', 
            re.IGNORECASE
        )
        
        def sys_replacer(match):
            nonlocal needed_import
            quote = match.group(1)
            sub_path = match.group(2)
            
            parts = sub_path.replace('\\', '/').split('/')
            if parts[0] in mapping:
                parts[0] = mapping[parts[0]]
                
            needed_import = True
            root_code = get_relative_root_code(filepath, root_dir)
            path_args = ", ".join(repr(p) for p in parts if p)
            return f"sys.path.append(os.path.join({root_code}, {path_args}))"

        new_content = sys_pattern.sub(sys_replacer, new_content)

        if new_content != original_content:
            if needed_import and 'import os' not in new_content:
                new_content = "import os\n" + new_content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        return False

    modified_count = 0
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if any(d in dirpath for d in ['.git', '__pycache__', 'venv', '.venv', 'env', 'node_modules']):
            continue
        for file in filenames:
            if file.endswith('.py'):
                filepath = os.path.join(dirpath, file)
                if process_file(filepath):
                    modified_count += 1
                    
    print(f"[OK] Dynamic path optimization finished. Modified {modified_count} files.")

def download_ffmpeg_if_needed(project_path):
    ffmpeg_path = os.path.join(project_path, "ffmpeg.exe")
    if not os.path.exists(ffmpeg_path):
        print("  -> ffmpeg.exe is missing. Downloading automatically...")
        import urllib.request
        # A reliable, fast static direct URL to a standard ffmpeg.exe for Windows
        url = "https://github.com/eugeneoden/ffmpeg-windows-builds/releases/download/1.0.0/ffmpeg.exe"
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                with open(ffmpeg_path, 'wb') as f:
                    f.write(response.read())
            print("  -> [OK] Downloaded ffmpeg.exe successfully.")
        except Exception as e:
            print(f"  -> [WARN] Failed to download ffmpeg.exe automatically: {e}")
            print("     Please download and copy ffmpeg.exe to the folder manually if needed.")

def main():
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    root_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"===================================================\n"
          f"     GAMS AUTO-UPDATE CLIENT INSTALLATION TOOL\n"
          f"===================================================\n")
    print(f"Current installation path: {root_dir}\n")

    # 1. Check if git is initialized and pull/clone from repository
    repo_url = "https://github.com/congtygiaan2022-crypto/Gia-An-Mega-System.git"
    git_dir = os.path.join(root_dir, ".git")
    
    if not os.path.exists(git_dir):
        print("[*] Initializing local repository on client machine...")
        try:
            subprocess.run(["git", "init"], cwd=root_dir, check=True)
            subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=root_dir, check=True)
            print("[*] Downloading software source code from Git repository...")
            subprocess.run(["git", "pull", "origin", "main"], cwd=root_dir, check=True)
            subprocess.run(["git", "branch", "-M", "main"], cwd=root_dir, check=True)
            print("[OK] Clone completed successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to download from git repository: {e}")
            return
    else:
        print("[*] Checking for updates and pulling latest changes...")
        try:
            # Clean local modifications if any to avoid pull conflicts
            subprocess.run(["git", "reset", "--hard"], cwd=root_dir, check=True)
            subprocess.run(["git", "pull", "origin", "main"], cwd=root_dir, check=True)
            print("[OK] Update completed successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to fetch updates: {e}")
            return

    # 2. Discover Gams- folders that were pulled
    gams_folders = []
    for item in os.listdir(root_dir):
        item_path = os.path.join(root_dir, item)
        if os.path.isdir(item_path) and item.startswith("Gams-"):
            gams_folders.append(item)

    if not gams_folders:
        print("[ERROR] No projects starting with 'Gams-' were found after update.")
        return

    # 3. Run path optimization
    fix_paths_for_client(root_dir, gams_folders)

    # 4. Process requirements and create CMD commands for each project
    for folder in gams_folders:
        project_path = os.path.join(root_dir, folder)
        print(f"\n[*] Processing: {folder}")
        
        # Download FFMPEG for Youtube Downloader if it's missing
        if "youtubedownloader" in folder.lower():
            download_ffmpeg_if_needed(project_path)
            
        req_path = os.path.join(project_path, "requirements.txt")
        if os.path.exists(req_path):
            print(f"  -> Installing requirements from: requirements.txt")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                    cwd=project_path, 
                    check=True
                )
                print(f"  -> [OK] Successfully installed requirements.")
            except Exception as e:
                print(f"  -> [WARN] Error installing requirements: {e}")

        script = None
        if os.path.exists(os.path.join(project_path, "gui.py")):
            script = "gui.py"
        elif os.path.exists(os.path.join(project_path, "app.py")):
            script = "app.py"
        elif os.path.exists(os.path.join(project_path, "main.py")):
            script = "main.py"

        if script:
            start_cmd = os.path.join(project_path, "start.cmd")
            stop_cmd = os.path.join(project_path, "stop.cmd")
            dashboard_cmd = os.path.join(project_path, "dashboard.cmd")

            # Writing start.cmd with CRLF line endings
            with open(start_cmd, "w", encoding="utf-8", newline='\r\n') as f:
                f.write(
                    f'@echo off\r\n'
                    f'chcp 65001 >nul 2>&1\r\n'
                    f'cd /d "%~dp0"\r\n'
                    f'echo Starting {folder}...\r\n'
                    f'pm2 start {script} --name "{folder}" --interpreter python\r\n'
                    f'pause\r\n'
                )

            # Writing stop.cmd with CRLF line endings
            with open(stop_cmd, "w", encoding="utf-8", newline='\r\n') as f:
                f.write(
                    f'@echo off\r\n'
                    f'chcp 65001 >nul 2>&1\r\n'
                    f'echo Stopping {folder}...\r\n'
                    f'pm2 stop "{folder}"\r\n'
                    f'pause\r\n'
                )

            # Writing dashboard.cmd with CRLF line endings
            with open(dashboard_cmd, "w", encoding="utf-8", newline='\r\n') as f:
                f.write(
                    f'@echo off\r\n'
                    f'chcp 65001 >nul 2>&1\r\n'
                    f'echo Fetching logs for {folder}...\r\n'
                    f'pm2 logs "{folder}"\r\n'
                    f'pause\r\n'
                )
            print(f"  -> [OK] Generated start/stop/dashboard.cmd scripts.")

    print("\n===================================================\n"
          "     CLIENT INSTALLATION / UPDATE COMPLETE!\n"
          "===================================================")

if __name__ == "__main__":
    main()
