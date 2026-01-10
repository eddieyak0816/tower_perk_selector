import pyautogui
import pytesseract
from PIL import Image
import time

# Try to import pygetwindow for window targeting
try:
    import pygetwindow as gw
    WINDOW_SUPPORT = True
except ImportError:
    WINDOW_SUPPORT = False
    print("WARNING: pygetwindow not installed. Run: pip install pygetwindow")
    print("Window targeting will not work without it.")

# Try to import win32gui for virtual desktop detection
try:
    import win32gui
    import win32con
    WIN32_SUPPORT = True
except ImportError:
    WIN32_SUPPORT = False
    print("WARNING: pywin32 not installed. Run: pip install pywin32")
    print("Virtual desktop detection will not work without it.")

# Set the path to Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ============================================
# WINDOW CONFIGURATION
# ============================================

# This script targets: Daddy Bluestack
TARGET_WINDOW = "Daddy Bluestack"

# ============================================
# CONFIGURATION - Coordinates WITH AD showing
# (These are RELATIVE to the window, not absolute screen coords)
# ============================================

COORDS_WITH_AD = {
    'play_pause': (1135, 28),
    'new_perk_bar': (1128, 74),
    'perk_option_1': (1133, 242),
    'perk_option_2': (1138, 345),
    'close_x': (1329, 132),
    'new_perk_region': ((1018, 63), (1228, 92)),
    'perk1_text_region': ((890, 200), (1343, 284)),
    'perk2_text_region': ((888, 305), (1345, 390)),
}

# ============================================
# CONFIGURATION - Coordinates WITHOUT AD showing
# ============================================

COORDS_NO_AD = {
    'play_pause': (1135, 27),
    'new_perk_bar': (944, 79),
    'perk_option_1': (956, 245),
    'perk_option_2': (957, 349),
    'close_x': (1145, 134),
    'new_perk_region': ((832, 62), (1044, 93)),
    'perk1_text_region': ((703, 199), (1159, 287)),
    'perk2_text_region': ((709, 307), (1160, 391)),
}

# Positions to check for ad detection (relative to window)
AD_CHECK_POS_1 = (5, 500)
AD_CHECK_POS_2 = (400, 500)

# ============================================
# PERK PRIORITY LIST - Using keyword matching
# Format: (priority, [list of keywords that ALL must match])
# Lower priority number = better perk
# ============================================

PERK_PRIORITY = [
    (1,  ["enemies damage", "tower damage"]),           # enemies damage -50%, but tower damage -50%
    (2,  ["perk wave requirement"]),                     # perk wave requirement -20
    (3,  ["golden tower"]),                              # golden tower
    (4,  ["death wave"]),                                # death wave
    (5,  ["spotlight"]),                                 # spotlight
    (6,  ["black hole"]),                                # black hole
    (7,  ["chrono field"]),                              # chrono field
    (8,  ["increase max game speed"]),                   # increase max game speed by +1
    (9,  ["max health"]),                                # x1.20 max health
    (10, ["poison swamp"]),                              # poison swamp
    (11, ["chain lightning"]),                           # chain lightning
    (12, ["smart missiles"]),                            # smart missiles
    (13, ["inner land mines"]),                          # inner land mines
    (14, ["defense percent"]),                           # defense percent +4
    (15, ["free upgrade chance"]),                       # free upgrade chance for all +5
    (16, ["cash bonus"]),                                # x1.15 cash bonus
    (17, ["all coin"]),                                  # x1.15 all coin
    (18, ["orbs"]),                                      # orbs +1
    (19, ["bounce shot"]),                               # bounce shot +2
    (20, ["interest"]),                                  # interest x1.50
    (21, ["land mine damage"]),                          # land mine damage x3.50
    (22, ["defense absolute"]),                          # x1.15 defense absolute
    (23, ["damage"]),                                    # x1.15 damage (generic - put after specific damage perks)
    (24, ["cash per wave"]),                             # x12.00 cash per wave
    (25, ["boss health", "boss speed"]),                 # boss health -70%, but boss speed +50%
    (26, ["ranged enemies", "attack distance"]),         # ranged enemies attack distance reduced
    (27, ["lifesteal"]),                                 # lifesteal x2.50
    (28, ["enemies speed"]),                             # enemies speed -40%
    (29, ["enemies have", "health"]),                    # enemies have -50% health
    (30, ["health regen"]),                              # tower health regen x8
    (31, ["coins", "tower max health"]),                 # x1.80 coins, but tower max health
    (32, ["tower damage", "bosses"]),                    # x1.50 tower damage, but bosses
]

# ============================================
# TIMING CONFIGURATION
# ============================================

