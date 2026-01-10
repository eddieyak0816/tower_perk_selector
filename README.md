# Tower Perk Selector

Automates perk selection in Tower Idle Defense using image recognition and window management.

## Features
- Supports multiple BlueStacks windows
- Uses different perk priority lists for different windows (e.g., Daddy window)
- Logs all perk selections and actions
- Detects purple background perks and deprioritizes them

## Requirements
- Python 3.8+
- pyautogui
- pytesseract
- Pillow
- pygetwindow
- pywin32

## Setup
1. Install dependencies:
   ```
   pip install pyautogui pytesseract pillow pygetwindow pywin32
   ```
2. Install Tesseract-OCR and set the path in the script if needed.
3. Configure your BlueStacks window names and coordinates as needed.

## Usage
Run the script:
```
python perk_automator_v6_combined.py
```

## Stopping
Move your mouse to any corner of the screen or press Ctrl+C in the terminal.

---

MIT License
