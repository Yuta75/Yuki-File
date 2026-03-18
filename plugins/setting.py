# settings.py
# ⚙️ Full Settings Panel — All 8 Sections
# Credits: @VoidXTora | Based for CosmicBotz FileStore

import asyncio
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from pyrogram.errors import MessageNotModified

from config import OWNER_ID, USER_REPLY_TEXT
from bot import Bot
from database.database import db
from plugins.VoidXTora import check_admin_or_owner


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def tick(val: bool) -> str:
    return "✅" if val else "❌"

async def is_admin_or_owner(user_id: int) -> bool:
    return user_id == OWNER_ID or await db.admin_exist(user_id)

async def safe_edit(cb: CallbackQuery, text: str, markup: InlineKeyboardMarkup):
    try:
        await cb.message.edit_text(text, reply_markup=markup)
    except MessageNotModified:
        pass
    except Exception:
        pass


# ─────────────────────────────────────────────
# MAIN SETTINGS MENU
# ─────────────────────────────────────────────

def main_settings_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📡 Fᴏʀᴄᴇ Sᴜʙ", callback_data="cfg_fsub")],
        [InlineKeyboardButton("👑 Aᴅᴍɪɴs", callback_data="cfg_admins")],
        [InlineKeyboardButton("🚫 Bᴀɴɴᴇᴅ Usᴇʀs", callback_data="cfg_banned")],
        [InlineKeyboardButton("⏱ Aᴜᴛᴏ Dᴇʟᴇᴛᴇ", callback_data="cfg_autodelete")],
        [InlineKeyboardButton("📁 Fɪʟᴇs Sᴇᴛᴛɪɴɢs", callback_data="cfg_files")],
        [InlineKeyboardButton("🔄 Rᴇǫ Fᴏʀᴄᴇ Sᴜʙ", callback_data="cfg_reqfsub")],
        [InlineKeyboardButton("💰 Vᴇʀɪꜰʏ Sᴇᴛᴛɪɴɢs", callback_data="cfg_verify")],
        [InlineKeyboardButton("✍️ Cᴀᴘᴛɪᴏɴ Sᴇᴛᴛɪɴɢs", callback_data="cfg_caption")],
        [InlineKeyboardButton("Cʟᴏsᴇ ✖", callback_data="cfg_close")],
    ])

MAIN_TEXT = (
    "<b>⚙️ Sᴇᴛᴛɪɴɢs Mᴇɴᴜ:</b>\n\n"
    "<b>Sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ᴄᴜsᴛᴏᴍɪᴢᴇ ʏᴏᴜʀ ʙᴏᴛ sᴇᴛᴛɪɴɢs:</b> 🔥"
)

@Bot.on_message(filters.command("settings") & filters.private)
async def settings_cmd(client: Client, message: Message):
    if not await check_admin_or_owner(message):
        return
    await message.reply_text(MAIN_TEXT, reply_markup=main_settings_markup())


# ─────────────────────────────────────────────
# 1. FORCE SUB
# ─────────────────────────────────────────────

async def fsub_text_markup(client: Client):
    channels = await db.show_channels()
    lines = ""
    buttons_rows = []
    if channels:
        for cid in channels:
            mode = await db.get_channel_mode(cid)
            mode_icon = "🔄" if mode == "on" else "📡"
            try:
                chat = await client.get_chat(cid)
                name = chat.title or str(cid)
            except Exception:
                name = str(cid)
            lines += f"<blockquote>◈ {mode_icon} <b>{name}</b>\n   ID: <code>{cid}</code> | Mode: <b>{mode.upper()}</b></blockquote>\n"
            buttons_rows.append([
                InlineKeyboardButton(f"🗑 Rᴇᴍᴏᴠᴇ {name[:15]}", callback_data=f"fsub_del_{cid}"),
                InlineKeyboardButton(
                    f"Mᴏᴅᴇ: {'Rᴇǫ' if mode == 'on' else 'Nᴏʀᴍᴀʟ'}",
                    callback_data=f"fsub_mode_{cid}"
                ),
            ])
    else:
        lines = "<blockquote>❌ Nᴏ ꜰᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟs ᴀᴅᴅᴇᴅ.</blockquote>"

    text = (
        "<b>📡 Fᴏʀᴄᴇ Sᴜʙ Sᴇᴛᴛɪɴɢs</b>\n\n"
        + lines
        + "\n<i>Usᴇ /addchnl [channel_id] ᴛᴏ ᴀᴅᴅ ᴀ ᴄʜᴀɴɴᴇʟ.</i>"
    )
    buttons_rows.append([InlineKeyboardButton("◁ Bᴀᴄᴋ", callback_data="cfg_back")])
    return text, InlineKeyboardMarkup(buttons_rows)


