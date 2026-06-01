import os
import sys
import re
import json
import time
import subprocess
import shutil
import hashlib
import requests
from dotenv import load_dotenv

# Load env variables if .env file exists
load_dotenv()

# Configuration settings
API_KEY = os.getenv("ANTHROPIC_API_KEY")
BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1/messages")
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
MAX_RETRIES = 5

# Ensure we are in workspace root
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(WORKSPACE_DIR, "backup_code")

# Colors for terminal styling
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log_info(msg):
    print(f"{Colors.BLUE}[INFO] {msg}{Colors.ENDC}")

def log_success(msg):
    print(f"{Colors.GREEN}[SUCCESS] {msg}{Colors.ENDC}")

def log_warning(msg):
    print(f"{Colors.WARNING}[WARNING] {msg}{Colors.ENDC}")

def log_error(msg):
    print(f"{Colors.FAIL}[ERROR] {msg}{Colors.ENDC}")

def run_command(args, env=None):
    """Runs a system command and returns stdout, stderr, and exit code."""
    try:
        # Run with default system environment + custom environment modifications
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        
        # We run the command and capture output
        process = subprocess.run(
            args,
            capture_output=True,
            text=True,
            cwd=WORKSPACE_DIR,
            env=run_env
        )
        return process.stdout, process.stderr, process.returncode
    except Exception as e:
        return "", f"Exception running command {args}: {str(e)}", -1

def git_commit(message):
    """Commits changes in the repository to track self-healing history."""
    stdout, stderr, code = run_command(["git", "status", "--porcelain"])
    if not stdout.strip():
        log_info("Git: No changes to commit.")
        return
        
    log_info(f"Git: Committing changes with message: '{message}'")
    run_command(["git", "add", "."])
    _, _, commit_code = run_command(["git", "commit", "-m", message])
    if commit_code == 0:
        log_success("Git: Changes committed successfully.")
    else:
        log_warning("Git: Failed to create commit (check credentials or settings).")

def make_file_backup(filepath):
    """Makes a physical backup of a file in the backup_code directory."""
    if not os.path.exists(filepath):
        return
    
    os.makedirs(BACKUP_DIR, exist_ok=True)
    rel_path = os.path.relpath(filepath, WORKSPACE_DIR)
    
    # Create the target directory structure inside backup_code
    backup_path = os.path.join(BACKUP_DIR, rel_path)
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    
    shutil.copy2(filepath, backup_path)
    log_info(f"Backup: Saved file {rel_path} to backup_code/")

def classify_error(log_content):
    """Classifies the error log into specific types to send hints to Claude."""
    lower_log = log_content.lower()
    
    # ChromeDriver / Chrome / Selenium Errors
    if any(k in lower_log for k in ["chromedriver", "selenium", "chrome not reachable", "session not created", "unable to initialize logging", "only one of --log-level, --verbose, or --silent"]):
        return "Chrome/Selenium Driver Error", "The issue is related to Chrome/ChromeDriver or Selenium driver capabilities initialization."
        
    # Syntax, Name, or Import Errors
    if "syntaxerror" in lower_log or "indentationerror" in lower_log or "taberror" in lower_log:
        return "Python Syntax Error", "The code has indentation or syntax violations."
    if "importerror" in lower_log or "modulenotfounderror" in lower_log:
        return "Python Import Error", "A package or module import failed. Consider verifying requirements.txt or installed modules."
    if "nameerror" in lower_log:
        return "Python Name Error", "An undefined variable or function name is being referenced."
        
    # Permission Error
    if "permissionerror" in lower_log or "access is denied" in lower_log:
        return "Permission Error", "File or directory permissions are blocking read/write access."
        
    # API / Connection Timeouts
    if any(k in lower_log for k in ["timeout", "connectionerror", "connection refused", "urllib.error", "requests.exceptions"]):
        return "API / Network Error", "Connection timed out, API refused to connect, or network is down."
        
    return "Generic Runtime Error", "An unhandled exception or crash occurred in the Python script."

def parse_traceback(log_content):
    """Extracts python file paths mentioned in tracebacks that are part of the workspace."""
    # Find all pattern: File "path", line line_num
    # Matches: File "D:\laptrinh_code\fb_copyright_checker\main.py", line 43
    pattern = r'File\s+"([^"]+)"\,\s+line\s+(\d+)'
    matches = re.findall(pattern, log_content)
    
    referenced_files = []
    for filepath, line in matches:
        # Check if the file resides within our workspace and exists
        abs_path = os.path.abspath(filepath) if os.path.isabs(filepath) else os.path.join(WORKSPACE_DIR, filepath)
        if os.path.exists(abs_path) and abs_path.startswith(WORKSPACE_DIR):
            rel_path = os.path.relpath(abs_path, WORKSPACE_DIR)
            if rel_path not in referenced_files and "ai_runner.py" not in rel_path:
                referenced_files.append(rel_path)
                
    return referenced_files

