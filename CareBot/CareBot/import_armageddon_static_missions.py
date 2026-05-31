"""Import static Armageddon missions from Wahapedia into local database.

Usage:
    python CareBot/CareBot/import_armageddon_static_missions.py
"""

import asyncio
import html
import os
import re
from pathlib import Path
from typing import Dict, List
from urllib.parse import urljoin
from urllib.request import urlopen, urlretrieve

# Ensure a portable default DB path for local runs (can be overridden via DATABASE_PATH).
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "db" / "database.db"
os.environ.setdefault("DATABASE_PATH", str(DEFAULT_DB_PATH))

import sqllite_helper
WAHAPEDIA_URL = "https://wahapedia.ru/wh40k10ed/the-rules/armageddon/#Mission-Map-Key"
WAHAPEDIA_BASE_URL = "https://wahapedia.ru"
SOURCE = "wahapedia_armageddon"
RULES = "wh40k"

ASSETS_DIR = Path(__file__).resolve().parent / "assets" / "deploys" / "armageddon"


MISSION_BLOCK_RE = re.compile(
    r'<a name="(?P<anchor>[^"]+)"></a>'
    r'<div class="mission_header2">Armageddon Crusade Mission</div>'
    r'<h3 class="outline_header_dice mission_header">(?P<header>.*?)</h3>'
    r'<div class="cruMissionLegend">(?P<legend>.*?)</div><br>'
    r'<div class="Columns2">(?P<body>.*?)</div>'
    r'<div style="clear:both"></div>'
    r'<div class=" img-opa"[^>]*><img border="0" src="(?P<map_src>[^"]+)"',
    re.IGNORECASE | re.DOTALL,
)


def _strip_tags(raw_html: str) -> str:
    """Convert HTML fragment to plain text with simple line formatting."""
    text = raw_html
    replacements = {
        "<br>": "\n",
        "<br/>": "\n",
        "<br />": "\n",
        "</div>": "\n",
        "</p>": "\n",
        "</li>": "\n",
        "<li>": "- ",
        "</ul>": "\n",
        "</h4>": "\n",
        "</h5>": "\n",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = text.replace("\xa0", " ")

    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines).strip()


def _extract_name_and_code(header_html: str) -> Dict[str, str]:
    """Extract mission name and D33 code from mission header block."""
    name_match = re.search(r"</div>\s*(.*?)\s*<div style=\"float:right\">", header_html, re.DOTALL)
    code_match = re.search(r"&nbsp;(\d+)", header_html)

    mission_name = _strip_tags(name_match.group(1)) if name_match else "Unknown Mission"
    mission_code = code_match.group(1) if code_match else "00"
    return {"mission_name": mission_name, "mission_code": mission_code}


def _fetch_page(url: str) -> str:
    with urlopen(url, timeout=60) as response:
        return response.read().decode("utf-8", errors="ignore")


def _parse_missions(page_html: str) -> List[Dict[str, str]]:
    records: List[Dict[str, str]] = []

    for match in MISSION_BLOCK_RE.finditer(page_html):
        header_html = match.group("header")
        legend_html = match.group("legend")
        body_html = match.group("body")
        map_src = match.group("map_src")

        parsed_header = _extract_name_and_code(header_html)
        legend_text = _strip_tags(legend_html)
        body_text = _strip_tags(body_html)

        mission_text_parts = [part for part in [legend_text, body_text] if part]
        mission_text_full = "\n\n".join(mission_text_parts).strip()

        records.append(
            {
                "mission_name": parsed_header["mission_name"],
                "mission_code": parsed_header["mission_code"],
                "mission_text_full": mission_text_full,
                "map_src": map_src,
            }
        )

    if len(records) != 16:
        raise RuntimeError(
            f"Expected 16 Armageddon missions in Mission Map Key, parsed {len(records)}"
        )

    return records


def _download_asset(map_src: str) -> str:
    """Download map image into assets/deploys/armageddon and return relative path."""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    filename = Path(map_src).name
    target = ASSETS_DIR / filename
    source_url = urljoin(WAHAPEDIA_BASE_URL, map_src)

    if not target.exists():
        urlretrieve(source_url, target)

    return f"armageddon/{filename}"


async def run_import() -> None:
    page_html = _fetch_page(WAHAPEDIA_URL)
    missions = _parse_missions(page_html)

    saved = 0
    for index, mission in enumerate(missions):
        table_prefix = "A" if index < 8 else "B"
        mission_code = f"{table_prefix}{mission['mission_code']}"
        asset_rel_path = _download_asset(mission["map_src"])

        await sqllite_helper.upsert_static_armageddon_mission(
            rules=RULES,
            source=SOURCE,
            source_url=WAHAPEDIA_URL,
            mission_code=mission_code,
            mission_name=mission["mission_name"],
            mission_text_full=mission["mission_text_full"],
            deploy_asset_path=asset_rel_path,
            map_asset_path=asset_rel_path,
            is_active=1,
        )
        saved += 1

    count = await sqllite_helper.get_static_armageddon_mission_count(RULES)
    print(f"✅ Imported/updated {saved} missions. Active static missions for {RULES}: {count}")


if __name__ == "__main__":
    asyncio.run(run_import())
