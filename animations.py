"""
animations.py — Tüm animasyon ve görsel efekt sınıfları | NexusStart v3.0

İçerik:
  FadeScaleAnimation   — Açılış/kapanış fade efekti
  RippleOverlay        — Tıklama ripple dalgası
  LedPulseWidget       — LED kenar nabız animasyonu
  MusicBarsWidget      — Müzik çubuğu animasyonu
  AnalogClockWidget    — Analog saat widget'i
  SkeletonWidget       — Yükleme iskelet efekti
  NightSkyWidget       — Gece gökyüzü yıldız arka planı
  StarBurstOverlay     — Pin yıldız patlaması
  ToastNotification    — Köşeden süzülen bildirim popup'ı
"""

import math, random
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QApplication
from PyQt6.QtCore import (Qt, QTimer, QPropertyAnimation, QEasingCurve,
                           QPoint, QByteArray)
from PyQt6.QtGui import QColor, QFont, QPainter, QPen


# ─────────────────────────────────────────────────────────────────────────────
# 1. AÇILIŞ / KAPANIŞ ANIMASYONU (fade + scale)
# ─────────────────────────────────────────────────────────────────────────────
class FadeScaleAnimation:
    """Menü açılırken fade-in, kapanırken fade-out."""

    def __init__(self, widget):
        self.w = widget

    def show_anim(self, duration=280):
        from config import cfg
        if not cfg["open_anim"]:
            self.w.show(); return
        self.w.setWindowOpacity(0.0)
        self.w.show()
        self._anim = QPropertyAnimation(self.w, QByteArray(b"windowOpacity"))
        self._anim.setDuration(duration)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    def hide_anim(self, done_cb=None, duration=200):
        from config import cfg
        if not cfg["open_anim"]:
            self.w.hide()
            if done_cb: done_cb()
            return
        self._anim2 = QPropertyAnimation(self.w, QByteArray(b"windowOpacity"))
        self._anim2.setDuration(duration)
        self._anim2.setStartValue(1.0)
        self._anim2.setEndValue(0.0)
        self._anim2.setEasingCurve(QEasingCurve.Type.InCubic)
        def _done():
            self.w.hide(); self.w.setWindowOpacity(1.0)
            if done_cb: done_cb()
        self._anim2.finished.connect(_done)
        self._anim2.start()


# ─────────────────────────────────────────────────────────────────────────────
# 2. RİPPLE EFEKTİ
# ─────────────────────────────────────────────────────────────────────────────
class RippleOverlay(QWidget):
    """Mouse tıklamasında yayılan halka animasyonu."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._circles = []          # [cx, cy, radius, alpha]
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def trigger(self, pos):
        self._circles.append([pos.x(), pos.y(), 0, 200])
        if not self._timer.isActive():
            self._timer.start(14)

    def _tick(self):
        alive = []
        for c in self._circles:
            c[2] += 9; c[3] -= 12
            if c[3] > 0: alive.append(c)
        self._circles = alive
        self.update()
        if not self._circles: self._timer.stop()

    def paintEvent(self, e):
        from config import cfg
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        lc = QColor(cfg["led_color"])
        for cx, cy, r, a in self._circles:
            lc.setAlpha(max(0, a))
            p.setPen(QPen(lc, 1.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(int(cx-r), int(cy-r), int(r*2), int(r*2))
        p.end()


# ─────────────────────────────────────────────────────────────────────────────
# 3. LED NABIZ ANIMASYONU
# ─────────────────────────────────────────────────────────────────────────────
class LedPulseWidget(QWidget):
    """Menü üst kenarında nefes alır gibi yanan ince çizgi."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(2)
        self._phase = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)

    def _tick(self):
        self._phase = (self._phase + 0.04) % (2 * math.pi)
        self.update()

    def paintEvent(self, e):
        from config import cfg
        p = QPainter(self)
        a = 0.5 + 0.5 * math.sin(self._phase)
        lc = QColor(cfg["led_color"]); lc.setAlphaF(0.3 + 0.65 * a)
        p.fillRect(self.rect(), lc)
        p.end()


