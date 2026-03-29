"""
settings_panel.py — Hızlı Ayarlar & Araçlar sekme paneli | NexusStart v3.0
"""

import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QCheckBox, QTabWidget, QSlider, QMessageBox, QFileDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QColorDialog

class QuickSettings(QWidget):
    closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        from config import cfg, led, _section, _icon_btn, _inp_qss, _btn_qss, tr
        lay = QVBoxLayout(self); lay.setContentsMargins(20,16,20,12); lay.setSpacing(10)

        hdr = QHBoxLayout()
        title = QLabel(tr("settings")); title.setFont(QFont("Orbitron",10,QFont.Weight.Bold))
        title.setStyleSheet(f"color:{cfg['led_color']};letter-spacing:2px;")
        back = _icon_btn("←", "Geri"); back.clicked.connect(self.closed.emit)
        hdr.addWidget(title); hdr.addStretch(); hdr.addWidget(back)
        lay.addLayout(hdr)

        tabs = QTabWidget(); tabs.setFont(QFont("Rajdhani",10))
        tabs.setStyleSheet(
            f"QTabWidget::pane{{border:1px solid {led(0.15)};border-radius:10px;"
            f"background:rgba(8,13,26,0.6);}}"
            f"QTabBar::tab{{background:{led(0.05)};color:rgba(200,220,255,0.55);"
            f"padding:6px 10px;border-radius:6px;font-family:'Rajdhani';font-size:11px;margin-right:3px;}}"
            f"QTabBar::tab:selected{{background:{led(0.15)};color:{cfg['led_color']};}}"
            f"QTabBar::tab:hover{{background:{led(0.1)};}}")

        # ── TEMA ──────────────────────────────────────────────────────────────
        tema = QWidget(); tl = QVBoxLayout(tema); tl.setContentsMargins(12,10,12,10); tl.setSpacing(10)

        tl.addWidget(_section("LED RENGİ"))
        row_c = QHBoxLayout(); row_c.setSpacing(6)
        presets = [("#00aaff","#006aff","Mavi"),("#00ffaa","#006655","Yeşil"),
                   ("#ff4488","#aa0044","Pembe"),("#aa44ff","#6600cc","Mor"),
                   ("#ff8800","#cc4400","Turuncu"),("#ff2222","#aa0000","Kırmızı")]
        for c1,c2,nm in presets:
            pb = QPushButton(); pb.setFixedSize(22,22); pb.setToolTip(nm)
            pb.setStyleSheet(f"background:{c1};border-radius:11px;border:2px solid rgba(255,255,255,0.15);")
            pb.clicked.connect(lambda _=None,a=c1,b=c2: self._preset(a,b))
            row_c.addWidget(pb)
        row_c.addSpacing(8)
        lbl1 = QLabel("Ana:"); lbl1.setFont(QFont("Rajdhani",11))
        self.prev1 = QPushButton(); self.prev1.setFixedSize(26,26); self._upd1()
        self.prev1.clicked.connect(self._pick1)
        lbl2 = QLabel("İkincil:"); lbl2.setFont(QFont("Rajdhani",11))
        self.prev2 = QPushButton(); self.prev2.setFixedSize(26,26); self._upd2()
        self.prev2.clicked.connect(self._pick2)
        row_c.addStretch(); row_c.addWidget(lbl1); row_c.addWidget(self.prev1)
        row_c.addWidget(lbl2); row_c.addWidget(self.prev2)
        tl.addLayout(row_c)

        tl.addWidget(_section("GÖRÜNÜM"))
        chk_row = QHBoxLayout(); chk_row.setSpacing(10)
        self.chk_neon  = self._chk("✨ Neon Glow",   cfg["neon_glow"])
        self.chk_night = self._chk("🌃 Gece Gökyüzü", cfg["night_sky"])
        self.chk_anim  = self._chk("▶ Açılış Anim.", cfg["open_anim"])
        for cb in (self.chk_neon, self.chk_night, self.chk_anim):
            chk_row.addWidget(cb)
        chk_row.addStretch(); tl.addLayout(chk_row)

        tl.addWidget(_section("SAYDAMLIK"))
        op_row = QHBoxLayout(); op_row.setSpacing(8)
        self.op_sl = QSlider(Qt.Orientation.Horizontal)
        self.op_sl.setRange(50,100); self.op_sl.setValue(cfg["bg_opacity"])
        self.op_sl.setStyleSheet(
            f"QSlider::groove:horizontal{{height:4px;background:{led(0.15)};border-radius:2px;}}"
            f"QSlider::handle:horizontal{{width:14px;height:14px;margin:-5px 0;"
            f"background:{cfg['led_color']};border-radius:7px;}}"
            f"QSlider::sub-page:horizontal{{background:{cfg['led_color']};border-radius:2px;}}")
        self.op_lbl = QLabel(f"{cfg['bg_opacity']}%"); self.op_lbl.setFixedWidth(32)
        self.op_lbl.setFont(QFont("Rajdhani",11)); self.op_lbl.setStyleSheet(f"color:{cfg['led_color']};")
        self.op_sl.valueChanged.connect(lambda v: self.op_lbl.setText(f"{v}%"))
        op_row.addWidget(self.op_sl,1); op_row.addWidget(self.op_lbl); tl.addLayout(op_row)

        tl.addWidget(_section("İKON BOYUTU"))
        sz_row = QHBoxLayout(); sz_row.setSpacing(8)
        lsz = QLabel("Boyut:"); lsz.setFont(QFont("Rajdhani",11))
        self.sz_cb = QComboBox(); self.sz_cb.addItems(["Küçük","Orta","Büyük"])
        self.sz_cb.setCurrentIndex({"small":0,"medium":1,"large":2}.get(cfg["icon_size"],1))
        self.sz_cb.setStyleSheet(_inp_qss()+"QComboBox{height:28px;}")
        sz_row.addWidget(lsz); sz_row.addWidget(self.sz_cb); sz_row.addStretch(); tl.addLayout(sz_row)

        tl.addWidget(_section("DİL"))
        lang_row = QHBoxLayout(); lang_row.setSpacing(8)
        llang = QLabel("Dil:"); llang.setFont(QFont("Rajdhani",11))
        self.lang_cb = QComboBox(); self.lang_cb.addItems(["Türkçe","English"])
        self.lang_cb.setCurrentIndex(0 if cfg["language"]=="tr" else 1)
        self.lang_cb.setStyleSheet(_inp_qss()+"QComboBox{height:28px;}")
        lang_row.addWidget(llang); lang_row.addWidget(self.lang_cb); lang_row.addStretch(); tl.addLayout(lang_row)
        tl.addStretch(); tabs.addTab(tema, "🎨 Tema")

        # ── SİSTEM ────────────────────────────────────────────────────────────
        sys_w = QWidget(); sl = QVBoxLayout(sys_w); sl.setContentsMargins(12,10,12,10); sl.setSpacing(10)

        sl.addWidget(_section("HAVA DURUMU"))
        wx_row = QHBoxLayout(); wx_row.setSpacing(8)
        lc = QLabel("Şehir:"); lc.setFont(QFont("Rajdhani",12))
        self.city_inp = QLineEdit(cfg["weather_city"]); self.city_inp.setFixedHeight(30)
        self.city_inp.setStyleSheet(_inp_qss())
        lu = QLabel("Birim:"); lu.setFont(QFont("Rajdhani",12))
        self.unit_cb = QComboBox(); self.unit_cb.addItems(["°C","°F"])
        self.unit_cb.setCurrentIndex(0 if cfg["weather_unit"]=="metric" else 1)
        self.unit_cb.setStyleSheet(_inp_qss()+"QComboBox{height:30px;}")
        wx_row.addWidget(lc); wx_row.addWidget(self.city_inp,1)
        wx_row.addWidget(lu); wx_row.addWidget(self.unit_cb); sl.addLayout(wx_row)

        sl.addWidget(_section("GÖSTER"))
        vis_row = QHBoxLayout(); vis_row.setSpacing(12)
        self.chk_cpu = self._chk("CPU/RAM",  cfg["show_cpu"])
        self.chk_wx  = self._chk("Hava",     cfg["show_weather"])
        self.chk_mus = self._chk("Müzik",    cfg["show_music"])
        vis_row.addWidget(self.chk_cpu); vis_row.addWidget(self.chk_wx)
        vis_row.addWidget(self.chk_mus); vis_row.addStretch(); sl.addLayout(vis_row)

        sl.addWidget(_section("SİSTEM İŞLEMLERİ"))
        sys_row = QHBoxLayout(); sys_row.setSpacing(6)
        for label, fn in [("📷 Duvar Kağıdı", self._pick_wp),
                           ("🚀 Başlangıca Ekle", self._startup),
                           ("🔔 Güncelleme Kontrol", self._check_update)]:
            b = QPushButton(label); b.setFixedHeight(28); b.setStyleSheet(_btn_qss())
            b.clicked.connect(fn); sys_row.addWidget(b)
        sys_row.addStretch(); sl.addLayout(sys_row)

        sl.addWidget(_section("YEDEKLEME"))
        bk_row = QHBoxLayout(); bk_row.setSpacing(6)
        bk_e = QPushButton("⬆ Dışa Aktar"); bk_e.setFixedHeight(26); bk_e.setStyleSheet(_btn_qss())
        bk_e.clicked.connect(self._export)
        bk_i = QPushButton("⬇ İçe Aktar"); bk_i.setFixedHeight(26); bk_i.setStyleSheet(_btn_qss())
        bk_i.clicked.connect(self._import)
        bk_row.addWidget(bk_e); bk_row.addWidget(bk_i); bk_row.addStretch(); sl.addLayout(bk_row)
        sl.addStretch(); tabs.addTab(sys_w, "⚙ Sistem")

        lay.addWidget(tabs)

        save = QPushButton("Kaydet & Uygula"); save.setFixedHeight(36)
        save.setStyleSheet(
            f"QPushButton{{background:{led(0.15)};border:1px solid {led(0.4)};"
            f"border-radius:10px;color:{cfg['led_color']};font-size:13px;"
            f"font-family:'Rajdhani';font-weight:600;letter-spacing:1px;}}"
            f"QPushButton:hover{{background:{led(0.25)};}}")
        save.clicked.connect(self._save); lay.addWidget(save)

    # ── helpers ───────────────────────────────────────────────────────────────
    def _chk(self, text, state):
        from config import led, cfg
        cb = QCheckBox(text); cb.setChecked(state); cb.setFont(QFont("Rajdhani",11))
        cb.setStyleSheet(
            f"QCheckBox{{color:#e8f4ff;spacing:6px;}}"
            f"QCheckBox::indicator{{width:14px;height:14px;border-radius:3px;"
            f"border:1px solid {led(0.35)};background:transparent;}}"
            f"QCheckBox::indicator:checked{{background:{cfg['led_color']};border-color:{cfg['led_color']};}}")
        return cb

    def _upd1(self):
        from config import cfg
        self.prev1.setStyleSheet(f"background:{cfg['led_color']};border-radius:8px;border:none;")
    def _upd2(self):
        from config import cfg
        self.prev2.setStyleSheet(f"background:{cfg['led_color2']};border-radius:8px;border:none;")
    def _pick1(self):
        from config import cfg
        c = QColorDialog.getColor(QColor(cfg["led_color"]),self,"Ana Renk")
        if c.isValid(): cfg["led_color"]=c.name(); self._upd1()
    def _pick2(self):
        from config import cfg
        c = QColorDialog.getColor(QColor(cfg["led_color2"]),self,"İkincil Renk")
        if c.isValid(): cfg["led_color2"]=c.name(); self._upd2()
    def _preset(self, c1, c2):
        from config import cfg
        cfg["led_color"]=c1; cfg["led_color2"]=c2; self._upd1(); self._upd2()

    def _pick_wp(self):
        from config import cfg
        f,_ = QFileDialog.getOpenFileName(self,"Duvar Kağıdı","","Resimler (*.png *.jpg *.jpeg *.bmp)")
        if f: cfg["wallpaper"]=f

    def _startup(self):
        from config import cfg
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",0,winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key,"NexusStart",0,winreg.REG_SZ,f'"{sys.executable}" "{__file__}"')
            winreg.CloseKey(key)
            QMessageBox.information(self,"Başlangıç","Windows başlangıcına eklendi ✓")
        except Exception as e:
            QMessageBox.warning(self,"Hata",str(e))

    def _check_update(self):
        from threads import UpdateChecker
        self._upd = UpdateChecker()
        self._upd.result.connect(lambda has, v:
            QMessageBox.information(self,"Güncelleme",
                f"Yeni sürüm mevcut: v{v}" if has else "Güncelsiniz ✓"))
        self._upd.start()

    def _export(self):
        from config import cfg
        path = cfg.export_backup()
        QMessageBox.information(self,"Yedekleme",f"Dışa aktarıldı:\n{path}")

    def _import(self):
        from config import cfg, BACKUP_DIR
        f,_ = QFileDialog.getOpenFileName(self,"Yedek Yükle",str(BACKUP_DIR),"JSON (*.json)")
        if f:
            try:
                cfg.import_backup(f)
                QMessageBox.information(self,"İçe Aktarma","Yüklendi. Yeniden başlatın.")
            except Exception as e:
                QMessageBox.warning(self,"Hata",str(e))

    def _save(self):
        from config import cfg
        cfg["weather_city"]  = self.city_inp.text().strip() or "Istanbul"
        cfg["weather_unit"]  = "metric" if self.unit_cb.currentIndex()==0 else "imperial"
        cfg["show_cpu"]      = self.chk_cpu.isChecked()
        cfg["show_weather"]  = self.chk_wx.isChecked()
        cfg["show_music"]    = self.chk_mus.isChecked()
        cfg["neon_glow"]     = self.chk_neon.isChecked()
        cfg["night_sky"]     = self.chk_night.isChecked()
        cfg["open_anim"]     = self.chk_anim.isChecked()
        cfg["bg_opacity"]    = self.op_sl.value()
        cfg["icon_size"]     = ["small","medium","large"][self.sz_cb.currentIndex()]
        cfg["language"]      = "tr" if self.lang_cb.currentIndex()==0 else "en"
        cfg.save(); self.closed.emit()
