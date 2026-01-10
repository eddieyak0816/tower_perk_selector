import pyautogui
import time

# Test positions
TEST_POS_1 = (5, 500)
TEST_POS_2 = (400, 500)

print("=== Ad Detection Test ===")
print(f"Testing pixel colors at positions {TEST_POS_1} and {TEST_POS_2}")
print()
print("This will check the colors every 2 seconds.")
print("Try with and without an ad to see the difference.")
print("Press Ctrl+C to stop.")
print()

try:
    while True:
        # Get color at position 1
        screenshot1 = pyautogui.screenshot(region=(TEST_POS_1[0], TEST_POS_1[1], 1, 1))
        pixel1 = screenshot1.getpixel((0, 0))
        r1, g1, b1 = pixel1[0], pixel1[1], pixel1[2]
        
        # Get color at position 2
        screenshot2 = pyautogui.screenshot(region=(TEST_POS_2[0], TEST_POS_2[1], 1, 1))
        pixel2 = screenshot2.getpixel((0, 0))
        r2, g2, b2 = pixel2[0], pixel2[1], pixel2[2]
        
        print(f"Position {TEST_POS_1}: RGB ({r1:3d}, {g1:3d}, {b1:3d})")
        print(f"Position {TEST_POS_2}: RGB ({r2:3d}, {g2:3d}, {b2:3d})")
        print("-" * 40)
        
        time.sleep(2)
        
except KeyboardInterrupt:
    print("\n\nTest stopped.")
