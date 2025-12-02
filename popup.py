import tkinter as tk

current_popup = None

def close_popup():
    global current_popup
    if current_popup:
        try:
            current_popup.destroy()
        except:
            pass
        current_popup = None

def get_popup():
    global current_popup
    return current_popup

def set_popup(popup):
    global current_popup
    current_popup = popup

def bind_popup_events(window):
    def on_focus_out(event):
        window.after(50, check_and_close)
    
    def check_and_close():
        try:
            if get_popup() and get_popup().focus_get() is not None:
                return
            close_popup()
        except tk.TclError:
            pass
    
    def on_escape(event):
        close_popup()
    
    window.bind("<FocusOut>", on_focus_out)
    window.bind("<Escape>", on_escape)
    window.after(10, lambda: safe_focus(window))

def safe_focus(window):
    try:
        window.focus_force()
        window.lift()
    except tk.TclError:
        pass