# ─────────────────────────────────────────────
# 2. ADMINS
# ─────────────────────────────────────────────

async def admins_text_markup():
    admin_ids = await db.get_all_admins()
    if admin_ids:
        lines = "\n".join(
            f"<blockquote>◈ <code>{aid}</code></blockquote>" for aid in admin_ids
        )
    else:
        lines = "<blockquote>❌ Nᴏ ᴀᴅᴍɪɴs ꜰᴏᴜɴᴅ.</blockquote>"

    text = (
        "<b>👑 Aᴅᴍɪɴs Lɪsᴛ</b>\n\n"
        + lines
        + "\n\n<i>/add_admin [id] — Aᴅᴅ\n/deladmin [id] — Rᴇᴍᴏᴠᴇ</i>"
    )
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("◁ Bᴀᴄᴋ", callback_data="cfg_back")]
    ])
    return text, markup


# ─────────────────────────────────────────────
# 3. BANNED USERS
# ─────────────────────────────────────────────

async def banned_text_markup():
    banned = await db.get_ban_users()
    if banned:
        lines = "\n".join(
            f"<blockquote>◈ <code>{uid}</code></blockquote>" for uid in banned
        )
    else:
        lines = "<blockquote>✅ Nᴏ ʙᴀɴɴᴇᴅ ᴜsᴇʀs.</blockquote>"

    text = (
        "<b>🚫 Bᴀɴɴᴇᴅ Usᴇʀs</b>\n\n"
        + lines
        + "\n\n<i>/ban [id] — Bᴀɴ\n/unban [id] — Uɴʙᴀɴ\n/banlist — Fᴜʟʟ ʟɪsᴛ</i>"
    )
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("◁ Bᴀᴄᴋ", callback_data="cfg_back")]
    ])
    return text, markup


# ─────────────────────────────────────────────
# 4. AUTO DELETE
# ─────────────────────────────────────────────

async def autodelete_text_markup():
    timer = await db.get_del_timer()
    status = f"<code>{timer}s</code>" if timer else "❌ Dɪsᴀʙʟᴇᴅ"
    text = (
        "<b>⏱ Aᴜᴛᴏ Dᴇʟᴇᴛᴇ Sᴇᴛᴛɪɴɢs</b>\n\n"
        f"<blockquote>◈ Cᴜʀʀᴇɴᴛ Tɪᴍᴇʀ: {status}</blockquote>\n\n"
        "<i>/dlt_time [seconds] — Sᴇᴛ ᴛɪᴍᴇʀ\n"
        "/check_dlt_time — Cʜᴇᴄᴋ ᴄᴜʀʀᴇɴᴛ ᴛɪᴍᴇʀ\n"
        "Set 0 ᴛᴏ ᴅɪsᴀʙʟᴇ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ.</i>"
    )
    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏱ Sᴇᴛ 5ᴍ", callback_data="adel_300"),
            InlineKeyboardButton("⏱ Sᴇᴛ 10ᴍ", callback_data="adel_600"),
            InlineKeyboardButton("⏱ Sᴇᴛ 30ᴍ", callback_data="adel_1800"),
        ],
        [
            InlineKeyboardButton("⏱ Sᴇᴛ 1ʜ", callback_data="adel_3600"),
            InlineKeyboardButton("❌ Dɪsᴀʙʟᴇ", callback_data="adel_0"),
        ],
        [InlineKeyboardButton("◁ Bᴀᴄᴋ", callback_data="cfg_back")],
    ])
    return text, markup


