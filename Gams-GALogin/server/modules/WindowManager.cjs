const { execSync } = require('child_process');

class WindowManager {
  constructor() {}

  /**
   * Calculates the bounds (x, y, width, height) for a window.
   * 
   * @param {number} index - 0-based index of the window
   * @param {number} total - total number of windows in the layout
   * @param {string} layoutType - 'grid' | 'cascade' | 'tile' | 'vertical' | 'horizontal'
   * @param {number} screenWidth - screen width (default 1920)
   * @param {number} screenHeight - screen height (default 1080)
   * @returns {Object} { x, y, width, height }
   */
  calculateBounds(index, total, layoutType = 'grid', screenWidth = 1920, screenHeight = 1080) {
    if (total <= 0) total = 1;
    index = index % total;

    // Standard taskbar padding on Windows (typically at the bottom, ~40px)
    const availableHeight = screenHeight - 40;
    const availableWidth = screenWidth;

    let x = 0;
    let y = 0;
    let width = 800;
    let height = 600;

    const type = (layoutType || 'grid').toLowerCase();

    switch (type) {
      case 'grid':
      case 'tile': {
        const cols = Math.ceil(Math.sqrt(total));
        const rows = Math.ceil(total / cols);
        
        width = Math.floor(availableWidth / cols);
        height = Math.floor(availableHeight / rows);
        
        const col = index % cols;
        const row = Math.floor(index / cols);
        
        x = col * width;
        y = row * height;
        break;
      }
      
      case 'cascade': {
        width = Math.min(1000, Math.floor(availableWidth * 0.6));
        height = Math.min(650, Math.floor(availableHeight * 0.7));
        
        const offset = 40; // pixel offset per window
        const maxOffsetCols = Math.floor((availableWidth - width) / offset) || 1;
        const maxOffsetRows = Math.floor((availableHeight - height) / offset) || 1;
        
        const cycle = Math.min(maxOffsetCols, maxOffsetRows);
        const cycleIdx = index % cycle;
        
        x = cycleIdx * offset;
        y = cycleIdx * offset;
        break;
      }
      
      case 'vertical': {
        width = Math.floor(availableWidth / total);
        height = availableHeight;
        x = index * width;
        y = 0;
        break;
      }
      
      case 'horizontal': {
        width = availableWidth;
        height = Math.floor(availableHeight / total);
        x = 0;
        y = index * height;
        break;
      }

      default:
        x = 100 + index * 30;
        y = 100 + index * 30;
        break;
    }

    return {
      x: Math.max(0, x),
      y: Math.max(0, y),
      width: Math.max(400, width),
      height: Math.max(300, height)
    };
  }

  /**
   * Generates CLI arguments for position and size
   */
  getLayoutArguments(index, total, layoutType, screenWidth, screenHeight) {
    if (!layoutType || layoutType === 'none') return [];
    
    const bounds = this.calculateBounds(index, total, layoutType, screenWidth, screenHeight);
    return [
      `--window-size=${bounds.width},${bounds.height}`,
      `--window-position=${bounds.x},${bounds.y}`
    ];
  }

  /**
   * Dynamically repositions an already-running process window via native PowerShell and User32.dll
   */
  repositionWindow(pid, x, y, width, height) {
    if (!pid) return false;
    try {
      const psCommand = `powershell -NoProfile -Command "
        $member = '[DllImport(\\"user32.dll\\")] public static extern bool MoveWindow(IntPtr hWnd, int X, int Y, int nWidth, int nHeight, bool bRepaint);';
        $type = Add-Type -Name Win32 -MemberDefinition $member -PassThru;
        $proc = Get-Process -Id ${pid} -ErrorAction SilentlyContinue;
        if ($proc) {
          $hwnd = $proc.MainWindowHandle;
          if ($hwnd -ne [IntPtr]::Zero) {
            $null = $type::MoveWindow($hwnd, ${x}, ${y}, ${width}, ${height}, $true);
          }
        }
      "`;
      execSync(psCommand);
      return true;
    } catch (err) {
      console.warn(`Failed to reposition window for PID ${pid}:`, err.message);
      return false;
    }
  }
}

module.exports = WindowManager;