def extract_json(response_text):
    """Robustly extracts JSON object from API response text."""
    # Try finding markdown code block ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL | re.IGNORECASE)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
            
    # Try finding any JSON-like substring starting with { and ending with }
    match = re.search(r"(\{.*\})", response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
            
    # Direct decode attempt
    return json.loads(response_text)

def query_claude(error_log, classified_type, classification_hint, file_contexts):
    """Calls the Claude API to request a fix for the error."""
    if not API_KEY:
        raise ValueError("Missing ANTHROPIC_API_KEY environment variable. Cannot call Claude API.")

    system_prompt = """You are an expert AI software agent designed to automatically fix bugs in a Python codebase.
Your task is to analyze the crash traceback/error logs and the associated source files, then return a corrected version of the code that resolves the issue.

You MUST respond strictly in the following JSON format:
{
  "explanation": "A brief explanation of why the crash occurred and how your fix resolves it.",
  "files": [
    {
      "path": "relative/path/to/file.py",
      "content": "The exact full corrected content of the file. You must return the ENTIRE file contents, not a diff."
    }
  ]
}

Only return this JSON inside a ```json ... ``` markdown block. Do not provide any conversational text outside the block. Keep it strictly non-interactive and ready for automatic parsing."""

    # Build prompt context with relevant file content
    context_str = ""
    for path in file_contexts:
        abs_path = os.path.join(WORKSPACE_DIR, path)
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
            context_str += f"\n--- FILE: {path} ---\n{content}\n"
        except Exception as e:
            log_warning(f"Could not read file context {path}: {str(e)}")

    user_message = f"""Here is a crash report in my project.

--- ERROR TYPE ---
{classified_type}: {classification_hint}

--- CRASH LOG ---
{error_log}

--- RELEVANT FILES CONTENT ---
{context_str}

Please return the JSON block with the corrected file contents to resolve the crash."""

    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "max_tokens": 4000,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_message}
        ]
    }
    
    # Construct correct API URL
    api_url = BASE_URL
    if not api_url.endswith("/v1/messages") and not api_url.endswith("/messages"):
        if api_url.endswith("/v1") or api_url.endswith("/v1/"):
            api_url = api_url.rstrip("/") + "/messages"
        else:
            api_url = api_url.rstrip("/") + "/v1/messages"

    max_api_retries = 3
    response = None
    for api_attempt in range(1, max_api_retries + 1):
        try:
            log_info(f"Claude API: Sending crash report to model '{MODEL}' at '{api_url}' (Attempt {api_attempt}/{max_api_retries})...")
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                break
            log_warning(f"Claude API returned status code {response.status_code}. Retrying in {api_attempt * 5}s...")
        except requests.exceptions.RequestException as e:
            log_warning(f"Request connection issue: {str(e)}. Retrying in {api_attempt * 5}s...")
        time.sleep(api_attempt * 5)
    else:
        if response is not None:
            raise RuntimeError(f"Claude API call failed after {max_api_retries} attempts (HTTP {response.status_code}): {response.text}")
        else:
            raise RuntimeError(f"Claude API call failed after {max_api_retries} attempts due to network connectivity issues.")

    res_data = response.json()
    response_text = res_data["content"][0]["text"]
    
    try:
        fix_json = extract_json(response_text)
        return fix_json
    except Exception as e:
        log_error(f"Failed to parse Claude response as JSON. Response text was:\n{response_text}")
        raise RuntimeError(f"Response format error: {str(e)}")

def apply_fix(fix_json):
    """Applies the fixes to the files in the workspace."""
    explanation = fix_json.get("explanation", "No explanation provided.")
    files = fix_json.get("files", [])
    
    log_info(f"Claude Explanation: {explanation}")
    
    applied_files = []
    for file_info in files:
        rel_path = file_info.get("path")
        content = file_info.get("content")
        
        if not rel_path or content is None:
            continue
            
        # Security check: ensure path does not escape workspace directory
        abs_path = os.path.abspath(os.path.join(WORKSPACE_DIR, rel_path))
        if not abs_path.startswith(WORKSPACE_DIR):
            log_error(f"Security Warning: Attempted path escape ignored: {rel_path}")
            continue
            
        # Make a physical backup of the file before editing
        make_file_backup(abs_path)
        
        # Write the new content
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        log_success(f"Applied patch to: {rel_path}")
        applied_files.append(rel_path)
        
    return applied_files