# ─────────────────────────────────────────────
# 5. FILES SETTINGS
# ─────────────────────────────────────────────

async def files_text_markup():
    cfg = await db.get_settings()
    protect = cfg.get("protect_content", False)
    hide_cap = cfg.get("hide_caption", False)
    chnl_btn = cfg.get("channel_button", False)

    text = (
        "<b>📁 Fɪʟᴇs Rᴇʟᴀᴛᴇᴅ Sᴇᴛᴛɪɴɢs ⚙️</b>\n\n"
        f"<blockquote>"
        f"🔒 ᴘʀᴏᴛᴇᴄᴛ ᴄᴏɴᴛᴇɴᴛ: {'Eɴᴀʙʟᴇᴅ ✅' if protect else 'Dɪsᴀʙʟᴇᴅ ❌'}\n"
        f"😶 ʜɪᴅᴇ ᴄᴀᴘᴛɪᴏɴ: {'Eɴᴀʙʟᴇᴅ ✅' if hide_cap else 'Dɪsᴀʙʟᴇᴅ ❌'}\n"
        f"🔘 ᴄʜᴀɴɴᴇʟ ʙᴜᴛᴛᴏɴ: {'Eɴᴀʙʟᴇᴅ ✅' if chnl_btn else 'Dɪsᴀʙʟᴇᴅ ❌'}"
        f"</blockquote>\n\n"
        "<i>Cʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴs ᴛᴏ ᴛᴏɢɢʟᴇ sᴇᴛᴛɪɴɢs.</i>"
    )
    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"Pʀᴏᴛᴇᴄᴛ Cᴏɴᴛᴇɴᴛ: {tick(protect)}", callback_data="files_protect"),
            InlineKeyboardButton(f"Hɪᴅᴇ Cᴀᴘᴛɪᴏɴ: {tick(hide_cap)}", callback_data="files_hidecap"),
        ],
        [
            InlineKeyboardButton(f"Cʜᴀɴɴᴇʟ Bᴜᴛᴛᴏɴ: {tick(chnl_btn)}", callback_data="files_chnlbtn"),
        ],
        [InlineKeyboardButton("◁ Bᴀᴄᴋ", callback_data="cfg_back")],
    ])
    return text, markup


# ─────────────────────────────────────────────
# 6. REQ FORCE SUB
# ─────────────────────────────────────────────

async def reqfsub_text_markup(client: Client):
    channels = await db.show_channels()
    lines = ""
    if channels:
        for cid in channels:
            mode = await db.get_channel_mode(cid)
            req_icon = "✅" if mode == "on" else "❌"
            try:
                chat = await client.get_chat(cid)
                name = chat.title or str(cid)
            except Exception:
                name = str(cid)
            lines += f"<blockquote>◈ <b>{name}</b> — Rᴇǫ Mᴏᴅᴇ: {req_icon}</blockquote>\n"
    else:
        lines = "<blockquote>❌ Nᴏ ᴄʜᴀɴɴᴇʟs ꜰᴏᴜɴᴅ.</blockquote>"

    text = (
        "<b>🔄 Rᴇǫᴜᴇsᴛ Fᴏʀᴄᴇ Sᴜʙ Sᴇᴛᴛɪɴɢs</b>\n\n"
        + lines
        + "\n<i>Usᴇ /fsub_mode ᴛᴏ ᴛᴏɢɢʟᴇ ᴍᴏᴅᴇ ᴘᴇʀ ᴄʜᴀɴɴᴇʟ.\n"
        "Rᴇǫ Mᴏᴅᴇ: ᴜsᴇʀs sᴇɴᴅ ᴀ ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛ ɪɴsᴛᴇᴀᴅ ᴏꜰ ᴅɪʀᴇᴄᴛʟʏ ᴊᴏɪɴɪɴɢ.</i>"
    )
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("◁ Bᴀᴄᴋ", callback_data="cfg_back")]
    ])
    return text, markup