# ─────────────────────────────────────────────────────────────────────────────
# 4. MÜZİK ÇUBUĞU ANIMASYONU
# ─────────────────────────────────────────────────────────────────────────────
class MusicBarsWidget(QWidget):
    """Müzik çalarken 5 bar animasyonu (ses dalgası)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(34, 20)
        self._playing = False
        self._h = [0.3] * 5
        self._t = [0.3] * 5
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(80)

    def set_playing(self, playing: bool):
        self._playing = playing

    def _tick(self):
        if self._playing:
            self._t = [random.uniform(0.15, 1.0) for _ in range(5)]
        else:
            self._t = [0.15] * 5
        for i in range(5):
            self._h[i] += (self._t[i] - self._h[i]) * 0.35
        self.update()

    def paintEvent(self, e):
        from config import cfg
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        lc = QColor(cfg["led_color"])
        bw, gap = 4, 2
        for i, h in enumerate(self._h):
            bh = max(2, int(self.height() * h))
            x = i * (bw + gap)
            y = self.height() - bh
            lc.setAlphaF(0.5 + 0.5 * h)
            p.fillRect(x, y, bw, bh, lc)
        p.end()


# ─────────────────────────────────────────────────────────────────────────────
# 5. ANALOG SAAT
# ─────────────────────────────────────────────────────────────────────────────
class AnalogClockWidget(QWidget):
    """Küçük, şık analog saat widget'i."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(1000)

    def paintEvent(self, e):
        from config import cfg
        from datetime import datetime as dt
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        now = dt.now()
        cx = cy = self.width() // 2
        r = cx - 4
        bg = QColor(10, 16, 32, 200)
        p.setBrush(bg)
        p.setPen(QPen(QColor(cfg["led_color"]), 1.5))
        p.drawEllipse(cx-r, cy-r, r*2, r*2)

        def hand(deg, length, width, color):
            rad = math.radians(deg - 90)
            x = cx + length * math.cos(rad)
            y = cy + length * math.sin(rad)
            pen = QPen(color, width, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawLine(cx, cy, int(x), int(y))

        lc = QColor(cfg["led_color"])
        hand((now.hour % 12 + now.minute/60) * 30, r*0.50, 2.5, lc)
        hand((now.minute + now.second/60) * 6,       r*0.72, 1.8, lc)
        sc = QColor("#ff4488"); sc.setAlphaF(0.9)
        hand(now.second * 6,                          r*0.84, 1.0, sc)
        p.setBrush(lc); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(cx-3, cy-3, 6, 6)
        p.end()


# ─────────────────────────────────────────────────────────────────────────────
# 6. SKELETON LOADING
# ─────────────────────────────────────────────────────────────────────────────
class SkeletonWidget(QWidget):
    """Uygulama listesi yüklenirken gösterilen tarama efektli yer tutucu."""

    def __init__(self, parent=None, rows=4, row_h=44):
        super().__init__(parent)
        self._phase = 0.0
        self._rows = rows; self._rh = row_h
        self.setFixedHeight(rows * (row_h + 6))
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)

    def _tick(self):
        self._phase = (self._phase + 0.04) % 2.0
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = max(0.0, min(1.0, abs(self._phase - 1.0)))
        base = QColor(14, 22, 45)
        hi   = QColor(30, 50, 95)
        mix  = QColor(
            int(base.red()   + (hi.red()  - base.red())  * t),
            int(base.green() + (hi.green()- base.green())* t),
            int(base.blue()  + (hi.blue() - base.blue()) * t),
        )
        for i in range(self._rows):
            y = i * (self._rh + 6)
            p.setBrush(mix); p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(0, y+4, 36, 36, 6, 6)
            p.drawRoundedRect(44, y+8,  int((self.width()-60)*0.6), 12, 4, 4)
            p.drawRoundedRect(44, y+26, int((self.width()-60)*0.35), 10, 4, 4)
        p.end()

    def stop(self):
        self._timer.stop()


