import importlib.util, pathlib, sys

print("Python:", sys.version)
try:
    import pydantic_core
    print("pydantic_core imported OK")
    print("pydantic_core.__file__ =", getattr(pydantic_core, "__file__", "missing"))
    print("pydantic_core version:", getattr(pydantic_core, "__version__", "unknown"))
except Exception as e:
    print("pydantic_core import error:", repr(e))

spec = importlib.util.find_spec("pydantic_core._pydantic_core")
print("_pydantic_core spec:", spec)
print("_pydantic_core origin:", None if spec is None else spec.origin)