# ─────────────────────────────────────────────
# 7. VERIFY SETTINGS
# ─────────────────────────────────────────────

async def verify_text_markup():
    cfg = await db.get_settings()
    verify_on = cfg.get("verify_enabled", False)

    text = (
        "<b>💰 Vᴇʀɪꜰʏ Sᴇᴛᴛɪɴɢs</b>\n\n"
        f"<blockquote>◈ Vᴇʀɪꜰɪᴄᴀᴛɪᴏɴ: {'Eɴᴀʙʟᴇᴅ ✅' if verify_on else 'Dɪsᴀʙʟᴇᴅ ❌'}</blockquote>\n\n"
        "<i>Wʜᴇɴ ᴇɴᴀʙʟᴇᴅ, ᴜsᴇʀs ᴍᴜsᴛ ᴄᴏᴍᴘʟᴇᴛᴇ ᴀ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ sᴛᴇᴘ\n"
        "ʙᴇꜰᴏʀᴇ ᴀᴄᴄᴇssɪɴɢ ꜰɪʟᴇs.</i>"
    )
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"Vᴇʀɪꜰɪᴄᴀᴛɪᴏɴ: {tick(verify_on)}",
            callback_data="verify_toggle"
        )],
        [InlineKeyboardButton("◁ Bᴀᴄᴋ", callback_data="cfg_back")],
    ])
    return text, markup


# ─────────────────────────────────────────────
# 8. CAPTION SETTINGS
# ─────────────────────────────────────────────

async def caption_text_markup():
    cfg = await db.get_settings()
    cap_on = cfg.get("custom_caption", True)

    text = (
        "<b>✍️ Cᴀᴘᴛɪᴏɴ Sᴇᴛᴛɪɴɢs</b>\n\n"
        f"<blockquote>◈ Cᴜsᴛᴏᴍ Cᴀᴘᴛɪᴏɴ: {'Eɴᴀʙʟᴇᴅ ✅' if cap_on else 'Dɪsᴀʙʟᴇᴅ ❌'}</blockquote>\n\n"
        "<i>Wʜᴇɴ ᴅɪsᴀʙʟᴇᴅ, ᴛʜᴇ ᴏʀɪɢɪɴᴀʟ ꜰɪʟᴇ ᴄᴀᴘᴛɪᴏɴ ɪs sᴇɴᴛ.\n"
        "Wʜᴇɴ ᴇɴᴀʙʟᴇᴅ, ʏᴏᴜʀ CUSTOM_CAPTION ꜰʀᴏᴍ ᴄᴏɴꜰɪɢ ɪs ᴜsᴇᴅ.</i>"
    )
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"Cᴜsᴛᴏᴍ Cᴀᴘᴛɪᴏɴ: {tick(cap_on)}",
            callback_data="caption_toggle"
        )],
        [InlineKeyboardButton("◁ Bᴀᴄᴋ", callback_data="cfg_back")],
    ])
    return text, markup


# ─────────────────────────────────────────────
# MASTER CALLBACK HANDLER
# ─────────────────────────────────────────────

