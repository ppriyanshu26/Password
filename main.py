import threading
import keyboard
import uiautomation as auto
from matcher import get_matching_accounts
from popup import show_popup
import sys
import os
from config import TRIGGER_KEYWORDS, HOTKEY, APP_NAME, APP_VERSION

def check_focused_element():
    try:
        with auto.UIAutomationInitializerInThread():
            element = auto.GetFocusedControl()
            if element is None:
                return False
            
            name_words = set((element.Name or "").lower().split())
            return bool(name_words & TRIGGER_KEYWORDS)       
    except Exception as e:
        print(f"Error checking focused element: {e}")
        return True

def show_menu():
    try:
        if not check_focused_element():
            element = auto.GetFocusedControl()
            if element:
                print(f"[Password Manager] Not a login field: '{element.Name}', skipping...")
            else:
                print("[Password Manager] No focused element found, skipping...")
            return
        
        accounts = get_matching_accounts()
        
        popup_thread = threading.Thread(target=lambda: show_popup(accounts), daemon=True)
        popup_thread.start()       
    except Exception as e:
        print(f"Error showing menu: {e}")

def on_hotkey():
    print("[Password Manager] Hotkey triggered!")
    show_menu()

def main():
    print("=" * 50)
    print(f"  {APP_NAME} Started")
    print(f"  Version: {APP_VERSION}")
    print(f"  Hotkey: {HOTKEY}")
    print("=" * 50)
    
    keyboard.add_hotkey(HOTKEY, on_hotkey, suppress=True)
    
    try:
        keyboard.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        keyboard.unhook_all()
        sys.exit(0)

if __name__ == "__main__":
    main()
