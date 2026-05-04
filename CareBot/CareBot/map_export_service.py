"""Shared service for generating planet map export PNG bytes."""

import asyncio
import functools
import hashlib
import logging
from typing import Optional

if __package__:
    from . import config
    from . import map_exporter

    # Automatically switch to mock DB helper in test mode.
    if config.TEST_MODE:
        from . import mock_sqlite_helper as sqllite_helper
    else:
        from . import sqllite_helper
else:
    import config
    import map_exporter

    if config.TEST_MODE:
        import mock_sqlite_helper as sqllite_helper
    else:
        import sqllite_helper

logger = logging.getLogger(__name__)

# In-memory cache: avoids re-rendering when map state hasn't changed.
_cache_hash: Optional[str] = None
_cache_png: Optional[bytes] = None


class EmptyMapExportError(Exception):
    """Raised when map export is requested but map has no cells."""


def _compute_map_hash(map_cells: list, alliances: list) -> str:
    """Return a quick MD5 fingerprint of the parts that affect map visuals."""
    # Include id, patron, has_warehouse for each cell; alliance ids only.
    state = str([(r[0], r[2], r[3]) for r in map_cells])
    state += str([r[0] for r in alliances])
    return hashlib.md5(state.encode()).hexdigest()


async def generate_realistic_map_png() -> bytes:
    """Build realistic map PNG bytes using shared DB + renderer flow.

    The CPU-heavy matplotlib render runs in a thread-pool executor so it
    never blocks the async event loop.  Identical map state is served from
    an in-memory cache without re-rendering.
    """
    global _cache_hash, _cache_png

    map_cells_raw = await sqllite_helper.get_map_cells_for_export()
    map_cells = [
        (int(row[0]), row[1], row[2], int(row[3]))
        for row in map_cells_raw
    ]

    if not map_cells:
        raise EmptyMapExportError("Map is empty")

    alliances_raw = await sqllite_helper.get_alliances_for_map_export()
    alliances = [
        (int(row[0]), row[1], row[2])
        for row in alliances_raw
    ]

    terrain_colors_raw = await sqllite_helper.get_terrain_colors()

    current_hash = _compute_map_hash(map_cells, alliances)
    if current_hash == _cache_hash and _cache_png is not None:
        logger.info("Map export: returning cached PNG (hash=%s)", current_hash[:8])
        return _cache_png

    logger.info("Map export: rendering new PNG (hash=%s)", current_hash[:8])
    loop = asyncio.get_event_loop()
    render_func = functools.partial(
        map_exporter.render_realistic_map_png,
        map_cells,
        alliances,
        terrain_colors_raw,
    )
    png_bytes = await loop.run_in_executor(None, render_func)

    _cache_hash = current_hash
    _cache_png = png_bytes
    return png_bytes
