# settings.py
# ⚙️ Full Settings Panel — All 8 Sections
# Credits: @VoidXTora | CosmicBotz FileStore

import asyncio
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from pyrogram.errors import MessageNotModified

from config import OWNER_ID, USER_REPLY_TEXT, CUSTOM_CAPTION
from bot import Bot
from database.database import db
from plugins.VoidXTora import check_admin_or_owner

# Import awaiting-input registry from channel_post to prevent it
# intercepting admin input messages as file links
try:
    from plugins.channel_post import mark_awaiting, clear_awaiting
except ImportError:
    try:
        from channel_post import mark_awaiting, clear_awaiting
    except Exception:
        def mark_awaiting(uid): pass
        def clear_awaiting(uid): pass


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
# AWAITING INPUT STATE
# ─────────────────────────────────────────────

_awaiting_template: set = set()
_awaiting_chnl_link: set = set()
_awaiting_chnl_title: set = set()


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
        [InlineKeyboardButton("Cʟᴏsᴇ ✖", callback_data="close")],
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
            lines += (
                f"<blockquote>◈ {mode_icon} <b>{name}</b>\n"
                f"   ID: <code>{cid}</code> | Mode: <b>{mode.upper()}</b></blockquote>\n"
            )
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
    lines = "\n".join(
        f"<blockquote>◈ <code>{aid}</code></blockquote>" for aid in admin_ids
    ) if admin_ids else "<blockquote>❌ Nᴏ ᴀᴅᴍɪɴs ꜰᴏᴜɴᴅ.</blockquote>"
    text = (
        "<b>👑 Aᴅᴍɪɴs Lɪsᴛ</b>\n\n" + lines
        + "\n\n<i>/add_admin [id] — Aᴅᴅ\n/deladmin [id] — Rᴇᴍᴏᴠᴇ</i>"
    )
    return text, InlineKeyboardMarkup([[InlineKeyboardButton("◁ Bᴀᴄᴋ", callback_data="cfg_back")]])


# ─────────────────────────────────────────────
# 3. BANNED USERS
# ─────────────────────────────────────────────

async def banned_text_markup():
    banned = await db.get_ban_users()
    lines = "\n".join(
        f"<blockquote>◈ <code>{uid}</code></blockquote>" for uid in banned
    ) if banned else "<blockquote>✅ Nᴏ ʙᴀɴɴᴇᴅ ᴜsᴇʀs.</blockquote>"
    text = (
        "<b>🚫 Bᴀɴɴᴇᴅ Usᴇʀs</b>\n\n" + lines
        + "\n\n<i>/ban [id] — Bᴀɴ\n/unban [id] — Uɴʙᴀɴ\n/banlist — Fᴜʟʟ ʟɪsᴛ</i>"
    )
    return text, InlineKeyboardMarkup([[InlineKeyboardButton("◁ Bᴀᴄᴋ", callback_data="cfg_back")]])


# ─────────────────────────────────────────────
# 4. AUTO DELETE
# ─────────────────────────────────────────────

