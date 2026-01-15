def check_for_new_perk(window_name, coords):
    """Check if 'New Perk' text is visible in the perk bar region."""
    region = coords['new_perk_region']
    text = get_text_from_region(window_name, region)
    print(f"  [{window_name}] OCR read: '{text}'")
    return "new perk" in text.lower()
def get_perk_priority(perk_text, window_name=None):
    """Return the priority value for a given perk text."""
    perk_text_lower = perk_text.strip().lower()
    # Choose the correct priority list
    if window_name and 'daddy' in window_name.lower():
        priority_list = PERK_PRIORITY_DADDY
    else:
        priority_list = PERK_PRIORITY

    # Special case: match 'free upgrade chance for all +5.00' if all words 'free', 'for', 'all' exist
    if all(word in perk_text_lower for word in ['free', 'for', 'all']):
        for priority, include_keywords, exclude_keywords in priority_list:
            if 'free upgrade chance' in include_keywords or 'upgrade chance for all' in include_keywords:
                return priority
    for priority, include_keywords, exclude_keywords in priority_list:
        all_include_match = all(keyword in perk_text_lower for keyword in include_keywords)
        no_exclude_match = not any(keyword in perk_text_lower for keyword in exclude_keywords)
        if all_include_match and no_exclude_match:
            return priority
    return 9999
import pyautogui
import pytesseract
from PIL import Image
import time
import threading
import os
from datetime import datetime
from pathlib import Path
try:
    import tkinter as tk
    from tkinter import messagebox
    TKINTER_AVAILABLE = True
except Exception:
    TKINTER_AVAILABLE = False

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.resolve()

# Try to import pygetwindow for window targeting
try:
    import pygetwindow as gw
    WINDOW_SUPPORT = True
except ImportError:
    WINDOW_SUPPORT = False
    print("WARNING: pygetwindow not installed. Run: pip install pygetwindow")
    print("Window targeting will not work without it.")

# Try to import win32gui for virtual desktop detection and window capture
try:
    import win32gui
    import win32con
    import win32ui
    from ctypes import windll
    WIN32_SUPPORT = True
except ImportError:
    WIN32_SUPPORT = False
    print("WARNING: pywin32 not installed. Run: pip install pywin32")
    print("Virtual desktop detection will not work without it.")

# Set the path to Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ============================================
# LOGGING CONFIGURATION
# ============================================

LOG_FILE = SCRIPT_DIR / "perk_selection_log.txt"
PERKS_ONLY_LOG = SCRIPT_DIR / "perks_seen.txt"

def initialize_log_files():
    """Clear and recreate both log files at startup."""
    # Clear the main log file
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("")  # Creates empty file (or clears existing)
    
    # Clear the perks-only log file
    with open(PERKS_ONLY_LOG, "w", encoding="utf-8") as f:
        f.write("")  # Creates empty file (or clears existing)
    
    print(f"Log files initialized (cleared):")
    print(f"  - {LOG_FILE}")
    print(f"  - {PERKS_ONLY_LOG}")

def write_to_log(message):
    """Write a message to the log file with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def log_perk_to_simple_list(window_name, perk_text, priority, was_selected):
    """Log a perk to the simple perks-only log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    selected_marker = ">>> SELECTED" if was_selected else "    not selected"
    
    with open(PERKS_ONLY_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{window_name}] Priority {priority:4} | {selected_marker} | {perk_text}\n")

def log_perk_selection(window_name, perk1_text, perk1_priority, perk2_text, perk2_priority, selected_perk,
                       perk1_is_purple=False, perk2_is_purple=False, 
                       effective_priority1=None, effective_priority2=None,
                       perk1_bg_color=None, perk2_bg_color=None,
                       perk_list_name=None):
    """Log a perk selection decision to the log file, including which perk list was used."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Use base priorities if effective not provided
    if effective_priority1 is None:
        effective_priority1 = perk1_priority
    if effective_priority2 is None:
        effective_priority2 = perk2_priority

    # Log to detailed log
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*70}\n")
        f.write(f"[{timestamp}] PERK SELECTION - {window_name}\n")
        f.write(f"{'='*70}\n")
        if perk_list_name:
            f.write(f"  Perk List Used: {perk_list_name}\n")
        f.write(f"  Perk 1: {perk1_text}\n")
        f.write(f"  Perk 1 Priority: {perk1_priority}\n")
        if perk1_bg_color:
            f.write(f"  Perk 1 Background: RGB{perk1_bg_color} | Hex: #{perk1_bg_color[0]:02X}{perk1_bg_color[1]:02X}{perk1_bg_color[2]:02X}\n")
        f.write(f"  Perk 1 Is Purple: {perk1_is_purple}\n")
        f.write(f"  Perk 1 Effective Priority: {effective_priority1}\n")
        f.write(f"\n")
        f.write(f"  Perk 2: {perk2_text}\n")
        f.write(f"  Perk 2 Priority: {perk2_priority}\n")
        if perk2_bg_color:
            f.write(f"  Perk 2 Background: RGB{perk2_bg_color} | Hex: #{perk2_bg_color[0]:02X}{perk2_bg_color[1]:02X}{perk2_bg_color[2]:02X}\n")
        f.write(f"  Perk 2 Is Purple: {perk2_is_purple}\n")
        f.write(f"  Perk 2 Effective Priority: {effective_priority2}\n")
        f.write(f"\n")
        selected_priority = effective_priority1 if selected_perk == 1 else effective_priority2
        f.write(f"  >>> SELECTED: Perk {selected_perk} (Effective Priority {selected_priority})\n")
        f.write(f"{'='*70}\n\n")

    # Log to simple perks-only log
    perk1_selected = (selected_perk == 1)
    perk2_selected = (selected_perk == 2)
    log_perk_to_simple_list(window_name, perk1_text, perk1_priority, perk1_selected)
    log_perk_to_simple_list(window_name, perk2_text, perk2_priority, perk2_selected)

def log_perk_selection_three(window_name, perk1_text, perk1_priority, perk2_text, perk2_priority, perk3_text, perk3_priority, selected_perk,
                             perk1_is_purple=False, perk2_is_purple=False, perk3_is_purple=False,
                             effective_priority1=None, effective_priority2=None, effective_priority3=None,
                             perk1_bg_color=None, perk2_bg_color=None, perk3_bg_color=None,
                             perk_list_name=None, selected_note=None):
    """Log a three-option perk selection decision to the log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if effective_priority1 is None:
        effective_priority1 = perk1_priority
    if effective_priority2 is None:
        effective_priority2 = perk2_priority
    if effective_priority3 is None:
        effective_priority3 = perk3_priority

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*70}\n")
        f.write(f"[{timestamp}] PERK SELECTION - {window_name}\n")
        f.write(f"{'='*70}\n")
        if perk_list_name:
            f.write(f"  Perk List Used: {perk_list_name}\n")
        f.write(f"  Perk 1: {perk1_text}\n")
        f.write(f"  Perk 1 Priority: {perk1_priority}\n")
        if perk1_bg_color:
            f.write(f"  Perk 1 Background: RGB{perk1_bg_color} | Hex: #{perk1_bg_color[0]:02X}{perk1_bg_color[1]:02X}{perk1_bg_color[2]:02X}\n")
        f.write(f"  Perk 1 Is Purple: {perk1_is_purple}\n")
        f.write(f"  Perk 1 Effective Priority: {effective_priority1}\n\n")

        f.write(f"  Perk 2: {perk2_text}\n")
        f.write(f"  Perk 2 Priority: {perk2_priority}\n")
        if perk2_bg_color:
            f.write(f"  Perk 2 Background: RGB{perk2_bg_color} | Hex: #{perk2_bg_color[0]:02X}{perk2_bg_color[1]:02X}{perk2_bg_color[2]:02X}\n")
        f.write(f"  Perk 2 Is Purple: {perk2_is_purple}\n")
        f.write(f"  Perk 2 Effective Priority: {effective_priority2}\n\n")

        f.write(f"  Perk 3: {perk3_text}\n")
        f.write(f"  Perk 3 Priority: {perk3_priority}\n")
        if perk3_bg_color:
            f.write(f"  Perk 3 Background: RGB{perk3_bg_color} | Hex: #{perk3_bg_color[0]:02X}{perk3_bg_color[1]:02X}{perk3_bg_color[2]:02X}\n")
        f.write(f"  Perk 3 Is Purple: {perk3_is_purple}\n")
        f.write(f"  Perk 3 Effective Priority: {effective_priority3}\n\n")

        selected_priority = None
        if selected_perk == 1:
            selected_priority = effective_priority1
        elif selected_perk == 2:
            selected_priority = effective_priority2
        elif selected_perk == 3:
            selected_priority = effective_priority3
        # Append selected_note if provided
        if selected_note:
            f.write(f"  >>> SELECTED: Perk {selected_perk} (Effective Priority {selected_priority}){selected_note}\n")
        else:
            f.write(f"  >>> SELECTED: Perk {selected_perk} (Effective Priority {selected_priority})\n")
        f.write(f"{'='*70}\n\n")

    # Log to simple perks-only log
    log_perk_to_simple_list(window_name, perk1_text, perk1_priority, selected_perk == 1)
    log_perk_to_simple_list(window_name, perk2_text, perk2_priority, selected_perk == 2)
    log_perk_to_simple_list(window_name, perk3_text, perk3_priority, selected_perk == 3)

