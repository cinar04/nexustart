"""config.py — Ayarlar, DataManager, i18n, stil yardımcıları | NexusStart v3.0"""
import os, json, time
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame, QPushButton, QMenu
from PyQt6.QtGui import QColor, QFont, QPixmap
from PyQt6.QtCore import Qt

APP_DIR       = Path(os.environ["APPDATA"]) / "NexusStart"
DATA_FILE     = APP_DIR / "data.json"
SETTINGS_FILE = APP_DIR / "settings.json"
SHORTCUTS_DIR = APP_DIR / "shortcuts"
ICONS_DIR     = APP_DIR / "icons"
BACKUP_DIR    = APP_DIR / "backups"
MENU_W, MENU_H = 760, 920

LANGS = {
    "tr": {
        "search_placeholder": "Uygulama, dosya ara...",
        "pinned": "SABİTLENDİ", "all_apps": "TÜM UYGULAMALAR",
        "recommended": "ÖNERİLEN", "favorites": "FAVORİLER",
        "all_apps_btn": "Tüm Uygulamalar  →", "back": "←  Geri",
        "settings": "HIZLI AYARLAR", "tools": "ARAÇLAR",
        "no_recent": "Uygulamaları çalıştırdıkça burada görünür.",
        "files": "DOSYALAR",
        "greet_morning": "Günaydın", "greet_afternoon": "İyi öğleden sonralar",
        "greet_evening": "İyi akşamlar", "greet_night": "İyi geceler",
    },
    "en": {
        "search_placeholder": "Search apps, files...",
        "pinned": "PINNED", "all_apps": "ALL APPS",
        "recommended": "RECOMMENDED", "favorites": "FAVORITES",
        "all_apps_btn": "All Applications  →", "back": "←  Back",
        "settings": "QUICK SETTINGS", "tools": "TOOLS",
        "no_recent": "Recently used apps will appear here.",
        "files": "FILES",
        "greet_morning": "Good morning", "greet_afternoon": "Good afternoon",
        "greet_evening": "Good evening", "greet_night": "Good night",
    },
}

DEFAULT_SETTINGS = {
    "led_color": "#00aaff", "led_color2": "#006aff", "bg_opacity": 92,
    "weather_city": "Istanbul", "weather_unit": "metric",
    "show_cpu": True, "show_weather": True, "show_music": True,
    "neon_glow": False, "night_sky": False, "open_anim": True,
    "language": "tr", "icon_size": "medium",
    "focus_mode": False, "dnd_mode": False, "auto_hide": True,
    "saved_palettes": [], "hotkey_vk": 0x20, "hotkey_mod": 0x0002,
    "update_check": True, "last_update_check": 0, "app_version": "3.0",
}


