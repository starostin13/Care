import asyncio
import os
import sys
from datetime import datetime

# Add module directory to path
MODULE_DIR = os.path.join(os.path.dirname(__file__), '..', 'CareBot')
sys.path.insert(0, os.path.abspath(MODULE_DIR))

# Ensure config exists for test mode
config_path = os.path.join(MODULE_DIR, 'config.py')
if not os.path.exists(config_path):
    with open(config_path, 'w') as cfg:
        cfg.write('TEST_MODE = True\ncrusade_care_bot_telegram_token = "test_token"\n')

# Enable mock helper
os.environ['CAREBOT_TEST_MODE'] = 'true'

import players_helper  # noqa: E402
import mock_sqlite_helper  # noqa: E402


def test_other_format_opponents():
    async def run_check():
        mock_sqlite_helper.MOCK_SCHEDULES.clear()

        game_date = datetime(2024, 4, 27)
        date_str = game_date.strftime('%c')
        # User 2 registers for wh40k on the target date
        mock_sqlite_helper.MOCK_SCHEDULES[str(game_date.date())] = [{
            'date': str(game_date.date()),
            'rules': 'wh40k',
            'user_telegram': mock_sqlite_helper.MOCK_WARMASTERS[2]['telegram_id']
        }]

        opponents = await players_helper.get_opponents_other_formats(
            int(mock_sqlite_helper.MOCK_WARMASTERS[1]['telegram_id']),
            f"{date_str},rule:killteam"
        )

        assert len(opponents) == 1
        nickname, phone, rule = opponents[0]
        assert nickname == mock_sqlite_helper.MOCK_WARMASTERS[2]['nickname']
        assert phone == mock_sqlite_helper.MOCK_WARMASTERS[2]['registered_as']
        assert rule == 'wh40k'

    asyncio.run(run_check())
