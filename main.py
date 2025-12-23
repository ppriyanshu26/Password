import threading
import keyboard
import uiautomation as auto
from matcher import get_matching_accounts
from popup import show_popup_from_root
import sys
from config import TRIGGER_KEYWORDS, HOTKEY, APP_NAME, APP_VERSION
import tkinter as tk

root = None
popup_active = False

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
    global popup_active, root
    
    try:
        if popup_active:
            print("[Password Manager] Popup already active, skipping...")
            return
        
        popup_active = True
        
        if not check_focused_element():
            element = auto.GetFocusedControl()
            if element:
                print(f"[Password Manager] Not a login field: '{element.Name}', skipping...")
            else:
                print("[Password Manager] No focused element found, skipping...")
            popup_active = False
            return
        
        accounts = get_matching_accounts()
        try:
            if root and root.winfo_exists():
                root.after(0, lambda: show_popup_from_root(root, accounts, lambda: globals().__setitem__('popup_active', False)))
            else:
                popup_active = False
        except Exception as e:
            print(f"Error showing popup: {e}")
            popup_active = False
            
    except Exception as e:
        print(f"Error showing menu: {e}")
        popup_active = False

def on_hotkey():
    print("[Password Manager] Hotkey triggered!")
    thread = threading.Thread(target=show_menu, daemon=True)
    thread.start()

def main():
    global root
    
    print("=" * 50)
    print(f"  {APP_NAME} Started")
    print(f"  Version: {APP_VERSION}")
    print(f"  Hotkey: {HOTKEY}")
    print("=" * 50)
    
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", False)
    root.geometry("1x1+0+0")
    
    keyboard.add_hotkey(HOTKEY, on_hotkey, suppress=True)
    keyboard_thread = threading.Thread(target=keyboard.wait, daemon=True)
    keyboard_thread.start()
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nShutting down...")
        keyboard.unhook_all()
        sys.exit(0)
    finally:
        try:
            root.destroy()
        except:
            pass

if __name__ == "__main__":
    main()