CHECK_INTERVAL = 2
CLICK_DELAY = 0.5
WINDOW_OPEN_WAIT = 1.5
WINDOW_CLOSE_WAIT = 1.0

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
    Windows on other virtual desktops have specific attributes we can check.
    """
    if not WIN32_SUPPORT:
        return True  # Assume yes if we can't check
    
    try:
        # Method 1: Check if window is cloaked (hidden on another virtual desktop)
        # Windows 10/11 uses DWM to "cloak" windows on other desktops
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
        
        if result == 0:  # Success
            # If cloaked value is non-zero, window is on another desktop
            if cloaked.value != 0:
                return False
        
        # Method 2: Also verify the window is actually visible
        if not win32gui.IsWindowVisible(hwnd):
            return False
            
        return True
        
    except Exception as e:
        print(f"  Warning: Could not check desktop status: {e}")
        return True  # Assume yes if check fails

def get_target_window():
    """Get the target BlueStacks window using EXACT title match only."""
    if not WINDOW_SUPPORT:
        return None
    
    try:
        # Get ALL windows and filter for EXACT match only
        all_windows = gw.getAllWindows()
        for win in all_windows:
            if win.title == TARGET_WINDOW:  # Exact match only!
                return win
        
        # No exact match found
        print(f"WARNING: Window with exact title '{TARGET_WINDOW}' not found!")
        print(f"  (Make sure the window title matches exactly)")
        return None
    except Exception as e:
        print(f"Error getting window: {e}")
        return None

def is_target_window_on_current_desktop():
    """Check if our target window is on the currently active virtual desktop."""
    if not WINDOW_SUPPORT:
        return True
    
    if not WIN32_SUPPORT:
        return True
    
    try:
        # Find the window handle (hwnd) for our target window
        hwnd = win32gui.FindWindow(None, TARGET_WINDOW)
        if hwnd == 0:
            print(f"  Window '{TARGET_WINDOW}' not found")
            return False
        
        return is_window_on_current_desktop(hwnd)
        
    except Exception as e:
        print(f"  Error checking desktop: {e}")
        return True  # Assume yes if we can't check

def get_window_offset():
    """Get the top-left corner offset of the target window."""
    window = get_target_window()
    if window:
        return (window.left, window.top)
    return (0, 0)  # Fallback to absolute coords if window not found

def to_absolute_coords(relative_coords):
    """Convert window-relative coordinates to absolute screen coordinates."""
    offset_x, offset_y = get_window_offset()
    
    if isinstance(relative_coords, tuple) and len(relative_coords) == 2:
        # Check if it's a region (tuple of two tuples) or a point (tuple of two ints)
        if isinstance(relative_coords[0], tuple):
            # It's a region: ((x1, y1), (x2, y2))
            (x1, y1), (x2, y2) = relative_coords
            return ((x1 + offset_x, y1 + offset_y), (x2 + offset_x, y2 + offset_y))
        else:
            # It's a point: (x, y)
            x, y = relative_coords
            return (x + offset_x, y + offset_y)
    
    return relative_coords

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

def is_ad_showing():
    """Check if an ad is showing by comparing colors at two positions."""
    pos1 = to_absolute_coords(AD_CHECK_POS_1)
    pos2 = to_absolute_coords(AD_CHECK_POS_2)
    
    # Get color at position 1
    screenshot1 = pyautogui.screenshot(region=(pos1[0], pos1[1], 1, 1))
    pixel1 = screenshot1.getpixel((0, 0))
    
    # Get color at position 2
    screenshot2 = pyautogui.screenshot(region=(pos2[0], pos2[1], 1, 1))
    pixel2 = screenshot2.getpixel((0, 0))
    
    # If colors match, no ad. If different, ad is showing.
    colors_match = (pixel1[0] == pixel2[0] and pixel1[1] == pixel2[1] and pixel1[2] == pixel2[2])
    
    return not colors_match

def get_coords():
    """Get the correct coordinates based on ad presence."""
    check_failsafe()
    
    if is_ad_showing():
        print("  [Ad detected - using ad coordinates]")
        return COORDS_WITH_AD
    else:
        print("  [No ad - using no-ad coordinates]")
        return COORDS_NO_AD

def click_play_pause():
    """Press the play/pause keyboard shortcut."""
    check_failsafe()
    print(f"  Pressing Ctrl+Shift+U for Play/Pause")
    pyautogui.hotkey('ctrl', 'shift', 'u')
    time.sleep(CLICK_DELAY)

def click_at(coords, description=""):
    """Click at the specified coordinates (converts to absolute)."""
    check_failsafe()
    abs_coords = to_absolute_coords(coords)
    x, y = abs_coords
    print(f"  Clicking {description} at ({x}, {y})")
    pyautogui.click(x, y)
    time.sleep(CLICK_DELAY)

def get_text_from_region(region):
    """Capture a region and extract text using OCR."""
    check_failsafe()
    abs_region = to_absolute_coords(region)
    (x1, y1), (x2, y2) = abs_region
    width = x2 - x1
    height = y2 - y1
    
    screenshot = pyautogui.screenshot(region=(x1, y1, width, height))
    screenshot = screenshot.convert('L')
    text = pytesseract.image_to_string(screenshot)
    
    return text.strip().lower()

def check_for_new_perk(coords):
    """Check if 'New Perk' text is visible in the perk bar region."""
    region = coords['new_perk_region']
    text = get_text_from_region(region)
    print(f"  OCR read: '{text}'")
    
    return "new perk" in text.lower()

def get_perk_priority(perk_text):
    """
    Get the priority of a perk based on keyword matching.
    All keywords in the list must be present for a match.
    Lower number = higher priority.
    """
    perk_text_lower = perk_text.lower()
    
    for priority, keywords in PERK_PRIORITY:
        # Check if ALL keywords are present in the perk text
        all_match = all(keyword in perk_text_lower for keyword in keywords)
        if all_match:
            return priority
    
    return 9999

def select_best_perk(coords):
    """Read both perk options and click the better one."""
    perk1_text = get_text_from_region(coords['perk1_text_region'])
    perk2_text = get_text_from_region(coords['perk2_text_region'])
    
    print(f"  Perk 1: {perk1_text[:60]}..." if len(perk1_text) > 60 else f"  Perk 1: {perk1_text}")
    print(f"  Perk 2: {perk2_text[:60]}..." if len(perk2_text) > 60 else f"  Perk 2: {perk2_text}")
    
    priority1 = get_perk_priority(perk1_text)
    priority2 = get_perk_priority(perk2_text)
    
    print(f"  Priority 1: {priority1}, Priority 2: {priority2}")
    
    if priority1 == 9999 and priority2 == 9999:
        print("  WARNING: Neither perk recognized!")
        print("  >>> Add these perks to PERK_PRIORITY list <<<")
        return False
    
    if priority1 <= priority2:
        print(f"  Selecting Perk 1 (priority {priority1})")
        click_at(coords['perk_option_1'], "Perk Option 1")
    else:
        print(f"  Selecting Perk 2 (priority {priority2})")
        click_at(coords['perk_option_2'], "Perk Option 2")
    
    return True

def main_loop():
    """Main automation loop."""
    print("=" * 50)
    print("Tower Idle Defense - Perk Automator v5 (Daddy Bluestack)")
    print("=" * 50)
    print()
    
    # Check window support
    if WINDOW_SUPPORT:
        window = get_target_window()
        if window:
            print(f"TARGET WINDOW: '{TARGET_WINDOW}'")
            print(f"  Position: ({window.left}, {window.top})")
            print(f"  Size: {window.width} x {window.height}")
        else:
            print(f"WARNING: Window '{TARGET_WINDOW}' not found!")
            print("Make sure BlueStacks is running.")
    else:
        print("WARNING: Window targeting disabled (pygetwindow not installed)")
        print("Script will use absolute screen coordinates.")
    
    print()
    print("TO STOP: Move mouse to ANY corner of the screen")
    print("         OR press Ctrl+C in this window")
    print()
    print("Starting in 3 seconds...")
    print()
    time.sleep(3)
    
    pyautogui.FAILSAFE = True
    
    while True:
        try:
            check_failsafe()
            
            # Verify window still exists
            if WINDOW_SUPPORT:
                window = get_target_window()
                if not window:
                    print("Window not found! Waiting...")
                    time.sleep(2)
                    continue
            
            # CHECK: Is our target window on the CURRENT virtual desktop?
            if not is_target_window_on_current_desktop():
                print(f"  [{TARGET_WINDOW} is on another desktop - skipping]")
                time.sleep(CHECK_INTERVAL)
                continue
            
            coords = get_coords()
            
            print("Checking for New Perk...")
            if check_for_new_perk(coords):
                print(">>> NEW PERK DETECTED! <<<")
                
                print("Step 1: Pausing macro...")
                click_play_pause()
                time.sleep(CLICK_DELAY)
                
                # Loop to select all available perks
                while True:
                    print("Step 2: Opening perk window...")
                    click_at(coords['new_perk_bar'], "New Perk Bar")
                    time.sleep(WINDOW_OPEN_WAIT)
                    
                    print("Step 3: Selecting best perk...")
                    coords = get_coords()
                    perk_selected = select_best_perk(coords)
                    
                    if perk_selected:
                        time.sleep(WINDOW_CLOSE_WAIT)
                    
                    print("Step 4: Closing perk window...")
                    click_at(coords['close_x'], "Close X")
                    time.sleep(WINDOW_CLOSE_WAIT)
                    
                    print("Step 5: Checking if more perks available...")
                    coords = get_coords()
                    if check_for_new_perk(coords):
                        print("  More perks available! Selecting another...")
                    else:
                        print("  No more perks available.")
                        break
                
                print("Step 6: Resuming macro...")
                click_play_pause()
                
                print(">>> Perk selection complete! <<<")
                print()
            else:
                print("  No new perk available.")
            
            print(f"Waiting {CHECK_INTERVAL} seconds...")
            print("-" * 30)
            
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
