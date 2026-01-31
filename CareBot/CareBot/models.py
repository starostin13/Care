"""
Data models for CareBot.

Using dataclasses for type safety and clear structure.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import date


@dataclass
class Mission:
    """Mission from mission_stack table."""
    id: int
    deploy: str
    rules: str
    cell: Optional[int]
    mission_description: str
    winner_bonus: Optional[str]
    locked: int
    created_date: str
    
    @classmethod
    def from_db_row(cls, row):
        """Create Mission from database row.
        
        Args:
            row: tuple from SELECT * FROM mission_stack
                 (id, deploy, rules, cell, mission_description, winner_bonus, locked, created_date)
        """
        if not row:
            return None
        return cls(
            id=row[0],
            deploy=row[1],
            rules=row[2],
            cell=row[3],
            mission_description=row[4],
            winner_bonus=row[5],
            locked=row[6],
            created_date=row[7]
        )
    
    def to_tuple(self):
        """Convert to tuple for backwards compatibility.
        
        Returns tuple in old format:
        (deploy, rules, cell, mission_description, winner_bonus)
        """
        return (self.deploy, self.rules, self.cell, self.mission_description, self.winner_bonus)


@dataclass
class Battle:
    """Battle from battles table."""
    id: int
    mission_id: Optional[int]
    fstplayer: Optional[int]  # First player score
    sndplayer: Optional[int]  # Second player score
    
    @classmethod
    def from_db_row(cls, row):
        """Create Battle from database row.
        
        Args:
            row: tuple from SELECT * FROM battles
                 (id, mission_id, fstplayer, sndplayer)
        """
        if not row:
            return None
        return cls(
            id=row[0],
            mission_id=row[1],
            fstplayer=row[2],
            sndplayer=row[3]
        )


@dataclass
class MissionDetails:
    """Extended mission details with all metadata."""
    id: int
    deploy: str
    rules: str
    cell: Optional[int]
    mission_description: str
    winner_bonus: Optional[str]
    locked: int
    created_date: str
    # Extended fields added by mission_helper
    killzone: Optional[str] = None
    hex_state: Optional[str] = None
    battle_points: Optional[str] = None
    history: Optional[list] = None
    
    @classmethod
    def from_mission(cls, mission: Mission):
        """Create MissionDetails from Mission."""
        return cls(
            id=mission.id,
            deploy=mission.deploy,
            rules=mission.rules,
            cell=mission.cell,
            mission_description=mission.mission_description,
            winner_bonus=mission.winner_bonus,
            locked=mission.locked,
            created_date=mission.created_date
        )


@dataclass
class Warmaster:
    """Warmaster (player) from warmasters table."""
    telegram_id: str
    alliance: Optional[int]
    nickname: Optional[str]
    language: Optional[str]
    notification_enabled: Optional[int]
    is_admin: Optional[int]
    
    @classmethod
    def from_db_row(cls, row):
        """Create Warmaster from database row."""
        if not row:
            return None
        return cls(
            telegram_id=row[0],
            alliance=row[1] if len(row) > 1 else None,
            nickname=row[2] if len(row) > 2 else None,
            language=row[3] if len(row) > 3 else None,
            notification_enabled=row[4] if len(row) > 4 else None,
            is_admin=row[5] if len(row) > 5 else None
        )


@dataclass
class Alliance:
    """Alliance from alliances table."""
    id: int
    name: str
    color: str
    common_resource: int
    
    @classmethod
    def from_db_row(cls, row):
        """Create Alliance from database row."""
        if not row:
            return None
        return cls(
            id=row[0],
            name=row[1],
            color=row[2],
            common_resource=row[3]
        )


@dataclass
class MapCell:
    """Map cell (hex) from map table."""
    id: int
    patron: Optional[int]  # Alliance ID
    q: int  # Hex coordinate q
    r: int  # Hex coordinate r
    state: Optional[str]
    
    @classmethod
    def from_db_row(cls, row):
        """Create MapCell from database row."""
        if not row:
            return None
        return cls(
            id=row[0],
            patron=row[1],
            q=row[2],
            r=row[3],
            state=row[4] if len(row) > 4 else None
        )
