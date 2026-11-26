import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import random
import ctypes
import json
import os
from pynput import keyboard

try:
    import winsound
except ImportError:
    winsound = None

# Windows API Mouse Constants
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040

# Map keyboard layout characters to standard QWERTY key names for hotkey consistency
LAYOUT_TO_EN_MAP = {
    '\u0636': 'Q', '\u0635': 'W', '\u062b': 'E', '\u0642': 'R', '\u0641': 'T',
    '\u063a': 'Y', '\u0639': 'U', '\u0647': 'I', '\u062e': 'O', '\u062d': 'P',
    '\u062c': '[', '\u062f': ']', '\u0634': 'A', '\u0633': 'S', '\u064a': 'D',
    '\u0628': 'F', '\u0644': 'G', '\u0627': 'H', '\u0623': 'H', '\u0625': 'H',
    '\u0622': 'H', '\u062a': 'J', '\u0646': 'K', '\u0645': 'L', '\u0643': ';',
    '\u0637': "'", '\u0626': 'Z', '\u0621': 'X', '\u0624': 'C', '\u0631': 'V',
    '\u0644\u0627': 'B', '\u0649': 'N', '\u0629': 'M', '\u0648': ',', '\u0632': '.',
    '\u0638': '/', '\u0630': '`'
}

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".autoclicker_fahad_pro_config.json")

# Neon Violet Color Palette
BG_MAIN = "#06040C"
BG_CARD = "#0B0816"
BG_INPUT = "#111622"
BORDER_VIOLET = "#6D28D9"
BORDER_SOFT = "#261A42"
NEON_CYAN = "#00D2FF"
NEON_PURPLE = "#A855F7"
NEON_GREEN = "#00E676"
DANGER_RED = "#E11D48"
GOLD = "#EAB308"
TEXT_PRIMARY = "#F8FAFC"
TEXT_MUTED = "#94A3B8"


class ScreenHudOverlay:
    """Draggable, resizable always-on-top screen indicator for in-game visibility."""

    def __init__(self, parent_app, x=40, y=40, scale=1.25):
        self.app = parent_app
        self.scale = max(0.8, min(2.5, float(scale)))
        self._drag_offset_x = 0
        self._drag_offset_y = 0

        self.win = tk.Toplevel(parent_app.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        try:
            self.win.attributes("-alpha", 0.92)
        except Exception:
            pass
        self.win.configure(bg=BG_MAIN)
        self.win.geometry(f"+{int(x)}+{int(y)}")

        self.outer = tk.Frame(
            self.win,
            bg="#0A0714",
            highlightbackground=NEON_GREEN,
            highlightthickness=2,
            padx=10,
            pady=6,
        )
        self.outer.pack(fill="both", expand=True)

        self.dot_lbl = tk.Label(
            self.outer,
            text="OFF",
            bg="#0A0714",
            fg=DANGER_RED,
            font=("Consolas", 16, "bold"),
            cursor="fleur",
        )
        self.dot_lbl.pack()

        self.sub_lbl = tk.Label(
            self.outer,
            text=f"KEY: {self.app.activation_key}",
            bg="#0A0714",
            fg=TEXT_MUTED,
            font=("Consolas", 8, "bold"),
            cursor="fleur",
        )
        self.sub_lbl.pack()

        for widget in (self.win, self.outer, self.dot_lbl, self.sub_lbl):
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._on_drag)
            widget.bind("<ButtonRelease-1>", self._end_drag)

        self.apply_scale(self.scale)
        self.update_state(False)

    def _start_drag(self, event):
        self._drag_offset_x = event.x_root - self.win.winfo_x()
        self._drag_offset_y = event.y_root - self.win.winfo_y()

    def _on_drag(self, event):
        new_x = event.x_root - self._drag_offset_x
        new_y = event.y_root - self._drag_offset_y
        self.win.geometry(f"+{new_x}+{new_y}")

    def _end_drag(self, event):
        self.app.hud_x = self.win.winfo_x()
        self.app.hud_y = self.win.winfo_y()
        self.app.save_config()

    def apply_scale(self, scale):
        self.scale = max(0.8, min(2.5, float(scale)))
        main_size = max(12, int(round(16 * self.scale)))
        sub_size = max(7, int(round(8 * self.scale)))
        pad_x = max(8, int(round(12 * self.scale)))
        pad_y = max(4, int(round(6 * self.scale)))
        self.outer.config(padx=pad_x, pady=pad_y)
        self.dot_lbl.config(font=("Consolas", main_size, "bold"))
        self.sub_lbl.config(font=("Consolas", sub_size, "bold"))

    def update_state(self, active: bool):
        self.sub_lbl.config(text=f"KEY: {self.app.activation_key}")
        if active:
            self.outer.config(bg="#06291E", highlightbackground=NEON_GREEN, highlightthickness=2)
            self.dot_lbl.config(text="ON", bg="#06291E", fg=NEON_GREEN)
            self.sub_lbl.config(text=f"ACTIVE [{self.app.activation_key}]", bg="#06291E", fg=NEON_GREEN)
        else:
            self.outer.config(bg="#1E0710", highlightbackground=DANGER_RED, highlightthickness=2)
            self.dot_lbl.config(text="OFF", bg="#1E0710", fg=DANGER_RED)
            self.sub_lbl.config(text=f"STOPPED [{self.app.activation_key}]", bg="#1E0710", fg=TEXT_MUTED)

    def show(self):
        self.win.deiconify()
        self.win.attributes("-topmost", True)

    def hide(self):
        self.win.withdraw()


