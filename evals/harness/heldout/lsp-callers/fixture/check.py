"""Pass = fetch requires a keyword-only timeout AND every caller (including the aliased one) runs."""
import inspect
import sys

sys.path.insert(0, ".")
import net  # noqa: E402
from app import health, sync  # noqa: E402

params = inspect.signature(net.fetch).parameters
ok = "timeout" in params and params["timeout"].default is inspect.Parameter.empty
try:
    ok = ok and sync.pull_all(["a", "b"])[1]["url"] == "b" and health.ping() is True
except TypeError:
    ok = False
sys.exit(0 if ok else 1)
