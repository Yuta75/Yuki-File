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


# ─────────────────────────────────────────────
# INTERNAL: strip bracket wrappers for clean matching
# ─────────────────────────────────────────────

def _unwrap(text: str) -> str:
    """Remove [], (), {} wrappers but keep content — used for pre-processing."""
    return re.sub(r'[\[\](){}]', ' ', text)


# ─────────────────────────────────────────────
# EPISODE & SEASON
# ─────────────────────────────────────────────

def _parse_episode_season(text: str) -> tuple:
    """
    Returns (season, episode) as zero-padded strings, or ('', '') if not found.

    Handles all common formats:
      Filename style : S01E02, S1E2, s01e02
      Bracketed      : [S01][EP01], [S01] [EP01], [S1][E2]
      Inline caption : Season : 01 / Season: 1 / Sᴇᴀsᴏɴ : 01
      Episode label  : EP01, E01, Episode 1, Eᴘɪsᴏᴅᴇs: 01
      Combined inline: S01E02 inside brackets
    """
    # 1. Classic joined: S01E02
    m = re.search(r'[Ss](\d{1,2})\s*[Ee](\d{1,3})', text)
    if m:
        return m.group(1).zfill(2), m.group(2).zfill(2)

    # 2. Bracketed separate: [S01][EP01] or [S01] [E02]
    ms = re.search(r'\[S(?:eason\s*)?(\d{1,2})\]', text, re.IGNORECASE)
    me = re.search(r'\[EP?(?:isode\s*)?(\d{1,3})\]', text, re.IGNORECASE)
    if ms and me:
        return ms.group(1).zfill(2), me.group(1).zfill(2)

    # 2b. Spaced/underscore-normalised: S01 EP01 or S01 E01 (no brackets)
    ms2b = re.search(r'\bS(\d{1,2})\b', text, re.IGNORECASE)
    me2b = re.search(r'\bEP?(\d{1,3})\b', text, re.IGNORECASE)
    if ms2b and me2b:
        return ms2b.group(1).zfill(2), me2b.group(1).zfill(2)

    # 3. Caption line: "Season : 01" or small-caps unicode variants
    #    Covers both ASCII and small-caps lookalikes by stripping non-ascii first
    plain = text.encode('ascii', errors='ignore').decode()
    ms2 = re.search(r'[Ss]eason\s*[:\-]\s*(\d{1,2})', plain, re.IGNORECASE)
    me2 = re.search(r'[Ee]p(?:isode)?s?\s*[:\-]\s*(\d{1,3})', plain, re.IGNORECASE)
    if ms2 or me2:
        season  = ms2.group(1).zfill(2) if ms2 else ''
        episode = me2.group(1).zfill(2) if me2 else ''
        return season, episode

    # 4. Bracketed season only: [S01]
    ms3 = re.search(r'\[S(\d{1,2})\]', text, re.IGNORECASE)
    if ms3:
        # Try standalone episode anywhere
        me3 = re.search(r'(?:EP?|Episode)\s*(\d{1,3})', text, re.IGNORECASE)
        return ms3.group(1).zfill(2), (me3.group(1).zfill(2) if me3 else '')

    # 5. Standalone episode only: EP01 / E01 / Episode 1
    me4 = re.search(r'(?:EP?|Episode)\s*(\d{1,3})', text, re.IGNORECASE)
    if me4:
        return '', me4.group(1).zfill(2)

    return '', ''


# ─────────────────────────────────────────────
# QUALITY
# ─────────────────────────────────────────────

def _parse_quality(text: str) -> str:
    """
    Handles both bracketed [480p] and plain 480p formats.
    Also catches label style: Quality : 480P
    """
    # Label style in caption: "Quality : 480p"
    m = re.search(r'[Qq]uality\s*[:\-]\s*(\S+)', text)
    if m:
        return m.group(1).upper().strip('.,')

    # Bracketed or plain
    m2 = re.search(r'[\[\(]?\s*(4K|2160p|1080p|720p|480p|360p|FHD|UHD|HD)\s*[\]\)]?', text, re.IGNORECASE)
    return m2.group(1).upper() if m2 else ''