async def autodelete_text_markup():
    timer = await db.get_del_timer()
    status = f"<code>{timer}s</code>" if timer else "❌ Dɪsᴀʙʟᴇᴅ"
    text = (
        "<b>⏱ Aᴜᴛᴏ Dᴇʟᴇᴛᴇ Sᴇᴛᴛɪɴɢs</b>\n\n"
        f"<blockquote>◈ Cᴜʀʀᴇɴᴛ Tɪᴍᴇʀ: {status}</blockquote>\n\n"
        "<i>/dlt_time [seconds] — Sᴇᴛ ᴛɪᴍᴇʀ\nSet 0 ᴛᴏ ᴅɪsᴀʙʟᴇ.</i>"
    )
    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏱ 5ᴍ", callback_data="adel_300"),
            InlineKeyboardButton("⏱ 10ᴍ", callback_data="adel_600"),
            InlineKeyboardButton("⏱ 30ᴍ", callback_data="adel_1800"),
        ],
        [
            InlineKeyboardButton("⏱ 1ʜ", callback_data="adel_3600"),
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
    protect   = cfg.get("protect_content", False)
    hide_cap  = cfg.get("hide_caption", False)
    chnl_btn  = cfg.get("channel_button", False)
    chnl_mode = cfg.get("channel_button_mode", "each")   # "each" | "end"
    chnl_link = cfg.get("channel_button_link", "") or "Nᴏᴛ sᴇᴛ"
    chnl_title= cfg.get("channel_button_title", "📢 Join Channel")

    mode_label = "Eᴀᴄʜ Fɪʟᴇ" if chnl_mode == "each" else "Dᴇʟᴇᴛᴇ Aʟᴇʀᴛ"

    text = (
        "<b>📁 Fɪʟᴇs Rᴇʟᴀᴛᴇᴅ Sᴇᴛᴛɪɴɢs ⚙️</b>\n\n"
        "<blockquote>"
        f"🔒 Pʀᴏᴛᴇᴄᴛ Cᴏɴᴛᴇɴᴛ : {'Eɴᴀʙʟᴇᴅ ✅' if protect else 'Dɪsᴀʙʟᴇᴅ ❌'}\n"
        f"😶 Hɪᴅᴇ Cᴀᴘᴛɪᴏɴ  : {'Eɴᴀʙʟᴇᴅ ✅' if hide_cap else 'Dɪsᴀʙʟᴇᴅ ❌'}\n"
        f"🔘 Cʜᴀɴɴᴇʟ Bᴜᴛᴛᴏɴ : {'Eɴᴀʙʟᴇᴅ ✅' if chnl_btn else 'Dɪsᴀʙʟᴇᴅ ❌'}\n"
        + (
            f"   ◈ Mᴏᴅᴇ  : {mode_label}\n"
            f"   ◈ Tɪᴛʟᴇ : <code>{chnl_title}</code>\n"
            f"   ◈ Lɪɴᴋ  : <code>{chnl_link}</code>"
            if chnl_btn else ""
        )
        + "</blockquote>\n\n"
        "<i>Cʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴs ᴛᴏ ᴄᴏɴꜰɪɢᴜʀᴇ.</i>"
    )

    rows = [
        [
            InlineKeyboardButton(f"🔒 Pʀᴏᴛᴇᴄᴛ: {tick(protect)}", callback_data="files_protect"),
            InlineKeyboardButton(f"😶 Hɪᴅᴇ Cᴀᴘ: {tick(hide_cap)}", callback_data="files_hidecap"),
        ],
        [InlineKeyboardButton(f"🔘 Cʜɴʟ Bᴛɴ: {tick(chnl_btn)}", callback_data="files_chnlbtn")],
    ]
    if chnl_btn:
        rows.append([
            InlineKeyboardButton(
                f"Pʟᴀᴄᴇ: {mode_label}",
                callback_data="files_chnlmode"
            ),
        ])
        rows.append([
            InlineKeyboardButton("✏️ Sᴇᴛ Tɪᴛʟᴇ", callback_data="files_chnl_title"),
            InlineKeyboardButton("🔗 Sᴇᴛ Lɪɴᴋ", callback_data="files_chnl_link"),
        ])
    rows.append([InlineKeyboardButton("◁ Bᴀᴄᴋ", callback_data="cfg_back")])
    return text, InlineKeyboardMarkup(rows)


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
        + "\n<i>Usᴇ /fsub_mode ᴛᴏ ᴛᴏɢɢʟᴇ ᴍᴏᴅᴇ ᴘᴇʀ ᴄʜᴀɴɴᴇʟ.</i>"
    )
    return text, InlineKeyboardMarkup([[InlineKeyboardButton("◁ Bᴀᴄᴋ", callback_data="cfg_back")]])


# ─────────────────────────────────────────────
# 7. VERIFY SETTINGS
# ─────────────────────────────────────────────

