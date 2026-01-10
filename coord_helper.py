import pyautogui
import time

print("=== Coordinate Helper Tool ===")
print("1. Position your mouse over the element you want")
print("2. Switch to this window (Alt+Tab)")
print("3. Press Enter to record the coordinates")
print("4. Type 'done' to finish\n")

coordinates = []

while True:
    name = input("Enter name for this location (or 'done' to finish): ")
    if name.lower() == 'done':
        break
    print("You have 3 seconds to position your mouse...")
    time.sleep(3)
    x, y = pyautogui.position()
    coordinates.append((name, x, y))
    print(f"  Recorded: {name} = ({x}, {y})\n")

print("\n=== All Recorded Coordinates ===")
for name, x, y in coordinates:
    print(f"{name}: ({x}, {y})")