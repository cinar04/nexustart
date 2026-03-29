"""
threads.py — Arka plan thread'leri | NexusStart v3.0

İçerik:
  ShortcutScanner    — Windows kısayollarını tarar
  SystemMonitor      — CPU / RAM izler
  DiskNetMonitor     — Disk, ağ hızı, pil izler
  WeatherFetcher     — Hava durumu + 5 günlük tahmin + güneş saati
  MediaWatcher       — Çalan müzik bilgisi
  FileSearchThread   — Dosya sistemi araması
  ClipboardWatcher   — Pano değişikliklerini izler
  UpdateChecker      — GitHub sürüm kontrolü
  CurrencyFetcher    — Döviz kurları (open.er-api.com)
"""

import os, json, time, subprocess, urllib.request, urllib.parse
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

import win32com.client, win32gui


# ─────────────────────────────────────────────────────────────────────────────
# 1. SHORTCUT SCANNER
# ─────────────────────────────────────────────────────────────────────────────
class ShortcutScanner(QThread):
    found = pyqtSignal(list)

    def run(self):
        from config import SHORTCUTS_DIR, ICONS_DIR, dm
        apps, seen = [], set()
        for d in [
            Path(os.environ.get("APPDATA",""))/"Microsoft/Windows/Start Menu/Programs",
            Path(os.environ.get("PROGRAMDATA",""))/"Microsoft/Windows/Start Menu/Programs",
            SHORTCUTS_DIR,
        ]:
            if not d.exists(): continue
            for lnk in d.rglob("*.lnk"):
                try:
                    sh = win32com.client.Dispatch("WScript.Shell")
                    sc = sh.CreateShortCut(str(lnk))
                    tgt = sc.Targetpath
                    if not tgt or not Path(tgt).exists(): continue
                    key = lnk.stem.lower()
                    if key in seen: continue
                    seen.add(key)
                    icon = self._icon(tgt, lnk.stem, ICONS_DIR)
                    alias = dm.get_alias(tgt)
                    tag   = dm.get_tag(tgt)
                    apps.append({"path": tgt,
                                 "name": alias or lnk.stem,
                                 "orig_name": lnk.stem,
                                 "icon_path": icon,
                                 "tag": tag})
                except Exception:
                    continue
        self.found.emit(sorted(apps, key=lambda x: x["name"].lower()))

    def _icon(self, exe, name, icons_dir):
        safe = "".join(c for c in name if c.isalnum() or c in " _-")[:40]
        out = icons_dir / f"{safe}.png"
        if out.exists(): return str(out)
        try:
            large, _ = win32gui.ExtractIconEx(exe, 0, 1)
            if not large: return ""
            hicon = large[0]; sz = 40
            hdc  = win32gui.CreateCompatibleDC(0)
            hbmp = win32gui.CreateCompatibleBitmap(win32gui.GetDC(0), sz, sz)
            win32gui.SelectObject(hdc, hbmp)
            win32gui.DrawIconEx(hdc, 0, 0, hicon, sz, sz, 0, None, 0x0003)
            pm = QPixmap.fromWinHBITMAP(int(hbmp), 2)
            pm.save(str(out), "PNG")
            win32gui.DestroyIcon(hicon)
            win32gui.DeleteDC(hdc)
            win32gui.DeleteObject(hbmp)
            return str(out)
        except Exception:
            return ""


# ─────────────────────────────────────────────────────────────────────────────
# 2. CPU / RAM MONİTÖR
# ─────────────────────────────────────────────────────────────────────────────
class SystemMonitor(QThread):
    updated = pyqtSignal(float, float)

    def __init__(self):
        super().__init__(); self._running = True

    def run(self):
        while self._running:
            try:
                if HAS_PSUTIL:
                    cpu = psutil.cpu_percent(interval=1)
                    ram = psutil.virtual_memory().percent
                else:
                    r  = subprocess.run(["wmic","cpu","get","LoadPercentage"],
                                        capture_output=True, text=True, timeout=2,
                                        creationflags=0x08000000)
                    cpu = float(r.stdout.strip().split()[-1])
                    r2 = subprocess.run(
                        ["wmic","OS","get","FreePhysicalMemory,TotalVisibleMemorySize"],
                        capture_output=True, text=True, timeout=2, creationflags=0x08000000)
                    parts = r2.stdout.strip().split()
                    free, total = float(parts[1]), float(parts[2])
                    ram = round((1 - free/total) * 100, 1)
                self.updated.emit(cpu, ram)
            except Exception:
                pass
            self.msleep(2000)

    def stop(self): self._running = False


