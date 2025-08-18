import os
import sys
import logging
import threading
import time
import webbrowser
from logging.handlers import RotatingFileHandler
from datetime import datetime

def _msgbox(title: str, text: str) -> None:
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, str(text), str(title), 0x10)
    except Exception:
        pass

def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def setup_paths() -> str:
    """
    Ensure the project root is on sys.path so 'app' can be imported,
    both when running from source and when frozen.
    Returns the resolved project root directory.
    """
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)

    try:
        os.chdir(base_dir)
    except Exception:
        pass

    return base_dir

def setup_logging(base_dir: str) -> logging.Logger:
    """
    Set up a rotating file log at <base_dir>/logs/runtime.log and console logging (if available).
    """
    logs_dir = os.path.join(base_dir, "logs")
    try:
        os.makedirs(logs_dir, exist_ok=True)
    except Exception:
        pass
    log_path = os.path.join(logs_dir, "runtime.log")

    logger = logging.getLogger("launcher")
    logger.setLevel(logging.INFO)
    logger.handlers[:] = []

    fmt = logging.Formatter("%(message)s")

    try:
        fh = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        fh.setFormatter(fmt)
        fh.setLevel(logging.INFO)
        logger.addHandler(fh)
    except Exception:
        pass

    # Add console handler only if sys.stdout is usable (console builds)
    try:
        if sys.stdout:
            ch = logging.StreamHandler(stream=sys.stdout)
            ch.setFormatter(fmt)
            ch.setLevel(logging.INFO)
            logger.addHandler(ch)
    except Exception:
        pass

    return logger

def _open_browser(url: str, delay: float = 0.6) -> None:
    def _worker():
        try:
            time.sleep(delay)
            webbrowser.open(url)
        except Exception:
            pass
    threading.Thread(target=_worker, daemon=True).start()

def main() -> int:
    try:
        base_dir = setup_paths()
        logger = setup_logging(base_dir)
        def log(msg: str) -> None: logger.info(f"[{ts()}] {msg}")
    except Exception as e:
        _msgbox("Startup error", f"Failed during early setup: {e}")
        return 1

    try:
        from app.main import app as fastapi_app
    except Exception as e:
        log(f"Failed to import app.main: {e}")
        try:
            import traceback
            tb = "".join(traceback.format_exc())
            for line in tb.rstrip().splitlines(): logger.info(line)
        except Exception:
            pass
        _msgbox("Import error", f"Failed to import app.main:\n{e}")
        return 1

    try:
        import uvicorn
    except Exception as e:
        log(f"Failed to import uvicorn: {e}")
        _msgbox("Import error", f"Failed to import uvicorn:\n{e}")
        return 1

    host = os.getenv("HOST", "127.0.0.1")
    try:
        port = int(os.getenv("PORT", "8000"))
    except ValueError:
        port = 8000

    url = f"http://{host}:{port}"
    log(f"Starting server on {url}")

    # Open the browser shortly after startup (helps when double-clicking a windowed EXE).
    _open_browser(url)

    try:
        uvicorn.run(
            fastapi_app,
            host=host,
            port=port,
            reload=False,
            log_level=os.getenv("LOG_LEVEL", "info"),
            log_config=None,   # critical in frozen apps to avoid stdout/isatty issues
            access_log=False   # optional: quieter logs
        )
    except KeyboardInterrupt:
        log("Shutting down (KeyboardInterrupt)")
    except Exception as e:
        log(f"Server crashed: {e}")
        try:
            import traceback
            tb = "".join(traceback.format_exc())
            for line in tb.rstrip().splitlines(): logger.info(line)
        except Exception:
            pass
        _msgbox("Server error", f"Server crashed:\n{e}")
        return 1

    log("Server stopped")
    return 0

if __name__ == "__main__":
    sys.exit(main())