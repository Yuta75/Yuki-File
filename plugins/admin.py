# admin.py
# Credits:- @VoidXTora | Maintained by: Mythic_Bots | Support: @MythicBot_Support
# This file is part of MythicBots Project. Base Repo: Codeflixbot.

import asyncio
import os
import random
import sys
import time

from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction, ChatMemberStatus, ChatType
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ReplyKeyboardMarkup,
    ChatMemberUpdated,
    ChatPermissions,
)
from pyrogram.errors.exceptions.bad_request_400 import (
    UserNotParticipant,
    InviteHashEmpty,
    ChatAdminRequired,
    PeerIdInvalid,
    UserIsBlocked,
    InputUserDeactivated,
)

from config import *
from bot import Bot
from helper_func import *
from database.database import *
from plugins.VoidXTora import check_owner_only, check_admin_or_owner


CLOSE_BTN = InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ ✖", callback_data="close")]])


# ─────────────────────────────────────────────
# ADD ADMINS  (Owner only)
# ─────────────────────────────────────────────

@Bot.on_message(filters.command('add_admin') & filters.private)
async def add_admins(client: Client, message: Message):
    if not await check_owner_only(message):
        return

    pro = await message.reply("<b><i>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ..</i></b>", quote=True)
    check = 0
    admin_ids = await db.get_all_admins()
    admins = message.text.split()[1:]

    if not admins:
        return await pro.edit(
            "<b>You need to provide user ID(s) to add as admin.</b>\n\n"
            "<b>Usage:</b>\n"
            "<code>/add_admin [user_id]</code> — Add one or more user IDs\n\n"
            "<b>Example:</b>\n"
            "<code>/add_admin 1234567890 9876543210</code>",
            reply_markup=CLOSE_BTN
        )

    admin_list = ""
    for uid in admins:
        try:
            uid_int = int(uid)
        except:
            admin_list += f"<blockquote><b>Invalid ID: <code>{uid}</code></b></blockquote>\n"
            continue

        if uid_int in admin_ids:
            admin_list += f"<blockquote><b>ID <code>{uid_int}</code> already exists.</b></blockquote>\n"
            continue

        uid_str = str(uid_int)
        if uid_str.isdigit() and len(uid_str) == 10:
            admin_list += f"<b><blockquote>(ID: <code>{uid_str}</code>) added.</blockquote></b>\n"
            check += 1
        else:
            admin_list += f"<blockquote><b>Invalid ID: <code>{uid}</code></b></blockquote>\n"

    if check == len(admins):
        for uid in admins:
            await db.add_admin(int(uid))
        await pro.edit(f"<b>✅ Admin(s) added successfully:</b>\n\n{admin_list}", reply_markup=CLOSE_BTN)
    else:
        await pro.edit(
            f"<b>❌ Some errors occurred while adding admins:</b>\n\n{admin_list.strip()}\n\n"
            "<b><i>Please check and try again.</i></b>",
            reply_markup=CLOSE_BTN
        )


# ─────────────────────────────────────────────
# DELETE ADMINS  (Owner only)
# ─────────────────────────────────────────────

@Bot.on_message(filters.command('deladmin') & filters.private)
async def delete_admins(client: Client, message: Message):
    if not await check_owner_only(message):
        return

    pro = await message.reply("<b><i>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ..</i></b>", quote=True)
    admin_ids = await db.get_all_admins()
    admins = message.text.split()[1:]

    if not admins:
        return await pro.edit(
            "<b>Please provide valid admin ID(s) to remove.</b>\n\n"
            "<b>Usage:</b>\n"
            "<code>/deladmin [user_id]</code> — Remove specific IDs\n"
            "<code>/deladmin all</code> — Remove all admins",
            reply_markup=CLOSE_BTN
        )

    if len(admins) == 1 and admins[0].lower() == "all":
        if admin_ids:
            for a in admin_ids:
                await db.del_admin(a)
            ids = "\n".join(f"<blockquote><code>{admin}</code> ✅</blockquote>" for admin in admin_ids)
            return await pro.edit(f"<b>⛔️ All admin IDs have been removed:</b>\n{ids}", reply_markup=CLOSE_BTN)
        else:
            return await pro.edit("<b><blockquote>No admin IDs to remove.</blockquote></b>", reply_markup=CLOSE_BTN)

    if admin_ids:
        passed = ''
        for admin_id in admins:
            try:
                aid = int(admin_id)
            except:
                passed += f"<blockquote><b>Invalid ID: <code>{admin_id}</code></b></blockquote>\n"
                continue

            if aid in admin_ids:
                await db.del_admin(aid)
                passed += f"<blockquote><code>{aid}</code> ✅ Removed</blockquote>\n"
            else:
                passed += f"<blockquote><b>ID <code>{aid}</code> not found in admin list.</b></blockquote>\n"

        await pro.edit(f"<b>⛔️ Admin removal result:</b>\n\n{passed}", reply_markup=CLOSE_BTN)
    else:
        await pro.edit("<b><blockquote>No admin IDs available to delete.</blockquote></b>", reply_markup=CLOSE_BTN)


# ─────────────────────────────────────────────
# ADMIN LIST  (Owner + Admins)
# ─────────────────────────────────────────────

@Bot.on_message(filters.command('admins') & filters.private)
async def get_admins(client: Client, message: Message):
    if not await check_admin_or_owner(message):
        return

    pro = await message.reply("<b><i>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ..</i></b>", quote=True)
    admin_ids = await db.get_all_admins()

    if not admin_ids:
        admin_list = "<b><blockquote>❌ No admins found.</blockquote></b>"
    else:
        admin_list = "\n".join(f"<b><blockquote>ID: <code>{id}</code></blockquote></b>" for id in admin_ids)

    await pro.edit(f"<b>⚡ Current Admin List:</b>\n\n{admin_list}", reply_markup=CLOSE_BTN)


# ─────────────────────────────────────────────
# CLOSE BUTTON HANDLER
# ─────────────────────────────────────────────

@Bot.on_callback_query(filters.regex(r"^close$"))
async def close_callback(client: Client, cb: CallbackQuery):
    try:
        await cb.message.delete()
    except Exception:
        pass
    await cb.answer()
