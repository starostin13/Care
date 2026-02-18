"""
Armagedon Anomalies Feature - Warp-based mission modifiers.

This feature adds anomalies and hellscapes to missions played on or near
Warp-altered Space hexes during the Armagedon crusade.
"""
import logging
import random
from typing import Dict, Any, Optional, Tuple
from features import Feature
import config

# Автоматическое переключение на mock версию в тестовом режиме
if config.TEST_MODE:
    import mock_sqlite_helper as sqllite_helper
    print("🧪 Armagedon Anomalies Feature using MOCK SQLite helper")
else:
    import sqllite_helper
    print("✅ Armagedon Anomalies Feature using REAL SQLite helper")

logger = logging.getLogger(__name__)

# Anomaly matrix: [timing][intensity]
# Numbers indicate count of anomalies
ANOMALY_MATRIX = [
    ['1; Начало второго хода', '1; Начало 2го и 3го хода', '1; Начало 2го, 3го, 4го хода'],
    ['1; Начало каждого раунда', '2; Начало каждого раунда', '3; Начало каждого раунда'],
    ['1; Начало каждого тёрна', '2; Начало каждого тёрна', '3; Начало каждого тёрна']
]

# Hellscape types
HELLSCAPES = [
    "Folded Space",
    "Fractured Realm",
    "Fading Reality",
    "Scattered Coordinates",
    "Staggered Time",
    "Banishing Rifts",
    "Gravitic Nexus",
    "Endless Nightmare"
]


class ArmagedonAnomaliesFeature(Feature):
    """
    Armagedon Anomalies - Warp-based mission modifiers.

    When enabled:
    - Missions on Warp-altered Space hexes have maximum anomalies
    - Missions adjacent to warp hexes have random anomalies
    - Other missions may or may not have anomalies
    - Hellscapes are applied based on warp proximity
    """

    def __init__(self):
        super().__init__(
            flag_name='armagedon_anomalies',
            description='Warp-based anomalies and hellscapes for Armagedon crusade'
        )

    async def on_create_mission(self, mission_data: Dict[str, Any]) -> None:
        """
        Modify mission when created based on warp cell proximity.

        Args:
            mission_data: Dictionary with mission information including:
                - mission_id: int - Mission ID
                - rules: str - Game rules
                - cell: Optional[int] - Map cell
                - description: str - Mission description
        """
        cell_id = mission_data.get('cell')

        # Only apply to missions with assigned cells
        if cell_id is None:
            logger.debug("No cell assigned, skipping anomalies")
            return

        # Determine warp status
        warp_status = await self._get_warp_status(cell_id)
        logger.info(f"Mission on cell {cell_id} has warp status: {warp_status}")

        # Generate anomalies based on warp status
        anomaly_text, hellscape_text = await self._generate_anomalies(warp_status)

        if anomaly_text or hellscape_text:
            # Build combined anomaly description
            anomaly_parts = []
            if anomaly_text:
                anomaly_parts.append(f"⚠️ Аномалии: {anomaly_text}")
            if hellscape_text:
                anomaly_parts.append(f"🌀 Hellscape: {hellscape_text}")

            anomaly_description = "\n".join(anomaly_parts)

            # Update mission description
            mission_id = mission_data.get('mission_id')
            current_description = mission_data.get('description', '')

            # Append anomalies to description
            new_description = f"{current_description}\n\n{anomaly_description}"

            await sqllite_helper.update_mission_description(mission_id, new_description)
            logger.info(f"Added anomalies to mission {mission_id}: {anomaly_description}")

    async def _get_warp_status(self, cell_id: int) -> str:
        """
        Determine warp proximity status for a cell.

        Args:
            cell_id: Map cell ID

        Returns:
            'on_warp' - Cell is Warp-altered Space
            'adjacent_warp' - Adjacent to warp cell
            'no_warp' - No warp nearby
        """
        # Check if current cell is warp
        cell_state = await sqllite_helper.get_state(cell_id)
        if cell_state == "Warp-altered Space":
            return 'on_warp'

        # Check if any adjacent cell is warp
        adjacent_cells = await sqllite_helper.get_adjacent_cells(cell_id)
        for adj_cell_id in adjacent_cells:
            adj_state = await sqllite_helper.get_state(adj_cell_id)
            if adj_state == "Warp-altered Space":
                return 'adjacent_warp'

        return 'no_warp'

    async def _generate_anomalies(self, warp_status: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate anomaly and hellscape text based on warp status.

        Args:
            warp_status: Warp proximity ('on_warp', 'adjacent_warp', 'no_warp')

        Returns:
            Tuple of (anomaly_text, hellscape_text)
        """
        anomaly_text = None
        hellscape_text = None

        if warp_status == 'on_warp':
            # Maximum anomalies (both parameters at max - bottom right of matrix)
            anomaly_text = ANOMALY_MATRIX[2][2]  # Maximum timing and intensity

            # Random hellscape from last 4
            hellscape_text = random.choice(HELLSCAPES[4:])

        elif warp_status == 'adjacent_warp':
            # Random anomaly parameters
            timing = random.randint(0, 2)
            intensity = random.randint(0, 2)
            anomaly_text = ANOMALY_MATRIX[timing][intensity]

            # Random hellscape from last 4
            hellscape_text = random.choice(HELLSCAPES[4:])

        else:  # no_warp
            # 50% chance of no anomalies
            if random.random() < 0.5:
                return None, None

            # Otherwise random anomaly parameters
            timing = random.randint(0, 2)
            intensity = random.randint(0, 2)
            anomaly_text = ANOMALY_MATRIX[timing][intensity]

            # 50% chance of no hellscape
            if random.random() < 0.5:
                hellscape_text = None
            else:
                # Random hellscape from first 4
                hellscape_text = random.choice(HELLSCAPES[:4])

        return anomaly_text, hellscape_text


# Create and export the feature instance
armagedon_anomalies_feature = ArmagedonAnomaliesFeature()
