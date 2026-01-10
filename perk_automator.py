import pyautogui
import pytesseract
from PIL import Image
import time

# Set the path to Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ============================================
# CONFIGURATION - Coordinates (WITH AD showing)
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

# Offset when NO ad is showing (with ad X - without ad X)
# New Perk bar: 1128 - 944 = 184
AD_OFFSET = 184

# Positions to check for ad detection
AD_CHECK_POS_1 = (5, 500)
AD_CHECK_POS_2 = (400, 500)

# ============================================
# PERK PRIORITY LIST
# ============================================

PERK_PRIORITY = [
    ("contains", "enemies damage -50%, but tower damage -50%", 1),
    ("contains", "perk wave requirement -20", 2),
    ("contains", "golden tower", 3),
    ("contains", "death wave", 4),
    ("contains", "spotlight", 5),
    ("contains", "black hole", 6),
    ("contains", "chrono field", 7),
    ("contains", "increase max game speed by +1", 8),
    ("contains", "x1.20 max health", 9),
    ("contains", "poison swamp", 10),
    ("contains", "chain lightning", 11),
    ("contains", "smart missiles", 12),
    ("contains", "inner land mines", 13),
    ("contains", "defense percent +4", 14),
    ("contains", "free upgrade chance for all +5", 15),
    ("contains", "x1.15 cash bonus", 16),
    ("contains", "x1.15 all coin", 17),
    ("contains", "orbs +1", 18),
    ("contains", "bounce shot +2", 19),
    ("contains", "interest x1.50", 20),
    ("contains", "land mine damage x3.50", 21),
    ("contains", "x1.15 defense absolute", 22),
    ("contains", "x1.15 damage", 23),
    ("contains", "x12.00 cash per wave", 24),
    ("contains", "boss health -70%, but boss speed +50%", 25),
    ("contains", "ranged enemies attack distance reduced", 26),
    ("contains", "lifesteal x2.50", 27),
    ("contains", "enemies speed -40%", 28),
    ("contains", "enemies have -50% health", 29),
    ("contains", "tower health regen x8", 30),
    ("contains", "x1.80 coins, but tower max health", 31),
    ("contains", "x1.50 tower damage, but bosses", 32),
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
    # Get color at position 1
    screenshot1 = pyautogui.screenshot(region=(AD_CHECK_POS_1[0], AD_CHECK_POS_1[1], 1, 1))
    pixel1 = screenshot1.getpixel((0, 0))
    
    # Get color at position 2
    screenshot2 = pyautogui.screenshot(region=(AD_CHECK_POS_2[0], AD_CHECK_POS_2[1], 1, 1))
    pixel2 = screenshot2.getpixel((0, 0))
    
    # If colors match, no ad. If different, ad is showing.
    colors_match = (pixel1[0] == pixel2[0] and pixel1[1] == pixel2[1] and pixel1[2] == pixel2[2])
    
    return not colors_match

def get_adjusted_coords():
    """Get coordinates adjusted for ad presence."""
    check_failsafe()
    
    if is_ad_showing():
        print("  [Ad detected - using base coordinates]")
        return COORDS_WITH_AD
    else:
        print("  [No ad - adjusting coordinates by -184 pixels]")
        adjusted = {}
        for key, value in COORDS_WITH_AD.items():
            if key.endswith('_region'):
                (x1, y1), (x2, y2) = value
                adjusted[key] = ((x1 - AD_OFFSET, y1), (x2 - AD_OFFSET, y2))
            else:
                x, y = value
                adjusted[key] = (x - AD_OFFSET, y)
        return adjusted

def click_at(coords, description=""):
    """Click at the specified coordinates."""
    check_failsafe()
    x, y = coords
    print(f"  Clicking {description} at ({x}, {y})")
    pyautogui.click(x, y)
    time.sleep(CLICK_DELAY)

def get_text_from_region(region):
    """Capture a region and extract text using OCR."""
    check_failsafe()
    (x1, y1), (x2, y2) = region
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
    """Get the priority of a perk based on its text. Lower number = higher priority."""
    perk_text_lower = perk_text.lower()
    
    for match_type, match_text, priority in PERK_PRIORITY:
        if match_type == "exact":
            if match_text == perk_text_lower:
                return priority
        elif match_type == "contains":
            if match_text in perk_text_lower:
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
    print("Tower Idle Defense - Perk Automator")
    print("=" * 50)
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
            
            coords = get_adjusted_coords()
            
            print("Checking for New Perk...")
            if check_for_new_perk(coords):
                print(">>> NEW PERK DETECTED! <<<")
                
                print("Step 1: Pausing macro...")
                click_at(coords['play_pause'], "Play/Pause")
                time.sleep(CLICK_DELAY)
                
                print("Step 2: Opening perk window...")
                click_at(coords['new_perk_bar'], "New Perk Bar")
                time.sleep(WINDOW_OPEN_WAIT)
                
                print("Step 3: Selecting best perk...")
                coords = get_adjusted_coords()
                perk_selected = select_best_perk(coords)
                
                if perk_selected:
                    time.sleep(WINDOW_CLOSE_WAIT)
                
                print("Step 4: Closing perk window...")
                click_at(coords['close_x'], "Close X")
                time.sleep(WINDOW_CLOSE_WAIT)
                
                print("Step 5: Verifying perk was selected...")
                coords = get_adjusted_coords()
                if check_for_new_perk(coords):
                    print("  WARNING: New Perk still showing! Waiting and retrying...")
                    time.sleep(1)
                else:
                    print("  Perk selection confirmed!")
                
                print("Step 6: Resuming macro...")
                click_at(coords['play_pause'], "Play/Pause")
                
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
