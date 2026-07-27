const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class ImportExportManager {
  constructor(profileManager, profilesDir) {
    this.profileManager = profileManager;
    this.profilesDir = profilesDir || path.join(__dirname, '..', '..', 'bin', 'profiles');
    this.tempDir = path.join(__dirname, '..', '..', 'bin', 'temp_backup');
    this.exportsDir = path.join(__dirname, '..', '..', 'bin', 'exports');

    this.ensureDirectoryExists(this.tempDir);
    this.ensureDirectoryExists(this.exportsDir);
  }

  ensureDirectoryExists(dir) {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  }

  cleanDirectory(dir) {
    if (fs.existsSync(dir)) {
      fs.rmSync(dir, { recursive: true, force: true });
    }
    this.ensureDirectoryExists(dir);
  }

  /**
   * Exports a profile configuration and its user data directory to a zip file.
   * Returns: absolute path of the generated ZIP file
   */
  exportProfile(profileId) {
    const profile = this.profileManager.getProfile(profileId);
    if (!profile) throw new Error('Profile not found');

    const uniqueTemp = path.join(this.tempDir, `${profileId}_export`);
    this.cleanDirectory(uniqueTemp);

    // 1. Write metadata JSON
    const metaFile = path.join(uniqueTemp, 'profile_meta.json');
    fs.writeFileSync(metaFile, JSON.stringify(profile, null, 2), 'utf8');

    // 2. Copy User Data Directory (excluding huge cache folder if possible to save space, but keeping general storage)
    const destUserDir = path.join(uniqueTemp, 'user_data');
    this.ensureDirectoryExists(destUserDir);

    const srcUserDir = profile.userDataDir;
    if (fs.existsSync(srcUserDir)) {
      try {
        // Copy directory on Windows using xcopy or robocopy
        // robocopy is fast and standard on modern Windows. Exit code < 8 means success for robocopy.
        execSync(`robocopy "${srcUserDir}" "${destUserDir}" /E /XD "Cache" "Code Cache" "GPUCache" /NFL /NDL /NJH /NJS`, { stdio: 'ignore' });
      } catch (err) {
        // Robocopy returns codes like 1 for success with copied files, which Node throws as error. Ignore.
      }
    }

    // 3. Compress using PowerShell
    const cleanName = profile.name.replace(/[^a-z0-9]/gi, '_').toLowerCase();
    const zipPath = path.join(this.exportsDir, `${cleanName}_${profileId}.zip`);
    
    if (fs.existsSync(zipPath)) {
      fs.unlinkSync(zipPath);
    }

    // Run powershell Compress-Archive
    const psCommand = `powershell -NoProfile -Command "Compress-Archive -Path '${uniqueTemp}\\*' -DestinationPath '${zipPath}' -Force"`;
    execSync(psCommand);

    // 4. Cleanup temp folder
    fs.rmSync(uniqueTemp, { recursive: true, force: true });

    return zipPath;
  }

  /**
   * Imports a profile from a ZIP backup archive.
   * Returns: imported Profile object
   */
  importProfile(zipPath) {
    if (!fs.existsSync(zipPath)) {
      throw new Error(`Backup file not found at: ${zipPath}`);
    }

    const uniqueTemp = path.join(this.tempDir, `import_${Date.now()}`);
    this.cleanDirectory(uniqueTemp);

    // 1. Decompress using PowerShell
    const psCommand = `powershell -NoProfile -Command "Expand-Archive -Path '${zipPath}' -DestinationPath '${uniqueTemp}' -Force"`;
    execSync(psCommand);

    // 2. Read Metadata
    const metaFile = path.join(uniqueTemp, 'profile_meta.json');
    if (!fs.existsSync(metaFile)) {
      fs.rmSync(uniqueTemp, { recursive: true, force: true });
      throw new Error('Invalid backup archive: missing profile_meta.json');
    }

    let meta = JSON.parse(fs.readFileSync(metaFile, 'utf8'));

    // 3. Generate a new Profile ID to avoid duplicate keys in database
    const newId = `p-${Date.now()}`;
    const newUserDataDir = path.join(this.profilesDir, newId);
    this.ensureDirectoryExists(newUserDataDir);

    // 4. Move user data files to the new profile location
    const unzippedData = path.join(uniqueTemp, 'user_data');
    if (fs.existsSync(unzippedData)) {
      try {
        execSync(`robocopy "${unzippedData}" "${newUserDataDir}" /E /NFL /NDL /NJH /NJS`, { stdio: 'ignore' });
      } catch (err) {
        // Robocopy code ignore
      }
    }

    // 5. Update metadata config for local paths
    meta.id = newId;
    meta.name = `${meta.name} (Imported)`;
    meta.userDataDir = newUserDataDir;
    meta.lastOpened = 'Chưa sử dụng';
    meta.port = null; // ProfileManager will assign a fresh debug port

    // Create the profile in database
    const importedProfile = this.profileManager.createProfile(meta);

    // 6. Cleanup temp folder
    fs.rmSync(uniqueTemp, { recursive: true, force: true });

    return importedProfile;
  }
}

module.exports = ImportExportManager;
