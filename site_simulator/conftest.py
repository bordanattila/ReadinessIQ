"""Pytest setup: isolate site_simulator's `app` package from backend's."""

import sys
from pathlib import Path

import pytest

SITE_SIM_ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = SITE_SIM_ROOT.parent / 'backend'
BACKEND_SCRIPTS = BACKEND_ROOT / 'scripts'
EXCLUDED_PATHS = {BACKEND_ROOT.resolve(), BACKEND_SCRIPTS.resolve()}


def _isolate_site_simulator_imports() -> None:
    sys.path[:] = [
        path
        for path in sys.path
        if not path or Path(path).resolve() not in EXCLUDED_PATHS
    ]
    if str(SITE_SIM_ROOT) not in sys.path:
        sys.path.insert(0, str(SITE_SIM_ROOT))

    for module_name in list(sys.modules):
        if module_name == 'app' or module_name.startswith('app.'):
            del sys.modules[module_name]


_isolate_site_simulator_imports()


@pytest.fixture(autouse=True)
def isolate_site_simulator_app():
    _isolate_site_simulator_imports()
    yield