# ============================================
# WINDOW CONFIGURATION - Both BlueStacks instances
# ============================================

WINDOWS = [
    "Daddy Bluestack",
    "Maximus Bluestack",
]

# ============================================
# CONFIGURATION - Coordinates WITH AD showing
# (These are RELATIVE to the window, not absolute screen coords)
# ============================================

COORDS_WITH_AD = {
    'play_pause': (1135, 28),
    'play_pause_region': ((1100, 10), (1170, 45)),
    'new_perk_bar': (1128, 74),
    'perk_option_1': (1133, 242),
    'perk_option_2': (1138, 345),
    'perk_option_3': (1135, 448),
    'close_x': (1329, 132),
    'new_perk_region': ((1018, 63), (1228, 92)),
    # OLD Perk 1: ((890, 200), (1343, 284))
    # OLD Perk 2: ((888, 305), (1345, 390))
    'perk1_text_region': ((994, 210), (1311, 288)),
    'perk2_text_region': ((994, 312), (1311, 391)),
    'perk3_text_region': ((994, 414), (1311, 493)),
    # 'wave_region': ((1130, 599), (1269, 624)),
}

# ============================================
# CONFIGURATION - Coordinates WITHOUT AD showing
# ============================================

COORDS_NO_AD = {
    'play_pause': (1135, 27),
    'play_pause_region': ((916, 10), (986, 45)),
    'new_perk_bar': (944, 79),
    'perk_option_1': (956, 245),
    'perk_option_2': (957, 349),
    'perk_option_3': (956, 453),
    'close_x': (1145, 134),
    'new_perk_region': ((832, 62), (1044, 93)),
    # OLD Perk 1: ((703, 199), (1159, 287))
    # OLD Perk 2: ((709, 307), (1160, 391))
    'perk1_text_region': ((814, 206), (1145, 283)),
    'perk2_text_region': ((814, 312), (1145, 391)),
    'perk3_text_region': ((814, 418), (1145, 497)),
    # 'wave_region': ((946, 601), (1080, 628)),
}

# Positions to check for ad detection (relative to window)
AD_CHECK_POS_1 = (5, 500)
AD_CHECK_POS_2 = (400, 500)

# Play/Pause button detection
PLAY_PAUSE_CHECK_POS = (1135, 24)  # Position to check for play/pause state
PAUSE_BUTTON_COLOR = (0x1B, 0x1E, 0x38)  # #1B1E38 - Color when PAUSE button showing (game running)
PLAY_BUTTON_COLOR = (0xB6, 0xB8, 0xCD)   # #B6B8CD - Color when PLAY button showing (game paused)
COLOR_TOLERANCE = 20  # Allow some variation in color matching

# ============================================
# PURPLE BACKGROUND DETECTION (Bad perks)
# ============================================
# Purple background perks should be avoided unless it's Priority 1 perk
# or if both perks have purple backgrounds

# Sample position offset from perk text region top-left corner to get background color
# This samples a point that should be on the perk card background
PERK_BG_SAMPLE_OFFSET = (10, 10)  # Offset into the perk region to sample background

# Purple background color - #1F0352 (dark purple)
# Border color is #EF17FD (bright magenta) - can use as alternative detection
PURPLE_BG_COLOR = (0x1F, 0x03, 0x52)  # RGB(31, 3, 82) - dark purple background
PURPLE_BORDER_COLOR = (0xEF, 0x17, 0xFD)  # RGB(239, 23, 253) - bright magenta border
PURPLE_TOLERANCE = 40  # How close to purple to be considered "purple background"

# Priority 1 perk is exempt from purple penalty
PURPLE_EXEMPT_PRIORITY = 1

# ============================================
# PERK PRIORITY LIST - Using keyword matching
# Format: (priority, [keywords that ALL must match], [keywords that must NOT match])
# Lower priority number = better perk
# ============================================

PERK_PRIORITY = [
    (1,  ["enemies damage", "tower damage"], []),           # enemies damage -50%, but tower damage -50%
    (2,  ["perk wave requirement"], []),                     # perk wave requirement -20
    (3,  ["chrono field"], []),                              # chrono field
    (4,  ["golden tower"], []),                              # golden tower
    (5,  ["death"], []),                                     # death wave
    (6,  ["spotlight"], []),                                 # spotlight
    (7,  ["black hole"], []),                                # black hole
    (8,  ["increase max game speed"], []),                   # increase max game speed by +1
    (9,  ["max health"], ["coins", "tower max"]),            # x1.20 max health (exclude perk 31)
    (10, ["poison swamp"], []),                              # poison swamp
    (11, ["swamp radius"], []),                              # swamp radius x1.5
    (12, ["defense percent"], []),                           # defense percent +4
    (13, ["free upgrade chance", "upgrade chance for all"], []),  # free upgrade chance for all +5
    (14, ["cash bonus"], []),                                # x1.15 cash bonus
    (15, ["all coin"], []),                                  # x1.15 all coin
    (16, ["orbs"], []),                                      # orbs +1
    (17, ["bounce shot"], []),                               # bounce shot +2
    (18, ["damage"], ["land mine", "tower damage", "enemies damage", "distance"]),  # x1.15 damage (generic)
    (19, ["interest"], []),                                  # interest x1.50
    (20, ["land mine damage"], []),                          # land mine damage x3.50
    (21, ["defense absolute"], []),                          # x1.15 defense absolute
    (22, ["chain lightning"], []),                           # chain lightning
    (23, ["smart missiles"], []),                            # smart missiles
    (24, ["inner land mines"], []),                          # inner land mines
    (25, ["health regen"], []),                               # health regen (generic)
    (26, ["cash per wave"], []),                             # x12.00 cash per wave
    (27, ["boss health"], []),                               # boss health -70%, but boss speed +50%
    (28, ["ranged enemies", "attack distance"], []),         # ranged enemies attack distance reduced
    (29, ["life", "steal"], []),                             # lifesteal x2.50
    (30, ["enemies speed"], []),                             # enemies speed -40%
    (31, ["enemies have", "health"], ["max health", "health regen"]),  # enemies have -50% health
    (32, ["tower health regen"], []),                         # tower health regen x8
    (33, ["coins", "tower max health"], []),                 # x1.80 coins, but tower max health
    (34, ["tower damage", "bosses"], []),                    # x1.50 tower damage, but bosses
]

