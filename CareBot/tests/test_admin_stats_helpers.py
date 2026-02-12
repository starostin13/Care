import os
import sys
import asyncio
import types

MODULE_DIR = os.path.join(os.path.dirname(__file__), '..', 'CareBot')
sys.path.insert(0, os.path.abspath(MODULE_DIR))

os.environ['CAREBOT_TEST_MODE'] = 'true'
sys.modules.setdefault("config", types.SimpleNamespace(TEST_MODE=True))

import mock_sqlite_helper  # noqa: E402


def test_mock_stats_helpers_provide_data():
    users = asyncio.run(mock_sqlite_helper.get_user_game_counts_last_month())
    alliances = asyncio.run(mock_sqlite_helper.get_alliance_game_counts_last_month())

    assert users
    assert alliances

    target_alliance = users[0][2]
    filtered = asyncio.run(
        mock_sqlite_helper.get_user_game_counts_last_month(alliance_id=target_alliance)
    )
    assert all(row[2] == target_alliance for row in filtered)
