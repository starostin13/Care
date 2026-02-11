import os
import sys
import asyncio
import types

MODULE_DIR = os.path.join(os.path.dirname(__file__), '..', 'CareBot')
sys.path.insert(0, os.path.abspath(MODULE_DIR))

os.environ['CAREBOT_TEST_MODE'] = 'true'
sys.modules.setdefault("config", types.SimpleNamespace(TEST_MODE=True))

import mission_helper  # noqa: E402


class DummyMissionDetails:
    def __init__(self):
        self.id = 1
        self.deploy = "Test Deploy"
        self.rules = "wh40k"
        self.cell = None
        self.mission_description = "Test mission"
        self.winner_bonus = None
        self.status = 0
        self.created_date = "2025-01-01"
        self.map_description = None
        self.reward_config = "COMMON_RESOURCE: 3"


def test_apply_mission_rewards_adds_base_and_bonus(monkeypatch):
    calls = []

    async def get_opponent_telegram_id(battle_id, user_telegram_id):
        return "opponent"

    async def get_mission_id_by_battle_id(battle_id):
        return 1

    async def get_mission_details(mission_id):
        return DummyMissionDetails()

    async def get_winner_bonus(mission_id):
        return None

    async def get_alliance_of_warmaster(telegram_id):
        return (1,) if str(telegram_id) == "user" else (2,)

    async def increase_common_resource(alliance_id, amount=1):
        calls.append(("inc", alliance_id, amount))
        return 0

    async def decrease_common_resource(alliance_id, amount=1):
        calls.append(("dec", alliance_id, amount))
        return 0

    async def get_hexes_by_alliance(alliance_id):
        return [(1,)]

    # Patch sqllite_helper functions used in apply_mission_rewards
    monkeypatch.setattr(mission_helper.sqllite_helper, "get_opponent_telegram_id", get_opponent_telegram_id)
    monkeypatch.setattr(mission_helper.sqllite_helper, "get_mission_id_by_battle_id", get_mission_id_by_battle_id)
    monkeypatch.setattr(mission_helper.sqllite_helper, "get_mission_details", get_mission_details)
    monkeypatch.setattr(mission_helper.sqllite_helper, "get_winner_bonus", get_winner_bonus)
    monkeypatch.setattr(mission_helper.sqllite_helper, "get_alliance_of_warmaster", get_alliance_of_warmaster)
    monkeypatch.setattr(mission_helper.sqllite_helper, "increase_common_resource", increase_common_resource)
    monkeypatch.setattr(mission_helper.sqllite_helper, "decrease_common_resource", decrease_common_resource)
    monkeypatch.setattr(mission_helper.sqllite_helper, "get_hexes_by_alliance", get_hexes_by_alliance)

    async def run():
        return await mission_helper.apply_mission_rewards(
            battle_id=10,
            user_reply="10 5",
            user_telegram_id="user"
        )

    result = asyncio.run(run())

    assert result["winner_alliance_id"] == 1
    assert ("inc", 1, 1) in calls  # base reward for user alliance
    assert ("inc", 2, 1) in calls  # base reward for opponent alliance
    assert ("inc", 1, 3) in calls  # mission resource bonus for winner