# Alternate perk priority for "Daddy" windows
PERK_PRIORITY_DADDY = [
    (1,  ["enemies damage", "tower damage"], []),           # enemies damage -50%, but tower damage -50%
    (2,  ["perk wave requirement"], []),                     # perk wave requirement -20
    (3,  ["golden tower"], []),                              # golden tower
    (4,  ["death"], []),                                     # death wave
    (5,  ["increase max game speed"], []),                   # increase max game speed by +1
    (6,  ["max health"], ["coins", "tower max"]),            # x1.20 max health (exclude perk 31)
    (7,  ["defense percent"], []),                           # defense percent +4
    (8,  ["free upgrade chance", "upgrade chance for all"], []),  # free upgrade chance for all +5
    (9,  ["cash bonus"], []),                                # x1.15 cash bonus
    (10, ["all coin"], []),                                  # x1.15 all coin
    (11, ["orbs"], []),                                      # orbs +1
    (12, ["bounce shot"], []),                               # bounce shot +2
    (13, ["damage"], ["land mine", "tower damage", "enemies damage", "distance"]),  # x1.15 damage (generic)
    (14, ["interest"], []),                                  # interest x1.50
    (15, ["land mine damage"], []),                          # land mine damage x3.50
    (16, ["defense absolute"], []),                          # x1.15 defense absolute
    (17, ["chrono field"], []),                              # #3: chrono field - Time slow field (Moved Up)
    (18, ["spotlight"], []),                                 # #6: spotlight (Moved Up)
    (19, ["black hole"], []),                                # #7: black hole (Moved Up)
    (20, ["poison swamp"], []),                              # #10: poison swamp (Moved Up)
    (21, ["swamp radius"], []),                              # 11: swamp radius (Moved Up)
    (22, ["chain lightning"], []),                           # chain lightning (Now after swamp)
    (23, ["smart missiles"], []),                            # smart missiles
    (24, ["inner land mines"], []),                          # inner land mines
    (25, ["health regen"], []),                               # health regen (generic)
    (26, ["cash per wave"], []),                             # x12.00 cash per wave
    (27, ["boss health"], []),                               # boss health -70%, but boss speed +50%
    (28, ["ranged enemies", "attack distance"], []),         # ranged enemies attack distance reduced
    (29, ["life", "steal"], []),                             # lifesteal x2.50
    (30, ["enemies speed"], []),                             # enemies speed -40%
    (31, ["enemies have", "health"], ["max health", "health regen"]),  # enemies have -50% health
    (32, ["tower health regen"], []),                         # tower health regen x8
    (33, ["coins", "tower max health"], []),                 # x1.80 coins, but tower max health
    (34, ["tower damage", "bosses"], []),                    # x1.50 tower damage, but bosses
]

# ============================================
# TIMING CONFIGURATION
# ============================================

CHECK_INTERVAL = 2
CLICK_DELAY = 0.5
WINDOW_OPEN_WAIT = 5.0
WINDOW_CLOSE_WAIT = 5.0

# Global timer for debug image saving (every 30 seconds)
last_debug_save_time = 0

# Global timer for wave 1 handling (cooldown per window)
last_wave1_times = {}
# Flag to skip clicking the New Perk bar until numeric detection recovers
SKIP_NEW_PERK_BAR_UNTIL_NUMBERS = False

# ============================================
# FAILSAFE CONFIGURATION
# ============================================

FAILSAFE_MARGIN = 10

# ============================================
# WINDOW MANAGEMENT
# ============================================

def is_window_on_current_desktop(hwnd):
    """
    Check if a window is visible on the current virtual desktop.
    """
    if not WIN32_SUPPORT:
        return True
    
    try:
        import ctypes
        DWMWA_CLOAKED = 14
        dwm = ctypes.windll.dwmapi
        cloaked = ctypes.c_int(0)
        result = dwm.DwmGetWindowAttribute(
            hwnd, 
            DWMWA_CLOAKED, 
            ctypes.byref(cloaked), 
            ctypes.sizeof(cloaked)
        )
        
        if result == 0:
            if cloaked.value != 0:
                return False
        
        if not win32gui.IsWindowVisible(hwnd):
            return False
            
        return True
        
    except Exception as e:
        return True

def get_target_window(window_name):
    """Get the target BlueStacks window using EXACT title match only."""
    if not WINDOW_SUPPORT:
        return None
    
    try:
        all_windows = gw.getAllWindows()
        for win in all_windows:
            if win.title == window_name:
                return win
        return None
    except Exception as e:
        print(f"Error getting window: {e}")
        return None

def is_target_window_on_current_desktop(window_name):
    """Check if our target window is on the currently active virtual desktop."""
    if not WINDOW_SUPPORT or not WIN32_SUPPORT:
        return True
    
    try:
        hwnd = win32gui.FindWindow(None, window_name)
        if hwnd == 0:
            return False
        return is_window_on_current_desktop(hwnd)
    except Exception as e:
        return True

def get_window_offset(window_name):
    """Get the top-left corner offset of the target window."""
    window = get_target_window(window_name)
    if window:
        return (window.left, window.top)
    return (0, 0)

def to_absolute_coords(relative_coords, window_name):
    """Convert window-relative coordinates to absolute screen coordinates."""
    offset_x, offset_y = get_window_offset(window_name)
    
    if isinstance(relative_coords, tuple) and len(relative_coords) == 2:
        if isinstance(relative_coords[0], tuple):
            (x1, y1), (x2, y2) = relative_coords
            return ((x1 + offset_x, y1 + offset_y), (x2 + offset_x, y2 + offset_y))
        else:
            x, y = relative_coords
            return (x + offset_x, y + offset_y)
    
    return relative_coords

def capture_window_screenshot(window_name, region=None):
    """
    Capture a screenshot directly from the target window, even if on another virtual desktop.
    """
    if not WIN32_SUPPORT:
        if region:
            (x1, y1), (x2, y2) = to_absolute_coords(region, window_name)
            return pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
        return None
    
    try:
        hwnd = win32gui.FindWindow(None, window_name)
        if hwnd == 0:
            return None
        
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        window_width = right - left
        window_height = bottom - top
        
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, window_width, window_height)
        saveDC.SelectObject(saveBitMap)
        
        result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
        if result == 0:
            result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)
        
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        
        img = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1
        )
        
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)
        
        if region:
            (x1, y1), (x2, y2) = region
            img = img.crop((x1, y1, x2, y2))
        
        return img
        
    except Exception as e:
        print(f"  Window capture error: {e}")
        if region:
            (x1, y1), (x2, y2) = to_absolute_coords(region, window_name)
            return pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
        return None

def capture_window_pixel(window_name, x, y):
    """Capture a single pixel from the window at relative coordinates."""
    img = capture_window_screenshot(window_name, ((x, y), (x+1, y+1)))
    if img:
        return img.getpixel((0, 0))
    return None

def check_failsafe():
    """Check if mouse is in any corner - if so, raise exception to stop."""
    x, y = pyautogui.position()
    screen_width, screen_height = pyautogui.size()
    
    in_left = x <= FAILSAFE_MARGIN
    in_right = x >= screen_width - FAILSAFE_MARGIN
    in_top = y <= FAILSAFE_MARGIN
    in_bottom = y >= screen_height - FAILSAFE_MARGIN
    
    if (in_left and in_top) or (in_right and in_top) or (in_left and in_bottom) or (in_right and in_bottom):
        raise Exception("FAILSAFE: Mouse in corner - stopping script!")

# ============================================
# FUNCTIONS
# ============================================

def is_ad_showing(window_name):
    """Check if an ad is showing by comparing colors at two positions."""
    pixel1 = capture_window_pixel(window_name, AD_CHECK_POS_1[0], AD_CHECK_POS_1[1])
    pixel2 = capture_window_pixel(window_name, AD_CHECK_POS_2[0], AD_CHECK_POS_2[1])
    
    if pixel1 is None or pixel2 is None:
        print(f"  [{window_name}] WARNING: Could not capture ad detection pixels!")
        return False
    
    colors_match = (pixel1[0] == pixel2[0] and pixel1[1] == pixel2[1] and pixel1[2] == pixel2[2])
    
    # Debug logging
    print(f"  [{window_name}] Ad check - Pixel1 {AD_CHECK_POS_1}: RGB{pixel1}, Pixel2 {AD_CHECK_POS_2}: RGB{pixel2}, Match: {colors_match}")
    
    return not colors_match

