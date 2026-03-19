#(©)Codexbotz

import asyncio
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

from bot import Bot
from config import *
from helper_func import encode, admin
from database.database import db


# Commands that should NOT trigger channel_post (admin inputs go here)
EXCLUDED_COMMANDS = [
    'start', 'commands', 'users', 'broadcast', 'batch', 'custom_batch',
    'genlink', 'stats', 'dlt_time', 'check_dlt_time', 'dbroadcast',
    'ban', 'unban', 'banlist', 'addchnl', 'delchnl', 'listchnl',
    'fsub_mode', 'pbroadcast', 'add_admin', 'deladmin', 'admins',
    'help', 'about', 'settings', 'setcaption', 'cancel', 'ping',
]


# Global awaiting-input registry — settings.py writes to this,
# channel_post.py reads from it. Avoids circular imports.
_AWAITING_INPUT: set = set()

def mark_awaiting(user_id: int):
    _AWAITING_INPUT.add(user_id)

def clear_awaiting(user_id: int):
    _AWAITING_INPUT.discard(user_id)

async def is_awaiting_input(user_id: int) -> bool:
    """
    Returns True if this user is currently waiting to send an admin input
    (caption template, channel link, channel title).
    settings.py calls mark_awaiting/clear_awaiting to keep this in sync.
    """
    if user_id in _AWAITING_INPUT:
        return True
    # Fallback: import directly from settings module
    # Try both absolute (plugins.settings) and relative (settings) paths
    for mod_path in ('plugins.settings', 'settings'):
        try:
            import importlib
            mod = importlib.import_module(mod_path)
            return (
                user_id in getattr(mod, '_awaiting_template', set())
                or user_id in getattr(mod, '_awaiting_chnl_link', set())
                or user_id in getattr(mod, '_awaiting_chnl_title', set())
            )
        except Exception:
            continue
    return False


@Bot.on_message(filters.private & admin & ~filters.command(EXCLUDED_COMMANDS))
async def channel_post(client: Client, message: Message):

    # Skip if admin is currently in an input-awaiting state
    if await is_awaiting_input(message.from_user.id):
        return

    reply_text = await message.reply_text("Please Wait...!", quote=True)
    try:
        post_message = await message.copy(chat_id=client.db_channel.id, disable_notification=True)
    except FloodWait as e:
        await asyncio.sleep(e.x)
        post_message = await message.copy(chat_id=client.db_channel.id, disable_notification=True)
    except Exception as e:
        print(e)
        await reply_text.edit_text("Something went Wrong..!")
        return

    converted_id = post_message.id * abs(client.db_channel.id)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')
    ]])

    await reply_text.edit(
        f"<b>Here is your link</b>\n\n{link}",
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

    if not DISABLE_CHANNEL_BUTTON:
        await post_message.edit_reply_markup(reply_markup)
