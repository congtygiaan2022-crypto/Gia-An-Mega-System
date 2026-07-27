const fs = require('fs');
const path = require('path');

class LoggingManager {
  constructor(profilesDir) {
    this.profilesDir = profilesDir || path.join(__dirname, '..', '..', 'bin', 'profiles');
  }

  getLogFilePath(profileId) {
    return path.join(this.profilesDir, profileId, 'profile.log');
  }

  ensureLogDirectory(profileId) {
    const logPath = this.getLogFilePath(profileId);
    const dir = path.dirname(logPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    return logPath;
  }

  log(profileId, message, level = 'INFO') {
    try {
      const logPath = this.ensureLogDirectory(profileId);
      const now = new Date();
      const timeStr = now.toISOString().replace('T', ' ').substring(0, 19);
      const line = `[${timeStr}] [${level}] ${message}\n`;
      fs.appendFileSync(logPath, line, 'utf8');
    } catch (err) {
      console.error(`Failed to write profile log for ${profileId}:`, err.message);
    }
  }

  readLogs(profileId, linesCount = 100) {
    try {
      const logPath = this.getLogFilePath(profileId);
      if (!fs.existsSync(logPath)) {
        return `[System] No logs exist yet for Profile ${profileId}.`;
      }
      const raw = fs.readFileSync(logPath, 'utf8');
      const lines = raw.split('\n').filter(Boolean);
      return lines.slice(-linesCount).join('\n');
    } catch (err) {
      return `[Error] Failed to read logs: ${err.message}`;
    }
  }

  clearLogs(profileId) {
    try {
      const logPath = this.getLogFilePath(profileId);
      if (fs.existsSync(logPath)) {
        fs.writeFileSync(logPath, '', 'utf8');
      }
      return true;
    } catch (err) {
      return false;
    }
  }
}

module.exports = LoggingManager;