def get_coords(window_name):
    """Get the correct coordinates based on ad presence."""
    check_failsafe()
    
    if is_ad_showing(window_name):
        print(f"  [{window_name}] Ad detected - using ad coordinates")
        coords = COORDS_WITH_AD
    else:
        print(f"  [{window_name}] No ad - using no-ad coordinates")
        coords = COORDS_NO_AD

    # Apply per-window tweaks (e.g., Maximus shifted UI)
    try:
        if window_name and 'maximus' in window_name.lower():
            # Make a shallow copy and adjust Y positions so perk1 top-left Y == 265
            adjusted = dict(coords)
            if 'perk1_text_region' in coords:
                (x1, y1), (x2, y2) = coords['perk1_text_region']
                delta = 265 - y1
                adjusted['perk1_text_region'] = ((x1, y1 + delta), (x2, y2 + delta))
                # Shift perk2 by same delta if present
                if 'perk2_text_region' in coords:
                    (x1b, y1b), (x2b, y2b) = coords['perk2_text_region']
                    adjusted['perk2_text_region'] = ((x1b, y1b + delta), (x2b, y2b + delta))
                # Shift perk3 by same delta if present
                if 'perk3_text_region' in coords:
                    (x1c, y1c), (x2c, y2c) = coords['perk3_text_region']
                    adjusted['perk3_text_region'] = ((x1c, y1c + delta), (x2c, y2c + delta))
                # Shift click targets if present
                if 'perk_option_1' in coords:
                    ox, oy = coords['perk_option_1']
                    adjusted['perk_option_1'] = (ox, oy + delta)
                if 'perk_option_2' in coords:
                    ox2, oy2 = coords['perk_option_2']
                    adjusted['perk_option_2'] = (ox2, oy2 + delta)
                if 'perk_option_3' in coords:
                    ox3, oy3 = coords['perk_option_3']
                    adjusted['perk_option_3'] = (ox3, oy3 + delta)
            coords = adjusted
            print(f"  [{window_name}] Applied Maximus Y-shift (perk regions) by delta {delta}")
    except Exception as e:
        print(f"  [{window_name}] Error adjusting Maximus coords: {e}")

    return coords

def bring_window_to_focus(window_name):
    """Bring the target window to the foreground."""
    if not WIN32_SUPPORT:
        print(f"  [{window_name}] WARNING: Window targeting not supported")
        return False
    
    try:
        # Find window by partial title match
        target_hwnd = None
        def enum_callback(hwnd, extra):
            nonlocal target_hwnd
            title = win32gui.GetWindowText(hwnd)
            if window_name.lower() in title.lower():
                target_hwnd = hwnd
                return False  # Stop enumeration
            return True
        
        win32gui.EnumWindows(enum_callback, None)
        
        if target_hwnd is None:
            print(f"  [{window_name}] WARNING: Window containing '{window_name}' not found")
            return False
        
        print(f"  [{window_name}] Found window with hwnd {target_hwnd}, title: '{win32gui.GetWindowText(target_hwnd)}'")
        
        if win32gui.IsIconic(target_hwnd):
            win32gui.ShowWindow(target_hwnd, win32con.SW_RESTORE)
            print(f"  [{window_name}] Restored minimized window")
        
        win32gui.SetForegroundWindow(target_hwnd)
        time.sleep(0.1)
        
        # Verify the window is now foreground
        fg_hwnd = win32gui.GetForegroundWindow()
        fg_title = win32gui.GetWindowText(fg_hwnd)
        print(f"  [{window_name}] Foreground window is now: '{fg_title}'")
        
        if fg_hwnd == target_hwnd:
            print(f"  [{window_name}] Successfully switched to window")
            return True
        else:
            print(f"  [{window_name}] WARNING: Failed to switch to window, still on '{fg_title}'")
            return False
    except Exception as e:
        print(f"  [{window_name}] Could not focus window: {e}")
        return False

def color_distance(color1, color2):
    """Calculate the distance between two RGB colors."""
    return abs(color1[0] - color2[0]) + abs(color1[1] - color2[1]) + abs(color1[2] - color2[2])

def is_purple_background(window_name, perk_region):
    """
    Check if a perk has a purple background by sampling the background color.
    Returns a tuple: (is_purple: bool, sampled_color: tuple or None)
    
    Purple background: #1F0352 - RGB(31, 3, 82) - dark purple
    Purple border: #EF17FD - RGB(239, 23, 253) - bright magenta
    """
    # Get the top-left corner of the perk region and apply the offset
    (x1, y1), (x2, y2) = perk_region
    sample_x = x1 + PERK_BG_SAMPLE_OFFSET[0]
    sample_y = y1 + PERK_BG_SAMPLE_OFFSET[1]
    
    pixel = capture_window_pixel(window_name, sample_x, sample_y)
    
    if pixel is None:
        print(f"  [{window_name}] Could not sample background color")
        return False, None
    
    r, g, b = pixel
    print(f"  [{window_name}] Perk background color at ({sample_x}, {sample_y}): RGB({r}, {g}, {b}) | Hex: #{r:02X}{g:02X}{b:02X}")
    
    # Method 1: Check distance from known purple background color (#1F0352)
    # ALSO require green channel to be very low (< 20) to distinguish from dark blue backgrounds
    # Purple has green=3, normal dark blue has green=35
    purple_bg_dist = color_distance(pixel, PURPLE_BG_COLOR)
    if purple_bg_dist <= PURPLE_TOLERANCE and g < 20:
        print(f"  [{window_name}] -> PURPLE BACKGROUND detected (distance: {purple_bg_dist}, green: {g})")
        return True, pixel
    
    # Method 2: Check distance from purple border color (#EF17FD)
    purple_border_dist = color_distance(pixel, PURPLE_BORDER_COLOR)
    if purple_border_dist <= PURPLE_TOLERANCE:
        print(f"  [{window_name}] -> PURPLE BORDER detected (distance: {purple_border_dist})")
        return True, pixel
    
    # Method 3: Heuristic check for dark purple-ish colors
    # The purple background #1F0352 has: low red (31), very low green (3), moderate blue (82)
    # Key characteristics: blue > red > green, green is very low
    is_dark_purple = (
        b > r and  # Blue is dominant
        b > g and  # Blue greater than green
        g < 20 and  # Green is very low (characteristic of this purple) - tightened from 30
        b > 40 and  # Blue has some presence
        r < 80  # Red is low-moderate
    )
    
    if is_dark_purple:
        print(f"  [{window_name}] -> PURPLE detected (heuristic: dark purple pattern)")
        return True, pixel
    
    # Method 4: Heuristic for bright magenta border (#EF17FD)
    # High red, low green, very high blue
    is_bright_magenta = (
        r > 180 and  # High red
        g < 80 and   # Low green
        b > 200      # Very high blue
    )
    
    if is_bright_magenta:
        print(f"  [{window_name}] -> PURPLE detected (heuristic: bright magenta pattern)")
        return True, pixel
    
    print(f"  [{window_name}] -> Not purple")
    return False, pixel

def check_play_pause_state(window_name, coords):
    """
    Check if the game is paused or running by checking the play/pause button color.
    """
    pixel = capture_window_pixel(window_name, PLAY_PAUSE_CHECK_POS[0], PLAY_PAUSE_CHECK_POS[1])
    
    if pixel is None:
        return 'unknown'
    
    print(f"  [{window_name}] Play/Pause button color: RGB({pixel[0]}, {pixel[1]}, {pixel[2]})")
    
    pause_distance = color_distance(pixel, PAUSE_BUTTON_COLOR)
    play_distance = color_distance(pixel, PLAY_BUTTON_COLOR)
    
    if play_distance <= COLOR_TOLERANCE:
        return 'paused'
    elif pause_distance <= COLOR_TOLERANCE:
        return 'running'
    else:
        if play_distance < pause_distance:
            print(f"  [{window_name}] (Color closer to PLAY button)")
            return 'paused'
        else:
            print(f"  [{window_name}] (Color closer to PAUSE button)")
            return 'running'

def click_play_pause_raw(window_name):
    """Press the play/pause keyboard shortcut without state checking."""
    check_failsafe()
    bring_window_to_focus(window_name)
    print(f"  [{window_name}] Pressing Ctrl+Shift+U for Play/Pause")
    pyautogui.hotkey('ctrl', 'shift', 'u')
    time.sleep(CLICK_DELAY)

