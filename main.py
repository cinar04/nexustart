"""
main.py — NexusStart v3.0  |  Ana pencere & giriş noktası

Modüler yapı:
  config.py         — Ayarlar, DataManager, i18n, stil yardımcıları
  animations.py     — Animasyon sınıfları (FadeScale, Ripple, LED nabız, ...)
  threads.py        — Arka plan thread'leri (Scanner, Monitor, Fetcher, ...)
  widgets.py        — Özellik widget'leri (AppTile, TopPanel, TodoWidget, ...)
  settings_panel.py — QuickSettings paneli
  main.py           — NexusStart ana penceresi ve araçlar sayfası
"""

import sys, os, subprocess, ctypes, ctypes.wintypes, time
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QLineEdit, QScrollArea,
    QStackedWidget, QSystemTrayIcon, QMenu, QTabWidget,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPalette, QPainter, QBrush, QIcon, QPixmap, QGuiApplication

# ── Modülleri içe aktar ───────────────────────────────────────────────────────
from config import (cfg, dm, tr, led, led2, BASE_QSS,
                    _section, _icon_btn, _styled_menu, _icon_label,
                    _greet, _btn_qss, _inp_qss,
                    APP_DIR, SHORTCUTS_DIR, MENU_W, MENU_H)
from animations import (FadeScaleAnimation, RippleOverlay, LedPulseWidget,
                        SkeletonWidget, NightSkyWidget, ToastNotification,
                        AnalogClockWidget)
from threads import (ShortcutScanner, SystemMonitor, DiskNetMonitor,
                     WeatherFetcher, MediaWatcher, FileSearchThread,
                     ClipboardWatcher, UpdateChecker)
from widgets import (TopPanel, AppTile, RecentRow,
                     NotesWidget, TodoWidget, PomodoroWidget, CountdownWidget,
                     ClipboardWidget, CalculatorWidget, UnitConverterWidget,
                     CurrencyWidget, QRWidget, PasswordWidget,
                     MultiClockWidget, CalendarWidget, WebSearchWidget,
                     EmojiSearchWidget, ColorPickerWidget,
                     FolderGroupWidget, TerminalWidget)
from settings_panel import QuickSettings

import win32api, win32con


