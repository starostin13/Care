"""
Helpers for offline sync and data export for mobile applications.
Handles mission export for caching and battle result synchronization with territory calculation.

Architecture:
- export_mission_generation_templates() - Templates to GENERATE new missions offline
- export_active_missions() - Current missions for display
- export_map_data_for_cache() - Map edges for territory calculations
- process_synced_battle_results() - Apply results on server
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import aiosqlite

logger = logging.getLogger("SyncHelper")


async def export_mission_generation_templates(db_path: str) -> Dict[str, Any]:
    """
    Export mission templates and rules for GENERATING new missions offline.
    
    This includes:
    - Mission types (Secure, Intel, Coordinates, Loot, etc.)
    - Descriptions for each mission type
    - Reward configurations
    - WH40K bonus templates (for winners only - never exported!)
    - Kill Team vs WH40K ruleset metadata
    
    Returns:
        {
            'templates': {
                'kill_team': [...],      # Kill Team mission types
                'wh40k': [...]           # WH40K mission types
            },
            'map': {
                'hex_locations': [...],  # Available map locations
                'adjacency': [...]       # Territory adjacency for Secure missions
            },
            'timestamp': ISO datetime,
            'version': '1.0'
        }
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            # Get Kill Team mission templates
            cursor = await db.execute("""
                SELECT DISTINCT mission_type, reward_type, mission_description
                FROM mission_stack
                WHERE rules IS NULL OR rules != 'wh40k'
                ORDER BY mission_type
            """)
            kill_team_missions = await cursor.fetchall()
            
            # Get WH40K mission templates (no winner_bonus in cache!)
            cursor = await db.execute("""
                SELECT DISTINCT mission_type, reward_type, mission_description
                FROM mission_stack
                WHERE rules = 'wh40k'
                ORDER BY mission_type
            """)
            wh40k_missions = await cursor.fetchall()
            
            # Get map hex locations
            cursor = await db.execute("""
                SELECT DISTINCT hex_id FROM map
            """)
            map_locations = await cursor.fetchall()
            
            # Get territory adjacency (edges)
            cursor = await db.execute("""
                SELECT hex_a, hex_b FROM edges
            """)
            adjacency = await cursor.fetchall()
            
            return {
                'templates': {
                    'kill_team': [
                        {
                            'type': m[0],
                            'reward': m[1],
                            'description': m[2]
                        }
                        for m in kill_team_missions
                    ],
                    'wh40k': [
                        {
                            'type': m[0],
                            'reward': m[1],
                            'description': m[2]
                            # NOTE: winner_bonus templates NOT included - secret!
                        }
                        for m in wh40k_missions
                    ]
                },
                'map': {
                    'hex_locations': [hex_id[0] for hex_id in map_locations],
                    'adjacency': [
                        {'from': e[0], 'to': e[1]}
                        for e in adjacency
                    ]
                },
                'timestamp': datetime.utcnow().isoformat(),
                'version': '1.0'
            }
    except Exception as e:
        logger.error(f"Error exporting mission generation templates: {e}")
        return {'error': str(e), 'timestamp': datetime.utcnow().isoformat()}


