"""
widgets.py — Özellik widget'leri | NexusStart v3.0

İçerik:
  TopPanel          — CPU/RAM + Hava + Müzik
  AppTile           — Uygulama kutucuğu (bounce + pin starburst)
  RecentRow         — Son kullanılanlar satırı
  NotesWidget       — Hızlı notlar
  TodoWidget        — Yapılacaklar listesi
  PomodoroWidget    — Pomodoro zamanlayıcı
  CountdownWidget   — Geri sayım
  ClipboardWidget   — Pano geçmişi
  CalculatorWidget  — Hesap makinesi
  UnitConverterWidget  — Birim dönüştürücü
  CurrencyWidget    — Para birimi dönüştürücü
  QRWidget          — QR kod üreteci
  PasswordWidget    — Şifre üreteci
  MultiClockWidget  — Çoklu saat dilimi
  CalendarWidget    — Mini aylık takvim
  WebSearchWidget   — Web arama + URL aç
  EmojiSearchWidget — Emoji arama
  ColorPickerWidget — Renk toplayıcı + palet kaydet
  FolderGroupWidget — Klasör grupları
  TerminalWidget    — Terminal başlatıcı + sistem butonları
"""

import subprocess, random, string, math, time, urllib.parse
from pathlib import Path
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QGraphicsDropShadowEffect,
    QTextEdit, QComboBox, QCheckBox, QSpinBox, QApplication, QColorDialog,
    QFileDialog,
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QByteArray
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen, QImage, QPixmap

try:
    import qrcode as _qrcode_mod; HAS_QR = True
except ImportError:
    HAS_QR = False

import win32api, win32con


def _lazy():
    """Deferred import — config must be initialised first."""
    from config import cfg, dm, led, led2, _rgba, _section, _icon_btn, _styled_menu, _icon_label, _btn_qss, _inp_qss, _chk_style
    return cfg, dm, led, led2, _rgba, _section, _icon_btn, _styled_menu, _icon_label, _btn_qss, _inp_qss, _chk_style


# ─────────────────────────────────────────────────────────────────────────────
# TOP PANEL
# ─────────────────────────────────────────────────────────────────────────────
class TopPanel(QWidget):
    def __init__(self):
        super().__init__(); self.setFixedHeight(95)
        from animations import MusicBarsWidget
        self._bars = MusicBarsWidget()
        lay = QHBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(8)
        self._cpu_w = self._mk_cpu()
        self._wx_w  = self._mk_wx()
        self._mus_w = self._mk_mus()
        lay.addWidget(self._cpu_w, 2); lay.addWidget(self._wx_w, 2); lay.addWidget(self._mus_w, 3)

    def _card(self):
        cfg = _lazy()[0]
        from config import led
        w = QWidget()
        w.setStyleSheet(f"background:rgba(10,16,32,0.85);border-radius:12px;border:1px solid {led(0.15)};")
        return w

    def _mk_cpu(self):
        from config import led, led2
        w = self._card(); lay = QVBoxLayout(w); lay.setContentsMargins(10,8,10,8); lay.setSpacing(2)
        t = QLabel("SİSTEM"); t.setFont(QFont("Orbitron",7,QFont.Weight.Bold))
        t.setStyleSheet(f"color:{led(0.7)};letter-spacing:2px;")
        self.cpu_bar = self._bar(); self.ram_bar = self._bar()
        self.cpu_lbl = QLabel("CPU 0%"); self.ram_lbl = QLabel("RAM 0%")
        self.disk_lbl = QLabel("Disk —"); self.net_lbl = QLabel("Net —")
        self.bat_lbl = QLabel("")
        for lb in (self.cpu_lbl, self.ram_lbl, self.disk_lbl, self.net_lbl, self.bat_lbl):
            lb.setFont(QFont("Rajdhani",9)); lb.setStyleSheet("color:rgba(200,220,255,0.65);")
        lay.addWidget(t)
        for label, bar, lbl in [("CPU",self.cpu_bar,self.cpu_lbl),("RAM",self.ram_bar,self.ram_lbl)]:
            row = QHBoxLayout(); row.setSpacing(4)
            l = QLabel(label); l.setFont(QFont("Rajdhani",9))
            l.setStyleSheet("color:rgba(200,220,255,0.4);"); l.setFixedWidth(24)
            row.addWidget(l); row.addWidget(bar, 1); row.addWidget(lbl)
            lay.addLayout(row)
        row2 = QHBoxLayout(); row2.setSpacing(6)
        row2.addWidget(self.disk_lbl); row2.addWidget(self.net_lbl); row2.addWidget(self.bat_lbl)
        lay.addLayout(row2)
        return w

    def _bar(self):
        from config import led
        b = QFrame(); b.setFixedHeight(4)
        b.setStyleSheet(f"background:{led(0.12)};border-radius:2px;"); return b

    def update_sys(self, cpu, ram):
        from config import led, led2
        self.cpu_lbl.setText(f"{int(cpu)}%"); self.ram_lbl.setText(f"{int(ram)}%")
        for bar, val, color in [(self.cpu_bar,cpu,led),(self.ram_bar,ram,led2)]:
            v = max(0.01, val/100)
            bar.setStyleSheet(f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                f"stop:0 {color(0.9)},stop:{v:.2f} {color(0.9)},"
                f"stop:{min(1.0,v+0.001):.3f} {color(0.1)},stop:1 {color(0.08)});"
                f"border-radius:2px;")

    def update_disk_net(self, info):
        dp = info.get("disk_pct", 0); df = info.get("disk_free_gb", 0)
        self.disk_lbl.setText(f"💾{dp:.0f}%({df:.1f}G)")
        dk = info.get("net_down_kb", 0); uk = info.get("net_up_kb", 0)
        def fmt(kb): return f"{kb/1024:.1f}M/s" if kb>1024 else f"{kb:.0f}K/s"
        self.net_lbl.setText(f"↓{fmt(dk)}↑{fmt(uk)}")
        bp = info.get("battery_pct", -1)
        if bp >= 0:
            plug = "🔌" if info.get("battery_plug") else "🔋"
            self.bat_lbl.setText(f"{plug}{bp:.0f}%")

    def _mk_wx(self):
        from config import led, cfg
        w = self._card(); lay = QVBoxLayout(w); lay.setContentsMargins(10,8,10,8); lay.setSpacing(2)
        t = QLabel("HAVA"); t.setFont(QFont("Orbitron",7,QFont.Weight.Bold))
        t.setStyleSheet(f"color:{led(0.7)};letter-spacing:2px;")
        self.wx_main = QLabel("..."); self.wx_main.setFont(QFont("Rajdhani",20,QFont.Weight.Bold))
        self.wx_main.setStyleSheet(f"color:{cfg['led_color']};")
        self.wx_sub = QLabel(cfg["weather_city"]); self.wx_sub.setFont(QFont("Rajdhani",10))
        self.wx_sub.setStyleSheet("color:rgba(200,220,255,0.5);")
        self.wx_extra = QLabel(""); self.wx_extra.setFont(QFont("Rajdhani",9))
        self.wx_extra.setStyleSheet("color:rgba(200,220,255,0.35);")
        self.wx_sun = QLabel(""); self.wx_sun.setFont(QFont("Rajdhani",9))
        self.wx_sun.setStyleSheet("color:rgba(255,200,80,0.7);")
        lay.addWidget(t); lay.addWidget(self.wx_main)
        lay.addWidget(self.wx_sub); lay.addWidget(self.wx_extra); lay.addWidget(self.wx_sun)
        return w

    def update_weather(self, info):
        from config import cfg
        if not info.get("ok"):
            self.wx_main.setText("—"); self.wx_sub.setText("Bağlanamadı"); return
        self.wx_main.setText(f"{info['emoji']} {info['temp']}")
        self.wx_sub.setText(f"{info['city']} · {info['desc']}")
        self.wx_extra.setText(f"Nem %{info['humidity']}  Rüzgar {info['wind']}km/s")
        sun = info.get("sunrise",""); sus = info.get("sunset","")
        if sun and sus: self.wx_sun.setText(f"🌅{sun}  🌇{sus}")

    def _mk_mus(self):
        from config import led, cfg
        from animations import MusicBarsWidget
        w = self._card(); lay = QVBoxLayout(w); lay.setContentsMargins(10,8,10,8); lay.setSpacing(4)
        t = QLabel("MÜZİK"); t.setFont(QFont("Orbitron",7,QFont.Weight.Bold))
        t.setStyleSheet(f"color:{led(0.7)};letter-spacing:2px;")
        self.mus_title = QLabel("Çalmıyor"); self.mus_title.setFont(QFont("Rajdhani",12,QFont.Weight.Medium))
        self.mus_artist = QLabel(""); self.mus_artist.setFont(QFont("Rajdhani",10))
        self.mus_artist.setStyleSheet("color:rgba(200,220,255,0.45);")
        for lb in (self.mus_title, self.mus_artist): lb.setMaximumWidth(220)
        bar_row = QHBoxLayout(); bar_row.setSpacing(6)
        bar_row.addWidget(self._bars); bar_row.addStretch()
        ctrl = QHBoxLayout(); ctrl.setSpacing(5)
        self.b_prev = self._cbtn("⏮"); self.b_play = self._cbtn("⏯"); self.b_next = self._cbtn("⏭")
        self.b_prev.clicked.connect(lambda: self._mk(win32con.VK_MEDIA_PREV_TRACK))
        self.b_play.clicked.connect(lambda: self._mk(win32con.VK_MEDIA_PLAY_PAUSE))
        self.b_next.clicked.connect(lambda: self._mk(win32con.VK_MEDIA_NEXT_TRACK))
        ctrl.addWidget(self.b_prev); ctrl.addWidget(self.b_play); ctrl.addWidget(self.b_next); ctrl.addStretch()
        lay.addWidget(t); lay.addLayout(bar_row)
        lay.addWidget(self.mus_title); lay.addWidget(self.mus_artist); lay.addLayout(ctrl)
        return w

    def _cbtn(self, txt):
        from config import led, cfg
        b = QPushButton(txt); b.setFixedSize(26,26)
        b.setStyleSheet(f"QPushButton{{background:{led(0.08)};border:1px solid {led(0.2)};"
            f"border-radius:7px;color:#e8f4ff;font-size:12px;}}"
            f"QPushButton:hover{{background:{led(0.2)};color:{cfg['led_color']};}}")
        return b

    def _mk(self, vk):
        win32api.keybd_event(vk, 0, 0, 0); win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)

    def update_music(self, info):
        playing = info.get("playing") and info.get("title")
        self._bars.set_playing(bool(playing))
        if playing:
            self.mus_title.setText(self.mus_title.fontMetrics().elidedText(
                info["title"], Qt.TextElideMode.ElideRight, 215))
            self.mus_artist.setText(self.mus_artist.fontMetrics().elidedText(
                info.get("artist",""), Qt.TextElideMode.ElideRight, 215))
        else:
            self.mus_title.setText("Çalmıyor"); self.mus_artist.setText("")