# ─────────────────────────────────────────────────────────────────────────────
# ARAÇLAR SAYFASI
# ─────────────────────────────────────────────────────────────────────────────
def _build_tools_page(launch_cb):
    page = QWidget(); page.setObjectName("tp")
    page.setStyleSheet(f"#tp{{background:rgba(8,13,26,0.96);border-radius:20px;"
                       f"border:1px solid {led(0.18)};}} {BASE_QSS}")
    lay = QVBoxLayout(page); lay.setContentsMargins(16,14,16,12); lay.setSpacing(8)

    hdr = QHBoxLayout()
    title = QLabel(tr("tools")); title.setFont(QFont("Orbitron",10,QFont.Weight.Bold))
    title.setStyleSheet(f"color:{cfg['led_color']};letter-spacing:2px;")
    hdr.addWidget(title); hdr.addStretch()
    lay.addLayout(hdr)

    tab_qss = (f"QTabWidget::pane{{border:1px solid {led(0.15)};border-radius:10px;"
               f"background:rgba(8,13,26,0.5);}}"
               f"QTabBar::tab{{background:{led(0.05)};color:rgba(200,220,255,0.55);"
               f"padding:5px 9px;border-radius:6px;font-family:'Rajdhani';font-size:11px;margin-right:3px;}}"
               f"QTabBar::tab:selected{{background:{led(0.15)};color:{cfg['led_color']};}}"
               f"QTabBar::tab:hover{{background:{led(0.1)};}}")

    tabs = QTabWidget(); tabs.setFont(QFont("Rajdhani",10)); tabs.setStyleSheet(tab_qss)

    def _tab(title_str, *widgets):
        w = QWidget(); wl = QVBoxLayout(w); wl.setContentsMargins(8,8,8,8); wl.setSpacing(6)
        for item in widgets:
            if isinstance(item, str):
                wl.addWidget(_section(item))
            else:
                wl.addWidget(item)
        return w

    # Notlar & Todo
    tabs.addTab(_tab("HIZLI NOTLAR", NotesWidget(), "YAPILACAKLAR", TodoWidget()), "📝 Notlar")

    # Zamanlayıcı
    tabs.addTab(_tab("POMODORO", PomodoroWidget(), "GERİ SAYIM", CountdownWidget()), "⏱ Zamanlayıcı")

    # Hesap
    tabs.addTab(_tab("HESAP MAKİNESİ", CalculatorWidget()), "🔢 Hesap")

    # Dönüştür
    tabs.addTab(_tab("BIRIM DONUSTURUCU", UnitConverterWidget(),
                     "PARA BİRİMİ", CurrencyWidget()), "🔄 Dönüştür")

    # Web
    web_w = _tab("WEB ARAMA", WebSearchWidget(), "QR KOD", QRWidget(),
                 "ŞİFRE ÜRETECİ", PasswordWidget())
    tabs.addTab(web_w, "🌐 Web")

    # Araçlar
    tabs.addTab(_tab("EMOJİ ARA", EmojiSearchWidget(), "RENK TOPLAYICI", ColorPickerWidget()), "🎨 Araçlar")

    # Pano + saat
    _clip = ClipboardWidget()
    tabs.addTab(_tab("PANO GEÇMİŞİ", _clip, "ÇOKLU SAAT DİLİMİ", MultiClockWidget()), "📋 Pano")

    # Takvim
    cal_w = QWidget(); cal_l = QVBoxLayout(cal_w); cal_l.setContentsMargins(8,8,8,8); cal_l.setSpacing(8)
    cal_l.addWidget(_section("TAKVİM")); cal_l.addWidget(CalendarWidget())
    clk_row = QHBoxLayout(); clk_row.addStretch(); clk_row.addWidget(AnalogClockWidget()); clk_row.addStretch()
    cal_l.addWidget(_section("ANALOG SAAT")); cal_l.addLayout(clk_row); cal_l.addStretch()
    tabs.addTab(cal_w, "📅 Takvim")

    # Sistem
    tabs.addTab(_tab("TERMINAL & SİSTEM", TerminalWidget()), "💻 Sistem")

    # Klasörler
    _fold = FolderGroupWidget([], launch_cb)
    tabs.addTab(_tab("KLASÖR GRUPLARI", _fold), "📁 Klasörler")

    lay.addWidget(tabs)

    # clipboard widget ve folder widget'i dışarıya geçir (main penceresi kullanır)
    page._clip_widget = _clip
    page._fold_widget = _fold
    return page