class Settings:
    def __init__(self):
        for d in (APP_DIR, SHORTCUTS_DIR, ICONS_DIR, BACKUP_DIR):
            d.mkdir(parents=True, exist_ok=True)
        self._d = dict(DEFAULT_SETTINGS)
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    self._d.update(json.load(f))
            except Exception: pass

    def save(self):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self._d, f, indent=2, ensure_ascii=False)

    def export_backup(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = BACKUP_DIR / f"settings_{ts}.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(self._d, f, indent=2, ensure_ascii=False)
        return str(out)

    def import_backup(self, path):
        with open(path, "r", encoding="utf-8") as f:
            self._d.update(json.load(f))
        self.save()

    def __getitem__(self, k):    return self._d.get(k, DEFAULT_SETTINGS.get(k))
    def __setitem__(self, k, v): self._d[k] = v
    def get(self, k, default=None): return self._d.get(k, default)


cfg = Settings()


def tr(key):
    return LANGS.get(cfg["language"], LANGS["tr"]).get(key, key)


class DataManager:
    def __init__(self):
        self.data = {
            "recent": [], "pins": [], "folders": {}, "notes": "",
            "todos": [], "clipboard": [], "aliases": {}, "tags": {},
            "favorites": [], "search_history": [], "app_stats": {},
        }
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.data.update(json.load(f))
            except Exception: pass

    def save(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def record_launch(self, path, name, icon_path=""):
        for it in self.data["recent"]:
            if it["path"].lower() == path.lower():
                it["last_used"] = time.time()
                it["use_count"] = it.get("use_count", 0) + 1
                self.save(); return
        self.data["recent"].insert(0, {"path": path, "name": name,
            "icon_path": icon_path, "last_used": time.time(), "use_count": 1})
        self.data["recent"] = self.data["recent"][:50]
        key = name.lower(); st = self.data["app_stats"]
        if key not in st: st[key] = {"launches": 0, "today": 0, "last_date": ""}
        today = datetime.now().strftime("%Y-%m-%d")
        if st[key]["last_date"] != today: st[key]["today"] = 0; st[key]["last_date"] = today
        st[key]["launches"] += 1; st[key]["today"] += 1
        self.save()

    def get_recent(self, n=6):
        return sorted(self.data["recent"], key=lambda x: x.get("last_used", 0), reverse=True)[:n]

    def get_pins(self):        return self.data.get("pins", [])
    def is_pinned(self, path): return any(p["path"].lower()==path.lower() for p in self.data["pins"])
    def pin_app(self, path, name, icon_path=""):
        if not self.is_pinned(path):
            self.data["pins"].append({"path":path,"name":name,"icon_path":icon_path}); self.save()
    def unpin_app(self, path):
        self.data["pins"] = [p for p in self.data["pins"] if p["path"].lower()!=path.lower()]; self.save()

    def get_favorites(self): return self.data.get("favorites", [])
    def add_favorite(self, app):
        if not any(f["path"].lower()==app["path"].lower() for f in self.data["favorites"]):
            self.data["favorites"].append(app); self.save()
    def remove_favorite(self, path):
        self.data["favorites"] = [f for f in self.data["favorites"] if f["path"].lower()!=path.lower()]; self.save()

    def add_clipboard(self, text):
        h = self.data["clipboard"]
        if text in h: h.remove(text)
        h.insert(0, text); self.data["clipboard"] = h[:30]; self.save()

    def add_search_history(self, q):
        h = self.data["search_history"]
        if q in h: h.remove(q)
        h.insert(0, q); self.data["search_history"] = h[:20]; self.save()

    def set_alias(self, path, alias): self.data["aliases"][path.lower()] = alias; self.save()
    def get_alias(self, path): return self.data["aliases"].get(path.lower(), "")
    def set_tag(self, path, tag): self.data["tags"][path.lower()] = tag; self.save()
    def get_tag(self, path): return self.data["tags"].get(path.lower(), "")


dm = DataManager()

# ── Stil yardımcıları ──────────────────────────────────────────────────────────
BASE_QSS = """
QScrollBar:vertical{background:transparent;width:4px;}
QScrollBar::handle:vertical{background:rgba(0,170,255,0.3);border-radius:2px;min-height:20px;}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}
QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{background:none;}
QToolTip{background:#080d1a;color:#e8f4ff;border:1px solid rgba(0,170,255,0.4);border-radius:6px;padding:4px 8px;}
"""

def _rgba(hex_color, a=1.0):
    c = QColor(hex_color); return f"rgba({c.red()},{c.green()},{c.blue()},{a})"
def led(a=1.0):  return _rgba(cfg["led_color"], a)
def led2(a=1.0): return _rgba(cfg["led_color2"], a)

def _section(text):
    w = QWidget(); w.setFixedHeight(22)
    lay = QHBoxLayout(w); lay.setContentsMargins(0,0,0,0); lay.setSpacing(8)
    lbl = QLabel(text); lbl.setFont(QFont("Orbitron",7,QFont.Weight.Bold))
    lbl.setStyleSheet(f"color:{led(0.75)};letter-spacing:2px;")
    ln = QFrame(); ln.setFrameShape(QFrame.Shape.HLine); ln.setStyleSheet(f"color:{led(0.1)};")
    lay.addWidget(lbl); lay.addWidget(ln); return w

def _icon_btn(text, tooltip="", danger=False):
    btn = QPushButton(text); btn.setFixedSize(34,34); btn.setToolTip(tooltip)
    hbg  = "rgba(255,40,40,0.12)" if danger else led(0.1)
    hbrd = "rgba(255,40,40,0.35)" if danger else led(0.3)
    hcol = "#ff4444"              if danger else cfg["led_color"]
    btn.setStyleSheet(f"QPushButton{{background:transparent;border:1px solid transparent;"
        f"border-radius:8px;color:rgba(200,220,255,0.5);font-size:15px;}}"
        f"QPushButton:hover{{background:{hbg};border:1px solid {hbrd};color:{hcol};}}")
    return btn

def _styled_menu(parent):
    m = QMenu(parent)
    m.setStyleSheet(f"QMenu{{background:#080d1a;border:1px solid {led(0.3)};border-radius:10px;"
        f"padding:6px;color:#e8f4ff;font-family:'Rajdhani','Segoe UI';font-size:13px;font-weight:500;}}"
        f"QMenu::item{{padding:7px 18px 7px 12px;border-radius:6px;}}"
        f"QMenu::item:selected{{background:{led(0.12)};color:{cfg['led_color']};}}")
    return m

def _icon_label(app, sz=40):
    ic = QLabel(); ic.setFixedSize(sz,sz); ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
    ic.setStyleSheet(f"border-radius:10px;"
        f"background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #0d1a35,stop:1 #0a1428);"
        f"border:1px solid {led(0.2)};font-size:{sz//2}px;")
    ip = app.get("icon_path","")
    if ip and Path(ip).exists():
        pm = QPixmap(ip).scaled(sz-8,sz-8,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
        ic.setPixmap(pm)
    else:
        alias = dm.get_alias(app.get("path",""))
        nm = alias if alias else app["name"]
        ic.setText(nm[0].upper()); ic.setFont(QFont("Orbitron",sz//3,QFont.Weight.Bold))
        ic.setStyleSheet(ic.styleSheet()+f"color:{cfg['led_color']};")
    return ic

def _greet():
    h = datetime.now().hour
    if 5<=h<12: return tr("greet_morning")
    if 12<=h<17: return tr("greet_afternoon")
    if 17<=h<21: return tr("greet_evening")
    return tr("greet_night")

def _btn_qss():
    return (f"QPushButton{{background:{led(0.07)};border:1px solid {led(0.25)};"
            f"border-radius:8px;padding:0 12px;color:#e8f4ff;font-family:'Rajdhani';font-size:12px;}}"
            f"QPushButton:hover{{background:{led(0.16)};}}")

def _inp_qss():
    return (f"QLineEdit,QComboBox{{background:{led(0.06)};border:1px solid {led(0.25)};"
            f"border-radius:8px;padding:0 10px;color:#e8f4ff;font-family:'Rajdhani';font-size:12px;}}"
            f"QLineEdit:focus,QComboBox:focus{{border-color:{led(0.55)};}}"
            f"QComboBox::drop-down{{border:none;}}"
            f"QComboBox QAbstractItemView{{background:#080d1a;color:#e8f4ff;selection-background-color:{led(0.2)};}}")

def _chk_style(cb):
    cb.setFont(QFont("Rajdhani",11))
    cb.setStyleSheet(f"QCheckBox{{color:#e8f4ff;spacing:6px;}}"
        f"QCheckBox::indicator{{width:14px;height:14px;border-radius:3px;border:1px solid {led(0.35)};background:transparent;}}"
        f"QCheckBox::indicator:checked{{background:{cfg['led_color']};border-color:{cfg['led_color']};}}")
