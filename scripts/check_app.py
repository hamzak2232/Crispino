import sys, os, pathlib, importlib.util

print("CWD:", os.getcwd())
print("Python:", sys.version)

# Ensure repo root (parent of this file's directory) is on sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
print("Added to sys.path:", repo_root)

spec = importlib.util.find_spec("app")
print("app spec:", spec)
print("app origin:", None if spec is None else spec.origin)

if spec and spec.origin:
    app_dir = pathlib.Path(spec.origin).parent
    print("app package dir:", app_dir)
    print("Contents of app dir:")
    for p in app_dir.iterdir():
        print(" -", p.name)