def ensure_game_paused(window_name, coords, max_attempts=3):
    """Ensure the game is paused before proceeding."""
    for attempt in range(max_attempts):
        state = check_play_pause_state(window_name, coords)
        
        if state == 'paused':
            print(f"  [{window_name}] Game is paused (confirmed)")
            return True
        elif state == 'running':
            print(f"  [{window_name}] Game is running, pressing play/pause... (attempt {attempt + 1})")
            click_play_pause_raw(window_name)
            time.sleep(CLICK_DELAY * 2)
        else:
            print(f"  [{window_name}] Could not determine state, pressing play/pause... (attempt {attempt + 1})")
            click_play_pause_raw(window_name)
            time.sleep(CLICK_DELAY * 2)
    
    final_state = check_play_pause_state(window_name, coords)
    if final_state == 'paused':
        print(f"  [{window_name}] Game is paused (confirmed)")
        return True
    else:
        print(f"  [{window_name}] WARNING: Could not confirm game is paused")
        return False

def ensure_game_running(window_name, coords, max_attempts=3):
    """Ensure the game is running after perk selection."""
    for attempt in range(max_attempts):
        state = check_play_pause_state(window_name, coords)
        
        if state == 'running':
            print(f"  [{window_name}] Game is running (confirmed)")
            return True
        elif state == 'paused':
            print(f"  [{window_name}] Game is paused, pressing play/pause... (attempt {attempt + 1})")
            click_play_pause_raw(window_name)
            time.sleep(CLICK_DELAY * 2)
        else:
            print(f"  [{window_name}] Could not determine state, pressing play/pause... (attempt {attempt + 1})")
            click_play_pause_raw(window_name)
            time.sleep(CLICK_DELAY * 2)
    
    final_state = check_play_pause_state(window_name, coords)
    if final_state == 'running':
        print(f"  [{window_name}] Game is running (confirmed)")
        return True
    else:
        print(f"  [{window_name}] WARNING: Could not confirm game is running")
        return False

def click_at(window_name, coords, description=""):
    """Click at the specified coordinates after focusing window."""
    check_failsafe()
    bring_window_to_focus(window_name)
    abs_coords = to_absolute_coords(coords, window_name)
    x, y = abs_coords
    print(f"  [{window_name}] Clicking {description} at ({x}, {y})")
    pyautogui.click(x, y)
    time.sleep(CLICK_DELAY)

def get_text_from_region(window_name, region, save_debug_image=True):
    """Capture a region and extract text using OCR."""
    global last_debug_save_time
    check_failsafe()
    screenshot = capture_window_screenshot(window_name, region)
    # Only save debug image if flag is set
    if save_debug_image and window_name:
        # Save last 6 Daddy and Maximus new_perk_region screenshots, stacked vertically (Daddy left, Maximus right)
        from PIL import Image as PILImage
        debug_path = os.path.join(SCRIPT_DIR, 'debug_newperk_combined.png')
        # Use lists to store last 6 for each, persistently
        if not hasattr(get_text_from_region, '_daddy_imgs'):
            get_text_from_region._daddy_imgs = []
        if not hasattr(get_text_from_region, '_maximus_imgs'):
            get_text_from_region._maximus_imgs = []

        # Add new screenshot to appropriate list
        updated = False
        if 'daddy' in window_name.lower():
            get_text_from_region._daddy_imgs.append(screenshot.copy())
            if len(get_text_from_region._daddy_imgs) > 6:
                get_text_from_region._daddy_imgs = get_text_from_region._daddy_imgs[-6:]
            updated = True
        if 'maximus' in window_name.lower():
            get_text_from_region._maximus_imgs.append(screenshot.copy())
            if len(get_text_from_region._maximus_imgs) > 6:
                get_text_from_region._maximus_imgs = get_text_from_region._maximus_imgs[-6:]
            updated = True

        # Always update the combined image if either list changed and 30 seconds have passed
        if updated and time.time() - last_debug_save_time > 30:
            daddy_imgs = get_text_from_region._daddy_imgs[-6:]
            maximus_imgs = get_text_from_region._maximus_imgs[-6:]
            # Always show 6 rows, fill with blank if missing
            from PIL import Image as PILImage
            max_daddy_w = max((img.width for img in daddy_imgs), default=1)
            max_maximus_w = max((img.width for img in maximus_imgs), default=1)
            row_height = max(
                max((img.height for img in daddy_imgs), default=1),
                max((img.height for img in maximus_imgs), default=1)
            )
            total_height = row_height * 6
            total_width = max_daddy_w + max_maximus_w
            combined = PILImage.new('RGB', (total_width, total_height), color=(128, 128, 128))
            # Fill up to 6 images with blank if needed
            blank_daddy = PILImage.new('RGB', (max_daddy_w, row_height), color=(64, 64, 64))
            blank_maximus = PILImage.new('RGB', (max_maximus_w, row_height), color=(64, 64, 64))
            for i in range(6):
                y = row_height * i
                # Daddy column
                if i < 6 - len(daddy_imgs):
                    combined.paste(blank_daddy, (0, y))
                else:
                    img = daddy_imgs[i - (6 - len(daddy_imgs))]
                    img_resized = img.resize((max_daddy_w, row_height))
                    combined.paste(img_resized, (0, y))
                # Maximus column
                if i < 6 - len(maximus_imgs):
                    combined.paste(blank_maximus, (max_daddy_w, y))
                else:
                    img = maximus_imgs[i - (6 - len(maximus_imgs))]
                    img_resized = img.resize((max_maximus_w, row_height))
                    combined.paste(img_resized, (max_daddy_w, y))
            combined.save(debug_path)
            print(f"[DEBUG] Saved combined new_perk_region screenshot to {debug_path}")
            last_debug_save_time = time.time()
    if screenshot is None:
        print(f"  [{window_name}] Warning: Could not capture region for OCR")
        return ""
    if False and save_debug_image and window_name:
        # Save last 6 Daddy and Maximus new_perk_region screenshots, stacked vertically (Daddy left, Maximus right)
        from PIL import Image as PILImage
        debug_path = os.path.join(SCRIPT_DIR, 'debug_newperk_combined.png')
        # Use lists to store last 6 for each, persistently
        if not hasattr(get_text_from_region, '_daddy_imgs'):
            get_text_from_region._daddy_imgs = []
        if not hasattr(get_text_from_region, '_maximus_imgs'):
            get_text_from_region._maximus_imgs = []

        # Add new screenshot to appropriate list
        updated = False
        if 'daddy' in window_name.lower():
            get_text_from_region._daddy_imgs.append(screenshot.copy())
            if len(get_text_from_region._daddy_imgs) > 6:
                get_text_from_region._daddy_imgs = get_text_from_region._daddy_imgs[-6:]
            updated = True
        if 'maximus' in window_name.lower():
            get_text_from_region._maximus_imgs.append(screenshot.copy())
            if len(get_text_from_region._maximus_imgs) > 6:
                get_text_from_region._maximus_imgs = get_text_from_region._maximus_imgs[-6:]
            updated = True

        # Always update the combined image if either list changed
        if updated:
            daddy_imgs = get_text_from_region._daddy_imgs[-6:]
            maximus_imgs = get_text_from_region._maximus_imgs[-6:]
            # Always show 6 rows, fill with blank if missing
            from PIL import Image as PILImage
            max_daddy_w = max((img.width for img in daddy_imgs), default=1)
            max_maximus_w = max((img.width for img in maximus_imgs), default=1)
            row_height = max(
                max((img.height for img in daddy_imgs), default=1),
                max((img.height for img in maximus_imgs), default=1)
            )
            total_height = row_height * 6
            total_width = max_daddy_w + max_maximus_w
            combined = PILImage.new('RGB', (total_width, total_height), color=(128, 128, 128))
            # Fill up to 6 images with blank if needed
            blank_daddy = PILImage.new('RGB', (max_daddy_w, row_height), color=(64, 64, 64))
            blank_maximus = PILImage.new('RGB', (max_maximus_w, row_height), color=(64, 64, 64))
            for i in range(6):
                y = row_height * i
                # Daddy column
                if i < 6 - len(daddy_imgs):
                    combined.paste(blank_daddy, (0, y))
                else:
                    img = daddy_imgs[i - (6 - len(daddy_imgs))]
                    img_resized = img.resize((max_daddy_w, row_height))
                    combined.paste(img_resized, (0, y))
                # Maximus column
                if i < 6 - len(maximus_imgs):
                    combined.paste(blank_maximus, (max_daddy_w, y))
                else:
                    img = maximus_imgs[i - (6 - len(maximus_imgs))]
                    img_resized = img.resize((max_maximus_w, row_height))
                    combined.paste(img_resized, (max_daddy_w, y))
            combined.save(debug_path)
            print(f"[DEBUG] Saved combined new_perk_region screenshot to {debug_path}")
            last_debug_save_time = time.time()
    if screenshot is None:
        print(f"  [{window_name}] Warning: Could not capture region for OCR")
        return ""
    # Preprocess: grayscale, threshold, sharpen (same as New Perk bar)
    # For Daddy and Maximus, use grayscale only, no thresholding
    if window_name and ('maximus' in window_name.lower() or 'daddy' in window_name.lower()):
        img = screenshot.convert('L')
        text = pytesseract.image_to_string(img, config='--psm 7')
    else:
        # For any other window, keep thresholding
        img = screenshot.convert('L')
        img = img.point(lambda x: 0 if x < 180 else 255, '1')
        text = pytesseract.image_to_string(img, config='--psm 7')
    # Extra cleaning: remove non-ascii, collapse whitespace
    import re
    if text is None:
        text = ""
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = ' '.join(text.split())
    return text

