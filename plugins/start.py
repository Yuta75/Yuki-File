# Don't Remove Credit @CodeFlix_Bots, @rohit_1888
# Ask Doubt on telegram @CodeflixSupport
#
# Copyright (C) 2025 by Codeflix-Bots@Github, < https://github.com/Codeflix-Bots >.
#
# This file is part of < https://github.com/Codeflix-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/Codeflix-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
import os
import random
import sys
import time
from datetime import datetime, timedelta
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, ReplyKeyboardMarkup, ChatInviteLink, ChatPrivileges
)
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant

from bot import Bot
from config import *
from helper_func import *
from database.database import *
from handlers.caption_parser import apply_template
from handlers.chat_action import show_action, show_file_action, refresh_action, NORMAL_ACTION

BAN_SUPPORT = f"{BAN_SUPPORT}"


# ─────────────────────────────────────────────
# CAPTION BUILDER
# ─────────────────────────────────────────────

async def build_caption(original: str, file_name: str, settings: dict):
    """
    Priority order:
      1. hide_caption ON          → return None (file sent with no caption)
      2. template mode ON         → fill template with auto-detected vars
      3. custom_caption ON        → original + CUSTOM_CAPTION suffix
      4. fallback                 → original as-is

    Returns None or a string.
    """
    if settings.get("hide_caption", False):
        return None

    if settings.get("caption_template_enabled", False):
        template = settings.get("caption_template", "")
        if template:
            return apply_template(template, original, file_name)

    if settings.get("custom_caption", True):
        return f"{original}\n\n{CUSTOM_CAPTION}".strip() if CUSTOM_CAPTION else original

    return original


# ─────────────────────────────────────────────
# /start HANDLER
# ─────────────────────────────────────────────

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id

    # ── Ban check ──
    banned_users = await db.get_ban_users()
    if user_id in banned_users:
        return await message.reply_text(
            "<b>⛔️ You are Bᴀɴɴᴇᴅ from using this bot.</b>\n\n"
            "<i>Contact support if you think this is a mistake.</i>",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Contact Support", url=BAN_SUPPORT)]]
            )
        )

    bot_settings = await db.get_settings()

    # ── Force sub check ──
    if bot_settings.get('fsub_mode', True):
        if not await is_subscribed(client, user_id):
            return await not_joined(client, message)

    FILE_AUTO_DELETE = await db.get_del_timer()

    # ── Register user ──
    if not await db.present_user(user_id):
        try:
            await db.add_user(user_id)
        except:
            pass

    text = message.text

    # ══════════════════════════════════════════
    # FILE DELIVERY
    # ══════════════════════════════════════════
    if len(text) > 7:

        # Show file action for full duration — visible even on fast servers
        action = await show_file_action(client, message.chat.id)

        try:
            base64_string = text.split(" ", 1)[1]
        except IndexError:
            return

        string   = await decode(base64_string)
        argument = string.split("-")

        ids = []
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end   = int(int(argument[2]) / abs(client.db_channel.id))
                ids   = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))
            except Exception as e:
                print(f"Error decoding IDs: {e}")
                return
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except Exception as e:
                print(f"Error decoding ID: {e}")
                return

        temp_msg = await message.reply("<b>Please wait...</b>")
        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            await message.reply_text("Something went wrong!")
            print(f"Error getting messages: {e}")
            return
        finally:
            await temp_msg.delete()

        # Channel button config
        chnl_btn_enabled = bot_settings.get("channel_button", False)
        chnl_btn_mode    = bot_settings.get("channel_button_mode", "each")  # "each" | "end"
        chnl_btn_title   = bot_settings.get("channel_button_title", "📢 Join Channel")
        chnl_btn_link    = bot_settings.get("channel_button_link", "")

        codeflix_msgs = []

        for msg in messages:
            original_caption = msg.caption.html if msg.caption else ""

            # Try to get filename from media
            file_name = ""
            for attr in ("document", "video", "audio"):
                media = getattr(msg, attr, None)
                if media and getattr(media, "file_name", None):
                    file_name = media.file_name
                    break

            caption = await build_caption(original_caption, file_name, bot_settings)
            protect = bot_settings.get('protect_content', False)

            # Per-file channel button
            if chnl_btn_enabled and chnl_btn_mode == "each" and chnl_btn_link:
                reply_markup = InlineKeyboardMarkup([[
                    InlineKeyboardButton(chnl_btn_title, url=chnl_btn_link)
                ]])
            else:
                reply_markup = msg.reply_markup if DISABLE_CHANNEL_BUTTON else None

            # Keep action alive during multi-file loops
            await refresh_action(client, message.chat.id, action)

            try:
                snt_msg = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=protect
                )
                await asyncio.sleep(0.5)
                codeflix_msgs.append(snt_msg)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                copied_msg = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=protect
                )
                codeflix_msgs.append(copied_msg)
            except:
                pass

        # ── Auto delete ──
        if FILE_AUTO_DELETE > 0:
            # Channel button on delete alert (end mode)
            end_btn_markup = None
            if chnl_btn_enabled and chnl_btn_mode == "end" and chnl_btn_link:
                end_btn_markup = InlineKeyboardMarkup([[
                    InlineKeyboardButton(chnl_btn_title, url=chnl_btn_link)
                ]])

            notification_msg = await message.reply(
                f"<b>Tʜɪs Fɪʟᴇ ᴡɪʟʟ ʙᴇ Dᴇʟᴇᴛᴇᴅ ɪɴ {get_exp_time(FILE_AUTO_DELETE)}. "
                f"Pʟᴇᴀsᴇ sᴀᴠᴇ ᴏʀ ғᴏʀᴡᴀʀᴅ ɪᴛ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ʙᴇғᴏʀᴇ ɪᴛ ɢᴇᴛs Dᴇʟᴇᴛᴇᴅ.</b>",
                reply_markup=end_btn_markup
            )

            await asyncio.sleep(FILE_AUTO_DELETE)

            for snt_msg in codeflix_msgs:
                if snt_msg:
                    try:
                        await snt_msg.delete()
                    except Exception as e:
                        print(f"Error deleting message {snt_msg.id}: {e}")

            try:
                reload_url = (
                    f"https://t.me/{client.username}?start={message.command[1]}"
                    if message.command and len(message.command) > 1
                    else None
                )
                final_buttons = []
                if reload_url:
                    final_buttons.append([InlineKeyboardButton("ɢᴇᴛ ғɪʟᴇ ᴀɢᴀɪɴ!", url=reload_url)])
                if chnl_btn_enabled and chnl_btn_mode == "end" and chnl_btn_link:
                    final_buttons.append([InlineKeyboardButton(chnl_btn_title, url=chnl_btn_link)])

                await notification_msg.edit(
                    "<b>ʏᴏᴜʀ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ !!\n\n"
                    "ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ᴅᴇʟᴇᴛᴇᴅ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ 👇</b>",
                    reply_markup=InlineKeyboardMarkup(final_buttons) if final_buttons else None
                )
            except Exception as e:
                print(f"Error updating notification: {e}")

    # ══════════════════════════════════════════
    # NORMAL /start
    # ══════════════════════════════════════════
    else:
        # Typing action held for full duration — visible on fast servers
        await show_action(client, message.chat.id, NORMAL_ACTION)

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("• ᴍᴏʀᴇ ᴄʜᴀɴɴᴇʟs •", url="https://t.me/+rt0k66qGSK83NDRl")],
            [
                InlineKeyboardButton("• ᴀʙᴏᴜᴛ", callback_data="about"),
                InlineKeyboardButton('ʜᴇʟᴘ •', callback_data="help")
            ]
        ])
        await message.reply_photo(
            photo=START_PIC,
            caption=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup,
            message_effect_id=5104841245755180586
        )
        return


