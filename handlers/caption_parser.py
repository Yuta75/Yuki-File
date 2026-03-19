# handlers/caption_parser.py
# Auto-detects metadata from file caption / filename
# Used by start.py → build_caption() to fill template variables
#
# To add new variables in future:
#   1. Add regex detection in parse_metadata()
#   2. Add replacement line in apply_template()
#   3. Document the new variable in SUPPORTED_VARS

import re

# ─────────────────────────────────────────────
# SUPPORTED VARIABLES  (for reference / settings display)
# ─────────────────────────────────────────────
SUPPORTED_VARS = {
    "{caption}"  : "Original file caption",
    "{title}"    : "Show / file title",
    "{episode}"  : "Episode number",
    "{season}"   : "Season number",
    "{quality}"  : "Quality (480p/720p/1080p/4K)",
    "{language}" : "Language",
    "{audio}"    : "Audio type (alias for language)",
    "{size}"     : "File size (MB/GB)",
}


def parse_metadata(text: str) -> dict:
    """
    Parses a file caption or filename and returns a dict of all detected values.
    Empty string for anything not found — never raises.
    """
    if not text:
        return _empty()

    data = {}

    # ── EPISODE & SEASON ─────────────────────────────────────────
    # S01E02 / S1E2 / s01e02
    ep_season = re.search(r'[Ss](\d{1,2})[Ee](\d{1,3})', text)
    if ep_season:
        data['season']  = ep_season.group(1).zfill(2)
        data['episode'] = ep_season.group(2).zfill(2)
    else:
        # Standalone: EP01 / E01 / Episode 1
        ep_only = re.search(r'(?:EP?|Episode)\s*(\d{1,3})', text, re.IGNORECASE)
        data['episode'] = ep_only.group(1).zfill(2) if ep_only else ''
        data['season']  = ''

    # ── QUALITY ──────────────────────────────────────────────────
    quality = re.search(
        r'(4K|2160p|1080p|720p|480p|360p|FHD|UHD|HD)',
        text, re.IGNORECASE
    )
    data['quality'] = quality.group(1).upper() if quality else ''

    # ── LANGUAGE / AUDIO ─────────────────────────────────────────
    # Ordered by specificity — first match wins
    lang_patterns = [
        r'(Multi[\s\-]?Audio)',
        r'(Dual[\s\-]?Audio)',
        r'(Hindi[\s\-]?Dubbed)',
        r'(Hindi[\s\-]?Dub)',
        r'(English[\s\-]?Sub(?:bed)?)',
        r'(English)',
        r'(Hindi)',
        r'(Japanese)',
        r'(Tamil)',
        r'(Telugu)',
        r'(Korean)',
        r'(Spanish)',
        r'(French)',
        r'(German)',
    ]
    lang_found = ''
    for pat in lang_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            lang_found = m.group(1).strip()
            break
    data['language'] = lang_found
    data['audio']    = lang_found   # {audio} is an alias

    # ── TITLE ────────────────────────────────────────────────────
    # Everything before the first recognisable metadata marker
    clean = re.sub(r'[@\[\](){}]', ' ', text)
    title_match = re.match(
        r'^(.+?)(?:\s*[-_]?\s*(?:[Ss]\d{1,2}[Ee]\d{1,3}|\d{3,4}p|4K|HD|FHD|UHD|Hindi|English|Dual|Multi))',
        clean
    )
    title = title_match.group(1).strip().strip('-_. ') if title_match else ''
    data['title'] = title

    # ── FILE SIZE ────────────────────────────────────────────────
    size = re.search(r'(\d+(?:\.\d+)?\s*(?:MB|GB|KB))', text, re.IGNORECASE)
    data['size'] = size.group(1).upper() if size else ''

    return data


def apply_template(template: str, original_caption: str, file_name: str = '') -> str:
    """
    Fills all {variables} in template using auto-detected metadata.
    Falls back to filename if caption is empty.
    Unrecognised variables are left as-is so future additions don't break old templates.
    """
    source = original_caption or file_name or ''
    meta   = parse_metadata(source)

    result = template
    result = result.replace('{caption}',  original_caption or '')
    result = result.replace('{title}',    meta.get('title',    ''))
    result = result.replace('{episode}',  meta.get('episode',  ''))
    result = result.replace('{season}',   meta.get('season',   ''))
    result = result.replace('{quality}',  meta.get('quality',  ''))
    result = result.replace('{language}', meta.get('language', ''))
    result = result.replace('{audio}',    meta.get('audio',    ''))
    result = result.replace('{size}',     meta.get('size',     ''))

    return result.strip()


def _empty() -> dict:
    return {k: '' for k in ('episode', 'season', 'quality', 'language', 'audio', 'title', 'size')}
