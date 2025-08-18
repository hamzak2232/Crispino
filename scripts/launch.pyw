import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def setup_paths() -> str:
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
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, "runtime.log")

    logger = logging.getLogger("launcher")
    logger.setLevel(logging.INFO)
    logger.handlers[:] = []

    fmt = logging.Formatter("%(message)s")

    fh = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt)
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)

    try:
        ch = logging.StreamHandler(stream=sys.stdout)
        ch.setFormatter(fmt)
        ch.setLevel(logging.INFO)
        logger.addHandler(ch)
    except Exception:
        pass

    return logger

def main() -> int:
    base_dir = setup_paths()
    logger = setup_logging(base_dir)
    def log(msg: str) -> None:
        logger.info(f"[{ts()}] {msg}")

    try:
        from app.main import app as fastapi_app
    except Exception as e:
        log(f"Failed to import app.main: {e}")
        try:
            import traceback
            tb = "".join(traceback.format_exc())
            for line in tb.rstrip().splitlines():
                logger.info(line)
        except Exception:
            pass
        return 1

    try:
        import uvicorn
    except Exception as e:
        log(f"Failed to import uvicorn: {e}")
        return 1

    host = os.getenv("HOST", "127.0.0.1")
    try:
        port = int(os.getenv("PORT", "8000"))
    except ValueError:
        port = 8000

    log(f"Starting server on http://{host}:{port}")
    try:
        uvicorn.run(
            fastapi_app,
            host=host,
            port=port,
            reload=False,
            log_level=os.getenv("LOG_LEVEL", "info"),
            log_config=None,          # critical for frozen apps
            access_log=False          # optional: avoid access log formatter
        )
    except KeyboardInterrupt:
        log("Shutting down (KeyboardInterrupt)")
    except Exception as e:
        log(f"Server crashed: {e}")
        try:
            import traceback
            tb = "".join(traceback.format_exc())
            for line in tb.rstrip().splitlines():
                logger.info(line)
        except Exception:
            pass
        return 1

    log("Server stopped")
    return 0

if __name__ == "__main__":
    sys.exit(main())