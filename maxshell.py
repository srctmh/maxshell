#!/usr/bin/env python3
# ============================================================
#   MAX Shell Tool v5.2.0 · Python Edition
#   by SRC TMH · Ultra-Fast · Universal Compatibility
#   Dynamic Box + Android 11+ APK Fix + Cached Startup
# ============================================================

import os
import sys
import re
import time
import shutil
import hashlib
import subprocess
import unicodedata
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime

# ─── Speed Boost ───────────────────────────────────────────
sys.dont_write_bytecode = True
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

# ─── Constants ─────────────────────────────────────────────
BASE = Path.home() / ".maxshell"
CONFIG = BASE / "config"
CREDITS_FILE = BASE / "credits.dat"
HISTORY_FILE = BASE / "history.log"
ACTIVATED_FILE = BASE / "activated.keys"
TMP_BASE = BASE / "tmp"
OUTPUT_FOLDER = "@SRCTMH"
TOOL_VERSION = "5.2.0"
SECRET_SALT = "MAX_GUARD_2026_CORE_X7kP9mQ2"
KEY_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CREDITS_URL_DEFAULT = "https://c19.lovable.app/free-dpt"

# ─── Colors ────────────────────────────────────────────────
class C:
    if sys.stdout.isatty():
        BOLD    = "\033[1m"
        RESET   = "\033[0m"
        DIM     = "\033[2m"
        GREEN   = "\033[38;5;46m"
        RED     = "\033[38;5;196m"
        CYAN    = "\033[38;5;51m"
        YELLOW  = "\033[38;5;226m"
        MAGENTA = "\033[38;5;201m"
        WHITE   = "\033[38;5;255m"
        GRAY    = "\033[38;5;245m"
        BLUE    = "\033[38;5;39m"
    else:
        BOLD = RESET = DIM = GREEN = RED = CYAN = YELLOW = MAGENTA = WHITE = GRAY = BLUE = ""

# ═══════════════════════════════════════════════════════════
#   FAST TERMINAL WIDTH (no tput, cached)
# ═══════════════════════════════════════════════════════════

MIN_WIDTH = 42
MAX_WIDTH = 78
DEFAULT_TERM_WIDTH = 80

def _get_terminal_width():
    """Fast: use COLUMNS env or os.get_terminal_size. No subprocess."""
    # 1. Environment variable (fastest)
    env_cols = os.environ.get("COLUMNS", "")
    if env_cols.isdigit():
        return int(env_cols)

    # 2. os.get_terminal_size (fast C call)
    try:
        cols = os.get_terminal_size().columns
        if cols > 0:
            return cols
    except Exception:
        pass

    # 3. shutil fallback
    try:
        return shutil.get_terminal_size((DEFAULT_TERM_WIDTH, 24)).columns
    except Exception:
        return DEFAULT_TERM_WIDTH

_terminal_width = _get_terminal_width()

if _terminal_width < MIN_WIDTH:
    BW, TOO_NARROW = 0, True
else:
    _avail = _terminal_width - 4
    BW, TOO_NARROW = (_avail if _avail <= MAX_WIDTH else MAX_WIDTH), False

# ─── ANSI Strip ────────────────────────────────────────────
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
_ANSI_SUB = ANSI_RE.sub

# Width cache (fast)
_WIDTH_CACHE = {}

def strip_ansi(s):
    return _ANSI_SUB("", s)

def display_width(s):
    cached = _WIDTH_CACHE.get(s)
    if cached is not None:
        return cached
    stripped = _ANSI_SUB("", s)
    width = 0
    for ch in stripped:
        if unicodedata.combining(ch):
            continue
        ea = unicodedata.east_asian_width(ch)
        width += 2 if ea in ("W", "F") else 1
    _WIDTH_CACHE[s] = width
    return width

# ═══════════════════════════════════════════════════════════
#   FAST BOX RENDERING
# ═══════════════════════════════════════════════════════════

_BORDER_CACHE = {}

def _get_border(top_mid_bot):
    if top_mid_bot in _BORDER_CACHE:
        return _BORDER_CACHE[top_mid_bot]
    left, right = top_mid_bot
    line = f"{C.GRAY}{left}{'─' * (BW + 2)}{right}{C.RESET}"
    _BORDER_CACHE[top_mid_bot] = line
    return line

def box_top():
    if TOO_NARROW:
        return
    print(_get_border(("╭", "╮")))

def box_mid():
    if TOO_NARROW:
        return
    print(_get_border(("├", "┤")))

def box_bot():
    if TOO_NARROW:
        return
    print(_get_border(("╰", "╯")))

def box_empty():
    box_line("")

def box_line(text=""):
    if TOO_NARROW:
        return
    vis = display_width(text)
    if vis > BW:
        plain = strip_ansi(text)
        cut = ""
        w = 0
        for ch in plain:
            cw = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
            if w + cw > BW - 3:
                break
            cut += ch
            w += cw
        text = cut + "..."
        vis = display_width(text)
    pad = BW - vis
    print(f"{C.GRAY}│{C.RESET} {text}{' ' * pad} {C.GRAY}│{C.RESET}")

def box_center(text=""):
    if TOO_NARROW:
        return
    vis = display_width(text)
    if vis > BW:
        box_line(text)
        return
    total = BW - vis
    left = total // 2
    right = total - left
    print(f"{C.GRAY}│{C.RESET} {' ' * left}{text}{' ' * right} {C.GRAY}│{C.RESET}")

def clear_screen():
    os.system("clear")

def too_narrow_screen():
    clear_screen()
    print()
    print(f"  {C.RED}{C.BOLD}⚠  Screen too narrow{C.RESET}")
    print()
    print(f"  {C.GRAY}Minimum width required: {C.WHITE}{MIN_WIDTH} cols{C.RESET}")
    print(f"  {C.GRAY}Current width detected: {C.WHITE}{_terminal_width} cols{C.RESET}")
    print()
    print(f"  {C.GRAY}Please rotate your device or resize your terminal.{C.RESET}")
    print()
    sys.exit(1)

# ═══════════════════════════════════════════════════════════
#   BANNER (pre-rendered strings)
# ═══════════════════════════════════════════════════════════

