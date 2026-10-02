import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CONFIG = ROOT / "config" / "jsonflow"


@pytest.fixture
def servers_config():
    return json.loads((CONFIG / "servers.json").read_text())


@pytest.fixture
def sajha_fixture():
    return json.loads((CONFIG / "fixtures" / "sajha_sector_events.json").read_text())


@pytest.fixture
def llm_fixture():
    return json.loads((CONFIG / "fixtures" / "llm_sector_events.json").read_text())


@pytest.fixture
def workflow_path():
    return CONFIG / "workflows" / "sector_events.json"
