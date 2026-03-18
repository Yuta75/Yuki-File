import asyncio
import os
import random
import sys
import time
from datetime import datetime, timedelta
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, ChatInviteLink, ChatPrivileges
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant
from bot import Bot
from config import *
from helper_func import *
from database.database import *
from plugins.VoidXTora import check_owner_only, check_admin_or_owner

#=====================================================================================##

@Bot.on_message(filters.command('stats'))
async def stats(bot: Bot, message: Message):
    if not await check_admin_or_owner(message):
        return

    pro = await message.reply("<b><i>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ..</i></b>", quote=True)

    now = datetime.now()
    delta = now - bot.uptime
    uptime_str = get_readable_time(delta.seconds)

    total_users = await db.full_userbase()
    total_count = len(total_users)

    # Users joined today (added_on field — fallback to N/A if not tracked)
    try:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_users = await db.user_data.count_documents(
            {"added_on": {"$gte": today_start}}
        )
    except Exception:
        today_users = "N/A"

    # Bot started date
    started_on = bot.uptime.strftime("%d %b %Y, %I:%M %p")

    text = (
        "<b><blockquote>📊 Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs</blockquote></b>\n\n"
        f"<b>⏱ Uᴘᴛɪᴍᴇ:</b> <code>{uptime_str}</code>\n"
        f"<b>🕐 Sᴛᴀʀᴛᴇᴅ:</b> <code>{started_on}</code>\n\n"
        f"<b>👥 Tᴏᴛᴀʟ Usᴇʀs:</b> <code>{total_count}</code>\n"
        f"<b>📅 Jᴏɪɴᴇᴅ Tᴏᴅᴀʏ:</b> <code>{today_users}</code>"
    )

    await pro.edit(
        text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ ✖", callback_data="close")]])
    )

#=====================================================================================##

@Bot.on_message(filters.command('ping') & filters.private)
async def ping(bot: Bot, message: Message):
    start = time.time()
    pro = await message.reply("<b>🏓 Pɪɴɢɪɴɢ...</b>", quote=True)
    end = time.time()
    ms = round((end - start) * 1000, 3)

    await pro.edit(
        f"<b>🏓 Pᴏɴɢ!</b>\n\n"
        f"<blockquote><b>⚡ Sᴘᴇᴇᴅ:</b> <code>{ms} ms</code></blockquote>"
    )

#=====================================================================================##

WAIT_MSG = "<b>Working....</b>"

@Bot.on_message(filters.command('users') & filters.private)
async def get_users(client: Bot, message: Message):
    if not await check_admin_or_owner(message):
        return
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await db.full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")

#=====================================================================================##

@Bot.on_message(filters.private & filters.command('dlt_time'))
async def set_delete_time(client: Bot, message: Message):
    if not await check_admin_or_owner(message):
        return
    try:
        duration = int(message.command[1])
        await db.set_del_timer(duration)
        await message.reply(f"<b>Dᴇʟᴇᴛᴇ Tɪᴍᴇʀ ʜᴀs ʙᴇᴇɴ sᴇᴛ ᴛᴏ <blockquote>{duration} sᴇᴄᴏɴᴅs.</blockquote></b>")
    except (IndexError, ValueError):
        await message.reply("<b>Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ sᴇᴄᴏɴᴅs.</b> Usage: /dlt_time {duration}")

@Bot.on_message(filters.private & filters.command('check_dlt_time'))
async def check_delete_time(client: Bot, message: Message):
    if not await check_admin_or_owner(message):
        return
    duration = await db.get_del_timer()
    await message.reply(f"<b><blockquote>Cᴜʀʀᴇɴᴛ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ ɪs sᴇᴛ ᴛᴏ {duration} sᴇᴄᴏɴᴅs.</blockquote></b>")

#=====================================================================================##
"""
#=====================================================================================##
# Credits:- @VoidXTora
# Maintained by: Mythic_Bots
# Support: @MythicBot_Support
#=====================================================================================##
This file is part of MythicBots Project.
Base Repo Codeflixbot.
"""