#=====================================================================================##
# Don't Remove Credit @CodeFlix_Bots, @rohit_1888

chat_data_cache = {}

async def not_joined(client: Client, message: Message):
    temp = await message.reply("<b><i>ᴡᴀɪᴛ ᴀ sᴇᴄ..</i></b>")
    user_id = message.from_user.id
    buttons = []
    count   = 0

    try:
        all_channels = await db.show_channels()
        for total, chat_id in enumerate(all_channels, start=1):
            mode = await db.get_channel_mode(chat_id)
            await message.reply_chat_action(ChatAction.TYPING)

            if not await is_sub(client, user_id, chat_id):
                try:
                    if chat_id in chat_data_cache:
                        data = chat_data_cache[chat_id]
                    else:
                        data = await client.get_chat(chat_id)
                        chat_data_cache[chat_id] = data

                    name = data.title

                    if mode == "on" and not data.username:
                        invite = await client.create_chat_invite_link(
                            chat_id=chat_id,
                            creates_join_request=True,
                            expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                        )
                        link = invite.invite_link
                    else:
                        if data.username:
                            link = f"https://t.me/{data.username}"
                        else:
                            invite = await client.create_chat_invite_link(
                                chat_id=chat_id,
                                expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                            )
                            link = invite.invite_link

                    buttons.append([InlineKeyboardButton(text=name, url=link)])
                    count += 1
                    await temp.edit(f"<b>{'! ' * count}</b>")

                except Exception as e:
                    print(f"Error with chat {chat_id}: {e}")
                    return await temp.edit(
                        f"<b><i>! Eʀʀᴏʀ, Cᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ sᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇs @rohit_1888</i></b>\n"
                        f"<blockquote expandable><b>Rᴇᴀsᴏɴ:</b> {e}</blockquote>"
                    )

        try:
            buttons.append([
                InlineKeyboardButton(
                    text='♻️ Tʀʏ Aɢᴀɪɴ',
                    url=f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ])
        except IndexError:
            pass

        await message.reply_photo(
            photo=FORCE_PIC,
            caption=FORCE_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    except Exception as e:
        print(f"Final Error: {e}")
        await temp.edit(
            f"<b><i>! Eʀʀᴏʀ, Cᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ sᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇs @VoidxTora</i></b>\n"
            f"<blockquote expandable><b>Rᴇᴀsᴏɴ:</b> {e}</blockquote>"
        )

#=====================================================================================##

@Bot.on_message(filters.command('commands') & filters.private)
async def bcmd(bot: Bot, message: Message):
    if not await check_admin_or_owner(message):
        return
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("• ᴄʟᴏsᴇ •", callback_data="close")]])
    await message.reply(text=CMD_TXT, reply_markup=reply_markup, quote=True)