async def verify_text_markup():
    cfg = await db.get_settings()
    verify_on = cfg.get("verify_enabled", False)
    text = (
        "<b>💰 Vᴇʀɪꜰʏ Sᴇᴛᴛɪɴɢs</b>\n\n"
        f"<blockquote>◈ Vᴇʀɪꜰɪᴄᴀᴛɪᴏɴ: {'Eɴᴀʙʟᴇᴅ ✅' if verify_on else 'Dɪsᴀʙʟᴇᴅ ❌'}</blockquote>\n\n"
        "<i>Wʜᴇɴ ᴇɴᴀʙʟᴇᴅ, ᴜsᴇʀs ᴍᴜsᴛ ᴄᴏᴍᴘʟᴇᴛᴇ ᴀ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ sᴛᴇᴘ ʙᴇꜰᴏʀᴇ ᴀᴄᴄᴇssɪɴɢ ꜰɪʟᴇs.</i>"
    )
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Vᴇʀɪꜰɪᴄᴀᴛɪᴏɴ: {tick(verify_on)}", callback_data="verify_toggle")],
        [InlineKeyboardButton("◁ Bᴀᴄᴋ", callback_data="cfg_back")],
    ])
    return text, markup


# ─────────────────────────────────────────────
# 8. CAPTION SETTINGS  (Template Mode)
# ─────────────────────────────────────────────

CAPTION_VARIABLES = (
    "<blockquote expandable>"
    "<b>📝 Aᴠᴀɪʟᴀʙʟᴇ Vᴀʀɪᴀʙʟᴇs:</b>\n"
    "<code>{caption}</code>  — Oʀɪɢɪɴᴀʟ ꜰɪʟᴇ ᴄᴀᴘᴛɪᴏɴ\n"
    "<code>{title}</code>    — Sʜᴏᴡ / ꜰɪʟᴇ ᴛɪᴛʟᴇ\n"
    "<code>{episode}</code>  — Eᴘɪsᴏᴅᴇ ɴᴜᴍʙᴇʀ\n"
    "<code>{season}</code>   — Sᴇᴀsᴏɴ ɴᴜᴍʙᴇʀ\n"
    "<code>{quality}</code>  — Qᴜᴀʟɪᴛʏ (480ᴘ/720ᴘ…)\n"
    "<code>{language}</code> — Lᴀɴɢᴜᴀɢᴇ\n"
    "<code>{audio}</code>    — Aᴜᴅɪᴏ ᴛʏᴘᴇ\n"
    "<code>{size}</code>     — Fɪʟᴇ sɪᴢᴇ\n"
    "<i>ᴠᴀʀɪᴀʙʟᴇs ᴀʀᴇ ᴀᴜᴛᴏ-ᴅᴇᴛᴇᴄᴛᴇᴅ ꜰʀᴏᴍ ꜰɪʟᴇ ɴᴀᴍᴇ / ᴄᴀᴘᴛɪᴏɴ</i>"
    "</blockquote>"
)