_BANNER_RENDERED = None

def _build_banner():
    lines = [
        "███╗   ███╗ █████╗ ██╗  ██╗",
        "████╗ ████║██╔══██╗╚██╗██╔╝",
        "██╔████╔██║███████║ ╚███╔╝ ",
        "██║╚██╔╝██║██╔══██║ ██╔██╗ ",
        "██║ ╚═╝ ██║██║  ██║██╔╝ ██╗",
        "╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝",
    ]
    out = []
    for line in lines:
        vis = len(line)
        if vis > BW:
            out.append(line)
            continue
        total = BW - vis
        left = total // 2
        right = total - left
        out.append(f"{C.GRAY}│{C.RESET} {' ' * left}{C.BOLD}{C.CYAN}{line}{C.RESET}{' ' * right} {C.GRAY}│{C.RESET}")
    return out

def print_banner():
    global _BANNER_RENDERED
    if _BANNER_RENDERED is None:
        _BANNER_RENDERED = _build_banner()
    for line in _BANNER_RENDERED:
        print(line)

# ═══════════════════════════════════════════════════════════
#   INPUT / PAUSE
# ═══════════════════════════════════════════════════════════

def read_input(prompt="  > "):
    try:
        sys.stderr.write(prompt)
        sys.stderr.flush()
        return input()
    except (EOFError, KeyboardInterrupt):
        return ""

def pause():
    print()
    sys.stderr.write(f"  {C.GRAY}Press {C.BOLD}{C.WHITE}Enter{C.RESET}{C.GRAY} to continue{C.RESET} ")
    sys.stderr.flush()
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass

# ═══════════════════════════════════════════════════════════
#   CONFIG (cached)
# ═══════════════════════════════════════════════════════════

def parse_config_file(path):
    cfg = {}
    if not path.is_file():
        return cfg
    try:
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return cfg

CONFIG_DATA = {}

def require_config():
    global CONFIG_DATA
    if TOO_NARROW:
        too_narrow_screen()
    if not CONFIG.is_file():
        clear_screen()
        box_top(); box_empty()
        box_center(f"{C.RED}{C.BOLD}NOT INSTALLED{C.RESET}")
        box_empty()
        box_center(f"{C.GRAY}Run: bash install.sh{C.RESET}")
        box_empty(); box_bot()
        print()
        sys.exit(1)
    CONFIG_DATA = parse_config_file(CONFIG)
    core_jar = CONFIG_DATA.get("CORE_JAR", "")
    if not core_jar or not Path(core_jar).is_file():
        clear_screen()
        box_top(); box_empty()
        box_center(f"{C.RED}{C.BOLD}ENGINE MISSING{C.RESET}")
        box_empty()
        box_center(f"{C.GRAY}Re-run install.sh{C.RESET}")
        box_empty(); box_bot()
        print()
        sys.exit(1)

def cfg(key, default=""):
    return CONFIG_DATA.get(key, default)

# ═══════════════════════════════════════════════════════════
#   DEVICE ID (fast, cached)
# ═══════════════════════════════════════════════════════════

_DEVICE_ID_CACHE = None

def _read_first(paths):
    for p in paths:
        try:
            val = Path(p).read_text().strip()
            if val:
                return val
        except Exception:
            continue
    return ""

def get_device_id():
    global _DEVICE_ID_CACHE
    if _DEVICE_ID_CACHE is not None:
        return _DEVICE_ID_CACHE

    # Try fast file-based sources first (no subprocess)
    android_id = _read_first([
        "/sys/class/android_usb/android0/iSerial",
        "/proc/sys/kernel/random/boot_id",
    ])

    # Fallback to getprop (single call)
    if not android_id:
        try:
            android_id = subprocess.run(
                "getprop ro.serialno",
                shell=True, capture_output=True, text=True, timeout=3
            ).stdout.strip()
        except Exception:
            android_id = ""

    if not android_id or android_id == "unknown":
        try:
            uuid_file = "/data/data/com.termux/files/usr/etc/uuid"
            if os.path.isfile(uuid_file):
                android_id = Path(uuid_file).read_text().strip()
        except Exception:
            pass

    if not android_id:
        android_id = "UNKNOWN"

    prefix = os.environ.get("PREFIX", str(Path.home()))
    raw = f"{android_id}-{prefix}-MAX2026"
    md5 = hashlib.md5(raw.encode()).hexdigest()[:12].upper()
    _DEVICE_ID_CACHE = f"MAX-{md5}"
    return _DEVICE_ID_CACHE

# ═══════════════════════════════════════════════════════════
#   CREDITS (fast load)
# ═══════════════════════════════════════════════════════════

DEVICE_ID = ""
CREDITS = 0
_CREDITS_LOADED = False

def init_credits():
    if _CREDITS_LOADED:
        return
    BASE.mkdir(parents=True, exist_ok=True)
    if not CREDITS_FILE.is_file():
        CREDITS_FILE.write_text(f"device_id={get_device_id()}\ncredits=0\n")

def save_credits():
    CREDITS_FILE.write_text(f"device_id={DEVICE_ID}\ncredits={CREDITS}\n")

def load_credits():
    global DEVICE_ID, CREDITS, _CREDITS_LOADED
    init_credits()
    cfg_data = parse_config_file(CREDITS_FILE)
    DEVICE_ID = cfg_data.get("device_id") or get_device_id()
    c = cfg_data.get("credits", "0")
    try:
        CREDITS = int(c)
    except ValueError:
        CREDITS = 0
    _CREDITS_LOADED = True

def deduct(n):
    global CREDITS
    if CREDITS < n:
        return False
    CREDITS -= n
    save_credits()
    return True

def add_credits(n):
    global CREDITS
    CREDITS += n
    save_credits()

# ═══════════════════════════════════════════════════════════
#   KEY GENERATION
# ═══════════════════════════════════════════════════════════

_KEY_CACHE = {}

def hex_to_charset(hex_str, length):
    out = []
    i = 0
    while len(out) < length and i < len(hex_str) - 1:
        try:
            byte = int(hex_str[i:i+2], 16)
        except ValueError:
            byte = 0
        out.append(KEY_CHARS[byte % 32])
        i += 2
    return "".join(out)