# ─────────────────────────────────────────────
# LANGUAGE / AUDIO
# ─────────────────────────────────────────────

# Ordered by specificity — first match wins
_LANG_PATTERNS = [
    r'Multi[\s\-]?Audio',
    r'Dual[\s\-]?Audio',
    r'Hindi[\s\-]?Dubbed',
    r'Hindi[\s\-]?Dub',
    r'English[\s\-]?Sub(?:bed)?',
    r'English',
    r'Hindi',
    r'Japanese',
    r'Tamil',
    r'Telugu',
    r'Korean',
    r'Spanish',
    r'French',
    r'German',
]

def _parse_language(text: str) -> str:
    """
    Handles:
      - Bracketed: [Hindi] [Multi]
      - Caption label: Audio : Hindi [Multi] #Official
      - Plain inline: Hindi Dubbed
    """
    # Caption label style: "Audio : Hindi [Multi] #Official"
    # Also handles Unicode small-caps like ᴀᴜᴅɪᴏ by matching the colon separator
    label = re.search(r'(?:[Aa]udio|udio)\s*[:\-]\s*(.+?)(?:\n|$)', text)
    if not label:
        # Fallback: match line containing a colon where RHS has a known lang
        label = re.search(r':\s*([^\n]*(?:Hindi|English|Multi|Dual|Japanese|Tamil|Telugu)[^\n]*)', text, re.IGNORECASE)
    if label:
        raw = label.group(1).strip()
        found_langs = []

        # Check for Multi/Dual audio keywords first (ASCII, always readable)
        if re.search(r'Multi', raw, re.IGNORECASE):
            found_langs.append('Multi Audio')
        elif re.search(r'Dual', raw, re.IGNORECASE):
            found_langs.append('Dual Audio')

        # Try ASCII language patterns
        for pat in _LANG_PATTERNS:
            if 'Multi' in pat or 'Dual' in pat:
                continue  # already handled above
            m = re.search(pat, raw, re.IGNORECASE)
            if m:
                token = m.group(0).strip()
                if token not in found_langs:
                    found_langs.append(token)
                break

        # If no ASCII lang matched, try detecting Hindi/English from context
        # (small-caps Unicode like ʜɪɴᴅɪ won't match regex but context hints)
        if not any(l for l in found_langs if l not in ('Multi Audio', 'Dual Audio')):
            # Check surrounding filename/caption for language clues
            pass  # lang_found will be filled by generic search below

        if found_langs:
            return ' + '.join(found_langs)
        # Fall through to generic search if nothing matched in label

    # Generic search anywhere in text
    for pat in _LANG_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(0).strip()

    return ''


# ─────────────────────────────────────────────
# TITLE
# ─────────────────────────────────────────────