def select_best_perk(window_name, coords):
    """Read both perk options and click the better one.
    
    Purple background perks are deprioritized unless:
    - The perk is Priority 1 (exempt from purple penalty)
    - Both perks have purple backgrounds (no choice)
    """
    global SKIP_NEW_PERK_BAR_UNTIL_NUMBERS
    # Read top two options always
    perk1_text = get_text_from_region(window_name, coords['perk1_text_region'])
    perk2_text = get_text_from_region(window_name, coords['perk2_text_region'])

    # Optionally read third perk region if present (only for Maximus)
    has_third = window_name and 'maximus' in window_name.lower() and 'perk3_text_region' in coords and 'perk_option_3' in coords
    perk3_text = None
    if has_third:
        perk3_text = get_text_from_region(window_name, coords['perk3_text_region'])

    print(f"  [{window_name}] Perk 1: {perk1_text[:50]}..." if len(perk1_text) > 50 else f"  [{window_name}] Perk 1: {perk1_text}")
    print(f"  [{window_name}] Perk 2: {perk2_text[:50]}..." if len(perk2_text) > 50 else f"  [{window_name}] Perk 2: {perk2_text}")
    if has_third:
        print(f"  [{window_name}] Perk 3: {perk3_text[:50]}..." if len(perk3_text) > 50 else f"  [{window_name}] Perk 3: {perk3_text}")

    # Pass window_name to get_perk_priority for alternate list support
    priority1 = get_perk_priority(perk1_text, window_name)
    priority2 = get_perk_priority(perk2_text, window_name)
    priority3 = get_perk_priority(perk3_text, window_name) if has_third else None

    # Determine which perk list was used
    if window_name and 'daddy' in window_name.lower():
        perk_list_name = "PERK_PRIORITY_DADDY"
    else:
        perk_list_name = "PERK_PRIORITY"

    print(f"  [{window_name}] Priority 1: {priority1}, Priority 2: {priority2}" + (f", Priority 3: {priority3}" if has_third else ""))

    # Check for purple backgrounds (returns tuple: (is_purple, color))
    print(f"  [{window_name}] Checking perk 1 background...")
    perk1_is_purple, perk1_bg_color = is_purple_background(window_name, coords['perk1_text_region'])
    print(f"  [{window_name}] Checking perk 2 background...")
    perk2_is_purple, perk2_bg_color = is_purple_background(window_name, coords['perk2_text_region'])
    perk3_is_purple = False
    perk3_bg_color = None
    if has_third:
        print(f"  [{window_name}] Checking perk 3 background...")
        perk3_is_purple, perk3_bg_color = is_purple_background(window_name, coords['perk3_text_region'])

    # List of keywords for acceptable purple perks
    ACCEPTABLE_PURPLE_KEYWORDS = [
        ["cash per wave"],
        ["boss health"],
        ["tower damage", "bosses"]
    ]

    def is_acceptable_purple(perk_text):
        if not perk_text:
            return False
        text = perk_text.lower()
        for keywords in ACCEPTABLE_PURPLE_KEYWORDS:
            if all(k in text for k in keywords):
                return True
        return False

    effective_priority1 = priority1
    effective_priority2 = priority2
    effective_priority3 = priority3 if has_third else None
    PURPLE_PENALTY = 10000

    # If all available perks are purple
    if has_third:
        if perk1_is_purple and perk2_is_purple and perk3_is_purple:
            perk1_ok = is_acceptable_purple(perk1_text)
            perk2_ok = is_acceptable_purple(perk2_text)
            perk3_ok = is_acceptable_purple(perk3_text)
            if not (perk1_ok or perk2_ok or perk3_ok):
                print(f"  [{window_name}] All three perks are purple and none acceptable. Skipping selection and closing window.")
                log_perk_selection_three(window_name, perk1_text, priority1, perk2_text, priority2, perk3_text, priority3, "NONE - ALL PURPLE",
                                         perk1_is_purple=perk1_is_purple, perk2_is_purple=perk2_is_purple, perk3_is_purple=perk3_is_purple,
                                         effective_priority1=effective_priority1, effective_priority2=effective_priority2, effective_priority3=effective_priority3,
                                         perk1_bg_color=perk1_bg_color, perk2_bg_color=perk2_bg_color, perk3_bg_color=perk3_bg_color,
                                         perk_list_name=perk_list_name, selected_note=None)
                click_at(window_name, coords['close_x'], "Close X (skip purple perks)")
                time.sleep(0.5)
                click_at(window_name, coords['play_pause'], "Resume Game (skip purple perks)")
                time.sleep(0.5)
                globals()['SKIP_NEW_PERK_BAR_UNTIL_NUMBERS'] = True
                return False
    else:
        # Two-perk case: original behavior
        if perk1_is_purple and perk2_is_purple:
            perk1_ok = is_acceptable_purple(perk1_text)
            perk2_ok = is_acceptable_purple(perk2_text)
            if not perk1_ok and not perk2_ok:
                print(f"  [{window_name}] Both perks are purple and neither is acceptable. Skipping selection and closing window.")
                log_perk_selection(window_name, perk1_text, priority1, perk2_text, priority2, "NONE - BOTH PURPLE",
                                  perk1_is_purple=perk1_is_purple, perk2_is_purple=perk2_is_purple,
                                  effective_priority1=effective_priority1, effective_priority2=effective_priority2,
                                  perk1_bg_color=perk1_bg_color, perk2_bg_color=perk2_bg_color,
                                  perk_list_name=perk_list_name)
                click_at(window_name, coords['close_x'], "Close X (skip purple perks)")
                time.sleep(0.5)
                click_at(window_name, coords['play_pause'], "Resume Game (skip purple perks)")
                time.sleep(0.5)
                globals()['SKIP_NEW_PERK_BAR_UNTIL_NUMBERS'] = True
                return False

    # Apply purple penalty (add large penalty to deprioritize)
    if perk1_is_purple and priority1 != PURPLE_EXEMPT_PRIORITY and not is_acceptable_purple(perk1_text):
        print(f"  [{window_name}] Perk 1 has PURPLE background - applying penalty")
        effective_priority1 = priority1 + PURPLE_PENALTY

    if perk2_is_purple and priority2 != PURPLE_EXEMPT_PRIORITY and not is_acceptable_purple(perk2_text):
        print(f"  [{window_name}] Perk 2 has PURPLE background - applying penalty")
        effective_priority2 = priority2 + PURPLE_PENALTY

    if has_third and perk3_is_purple and priority3 != PURPLE_EXEMPT_PRIORITY and not is_acceptable_purple(perk3_text):
        print(f"  [{window_name}] Perk 3 has PURPLE background - applying penalty")
        effective_priority3 = priority3 + PURPLE_PENALTY

    print(f"  [{window_name}] Effective Priority 1: {effective_priority1}, Effective Priority 2: {effective_priority2}" + (f", Effective Priority 3: {effective_priority3}" if has_third else ""))

    # If none recognized
    if priority1 == 9999 and priority2 == 9999 and (not has_third or priority3 == 9999):
        print(f"  [{window_name}] WARNING: No perk recognized!")
        if has_third:
            log_perk_selection_three(window_name, perk1_text, priority1, perk2_text, priority2, perk3_text, priority3, "NONE - UNRECOGNIZED",
                                     perk1_is_purple=perk1_is_purple, perk2_is_purple=perk2_is_purple, perk3_is_purple=perk3_is_purple,
                                     effective_priority1=effective_priority1, effective_priority2=effective_priority2, effective_priority3=effective_priority3,
                                     perk1_bg_color=perk1_bg_color, perk2_bg_color=perk2_bg_color, perk3_bg_color=perk3_bg_color,
                                     perk_list_name=perk_list_name, selected_note=None)
        else:
            log_perk_selection(window_name, perk1_text, priority1, perk2_text, priority2, "NONE - UNRECOGNIZED",
                              perk1_is_purple=perk1_is_purple, perk2_is_purple=perk2_is_purple,
                              effective_priority1=effective_priority1, effective_priority2=effective_priority2,
                              perk1_bg_color=perk1_bg_color, perk2_bg_color=perk2_bg_color,
                              perk_list_name=perk_list_name)
        return False

    # Choose the minimal effective priority
    if has_third:
        # Build list and pick first occurrence of minimal value
        effs = [effective_priority1, effective_priority2, effective_priority3]
        min_val = min(effs)
        selected_index = effs.index(min_val) + 1
        # Determine purple note (exempt if base priority equals PURPLE_EXEMPT_PRIORITY)
        base_priorities = [priority1, priority2, priority3]
        is_purples = [perk1_is_purple, perk2_is_purple, perk3_is_purple]
        sel_base = base_priorities[selected_index-1]
        sel_is_purple = is_purples[selected_index-1]
        purple_note = " (purple but exempt)" if sel_is_purple and sel_base == PURPLE_EXEMPT_PRIORITY else ""
        print(f"  [{window_name}] Selecting Perk {selected_index} (priority {base_priorities[selected_index-1]}){purple_note}")
        # Log and click
        log_perk_selection_three(window_name, perk1_text, priority1, perk2_text, priority2, perk3_text, priority3, selected_index,
                                 perk1_is_purple=perk1_is_purple, perk2_is_purple=perk2_is_purple, perk3_is_purple=perk3_is_purple,
                                 effective_priority1=effective_priority1, effective_priority2=effective_priority2, effective_priority3=effective_priority3,
                                 perk1_bg_color=perk1_bg_color, perk2_bg_color=perk2_bg_color, perk3_bg_color=perk3_bg_color,
                                 perk_list_name=perk_list_name, selected_note=purple_note)
        # Click the selected option
        if selected_index == 1:
            click_at(window_name, coords['perk_option_1'], "Perk Option 1")
        elif selected_index == 2:
            click_at(window_name, coords['perk_option_2'], "Perk Option 2")
        else:
            click_at(window_name, coords['perk_option_3'], "Perk Option 3")
    else:
        # Two-option selection (preserve previous behavior)
        if effective_priority1 <= effective_priority2:
            purple_note = " (purple but exempt)" if perk1_is_purple and priority1 == PURPLE_EXEMPT_PRIORITY else ""
            purple_note = " (purple but other is worse)" if perk1_is_purple and perk2_is_purple else purple_note
            print(f"  [{window_name}] Selecting Perk 1 (priority {priority1}){purple_note}")
            log_perk_selection(window_name, perk1_text, priority1, perk2_text, priority2, 1,
                              perk1_is_purple=perk1_is_purple, perk2_is_purple=perk2_is_purple,
                              effective_priority1=effective_priority1, effective_priority2=effective_priority2,
                              perk1_bg_color=perk1_bg_color, perk2_bg_color=perk2_bg_color,
                              perk_list_name=perk_list_name)
            click_at(window_name, coords['perk_option_1'], "Perk Option 1")
        else:
            purple_note = " (purple but exempt)" if perk2_is_purple and priority2 == PURPLE_EXEMPT_PRIORITY else ""
            purple_note = " (purple but other is worse)" if perk1_is_purple and perk2_is_purple else purple_note
            print(f"  [{window_name}] Selecting Perk 2 (priority {priority2}){purple_note}")
            log_perk_selection(window_name, perk1_text, priority1, perk2_text, priority2, 2,
                              perk1_is_purple=perk1_is_purple, perk2_is_purple=perk2_is_purple,
                              effective_priority1=effective_priority1, effective_priority2=effective_priority2,
                              perk1_bg_color=perk1_bg_color, perk2_bg_color=perk2_bg_color,
                              perk_list_name=perk_list_name)
            click_at(window_name, coords['perk_option_2'], "Perk Option 2")

    return True

