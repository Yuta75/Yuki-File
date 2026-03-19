# handlers/chat_action.py
# Sends a ChatAction for a set duration so it's visible even on fast servers.
# Used by start.py for both normal /start and file delivery flows.
#
# Future-proof design:
#   - NORMAL_ACTION and FILE_ACTIONS can be swapped without touching start.py
#   - duration is configurable per call
#   - show_action() can be called in a fire-and-forget task for long operations

import asyncio
import random
from pyrogram import Client
from pyrogram.enums import ChatAction

# ─────────────────────────────────────────────
# ACTION POOLS
# ─────────────────────────────────────────────

# Shown on plain /start
NORMAL_ACTION = ChatAction.TYPING

# Randomly picked while fetching/sending files
FILE_ACTIONS = [
    ChatAction.UPLOAD_VIDEO,
    ChatAction.UPLOAD_DOCUMENT,
    ChatAction.PLAYING,
    ChatAction.UPLOAD_VIDEO_NOTE,
]

# How long (seconds) to hold the action so it's visible on fast servers
# Telegram auto-cancels after 5s if no follow-up, so 2–3s is sweet spot
ACTION_DURATION: float = 2.5


async def show_action(
    client: Client,
    chat_id: int,
    action: ChatAction = ChatAction.TYPING,
    duration: float = ACTION_DURATION
) -> None:
    """
    Sends a chat action and holds it for `duration` seconds.
    Safe to call — silently ignores any errors.
    """
    try:
        await client.send_chat_action(chat_id, action)
        await asyncio.sleep(duration)
    except Exception:
        pass


async def show_file_action(
    client: Client,
    chat_id: int,
    duration: float = ACTION_DURATION
) -> ChatAction:
    """
    Picks a random file-related action, shows it, and returns
    the chosen action so the caller can re-use it mid-loop.
    """
    action = random.choice(FILE_ACTIONS)
    await show_action(client, chat_id, action, duration)
    return action


async def refresh_action(
    client: Client,
    chat_id: int,
    action: ChatAction
) -> None:
    """
    Re-sends an already-chosen action (e.g. inside a multi-file loop)
    without sleeping, so Telegram keeps showing it.
    """
    try:
        await client.send_chat_action(chat_id, action)
    except Exception:
        pass