# ─────────────────────────────────────────────────────────────────────────────
# 3. DİSK / AĞ / PİL MONİTÖR
# ─────────────────────────────────────────────────────────────────────────────
class DiskNetMonitor(QThread):
    updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__(); self._running = True
        self._prev_net = None; self._prev_t = None

    def run(self):
        while self._running:
            info = {}
            if HAS_PSUTIL:
                try:
                    du = psutil.disk_usage("/")
                    info["disk_pct"]     = du.percent
                    info["disk_free_gb"] = du.free  / 1024**3
                    info["disk_total_gb"]= du.total / 1024**3
                except Exception:
                    info["disk_pct"] = 0

                try:
                    nc = psutil.net_io_counters(); nt = time.time()
                    if self._prev_net and self._prev_t:
                        dt = nt - self._prev_t
                        info["net_down_kb"] = (nc.bytes_recv - self._prev_net.bytes_recv) / dt / 1024
                        info["net_up_kb"]   = (nc.bytes_sent - self._prev_net.bytes_sent) / dt / 1024
                    else:
                        info["net_down_kb"] = info["net_up_kb"] = 0
                    self._prev_net = nc; self._prev_t = nt
                except Exception:
                    info["net_down_kb"] = info["net_up_kb"] = 0

                try:
                    bat = psutil.sensors_battery()
                    if bat:
                        info["battery_pct"]  = bat.percent
                        info["battery_plug"] = bat.power_plugged
                    else:
                        info["battery_pct"] = -1
                except Exception:
                    info["battery_pct"] = -1

            self.updated.emit(info)
            self.msleep(3000)

    def stop(self): self._running = False


# ─────────────────────────────────────────────────────────────────────────────
# 4. HAVA DURUMU (5 günlük + güneş)
# ─────────────────────────────────────────────────────────────────────────────
class WeatherFetcher(QThread):
    fetched = pyqtSignal(dict)

    def run(self):
        from config import cfg
        city = cfg["weather_city"]; unit = cfg["weather_unit"]
        try:
            url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
            req = urllib.request.Request(url, headers={"User-Agent":"NexusStart/3.0"})
            with urllib.request.urlopen(req, timeout=7) as r:
                data = json.loads(r.read().decode())
            cur   = data["current_condition"][0]
            temp_c = int(cur["temp_C"])
            temp   = temp_c if unit=="metric" else round(temp_c*9/5+32)
            sym    = "°C" if unit=="metric" else "°F"
            desc   = cur.get("weatherDesc",[{"value":""}])[0]["value"]
            humidity = cur.get("humidity","?")
            wind     = cur.get("windspeedKmph","?")
            emoji    = self._emoji(int(cur.get("weatherCode",113)))

            forecast = []
            for day in data.get("weather",[])[:5]:
                maxc = int(day.get("maxtempC",0))
                minc = int(day.get("mintempC",0))
                h4   = day.get("hourly",[{}])[4] if len(day.get("hourly",[])) > 4 else {}
                desc_d = h4.get("weatherDesc",[{"value":""}])[0]["value"]
                code_d = int(h4.get("weatherCode",113))
                forecast.append({"date": day.get("date",""),
                                  "max": maxc, "min": minc,
                                  "desc": desc_d,
                                  "emoji": self._emoji(code_d)})

            astro   = data["weather"][0].get("astronomy",[{}])[0] if data.get("weather") else {}
            sunrise = astro.get("sunrise","")
            sunset  = astro.get("sunset","")

            self.fetched.emit({
                "temp": f"{temp}{sym}", "desc": desc,
                "humidity": humidity, "wind": wind,
                "emoji": emoji, "city": city, "ok": True,
                "forecast": forecast, "sunrise": sunrise, "sunset": sunset,
            })
        except Exception as e:
            self.fetched.emit({"ok": False, "error": str(e)})

    def _emoji(self, c):
        if c==113: return "☀️"
        if c in(116,): return "⛅"
        if c in(119,122): return "☁️"
        if c in(143,248,260): return "🌫️"
        if c in(176,179,182,185,281,284,311,314,317,350,377): return "🌧️"
        if c in(200,386,389,392,395): return "⛈️"
        if c in(227,230,335,338,368,371,374): return "❄️"
        return "🌡️"


