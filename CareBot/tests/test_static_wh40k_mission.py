"""
Tests for static WH40K mission selection logic in mission_helper.py.

Covers:
- Static dataset path is used when available (50% chance path)
- Fallback to generator when static table is unavailable (exception)
- Fallback to generator when static dataset is empty (count == 0)
- Winner bonus and deploy asset path handling for static missions
"""
import os
import sys
import asyncio
import types

MODULE_DIR = os.path.join(os.path.dirname(__file__), '..', 'CareBot')
sys.path.insert(0, os.path.abspath(MODULE_DIR))

os.environ['CAREBOT_TEST_MODE'] = 'true'
sys.modules.setdefault("config", types.SimpleNamespace(TEST_MODE=True))

import mission_helper  # noqa: E402
import mock_sqlite_helper  # noqa: E402


# ---------------------------------------------------------------------------
# Tests for _build_static_wh40k_mission_tuple
# ---------------------------------------------------------------------------

def test_build_static_wh40k_mission_tuple_winner_bonus_populated():
    """Static mission tuples must always carry a non-None winner bonus."""
    static_mission = {
        'mission_name': 'Armageddon Strike',
        'mission_code': 'ARM-01',
        'mission_text_full': 'Hold the line at all costs.',
        'deploy_asset_path': 'custom_deploy.jpg',
    }
    result = mission_helper._build_static_wh40k_mission_tuple(static_mission)
    # Tuple: (deploy, rules, cell, description, winner_bonus, map_description)
    winner_bonus = result[4]
    assert winner_bonus is not None, "Winner bonus must be populated for static WH40K missions"
    assert isinstance(winner_bonus, str) and len(winner_bonus) > 0


def test_build_static_wh40k_mission_tuple_uses_deploy_asset_path():
    """deploy_asset_path field should be preferred for the deploy image."""
    static_mission = {
        'mission_name': 'Strike',
        'mission_code': 'S-01',
        'mission_text_full': 'Mission text.',
        'deploy_asset_path': 'my_deploy.jpg',
        'map_asset_path': 'my_map.jpg',
    }
    result = mission_helper._build_static_wh40k_mission_tuple(static_mission)
    assert result[0] == 'my_deploy.jpg'


def test_build_static_wh40k_mission_tuple_falls_back_to_map_asset():
    """map_asset_path should be used when deploy_asset_path is absent."""
    static_mission = {
        'mission_name': 'Strike',
        'mission_code': 'S-01',
        'mission_text_full': 'Mission text.',
        'deploy_asset_path': None,
        'map_asset_path': 'fallback_map.jpg',
    }
    result = mission_helper._build_static_wh40k_mission_tuple(static_mission)
    assert result[0] == 'fallback_map.jpg'


def test_build_static_wh40k_mission_tuple_default_deploy_when_no_asset():
    """Default deploy image is used when both asset fields are absent/None."""
    static_mission = {
        'mission_name': 'Strike',
        'mission_code': 'S-01',
        'mission_text_full': 'Mission text.',
    }
    result = mission_helper._build_static_wh40k_mission_tuple(static_mission)
    assert result[0] == 'total_domination.jpg'


def test_build_static_wh40k_mission_tuple_rules_and_cell():
    """Rules must be 'wh40k' and cell must be None for static missions."""
    static_mission = {
        'mission_name': 'Strike',
        'mission_code': 'S-01',
        'mission_text_full': 'Mission text.',
    }
    result = mission_helper._build_static_wh40k_mission_tuple(static_mission)
    assert result[1] == 'wh40k'
    assert result[2] is None   # cell
    assert result[5] is None   # map_description


def test_build_static_wh40k_mission_tuple_description_format():
    """Description must include the mission name and code as a title."""
    static_mission = {
        'mission_name': 'Total War',
        'mission_code': 'TW-42',
        'mission_text_full': 'Fight until the last.',
    }
    result = mission_helper._build_static_wh40k_mission_tuple(static_mission)
    description = result[3]
    assert 'Total War' in description
    assert 'TW-42' in description
    assert 'Fight until the last.' in description


# ---------------------------------------------------------------------------
# Tests for _try_create_static_wh40k_mission
# ---------------------------------------------------------------------------

def test_try_create_static_wh40k_mission_uses_static_when_available(monkeypatch):
    """Static mission is created when dataset is non-empty and random favours it."""
    static_row = {
        'mission_name': 'Armageddon',
        'mission_code': 'ARM-01',
        'mission_text_full': 'Hold the line.',
        'deploy_asset_path': 'arm_deploy.jpg',
    }
    saved = []

    async def fake_count(rules):
        return 5

    async def fake_random_mission(rules):
        return static_row

    async def fake_save(mission_tuple):
        saved.append(mission_tuple)

    monkeypatch.setattr(mission_helper.sqllite_helper, 'get_static_armageddon_mission_count', fake_count)
    monkeypatch.setattr(mission_helper.sqllite_helper, 'get_random_static_armageddon_mission', fake_random_mission)
    monkeypatch.setattr(mission_helper.sqllite_helper, 'save_mission', fake_save)
    # Force random.random() to return a value < 0.5 so the static path is taken
    monkeypatch.setattr(mission_helper.random, 'random', lambda: 0.1)

    result = asyncio.run(mission_helper._try_create_static_wh40k_mission())

    assert result is True
    assert len(saved) == 1
    # Saved tuple must have winner_bonus populated
    assert saved[0][4] is not None