async def caption_text_markup():
    cfg = await db.get_settings()
    cap_on   = cfg.get("custom_caption", True)
    tmpl_on  = cfg.get("caption_template_enabled", False)
    template = cfg.get("caption_template", "")
    tmpl_preview = (
        f"\n\n<blockquote>📄 <b>Cᴜʀʀᴇɴᴛ Tᴇᴍᴘʟᴀᴛᴇ:</b>\n<code>{template}</code></blockquote>"
        if template
        else "\n\n<blockquote>📄 Tᴇᴍᴘʟᴀᴛᴇ ɴᴏᴛ sᴇᴛ</blockquote>"
    )
    text = (
        "<b>✍️ Cᴀᴘᴛɪᴏɴ Sᴇᴛᴛɪɴɢs</b>\n\n"
        "<blockquote>"
        f"◈ Cᴜsᴛᴏᴍ Cᴀᴘᴛɪᴏɴ  : {'Eɴᴀʙʟᴇᴅ ✅' if cap_on else 'Dɪsᴀʙʟᴇᴅ ❌'}\n"
        f"◈ Tᴇᴍᴘʟᴀᴛᴇ Mᴏᴅᴇ : {'Eɴᴀʙʟᴇᴅ ✅' if tmpl_on else 'Dɪsᴀʙʟᴇᴅ ❌'}"
        "</blockquote>"
        f"{tmpl_preview}\n\n"
        + CAPTION_VARIABLES
        + "\n\n<i>⚠️ Tᴇᴍᴘʟᴀᴛᴇ Mᴏᴅᴇ ᴏᴠᴇʀʀɪᴅᴇs Cᴜsᴛᴏᴍ Cᴀᴘᴛɪᴏɴ.\n"
        "Usᴇ /setcaption ᴏʀ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ.</i>"
    )
    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"Cᴜsᴛᴏᴍ Cᴀᴘ: {tick(cap_on)}", callback_data="caption_toggle"),
            InlineKeyboardButton(f"Tᴇᴍᴘʟᴀᴛᴇ: {tick(tmpl_on)}", callback_data="caption_tmpl_toggle"),
        ],
        [InlineKeyboardButton("📝 Sᴇᴛ Tᴇᴍᴘʟᴀᴛᴇ", callback_data="caption_set_tmpl")],
        [InlineKeyboardButton("🗑 Cʟᴇᴀʀ Tᴇᴍᴘʟᴀᴛᴇ", callback_data="caption_clear_tmpl")],
        [InlineKeyboardButton("◁ Bᴀᴄᴋ", callback_data="cfg_back")],
    ])
    return text, markup


# ─────────────────────────────────────────────
# INPUT RECEIVER (template / chnl link / chnl title)
# group=10 keeps it low priority so commands run first
# ─────────────────────────────────────────────

@Bot.on_message(filters.private & filters.text, group=10)
async def awaiting_input_receiver(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip() if message.text else ""

    if text.startswith("/"):
        return

    # ── Caption template ──
    if user_id in _awaiting_template:
        _awaiting_template.discard(user_id)
        clear_awaiting(user_id)
        if not text:
            await message.reply("<b>❌ Empty template. Aborted.</b>")
            return
        await db.update_setting("caption_template", text)
        await db.update_setting("caption_template_enabled", True)
        await message.reply(
            "<b>✅ Tᴇᴍᴘʟᴀᴛᴇ sᴀᴠᴇᴅ ᴀɴᴅ ᴇɴᴀʙʟᴇᴅ!</b>\n\n"
            f"<blockquote><code>{text}</code></blockquote>",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⚙️ Cᴀᴘᴛɪᴏɴ Sᴇᴛᴛɪɴɢs", callback_data="cfg_caption")
            ]])
        )
        return

    # ── Channel button link ──
    if user_id in _awaiting_chnl_link:
        _awaiting_chnl_link.discard(user_id)
        clear_awaiting(user_id)
        if not text.startswith("http"):
            await message.reply("<b>❌ Invalid link. Must start with https://</b>")
            return
        await db.update_setting("channel_button_link", text)
        await message.reply(
            f"<b>✅ Cʜᴀɴɴᴇʟ ʙᴜᴛᴛᴏɴ ʟɪɴᴋ sᴀᴠᴇᴅ!</b>\n<code>{text}</code>",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⚙️ Fɪʟᴇs Sᴇᴛᴛɪɴɢs", callback_data="cfg_files")
            ]])
        )
        return

    # ── Channel button title ──
    if user_id in _awaiting_chnl_title:
        _awaiting_chnl_title.discard(user_id)
        clear_awaiting(user_id)
        if not text:
            await message.reply("<b>❌ Empty title. Aborted.</b>")
            return
        await db.update_setting("channel_button_title", text)
        await message.reply(
            f"<b>✅ Cʜᴀɴɴᴇʟ ʙᴜᴛᴛᴏɴ ᴛɪᴛʟᴇ sᴀᴠᴇᴅ!</b>\n<code>{text}</code>",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⚙️ Fɪʟᴇs Sᴇᴛᴛɪɴɢs", callback_data="cfg_files")
            ]])
        )
        return