def generate_key_for(did, amount):
    key = (did, amount)
    cached = _KEY_CACHE.get(key)
    if cached is not None:
        return cached
    payload = f"{did}|{amount}|max_v1|{SECRET_SALT}"
    h = hashlib.sha256(payload.encode()).hexdigest()
    body = hex_to_charset(h, 16)
    checksum = hex_to_charset(h[-16:], 4)
    result = f"MAX-{body[0:4]}-{body[4:8]}-{body[8:12]}-{body[12:16]}-{checksum}"
    _KEY_CACHE[key] = result
    return result

_QUICK_AMOUNTS = [1, 2, 3, 5, 10, 15, 20, 25, 30, 40, 50, 75, 100, 150,
                  200, 250, 300, 500, 750, 1000, 1500, 2000, 5000]
_QUICK_SET = set(_QUICK_AMOUNTS)

def decode_credits_from_key(key):
    for c in _QUICK_AMOUNTS:
        if generate_key_for(DEVICE_ID, c) == key:
            return c
    for c in range(1, 501):
        if c in _QUICK_SET:
            continue
        if generate_key_for(DEVICE_ID, c) == key:
            return c
    return None

_KEY_RE = re.compile(r"^MAX-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$")
_WS_RE = re.compile(r"\s+")

def verify_code(key):
    key = _WS_RE.sub("", key).upper()
    if not _KEY_RE.match(key):
        return ("INVALID_FORMAT", None)
    BASE.mkdir(parents=True, exist_ok=True)
    if ACTIVATED_FILE.is_file():
        try:
            used = ACTIVATED_FILE.read_text().splitlines()
            if key in used:
                return ("ALREADY_USED", None)
        except Exception:
            pass
    amount = decode_credits_from_key(key)
    if not amount or amount < 1:
        return ("INVALID_KEY", None)
    add_credits(amount)
    with ACTIVATED_FILE.open("a") as f:
        f.write(key + "\n")
    return ("OK", amount)

# ═══════════════════════════════════════════════════════════
#   CLIPBOARD / URL (non-blocking)
# ═══════════════════════════════════════════════════════════

def copy_id():
    try:
        subprocess.Popen(["termux-clipboard-set"],
                       stdin=subprocess.PIPE, text=True)
        return True
    except Exception:
        return False