def test_try_create_static_wh40k_mission_skips_when_random_high(monkeypatch):
    """When random >= 0.5 the static path should be skipped (returns False)."""
    async def fake_count(rules):
        return 5

    monkeypatch.setattr(mission_helper.sqllite_helper, 'get_static_armageddon_mission_count', fake_count)
    # Force random to return >= 0.5
    monkeypatch.setattr(mission_helper.random, 'random', lambda: 0.9)

    result = asyncio.run(mission_helper._try_create_static_wh40k_mission())

    assert result is False


def test_try_create_static_wh40k_mission_fallback_on_table_unavailable(monkeypatch):
    """Exception from count query causes graceful fallback (returns False)."""
    async def fake_count(rules):
        raise RuntimeError("table armageddon_static_missions does not exist")

    monkeypatch.setattr(mission_helper.sqllite_helper, 'get_static_armageddon_mission_count', fake_count)

    result = asyncio.run(mission_helper._try_create_static_wh40k_mission())

    assert result is False


def test_try_create_static_wh40k_mission_fallback_when_empty(monkeypatch):
    """When count == 0 the static path should be skipped (returns False)."""
    async def fake_count(rules):
        return 0

    monkeypatch.setattr(mission_helper.sqllite_helper, 'get_static_armageddon_mission_count', fake_count)

    result = asyncio.run(mission_helper._try_create_static_wh40k_mission())

    assert result is False


def test_try_create_static_wh40k_mission_fallback_when_no_row_returned(monkeypatch):
    """When get_random_static_armageddon_mission returns None, return False."""
    async def fake_count(rules):
        return 3

    async def fake_random_mission(rules):
        return None

    monkeypatch.setattr(mission_helper.sqllite_helper, 'get_static_armageddon_mission_count', fake_count)
    monkeypatch.setattr(mission_helper.sqllite_helper, 'get_random_static_armageddon_mission', fake_random_mission)
    monkeypatch.setattr(mission_helper.random, 'random', lambda: 0.1)

    result = asyncio.run(mission_helper._try_create_static_wh40k_mission())

    assert result is False


# ---------------------------------------------------------------------------
# Integration: get_mission uses static path vs generator
# ---------------------------------------------------------------------------

class _FakeMission:
    """Minimal Mission-like object returned by sqllite_helper.get_mission."""
    def __init__(self):
        self.id = 99
        self.deploy = 'arm_deploy.jpg'
        self.rules = 'wh40k'
        self.cell = None
        self.mission_description = 'Armageddon mission'
        self.winner_bonus = 'Some bonus'
        self.status = 0
        self.created_date = '2025-01-01'
        self.map_description = None
        self.reward_config = None

    def to_tuple(self):
        return (self.deploy, self.rules, self.cell, self.mission_description, self.id, self.winner_bonus)


def test_get_mission_uses_static_path_when_available(monkeypatch):
    """get_mission creates a static mission when static data is available."""
    static_created_flag = []

    async def fake_get_mission_first_call(rules):
        # First call returns None (no existing mission), subsequent calls return one
        if not static_created_flag:
            return None
        return _FakeMission()

    async def fake_try_create_static():
        static_created_flag.append(True)
        return True

    async def fake_ensure_cell(mission_id, attacker_id, defender_id):
        return None

    monkeypatch.setattr(mission_helper.sqllite_helper, 'get_mission', fake_get_mission_first_call)
    monkeypatch.setattr(mission_helper, '_try_create_static_wh40k_mission', fake_try_create_static)
    monkeypatch.setattr(mission_helper, 'ensure_mission_cell', fake_ensure_cell)

    result = asyncio.run(mission_helper.get_mission('wh40k'))

    assert static_created_flag, "_try_create_static_wh40k_mission should have been called"
    assert result is not None


def test_get_mission_uses_generator_when_static_unavailable(monkeypatch):
    """get_mission falls back to generate_new_one when static creation fails."""
    generator_called = []
    saved = []

    async def fake_get_mission(rules):
        if not saved:
            return None
        return _FakeMission()

    async def fake_try_create_static():
        return False  # static path not taken

    def fake_generate_new_one(rules):
        generator_called.append(rules)
        return ('deploy.jpg', rules, None, 'Generated mission', 'Winner bonus', None)

    async def fake_save_mission(mission_tuple):
        saved.append(mission_tuple)

    async def fake_ensure_cell(mission_id, attacker_id, defender_id):
        return None

    monkeypatch.setattr(mission_helper.sqllite_helper, 'get_mission', fake_get_mission)
    monkeypatch.setattr(mission_helper, '_try_create_static_wh40k_mission', fake_try_create_static)
    monkeypatch.setattr(mission_helper, 'generate_new_one', fake_generate_new_one)
    monkeypatch.setattr(mission_helper.sqllite_helper, 'save_mission', fake_save_mission)
    monkeypatch.setattr(mission_helper, 'ensure_mission_cell', fake_ensure_cell)

    result = asyncio.run(mission_helper.get_mission('wh40k'))

    assert generator_called, "generate_new_one should have been called as fallback"
    assert result is not None