def get_current_foreground_window():
    """Get the handle and title of the currently active foreground window."""
    if not WIN32_SUPPORT:
        return None, None
    
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            title = win32gui.GetWindowText(hwnd)
            return hwnd, title
        return None, None
    except Exception as e:
        print(f"  Error getting foreground window: {e}")
        return None, None

def restore_foreground_window(hwnd, title):
    """Restore a previously saved window to the foreground."""
    if not WIN32_SUPPORT or hwnd is None:
        return False
    
    try:
        # Check if window still exists
        if not win32gui.IsWindow(hwnd):
            print(f"  Previous window no longer exists: '{title}'")
            return False
        
        # Restore if minimized
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        
        # Bring to foreground
        win32gui.SetForegroundWindow(hwnd)
        print(f"  Restored previous window: '{title}'")
        return True
    except Exception as e:
        print(f"  Error restoring window '{title}': {e}")
        return False

def handle_perk_selection(window_name):
    """Handle the complete perk selection process for a window."""
    
    # Save the current foreground window so we can restore it later
    saved_hwnd, saved_title = get_current_foreground_window()
    if saved_title:
        print(f"  Saving current window: '{saved_title}'")
    
    coords = get_coords(window_name)
    
    print(f">>> [{window_name}] NEW PERK DETECTED! <<<")
    
    print(f"  [{window_name}] Step 1: Ensuring game is paused...")
    ensure_game_paused(window_name, coords)
    
    # Loop to select all available perks
    while True:
        print(f"  [{window_name}] Step 2: Opening perk window...")
        click_at(window_name, coords['new_perk_bar'], "New Perk Bar")
        time.sleep(WINDOW_OPEN_WAIT)
        
        print(f"  [{window_name}] Step 3: Selecting best perk...")
        coords = get_coords(window_name)
        # If this is Maximus and a third perk region exists, capture an image of all 3 perks for verification
        try:
            if window_name and 'maximus' in window_name.lower() and 'perk1_text_region' in coords and 'perk2_text_region' in coords and 'perk3_text_region' in coords:
                try:
                    img1 = capture_window_screenshot(window_name, coords['perk1_text_region'])
                    img2 = capture_window_screenshot(window_name, coords['perk2_text_region'])
                    img3 = capture_window_screenshot(window_name, coords['perk3_text_region'])
                    if img1 and img2 and img3:
                        from PIL import Image as PILImage
                        widths = [img1.width, img2.width, img3.width]
                        heights = [img1.height, img2.height, img3.height]
                        total_height = sum(heights)
                        max_width = max(widths)
                        combined = PILImage.new('RGB', (max_width, total_height), color=(0,0,0))
                        y = 0
                        for im in (img1, img2, img3):
                            # If narrower than max width, pad to center
                            if im.width < max_width:
                                bg = PILImage.new('RGB', (max_width, im.height), color=(0,0,0))
                                bg.paste(im, ((max_width - im.width)//2, 0))
                                im = bg
                            combined.paste(im, (0, y))
                            y += im.height
                        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        out_path = SCRIPT_DIR / f"maximus_perks_{stamp}.png"
                        combined.save(out_path)
                        print(f"  [{window_name}] Saved Maximus 3-perk snapshot to {out_path}")
                except Exception as e:
                    print(f"  [{window_name}] Could not capture/save Maximus perks image: {e}")
        except Exception:
            pass

        perk_selected = select_best_perk(window_name, coords)
        
        if perk_selected:
            time.sleep(WINDOW_CLOSE_WAIT)
        
        print(f"  [{window_name}] Step 4: Closing perk window...")
        click_at(window_name, coords['close_x'], "Close X")
        time.sleep(WINDOW_CLOSE_WAIT)
        
        print(f"  [{window_name}] Step 5: Checking if more perks available...")
        coords = get_coords(window_name)
        if check_for_new_perk(window_name, coords):
            print(f"  [{window_name}] More perks available! Selecting another...")
        else:
            print(f"  [{window_name}] No more perks available.")
            break
    
    print(f"  [{window_name}] Step 6: Ensuring game is running...")
    ensure_game_running(window_name, coords)
    
    print(f">>> [{window_name}] Perk selection complete! <<<")
    
    # Restore the previous foreground window
    if saved_hwnd:
        print(f"  [{window_name}] Step 7: Restoring previous window...")
        time.sleep(0.3)  # Brief pause before switching back
        restore_foreground_window(saved_hwnd, saved_title)
    
    print()

def check_window(window_name):
    """Check a single window for new perks and handle if found."""
    window = get_target_window(window_name)
    if not window:
        return False
    
    coords = get_coords(window_name)
    
    if check_for_new_perk(window_name, coords):
        handle_perk_selection(window_name)
        return True
    
    return False

def handle_wave_1_detected(window_name):
    """Handle when wave 1 is detected - bring window to focus, then switch back after 10 seconds."""
    # Save the current foreground window
    saved_hwnd, saved_title = get_current_foreground_window()
    if saved_title:
        print(f"  Saving current window: '{saved_title}'")
    
    print(f"\n{'!'*60}")
    print(f"  WAVE 1 DETECTED ON: {window_name}")
    print(f"  Bringing window to focus...")
    print(f"{'!'*60}\n")
    
    # Log the event
    write_to_log(f"WAVE 1 DETECTED on {window_name} - bringing to focus")
    
    # Bring the window to focus
    bring_window_to_focus(window_name)
    
    # Start a thread to restore the original window after 10 seconds
    if saved_hwnd:
        def restore_after_delay():
            time.sleep(10)
            print(f"  Restoring previous window after 10 seconds...")
            restore_foreground_window(saved_hwnd, saved_title)
        
        threading.Thread(target=restore_after_delay, daemon=True).start()

def main_loop():
    """Main automation loop."""
    global last_wave1_times
    print("=" * 60)
    print("Tower Idle Defense - Perk Automator v5 (Combined)")
    print("=" * 60)
    print()
    
    # Clear and recreate log files at startup
    initialize_log_files()
    print()
    
    # Log startup
    write_to_log("=" * 70)
    write_to_log("PERK AUTOMATOR STARTED")
    write_to_log("=" * 70)
    
    # Check all windows
    print("Configured windows:")
    for window_name in WINDOWS:
        window = get_target_window(window_name)
        if window:
            print(f"  ✓ {window_name}: Position ({window.left}, {window.top}), Size {window.width}x{window.height}")
            write_to_log(f"Window found: {window_name} at ({window.left}, {window.top})")
        else:
            print(f"  ✗ {window_name}: NOT FOUND")
            write_to_log(f"Window NOT found: {window_name}")
    
    print()
    print(f"Log file: {os.path.abspath(LOG_FILE)}")
    print()
    print("TO STOP: Move mouse to ANY corner of the screen")
    print("         OR press Ctrl+C in this window")
    print()
    print("Features enabled:")
    print("  - Auto perk selection")
    print("  - Purple background detection")
    print("  - Wave 1 detection (will bring window to focus)")
    print()
    print("Starting in 3 seconds...")
    print()
    time.sleep(3)
    
    pyautogui.FAILSAFE = True

    # Show a simple GUI to allow toggling which windows to monitor
    if TKINTER_AVAILABLE:
        try:
            def show_window_selector():
                root = tk.Tk()
                root.title("Perk Automator - Window Selector")

                tk.Label(root, text="Select windows to enable for perk selection:").pack(padx=10, pady=(10, 0))

                vars = {}
                # Show each configured window with a checkbox
                for name in list(WINDOWS):
                    found = False
                    try:
                        if WINDOW_SUPPORT:
                            for w in gw.getAllWindows():
                                if w.title and name.lower() in w.title.lower():
                                    found = True
                                    break
                    except Exception:
                        found = False
                    var = tk.BooleanVar(value=found)
                    cb_text = f"{name} {'(found)' if found else '(not found)'}"
                    chk = tk.Checkbutton(root, text=cb_text, variable=var)
                    chk.pack(anchor='w', padx=12)
                    vars[name] = var

                def select_all():
                    for v in vars.values():
                        v.set(True)

                def clear_all():
                    for v in vars.values():
                        v.set(False)

                btn_frame = tk.Frame(root)
                btn_frame.pack(pady=8)
                tk.Button(btn_frame, text="Select All", command=select_all).pack(side='left', padx=6)
                tk.Button(btn_frame, text="Clear All", command=clear_all).pack(side='left', padx=6)

                def on_start():
                    selected = [n for n, v in vars.items() if v.get()]
                    if not selected:
                        if not messagebox.askyesno("No Windows Selected", "No windows are selected — continue with none?"):
                            return
                    # Update global WINDOWS list
                    global WINDOWS
                    WINDOWS = selected
                    root.destroy()

                tk.Button(root, text="Start", command=on_start).pack(pady=(0, 12))
                # Center window
                root.update_idletasks()
                w = root.winfo_width()
                h = root.winfo_height()
                x = (root.winfo_screenwidth() // 2) - (w // 2)
                y = (root.winfo_screenheight() // 2) - (h // 2)
                root.geometry(f"+{x}+{y}")
                root.mainloop()

            # Show selector before starting
            show_window_selector()
        except Exception as e:
            print(f"GUI selector failed: {e}")
    else:
        print("Tkinter not available — running with configured WINDOWS list.")
    
    while True:
        try:
            check_failsafe()
            # Check each window for new perks and wave 1
            for window_name in WINDOWS:
                check_failsafe()
                window = get_target_window(window_name)
                if not window:
                    continue
                coords = get_coords(window_name)
                # Check for wave 1 using New Perk bar
                print(f"[{window_name}] Checking for Wave 1 using New Perk bar...")
                perk_bar_text = get_text_from_region(window_name, coords['new_perk_region'])
                perk_bar_text_clean = perk_bar_text.strip().lower().replace('|', '').replace(' ', '')
                print(f"  [{window_name}] Perk bar OCR (for wave): '{perk_bar_text}'")
                import re
                match = re.match(r'^1/\d+', perk_bar_text_clean)
                if match and (window_name not in last_wave1_times or time.time() - last_wave1_times[window_name] > 30):
                    print(f"  [{window_name}] >>> WAVE 1 DETECTED! <<<")
                    handle_wave_1_detected(window_name)
                    last_wave1_times[window_name] = time.time()
                # Check for new perk
                print(f"[{window_name}] Checking for New Perk...")
                perk_text = get_text_from_region(window_name, coords['new_perk_region'])
                perk_text_lower = perk_text.strip().lower()
                print(f"  [{window_name}] Perk bar OCR: '{perk_text_lower}'")
                if "new perk" in perk_text_lower or "perk" in perk_text_lower:
                    print(f"  [{window_name}] New Perk detected!")
                    handle_perk_selection(window_name)
                else:
                    print(f"  [{window_name}] No new perk available.")
            print(f"Waiting {CHECK_INTERVAL} seconds...")
            print("-" * 60)
            for _ in range(CHECK_INTERVAL * 5):
                check_failsafe()
                time.sleep(0.2)
        except KeyboardInterrupt:
            print("\n\nStopped by user (Ctrl+C)")
            break
        except Exception as e:
            if "FAILSAFE" in str(e):
                print(f"\n\n{e}")
                break
            else:
                print(f"\nERROR: {e}")
                print("Waiting 5 seconds before retrying...")
                time.sleep(5)

if __name__ == "__main__":
    main_loop()