@Bot.on_callback_query(filters.regex(r"^cfg_|^fsub_|^adel_|^files_|^verify_|^caption_"))
async def settings_callback(client: Client, cb: CallbackQuery):
    user_id = cb.from_user.id
    if not await is_admin_or_owner(user_id):
        await cb.answer(USER_REPLY_TEXT, show_alert=True)
        return

    data = cb.data

    # ── MAIN MENU ──
    if data == "cfg_back":
        await safe_edit(cb, MAIN_TEXT, main_settings_markup())
        await cb.answer()

    elif data == "cfg_close":
        try:
            await cb.message.delete()
        except Exception:
            pass
        await cb.answer()

    # ── SECTION ROUTERS ──
    elif data == "cfg_fsub":
        text, markup = await fsub_text_markup(client)
        await safe_edit(cb, text, markup)
        await cb.answer()

    elif data == "cfg_admins":
        text, markup = await admins_text_markup()
        await safe_edit(cb, text, markup)
        await cb.answer()

    elif data == "cfg_banned":
        text, markup = await banned_text_markup()
        await safe_edit(cb, text, markup)
        await cb.answer()

    elif data == "cfg_autodelete":
        text, markup = await autodelete_text_markup()
        await safe_edit(cb, text, markup)
        await cb.answer()

    elif data == "cfg_files":
        text, markup = await files_text_markup()
        await safe_edit(cb, text, markup)
        await cb.answer()

    elif data == "cfg_reqfsub":
        text, markup = await reqfsub_text_markup(client)
        await safe_edit(cb, text, markup)
        await cb.answer()

    elif data == "cfg_verify":
        text, markup = await verify_text_markup()
        await safe_edit(cb, text, markup)
        await cb.answer()

    elif data == "cfg_caption":
        text, markup = await caption_text_markup()
        await safe_edit(cb, text, markup)
        await cb.answer()

    # ── FORCE SUB ACTIONS ──
    elif data.startswith("fsub_del_"):
        cid = int(data.split("fsub_del_")[1])
        await db.rem_channel(cid)
        text, markup = await fsub_text_markup(client)
        await safe_edit(cb, text, markup)
        await cb.answer("✅ Channel removed!")

    elif data.startswith("fsub_mode_"):
        cid = int(data.split("fsub_mode_")[1])
        cur = await db.get_channel_mode(cid)
        new_mode = "off" if cur == "on" else "on"
        await db.set_channel_mode(cid, new_mode)
        text, markup = await fsub_text_markup(client)
        await safe_edit(cb, text, markup)
        await cb.answer(f"Mode set to {new_mode.upper()}")

    # ── AUTO DELETE PRESETS ──
    elif data.startswith("adel_"):
        secs = int(data.split("adel_")[1])
        await db.set_del_timer(secs)
        text, markup = await autodelete_text_markup()
        await safe_edit(cb, text, markup)
        label = f"{secs}s" if secs else "Disabled"
        await cb.answer(f"✅ Timer set to {label}")

    # ── FILES SETTINGS TOGGLES ──
    elif data == "files_protect":
        cfg = await db.get_settings()
        await db.update_setting("protect_content", not cfg.get("protect_content", False))
        text, markup = await files_text_markup()
        await safe_edit(cb, text, markup)
        await cb.answer("✅ Protect Content toggled!")

    elif data == "files_hidecap":
        cfg = await db.get_settings()
        await db.update_setting("hide_caption", not cfg.get("hide_caption", False))
        text, markup = await files_text_markup()
        await safe_edit(cb, text, markup)
        await cb.answer("✅ Hide Caption toggled!")

    elif data == "files_chnlbtn":
        cfg = await db.get_settings()
        await db.update_setting("channel_button", not cfg.get("channel_button", False))
        text, markup = await files_text_markup()
        await safe_edit(cb, text, markup)
        await cb.answer("✅ Channel Button toggled!")

    # ── VERIFY TOGGLE ──
    elif data == "verify_toggle":
        cfg = await db.get_settings()
        await db.update_setting("verify_enabled", not cfg.get("verify_enabled", False))
        text, markup = await verify_text_markup()
        await safe_edit(cb, text, markup)
        await cb.answer("✅ Verify setting toggled!")

    # ── CAPTION TOGGLE ──
    elif data == "caption_toggle":
        cfg = await db.get_settings()
        await db.update_setting("custom_caption", not cfg.get("custom_caption", True))
        text, markup = await caption_text_markup()
        await safe_edit(cb, text, markup)
        await cb.answer("✅ Caption setting toggled!")


#=====================================================================================##
# Credits:- @VoidXTora
# Maintained by: Mythic_Bots
# Support: @MythicBot_Support
#=====================================================================================##