def update_report(status, attempt, error_type, explanation, applied_files, full_log):
    """Appends reports to report.txt for tracking."""
    report_file = os.path.join(WORKSPACE_DIR, "report.txt")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    with open(report_file, 'a', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write(f"TIMESTAMP: {timestamp}\n")
        f.write(f"RUN ATTEMPT: {attempt}\n")
        f.write(f"STATUS: {status}\n")
        f.write(f"ERROR TYPE: {error_type}\n")
        f.write(f"EXPLANATION: {explanation}\n")
        f.write(f"AFFECTED FILES: {', '.join(applied_files)}\n")
        f.write("-" * 30 + " FULL ERROR LOG " + "-" * 30 + "\n")
        f.write(full_log + "\n")
        f.write("="*60 + "\n\n")

def write_last_error_json(log_content, err_type, referenced_files):
    """Compiles and writes last_error.json to the workspace root."""
    feature = "Unknown Feature"
    step = "Unknown Step"
    error_msg = ""
    
    # Simple heuristics to detect feature and step from traceback/logs
    tb_matches = re.findall(r'File "([^"]+)", line (\d+), in (\w+)', log_content)
    if tb_matches:
        workspace_calls = []
        for file, line, func in tb_matches:
            if "ai_runner.py" not in file:
                workspace_calls.append((file, line, func))
        
        if workspace_calls:
            deepest_call = workspace_calls[-1]  # The one that crashed
            filepath, line_num, func_name = deepest_call
            filename = os.path.basename(filepath)
            step = f"Function '{func_name}' at line {line_num} in file '{filename}'"
            
            # Map filename to Feature
            if "fb_login.py" in filename:
                feature = "Facebook Login"
            elif "fb_profile.py" in filename:
                feature = "Profile / Fanpage Fetching"
            elif "copyright_checker.py" in filename:
                feature = "Copyright Appeals Checking"
            elif "delete_post.py" in filename:
                feature = "Post Deletion"
            elif "database.py" in filename:
                feature = "Database Operations"
            elif "main.py" in filename:
                feature = "Main Orchestration"
    
    # Extract the actual exception message
    lines = [line.strip() for line in log_content.splitlines() if line.strip()]
    for line in reversed(lines):
        if any(exc in line for exc in ["Error:", "Exception:", "Fail:", "OSError:", "ValueError:", "NameError:", "TypeError:", "ZeroDivisionError:"]):
            error_msg = line
            break
    if not error_msg and lines:
        error_msg = lines[-1]

    error_data = {
        "feature": feature,
        "step": step,
        "error_type": err_type,
        "error_message": error_msg,
        "referenced_files": referenced_files,
        "traceback": log_content
    }
    
    try:
        error_file = os.path.join(WORKSPACE_DIR, "last_error.json")
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, indent=2, ensure_ascii=False)
        print("[SUCCESS] Error Report: Compiled and saved to last_error.json")
    except Exception as e:
        print(f"[ERROR] Failed to write last_error.json: {str(e)}")

def main():
    target_cmd = ["python", "main.py", "cli"]
    if len(sys.argv) > 1:
        target_cmd = sys.argv[1:]

    # Check for API Key first
    if not API_KEY:
        log_error("Missing ANTHROPIC_API_KEY environment variable. Create a .env file or set it in the shell environment.")
        sys.exit(1)

    log_info(f"=== Starting AI Self-Healing Loop for command: {' '.join(target_cmd)} ===")
    
    # Store error hashes to prevent loops
    seen_error_hashes = set()
    
    for attempt in range(1, MAX_RETRIES + 1):
        log_info("\n" + "="*30 + f" ATTEMPT {attempt}/{MAX_RETRIES} " + "="*30)
        
        # Run tool
        stdout, stderr, exit_code = run_command(target_cmd)
        full_output = f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        
        if exit_code == 0:
            log_success(f"Command succeeded with exit code 0 on attempt {attempt}!")
            update_report("SUCCESS", attempt, "None", "Script executed successfully without crashes.", [], full_output)
            break
            
        # Error detected!
        log_warning(f"Command crashed with exit code {exit_code}.")
        
        # Hash of the error log to check for cycles
        log_hash = hashlib.md5(full_output.encode('utf-8')).hexdigest()
        if log_hash in seen_error_hashes:
            log_error("Detected loop: The exact same error was encountered. Aborting to prevent infinite loops.")
            update_report("LOOP_FAILURE", attempt, "Loop Detected", "Infinite fixing loop detected for the same traceback.", [], full_output)
            sys.exit(1)
        seen_error_hashes.add(log_hash)
        
        # Parse tracebacks and classify
        err_type, err_hint = classify_error(full_output)
        referenced_files = parse_traceback(full_output)
        
        log_info(f"Error Classified: {err_type}")
        log_info(f"Referenced files in traceback: {referenced_files}")
        
        if not referenced_files:
            log_warning("No workspace files detected in traceback. Adding default entry main.py.")
            referenced_files = ["main.py"]
            
        # Write compile error report JSON
        write_last_error_json(full_output, err_type, referenced_files)
            
        try:
            # Query Claude for fix
            fix_json = query_claude(full_output, err_type, err_hint, referenced_files)
            
            # Commit pre-fix state
            git_commit(f"Pre-fix backup: Run {attempt}")
            
            # Apply fix
            applied = apply_fix(fix_json)
            
            # Commit post-fix state
            git_commit(f"AI Auto-fix applied: Run {attempt} - {err_type}")
            
            # Log to report
            update_report(
                "FIX_APPLIED", 
                attempt, 
                err_type, 
                fix_json.get("explanation", ""), 
                applied, 
                full_output
            )
            
        except Exception as e:
            log_error(f"Error during self-healing: {str(e)}")
            update_report("HEALING_CRASHED", attempt, err_type, f"Exception in healer: {str(e)}", [], full_output)
            sys.exit(1)
            
        # Wait a moment before rerunning
        time.sleep(2)
    else:
        log_error(f"Max retries ({MAX_RETRIES}) reached. Self-healing failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