# ─────────────────────────────────────────────────────────────────────────────
# 7. GECE GÖKYÜZÜ
# ─────────────────────────────────────────────────────────────────────────────
class NightSkyWidget(QWidget):
    """Arka planda yavaşça titreyerek parlayan yıldızlar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._stars = [
            (random.randint(0, 800), random.randint(0, 1000),
             random.uniform(0.2, 1.0), random.uniform(0, math.pi*2))
            for _ in range(130)
        ]
        self._phase = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(60)

    def _tick(self):
        self._phase += 0.02; self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        for x, y, bri, off in self._stars:
            a = bri * (0.5 + 0.5 * math.sin(self._phase + off))
            c = QColor(200, 220, 255); c.setAlphaF(a * 0.7)
            sz = 1.5 if bri > 0.7 else 1.0
            p.fillRect(int(x % self.width()), int(y % self.height()),
                       int(sz), int(sz), c)
        p.end()


# ─────────────────────────────────────────────────────────────────────────────
# 8. PIN YILDIZ PATLAMASI
# ─────────────────────────────────────────────────────────────────────────────
class StarBurstOverlay(QWidget):
    """Uygulama sabitlenince yıldız parçacık patlaması."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._particles = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def burst(self, cx, cy):
        self._particles = []
        for _ in range(16):
            angle = random.uniform(0, math.pi*2)
            speed = random.uniform(2, 7)
            self._particles.append({
                "x": float(cx), "y": float(cy),
                "vx": math.cos(angle)*speed,
                "vy": math.sin(angle)*speed,
                "life": 1.0, "size": random.uniform(2, 5),
            })
        self.resize(self.parent().size())
        self.show(); self._timer.start(16)

    def _tick(self):
        for pt in self._particles:
            pt["x"] += pt["vx"]; pt["y"] += pt["vy"]
            pt["vy"] += 0.3; pt["life"] -= 0.045
        self._particles = [p for p in self._particles if p["life"] > 0]
        self.update()
        if not self._particles: self._timer.stop(); self.hide()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        lc = QColor("#ffcc00")
        for pt in self._particles:
            lc.setAlphaF(pt["life"])
            p.setBrush(lc); p.setPen(Qt.PenStyle.NoPen)
            s = pt["size"] * pt["life"]
            p.drawEllipse(int(pt["x"]-s/2), int(pt["y"]-s/2), int(s), int(s))
        p.end()


# ─────────────────────────────────────────────────────────────────────────────
# 9. TOAST BİLDİRİM
# ─────────────────────────────────────────────────────────────────────────────
class ToastNotification(QWidget):
    """Ekranın sağ altından kayarak gelen, otomatik kapanan bildirim."""

    def __init__(self, parent, message, icon="ℹ️", duration=3000):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.SubWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(300, 52)

        from config import led, cfg
        lay = QHBoxLayout(self); lay.setContentsMargins(12,8,12,8); lay.setSpacing(10)
        ic = QLabel(icon); ic.setFont(QFont("Segoe UI Emoji", 14))
        msg = QLabel(message); msg.setFont(QFont("Rajdhani", 12))
        msg.setStyleSheet("color:#e8f4ff;"); msg.setWordWrap(True)
        lay.addWidget(ic); lay.addWidget(msg, 1)
        self.setStyleSheet(f"QWidget{{background:rgba(8,13,26,0.95);border-radius:12px;"
                           f"border:1px solid {led(0.35)};}}")

        pr = parent.rect()
        start_x = pr.width() + 20
        end_x   = pr.width() - 318
        end_y   = pr.height() - 80
        self.move(start_x, end_y); self.show(); self.raise_()

        self._in = QPropertyAnimation(self, QByteArray(b"pos"))
        self._in.setDuration(360)
        self._in.setStartValue(QPoint(start_x, end_y))
        self._in.setEndValue(QPoint(end_x, end_y))
        self._in.setEasingCurve(QEasingCurve.Type.OutBack)
        self._in.start()

        QTimer.singleShot(duration, self._dismiss)

    def _dismiss(self):
        self._out = QPropertyAnimation(self, QByteArray(b"pos"))
        self._out.setDuration(250)
        self._out.setStartValue(self.pos())
        self._out.setEndValue(QPoint(self.parent().width()+20, self.pos().y()))
        self._out.setEasingCurve(QEasingCurve.Type.InCubic)
        self._out.finished.connect(self.deleteLater)
        self._out.start()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        super().paintEvent(e)
