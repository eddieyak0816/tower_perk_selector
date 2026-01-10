import pyautogui
import time

# Try to import win32gui for window capture
try:
    import win32gui
    import win32ui
    from ctypes import windll
    from PIL import Image
    WIN32_SUPPORT = True
except ImportError:
    WIN32_SUPPORT = False
    print("WARNING: pywin32 not installed. Run: pip install pywin32")

# ============================================
# CONFIGURATION - Change this to match your window
# ============================================

TARGET_WINDOW = "Daddy Bluestack"  # Change to "Maximus Bluestack" if needed
CHECK_POSITION = (1135, 24)  # Position to check

# ============================================

def capture_window_pixel(x, y):
    """Capture a single pixel from the window at relative coordinates."""
    if not WIN32_SUPPORT:
        return None
    
    try:
        hwnd = win32gui.FindWindow(None, TARGET_WINDOW)
        if hwnd == 0:
            print(f"Window '{TARGET_WINDOW}' not found!")
            return None
        
        # Get window dimensions
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        window_width = right - left
        window_height = bottom - top
        
        # Create device contexts
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        
        # Create bitmap
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, window_width, window_height)
        saveDC.SelectObject(saveBitMap)
        
        # Use PrintWindow to capture
        result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
        if result == 0:
            result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)
        
        # Convert to PIL Image
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        
        img = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1
        )
        
        # Cleanup
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)
        
        # Get pixel at position
        if x < img.width and y < img.height:
            return img.getpixel((x, y))
        else:
            print(f"Position ({x}, {y}) is outside window bounds ({img.width}, {img.height})")
            return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print("=" * 50)
    print("Pixel Color Checker")
    print("=" * 50)
    print(f"Target Window: {TARGET_WINDOW}")
    print(f"Check Position: {CHECK_POSITION}")
    print()
    print("This will check the pixel color every 2 seconds.")
    print("Toggle play/pause in your game to see the color change.")
    print()
    print("Press Ctrl+C to stop.")
    print()
    print("-" * 50)
    
    while True:
        try:
            pixel = capture_window_pixel(CHECK_POSITION[0], CHECK_POSITION[1])
            
            if pixel:
                r, g, b = pixel
                print(f"Color at {CHECK_POSITION}: RGB({r}, {g}, {b}) | Hex: #{r:02X}{g:02X}{b:02X}")
            else:
                print("Could not capture pixel")
            
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("\nStopped.")
            break

if __name__ == "__main__":
    main()
