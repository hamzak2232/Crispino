# Robust windowed launcher for the packaged POS.
# - Imports the ASGI app object directly (no dotted string).
# - Chooses a free port if 8000 is busy.
# - Logs errors to logs/launcher.log next to the EXE (and prints in console builds).
# - Opens the browser when the server is ready.

import threading
import time
import webbrowser
import socket
import sys
import traceback
from pathlib import Path

# Eager imports so PyInstaller collects these packages
import uvicorn  # runtime server
import fastapi  # ensure bundled
import starlette  # ensure bundled
import jinja2  # ensure bundled

HOST = "127.0.0.1"
START_PORT = 8000
MAX_PORT = 8010  # try up to this port if 8000 is busy


def base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


LOG_DIR = base_dir() / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "launcher.log"


def log(msg: str) -> None:
    # Write to file and to console (useful for console builds)
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    try:
        print(line, flush=True)
    except Exception:
        pass


def log_exc(prefix: str, e: BaseException) -> None:
    tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
    log(prefix)
    log(tb)


def is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.25)
        return s.connect_ex((host, port)) == 0


def find_free_port(host: str, start: int, end: int) -> int:
    for p in range(start, end + 1):
        if not is_port_open(host, p):
            return p
    raise RuntimeError(f"No free port between {start} and {end}")


def run_server(server_holder: dict):
    try:
        # Ensure the unpacked resources (app/ templates/static) are importable when frozen
        here = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))  # type: ignore[attr-defined]
        sys.path.insert(0, str(here))
        sys.path.insert(0, str(base_dir()))

        # Import ASGI app directly
        try:
            from app.main import app as asgi_app  # type: ignore
        except Exception as e:
            log_exc("Failed to import app.main:", e)
            server_holder["error"] = f"Import error: {e}"
            return

        port = find_free_port(HOST, START_PORT, MAX_PORT)
        server_holder["port"] = port

        config = uvicorn.Config(
            asgi_app,
            host=HOST,
            port=port,
            reload=False,
            log_level="info",
        )
        server = uvicorn.Server(config)
        server_holder["server"] = server
        log(f"Starting server on http://{HOST}:{port}/")
        server.run()
        log("Server stopped.")
    except Exception as e:
        log_exc("Server thread crashed:", e)
        server_holder["error"] = str(e)


def main():
    # Try to show a tiny GUI; fall back to headless if Tk not available
    try:
        import tkinter as tk
    except Exception:
        server_holder = {}
        t = threading.Thread(target=run_server, args=(server_holder,), daemon=True)
        t.start()
        # Wait for server or error
        for _ in range(120):
            if "error" in server_holder:
                break
            port = server_holder.get("port")
            if port and is_port_open(HOST, port):
                webbrowser.open_new_tab(f"http://{HOST}:{port}/")
                break
            time.sleep(0.25)
        # Keep process alive while server runs
        try:
            while t.is_alive():
                time.sleep(0.25)
        except KeyboardInterrupt:
            if server_holder.get("server"):
                server_holder["server"].should_exit = True
        return

    root = tk.Tk()
    root.title("Crispino POS")
    root.geometry("420x160")
    root.resizable(False, False)

    status_var = tk.StringVar(value="Starting server...")
    tk.Label(root, textvariable=status_var, padx=10, pady=10, justify="left").pack(anchor="w")

    btns = tk.Frame(root)
    open_btn = tk.Button(btns, text="Open POS", width=12, state="disabled")
    quit_btn = tk.Button(btns, text="Quit", width=12, command=root.destroy)
    open_btn.pack(side=tk.LEFT, padx=6)
    quit_btn.pack(side=tk.LEFT, padx=6)
    btns.pack(pady=8)

    server_holder = {}
    t = threading.Thread(target=run_server, args=(server_holder,), daemon=True)
    t.start()

    def poll():
        if "error" in server_holder:
            status_var.set(f"Error starting server.\nSee {LOG_FILE}\n\n{server_holder['error']}")
            open_btn.config(state="disabled")
            return
        port = server_holder.get("port")
        if port and is_port_open(HOST, port):
            status_var.set(f"Server running on http://{HOST}:{port}/")
            open_btn.config(state="normal")
            # Auto-open once
            if not getattr(poll, "_opened", False):
                webbrowser.open_new_tab(f"http://{HOST}:{port}/")
                poll._opened = True
        root.after(300, poll)

    def open_pos():
        port = server_holder.get("port", START_PORT)
        webbrowser.open_new_tab(f"http://{HOST}:{port}/")

    open_btn.config(command=open_pos)
    root.after(200, poll)

    def on_close():
        srv = server_holder.get("server")
        if srv:
            srv.should_exit = True
        root.after(200, root.quit)

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()