class SpeedAutoClickerPro:
    def __init__(self, root):
        self.root = root
        self.root.title("auto clicker fahad pro")
        self.root.geometry("540x735")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_MAIN)

        self.saved_cfg = self.load_config()

        # Core State Variables
        self.activation_key = self.saved_cfg.get("activation_key", "T")
        self.listening_for_key = False
        self.is_clicking = False
        self._last_cue_time = 0.0
        self._cue_lock = threading.Lock()
        self.click_count = 0
        self.session_start_time = None
        self.session_elapsed = 0.0
        self.hud_x = int(self.saved_cfg.get("hud_x", 40))
        self.hud_y = int(self.saved_cfg.get("hud_y", 40))

        # UI Variables (loaded from saved config)
        self.mode_var = tk.StringVar(value=self.saved_cfg.get("mode", "toggle"))
        self.button_var = tk.StringVar(value=self.saved_cfg.get("button", "left"))
        self.cps_var = tk.StringVar(value=str(self.saved_cfg.get("cps", "270.0")))
        self.unlimited_var = tk.BooleanVar(value=self.saved_cfg.get("unlimited", False))
        self.random_var = tk.BooleanVar(value=self.saved_cfg.get("random", False))
        self.duty_var = tk.DoubleVar(value=float(self.saved_cfg.get("duty", 50.0)))
        self.limit_enable_var = tk.BooleanVar(value=self.saved_cfg.get("limit_enable", False))
        self.max_clicks_var = tk.StringVar(value=str(self.saved_cfg.get("max_clicks", "20000")))
        self.autostart_var = tk.BooleanVar(value=self.saved_cfg.get("autostart", False))
        self.usage_var = tk.BooleanVar(value=self.saved_cfg.get("usage", True))
        self.audio_cue_var = tk.BooleanVar(value=self.saved_cfg.get("audio_cue", True))
        self.hud_enable_var = tk.BooleanVar(value=self.saved_cfg.get("hud_enable", True))
        self.hud_scale_var = tk.DoubleVar(value=float(self.saved_cfg.get("hud_scale", 1.3)))
        self.lang_var = tk.StringVar(value="en")

        self.setup_styles()
        self.build_ui()
        self.hud = ScreenHudOverlay(self, x=self.hud_x, y=self.hud_y, scale=self.hud_scale_var.get())
        if not self.hud_enable_var.get():
            self.hud.hide()

        self.toggle_unlimited()
        self.toggle_limit()
        self.update_timing_label()
        self.draw_mouse()

        # Auto-save whenever any setting changes
        for var in (self.mode_var, self.button_var, self.cps_var, self.unlimited_var,
                    self.random_var, self.limit_enable_var, self.max_clicks_var,
                    self.autostart_var, self.usage_var, self.audio_cue_var,
                    self.hud_enable_var, self.hud_scale_var):
            var.trace_add("write", lambda *args: self.save_config())

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Background keyboard listener
        self.kb_listener = keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release)
        self.kb_listener.start()

        # Click execution thread
        self.click_thread = threading.Thread(target=self.click_loop, daemon=True)
        self.click_thread.start()
        self.root.after(250, self.refresh_timer_label)

    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
        except Exception:
            pass
        return {}

    def save_config(self):
        try:
            hud_x = self.hud.win.winfo_x() if hasattr(self, "hud") else self.hud_x
            hud_y = self.hud.win.winfo_y() if hasattr(self, "hud") else self.hud_y
            data = {
                "activation_key": self.activation_key,
                "mode": self.mode_var.get(),
                "button": self.button_var.get(),
                "cps": self.cps_var.get(),
                "unlimited": bool(self.unlimited_var.get()),
                "random": bool(self.random_var.get()),
                "duty": float(self.duty_var.get()),
                "limit_enable": bool(self.limit_enable_var.get()),
                "max_clicks": self.max_clicks_var.get(),
                "autostart": bool(self.autostart_var.get()),
                "usage": bool(self.usage_var.get()),
                "audio_cue": bool(self.audio_cue_var.get()),
                "hud_enable": bool(self.hud_enable_var.get()),
                "hud_scale": float(self.hud_scale_var.get()),
                "hud_x": int(hud_x),
                "hud_y": int(hud_y),
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def on_close(self):
        self.save_config()
        self.root.destroy()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox",
                        fieldbackground=BG_INPUT,
                        background=BG_INPUT,
                        foreground=NEON_CYAN,
                        arrowcolor=NEON_PURPLE,
                        bordercolor=BORDER_VIOLET,
                        darkcolor=BG_INPUT,
                        lightcolor=BG_INPUT)

    def validate_numeric(self, new_val, allow_decimal="0"):
        """Strictly allow only ASCII digits (0-9) and optional single decimal point."""
        if new_val == "":
            return True
        allowed = "0123456789." if allow_decimal == "1" else "0123456789"
        if any(ch not in allowed for ch in new_val):
            return False
        if allow_decimal == "1" and new_val.count(".") > 1:
            return False
        return True

    def style_button(self, btn, bg_color, fg_color, hover_bg, hover_fg=None, padx=10, pady=5):
        if hover_fg is None:
            hover_fg = fg_color
        btn.config(
            bg=bg_color,
            fg=fg_color,
            activebackground=hover_bg,
            activeforeground=hover_fg,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=padx,
            pady=pady,
        )
        btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg, fg=hover_fg))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg_color, fg=fg_color))
        return btn

    def create_card(self, parent, title):
        wrapper = tk.Frame(parent, bg=BG_MAIN)
        wrapper.pack(fill="x", padx=16, pady=5)

        header = tk.Label(wrapper, text=title.upper(), bg=BG_MAIN, fg=NEON_PURPLE,
                          font=("Segoe UI", 8, "bold"))
        header.pack(anchor="w", padx=4, pady=(0, 2))

        card = tk.Frame(wrapper, bg=BG_CARD, highlightbackground=BORDER_VIOLET,
                        highlightthickness=1, padx=14, pady=10)
        card.pack(fill="x")
        return card

    def build_ui(self):
        vcmd_int = (self.root.register(self.validate_numeric), "%P", "0")
        vcmd_float = (self.root.register(self.validate_numeric), "%P", "1")

        # ================= Top Header =================
        top_header = tk.Frame(self.root, bg=BG_CARD, pady=10, padx=16)
        top_header.pack(fill="x")

        title_left = tk.Frame(top_header, bg=BG_CARD)
        title_left.pack(side="left")
        tk.Label(title_left, text="AUTO CLICKER FAHAD", bg=BG_CARD, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 12, "bold")).pack(side="left")
        tk.Label(title_left, text=" PRO", bg=BG_CARD, fg=NEON_PURPLE,
                 font=("Segoe UI", 12, "bold")).pack(side="left")

        self.status_badge = tk.Label(top_header, text="IDLE", bg=BG_INPUT, fg=TEXT_MUTED,
                                     font=("Segoe UI", 9, "bold"), padx=12, pady=3,
                                     highlightbackground=BORDER_SOFT, highlightthickness=1)
        self.status_badge.pack(side="right")

        grad_line = tk.Canvas(self.root, height=3, bg=BG_MAIN, highlightthickness=0)
        grad_line.pack(fill="x")
        grad_line.create_rectangle(0, 0, 270, 3, fill="#7C3AED", outline="")
        grad_line.create_rectangle(270, 0, 540, 3, fill="#0284C7", outline="")

        # ================= 1. Activation =================
        act_card = self.create_card(self.root, "Activation")

        row1 = tk.Frame(act_card, bg=BG_CARD)
        row1.pack(fill="x", pady=(0, 8))

        tk.Label(row1, text="Activation Key:", bg=BG_CARD, fg=TEXT_PRIMARY, font=("Segoe UI", 9)).pack(side="left")

        self.key_display = tk.Label(row1, text=f"{self.activation_key}", bg="#07050E", fg=NEON_PURPLE,
                                    width=16, height=1, font=("Segoe UI", 11, "bold"),
                                    highlightbackground=BORDER_VIOLET, highlightthickness=1)
        self.key_display.pack(side="left", padx=15)

        self.select_btn = tk.Button(row1, text="SELECT KEY", width=14,
                                    font=("Segoe UI", 9, "bold"), command=self.start_key_bind)
        self.style_button(self.select_btn, "#7C3AED", "#FFFFFF", "#8B5CF6", "#FFFFFF", padx=10, pady=4)
        self.select_btn.pack(side="right")

        row2 = tk.Frame(act_card, bg=BG_CARD)
        row2.pack(fill="x")

        tk.Label(row2, text="Activation Mode:", bg=BG_CARD, fg=TEXT_PRIMARY, font=("Segoe UI", 9)).pack(side="left")

        radio_style = {"bg": BG_CARD, "fg": TEXT_PRIMARY, "selectcolor": BG_INPUT,
                       "activebackground": BG_CARD, "activeforeground": NEON_GREEN,
                       "font": ("Segoe UI", 9, "bold"), "cursor": "hand2"}

        tk.Radiobutton(row2, text="Hold", variable=self.mode_var, value="hold", **radio_style).pack(side="left", padx=(18, 10))
        tk.Radiobutton(row2, text="Toggle", variable=self.mode_var, value="toggle", **radio_style).pack(side="left", padx=10)

        choose_btn = tk.Button(row2, text="CHOOSE APPS", width=14,
                               font=("Segoe UI", 8, "bold"),
                               highlightbackground=BORDER_VIOLET, highlightthickness=1,
                               command=self.choose_apps_info)
        self.style_button(choose_btn, BG_INPUT, NEON_CYAN, "#182236", TEXT_PRIMARY, padx=10, pady=4)
        choose_btn.pack(side="right")

        # ================= 2. Mouse Button Selection =================
        clicks_card = self.create_card(self.root, "Mouse Button Selection")

        mid_frame = tk.Frame(clicks_card, bg=BG_CARD)
        mid_frame.pack()
        tk.Radiobutton(mid_frame, text="Middle Button (Scroll Wheel)", variable=self.button_var,
                       value="middle", command=self.draw_mouse, **radio_style).pack()
        tk.Label(mid_frame, text="MButton", bg=BG_CARD, fg=NEON_CYAN, font=("Segoe UI", 8, "bold")).pack()

        center_row = tk.Frame(clicks_card, bg=BG_CARD)
        center_row.pack(fill="x", pady=4)

        left_frame = tk.Frame(center_row, bg=BG_CARD)
        left_frame.pack(side="left", expand=True)
        tk.Radiobutton(left_frame, text="Left Button", variable=self.button_var,
                       value="left", command=self.draw_mouse, **radio_style).pack()
        tk.Label(left_frame, text="LButton", bg=BG_CARD, fg=NEON_CYAN, font=("Segoe UI", 8, "bold")).pack()

        self.mouse_canvas = tk.Canvas(center_row, width=100, height=120, bg=BG_CARD, highlightthickness=0)
        self.mouse_canvas.pack(side="left", padx=10)

        right_frame = tk.Frame(center_row, bg=BG_CARD)
        right_frame.pack(side="left", expand=True)
        tk.Radiobutton(right_frame, text="Right Button", variable=self.button_var,
                       value="right", command=self.draw_mouse, **radio_style).pack()
        tk.Label(right_frame, text="RButton", bg=BG_CARD, fg=NEON_CYAN, font=("Segoe UI", 8, "bold")).pack()

        # ================= 3. Clicks & Risk Check + Click Limit =================
        split_wrapper = tk.Frame(self.root, bg=BG_MAIN)
        split_wrapper.pack(fill="x", padx=16, pady=5)

        # Left card: Click Count & Risk Check
        left_col = tk.Frame(split_wrapper, bg=BG_MAIN)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 6))
        tk.Label(left_col, text="CLICKS & RISK CHECK", bg=BG_MAIN, fg=NEON_PURPLE, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=4, pady=(0, 2))
        rate_card = tk.Frame(left_col, bg=BG_CARD, highlightbackground=BORDER_VIOLET, highlightthickness=1, padx=12, pady=10)
        rate_card.pack(fill="both", expand=True)

        spin_style = {"bg": BG_INPUT, "fg": NEON_CYAN, "buttonbackground": BORDER_SOFT,
                      "insertbackground": NEON_CYAN, "relief": "flat", "font": ("Segoe UI", 10, "bold")}

        chk_style = {"bg": BG_CARD, "fg": TEXT_PRIMARY, "selectcolor": BG_INPUT,
                     "activebackground": BG_CARD, "activeforeground": NEON_GREEN,
                     "font": ("Segoe UI", 9), "cursor": "hand2"}

        c_row = tk.Frame(rate_card, bg=BG_CARD)
        c_row.pack(fill="x", pady=(0, 4))
        tk.Label(c_row, text="Clicks:", bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 9, "bold")).pack(side="left")
        self.clicks_counter_lbl = tk.Label(c_row, text="0", bg=BG_INPUT, fg=NEON_CYAN,
                                           font=("Consolas", 11, "bold"), padx=10, pady=2,
                                           highlightbackground=BORDER_SOFT, highlightthickness=1)
        self.clicks_counter_lbl.pack(side="right")

        click_state_row = tk.Frame(rate_card, bg=BG_CARD)
        click_state_row.pack(fill="x", pady=2)
        tk.Label(click_state_row, text="Clicking:", bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 9, "bold")).pack(side="left")
        self.click_state_lbl = tk.Label(click_state_row, text="OFF", bg=BG_INPUT, fg=TEXT_MUTED,
                                        font=("Segoe UI", 9, "bold"), padx=10, pady=2,
                                        highlightbackground=BORDER_SOFT, highlightthickness=1)
        self.click_state_lbl.pack(side="right")

        risk_row = tk.Frame(rate_card, bg=BG_CARD)
        risk_row.pack(fill="x", pady=2)
        tk.Label(risk_row, text="Status:", bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 9, "bold")).pack(side="left")
        self.risk_badge_lbl = tk.Label(risk_row, text="SAFE", bg="#06291E", fg=NEON_GREEN,
                                       font=("Segoe UI", 9, "bold"), padx=10, pady=2,
                                       highlightbackground=NEON_GREEN, highlightthickness=1)
        self.risk_badge_lbl.pack(side="right")

        timer_row = tk.Frame(rate_card, bg=BG_CARD)
        timer_row.pack(fill="x", pady=2)
        tk.Label(timer_row, text="Timer:", bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 9, "bold")).pack(side="left")
        self.session_timer_lbl = tk.Label(timer_row, text="00:00", bg=BG_INPUT, fg=NEON_PURPLE,
                                          font=("Consolas", 10, "bold"), padx=10, pady=1,
                                          highlightbackground=BORDER_SOFT, highlightthickness=1)
        self.session_timer_lbl.pack(side="right")

        s_row = tk.Frame(rate_card, bg=BG_CARD)
        s_row.pack(fill="x", pady=(6, 0))

        self.toggle_action_btn = tk.Button(
            s_row,
            text="START",
            font=("Segoe UI", 8, "bold"),
            highlightbackground=NEON_GREEN,
            highlightthickness=1,
            command=lambda: self.set_clicking_state(not self.is_clicking),
        )
        self.style_button(self.toggle_action_btn, "#06291E", NEON_GREEN, "#0B3B2C", "#FFFFFF", padx=8, pady=4)
        self.toggle_action_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        reset_cnt_btn = tk.Button(
            s_row,
            text="RESET",
            font=("Segoe UI", 8, "bold"),
            highlightbackground=BORDER_SOFT,
            highlightthickness=1,
            command=self.reset_click_counter,
        )
        self.style_button(reset_cnt_btn, BG_INPUT, GOLD, "#1A2234", "#FDE047", padx=8, pady=4)
        reset_cnt_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))

        # Right card: Click Limit & Screen HUD Size
        right_col = tk.Frame(split_wrapper, bg=BG_MAIN)
        right_col.pack(side="left", fill="both", expand=True, padx=(6, 0))
        tk.Label(right_col, text="CLICK LIMIT & HUD", bg=BG_MAIN, fg=NEON_PURPLE, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=4, pady=(0, 2))
        limit_card = tk.Frame(right_col, bg=BG_CARD, highlightbackground=BORDER_VIOLET, highlightthickness=1, padx=12, pady=10)
        limit_card.pack(fill="both", expand=True)

        tk.Checkbutton(limit_card, text="Enable Click Limit", variable=self.limit_enable_var,
                       command=self.toggle_limit, **chk_style).pack(anchor="w")

        l2 = tk.Frame(limit_card, bg=BG_CARD)
        l2.pack(fill="x", pady=5)
        self.max_lbl = tk.Label(l2, text="Max:", bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 9))
        self.max_lbl.pack(side="left")
        self.max_spin = tk.Spinbox(l2, from_=1, to=1000000, textvariable=self.max_clicks_var,
                                   width=8, validate="key", validatecommand=vcmd_int,
                                   state="disabled", disabledbackground="#090712", **spin_style)
        self.max_spin.pack(side="left", padx=6)
        self.clicks_lbl = tk.Label(l2, text="Clicks", bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 9))
        self.clicks_lbl.pack(side="left")

        tk.Checkbutton(limit_card, text="Show Screen HUD", variable=self.hud_enable_var,
                       command=self.toggle_hud, **chk_style).pack(anchor="w", pady=(2, 2))

        hud_size_row = tk.Frame(limit_card, bg=BG_CARD)
        hud_size_row.pack(fill="x")
        tk.Label(hud_size_row, text="HUD Size:", bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 8, "bold")).pack(side="left")
        self.hud_scale_slider = tk.Scale(
            hud_size_row,
            from_=0.8,
            to=2.4,
            resolution=0.1,
            orient="horizontal",
            variable=self.hud_scale_var,
            bg=BG_CARD,
            fg=NEON_CYAN,
            highlightthickness=0,
            troughcolor=BG_INPUT,
            activebackground=NEON_PURPLE,
            sliderlength=12,
            length=105,
            command=lambda val: self.hud.apply_scale(float(val)) if hasattr(self, "hud") else None,
        )
        self.hud_scale_slider.pack(side="right")

        self.timing_label = tk.Label(limit_card, text="Click / Wait: 1851.9 us / 1851.9 us",
                                     bg=BG_CARD, fg=NEON_CYAN, font=("Consolas", 8, "bold"))
        self.timing_label.pack(anchor="w", pady=(4, 0))

        # ================= 4. System & Misc =================
        misc_card = self.create_card(self.root, "System & Misc")

        m_left = tk.Frame(misc_card, bg=BG_CARD)
        m_left.pack(side="left", fill="y")
        tk.Checkbutton(m_left, text="Autostart with Windows", variable=self.autostart_var, **chk_style).pack(anchor="w", pady=2)
        tk.Checkbutton(m_left, text="Send anonymous usage data", variable=self.usage_var, **chk_style).pack(anchor="w", pady=2)
        tk.Checkbutton(m_left, text="Beep Cue", variable=self.audio_cue_var, **chk_style).pack(anchor="w", pady=2)

        m_right = tk.Frame(misc_card, bg=BG_CARD)
        m_right.pack(side="right")
        lang_box = ttk.Combobox(m_right, textvariable=self.lang_var, values=["en"], width=16, state="readonly")
        lang_box.pack(pady=(0, 8))
        reset_set_btn = tk.Button(
            m_right,
            text="RESET SETTINGS",
            width=18,
            font=("Segoe UI", 8, "bold"),
            highlightbackground=BORDER_VIOLET,
            highlightthickness=1,
            command=self.reset_settings,
        )
        self.style_button(reset_set_btn, BG_INPUT, GOLD, "#1A2234", "#FDE047", padx=10, pady=5)
        reset_set_btn.pack()

        # ================= 5. Bottom Bar =================
        bottom_bar = tk.Frame(self.root, bg=BG_MAIN)
        bottom_bar.pack(fill="x", padx=16, pady=(8, 12))

        tk.Label(bottom_bar, text="Drag HUD Anywhere Over Game | Auto-Save ON", bg=BG_MAIN, fg=NEON_PURPLE,
                 font=("Segoe UI", 8, "bold")).pack(side="left")

        exit_btn = tk.Button(
            bottom_bar,
            text="EXIT",
            width=11,
            font=("Segoe UI", 9, "bold"),
            command=self.on_close,
        )
        self.style_button(exit_btn, DANGER_RED, "#FFFFFF", "#F43F5E", "#FFFFFF", padx=10, pady=5)
        exit_btn.pack(side="right", padx=(8, 0))

        min_btn = tk.Button(
            bottom_bar,
            text="MINIMIZE",
            width=11,
            font=("Segoe UI", 9, "bold"),
            highlightbackground=BORDER_SOFT,
            highlightthickness=1,
            command=self.minimize_to_taskbar,
        )
        self.style_button(min_btn, BG_INPUT, TEXT_PRIMARY, "#1B2438", NEON_CYAN, padx=10, pady=5)
        min_btn.pack(side="right")

    def toggle_hud(self):
        if not hasattr(self, "hud"):
            return
        if self.hud_enable_var.get():
            self.hud.show()
            self.hud.update_state(self.is_clicking)
        else:
            self.hud.hide()

    def draw_mouse(self):
        self.mouse_canvas.delete("all")
        btn = self.button_var.get()
        left_color = DANGER_RED if btn == "left" else "#161229"
        right_color = DANGER_RED if btn == "right" else "#161229"
        mid_color = NEON_GREEN if btn == "middle" else NEON_PURPLE

        self.mouse_canvas.create_oval(15, 6, 85, 114, fill="#0F0B1E", outline=BORDER_VIOLET, width=2)
        self.mouse_canvas.create_arc(15, 6, 85, 78, start=90, extent=90, fill=left_color, outline=BORDER_VIOLET, width=2)
        self.mouse_canvas.create_arc(15, 6, 85, 78, start=0, extent=90, fill=right_color, outline=BORDER_VIOLET, width=2)
        self.mouse_canvas.create_oval(45, 16, 55, 38, fill=mid_color, outline=BG_MAIN, width=1.5)

    def measure_ui_lag_ms(self):
        t0 = time.perf_counter()
        self.root.update_idletasks()
        return (time.perf_counter() - t0) * 1000.0

    def evaluate_risk(self, cps=None, count=None):
        if cps is None:
            try:
                cps = float(self.cps_var.get())
            except Exception:
                cps = 100.0
        if count is None:
            count = self.click_count

        lag_ms = 0.0
        try:
            lag_ms = self.measure_ui_lag_ms()
        except Exception:
            lag_ms = 0.0

        is_risk = self.unlimited_var.get() or (cps > 350.0) or (lag_ms > 80.0)
        if hasattr(self, "risk_badge_lbl"):
            if is_risk:
                self.risk_badge_lbl.config(
                    text="RISK", fg=DANGER_RED, bg="#2A0914", highlightbackground=DANGER_RED
                )
            else:
                self.risk_badge_lbl.config(
                    text="SAFE", fg=NEON_GREEN, bg="#06291E", highlightbackground=NEON_GREEN
                )

    def reset_click_counter(self):
        self.click_count = 0
        self.session_elapsed = 0.0
        if self.is_clicking:
            self.session_start_time = time.perf_counter()
        if hasattr(self, "clicks_counter_lbl"):
            self.clicks_counter_lbl.config(text="0")
        if hasattr(self, "session_timer_lbl"):
            self.session_timer_lbl.config(text="00:00")
        self.evaluate_risk(count=0)

    def update_timing_label(self):
        try:
            cps = float(self.cps_var.get())
            duty = float(self.duty_var.get())
            if cps <= 0:
                cps = 1.0
            total_us = 1_000_000.0 / cps
            click_us = total_us * (duty / 100.0)
            wait_us = total_us - click_us
            self.timing_label.config(text=f"Click / Wait: {click_us:.1f} us / {wait_us:.1f} us")
            self.evaluate_risk(cps=cps)
        except ValueError:
            pass

    def toggle_unlimited(self):
        if hasattr(self, "cps_spin"):
            state = "disabled" if self.unlimited_var.get() else "normal"
            self.cps_spin.config(state=state)
        if self.unlimited_var.get():
            self.timing_label.config(text="Click / Wait: MAX UNLIMITED")
            self.evaluate_risk()
        else:
            self.update_timing_label()

    def toggle_limit(self):
        if self.limit_enable_var.get():
            self.max_spin.config(state="normal")
            self.max_lbl.config(fg=TEXT_PRIMARY)
            self.clicks_lbl.config(fg=TEXT_PRIMARY)
        else:
            self.max_spin.config(state="disabled")
            self.max_lbl.config(fg=TEXT_MUTED)
            self.clicks_lbl.config(fg=TEXT_MUTED)

    def start_key_bind(self):
        self.listening_for_key = True
        self.key_display.config(text="PRESS KEY...", fg=GOLD, highlightbackground=GOLD)

    def normalize_key(self, key):
        try:
            if hasattr(key, 'char') and key.char is not None:
                ch = key.char
                if ch in LAYOUT_TO_EN_MAP:
                    return LAYOUT_TO_EN_MAP[ch]
                if len(ch) == 1 and 1 <= ord(ch) <= 26:
                    return chr(ord(ch) + 64)
                if ch.isascii():
                    return ch.upper()
        except Exception:
            pass

        if hasattr(key, 'vk') and key.vk is not None:
            vk = key.vk
            if 65 <= vk <= 90:
                return chr(vk)
            if 48 <= vk <= 57:
                return chr(vk)

        raw = str(key).replace("Key.", "").upper()
        return raw if raw.isascii() else "T"

    def on_key_press(self, key):
        k_name = self.normalize_key(key)
        if self.listening_for_key:
            self.activation_key = k_name
            self.listening_for_key = False
            self.save_config()
            self.root.after(0, lambda: (
                self.key_display.config(
                    text=f"{self.activation_key}", fg=NEON_PURPLE, highlightbackground=BORDER_VIOLET),
                self.hud.update_state(self.is_clicking) if hasattr(self, "hud") else None
            ))
            return

        if k_name == self.activation_key:
            now = time.perf_counter()
            if hasattr(self, "_last_toggle_time") and (now - self._last_toggle_time) < 0.12:
                return
            self._last_toggle_time = now

            if self.mode_var.get() == "toggle":
                self.set_clicking_state(not self.is_clicking)
            elif self.mode_var.get() == "hold":
                self.set_clicking_state(True)

    def on_key_release(self, key):
        if self.mode_var.get() == "hold":
            k_name = self.normalize_key(key)
            if k_name == self.activation_key:
                self.set_clicking_state(False)

    def play_audio_cue(self, started: bool):
        if not self.audio_cue_var.get() or winsound is None:
            return
        now = time.perf_counter()
        with self._cue_lock:
            if (now - self._last_cue_time) < 0.35:
                return
            self._last_cue_time = now

        freq = 850 if started else 500

        def _beep():
            try:
                winsound.Beep(freq, 65)
            except Exception:
                pass

        threading.Thread(target=_beep, daemon=True).start()

    def format_duration(self, seconds: float) -> str:
        total = max(0, int(seconds))
        hrs = total // 3600
        mins = (total % 3600) // 60
        secs = total % 60
        if hrs > 0:
            return f"{hrs:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    def refresh_timer_label(self):
        if not hasattr(self, "session_timer_lbl"):
            return
        elapsed = self.session_elapsed
        if self.is_clicking and self.session_start_time is not None:
            elapsed += time.perf_counter() - self.session_start_time
        self.session_timer_lbl.config(text=self.format_duration(elapsed))
        self.root.after(250, self.refresh_timer_label)

    def set_clicking_state(self, active: bool):
        if active == self.is_clicking:
            return
        now = time.perf_counter()
        if active:
            self.is_clicking = True
            self.click_count = 0
            self.session_start_time = now
            self.play_audio_cue(True)
        else:
            if self.is_clicking and self.session_start_time is not None:
                self.session_elapsed += now - self.session_start_time
            self.is_clicking = False
            self.session_start_time = None
            self.play_audio_cue(False)
        self.update_status()

    def update_status(self):
        if self.is_clicking:
            self.root.after(0, lambda: (
                self.status_badge.config(
                    text="RUNNING", fg=NEON_GREEN, bg="#06291E", highlightbackground=NEON_GREEN),
                self.click_state_lbl.config(
                    text="CLICKING ON", fg=NEON_GREEN, bg="#06291E", highlightbackground=NEON_GREEN),
                self.toggle_action_btn.config(
                    text="STOP", fg="#FFFFFF", bg=DANGER_RED,
                    activebackground="#F43F5E", activeforeground="#FFFFFF",
                    highlightbackground=DANGER_RED) if hasattr(self, "toggle_action_btn") else None,
                self.hud.update_state(True) if hasattr(self, "hud") else None
            ))
        else:
            self.root.after(0, lambda: (
                self.status_badge.config(
                    text="IDLE", fg=TEXT_MUTED, bg=BG_INPUT, highlightbackground=BORDER_SOFT),
                self.click_state_lbl.config(
                    text="CLICKING OFF", fg=DANGER_RED, bg="#2A0914", highlightbackground=DANGER_RED),
                self.toggle_action_btn.config(
                    text="START", fg=NEON_GREEN, bg="#06291E",
                    activebackground="#0B3B2C", activeforeground="#FFFFFF",
                    highlightbackground=NEON_GREEN) if hasattr(self, "toggle_action_btn") else None,
                self.hud.update_state(False) if hasattr(self, "hud") else None
            ))

    def send_click(self, down_flag, up_flag, hold_time):
        ctypes.windll.user32.mouse_event(down_flag, 0, 0, 0, 0)
        if hold_time > 0:
            self.precise_sleep(hold_time)
        ctypes.windll.user32.mouse_event(up_flag, 0, 0, 0, 0)

    def precise_sleep(self, duration):
        end = time.perf_counter() + duration
        while time.perf_counter() < end:
            if duration > 0.002:
                time.sleep(0.001)

    def click_loop(self):
        while True:
            if self.is_clicking:
                btn = self.button_var.get()
                if btn == "left":
                    down, up = MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP
                elif btn == "right":
                    down, up = MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP
                else:
                    down, up = MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP

                if self.unlimited_var.get():
                    self.send_click(down, up, 0)
                    self.click_count += 1
                    time.sleep(0.0001)
                else:
                    try:
                        cps = max(0.1, float(self.cps_var.get()))
                        duty = max(1.0, min(99.0, float(self.duty_var.get()))) / 100.0
                    except ValueError:
                        cps, duty = 10.0, 0.5

                    if self.random_var.get():
                        cps *= random.uniform(0.8, 1.2)

                    period = 1.0 / cps
                    hold_t = period * duty
                    wait_t = period - hold_t

                    self.send_click(down, up, hold_t)
                    self.click_count += 1
                    if self.click_count % 5 == 0 or self.click_count <= 20:
                        c_val = self.click_count
                        self.root.after(0, lambda v=c_val: (
                            self.clicks_counter_lbl.config(text=f"{v:,}"),
                            self.evaluate_risk(count=v)
                        ))
                    self.precise_sleep(wait_t)
            else:
                time.sleep(0.01)

    def reset_settings(self):
        self.activation_key = "T"
        self.key_display.config(text="T", fg=NEON_PURPLE, highlightbackground=BORDER_VIOLET)
        self.mode_var.set("toggle")
        self.button_var.set("left")
        self.cps_var.set("270.0")
        self.unlimited_var.set(False)
        self.random_var.set(False)
        self.duty_var.set(50.00)
        self.limit_enable_var.set(False)
        self.max_clicks_var.set("20000")
        self.hud_enable_var.set(True)
        self.hud_scale_var.set(1.3)
        self.audio_cue_var.set(True)
        self.reset_click_counter()
        self.toggle_unlimited()
        self.toggle_limit()
        self.toggle_hud()
        if hasattr(self, "hud"):
            self.hud.apply_scale(1.3)
            self.hud.update_state(self.is_clicking)
        self.draw_mouse()
        self.update_timing_label()
        self.save_config()

    def choose_apps_info(self):
        messagebox.showinfo("Choose Apps", "Running globally across all active windows.")

    def minimize_to_taskbar(self):
        self.root.iconify()


if __name__ == "__main__":
    root = tk.Tk()
    app = SpeedAutoClickerPro(root)
    root.mainloop()
