import importlib
import os
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture
def app(monkeypatch):
    """Fresh app bound to a temporary database."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("SPENDLY_DB_PATH", path)
    monkeypatch.setenv("SECRET_KEY", "test-secret")

    import database.db as db
    importlib.reload(db)
    import app as app_module
    importlib.reload(app_module)

    app_module.app.config["TESTING"] = True
    yield app_module.app
    try:
        os.remove(path)
    except OSError:
        pass


@pytest.fixture
def client(app):
    return app.test_client()