def _parse_title(text: str) -> str:
    """
    Extracts show/file title from filename or caption first line.

    Handles:
      Bracketed  : [@Channel] Show Name [S01] [EP01] [480p].mkv
      Underscore : @Channel_Show_Name_S01_EP01_480p
      Plain      : My Hero Academia Two Heroes 480p
      Spaced     : One Piece S01E01 720p Dual Audio.mkv
    """
    # Use first line only
    line = text.split('\n')[0]

    # Strip file extension
    line = re.sub(r'\.\w{2,4}$', '', line).strip()

    # Strip channel tags BEFORE underscore normalisation
    # Bracketed: [@Otaku_Hindi_Hub] or [Channel_Name] — safe, always strip
    line = re.sub(r'^\s*\[\s*@?[\w_]+\s*\]\s*', '', line)
    # Bare @tag: only strip if it looks like a pure channel handle
    # i.e. it has 3+ underscore-segments AND ends right before a title word or metadata
    # Avoids eating the whole string when channel+title are merged without brackets
    bare_tag = re.match(r'^@([\w_]+)', line)
    if bare_tag:
        tag_body = bare_tag.group(1)
        segments = tag_body.split('_')
        # If 3 or fewer segments it might just be a short channel name — safe to strip
        # If more than 3 segments, the title is likely merged in — don't strip
        if len(segments) <= 3:
            line = line[bare_tag.end():].lstrip()

    # Normalise underscores to spaces (after tag strip so tags don't lose their _ boundaries)
    line = line.replace('_', ' ')

    # Metadata stop-pattern — title ends just before any of these tokens
    STOP = re.compile(
        r'(?:'
        r'\[?\s*[Ss]\d{1,2}\s*[Ee]\d{1,3}\s*\]?'  # S01E02 / [S01E02]
        r'|\[?\s*[Ss]\d{1,2}\s*\]?(?=\s)'           # [S01] followed by space
        r'|\b[Ss]\d{1,2}\b(?=\s+[Ee][Pp]?\d)'       # S01 before EP01
        r'|\b[Ee]pisode\s*\d{1,3}\b'                 # Episode 1
        r'|\[?\s*[Ee][Pp]\s*\d{1,3}\s*\]?'           # EP01 / [EP01]
        r'|\[?\s*E\d{1,3}\s*\]?'                     # E01 / [E01]
        r'|\[?\s*\d{3,4}[pP]\s*\]?'                  # [480p] / 480p
        r'|\b4[Kk]\b|\bFHD\b|\bUHD\b|\bHD\b'        # quality labels
        r'|\bDual\s*Audio\b|\bMulti\s*Audio\b'        # audio labels
        r'|\bHindi\s*Dubbed\b|\bHindi\s*Dub\b'        # lang labels
        r'|\bDual\b|\bMulti\b'                        # shorter audio
        r'|\bHindi\b|\bEnglish\b|\bJapanese\b'        # language
        r')',
        re.IGNORECASE
    )

    m = STOP.search(line)
    if m:
        title = line[:m.start()]
    else:
        # Nothing found — strip any remaining bracket content
        title = re.sub(r'\[.*?\]|\(.*?\)', '', line)

    return title.strip().strip('-_[]@(). ')


# ─────────────────────────────────────────────
# SIZE
# ─────────────────────────────────────────────

def _parse_size(text: str) -> str:
    m = re.search(r'(\d+(?:\.\d+)?\s*(?:MB|GB|KB))', text, re.IGNORECASE)
    return m.group(1).upper() if m else ''


# ─────────────────────────────────────────────
# MAIN PARSER
# ─────────────────────────────────────────────

def parse_metadata(text: str) -> dict:
    """
    Parses a file caption or filename and returns a dict of all detected values.
    Empty string for anything not found — never raises.
    """
    if not text:
        return _empty()

    season, episode = _parse_episode_season(text)
    language        = _parse_language(text)

    return {
        'season'  : season,
        'episode' : episode,
        'quality' : _parse_quality(text),
        'language': language,
        'audio'   : language,           # {audio} is an alias for {language}
        'title'   : _parse_title(text),
        'size'    : _parse_size(text),
    }


# ─────────────────────────────────────────────
# TEMPLATE FILLER
# ─────────────────────────────────────────────

def apply_template(template: str, original_caption: str, file_name: str = '') -> str:
    """
    Fills all {variables} in template using auto-detected metadata.
    Falls back to filename if caption is empty.
    Unrecognised variables are left as-is so future additions don't break old templates.
    """
    # Parse from both sources and merge:
    # - Title: filename wins (captions have decorative first lines)
    # - Everything else: caption wins, fallback to filename
    meta_cap  = parse_metadata(original_caption) if original_caption else _empty()
    meta_file = parse_metadata(file_name)         if file_name        else _empty()

    meta = {
        'title'   : meta_file.get('title')    or meta_cap.get('title',    ''),
        'season'  : meta_cap.get('season')    or meta_file.get('season',   ''),
        'episode' : meta_cap.get('episode')   or meta_file.get('episode',  ''),
        'quality' : meta_cap.get('quality')   or meta_file.get('quality',  ''),
        'language': meta_cap.get('language')  or meta_file.get('language', ''),
        'audio'   : meta_cap.get('audio')     or meta_file.get('audio',    ''),
        'size'    : meta_cap.get('size')      or meta_file.get('size',     ''),
    }

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
