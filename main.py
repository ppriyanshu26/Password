import threading
import keyboard
import uiautomation as auto
from matcher import get_matching_accounts
from popup import show_popup
import pystray
from PIL import Image, ImageDraw
import sys
import os


TRIGGER_KEYWORDS = {
    "email", "e-mail", "username", "user", "login", 
    "password", "pass", "signin", "sign in", "sign-in",
    "account", "credential", "id", "identifier",
    "phone", "mobile", "number"
}


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


def create_tray_icon():
    def create_image():
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        draw.ellipse([10, 10, 35, 35], fill='#4fc3f7', outline='#1a1a2e', width=2)
        draw.ellipse([18, 18, 27, 27], fill='#1a1a2e')
        
        draw.rectangle([30, 18, 55, 27], fill='#4fc3f7', outline='#1a1a2e', width=1)
        
        draw.rectangle([45, 27, 50, 35], fill='#4fc3f7')
        draw.rectangle([52, 27, 55, 32], fill='#4fc3f7')
        
        return image
    
    def on_quit(icon, item):
        icon.stop()
        keyboard.unhook_all()
        os._exit(0)
    
    def on_show_popup(icon, item):
        on_hotkey()
    
    menu = pystray.Menu(
        pystray.MenuItem("Show Popup (Ctrl+Shift+L)", on_show_popup),
        pystray.MenuItem("Quit", on_quit)
    )
    
    icon = pystray.Icon(
        "Password Manager",
        create_image(),
        "Password Manager\nCtrl+Shift+L",
        menu
    )
    
    return icon


def main():
    print("=" * 50)
    print("  Password Manager Started")
    print("  Hotkey: Ctrl+Shift+L")
    print("  Running in system tray...")
    print("=" * 50)
    
    keyboard.add_hotkey('ctrl+shift+l', on_hotkey, suppress=True)
    
    icon = create_tray_icon()
    
    try:
        icon.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        keyboard.unhook_all()
        sys.exit(0)


if __name__ == "__main__":
    main()