# ─────────────────────────────────────────────────────────────────────────────
# ANA PENCERE
# ─────────────────────────────────────────────────────────────────────────────
class NexusStart(QMainWindow):
    def __init__(self):
        super().__init__()
        self.all_apps = []
        self._fs_thread = None
        self._fade = FadeScaleAnimation(self)
        self._setup_win()
        self._setup_ui()
        self._setup_tray()
        self._setup_threads()
        self._setup_hotkey()
        self._scan_apps()

    # ── Pencere ──────────────────────────────────────────────────────────────
    def _setup_win(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.Tool |
                            Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        scr = QGuiApplication.primaryScreen().geometry()
        self.sw, self.sh = scr.width(), scr.height()
        self.setGeometry((self.sw-MENU_W)//2, self.sh-MENU_H-62, MENU_W, MENU_H)
        self.hide()

    # ── UI ───────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        self.stack = QStackedWidget(); self.setCentralWidget(self.stack)

        # Ana sayfa
        self.main_page = QWidget(); self.main_page.setObjectName("mp")
        self._apply_page_style()
        self._build_main(self.main_page)

        # Gece gökyüzü (arka plan katmanı)
        self._night = NightSkyWidget(self.main_page)
        self._night.setGeometry(0, 0, MENU_W, MENU_H)
        self._night.lower()
        self._night.setVisible(cfg["night_sky"])

        # Ripple overlay (üst katman)
        self._ripple = RippleOverlay(self.main_page)
        self._ripple.setGeometry(0, 0, MENU_W, MENU_H)
        self._ripple.raise_()

        # Ayarlar sayfası (index 1)
        self.qs_page = QWidget(); self.qs_page.setObjectName("qsp")
        self.qs_page.setStyleSheet(f"#qsp{{background:rgba(8,13,26,0.96);border-radius:20px;"
                                   f"border:1px solid {led(0.18)};}} {BASE_QSS}")
        self.qs = QuickSettings()
        qsl = QVBoxLayout(self.qs_page); qsl.setContentsMargins(0,0,0,0); qsl.addWidget(self.qs)
        self.qs.closed.connect(self._close_qs)

        # Araçlar sayfası (index 2)
        self.tools_page = _build_tools_page(self._launch)
        self._clip_w = self.tools_page._clip_widget
        self._fold_w = self.tools_page._fold_widget
        # Araçlar sayfasına geri butonu
        tools_hdr = self.tools_page.findChildren(QHBoxLayout)[0] if self.tools_page.findChildren(QHBoxLayout) else None
        back_tools = _icon_btn("←","Geri")
        back_tools.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        if tools_hdr: tools_hdr.addWidget(back_tools)

        self.stack.addWidget(self.main_page)   # 0
        self.stack.addWidget(self.qs_page)     # 1
        self.stack.addWidget(self.tools_page)  # 2

    def _apply_page_style(self):
        op = cfg["bg_opacity"]
        self.main_page.setStyleSheet(
            f"#mp{{background:rgba(8,13,26,{op/100:.2f});border-radius:20px;"
            f"border:1px solid {led(0.18)};}} {BASE_QSS}")
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        eff = QGraphicsDropShadowEffect()
        eff.setColor(QColor(cfg["led_color"])); eff.setBlurRadius(50); eff.setOffset(0,6)
        self.main_page.setGraphicsEffect(eff)

    # ── Ana sayfa inşa ───────────────────────────────────────────────────────
    def _build_main(self, parent):
        root = QVBoxLayout(parent); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # LED nabız çizgisi
        root.addWidget(LedPulseWidget())

        c = QWidget(); cl = QVBoxLayout(c); cl.setContentsMargins(22,12,22,0); cl.setSpacing(0)

        # Selamlama + analog saat
        greet_row = QHBoxLayout()
        self.greet_lbl = QLabel(_greet() + f", {os.environ.get('USERNAME','Kullanıcı')}!")
        self.greet_lbl.setFont(QFont("Rajdhani",13,QFont.Weight.Medium))
        self.greet_lbl.setStyleSheet(f"color:{led(0.7)};")
        greet_row.addWidget(self.greet_lbl); greet_row.addStretch()
        greet_row.addWidget(AnalogClockWidget())
        cl.addLayout(greet_row); cl.addSpacing(6)

        # Top panel (CPU/RAM + Hava + Müzik)
        self.top_panel = TopPanel(); cl.addWidget(self.top_panel); cl.addSpacing(8)

        # Odak / DnD modu çubuğu
        mode_bar = QWidget(); mode_bar.setFixedHeight(22)
        ml = QHBoxLayout(mode_bar); ml.setContentsMargins(0,0,0,0); ml.setSpacing(6)
        mode_qss = (f"QPushButton{{background:{led(0.05)};border:1px solid {led(0.15)};"
                    f"border-radius:6px;color:rgba(200,220,255,0.45);"
                    f"font-family:'Rajdhani';font-size:10px;padding:0 8px;}}"
                    f"QPushButton:hover{{background:{led(0.12)};color:{cfg['led_color']};}}")
        self.focus_btn = QPushButton("🎯 Odak Kapalı"); self.focus_btn.setFixedHeight(20)
        self.focus_btn.setStyleSheet(mode_qss); self.focus_btn.clicked.connect(self._toggle_focus)
        self.dnd_btn = QPushButton("🔕 DnD Kapalı"); self.dnd_btn.setFixedHeight(20)
        self.dnd_btn.setStyleSheet(mode_qss); self.dnd_btn.clicked.connect(self._toggle_dnd)
        ml.addWidget(self.focus_btn); ml.addWidget(self.dnd_btn); ml.addStretch()
        cl.addWidget(mode_bar); cl.addSpacing(6)

        # Arama
        sw = QWidget(); sw.setFixedHeight(46); sl2 = QHBoxLayout(sw); sl2.setContentsMargins(0,0,0,0)
        self.search = QLineEdit(); self.search.setPlaceholderText(tr("search_placeholder"))
        self.search.setFixedHeight(42)
        self.search.setStyleSheet(
            f"QLineEdit{{background:{led(0.05)};border:1px solid {led(0.2)};"
            f"border-radius:10px;padding:0 14px 0 42px;color:#e8f4ff;"
            f"font-family:'Rajdhani','Segoe UI';font-size:15px;font-weight:500;}}"
            f"QLineEdit:focus{{border-color:{led(0.55)};background:{led(0.09)};}}")
        self.search.textChanged.connect(self._on_search)
        self.search.returnPressed.connect(lambda: dm.add_search_history(self.search.text().strip()) if self.search.text().strip() else None)
        sl2.addWidget(self.search)
        si = QLabel("🔍"); si.setFixedSize(22,22); si.setParent(sw); si.move(12,10); si.raise_()
        cl.addWidget(sw); cl.addSpacing(8)

        # Favoriler
        cl.addWidget(_section(tr("favorites"))); cl.addSpacing(4)
        self.fav_scroll = QScrollArea(); self.fav_scroll.setWidgetResizable(True)
        self.fav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.fav_scroll.setFixedHeight(92); self.fav_scroll.setStyleSheet("background:transparent;border:none;")
        self.fav_ctr = QWidget(); self.fav_ctr.setStyleSheet("background:transparent;")
        self.fav_lay = QHBoxLayout(self.fav_ctr); self.fav_lay.setSpacing(6); self.fav_lay.setContentsMargins(0,0,0,0)
        self.fav_scroll.setWidget(self.fav_ctr); cl.addWidget(self.fav_scroll); cl.addSpacing(6)

        # Sabitlendi
        cl.addWidget(_section(tr("pinned"))); cl.addSpacing(4)
        self.pin_scroll = QScrollArea(); self.pin_scroll.setWidgetResizable(True)
        self.pin_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.pin_scroll.setFixedHeight(176); self.pin_scroll.setStyleSheet("background:transparent;border:none;")
        self.pin_ctr = QWidget(); self.pin_ctr.setStyleSheet("background:transparent;")
        self.pin_grid = QGridLayout(self.pin_ctr); self.pin_grid.setSpacing(2); self.pin_grid.setContentsMargins(0,0,0,0)
        self.pin_scroll.setWidget(self.pin_ctr); cl.addWidget(self.pin_scroll)

        # Nav
        nav = QHBoxLayout(); nav.addStretch()
        self.all_btn = QPushButton(tr("all_apps_btn")); self.all_btn.setFixedHeight(28)
        nav_qss = (f"QPushButton{{background:transparent;border:1px solid {led(0.22)};"
                   f"border-radius:8px;padding:0 12px;color:rgba(200,220,255,0.55);"
                   f"font-family:'Rajdhani','Segoe UI';font-size:12px;font-weight:600;letter-spacing:1px;}}"
                   f"QPushButton:hover{{background:{led(0.08)};color:{cfg['led_color']};border-color:{led(0.4)};}}")
        self.all_btn.setStyleSheet(nav_qss); self.all_btn.clicked.connect(self._toggle_all)
        qs_btn = QPushButton("⚙"); qs_btn.setFixedSize(28,28); qs_btn.setToolTip("Ayarlar")
        tl_btn = QPushButton("🛠"); tl_btn.setFixedSize(28,28); tl_btn.setToolTip("Araçlar")
        qs_btn.setStyleSheet(nav_qss); tl_btn.setStyleSheet(nav_qss)
        qs_btn.clicked.connect(self._open_qs); tl_btn.clicked.connect(self._open_tools)
        nav.addWidget(self.all_btn); nav.addSpacing(4)
        nav.addWidget(tl_btn); nav.addSpacing(4); nav.addWidget(qs_btn)
        cl.addSpacing(6); cl.addLayout(nav); cl.addSpacing(8)

        # Tüm uygulamalar paneli (skeleton ile başlar)
        self.all_panel = QWidget(); self.all_panel.hide()
        apl = QVBoxLayout(self.all_panel); apl.setContentsMargins(0,0,0,0); apl.setSpacing(4)
        apl.addWidget(_section(tr("all_apps")))
        self.all_scroll = QScrollArea(); self.all_scroll.setWidgetResizable(True)
        self.all_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.all_scroll.setFixedHeight(205); self.all_scroll.setStyleSheet("background:transparent;border:none;")
        self.all_ctr = QWidget(); self.all_ctr.setStyleSheet("background:transparent;")
        self.all_lay = QVBoxLayout(self.all_ctr); self.all_lay.setContentsMargins(0,0,0,0); self.all_lay.setSpacing(2)
        self._skeleton = SkeletonWidget(rows=4); self.all_lay.addWidget(self._skeleton); self.all_lay.addStretch()
        self.all_scroll.setWidget(self.all_ctr); apl.addWidget(self.all_scroll)
        cl.addWidget(self.all_panel)

        # Önerilen
        cl.addWidget(_section(tr("recommended"))); cl.addSpacing(4)
        self.rec_ctr = QWidget()
        self.rec_lay = QVBoxLayout(self.rec_ctr); self.rec_lay.setContentsMargins(0,0,0,0); self.rec_lay.setSpacing(2)
        cl.addWidget(self.rec_ctr); cl.addStretch()

        root.addWidget(c)

        # Footer
        footer = QWidget(); footer.setFixedHeight(48)
        footer.setStyleSheet(f"border-top:1px solid {led(0.1)};background:rgba(5,8,16,0.5);"
                             f"border-bottom-left-radius:20px;border-bottom-right-radius:20px;")
        fl = QHBoxLayout(footer); fl.setContentsMargins(16,6,16,6)
        av = QLabel(os.environ.get("USERNAME","U")[0].upper()); av.setFixedSize(34,34)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter); av.setFont(QFont("Orbitron",12,QFont.Weight.Bold))
        av.setStyleSheet(
            f"background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {cfg['led_color2']},stop:1 {cfg['led_color']});"
            f"border-radius:17px;color:white;border:1px solid {led(0.4)};")
        un = QLabel(os.environ.get("USERNAME","User")); un.setFont(QFont("Rajdhani",12,QFont.Weight.Medium))
        fl.addWidget(av); fl.addWidget(un); fl.addStretch()
        for ic, tip, dng, fn in [("🔒","Kilitle",False,self._lock),
                                  ("↺","Yeniden Başlat",False,self._restart),
                                  ("⏻","Kapat",True,self._shutdown)]:
            b = _icon_btn(ic,tip,dng); b.clicked.connect(fn); fl.addWidget(b)
        root.addWidget(footer)

    # ── Thread'ler ───────────────────────────────────────────────────────────
    def _setup_threads(self):
        self.sys_mon = SystemMonitor(); self.sys_mon.updated.connect(self.top_panel.update_sys); self.sys_mon.start()
        self.media   = MediaWatcher();  self.media.updated.connect(self.top_panel.update_music);   self.media.start()
        self.disk_mon= DiskNetMonitor();self.disk_mon.updated.connect(self.top_panel.update_disk_net);self.disk_mon.start()
        self.clip_w  = ClipboardWatcher(); self.clip_w.new_item.connect(self._on_clipboard); self.clip_w.start()
        self._fetch_weather()
        self._wx_t = QTimer(); self._wx_t.timeout.connect(self._fetch_weather); self._wx_t.start(600_000)
        if cfg["update_check"] and (time.time()-cfg["last_update_check"] > 86400):
            QTimer.singleShot(8000, self._bg_update_check)

    def _bg_update_check(self):
        self._upd = UpdateChecker(); self._upd.result.connect(self._on_bg_update); self._upd.start()

    def _on_bg_update(self, has, latest):
        cfg["last_update_check"] = time.time(); cfg.save()
        if has: self._toast(f"Yeni sürüm: v{latest}", "🆕")

    def _on_clipboard(self, text):
        if hasattr(self, '_clip_w') and self._clip_w: self._clip_w.add_item(text)
        # tools page'deki clipboard widget
        if hasattr(self, '_clip_widget') and self._clip_widget: self._clip_widget.add_item(text)

    def _fetch_weather(self):
        self._wx = WeatherFetcher(); self._wx.fetched.connect(self.top_panel.update_weather); self._wx.start()

    # ── Tray ─────────────────────────────────────────────────────────────────
    def _setup_tray(self):
        pm = QPixmap(16,16); pm.fill(QColor(0,0,0,0))
        p = QPainter(pm); p.setBrush(QBrush(QColor(cfg["led_color"])))
        p.setPen(__import__('PyQt6.QtCore',fromlist=['Qt']).Qt.PenStyle.NoPen)
        for x,y in [(1,1),(9,1),(1,9),(9,9)]: p.drawRoundedRect(x,y,6,6,1,1)
        p.end()
        self.tray = QSystemTrayIcon(QIcon(pm), self); self.tray.setToolTip("NEXUS Start — Ctrl+Space")
        self.tray.activated.connect(lambda r: self._toggle() if r==QSystemTrayIcon.ActivationReason.DoubleClick else None)
        m = QMenu()
        m.addAction("▶  Aç/Kapat").triggered.connect(self._toggle)
        m.addAction("📂  Shortcut Klasörü").triggered.connect(lambda: subprocess.Popen(f'explorer "{SHORTCUTS_DIR}"'))
        m.addAction("⚙  Ayarlar").triggered.connect(lambda: (self._show(), self._open_qs()))
        m.addSeparator(); m.addAction("✕  Çıkış").triggered.connect(QApplication.quit)
        self.tray.setContextMenu(m); self.tray.show()

    # ── Hotkey ───────────────────────────────────────────────────────────────
    def _setup_hotkey(self):
        try:
            ctypes.windll.user32.RegisterHotKey(None, 1, cfg["hotkey_mod"], cfg["hotkey_vk"])
            self._hkt = QTimer(); self._hkt.timeout.connect(self._poll_hk); self._hkt.start(50)
        except Exception:
            pass

    def _poll_hk(self):
        msg = ctypes.wintypes.MSG()
        if ctypes.windll.user32.PeekMessageW(ctypes.byref(msg), None, 0x0312, 0x0312, 1):
            self._toggle()

    # ── Uygulama tarama ──────────────────────────────────────────────────────
    def _scan_apps(self):
        self._sc = ShortcutScanner(); self._sc.found.connect(self._on_apps); self._sc.start()

    @pyqtSlot(list)
    def _on_apps(self, apps):
        self.all_apps = apps
        if hasattr(self, '_fold_w') and self._fold_w:
            self._fold_w.update_apps(apps)
        self._rebuild_favs(); self._rebuild_pins()
        self._rebuild_all(apps); self._rebuild_rec()
        if hasattr(self, '_skeleton'): self._skeleton.stop(); self._skeleton.hide()

    # ── Rebuild ──────────────────────────────────────────────────────────────
    def _rebuild_favs(self):
        while self.fav_lay.count():
            it = self.fav_lay.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        favs = dm.get_favorites()
        if not favs:
            lbl = QLabel("★ Sağ tıkla → Favorilere Ekle")
            lbl.setFont(QFont("Rajdhani",10)); lbl.setStyleSheet("color:rgba(200,220,255,0.22);")
            self.fav_lay.addWidget(lbl); self.fav_lay.addStretch(); return
        for app in favs[:8]:
            t = AppTile(app, 8); t.clicked.connect(self._launch)
            t.pin_toggle.connect(self._toggle_pin); t.kill_sig.connect(self._kill)
            self.fav_lay.addWidget(t)
        self.fav_lay.addStretch()

    def _rebuild_pins(self):
        while self.pin_grid.count():
            it = self.pin_grid.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        src = dm.get_pins() or self.all_apps[:12]
        for i, app in enumerate(src[:12]):
            t = AppTile(app); t.clicked.connect(self._launch)
            t.pin_toggle.connect(self._toggle_pin); t.kill_sig.connect(self._kill)
            self.pin_grid.addWidget(t, i//6, i%6)

    def _rebuild_all(self, apps):
        while self.all_lay.count():
            it = self.all_lay.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        for app in apps: self.all_lay.addWidget(self._list_row(app))
        self.all_lay.addStretch()

    def _list_row(self, app):
        w = QWidget(); w.setFixedHeight(44); w.setCursor(Qt.CursorShape.PointingHandCursor)
        hl = QHBoxLayout(w); hl.setContentsMargins(8,4,8,4); hl.setSpacing(10)
        ic = _icon_label(app, 30)
        disp = dm.get_alias(app.get("path","")) or app["name"]
        nm = QLabel(disp); nm.setFont(QFont("Rajdhani",12,QFont.Weight.Medium))
        tag = app.get("tag","")
        tl = QLabel(f" #{tag}" if tag else ""); tl.setFont(QFont("Rajdhani",10))
        tl.setStyleSheet(f"color:{led(0.6)};")
        hl.addWidget(ic); hl.addWidget(nm); hl.addWidget(tl); hl.addStretch()
        w.enterEvent = lambda e: w.setStyleSheet(f"background:{led(0.07)};border-radius:9px;")
        w.leaveEvent = lambda e: w.setStyleSheet("")
        w.mousePressEvent = lambda e, a=app: self._launch(a) if e.button()==Qt.MouseButton.LeftButton else None
        return w

    def _rebuild_rec(self):
        while self.rec_lay.count():
            it = self.rec_lay.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        recent = dm.get_recent(6)
        if not recent:
            lb = QLabel(tr("no_recent")); lb.setStyleSheet("color:rgba(200,220,255,0.3);font-size:12px;padding:8px;")
            self.rec_lay.addWidget(lb); return
        g = QGridLayout(); g.setSpacing(2)
        for i, app in enumerate(recent[:6]):
            r = RecentRow(app); r.clicked.connect(self._launch); g.addWidget(r, i//2, i%2)
        ctr = QWidget(); ctr.setLayout(g); self.rec_lay.addWidget(ctr)

    # ── Arama ────────────────────────────────────────────────────────────────
    def _on_search(self, text):
        q = text.strip().lower()
        if not q:
            self._rebuild_pins(); self._rebuild_favs()
            self.all_panel.hide(); self.rec_ctr.show(); self.all_btn.show(); return
        hits = [a for a in self.all_apps if q in a["name"].lower()]
        while self.pin_grid.count():
            it = self.pin_grid.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        for i, app in enumerate(hits[:12]):
            t = AppTile(app); t.clicked.connect(self._launch); self.pin_grid.addWidget(t, i//6, i%6)
        if self._fs_thread and self._fs_thread.isRunning(): self._fs_thread.terminate()
        self._fs_thread = FileSearchThread(q); self._fs_thread.results.connect(self._on_files); self._fs_thread.start()
        self.rec_ctr.show(); self.all_panel.hide()

    def _on_files(self, files):
        while self.rec_lay.count():
            it = self.rec_lay.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        if not files: return
        lb = QLabel(tr("files")); lb.setFont(QFont("Orbitron",7,QFont.Weight.Bold))
        lb.setStyleSheet(f"color:{led(0.7)};letter-spacing:2px;")
        self.rec_lay.addWidget(lb)
        for f in files[:6]:
            r = RecentRow(f); r.clicked.connect(lambda a: subprocess.Popen(f'explorer /select,"{a["path"]}"'))
            self.rec_lay.addWidget(r)

    # ── Eylemler ─────────────────────────────────────────────────────────────
    def _toggle_all(self):
        if self.all_panel.isHidden():
            self.all_panel.show(); self.rec_ctr.hide(); self.all_btn.setText(tr("back"))
        else:
            self.all_panel.hide(); self.rec_ctr.show(); self.all_btn.setText(tr("all_apps_btn"))

    def _toggle_focus(self):
        cfg["focus_mode"] = not cfg["focus_mode"]
        on = cfg["focus_mode"]
        self.focus_btn.setText(f"🎯 Odak {'AÇIK' if on else 'Kapalı'}")
        self._toast("Odak modu açıldı" if on else "Odak modu kapandı", "🎯")

    def _toggle_dnd(self):
        cfg["dnd_mode"] = not cfg["dnd_mode"]
        on = cfg["dnd_mode"]
        self.dnd_btn.setText(f"🔕 DnD {'AÇIK' if on else 'Kapalı'}")
        self._toast("Rahatsız etme modu açıldı" if on else "Kapandı", "🔕")

    def _open_qs(self):    self.stack.setCurrentIndex(1)
    def _open_tools(self): self.stack.setCurrentIndex(2)

    def _close_qs(self):
        self.stack.setCurrentIndex(0); self._apply_page_style()
        if hasattr(self, '_night'): self._night.setVisible(cfg["night_sky"])
        self._fetch_weather()

    def _launch(self, app):
        try:
            subprocess.Popen(app["path"], shell=True)
            dm.record_launch(app["path"], app["name"], app.get("icon_path",""))
            self._rebuild_rec()
        except Exception as ex:
            self._toast(str(ex), "⚠️")
        if not cfg.get("focus_mode"): self._hide_anim()

    def _toggle_pin(self, app):
        if dm.is_pinned(app["path"]): dm.unpin_app(app["path"])
        else: dm.pin_app(app["path"], app["name"], app.get("icon_path",""))
        self._rebuild_pins()

    def _kill(self, app):
        try:
            subprocess.call(["taskkill","/F","/IM",Path(app["path"]).name], creationflags=0x08000000)
            self._toast(f"{app['name']} sonlandırıldı.", "✕")
        except Exception as ex:
            self._toast(str(ex), "⚠️")

    def _toast(self, message, icon="ℹ️"):
        if cfg.get("dnd_mode"): return
        ToastNotification(self.main_page, message, icon)

    # ── Göster / Gizle ───────────────────────────────────────────────────────
    def _toggle(self):
        if self.isVisible(): self._hide_anim()
        else: self._show()

    def _show(self):
        scr = QGuiApplication.primaryScreen().geometry()
        self.setGeometry((scr.width()-MENU_W)//2, scr.height()-MENU_H-62, MENU_W, MENU_H)
        self.search.clear(); self._scan_apps()
        self.greet_lbl.setText(_greet() + f", {os.environ.get('USERNAME','Kullanıcı')}!")
        self._fade.show_anim()
        self.raise_(); self.activateWindow(); self.search.setFocus()

    def _hide_anim(self):
        self._fade.hide_anim()

    # ── Olaylar ──────────────────────────────────────────────────────────────
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._ripple.trigger(e.position().toPoint())
        super().mousePressEvent(e)

    def focusOutEvent(self, e):
        if cfg["auto_hide"]: self._hide_anim()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape: self._hide_anim()
        elif e.key() in (Qt.Key.Key_Up,Qt.Key.Key_Down,Qt.Key.Key_Left,Qt.Key.Key_Right):
            self.search.setFocus()
        else: super().keyPressEvent(e)

    def _lock(self):     ctypes.windll.user32.LockWorkStation(); self._hide_anim()
    def _restart(self):  subprocess.call(["shutdown","/r","/t","5"]); self._hide_anim()
    def _shutdown(self): subprocess.call(["shutdown","/s","/t","5"]); self._hide_anim()

    def closeEvent(self, e):
        for thr in (getattr(self,'sys_mon',None), getattr(self,'media',None),
                    getattr(self,'disk_mon',None), getattr(self,'clip_w',None)):
            if thr: thr.stop(); thr.wait(800)
        super().closeEvent(e)


# ─────────────────────────────────────────────────────────────────────────────
# GİRİŞ NOKTASI
# ─────────────────────────────────────────────────────────────────────────────
def main():
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window,          QColor(5,8,16))
    pal.setColor(QPalette.ColorRole.WindowText,      QColor(232,244,255))
    pal.setColor(QPalette.ColorRole.Base,            QColor(8,13,26))
    pal.setColor(QPalette.ColorRole.Text,            QColor(232,244,255))
    pal.setColor(QPalette.ColorRole.Highlight,       QColor(cfg["led_color"]))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(255,255,255))
    app.setPalette(pal)
    win = NexusStart()
    QTimer.singleShot(1500, lambda: win.tray.showMessage(
        "NEXUS Start v3.0",
        "Ctrl+Space ile aç  |  🛠 81 yeni özellik!",
        QSystemTrayIcon.MessageIcon.Information, 4500))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