# ─────────────────────────────────────────────────────────────────────────────
# APP TILE
# ─────────────────────────────────────────────────────────────────────────────
class AppTile(QWidget):
    from PyQt6.QtCore import pyqtSignal
    clicked    = pyqtSignal(dict)
    pin_toggle = pyqtSignal(dict)
    kill_sig   = pyqtSignal(dict)

    def __init__(self, app, cols=6):
        super().__init__()
        from config import cfg, dm, led, _icon_label, _styled_menu, MENU_W
        from animations import StarBurstOverlay
        self.app = app
        sz_map = {"small":70,"medium":86,"large":102}
        tile_h = sz_map.get(cfg["icon_size"], 86)
        ic_sz  = {"small":30,"medium":40,"large":50}.get(cfg["icon_size"], 40)
        w = max(80, (MENU_W-52)//cols-4)
        self.setFixedSize(w, tile_h)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QVBoxLayout(self); lay.setContentsMargins(4,8,4,6); lay.setSpacing(5)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ic = _icon_label(app, ic_sz)
        self.nm = QLabel()
        fm = QFont("Rajdhani",10,QFont.Weight.Medium); self.nm.setFont(fm)
        self.nm.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nm.setStyleSheet("color:rgba(232,244,255,0.85);")
        disp = dm.get_alias(app.get("path","")) or app["name"]
        self.nm.setText(QFontMetrics(fm).elidedText(disp, Qt.TextElideMode.ElideRight, w-10))
        lay.addWidget(self.ic, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.nm, alignment=Qt.AlignmentFlag.AlignCenter)
        tag = app.get("tag","")
        if tag:
            tb = QLabel(f"#{tag}"); tb.setFont(QFont("Rajdhani",8))
            tb.setStyleSheet(f"color:{led(0.8)};"); tb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(tb, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border-radius:12px;border:1px solid transparent;")
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._ctx)
        self._star = StarBurstOverlay(self); self._star.hide()

    def enterEvent(self, e):
        from config import cfg, led
        glow_r = 28 if cfg.get("neon_glow") else 16
        self.setStyleSheet(f"border-radius:12px;background:{led(0.09)};border:1px solid {led(0.28)};")
        eff = QGraphicsDropShadowEffect()
        eff.setColor(QColor(cfg["led_color"])); eff.setBlurRadius(glow_r); eff.setOffset(0,0)
        self.setGraphicsEffect(eff)

    def leaveEvent(self, e):
        self.setStyleSheet("border-radius:12px;border:1px solid transparent;")
        self.setGraphicsEffect(None)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._bounce(); self.clicked.emit(self.app)

    def _bounce(self):
        anim = QPropertyAnimation(self, QByteArray(b"geometry"))
        anim.setDuration(200)
        g = self.geometry()
        shrunk = g.adjusted(3, 3, -3, -3)
        anim.setKeyValueAt(0, g); anim.setKeyValueAt(0.5, shrunk); anim.setKeyValueAt(1, g)
        anim.setEasingCurve(QEasingCurve.Type.OutBounce)
        self._ba = anim; anim.start()

    def _ctx(self, pos):
        from config import dm, _styled_menu
        m = _styled_menu(self)
        pinned = dm.is_pinned(self.app["path"])
        fav = any(f["path"].lower()==self.app["path"].lower() for f in dm.get_favorites())
        m.addAction("📌  Sabitlemeden Kaldır" if pinned else "📌  Sabitle").triggered.connect(self._do_pin)
        m.addAction("⭐  Favorilerden Çıkar" if fav else "⭐  Favorilere Ekle").triggered.connect(
            lambda: dm.remove_favorite(self.app["path"]) if fav else dm.add_favorite(self.app))
        m.addAction("▶  Aç").triggered.connect(lambda: self.clicked.emit(self.app))
        m.addSeparator()
        m.addAction("✕  Görevi Sonlandır").triggered.connect(lambda: self.kill_sig.emit(self.app))
        m.addAction("📂  Konumu Aç").triggered.connect(
            lambda: subprocess.Popen(f'explorer /select,"{self.app["path"]}"'))
        m.exec(self.mapToGlobal(pos))

    def _do_pin(self):
        self._star.burst(self.width()//2, self.height()//2)
        self.pin_toggle.emit(self.app)


# ─────────────────────────────────────────────────────────────────────────────
# RECENT ROW
# ─────────────────────────────────────────────────────────────────────────────
class RecentRow(QWidget):
    from PyQt6.QtCore import pyqtSignal
    clicked = pyqtSignal(dict)

    def __init__(self, app):
        super().__init__(); self.app = app
        from config import led, dm, _icon_label
        self.setFixedHeight(48); self.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QHBoxLayout(self); lay.setContentsMargins(10,4,10,4); lay.setSpacing(10)
        ic = _icon_label(app, 32)
        info = QVBoxLayout(); info.setSpacing(1)
        n = QLabel(app["name"]); n.setFont(QFont("Rajdhani",12,QFont.Weight.Medium))
        stats = dm.data["app_stats"].get(app["name"].lower(), {})
        cnt = stats.get("today", 0)
        ago = self._ago(app.get("last_used",0))
        if cnt > 0: ago += f"  ·  bugün {cnt}x"
        t = QLabel(ago); t.setFont(QFont("Rajdhani",10))
        t.setStyleSheet("color:rgba(200,220,255,0.4);")
        info.addWidget(n); info.addWidget(t)
        lay.addWidget(ic); lay.addLayout(info); lay.addStretch()
        self.setStyleSheet("border-radius:10px;border:1px solid transparent;")

    def _ago(self, ts):
        if not ts: return "—"
        d = time.time()-ts
        if d<60:    return "Az önce"
        if d<3600:  return f"{int(d//60)} dk önce"
        if d<86400: return f"{int(d//3600)} saat önce"
        return f"{int(d//86400)} gün önce"

    def enterEvent(self, e):
        from config import led
        self.setStyleSheet(f"border-radius:10px;background:{led(0.07)};border:1px solid {led(0.2)};")
    def leaveEvent(self, e):
        self.setStyleSheet("border-radius:10px;border:1px solid transparent;")
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton: self.clicked.emit(self.app)


# ─────────────────────────────────────────────────────────────────────────────
# NOTES
# ─────────────────────────────────────────────────────────────────────────────
class NotesWidget(QWidget):
    def __init__(self):
        super().__init__()
        from config import led, dm
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(6)
        self.edit = QTextEdit()
        self.edit.setPlaceholderText("Hızlı notlar buraya...")
        self.edit.setFont(QFont("Rajdhani",12))
        self.edit.setStyleSheet(f"QTextEdit{{background:{led(0.05)};border:1px solid {led(0.2)};"
            f"border-radius:10px;padding:8px;color:#e8f4ff;}}")
        self.edit.setText(dm.data.get("notes",""))
        self.edit.textChanged.connect(self._save)
        lay.addWidget(self.edit)

    def _save(self):
        from config import dm
        dm.data["notes"] = self.edit.toPlainText(); dm.save()


# ─────────────────────────────────────────────────────────────────────────────
# TODO
# ─────────────────────────────────────────────────────────────────────────────
class TodoWidget(QWidget):
    def __init__(self):
        super().__init__()
        from config import led
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(6)
        row = QHBoxLayout(); row.setSpacing(6)
        self.inp = QLineEdit(); self.inp.setPlaceholderText("Yeni görev...")
        self.inp.setFixedHeight(30)
        self.inp.setStyleSheet(f"QLineEdit{{background:{led(0.06)};border:1px solid {led(0.22)};"
            f"border-radius:8px;padding:0 8px;color:#e8f4ff;font-family:'Rajdhani';font-size:12px;}}"
            f"QLineEdit:focus{{border-color:{led(0.5)};}}")
        add = QPushButton("+"); add.setFixedSize(30,30)
        add.setStyleSheet(f"QPushButton{{background:{led(0.06)};border:1px solid {led(0.22)};"
            f"border-radius:8px;color:#e8f4ff;font-size:16px;}}"
            f"QPushButton:hover{{background:{led(0.15)};}}")
        add.clicked.connect(self._add); self.inp.returnPressed.connect(self._add)
        row.addWidget(self.inp,1); row.addWidget(add)
        lay.addLayout(row)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background:transparent;border:none;")
        self.scroll.setMaximumHeight(180)
        self.lw = QWidget(); self.ll = QVBoxLayout(self.lw)
        self.ll.setContentsMargins(0,0,0,0); self.ll.setSpacing(3)
        self.scroll.setWidget(self.lw); lay.addWidget(self.scroll)
        self._refresh()

    def _add(self):
        from config import dm
        text = self.inp.text().strip()
        if not text: return
        dm.data["todos"].append({"text":text,"done":False}); dm.save()
        self.inp.clear(); self._refresh()

    def _refresh(self):
        from config import dm, led, cfg
        while self.ll.count():
            it = self.ll.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        for i, todo in enumerate(dm.data.get("todos",[])):
            row = QWidget(); rl = QHBoxLayout(row); rl.setContentsMargins(4,2,4,2); rl.setSpacing(8)
            cb = QCheckBox(); cb.setChecked(todo.get("done",False))
            cb.setStyleSheet(f"QCheckBox::indicator{{width:14px;height:14px;border-radius:3px;"
                f"border:1px solid {led(0.35)};background:transparent;}}"
                f"QCheckBox::indicator:checked{{background:{cfg['led_color']};}}")
            cb.toggled.connect(lambda c, j=i: self._toggle(j, c))
            lbl = QLabel(todo["text"]); lbl.setFont(QFont("Rajdhani",11))
            color = "color:rgba(200,220,255,0.35);text-decoration:line-through;" if todo.get("done") else "color:#e8f4ff;"
            lbl.setStyleSheet(color)
            dl = QPushButton("✕"); dl.setFixedSize(18,18)
            dl.setStyleSheet("color:rgba(255,80,80,0.6);background:transparent;border:none;font-size:10px;")
            dl.clicked.connect(lambda _, j=i: self._delete(j))
            rl.addWidget(cb); rl.addWidget(lbl,1); rl.addWidget(dl)
            self.ll.addWidget(row)
        self.ll.addStretch()

    def _toggle(self, i, c):
        from config import dm
        if i < len(dm.data["todos"]): dm.data["todos"][i]["done"] = c; dm.save(); self._refresh()
    def _delete(self, i):
        from config import dm
        if i < len(dm.data["todos"]): dm.data["todos"].pop(i); dm.save(); self._refresh()


# ─────────────────────────────────────────────────────────────────────────────
# POMODORO
# ─────────────────────────────────────────────────────────────────────────────
class PomodoroWidget(QWidget):
    def __init__(self):
        super().__init__()
        from config import led, cfg
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(8)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._work=25; self._break=5; self._rem=25*60; self._is_work=True; self._running=False
        self.phase = QLabel("ÇALIŞMA"); self.phase.setFont(QFont("Orbitron",8,QFont.Weight.Bold))
        self.phase.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.phase.setStyleSheet(f"color:{led(0.6)};letter-spacing:2px;")
        self.display = QLabel(self._fmt(self._rem))
        self.display.setFont(QFont("Orbitron",28,QFont.Weight.Bold))
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display.setStyleSheet(f"color:{cfg['led_color']};")
        qss = (f"QPushButton{{background:{led(0.08)};border:1px solid {led(0.25)};"
               f"border-radius:8px;color:#e8f4ff;font-family:'Rajdhani';font-size:12px;}}"
               f"QPushButton:hover{{background:{led(0.18)};}}")
        row = QHBoxLayout(); row.setSpacing(8)
        self.btn_s = QPushButton("▶ Başlat"); self.btn_s.setFixedHeight(30)
        self.btn_s.setStyleSheet(qss); self.btn_s.clicked.connect(self._toggle)
        btn_r = QPushButton("↺ Sıfırla"); btn_r.setFixedHeight(30)
        btn_r.setStyleSheet(qss); btn_r.clicked.connect(self._reset)
        row.addWidget(self.btn_s); row.addWidget(btn_r)
        lay.addWidget(self.phase); lay.addWidget(self.display); lay.addLayout(row)
        self._t = QTimer(self); self._t.timeout.connect(self._tick)

    def _toggle(self):
        self._running = not self._running
        self.btn_s.setText("⏸ Duraklat" if self._running else "▶ Devam")
        if self._running: self._t.start(1000)
        else: self._t.stop()

    def _reset(self):
        self._t.stop(); self._running=False; self._is_work=True; self._rem=self._work*60
        self.display.setText(self._fmt(self._rem)); self.phase.setText("ÇALIŞMA")
        self.btn_s.setText("▶ Başlat")

    def _tick(self):
        self._rem -= 1
        if self._rem <= 0:
            self._is_work = not self._is_work
            self._rem = (self._work if self._is_work else self._break)*60
            self.phase.setText("ÇALIŞMA" if self._is_work else "MOLA")
            QApplication.beep()
        self.display.setText(self._fmt(self._rem))

    def _fmt(self, s): return f"{s//60:02d}:{s%60:02d}"


# ─────────────────────────────────────────────────────────────────────────────
# COUNTDOWN
# ─────────────────────────────────────────────────────────────────────────────
class CountdownWidget(QWidget):
    def __init__(self):
        super().__init__()
        from config import led, cfg
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(6)
        self.display = QLabel("-- gün --:--:--")
        self.display.setFont(QFont("Rajdhani",15,QFont.Weight.Bold))
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display.setStyleSheet(f"color:{cfg['led_color']};")
        row = QHBoxLayout(); row.setSpacing(6)
        self.inp = QLineEdit(); self.inp.setPlaceholderText("Tarih: 2026-12-31")
        self.inp.setFixedHeight(30)
        self.inp.setStyleSheet(f"QLineEdit{{background:{led(0.06)};border:1px solid {led(0.22)};"
            f"border-radius:8px;padding:0 8px;color:#e8f4ff;font-family:'Rajdhani';font-size:12px;}}")
        go = QPushButton("→"); go.setFixedSize(30,30)
        go.setStyleSheet(f"QPushButton{{background:{led(0.08)};border:1px solid {led(0.25)};"
            f"border-radius:8px;color:#e8f4ff;}}"
            f"QPushButton:hover{{background:{led(0.18)};}}")
        go.clicked.connect(self._start); self.inp.returnPressed.connect(self._start)
        row.addWidget(self.inp,1); row.addWidget(go)
        lay.addWidget(self.display); lay.addLayout(row)
        self._target = None
        self._t = QTimer(self); self._t.timeout.connect(self._tick); self._t.start(1000)

    def _start(self):
        try:
            self._target = datetime.strptime(self.inp.text().strip(), "%Y-%m-%d")
            self._tick()
        except ValueError:
            self.display.setText("Geçersiz tarih")

    def _tick(self):
        if not self._target: return
        diff = self._target - datetime.now()
        if diff.total_seconds() <= 0: self.display.setText("🎉 Geldi!"); return
        h = diff.seconds//3600; m=(diff.seconds%3600)//60; s=diff.seconds%60
        self.display.setText(f"{diff.days}g {h:02d}:{m:02d}:{s:02d}")


# ─────────────────────────────────────────────────────────────────────────────
# CLIPBOARD
# ─────────────────────────────────────────────────────────────────────────────
class ClipboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        from config import led, cfg, dm
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(4)
        hdr = QHBoxLayout()
        clr = QPushButton("Temizle"); clr.setFixedHeight(22)
        clr.setStyleSheet(f"QPushButton{{background:transparent;border:1px solid {led(0.2)};"
            f"border-radius:6px;color:rgba(200,220,255,0.5);font-size:11px;padding:0 8px;}}"
            f"QPushButton:hover{{background:{led(0.1)};color:{cfg['led_color']};}}")
        clr.clicked.connect(self._clear)
        hdr.addStretch(); hdr.addWidget(clr)
        lay.addLayout(hdr)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background:transparent;border:none;"); self.scroll.setMaximumHeight(200)
        self.lw = QWidget(); self.ll = QVBoxLayout(self.lw)
        self.ll.setContentsMargins(0,0,0,0); self.ll.setSpacing(3)
        self.scroll.setWidget(self.lw); lay.addWidget(self.scroll)
        self._refresh()

    def add_item(self, text):
        from config import dm
        dm.add_clipboard(text); self._refresh()

    def _clear(self):
        from config import dm
        dm.data["clipboard"] = []; dm.save(); self._refresh()

    def _refresh(self):
        from config import dm, led, cfg
        while self.ll.count():
            it = self.ll.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        for item in dm.data.get("clipboard",[])[:25]:
            row = QWidget(); rl = QHBoxLayout(row); rl.setContentsMargins(6,3,6,3)
            lbl = QLabel(item[:55] + ("…" if len(item)>55 else ""))
            lbl.setFont(QFont("Rajdhani",10)); lbl.setStyleSheet("color:rgba(200,220,255,0.8);")
            cp = QPushButton("⎘"); cp.setFixedSize(22,22)
            cp.setStyleSheet(f"QPushButton{{background:transparent;border:none;color:{led(0.7)};font-size:12px;}}"
                f"QPushButton:hover{{color:{cfg['led_color']};background:{led(0.08)};border-radius:4px;}}")
            txt = item; cp.clicked.connect(lambda _, x=txt: QApplication.clipboard().setText(x))
            rl.addWidget(lbl,1); rl.addWidget(cp)
            row.setStyleSheet(f"background:{led(0.04)};border-radius:6px;")
            self.ll.addWidget(row)
        self.ll.addStretch()


# ─────────────────────────────────────────────────────────────────────────────
# CALCULATOR
# ─────────────────────────────────────────────────────────────────────────────
class CalculatorWidget(QWidget):
    def __init__(self):
        super().__init__()
        from config import led, cfg
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(6)
        self.display = QLineEdit("0")
        self.display.setFont(QFont("Rajdhani",20,QFont.Weight.Bold))
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setReadOnly(True); self.display.setFixedHeight(44)
        self.display.setStyleSheet(f"QLineEdit{{background:{led(0.06)};border:1px solid {led(0.2)};"
            f"border-radius:10px;padding:0 12px;color:{cfg['led_color']};}}")
        qss = (f"QPushButton{{background:{led(0.07)};border:1px solid {led(0.18)};"
               f"border-radius:8px;color:#e8f4ff;font-family:'Rajdhani';font-size:14px;font-weight:600;}}"
               f"QPushButton:hover{{background:{led(0.18)};color:{cfg['led_color']};}}")
        grid = QGridLayout(); grid.setSpacing(4)
        buttons = [["C","±","%","÷"],["7","8","9","×"],["4","5","6","−"],["1","2","3","+"],["0",".","=","="]]
        self._expr = ""
        for r, row in enumerate(buttons):
            for c, label in enumerate(row):
                if label == "=" and c == 3 and r == 4: continue
                btn = QPushButton(label); btn.setFixedHeight(36); btn.setStyleSheet(qss)
                btn.clicked.connect(lambda _, l=label: self._press(l))
                grid.addWidget(btn, r, c, 1, 2 if label=="0" else 1)
        lay.addWidget(self.display); lay.addLayout(grid)

    def _press(self, key):
        if key == "C": self._expr = ""; self.display.setText("0"); return
        if key == "=":
            try:
                r = eval(self._expr.replace("÷","/").replace("×","*").replace("−","-"))
                self._expr = str(r); self.display.setText(str(round(r,8)))
            except Exception: self.display.setText("Hata")
            return
        if key == "±":
            try: self._expr = str(-float(self._expr)); self.display.setText(self._expr)
            except: pass; return
        if key == "%":
            try: self._expr = str(float(self._expr)/100); self.display.setText(self._expr)
            except: pass; return
        self._expr += key; self.display.setText(self._expr[-22:])


# ─────────────────────────────────────────────────────────────────────────────
# UNIT CONVERTER
# ─────────────────────────────────────────────────────────────────────────────
class UnitConverterWidget(QWidget):
    UNITS = {
        "Uzunluk": {"m":1,"km":0.001,"cm":100,"mm":1000,"mi":0.000621371,"ft":3.28084,"in":39.3701},
        "Ağırlık": {"kg":1,"g":1000,"lb":2.20462,"oz":35.274,"t":0.001},
        "Sıcaklık": {"°C":"base","°F":None,"K":None},
        "Alan":    {"m²":1,"km²":1e-6,"cm²":10000,"ha":0.0001,"acre":0.000247105},
        "Hacim":   {"L":1,"mL":1000,"m³":0.001,"gal":0.264172},
    }

    def __init__(self):
        super().__init__()
        from config import led, cfg
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(6)
        cb_qss = (f"QComboBox{{background:{led(0.06)};border:1px solid {led(0.22)};"
                  f"border-radius:8px;padding:0 6px;color:#e8f4ff;height:28px;"
                  f"font-family:'Rajdhani';font-size:12px;}}"
                  f"QComboBox::drop-down{{border:none;}}"
                  f"QComboBox QAbstractItemView{{background:#080d1a;color:#e8f4ff;selection-background-color:{led(0.2)};}}")
        inp_qss = (f"QLineEdit{{background:{led(0.06)};border:1px solid {led(0.22)};"
                   f"border-radius:8px;padding:0 8px;color:#e8f4ff;font-family:'Rajdhani';font-size:13px;}}"
                   f"QLineEdit:focus{{border-color:{led(0.5)};}}")
        self.cat_cb = QComboBox(); self.cat_cb.addItems(list(self.UNITS.keys()))
        self.cat_cb.setStyleSheet(cb_qss)
        row = QHBoxLayout(); row.setSpacing(6)
        self.val = QLineEdit("1"); self.val.setFixedHeight(32); self.val.setStyleSheet(inp_qss)
        self.fc = QComboBox(); self.tc = QComboBox()
        self.fc.setStyleSheet(cb_qss); self.tc.setStyleSheet(cb_qss)
        swap = QPushButton("⇌"); swap.setFixedSize(30,32)
        swap.setStyleSheet(f"QPushButton{{background:{led(0.07)};border:1px solid {led(0.22)};"
            f"border-radius:8px;color:{cfg['led_color']};font-size:14px;}}"
            f"QPushButton:hover{{background:{led(0.18)};}}")
        swap.clicked.connect(lambda: (self.fc.setCurrentIndex(self.tc.currentIndex()),
                                       self.tc.setCurrentIndex(self.fc.currentIndex())))
        row.addWidget(self.val,2); row.addWidget(self.fc,2); row.addWidget(swap); row.addWidget(self.tc,2)
        self.result = QLabel("= 1"); self.result.setFont(QFont("Rajdhani",16,QFont.Weight.Bold))
        self.result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result.setStyleSheet(f"color:{cfg['led_color']};")
        lay.addWidget(self.cat_cb); lay.addLayout(row); lay.addWidget(self.result)
        self.cat_cb.currentTextChanged.connect(self._update_units)
        self.val.textChanged.connect(self._convert)
        self.fc.currentTextChanged.connect(self._convert)
        self.tc.currentTextChanged.connect(self._convert)
        self._update_units(self.cat_cb.currentText())

    def _update_units(self, cat):
        units = list(self.UNITS.get(cat,{}).keys())
        self.fc.blockSignals(True); self.tc.blockSignals(True)
        self.fc.clear(); self.tc.clear()
        self.fc.addItems(units); self.tc.addItems(units)
        if len(units) > 1: self.tc.setCurrentIndex(1)
        self.fc.blockSignals(False); self.tc.blockSignals(False)
        self._convert()

    def _convert(self):
        try:
            cat = self.cat_cb.currentText(); val = float(self.val.text() or "0")
            fu = self.fc.currentText(); tu = self.tc.currentText()
            units = self.UNITS[cat]
            if cat == "Sıcaklık":
                if fu=="°F": base = (val-32)*5/9
                elif fu=="K": base = val-273.15
                else: base = val
                if tu=="°F": res = base*9/5+32
                elif tu=="K": res = base+273.15
                else: res = base
            else:
                base = val / units[fu]; res = base * units[tu]
            if abs(res) >= 1e6 or (abs(res) < 0.001 and res != 0):
                self.result.setText(f"= {res:.4e} {tu}")
            else:
                self.result.setText(f"= {round(res,6):.6g} {tu}")
        except Exception:
            self.result.setText("—")


# ─────────────────────────────────────────────────────────────────────────────
# CURRENCY
# ─────────────────────────────────────────────────────────────────────────────
class CurrencyWidget(QWidget):
    def __init__(self):
        super().__init__()
        from config import led, cfg
        from threads import CurrencyFetcher
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(6)
        self._rates = {}
        cb_qss = (f"QComboBox{{background:{led(0.06)};border:1px solid {led(0.22)};"
                  f"border-radius:8px;padding:0 6px;color:#e8f4ff;height:30px;"
                  f"font-family:'Rajdhani';font-size:12px;}}"
                  f"QComboBox::drop-down{{border:none;}}"
                  f"QComboBox QAbstractItemView{{background:#080d1a;color:#e8f4ff;selection-background-color:{led(0.2)};}}")
        inp_qss = (f"QLineEdit{{background:{led(0.06)};border:1px solid {led(0.22)};"
                   f"border-radius:8px;padding:0 8px;color:#e8f4ff;font-family:'Rajdhani';font-size:13px;}}"
                   f"QLineEdit:focus{{border-color:{led(0.5)};}}")
        currencies = ["USD","EUR","TRY","GBP","JPY","CHF","CNY","AUD","CAD","RUB"]
        top = QHBoxLayout(); top.setSpacing(6)
        self.amount = QLineEdit("1"); self.amount.setFixedHeight(32); self.amount.setStyleSheet(inp_qss)
        self.fc = QComboBox(); self.fc.addItems(currencies); self.fc.setStyleSheet(cb_qss); self.fc.setCurrentText("USD")
        self.tc = QComboBox(); self.tc.addItems(currencies); self.tc.setStyleSheet(cb_qss); self.tc.setCurrentText("TRY")
        top.addWidget(self.amount,2); top.addWidget(self.fc); top.addWidget(self.tc)
        self.result = QLabel("Kur yükleniyor...")
        self.result.setFont(QFont("Rajdhani",14,QFont.Weight.Bold))
        self.result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result.setStyleSheet(f"color:{cfg['led_color']};")
        self.rate_lbl = QLabel("")
        self.rate_lbl.setFont(QFont("Rajdhani",10)); self.rate_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rate_lbl.setStyleSheet("color:rgba(200,220,255,0.4);")
        ref = QPushButton("⟳ Güncelle"); ref.setFixedHeight(26)
        ref.setStyleSheet(f"QPushButton{{background:{led(0.07)};border:1px solid {led(0.22)};"
            f"border-radius:8px;color:#e8f4ff;font-family:'Rajdhani';font-size:11px;}}"
            f"QPushButton:hover{{background:{led(0.15)};}}")
        ref.clicked.connect(self._fetch)
        lay.addLayout(top); lay.addWidget(self.result); lay.addWidget(self.rate_lbl); lay.addWidget(ref)
        for sig in (self.amount.textChanged, self.fc.currentTextChanged, self.tc.currentTextChanged):
            sig.connect(self._convert)
        self._CurrencyFetcher = CurrencyFetcher
        self._fetch()

    def _fetch(self):
        self._f = self._CurrencyFetcher(); self._f.done.connect(self._on); self._f.start()
    def _on(self, rates): self._rates = rates; self._convert()
    def _convert(self):
        if not self._rates: return
        try:
            amt = float(self.amount.text() or "0")
            rf = self._rates.get(self.fc.currentText(),1)
            rt = self._rates.get(self.tc.currentText(),1)
            res = amt * (rt/rf)
            self.result.setText(f"{res:,.4f} {self.tc.currentText()}")
            self.rate_lbl.setText(f"1 {self.fc.currentText()} = {rt/rf:.4f} {self.tc.currentText()}")
        except Exception:
            self.result.setText("—")


# ─────────────────────────────────────────────────────────────────────────────
# QR
# ─────────────────────────────────────────────────────────────────────────────
class QRWidget(QWidget):
    def __init__(self):
        super().__init__()
        from config import led
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(6)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.inp = QLineEdit(); self.inp.setPlaceholderText("URL veya metin girin...")
        self.inp.setFixedHeight(30)
        self.inp.setStyleSheet(f"QLineEdit{{background:{led(0.06)};border:1px solid {led(0.22)};"
            f"border-radius:8px;padding:0 8px;color:#e8f4ff;font-family:'Rajdhani';font-size:12px;}}")
        self.lbl = QLabel(); self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl.setFixedSize(150,150); self.lbl.setStyleSheet("background:white;border-radius:8px;")
        gen = QPushButton("QR Oluştur"); gen.setFixedHeight(28)
        gen.setStyleSheet(f"QPushButton{{background:{led(0.08)};border:1px solid {led(0.25)};"
            f"border-radius:8px;color:#e8f4ff;font-family:'Rajdhani';font-size:12px;}}"
            f"QPushButton:hover{{background:{led(0.18)};}}")
        gen.clicked.connect(self._gen)
        lay.addWidget(self.inp); lay.addWidget(gen); lay.addWidget(self.lbl)
        if not HAS_QR:
            n = QLabel("pip install qrcode pillow"); n.setAlignment(Qt.AlignmentFlag.AlignCenter)
            n.setStyleSheet("color:rgba(255,160,0,0.8);font-size:11px;"); lay.addWidget(n)

    def _gen(self):
        if not HAS_QR or not self.inp.text().strip(): return
        try:
            import qrcode
            qr = qrcode.QRCode(box_size=4, border=2)
            qr.add_data(self.inp.text().strip()); qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = img.tobytes()
            qi = QImage(buf, img.size[0], img.size[1], QImage.Format.Format_Grayscale8)
            pm = QPixmap.fromImage(qi).scaled(140,140,Qt.AspectRatioMode.KeepAspectRatio)
            self.lbl.setPixmap(pm)
        except Exception as ex:
            self.lbl.setText(str(ex))


# ─────────────────────────────────────────────────────────────────────────────
# PASSWORD
# ─────────────────────────────────────────────────────────────────────────────
class PasswordWidget(QWidget):
    def __init__(self):
        super().__init__()
        from config import led, cfg
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(6)
        self.spin = QSpinBox(); self.spin.setRange(8,64); self.spin.setValue(16)
        self.spin.setStyleSheet(f"QSpinBox{{background:{led(0.06)};border:1px solid {led(0.22)};"
            f"border-radius:8px;padding:0 6px;color:#e8f4ff;height:28px;font-family:'Rajdhani';}}")
        len_row = QHBoxLayout()
        ll = QLabel("Uzunluk:"); ll.setFont(QFont("Rajdhani",11)); ll.setStyleSheet("color:rgba(200,220,255,0.6);")
        len_row.addWidget(ll); len_row.addWidget(self.spin); len_row.addStretch()
        self.chk_u = QCheckBox("A-Z"); self.chk_l = QCheckBox("a-z")
        self.chk_d = QCheckBox("0-9"); self.chk_s = QCheckBox("!@#…")
        for cb in (self.chk_u, self.chk_l, self.chk_d, self.chk_s):
            cb.setChecked(True); cb.setFont(QFont("Rajdhani",11))
            cb.setStyleSheet(f"QCheckBox{{color:#e8f4ff;spacing:6px;}}"
                f"QCheckBox::indicator{{width:13px;height:13px;border-radius:3px;"
                f"border:1px solid {led(0.35)};background:transparent;}}"
                f"QCheckBox::indicator:checked{{background:{cfg['led_color']};}}")
        self.out = QLineEdit(); self.out.setReadOnly(True)
        self.out.setFont(QFont("Rajdhani",13)); self.out.setFixedHeight(34)
        self.out.setStyleSheet(f"QLineEdit{{background:{led(0.06)};border:1px solid {led(0.25)};"
            f"border-radius:10px;padding:0 10px;color:{cfg['led_color']};}}")
        btn_row = QHBoxLayout(); btn_row.setSpacing(6)
        gen = QPushButton("Üret"); cp = QPushButton("⎘ Kopyala")
        qss = (f"QPushButton{{background:{led(0.07)};border:1px solid {led(0.22)};"
               f"border-radius:8px;color:#e8f4ff;font-family:'Rajdhani';font-size:12px;}}"
               f"QPushButton:hover{{background:{led(0.17)};}}")
        gen.setFixedHeight(28); gen.setStyleSheet(qss); gen.clicked.connect(self._gen)
        cp.setFixedHeight(28); cp.setStyleSheet(qss)
        cp.clicked.connect(lambda: QApplication.clipboard().setText(self.out.text()) if self.out.text() else None)
        btn_row.addWidget(gen); btn_row.addWidget(cp)
        chk_row = QHBoxLayout(); chk_row.setSpacing(10)
        for cb in (self.chk_u, self.chk_l, self.chk_d, self.chk_s): chk_row.addWidget(cb)
        lay.addLayout(len_row); lay.addLayout(chk_row); lay.addWidget(self.out); lay.addLayout(btn_row)
        self._gen()

    def _gen(self):
        chars = ""
        if self.chk_u.isChecked(): chars += string.ascii_uppercase
        if self.chk_l.isChecked(): chars += string.ascii_lowercase
        if self.chk_d.isChecked(): chars += string.digits
        if self.chk_s.isChecked(): chars += "!@#$%^&*()-_=+[]{}|;:,.<>?"
        if not chars: chars = string.ascii_letters + string.digits
        self.out.setText("".join(random.choice(chars) for _ in range(self.spin.value())))


# ─────────────────────────────────────────────────────────────────────────────
# MULTI CLOCK
# ─────────────────────────────────────────────────────────────────────────────
class MultiClockWidget(QWidget):
    ZONES = {"İstanbul":3,"New York":-4,"Londra":1,"Tokyo":9,
             "Dubai":4,"Berlin":2,"Sydney":10,"Pekin":8,"Los Angeles":-7}

    def __init__(self):
        super().__init__()
        from config import led, cfg
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(3)
        self.labels = {}
        for city, offset in self.ZONES.items():
            row = QWidget(); rl = QHBoxLayout(row); rl.setContentsMargins(4,2,4,2)
            cl = QLabel(city); cl.setFont(QFont("Rajdhani",11))
            cl.setStyleSheet("color:rgba(200,220,255,0.55);"); cl.setFixedWidth(100)
            tl = QLabel("—"); tl.setFont(QFont("Rajdhani",12,QFont.Weight.Medium))
            tl.setStyleSheet(f"color:{cfg['led_color']};")
            tl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            rl.addWidget(cl); rl.addWidget(tl,1); lay.addWidget(row)
            self.labels[city] = (tl, offset)
        self._t = QTimer(self); self._t.timeout.connect(self._tick); self._t.start(1000); self._tick()

    def _tick(self):
        utc = datetime.utcnow()
        for city, (lbl, off) in self.labels.items():
            local = utc + timedelta(hours=off)
            lbl.setText(local.strftime("%H:%M:%S"))


# ─────────────────────────────────────────────────────────────────────────────
# CALENDAR
# ─────────────────────────────────────────────────────────────────────────────
class CalendarWidget(QWidget):
    def __init__(self):
        super().__init__()
        from config import led, cfg
        self._now = datetime.now(); self._y = self._now.year; self._m = self._now.month
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(4)
        btn_qss = (f"QPushButton{{background:{led(0.06)};border:1px solid {led(0.2)};"
                   f"border-radius:6px;color:{cfg['led_color']};font-size:14px;}}"
                   f"QPushButton:hover{{background:{led(0.15)};}}")
        nav = QHBoxLayout()
        prev = QPushButton("‹"); prev.setFixedSize(24,24); prev.setStyleSheet(btn_qss)
        nxt  = QPushButton("›"); nxt.setFixedSize(24,24);  nxt.setStyleSheet(btn_qss)
        self.mlbl = QLabel(); self.mlbl.setFont(QFont("Orbitron",9,QFont.Weight.Bold))
        self.mlbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mlbl.setStyleSheet(f"color:{cfg['led_color']};letter-spacing:1px;")
        prev.clicked.connect(self._prev); nxt.clicked.connect(self._next)
        nav.addWidget(prev); nav.addWidget(self.mlbl,1); nav.addWidget(nxt)
        lay.addLayout(nav)
        self.grid = QGridLayout(); self.grid.setSpacing(2); lay.addLayout(self.grid)
        self._render()

    def _prev(self):
        self._m -= 1
        if self._m < 1: self._m=12; self._y -= 1
        self._render()

    def _next(self):
        self._m += 1
        if self._m > 12: self._m=1; self._y += 1
        self._render()

    def _render(self):
        import calendar
        from config import led, cfg
        while self.grid.count():
            it = self.grid.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        months = ["Oca","Şub","Mar","Nis","May","Haz","Tem","Ağu","Eyl","Eki","Kas","Ara"]
        self.mlbl.setText(f"{months[self._m-1]} {self._y}")
        for i, d in enumerate(["Pzt","Sal","Çar","Per","Cum","Cmt","Paz"]):
            l = QLabel(d); l.setFont(QFont("Rajdhani",9))
            l.setAlignment(Qt.AlignmentFlag.AlignCenter); l.setStyleSheet("color:rgba(200,220,255,0.4);")
            self.grid.addWidget(l, 0, i)
        today = datetime.now()
        for r, week in enumerate(calendar.monthcalendar(self._y, self._m)):
            for c, day in enumerate(week):
                if day == 0: continue
                is_today = (day==today.day and self._m==today.month and self._y==today.year)
                l = QLabel(str(day)); l.setFont(QFont("Rajdhani",10))
                l.setAlignment(Qt.AlignmentFlag.AlignCenter); l.setFixedSize(26,20)
                if is_today:
                    l.setStyleSheet(f"color:white;background:{cfg['led_color']};border-radius:4px;font-weight:600;")
                else:
                    color = led(0.7) if c>=5 else "rgba(200,220,255,0.75)"
                    l.setStyleSheet(f"color:{color};")
                self.grid.addWidget(l, r+1, c)


# ─────────────────────────────────────────────────────────────────────────────
# WEB SEARCH
# ─────────────────────────────────────────────────────────────────────────────
class WebSearchWidget(QWidget):
    ENGINES = {
        "Google":      "https://www.google.com/search?q=",
        "YouTube":     "https://www.youtube.com/results?search_query=",
        "Bing":        "https://www.bing.com/search?q=",
        "DuckDuckGo":  "https://duckduckgo.com/?q=",
        "GitHub":      "https://github.com/search?q=",
        "Wikipedia":   "https://tr.wikipedia.org/wiki/Special:Search?search=",
    }

    def __init__(self):
        super().__init__()
        from config import led, cfg
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(6)
        cb_qss = (f"QComboBox{{background:{led(0.06)};border:1px solid {led(0.22)};"
                  f"border-radius:8px;padding:0 6px;color:#e8f4ff;height:28px;"
                  f"font-family:'Rajdhani';font-size:12px;}}"
                  f"QComboBox::drop-down{{border:none;}}"
                  f"QComboBox QAbstractItemView{{background:#080d1a;color:#e8f4ff;selection-background-color:{led(0.2)};}}")
        inp_qss = (f"QLineEdit{{background:{led(0.06)};border:1px solid {led(0.22)};"
                   f"border-radius:8px;padding:0 8px;color:#e8f4ff;font-family:'Rajdhani';font-size:12px;}}"
                   f"QLineEdit:focus{{border-color:{led(0.5)};}}")
        btn_qss = (f"QPushButton{{background:{led(0.08)};border:1px solid {led(0.25)};"
                   f"border-radius:8px;color:#e8f4ff;font-family:'Rajdhani';font-size:12px;padding:0 10px;}}"
                   f"QPushButton:hover{{background:{led(0.18)};}}")
        self.engine = QComboBox(); self.engine.addItems(list(self.ENGINES.keys()))
        self.engine.setStyleSheet(cb_qss)
        row = QHBoxLayout(); row.setSpacing(6)
        self.inp = QLineEdit(); self.inp.setPlaceholderText("Arama yap...")
        self.inp.setFixedHeight(30); self.inp.setStyleSheet(inp_qss)
        go = QPushButton("🔍 Ara"); go.setFixedHeight(30); go.setStyleSheet(btn_qss)
        go.clicked.connect(self._search); self.inp.returnPressed.connect(self._search)
        row.addWidget(self.inp,1); row.addWidget(go)
        url_row = QHBoxLayout(); url_row.setSpacing(6)
        self.url = QLineEdit(); self.url.setPlaceholderText("URL aç: https://...")
        self.url.setFixedHeight(28); self.url.setStyleSheet(inp_qss)
        open_u = QPushButton("↗"); open_u.setFixedSize(28,28)
        open_u.setStyleSheet(f"QPushButton{{background:{led(0.07)};border:1px solid {led(0.22)};"
            f"border-radius:8px;color:{cfg['led_color']};font-size:14px;}}"
            f"QPushButton:hover{{background:{led(0.17)};}}")
        open_u.clicked.connect(self._open_url); self.url.returnPressed.connect(self._open_url)
        url_row.addWidget(self.url,1); url_row.addWidget(open_u)
        lay.addWidget(self.engine); lay.addLayout(row); lay.addLayout(url_row)

    def _search(self):
        from config import dm
        q = self.inp.text().strip()
        if not q: return
        dm.add_search_history(q)
        url = self.ENGINES[self.engine.currentText()] + urllib.parse.quote(q)
        subprocess.Popen(["start","",url], shell=True)

    def _open_url(self):
        url = self.url.text().strip()
        if not url: return
        if not url.startswith(("http://","https://")): url = "https://" + url
        subprocess.Popen(["start","",url], shell=True)


# ─────────────────────────────────────────────────────────────────────────────
# EMOJI SEARCH
# ─────────────────────────────────────────────────────────────────────────────
class EmojiSearchWidget(QWidget):
    ALL = "😀😂🥰😎😭😤🤔💀🙏❤️🔥✨🎉🎊🎁🎂🏆🥇🌟⭐💫🌈🦋🐱🐶🦊🐻🐼🦁🐯🦄🐉🌺🌸🍎🍕🍔🌮🍜🍣🍰🎂🍩🍦🥤☕🎮🎵🎸🎹🚀✈️🚂🚗🏠🏰🌍🌙☀️⛅🌊🏔️🌴🌵🍀🌻💡🔑🔒📱💻📷📚📝✏️📌🔧⚙️🎯🎲♟️🍺💎👑🌹🦅🎭🎬🏋️🤸🧘🚴🏊⚽🏀🎾🏈⚾🥊🎿🏄🧩🔮🧲🎨🖼️🎭🎪🎡🎢"

    def __init__(self):
        super().__init__()
        from config import led, cfg
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(6)
        self.inp = QLineEdit(); self.inp.setPlaceholderText("Emoji ara...")
        self.inp.setFixedHeight(28)
        self.inp.setStyleSheet(f"QLineEdit{{background:{led(0.06)};border:1px solid {led(0.22)};"
            f"border-radius:8px;padding:0 8px;color:#e8f4ff;font-family:'Rajdhani';font-size:12px;}}")
        self.gw = QWidget(); self.gl = QGridLayout(self.gw)
        self.gl.setSpacing(3); self.gl.setContentsMargins(0,0,0,0)
        self.info = QLabel(""); self.info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info.setStyleSheet(f"color:{cfg['led_color']};font-size:12px;")
        lay.addWidget(self.inp); lay.addWidget(self.gw); lay.addWidget(self.info)
        self._render()
        self.inp.textChanged.connect(lambda _: self._render())

    def _render(self):
        from config import led, cfg
        while self.gl.count():
            it = self.gl.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        emojis = [e for e in self.ALL if e.strip()][:80]
        cols = 12
        for i, em in enumerate(emojis):
            btn = QPushButton(em); btn.setFixedSize(30,30)
            btn.setFont(QFont("Segoe UI Emoji",13))
            btn.setStyleSheet(f"QPushButton{{background:transparent;border:none;border-radius:6px;}}"
                f"QPushButton:hover{{background:{led(0.1)};}}")
            btn.clicked.connect(lambda _, e=em: self._copy(e))
            self.gl.addWidget(btn, i//cols, i%cols)

    def _copy(self, em):
        QApplication.clipboard().setText(em)
        self.info.setText(f"Kopyalandı: {em}")
        QTimer.singleShot(2000, lambda: self.info.setText(""))


# ─────────────────────────────────────────────────────────────────────────────
# COLOR PICKER
# ─────────────────────────────────────────────────────────────────────────────
class ColorPickerWidget(QWidget):
    def __init__(self):
        super().__init__()
        from config import led, cfg
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(6)
        self.preview = QWidget(); self.preview.setFixedHeight(44)
        self.preview.setStyleSheet("background:#00aaff;border-radius:10px;")
        self.hex_inp = QLineEdit("#00aaff"); self.hex_inp.setFixedHeight(30)
        self.hex_inp.setFont(QFont("Rajdhani",13))
        self.hex_inp.setStyleSheet(f"QLineEdit{{background:{led(0.06)};border:1px solid {led(0.22)};"
            f"border-radius:8px;padding:0 8px;color:#e8f4ff;}}")
        self.hex_inp.textChanged.connect(self._update)
        pick = QPushButton("🎨 Renk Seç"); pick.setFixedHeight(28)
        pick.setStyleSheet(f"QPushButton{{background:{led(0.07)};border:1px solid {led(0.22)};"
            f"border-radius:8px;color:#e8f4ff;font-family:'Rajdhani';font-size:12px;}}"
            f"QPushButton:hover{{background:{led(0.17)};}}")
        pick.clicked.connect(self._pick)
        copy_row = QHBoxLayout(); copy_row.setSpacing(6)
        for fmt, fn in [("HEX", lambda: self.hex_inp.text()),
                        ("RGB", self._rgb), ("HSL", self._hsl)]:
            b = QPushButton(f"⎘ {fmt}"); b.setFixedHeight(24)
            b.setStyleSheet(f"QPushButton{{background:{led(0.05)};border:1px solid {led(0.18)};"
                f"border-radius:6px;color:#e8f4ff;font-family:'Rajdhani';font-size:11px;}}"
                f"QPushButton:hover{{background:{led(0.14)};}}")
            b.clicked.connect(lambda _, f=fn: QApplication.clipboard().setText(f()))
            copy_row.addWidget(b)
        save_p = QPushButton("+ Palette'e Kaydet"); save_p.setFixedHeight(24)
        save_p.setStyleSheet(f"QPushButton{{background:{led(0.05)};border:1px solid {led(0.18)};"
            f"border-radius:6px;color:{cfg['led_color']};font-family:'Rajdhani';font-size:11px;}}"
            f"QPushButton:hover{{background:{led(0.12)};}}")
        save_p.clicked.connect(self._save_pal)
        self.pal_row = QHBoxLayout(); self.pal_row.setSpacing(4)
        lay.addWidget(self.preview); lay.addWidget(self.hex_inp); lay.addWidget(pick)
        lay.addLayout(copy_row); lay.addWidget(save_p); lay.addLayout(self.pal_row)
        self._refresh_pals()

    def _update(self, t):
        if QColor(t).isValid(): self.preview.setStyleSheet(f"background:{t};border-radius:10px;")
    def _pick(self):
        c = QColorDialog.getColor(QColor(self.hex_inp.text() or "#fff"), self)
        if c.isValid(): self.hex_inp.setText(c.name())
    def _rgb(self):
        c = QColor(self.hex_inp.text()); return f"rgb({c.red()},{c.green()},{c.blue()})"
    def _hsl(self):
        c = QColor(self.hex_inp.text())
        return f"hsl({c.hslHue()},{c.hslSaturation()*100//255}%,{c.lightness()*100//255}%)"
    def _save_pal(self):
        from config import cfg
        h = self.hex_inp.text()
        if QColor(h).isValid():
            p = cfg["saved_palettes"]
            if h not in p: p.append(h); cfg["saved_palettes"]=p; cfg.save()
            self._refresh_pals()
    def _refresh_pals(self):
        from config import cfg
        while self.pal_row.count():
            it = self.pal_row.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        for color in cfg["saved_palettes"][-10:]:
            b = QPushButton(); b.setFixedSize(22,22)
            b.setStyleSheet(f"background:{color};border-radius:11px;border:1px solid rgba(255,255,255,0.2);")
            b.setToolTip(color); b.clicked.connect(lambda _, c=color: self.hex_inp.setText(c))
            self.pal_row.addWidget(b)
        self.pal_row.addStretch()


# ─────────────────────────────────────────────────────────────────────────────
# FOLDER GROUPS
# ─────────────────────────────────────────────────────────────────────────────
class FolderGroupWidget(QWidget):
    def __init__(self, all_apps, launch_cb):
        super().__init__()
        self.all_apps = all_apps; self.launch_cb = launch_cb
        from config import led
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(6)
        hdr = QHBoxLayout()
        add = QPushButton("+ Yeni Klasör"); add.setFixedHeight(26)
        add.setStyleSheet(f"QPushButton{{background:{led(0.07)};border:1px solid {led(0.22)};"
            f"border-radius:8px;color:#e8f4ff;font-family:'Rajdhani';font-size:12px;padding:0 10px;}}"
            f"QPushButton:hover{{background:{led(0.17)};}}")
        add.clicked.connect(self._add); hdr.addStretch(); hdr.addWidget(add)
        lay.addLayout(hdr)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background:transparent;border:none;")
        self.cw = QWidget(); self.cl = QVBoxLayout(self.cw)
        self.cl.setContentsMargins(0,0,0,0); self.cl.setSpacing(6)
        self.scroll.setWidget(self.cw); lay.addWidget(self.scroll)
        self._render()

    def update_apps(self, apps): self.all_apps = apps; self._render()

    def _add(self):
        from config import dm
        nm = "Yeni Klasör"
        count = 1
        while nm in dm.data["folders"]: nm = f"Yeni Klasör {count}"; count+=1
        dm.data["folders"][nm] = []; dm.save(); self._render()

    def _render(self):
        from config import dm
        while self.cl.count():
            it = self.cl.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        for fname, paths in dm.data["folders"].items():
            self.cl.addWidget(self._folder_w(fname, paths))
        self.cl.addStretch()

    def _folder_w(self, name, paths):
        from config import led, cfg, dm, _icon_label
        w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(8,6,8,6); lay.setSpacing(4)
        w.setStyleSheet(f"background:{led(0.05)};border-radius:10px;border:1px solid {led(0.15)};")
        hdr = QHBoxLayout()
        lbl = QLabel(f"📁 {name}"); lbl.setFont(QFont("Rajdhani",12,QFont.Weight.Medium))
        lbl.setStyleSheet(f"color:{cfg['led_color']};")
        dl = QPushButton("✕"); dl.setFixedSize(20,20)
        dl.setStyleSheet("color:rgba(255,80,80,0.6);background:transparent;border:none;font-size:11px;")
        dl.clicked.connect(lambda _, n=name: self._del(n))
        hdr.addWidget(lbl); hdr.addStretch(); hdr.addWidget(dl); lay.addLayout(hdr)
        apps_in = [a for a in self.all_apps if a.get("path","") in paths]
        for app in apps_in[:6]:
            row = QWidget(); rl = QHBoxLayout(row); rl.setContentsMargins(0,1,0,1)
            ic = _icon_label(app, 22)
            nm = QLabel(app["name"][:28]); nm.setFont(QFont("Rajdhani",11))
            nm.setStyleSheet("color:rgba(200,220,255,0.8);"); nm.setCursor(Qt.CursorShape.PointingHandCursor)
            nm.mousePressEvent = lambda e, a=app: self.launch_cb(a)
            rm = QPushButton("−"); rm.setFixedSize(16,16)
            rm.setStyleSheet("background:transparent;border:none;color:rgba(255,80,80,0.5);font-size:13px;")
            rm.clicked.connect(lambda _, n=name, p=app["path"]: self._rm(n,p))
            rl.addWidget(ic); rl.addWidget(nm,1); rl.addWidget(rm)
            lay.addWidget(row)
        cb = QComboBox(); cb.setFixedHeight(22)
        cb.setStyleSheet(f"QComboBox{{background:{led(0.04)};border:1px solid {led(0.15)};"
            f"border-radius:6px;padding:0 4px;color:#e8f4ff;font-family:'Rajdhani';font-size:11px;}}"
            f"QComboBox::drop-down{{border:none;}}"
            f"QComboBox QAbstractItemView{{background:#080d1a;color:#e8f4ff;}}")
        cb.addItem("Uygulama ekle...")
        for a in self.all_apps: cb.addItem(a["name"])
        add_r = QHBoxLayout(); add_r.setSpacing(4)
        ab = QPushButton("+"); ab.setFixedSize(22,22)
        ab.setStyleSheet(f"QPushButton{{background:{led(0.06)};border:1px solid {led(0.2)};"
            f"border-radius:6px;color:{cfg['led_color']};font-size:14px;}}"
            f"QPushButton:hover{{background:{led(0.14)};}}")
        ab.clicked.connect(lambda _, n=name, c=cb: self._add_app(n,c))
        add_r.addWidget(cb,1); add_r.addWidget(ab); lay.addLayout(add_r)
        return w

    def _del(self, name):
        from config import dm
        dm.data["folders"].pop(name, None); dm.save(); self._render()
    def _rm(self, name, path):
        from config import dm
        if name in dm.data["folders"] and path in dm.data["folders"][name]:
            dm.data["folders"][name].remove(path); dm.save(); self._render()
    def _add_app(self, name, cb):
        from config import dm
        i = cb.currentIndex()
        if i==0 or i>len(self.all_apps): return
        app = self.all_apps[i-1]
        if app["path"] not in dm.data["folders"].get(name,[]):
            dm.data["folders"].setdefault(name,[]).append(app["path"]); dm.save(); self._render()


# ─────────────────────────────────────────────────────────────────────────────
# TERMINAL + SYSTEM BUTTONS
# ─────────────────────────────────────────────────────────────────────────────
class TerminalWidget(QWidget):
    def __init__(self):
        super().__init__()
        from config import led, cfg
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(6)
        btn_qss = (f"QPushButton{{background:{led(0.06)};border:1px solid {led(0.2)};"
                   f"border-radius:9px;color:#e8f4ff;font-family:'Rajdhani';font-size:13px;"
                   f"text-align:left;padding:0 12px;}}"
                   f"QPushButton:hover{{background:{led(0.15)};border-color:{led(0.4)};color:{cfg['led_color']};}}")
        for label, cmd in [
            ("💻 CMD", "cmd"),
            ("⚡ PowerShell", "powershell"),
            ("🔷 Windows Terminal", "wt"),
            ("🐙 Git Bash", r'"C:\Program Files\Git\git-bash.exe"'),
        ]:
            b = QPushButton(label); b.setFixedHeight(32); b.setStyleSheet(btn_qss)
            b.clicked.connect(lambda _, c=cmd: subprocess.Popen(c, shell=True))
            lay.addWidget(b)
        lay.addSpacing(8)
        for label, fn, dng in [
            ("🔁 Yeniden Başlat", lambda: subprocess.call(["shutdown","/r","/t","5"]), False),
            ("😴 Uyku Modu", lambda: subprocess.call(["rundll32","powrprof.dll,SetSuspendState","0","1","0"]), False),
            ("⏻ Kapat", lambda: subprocess.call(["shutdown","/s","/t","5"]), True),
        ]:
            col = "rgba(255,80,80,0.15)" if dng else led(0.06)
            brd = "rgba(255,80,80,0.4)"  if dng else led(0.2)
            b = QPushButton(label); b.setFixedHeight(28)
            b.setStyleSheet(f"QPushButton{{background:{col};border:1px solid {brd};"
                f"border-radius:8px;color:#e8f4ff;font-family:'Rajdhani';font-size:12px;}}"
                f"QPushButton:hover{{background:{led(0.15)};}}")
            b.clicked.connect(fn); lay.addWidget(b)
        lay.addStretch()