# ─────────────────────────────────────────────────────────────────────────────
# 5. MÜZİK İZLEYİCİ
# ─────────────────────────────────────────────────────────────────────────────
class MediaWatcher(QThread):
    updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__(); self._running = True

    def run(self):
        while self._running:
            self.updated.emit(self._get())
            self.msleep(2500)

    def _get(self):
        try:
            ps = (
                "Add-Type -AssemblyName System.Runtime.WindowsRuntime;"
                "$t=[Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager,"
                "Windows.Media.Control,ContentType=WindowsRuntime];"
                "$m=[System.WindowsRuntimeSystemExtensions]::AsTask($t::RequestAsync());"
                "$m.Wait(1000);"
                "if($m.Result){$s=$m.Result.GetCurrentSession();if($s){"
                "$p=[System.WindowsRuntimeSystemExtensions]::AsTask($s.TryGetMediaPropertiesAsync());"
                "$p.Wait(1000);Write-Output ($p.Result.Title+'|||'+$p.Result.Artist)}}"
            )
            r = subprocess.run(["powershell","-NoProfile","-Command",ps],
                               capture_output=True, text=True, timeout=5,
                               creationflags=0x08000000)
            out = r.stdout.strip()
            if "|||" in out:
                title, artist = out.split("|||", 1)
                return {"title": title.strip(), "artist": artist.strip(),
                        "playing": bool(title.strip())}
        except Exception:
            pass
        return {"title": "", "artist": "", "playing": False}

    def stop(self): self._running = False


# ─────────────────────────────────────────────────────────────────────────────
# 6. DOSYA ARAMA
# ─────────────────────────────────────────────────────────────────────────────
class FileSearchThread(QThread):
    results = pyqtSignal(list)

    def __init__(self, q):
        super().__init__(); self.q = q

    def run(self):
        found = []
        for d in [Path.home()/"Desktop", Path.home()/"Documents",
                  Path.home()/"Downloads", Path.home()/"Pictures"]:
            if not d.exists(): continue
            try:
                for f in d.rglob("*"):
                    if self.q in f.name.lower() and f.is_file():
                        found.append({"path": str(f), "name": f.name,
                                      "icon_path": "",
                                      "last_used": f.stat().st_mtime})
                    if len(found) >= 20: break
            except Exception:
                pass
            if len(found) >= 20: break
        self.results.emit(found)


# ─────────────────────────────────────────────────────────────────────────────
# 7. PANO İZLEYİCİ
# ─────────────────────────────────────────────────────────────────────────────
class ClipboardWatcher(QThread):
    new_item = pyqtSignal(str)

    def __init__(self):
        super().__init__(); self._running = True; self._last = ""

    def run(self):
        while self._running:
            try:
                text = QApplication.clipboard().text()
                if text and text != self._last and len(text) < 500:
                    self._last = text
                    self.new_item.emit(text)
            except Exception:
                pass
            self.msleep(1500)

    def stop(self): self._running = False


# ─────────────────────────────────────────────────────────────────────────────
# 8. GÜNCELLEME KONTROLÜ
# ─────────────────────────────────────────────────────────────────────────────
class UpdateChecker(QThread):
    result = pyqtSignal(bool, str)

    def run(self):
        from config import cfg
        try:
            url = "https://api.github.com/repos/nexusstart/nexusstart/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent":"NexusStart/3.0"})
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read().decode())
            latest  = data.get("tag_name","v3.0").lstrip("v")
            current = cfg["app_version"]
            self.result.emit(latest != current, latest)
        except Exception:
            self.result.emit(False, cfg["app_version"])


# ─────────────────────────────────────────────────────────────────────────────
# 9. DÖVİZ KURU
# ─────────────────────────────────────────────────────────────────────────────
class CurrencyFetcher(QThread):
    done = pyqtSignal(dict)

    def run(self):
        try:
            url = "https://open.er-api.com/v6/latest/USD"
            with urllib.request.urlopen(url, timeout=5) as r:
                data = json.loads(r.read().decode())
            self.done.emit(data.get("rates", {}))
        except Exception:
            self.done.emit({})