async def export_active_missions(db_path: str) -> Dict[str, Any]:
    """
    Export currently active missions for display/history in offline app.
    
    This is separate from generation templates - these are missions that
    need results entered (status = pending/active).
    
    Returns list of missions available for result entry.
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            # Get missions that need results (not yet completed)
            cursor = await db.execute("""
                SELECT id, mission_type, reward_type, map_location, 
                       created_at, status, rules, mission_description
                FROM mission_stack
                WHERE status IN (0, 1)
                ORDER BY created_at DESC
            """)
            missions = await cursor.fetchall()
            
            return {
                'missions': [
                    {
                        'id': m[0],
                        'type': m[1],
                        'reward': m[2],
                        'location': m[3],
                        'created': m[4],
                        'status': m[5],  # 0=pending, 1=active
                        'rules': m[6],   # 'wh40k' or other
                        'description': m[7]
                    }
                    for m in missions
                ],
                'timestamp': datetime.utcnow().isoformat(),
                'version': '1.0'
            }
    except Exception as e:
        logger.error(f"Error exporting active missions: {e}")
        return {'missions': [], 'error': str(e), 'timestamp': datetime.utcnow().isoformat()}


async def export_missions_for_cache(db_path: str) -> Dict[str, Any]:
    """
    DEPRECATED: Use export_mission_generation_templates() and export_active_missions() instead.
    
    Kept for backward compatibility.
    """
    templates = await export_mission_generation_templates(db_path)
    active = await export_active_missions(db_path)
    
    return {
        'generation_templates': templates,
        'active_missions': active,
        'timestamp': datetime.utcnow().isoformat()
    }


async def export_map_data_for_cache(db_path: str) -> Dict[str, Any]:
    """
    Export map edges for territory calculation.
    Used for offline mission result processing.
    
    Returns:
        {
            'edges': [...],  # Territory adjacency list
            'timestamp': ISO datetime
        }
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute("""
                SELECT hex_a, hex_b
                FROM edges
            """)
            edges = await cursor.fetchall()
            
            return {
                'edges': [
                    {'from': e[0], 'to': e[1]}
                    for e in edges
                ],
                'timestamp': datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Error exporting map data: {e}")
        return {'edges': [], 'error': str(e), 'timestamp': datetime.utcnow().isoformat()}


async def process_synced_battle_results(
    db_path: str,
    warmaster_id: int,
    synced_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Process battle results synced from mobile app.
    Handles BOTH rule sets:
    - Kill Team: Territory capture/protection calculation
    - WH40K: Secret winner_bonus revelation (only to winner!)
    
    Args:
        db_path: Path to SQLite database
        warmaster_id: Warmaster who synced the results
        synced_results: List of battle results from mobile app
        
    Returns:
        {
            'processed': number of results,
            'territories_affected': [...],  # Kill Team only
            'winner_bonuses': {...},        # WH40K only
            'errors': [...]
        }
    """
    processed = 0
    affected_territories = set()
    winner_bonuses_revealed = {}  # WH40K: bonuses revealed to winners
    errors = []
    
    try:
        async with aiosqlite.connect(db_path) as db:
            for result in synced_results:
                try:
                    mission_id = result.get('mission_id')
                    winner_id = result.get('winner_id')
                    loser_id = result.get('loser_id')
                    mission_type = result.get('mission_type')
                    mission_location = result.get('location')
                    
                    # Get mission from database to check rules
                    cursor = await db.execute("""
                        SELECT rules, mission_type, mission_description, winner_bonus
                        FROM mission_stack
                        WHERE id = ?
                    """, (mission_id,))
                    mission_data = await cursor.fetchone()
                    
                    if not mission_data:
                        errors.append({
                            'mission_id': mission_id,
                            'error': 'Mission not found'
                        })
                        continue
                    
                    rules, db_mission_type, description, winner_bonus = mission_data
                    
                    # Record the battle result
                    await db.execute("""
                        UPDATE mission_stack
                        SET status = 3, winner_id = ?, updated_at = ?
                        WHERE id = ?
                    """, (winner_id, datetime.utcnow().isoformat(), mission_id))
                    
                    # Handle based on rule set
                    if rules == 'wh40k':
                        # WH40K: Reveal secret winner_bonus to winner
                        if winner_bonus:
                            winner_bonuses_revealed[mission_id] = {
                                'winner_id': winner_id,
                                'bonus': winner_bonus,
                                'description': description
                            }
                            logger.info(f"WH40K mission {mission_id}: bonus revealed to winner {winner_id}")
                    else:
                        # Kill Team: Apply territory effects
                        if mission_location:
                            affected_territories.add(mission_location)
                            
                            # Different mission types have different territory effects
                            if mission_type == 'Secure':
                                # Secure mission - winner claims territory
                                await _claim_territory(db, mission_location, winner_id, mission_type)
                            elif mission_type == 'Intel':
                                # Intel - creates supply depot
                                await _create_supply_depot(db, mission_location, winner_id)
                            elif mission_type == 'Coordinates':
                                # Coordinates - destroy enemy supply depot
                                if loser_id:
                                    await _destroy_enemy_depot(db, mission_location, loser_id)
                    
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing battle result {result.get('mission_id')}: {e}")
                    errors.append({
                        'mission_id': result.get('mission_id'),
                        'error': str(e)
                    })
            
            await db.commit()
            
    except Exception as e:
        logger.error(f"Error in process_synced_battle_results: {e}")
        errors.append({'error': str(e)})
    
    return {
        'processed': processed,
        'territories_affected': list(affected_territories),  # Kill Team
        'winner_bonuses': winner_bonuses_revealed,           # WH40K
        'errors': errors,
        'timestamp': datetime.utcnow().isoformat()
    }


async def _claim_territory(db: aiosqlite.Connection, hex_id: str, fm_id: int, mission_type: str) -> None:
    """Mark territory as claimed by faction master after Secure mission."""
    try:
        # Get faction from warmaster
        cursor = await db.execute("""
            SELECT faction FROM warmasters WHERE id = ?
        """, (fm_id,))
        result = await cursor.fetchone()
        
        if result:
            faction = result[0]
            # Update map to mark territory as controlled by faction
            await db.execute("""
                UPDATE map
                SET controlled_by = ?, last_updated = ?
                WHERE hex_id = ?
            """, (faction, datetime.utcnow().isoformat(), hex_id))
            
            logger.info(f"Territory {hex_id} claimed by faction {faction} after {mission_type}")
    except Exception as e:
        logger.error(f"Error claiming territory {hex_id}: {e}")


async def _create_supply_depot(db: aiosqlite.Connection, hex_id: str, fm_id: int) -> None:
    """Create supply depot in territory after Intel mission."""
    try:
        cursor = await db.execute("""
            SELECT faction FROM warmasters WHERE id = ?
        """, (fm_id,))
        result = await cursor.fetchone()
        
        if result:
            faction = result[0]
            # Mark territory as having supply depot
            await db.execute("""
                UPDATE map
                SET has_supply_depot = 1, supply_depot_faction = ?, last_updated = ?
                WHERE hex_id = ?
            """, (faction, datetime.utcnow().isoformat(), hex_id))
            
            logger.info(f"Supply depot created in {hex_id} for faction {faction}")
    except Exception as e:
        logger.error(f"Error creating supply depot in {hex_id}: {e}")


async def _destroy_enemy_depot(db: aiosqlite.Connection, hex_id: str, enemy_fm_id: int) -> None:
    """Destroy enemy supply depot after Coordinates mission."""
    try:
        # Check if enemy has depot there
        cursor = await db.execute("""
            SELECT faction FROM warmasters WHERE id = ?
        """, (enemy_fm_id,))
        result = await cursor.fetchone()
        
        if result:
            enemy_faction = result[0]
            # Remove supply depot if it belongs to enemy
            await db.execute("""
                UPDATE map
                SET has_supply_depot = 0, supply_depot_faction = NULL, last_updated = ?
                WHERE hex_id = ? AND supply_depot_faction = ?
            """, (datetime.utcnow().isoformat(), hex_id, enemy_faction))
            
            logger.info(f"Supply depot destroyed in {hex_id}")
    except Exception as e:
        logger.error(f"Error destroying depot in {hex_id}: {e}")


async def get_sync_status(db_path: str) -> Dict[str, Any]:
    """
    Get current sync status for mobile apps.
    Shows what data needs to be synced.
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            # Count pending missions
            cursor = await db.execute("""
                SELECT COUNT(*) FROM mission_stack WHERE status < 3
            """)
            pending_missions = (await cursor.fetchone())[0]
            
            # Count completed missions that haven't been synced yet
            cursor = await db.execute("""
                SELECT COUNT(*) FROM mission_stack WHERE status = 3 AND updated_at > datetime('now', '-1 hour')
            """)
            recent_completions = (await cursor.fetchone())[0]
            
            return {
                'pending_missions': pending_missions,
                'recent_completions': recent_completions,
                'last_sync': datetime.utcnow().isoformat(),
                'sync_ready': pending_missions > 0 or recent_completions > 0
            }
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        return {'error': str(e)}

async def get_wh40k_winner_bonus(db_path: str, mission_id: int, requesting_warmaster_id: int) -> Dict[str, Any]:
    """
    Get WH40K mission winner bonus - ONLY for the actual winner!
    
    This is a SECRET bonus that should ONLY be revealed to the player who won.
    SECURITY: Verify that requesting_warmaster_id is the actual winner.
    
    Args:
        db_path: Path to SQLite database
        mission_id: Mission ID
        requesting_warmaster_id: Warmaster requesting the bonus
        
    Returns:
        {
            'bonus': <bonus text>,
            'mission_id': <id>,
            'authorized': True/False
        }
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute("""
                SELECT winner_id, winner_bonus, rules, mission_type
                FROM mission_stack
                WHERE id = ?
            """, (mission_id,))
            mission = await cursor.fetchone()
            
            if not mission:
                logger.warning(f"WH40K bonus request: Mission {mission_id} not found")
                return {
                    'error': 'Mission not found',
                    'authorized': False
                }
            
            winner_id, bonus, rules, mission_type = mission
            
            # Verify it's a WH40K mission
            if rules != 'wh40k':
                logger.warning(f"WH40K bonus request: Mission {mission_id} is not WH40K")
                return {
                    'error': 'Not a WH40K mission',
                    'authorized': False
                }
            
            # SECURITY: Only reveal bonus to the actual winner!
            if winner_id != requesting_warmaster_id:
                logger.warning(
                    f"SECURITY: Unauthorized WH40K bonus access - "
                    f"Mission {mission_id}, "
                    f"Requester {requesting_warmaster_id}, "
                    f"Winner {winner_id}"
                )
                return {
                    'error': 'Not authorized - only winner can view bonus',
                    'authorized': False,
                    'mission_id': mission_id
                }
            
            # Winner is authorized - reveal the secret bonus
            logger.info(f"WH40K bonus revealed to winner {winner_id} for mission {mission_id}")
            return {
                'bonus': bonus,
                'mission_id': mission_id,
                'mission_type': mission_type,
                'authorized': True,
                'revealed_at': datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error getting WH40K winner bonus: {e}")
        return {'error': str(e), 'authorized': False}


async def get_mission_rules(db_path: str, mission_id: int) -> Optional[str]:
    """Get the rule set for a mission (e.g., 'wh40k' or None for Kill Team)"""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute("""
                SELECT rules FROM mission_stack WHERE id = ?
            """, (mission_id,))
            result = await cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting mission rules: {e}")
        return None