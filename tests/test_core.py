from pathlib import Path

from arm_ripper.config import AppConfig
from arm_ripper.ripper import safe_name
from arm_ripper.state import StateStore


def test_default_port_is_9090():
    assert AppConfig().port == 9090


def test_safe_name_removes_problematic_path_characters():
    assert safe_name('../AC/DC: Live!') == 'AC_DC_ Live'


def test_state_store_persists_drives(tmp_path: Path):
    state_file = tmp_path / 'state.json'
    store = StateStore(state_file)
    store.set_drives([{'id': 'sr0', 'device': '/dev/sr0', 'status': 'bereit'}])
    store.save()

    restored = StateStore(state_file)
    assert restored.snapshot()['drives']['sr0']['device'] == '/dev/sr0'