def open_credits_url():
    url = cfg("CREDITS_URL", CREDITS_URL_DEFAULT)
    # Fire and forget clipboard (async)
    try:
        p = subprocess.Popen(["termux-clipboard-set"],
                            stdin=subprocess.PIPE, text=True)
        p.communicate(input=DEVICE_ID, timeout=3)
    except Exception:
        pass
    # Fire and forget URL open
    try:
        subprocess.Popen(["termux-open-url", url],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════
#   HISTORY
# ═══════════════════════════════════════════════════════════

def log_history(name, ptype, status):
    BASE.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%d %b %Y %H:%M")
    with HISTORY_FILE.open("a") as f:
        f.write(f"{ts}|{name}|{ptype}|{status}\n")

def unique_output_name(directory, base, ext):
    candidate = Path(directory) / f"{base}.{ext}"
    if not candidate.exists():
        return str(candidate)
    n = 1
    while True:
        candidate = Path(directory) / f"{base}({n}).{ext}"
        if not candidate.exists():
            return str(candidate)
        n += 1

# ═══════════════════════════════════════════════════════════
#   TOOL DETECTION
# ═══════════════════════════════════════════════════════════

_TOOL_CACHE = {}

def tool_exists(name):
    cached = _TOOL_CACHE.get(name)
    if cached is not None:
        return cached
    try:
        r = subprocess.run(f"command -v {name}", shell=True,
                          capture_output=True, timeout=3)
        result = r.returncode == 0
    except Exception:
        result = False
    _TOOL_CACHE[name] = result
    return result

# ═══════════════════════════════════════════════════════════
#   KEYSTORE
# ═══════════════════════════════════════════════════════════

_KEYSTORE_PATH = None

def ensure_debug_keystore():
    global _KEYSTORE_PATH
    if _KEYSTORE_PATH:
        return _KEYSTORE_PATH
    keystore = BASE / "debug.keystore"
    if keystore.is_file():
        _KEYSTORE_PATH = str(keystore)
        return _KEYSTORE_PATH
    BASE.mkdir(parents=True, exist_ok=True)
    if not tool_exists("keytool"):
        return None
    try:
        r = subprocess.run([
            "keytool", "-genkeypair",
            "-keystore", str(keystore),
            "-alias", "maxshell",
            "-keyalg", "RSA",
            "-keysize", "2048",
            "-validity", "10000",
            "-storepass", "android",
            "-keypass", "android",
            "-dname", "CN=MAX Shell,OU=Dev,O=SRCTMH,L=IN,ST=IN,C=IN"
        ], capture_output=True, text=True, timeout=90)
        if r.returncode == 0 and keystore.is_file():
            _KEYSTORE_PATH = str(keystore)
            return _KEYSTORE_PATH
    except Exception:
        pass
    return None

# ═══════════════════════════════════════════════════════════
#   APK FIX (Android 11+)
# ═══════════════════════════════════════════════════════════

def fix_apk_for_android11(apk_path, output_path):
    src = Path(apk_path)
    if not src.is_file():
        return None

    work = Path(tempfile.mkdtemp(prefix="apkfix_"))
    try:
        rebuilt = work / "rebuilt.apk"
        try:
            with zipfile.ZipFile(str(src), "r") as zin:
                with zipfile.ZipFile(str(rebuilt), "w", zipfile.ZIP_DEFLATED) as zout:
                    for item in zin.infolist():
                        data = zin.read(item.filename)
                        if item.filename == "resources.arsc":
                            new_info = zipfile.ZipInfo(item.filename)
                            new_info.compress_type = zipfile.ZIP_STORED
                            new_info.external_attr = item.external_attr
                            new_info.date_time = item.date_time
                            zout.writestr(new_info, data)
                        else:
                            zout.writestr(item, data)
        except Exception:
            return None

        current = rebuilt

        if tool_exists("zipalign"):
            aligned = work / "aligned.apk"
            try:
                r = subprocess.run(
                    ["zipalign", "-p", "-f", "4", str(current), str(aligned)],
                    capture_output=True, text=True, timeout=180
                )
                if r.returncode == 0 and aligned.is_file():
                    current = aligned
            except Exception:
                pass

        if tool_exists("apksigner"):
            ks = ensure_debug_keystore()
            if ks:
                signed = Path(output_path)
                try:
                    r = subprocess.run([
                        "apksigner", "sign",
                        "--ks", ks,
                        "--ks-key-alias", "maxshell",
                        "--ks-pass", "pass:android",
                        "--key-pass", "pass:android",
                        "--v1-signing-enabled", "true",
                        "--v2-signing-enabled", "true",
                        "--v3-signing-enabled", "true",
                        "--out", str(signed),
                        str(current)
                    ], capture_output=True, text=True, timeout=300)
                    if r.returncode == 0 and signed.is_file():
                        return str(signed)
                    r = subprocess.run([
                        "apksigner", "sign",
                        "--ks", ks,
                        "--ks-key-alias", "maxshell",
                        "--ks-pass", "pass:android",
                        "--key-pass", "pass:android",
                        "--out", str(signed),
                        str(current)
                    ], capture_output=True, text=True, timeout=300)
                    if r.returncode == 0 and signed.is_file():
                        return str(signed)
                except Exception:
                    pass

        if current.is_file():
            try:
                shutil.copy2(str(current), output_path)
                return output_path
            except Exception:
                pass
        return None
    finally:
        shutil.rmtree(work, ignore_errors=True)

# ═══════════════════════════════════════════════════════════
#   LIBRARY PROTECT (fast)
# ═══════════════════════════════════════════════════════════

def apply_library(apk_path, choice):
    libs_dir = Path(cfg("LIBS_DIR", str(BASE / "libs")))
    work = TMP_BASE / f"lib_{os.getpid()}"
    extracted = work / "ex"
    out_apk = work / "out.apk"
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    extracted.mkdir(parents=True, exist_ok=True)

    try:
        r = subprocess.run(["unzip", "-q", "-o", apk_path, "-d", str(extracted)],
                          capture_output=True, timeout=120)
        if r.returncode != 0:
            return None
    except Exception:
        return None

    if not (extracted / "AndroidManifest.xml").is_file():
        return None

    targets = {
        "1": (extracted / "lib" / "armeabi-v7a", libs_dir / "jiagu" / "libjiagu.so"),
        "2": (extracted / "lib" / "arm64-v8a", libs_dir / "tencent" / "libshell-super.2019.so"),
        "3": (extracted / "lib" / "arm64-v8a", libs_dir / "google" / "libpairipcore.so"),
        "4": (extracted / "lib" / "arm64-v8a", libs_dir / "arm" / "libarm_protect.so"),
    }

    if choice in targets:
        dest_dir, src_file = targets[choice]
        dest_dir.mkdir(parents=True, exist_ok=True)
        if not src_file.is_file():
            return None
        try:
            shutil.copy2(src_file, dest_dir / src_file.name)
        except Exception:
            return None
    elif choice == "5":
        assets = extracted / "assets"
        assets.mkdir(parents=True, exist_ok=True)
        for f in ["ijiami.ajm", "ijiami_x86.ajm"]:
            src = libs_dir / "ijiami" / f
            if src.is_file():
                try:
                    shutil.copy2(src, assets / f)
                except Exception:
                    return None
    else:
        return None

    try:
        r = subprocess.run(f"cd {extracted} && zip -qr {out_apk} .",
                          shell=True, capture_output=True, timeout=180)
        if r.returncode != 0 or not out_apk.is_file():
            return None
    except Exception:
        return None

    return str(out_apk)

# ═══════════════════════════════════════════════════════════
#   PROGRESS SCREEN
# ═══════════════════════════════════════════════════════════

_PROGRESS_LABELS = ["File verified", "Library Protect", "Resource Protect",
                    "MAX Engine", "Finalizing"]

def show_progress(stage, fname, size):
    dots = ["○"] * 5
    for i in range(5):
        if stage >= i + 1:
            dots[i] = "●"
    if 0 <= stage < 5:
        dots[stage] = "◉"

    colors = [C.GREEN] * 5
    if 0 <= stage < 5:
        colors[stage] = C.CYAN

    clear_screen()
    box_top(); box_empty()
    box_center(f"{C.BOLD}{C.CYAN}⚡ PROCESSING APK ⚡{C.RESET}")
    box_empty(); box_mid(); box_empty()
    box_line(f"   {C.GRAY}File{C.RESET}  :  {C.WHITE}{fname}{C.RESET}")
    if size:
        box_line(f"   {C.GRAY}Size{C.RESET}  :  {C.WHITE}{size}{C.RESET}")
    box_empty(); box_empty()
    for i, label in enumerate(_PROGRESS_LABELS):
        box_line(f"    {colors[i]}{dots[i]}{C.RESET}   {C.GRAY}{label}{C.RESET}")
    box_empty(); box_bot()

# ═══════════════════════════════════════════════════════════
#   SCREENS
# ═══════════════════════════════════════════════════════════

def main_menu():
    while True:
        load_credits()
        clear_screen()
        box_top(); box_empty()
        print_banner()
        box_empty()
        box_center(f"{C.GRAY}MAX SHELL · PROTECTION SUITE{C.RESET}")
        box_center(f"{C.GRAY}by SRC TMH · v{TOOL_VERSION}{C.RESET}")
        box_empty(); box_mid(); box_empty()
        box_line(f"   {C.GRAY}Credits{C.RESET}   :  {C.GREEN}{C.BOLD}{CREDITS}{C.RESET}")
        box_line(f"   {C.GRAY}Device{C.RESET}    :  {C.CYAN}{DEVICE_ID}{C.RESET}")
        box_empty(); box_mid(); box_empty()
        box_line(f"   {C.CYAN}[1]{C.RESET}   {C.BOLD}Protect APK{C.RESET}")
        box_line(f"   {C.CYAN}[2]{C.RESET}   {C.BOLD}History{C.RESET}")
        box_line(f"   {C.CYAN}[3]{C.RESET}   {C.BOLD}Get Credits{C.RESET}")
        box_line(f"   {C.CYAN}[4]{C.RESET}   {C.BOLD}About{C.RESET}")
        box_line(f"   {C.CYAN}[5]{C.RESET}   {C.BOLD}Exit{C.RESET}")
        box_empty(); box_bot()
        print()
        c = read_input(f"  {C.BOLD}{C.CYAN}❯{C.RESET} ").strip()
        if c == "1":
            protect_flow()
        elif c == "2":
            history_screen()
        elif c == "3":
            get_credits_screen()
        elif c == "4":
            about_screen()
        elif c == "5":
            clear_screen()
            box_top(); box_empty()
            box_center(f"{C.BOLD}{C.GREEN}Thank You{C.RESET}")
            box_empty()
            box_center(f"{C.GRAY}Developed by @SRCTMH{C.RESET}")
            box_empty(); box_bot()
            print()
            sys.exit(0)

def get_credits_screen():
    load_credits()
    while True:
        clear_screen()
        box_top(); box_empty()
        box_center(f"{C.BOLD}{C.CYAN}GET CREDITS{C.RESET}")
        box_empty(); box_mid(); box_empty()
        box_line(f"   {C.GRAY}Device{C.RESET}    :  {C.CYAN}{DEVICE_ID}{C.RESET}")
        box_line(f"   {C.GRAY}Balance{C.RESET}   :  {C.GREEN}{C.BOLD}{CREDITS}{C.RESET}")
        box_empty(); box_mid(); box_empty()
        box_line(f"   {C.GREEN}[1]{C.RESET}   {C.BOLD}VIP Code{C.RESET}")
        box_line(f"        {C.GRAY}Redeem your code{C.RESET}")
        box_empty()
        box_line(f"   {C.CYAN}[2]{C.RESET}   {C.BOLD}Get Free Credit{C.RESET}")
        box_line(f"        {C.GRAY}Open credit page in browser{C.RESET}")
        box_empty()
        box_line(f"   {C.YELLOW}[0]{C.RESET}   {C.BOLD}Back{C.RESET}")
        box_empty(); box_bot()
        print()
        c = read_input(f"  {C.BOLD}{C.CYAN}❯{C.RESET} ").strip()
        if c == "1":
            vip_code_flow()
        elif c == "2":
            clear_screen()
            box_top(); box_empty()
            box_center(f"{C.BOLD}{C.CYAN}OPENING BROWSER{C.RESET}")
            box_empty(); box_mid(); box_empty()
            box_center(f"{C.GREEN}✓{C.RESET} Device ID copied to clipboard")
            box_empty()
            box_center(f"{C.GRAY}Opening credits page...{C.RESET}")
            box_empty(); box_bot()
            open_credits_url()
            time.sleep(0.8)
            pause()
        elif c in ("0", ""):
            return

def vip_code_flow():
    load_credits()
    while True:
        clear_screen()
        box_top(); box_empty()
        box_center(f"{C.BOLD}{C.GREEN}VIP CODE REDEEM{C.RESET}")
        box_empty(); box_mid(); box_empty()
        box_line(f"   {C.GRAY}Device{C.RESET}    :  {C.CYAN}{DEVICE_ID}{C.RESET}")
        box_line(f"   {C.GRAY}Balance{C.RESET}   :  {C.GREEN}{C.BOLD}{CREDITS}{C.RESET}")
        box_empty(); box_mid(); box_empty()
        box_center("Enter your VIP code below")
        box_empty()
        box_center(f"{C.GRAY}MAX-XXXX-XXXX-XXXX-XXXX-XXXX{C.RESET}")
        box_empty()
        box_line(f"   {C.YELLOW}[0]{C.RESET}   {C.BOLD}Back{C.RESET}")
        box_empty(); box_bot()
        print()
        code = read_input(f"  {C.BOLD}{C.GREEN}Code ❯{C.RESET} ").strip()
        if code in ("0", ""):
            return
        status, value = verify_code(code)
        if status == "OK":
            load_credits()
            clear_screen()
            box_top(); box_empty()
            box_center(f"{C.BOLD}{C.GREEN}✓ CODE ACCEPTED ✓{C.RESET}")
            box_empty(); box_mid(); box_empty()
            box_line(f"   {C.GRAY}Added{C.RESET}    :  {C.GREEN}{C.BOLD}+{value} credits{C.RESET}")
            box_line(f"   {C.GRAY}Total{C.RESET}    :  {C.GREEN}{C.BOLD}{CREDITS}{C.RESET}")
            box_empty(); box_mid(); box_empty()
            box_center(f"{C.GRAY}Happy Protecting 🔥{C.RESET}")
            box_empty(); box_bot()
            pause()
            return
        else:
            msg = {
                "ALREADY_USED": "Code already used",
                "INVALID_FORMAT": "Invalid code format",
                "INVALID_KEY": "Code not valid for this device",
            }.get(status, "Invalid code")
            clear_screen()
            box_top(); box_empty()
            box_center(f"{C.BOLD}{C.RED}✗ CODE REJECTED ✗{C.RESET}")
            box_empty(); box_mid(); box_empty()
            box_center(f"{C.WHITE}{msg}{C.RESET}")
            box_empty(); box_mid(); box_empty()
            box_line(f"   {C.CYAN}[1]{C.RESET}   {C.BOLD}Try Again{C.RESET}")
            box_line(f"   {C.YELLOW}[0]{C.RESET}   {C.BOLD}Back{C.RESET}")
            box_empty(); box_bot()
            print()
            opt = read_input(f"  {C.BOLD}{C.CYAN}❯{C.RESET} ").strip()
            if opt == "0":
                return

def history_screen():
    clear_screen()
    box_top(); box_empty()
    box_center(f"{C.BOLD}{C.CYAN}PROTECTION HISTORY{C.RESET}")
    box_empty(); box_mid(); box_empty()
    if not HISTORY_FILE.is_file() or HISTORY_FILE.stat().st_size == 0:
        box_center(f"{C.GRAY}No history yet{C.RESET}")
    else:
        try:
            lines = HISTORY_FILE.read_text().splitlines()[-6:]
            lines.reverse()
            for i, line in enumerate(lines, 1):
                parts = line.split("|")
                if len(parts) == 4:
                    date, name, ptype, status = parts
                    mark = f"{C.RED}✗{C.RESET}" if status == "Failed" else f"{C.GREEN}✓{C.RESET}"
                    box_line(f"   {C.BOLD}{i}.{C.RESET} {mark} {name}")
                    box_line(f"      {C.GRAY}{ptype} · {date}{C.RESET}")
                    if i < len(lines):
                        box_empty()
        except Exception:
            box_center(f"{C.GRAY}No history yet{C.RESET}")
    box_empty(); box_bot()
    pause()

def about_screen():
    _URLS = {
        "1": "https://instagram.com/srctmh",
        "2": "https://t.me/srcmax",
        "3": "https://youtube.com/@srctmh",
        "4": "https://wa.me/916262262193",
    }
    while True:
        clear_screen()
        box_top(); box_empty()
        box_center(f"{C.BOLD}{C.CYAN}ABOUT{C.RESET}")
        box_empty(); box_mid(); box_empty()
        box_center(f"{C.BOLD}{C.WHITE}MAX Shell Tool{C.RESET}")
        box_empty()
        box_center(f"{C.GRAY}Version {C.WHITE}{TOOL_VERSION}{C.RESET}")
        box_empty()
        box_center(f"{C.GRAY}Developed by{C.RESET}")
        box_center(f"{C.BOLD}{C.MAGENTA}SRC TMH{C.RESET}")
        box_empty(); box_mid(); box_empty()
        box_line(f"   {C.CYAN}[1]{C.RESET}   Instagram")
        box_line(f"   {C.CYAN}[2]{C.RESET}   Telegram")
        box_line(f"   {C.CYAN}[3]{C.RESET}   YouTube")
        box_line(f"   {C.CYAN}[4]{C.RESET}   WhatsApp")
        box_empty()
        box_line(f"   {C.YELLOW}[0]{C.RESET}   {C.BOLD}Back{C.RESET}")
        box_empty(); box_bot()
        print()
        c = read_input(f"  {C.BOLD}{C.CYAN}❯{C.RESET} ").strip()
        if c in _URLS:
            try:
                subprocess.Popen(["termux-open-url", _URLS[c]],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
            except Exception:
                pass
        elif c in ("0", ""):
            return

# ═══════════════════════════════════════════════════════════
#   PROTECT FLOW
# ═══════════════════════════════════════════════════════════

def protect_flow():
    load_credits()
    if CREDITS < 1:
        clear_screen()
        box_top(); box_empty()
        box_center(f"{C.BOLD}{C.YELLOW}NO CREDITS LEFT{C.RESET}")
        box_empty(); box_mid(); box_empty()
        box_center(f"Minimum {C.WHITE}1 credit{C.RESET} required")
        box_empty()
        box_center(f"{C.GRAY}Device: {C.CYAN}{DEVICE_ID}{C.RESET}")
        box_empty()
        box_center(f"{C.GRAY}Opening credit page...{C.RESET}")
        box_empty(); box_bot()
        open_credits_url()
        time.sleep(0.8)
        return

    clear_screen()
    box_top(); box_empty()
    box_center(f"{C.BOLD}{C.CYAN}SELECT YOUR APK{C.RESET}")
    box_empty(); box_mid(); box_empty()
    box_center("Enter full path of your APK")
    box_empty()
    box_center(f"{C.GRAY}Example:{C.RESET}")
    box_center(f"{C.GRAY}/storage/emulated/0/Download/app.apk{C.RESET}")
    box_empty(); box_bot()
    print()
    apk_path = read_input(f"  {C.BOLD}{C.GREEN}APK ❯{C.RESET} ").strip()
    apk_path = apk_path.strip('"').strip("'")
    if apk_path.startswith("~/"):
        apk_path = str(Path.home() / apk_path[2:])

    if not apk_path or not Path(apk_path).is_file():
        clear_screen()
        box_top(); box_empty()
        box_center(f"{C.BOLD}{C.RED}FILE NOT FOUND{C.RESET}")
        box_empty()
        if apk_path:
            box_center(f"{C.GRAY}{apk_path}{C.RESET}")
        box_empty(); box_bot()
        pause()
        return

    if not apk_path.lower().endswith((".apk", ".aab")):
        clear_screen()
        box_top(); box_empty()
        box_center(f"{C.RED}Only APK or AAB allowed{C.RESET}")
        box_empty(); box_bot()
        pause()
        return

    clear_screen()
    box_top(); box_empty()
    box_center(f"{C.BOLD}{C.CYAN}LIBRARY PROTECT{C.RESET}")
    box_empty(); box_mid(); box_empty()
    box_line(f"   {C.GREEN}[1]{C.RESET}   360 Jiagu         {C.GRAY}armeabi-v7a{C.RESET}")
    box_line(f"   {C.GREEN}[2]{C.RESET}   Tencent Shell     {C.GRAY}arm64-v8a{C.RESET}")
    box_line(f"   {C.GREEN}[3]{C.RESET}   Google PairIP     {C.GRAY}arm64-v8a{C.RESET}")
    box_line(f"   {C.GREEN}[4]{C.RESET}   Arm Protect       {C.GRAY}arm64-v8a{C.RESET}")
    box_line(f"   {C.GREEN}[5]{C.RESET}   iJiami            {C.GRAY}assets{C.RESET}")
    box_empty()
    box_line(f"   {C.YELLOW}[0]{C.RESET}   {C.BOLD}Skip{C.RESET}")
    box_empty(); box_bot()
    print()
    lib_c = read_input(f"  {C.BOLD}{C.CYAN}❯{C.RESET} ").strip()
    if lib_c not in ("0", "1", "2", "3", "4", "5"):
        lib_c = "0"

    clear_screen()
    box_top(); box_empty()
    box_center(f"{C.BOLD}{C.CYAN}RESOURCE PROTECT{C.RESET}")
    box_empty(); box_mid(); box_empty()
    box_line(f"   {C.GREEN}[1]{C.RESET}   Apply Resource Protect")
    box_empty()
    box_line(f"   {C.YELLOW}[0]{C.RESET}   {C.BOLD}Skip{C.RESET}")
    box_empty(); box_bot()
    print()
    res_c = read_input(f"  {C.BOLD}{C.CYAN}❯{C.RESET} ").strip()
    if res_c not in ("0", "1"):
        res_c = "0"

    clear_screen()
    box_top(); box_empty()
    box_center(f"{C.BOLD}{C.CYAN}PROTECTION TYPE{C.RESET}")
    box_empty(); box_mid(); box_empty()
    box_line(f"   {C.GREEN}[1]{C.RESET}   {C.BOLD}Normal{C.RESET}           {C.GRAY}1 credit{C.RESET}")
    box_line(f"   {C.MAGENTA}[2]{C.RESET}   {C.BOLD}Signature Plus{C.RESET}   {C.GRAY}2 credits{C.RESET}")
    box_empty()
    box_line(f"   {C.YELLOW}[0]{C.RESET}   {C.BOLD}Skip{C.RESET}             {C.GRAY}1 credit{C.RESET}")
    box_empty(); box_bot()
    print()
    ptype = read_input(f"  {C.BOLD}{C.CYAN}❯{C.RESET} ").strip()

    mode, cost, ptype_label, extra_flags = "normal", 1, "Normal", []
    if ptype == "2":
        mode, cost, ptype_label = "signature", 2, "Signature Plus"
        extra_flags = ["-vs"]
        if CREDITS < 2:
            while True:
                clear_screen()
                box_top(); box_empty()
                box_center(f"{C.BOLD}{C.YELLOW}INSUFFICIENT CREDITS{C.RESET}")
                box_empty(); box_mid(); box_empty()
                box_center(f"Signature Plus needs {C.WHITE}2 credits{C.RESET}")
                box_empty()
                box_center(f"You have {C.GREEN}{CREDITS}{C.RESET}")
                box_empty()
                box_center(f"{C.GRAY}Device: {C.CYAN}{DEVICE_ID}{C.RESET}")
                box_empty(); box_mid(); box_empty()
                box_center(f"{C.GRAY}Paste a code to add credits{C.RESET}")
                box_empty()
                box_line(f"   {C.CYAN}[1]{C.RESET}   Main Menu")
                box_line(f"   {C.CYAN}[2]{C.RESET}   Use Normal (1 credit)")
                box_line(f"   {C.YELLOW}[0]{C.RESET}   Cancel")
                box_empty(); box_bot()
                open_credits_url()
                print()
                inp = read_input(f"  {C.BOLD}{C.GREEN}Code ❯{C.RESET} ").strip()
                if inp == "1":
                    return
                if inp == "2":
                    mode, cost, ptype_label, extra_flags = "normal", 1, "Normal", []
                    break
                if inp == "0":
                    mode, cost, ptype_label, extra_flags = "skip", 1, "Skip", []
                    break
                if not inp:
                    continue
                status, value = verify_code(inp)
                if status == "OK":
                    load_credits()
                    clear_screen()
                    box_top(); box_empty()
                    box_center(f"{C.GREEN}{C.BOLD}✓ CODE ACCEPTED{C.RESET}")
                    box_empty()
                    box_center(f"Added {C.GREEN}+{value}{C.RESET} credits")
                    box_center(f"Total: {C.GREEN}{CREDITS}{C.RESET}")
                    box_empty(); box_bot()
                    time.sleep(0.8)
                    if CREDITS >= 2:
                        break
                else:
                    clear_screen()
                    box_top(); box_empty()
                    box_center(f"{C.RED}{C.BOLD}✗ INVALID CODE{C.RESET}")
                    box_empty()
                    box_center(f"{C.GRAY}Try again{C.RESET}")
                    box_empty(); box_bot()
                    time.sleep(0.6)
    elif ptype == "0":
        mode, cost, ptype_label = "skip", 1, "Skip"
    else:
        mode, cost, ptype_label = "normal", 1, "Normal"

    if CREDITS < cost:
        clear_screen()
        box_top(); box_empty()
        box_center(f"{C.YELLOW}Not enough credits{C.RESET}")
        box_empty()
        box_center(f"Need {cost} · Have {CREDITS}")
        box_empty(); box_bot()
        open_credits_url()
        pause()
        return

    storage_root = cfg("STORAGE_ROOT", "/storage/emulated/0")
    out_root = Path(storage_root) / OUTPUT_FOLDER
    try:
        out_root.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    apk_name = Path(apk_path).name
    apk_ext = apk_name.rsplit(".", 1)[-1] if "." in apk_name else "apk"
    apk_base = apk_name.rsplit(".", 1)[0] if "." in apk_name else apk_name
    work_dir = TMP_BASE / f"p_{os.getpid()}"
    if work_dir.exists():
        shutil.rmtree(work_dir, ignore_errors=True)
    TMP_BASE.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    # Fast file size (Python, no subprocess)
    try:
        sz_bytes = Path(apk_path).stat().st_size
        if sz_bytes < 1024:
            size_str = f"{sz_bytes} B"
        elif sz_bytes < 1024 * 1024:
            size_str = f"{sz_bytes / 1024:.1f} KB"
        else:
            size_str = f"{sz_bytes / (1024*1024):.2f} MB"
    except Exception:
        size_str = "?"

    show_progress(0, apk_name, size_str)
    time.sleep(0.15)

    current = apk_path

    show_progress(1, apk_name, size_str)
    if lib_c != "0":
        result = apply_library(current, lib_c)
        if result:
            current = result
        else:
            clear_screen()
            box_top(); box_empty()
            box_center(f"{C.RED}Library Protect failed{C.RESET}")
            box_empty(); box_bot()
            shutil.rmtree(work_dir, ignore_errors=True)
            shutil.rmtree(TMP_BASE / f"lib_{os.getpid()}", ignore_errors=True)
            pause()
            return

    show_progress(2, apk_name, size_str)
    if res_c == "1":
        shield = cfg("APKSHIELD", str(BASE / "apkshield.py"))
        shield_out = work_dir / "res.apk"
        if Path(shield).is_file():
            try:
                r = subprocess.run(["python3", shield, current, str(shield_out), "--no-sign"],
                                  capture_output=True, timeout=600)
                if r.returncode == 0 and shield_out.is_file():
                    current = str(shield_out)
                else:
                    clear_screen()
                    box_top(); box_empty()
                    box_center(f"{C.RED}Resource Protect failed{C.RESET}")
                    box_empty(); box_bot()
                    shutil.rmtree(work_dir, ignore_errors=True)
                    pause()
                    return
            except Exception:
                clear_screen()
                box_top(); box_empty()
                box_center(f"{C.RED}Resource Protect failed{C.RESET}")
                box_empty(); box_bot()
                shutil.rmtree(work_dir, ignore_errors=True)
                pause()
                return

    show_progress(3, apk_name, size_str)
    produced = ""
    if mode != "skip":
        core_jar = cfg("CORE_JAR")
        core_dir = cfg("CORE_DIR", str(BASE / "core"))
        log_out = work_dir / "run.log"
        cmd = ["java", "-jar", core_jar, "-f", current, "-o", str(work_dir)] + extra_flags
        try:
            with open(log_out, "w") as logf:
                r = subprocess.run(cmd, cwd=core_dir, stdout=logf,
                                  stderr=subprocess.STDOUT, timeout=1800)
            if r.returncode != 0:
                reason = ""
                try:
                    reason = log_out.read_text().splitlines()[-3:]
                    reason = " ".join(reason)[:40]
                except Exception:
                    pass
                clear_screen()
                box_top(); box_empty()
                box_center(f"{C.RED}{C.BOLD}PROTECTION FAILED{C.RESET}")
                box_empty()
                box_center(f"{C.GRAY}{reason or 'Unknown error'}{C.RESET}")
                box_empty(); box_bot()
                log_history(apk_name, ptype_label, "Failed")
                shutil.rmtree(work_dir, ignore_errors=True)
                pause()
                return
        except Exception as e:
            clear_screen()
            box_top(); box_empty()
            box_center(f"{C.RED}{C.BOLD}ENGINE ERROR{C.RESET}")
            box_empty()
            box_center(f"{C.GRAY}{str(e)[:40]}{C.RESET}")
            box_empty(); box_bot()
            log_history(apk_name, ptype_label, "Failed")
            shutil.rmtree(work_dir, ignore_errors=True)
            pause()
            return

        # Fast find using rglob with early exit
        for f in work_dir.rglob("*"):
            if f.is_file() and f.name != "res.apk" and "_unsign" not in f.name:
                if f.name.endswith(("_signed.apk", ".apk", ".aab")):
                    produced = str(f)
                    break
    else:
        produced = str(work_dir / f"final.{apk_ext}")
        try:
            shutil.copy2(current, produced)
        except Exception:
            produced = ""

    show_progress(4, apk_name, size_str)
    time.sleep(0.15)
    show_progress(5, apk_name, size_str)
    time.sleep(0.15)

    if not produced or not Path(produced).is_file():
        clear_screen()
        box_top(); box_empty()
        box_center(f"{C.RED}No output file{C.RESET}")
        box_empty(); box_bot()
        log_history(apk_name, ptype_label, "Failed")
        shutil.rmtree(work_dir, ignore_errors=True)
        pause()
        return

    # Android 11+ fix
    fixed_apk = work_dir / "fixed.apk"
    fixed_result = fix_apk_for_android11(produced, str(fixed_apk))
    if fixed_result and Path(fixed_result).is_file():
        produced = fixed_result

    final_path = unique_output_name(str(out_root), apk_base, apk_ext)
    try:
        shutil.move(produced, final_path)
    except Exception:
        try:
            shutil.copy2(produced, final_path)
        except Exception:
            clear_screen()
            box_top(); box_empty()
            box_center(f"{C.RED}Could not save output{C.RESET}")
            box_empty(); box_bot()
            shutil.rmtree(work_dir, ignore_errors=True)
            pause()
            return

    shutil.rmtree(work_dir, ignore_errors=True)
    shutil.rmtree(TMP_BASE / f"lib_{os.getpid()}", ignore_errors=True)

    try:
        for d in Path.home().glob("apkshield_*"):
            if d.is_dir():
                shutil.rmtree(d, ignore_errors=True)
    except Exception:
        pass

    deduct(cost)
    log_history(apk_name, ptype_label, "Success")
    load_credits()

    clear_screen()
    box_top(); box_empty()
    box_center(f"{C.BOLD}{C.GREEN}✓ SUCCESS ✓{C.RESET}")
    box_empty(); box_mid(); box_empty()
    box_center(f"{C.GRAY}Protection applied successfully{C.RESET}")
    box_empty(); box_mid(); box_empty()
    box_line(f"   {C.GRAY}File{C.RESET}     :  {C.WHITE}{apk_name}{C.RESET}")
    box_line(f"   {C.GRAY}Output{C.RESET}   :  {C.WHITE}{Path(final_path).name}{C.RESET}")
    box_line(f"   {C.GRAY}Folder{C.RESET}   :  {C.CYAN}@SRCTMH{C.RESET}")
    box_line(f"   {C.GRAY}Credits{C.RESET}  :  {C.GREEN}{CREDITS} left{C.RESET}")
    box_empty(); box_bot()
    pause()

# ═══════════════════════════════════════════════════════════
#   INTERRUPT
# ═══════════════════════════════════════════════════════════

def on_interrupt(sig, frame):
    print()
    print()
    box_top(); box_empty()
    box_center(f"{C.YELLOW}Exiting safely{C.RESET}")
    box_empty()
    box_center(f"{C.GRAY}Thanks · {C.BOLD}@SRCTMH{C.RESET}")
    box_empty(); box_bot()
    print()
    sys.exit(130)

import signal
signal.signal(signal.SIGINT, on_interrupt)
signal.signal(signal.SIGTERM, on_interrupt)

# ═══════════════════════════════════════════════════════════
#   ENTRY
# ═══════════════════════════════════════════════════════════

def main():
    if TOO_NARROW:
        too_narrow_screen()
    require_config()
    load_credits()
    main_menu()

if __name__ == "__main__":
    main()