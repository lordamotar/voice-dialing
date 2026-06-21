import tkinter as tk
import math
import logging

logger = logging.getLogger(__name__)

class RecordingOverlay:
    def __init__(self, root, hotkey_str: str = "ctrl+space"):
        self.root = root
        self.hotkey_str = hotkey_str
        self.pulse_phase = 0
        self.animating = False
        
        # Configure root window
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        
        # Windows-specific transparency key
        # Using a rare color code #000001 for transparent background key
        self.trans_color = "#000001"
        self.root.configure(bg=self.trans_color)
        self.root.wm_attributes("-transparentcolor", self.trans_color)
        
        # Size and position: top center of the screen
        screen_width = self.root.winfo_screenwidth()
        self.width = 380
        self.height = 64
        x = (screen_width - self.width) // 2
        y = 40  # 40px down from screen top
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        # Canvas covering the entire root window
        self.canvas = tk.Canvas(
            self.root, 
            width=self.width, 
            height=self.height, 
            bg=self.trans_color, 
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Format hotkey instruction label
        hotkey_display = hotkey_str.replace("+", " + ").upper()
        subtext = f"Отпустите {hotkey_display} для ввода"
        
        # Draw dynamic island style rounded pill background
        # Color: #18181B (deep slate gray), Border: #F43F5E (vibrant coral rose)
        self.bg_pill = self.draw_rounded_rect(
            self.canvas, 
            2, 2, 
            self.width - 2, 
            self.height - 2, 
            20, 
            fill="#18181B", 
            outline="#F43F5E", 
            width=1.5
        )
        
        # Pulsing recording glow circle
        self.glow = self.canvas.create_oval(
            20, 17, 
            44, 41, 
            fill="", 
            outline="#F43F5E", 
            width=2
        )
        
        # Central recording dot
        self.indicator = self.canvas.create_oval(
            25, 22, 
            39, 36, 
            fill="#F43F5E", 
            outline=""
        )
        
        # Sleek white/light typography
        self.canvas.create_text(
            65, 22,
            text="🎙️ ИДЕТ ЗАПИСЬ...",
            fill="#F8FAFC",
            font=("Segoe UI", 11, "bold"),
            anchor="w"
        )
        
        self.canvas.create_text(
            65, 41,
            text=subtext,
            fill="#94A3B8",
            font=("Segoe UI", 9),
            anchor="w"
        )
        
        # Hide window by default on startup
        self.root.withdraw()
        logger.info("Графический оверлей успешно создан.")
        
    def draw_rounded_rect(self, canvas, x1, y1, x2, y2, r, **kwargs):
        """Draw a smooth rounded polygon to simulate a rounded rectangle."""
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1
        ]
        return canvas.create_polygon(points, **kwargs, smooth=True)

    def show(self):
        """Make overlay visible and start indicator animation thread-safely."""
        def _show():
            self.root.deiconify()
            self.animating = True
            self.animate()
        self.root.after(0, _show)
        
    def hide(self):
        """Hide overlay and stop indicator animation thread-safely."""
        def _hide():
            self.animating = False
            self.root.withdraw()
        self.root.after(0, _hide)
        
    def animate(self):
        """Perform micro-pulse animation frame."""
        if not self.animating:
            return
        
        self.pulse_phase += 0.12
        pulse_val = (math.sin(self.pulse_phase) + 1) / 2
        
        r_base = 8
        r_glow = r_base + int(pulse_val * 9)
        cx, cy = 32, 29
        
        try:
            self.canvas.coords(
                self.glow, 
                cx - r_glow, 
                cy - r_glow, 
                cx + r_glow, 
                cy + r_glow
            )
            
            # Fade colors by interpolating between background (#18181B) and pulse (#F43F5E)
            bg_rgb = (0x18, 0x18, 0x1B)
            glow_rgb = (0xF4, 0x3F, 0x5E)
            
            interpolated = tuple(
                int(bg_rgb[i] + (glow_rgb[i] - bg_rgb[i]) * (1 - pulse_val)) for i in range(3)
            )
            glow_color = "#%02x%02x%02x" % interpolated
            
            self.canvas.itemconfig(self.glow, outline=glow_color)
            self.root.after(30, self.animate)
        except Exception:
            pass