# ─────────────────────────────────────────────
# /setcaption COMMAND
# ─────────────────────────────────────────────

@Bot.on_message(filters.command("setcaption") & filters.private)
async def setcaption_cmd(client: Client, message: Message):
    if not await check_admin_or_owner(message):
        return
    _awaiting_template.add(message.from_user.id)
    mark_awaiting(message.from_user.id)
    await message.reply(
        "<b>✍️ Sᴇɴᴅ ʏᴏᴜʀ ᴄᴀᴘᴛɪᴏɴ ᴛᴇᴍᴘʟᴀᴛᴇ ɴᴏᴡ.</b>\n\n"
        + CAPTION_VARIABLES
        + "\n\n<b>Exᴀᴍᴘʟᴇ:</b>\n"
          "<code>🎬 {title}\n📺 S{season}E{episode}\n"
          "🎞 {quality} | {language}\n📁 {size}\n\n{caption}</code>\n\n"
          "<i>Sᴇɴᴅ /cancel ᴛᴏ ᴀʙᴏʀᴛ.</i>",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ", callback_data="caption_cancel_set")
        ]])
    )

@Bot.on_message(filters.command("cancel") & filters.private)
async def cancel_input(client: Client, message: Message):
    uid = message.from_user.id
    if uid in _awaiting_template or uid in _awaiting_chnl_link or uid in _awaiting_chnl_title:
        _awaiting_template.discard(uid)
        clear_awaiting(uid)
        _awaiting_chnl_link.discard(uid)
        clear_awaiting(uid)
        _awaiting_chnl_title.discard(uid)
        clear_awaiting(uid)
        await message.reply("<b>❌ Cᴀɴᴄᴇʟʟᴇᴅ.</b>")


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

    # Main menu
    if data == "cfg_back":
        await safe_edit(cb, MAIN_TEXT, main_settings_markup())
        await cb.answer()

    # Section routers
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

    # Force sub actions
    elif data.startswith("fsub_del_"):
        cid = int(data.split("fsub_del_")[1])
        await db.rem_channel(cid)
        text, markup = await fsub_text_markup(client)
        await safe_edit(cb, text, markup)
        await cb.answer("✅ Channel removed!")

    elif data.startswith("fsub_mode_"):
        cid = int(data.split("fsub_mode_")[1])
        cur = await db.get_channel_mode(cid)
        await db.set_channel_mode(cid, "off" if cur == "on" else "on")
        text, markup = await fsub_text_markup(client)
        await safe_edit(cb, text, markup)
        await cb.answer(f"Mode → {'OFF' if cur == 'on' else 'ON'}")

    # Auto delete presets
    elif data.startswith("adel_"):
        secs = int(data.split("adel_")[1])
        await db.set_del_timer(secs)
        text, markup = await autodelete_text_markup()
        await safe_edit(cb, text, markup)
        await cb.answer(f"✅ Timer → {secs}s" if secs else "✅ Disabled")

    # ── Files Settings toggles ──
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

    elif data == "files_chnlmode":
        cfg = await db.get_settings()
        cur_mode = cfg.get("channel_button_mode", "each")
        new_mode = "end" if cur_mode == "each" else "each"
        await db.update_setting("channel_button_mode", new_mode)
        text, markup = await files_text_markup()
        await safe_edit(cb, text, markup)
        label = "Dᴇʟᴇᴛᴇ Aʟᴇʀᴛ" if new_mode == "end" else "Eᴀᴄʜ Fɪʟᴇ"
        await cb.answer(f"Mode → {label}")

    elif data == "files_chnl_link":
        _awaiting_chnl_link.add(cb.from_user.id)
        mark_awaiting(cb.from_user.id)
        await safe_edit(
            cb,
            "<b>🔗 Sᴇɴᴅ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ / ɢʀᴏᴜᴘ ʟɪɴᴋ ɴᴏᴡ.</b>\n\n"
            "<i>Example: https://t.me/yourchannel\n\nSᴇɴᴅ /cancel ᴛᴏ ᴀʙᴏʀᴛ.</i>",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ", callback_data="files_cancel_input")]])
        )
        await cb.answer()

    elif data == "files_chnl_title":
        _awaiting_chnl_title.add(cb.from_user.id)
        mark_awaiting(cb.from_user.id)
        await safe_edit(
            cb,
            "<b>✏️ Sᴇɴᴅ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ᴛɪᴛʟᴇ ɴᴏᴡ.</b>\n\n"
            "<i>Example: 📢 Join Our Channel\n\nSᴇɴᴅ /cancel ᴛᴏ ᴀʙᴏʀᴛ.</i>",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ", callback_data="files_cancel_input")]])
        )
        await cb.answer()

    elif data == "files_cancel_input":
        _awaiting_chnl_link.discard(cb.from_user.id)
        clear_awaiting(cb.from_user.id)
        _awaiting_chnl_title.discard(cb.from_user.id)
        clear_awaiting(cb.from_user.id)
        text, markup = await files_text_markup()
        await safe_edit(cb, text, markup)
        await cb.answer("❌ Cancelled")

    # Verify toggle
    elif data == "verify_toggle":
        cfg = await db.get_settings()
        await db.update_setting("verify_enabled", not cfg.get("verify_enabled", False))
        text, markup = await verify_text_markup()
        await safe_edit(cb, text, markup)
        await cb.answer("✅ Verify toggled!")

    # Caption toggles
    elif data == "caption_toggle":
        cfg = await db.get_settings()
        await db.update_setting("custom_caption", not cfg.get("custom_caption", True))
        text, markup = await caption_text_markup()
        await safe_edit(cb, text, markup)
        await cb.answer("✅ Custom Caption toggled!")

    elif data == "caption_tmpl_toggle":
        cfg = await db.get_settings()
        await db.update_setting("caption_template_enabled", not cfg.get("caption_template_enabled", False))
        text, markup = await caption_text_markup()
        await safe_edit(cb, text, markup)
        await cb.answer("✅ Template Mode toggled!")

    elif data == "caption_set_tmpl":
        _awaiting_template.add(cb.from_user.id)
        mark_awaiting(cb.from_user.id)
        await safe_edit(
            cb,
            "<b>✍️ Sᴇɴᴅ ʏᴏᴜʀ ᴄᴀᴘᴛɪᴏɴ ᴛᴇᴍᴘʟᴀᴛᴇ ɴᴏᴡ.</b>\n\n"
            + CAPTION_VARIABLES
            + "\n\n<b>Exᴀᴍᴘʟᴇ:</b>\n"
              "<code>🎬 {title}\n📺 S{season}E{episode}\n"
              "🎞 {quality} | {language}\n📁 {size}\n\n{caption}</code>\n\n"
              "<i>Sᴇɴᴅ /cancel ᴛᴏ ᴀʙᴏʀᴛ.</i>",
            InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cᴀɴᴄᴇʟ", callback_data="caption_cancel_set")]])
        )
        await cb.answer()

    elif data == "caption_clear_tmpl":
        await db.update_setting("caption_template", "")
        await db.update_setting("caption_template_enabled", False)
        text, markup = await caption_text_markup()
        await safe_edit(cb, text, markup)
        await cb.answer("🗑 Template cleared!")

    elif data == "caption_cancel_set":
        _awaiting_template.discard(cb.from_user.id)
        clear_awaiting(cb.from_user.id)
        text, markup = await caption_text_markup()
        await safe_edit(cb, text, markup)
        await cb.answer("❌ Cancelled")


#=====================================================================================##
# Credits:- @VoidXTora
# Maintained by: Mythic_Bots | Support: @MythicBot_Support
#=====================================================================================##
