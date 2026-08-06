"""
=============================================================================
  901 SYSTEM BOT — FULL MIGRATION FROM PREFIX TO SLASH COMMAND
  Library : discord.py (app_commands + Cogs)
  Author      : Migration Assistant
=============================================================================

CHANGE SUMMARY
─────────────────────────────────────────────────────────────────────────────
  BEFORE (Prefix)        →   AFTER (Slash)
  @bot.command()         →   @app_commands.command()  (Inside Cog)
  ctx: commands.Context  →   interaction: discord.Interaction
  ctx.send(...)          →   interaction.response.send_message(...)
  ctx.author             →   interaction.user
  ctx.guild              →   interaction.guild
  commands.Greedy[Member]→   member1, member2, ... (separate parameters)
  aliases=[...]          →   None — alternative names indicated as comments

COMMAND GROUPS (Slash Groups)
─────────────────────────────────────────────────────────────────────────────
  /economy  → balance, daily, coinflip, slot, send, rob, sweetbonanza,
               blackjack, gambler
  /mod      → ban, kick, unban, mute, unmute, clear, clearall,
               giverole, takerole, giveroleall
  /voice    → join, leave, duration, leaderboard, lock, unlock, pull
  /admin    → whitelist, whitelistlist, addmoney, removemoney
  Single    → /rank, /stats, /profile, /owner, /help, /adminmenu
=============================================================================
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import asyncio
import sys
import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Button, View
import re
import time
import asyncio
import random
import json
import os
import datetime
from datetime import datetime, timedelta, timezone, time as dt_time
import aiohttp
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# For error-free printing of emoji/unicode characters in Windows console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ─────────────────────────────────────────────────────────────────────────────
# SETTINGS (original constant values preserved)
# ─────────────────────────────────────────────────────────────────────────────
# Your bot's token value obtained from Discord Developer Portal. Must be written in quotes.
TOKEN = 'ENTER_BOT_TOKEN_HERE'

# Write the NAMES of the relevant channels in the variables below (e.g., 'general-chat').
LOG_KANAL_ADI = 'log-channel-name'
HOSGELDIN_KANAL_ADI = 'welcome-channel-name'
DUYURU_KANAL_ADI = 'announcement-channel-name'  # Name of the announcement channel where the welcome tag will be sent
HOSGELDIN_ETIKET_KANAL_ADI = 'announcement-channel-name'  # Channel where the user will be tagged upon entry (deleted after 4 sec)
SES_SIRALAMA_KANAL_ADI   = 'voice-leaderboard-channel-name'    # Channel where the daily voice leaderboard will be sent
LIDERLIK_KANAL_ADI       = 'leaderboard-channel-name'      # Channel where the top 3 leaderboard will be sent
MUTE_LOG_KANAL_ADI       = 'mute-log-channel-name'         # Channel where mute/deafen logs will be sent

# ─────────────────────────────────────────────────────────────────────────────
# UI & EMBED UTILS
# ─────────────────────────────────────────────────────────────────────────────
class BotUI:
    COLOR_SUCCESS = 0x2ecc71
    COLOR_ERROR   = 0xe74c3c
    COLOR_INFO    = 0x3498db
    COLOR_WARN    = 0xf1c40f
    COLOR_PREMIUM = 0x2b2d31

    @staticmethod
    def embed(title: str = None, desc: str = None, color: int = COLOR_PREMIUM, user: discord.User = None) -> discord.Embed:
        e = discord.Embed(color=color)
        if title: e.title = title
        if desc: e.description = desc
        if user:
            e.set_footer(text=f"Requested by: {user.display_name}", icon_url=user.display_avatar.url)
        else:
            e.set_footer(text="Z 3 İ T T System")
        e.timestamp = discord.utils.utcnow()
        return e

    @staticmethod
    def success(text: str) -> str: return f"> ✅ **Success:** {text}"
    
    @staticmethod
    def error(text: str) -> str: return f"> ❌ **Error:** {text}"
    
    @staticmethod
    def info(text: str) -> str: return f"> ℹ️ **Info:** {text}"
    
    @staticmethod
    def warn(text: str) -> str: return f"> ⚠️ **Warning:** {text}"
DAVET_TAKIP_KANAL_ADI   = 'invite-tracker-channel-name'      # Channel where invite tracking logs will be sent
OTO_ROL_ADI = 'auto-role-name'  # NAME of the role to be given automatically to new members

# Enter the NUMERICAL ID values copied from Discord without quotes in the fields below.
# (Developer mode must be on, you can right-click the user/channel and say "Copy ID")
OZEL_SAHIP_ID = 0  # The user ID of the special owner of the bot
BOT_KANAL_ID = 0   # The ID of the 1st channel where bot commands can be used
BOT_KANAL_ID2 = 0  # The ID of the 2nd channel where bot commands can be used
MUAF_KANAL_IDLERI = []  # Channel IDs to be exempt from spam/ad protection (e.g., [12345, 67890])

REKLAM_UZANTILARI = ["discord.gg/", "discord.com/", ".gg", ".gg/"]
KOMUT_ISARETLERI = ("/", "e!", "s?")

# You can add levels in the form of "Level": "Role Name" to set level roles.
LEVEL_ROLLER = {"5": "level-5-role-name"}

# Auto Moderation and Limit Settings
SPAM_LIMIT = 10
SPAM_ZAMANI = 5
SUSTURMA_SURESI = 10
BAN_LIMIT_SAYISI = 3
BAN_LIMIT_SURESI = 15
KICK_LIMIT_SAYISI = 3
KICK_LIMIT_SURESI = 15
ZAMAN_ASIMI = 60

# Temporary Voice Room (Private VC) Settings
CREATE_VC_ID = 0    # ID of the main voice channel that will trigger the creation of rooms (e.g., "Create Room" channel)
# ID of the category where rooms will be opened
CATEGORY_ID = 0     # ID of the category where temporary voice channels will be created
PANEL_CHANNEL_ID = 0 # Channel ID to be used for a special system such as a control panel
LIMITLER = {
    "Üye Yasaklama (Ban)": 5,
    "Üye Atma (Kick)": 5,
    "Kanal Silme": 3,
    "Kanal Oluşturma": 3,
    "Rol Silme": 5,
    "Webhook Oluşturma": 1,
}
# ─── Protected Categories ─────────────────────────────────────────────────────
# Channels in these categories are NOT AFFECTED by the /mod unlock all command.
# Add the ID of the log/management category in your server here.
KORUNAN_KATEGORI_IDLERI = [
    # Example: 1234567890123456789,
    # You can add multiple categories by separating them with commas.
]

# ─────────────────────────────────────────────────────────────────────────────
# RUNTIME STATE (original variables preserved)
# ─────────────────────────────────────────────────────────────────────────────
spam_takip = {}
spam_ceza_takip = {}
ceza_kilidi = {}
ban_takip = {}
kick_takip = {}
kullanici_takip = {}
ses_giris_takip = {}
yayin_giris_takip = {}
TEMP_ROOMS = {}
gecici_odalar = {}  # Channel ID : Creator ID
silme_gorevleri = {}  # Channel ID : Timer Task
ses_data_cache = {}
aktif_cekilisler: dict[int, dict] = {}
BEYAZ_LISTE = []

# ─────────────────────────────────────────────────────────────────────────────
# FILE HELPERS (business logic not changed)
# ─────────────────────────────────────────────────────────────────────────────
BEYAZ_LISTE_FILE = "beyazliste.json"
DAVET_FILE       = "davetler.json"
YEDEK_FILE       = "yedekler.json"
SES_FILE = "ses_verisi.json"
LEVEL_FILE = "levels.json"
ECONOMY_FILE = "economy.json"
SIRALAMA_FILE = "siralama_verileri.json"

levels = {}
economy = {}
siralama_verileri = {
    "mesajlar": {},
    "yayin": {},
    "mesaj_ids": {}
}


def load_white_list():
    global BEYAZ_LISTE
    if os.path.exists(BEYAZ_LISTE_FILE):
        with open(BEYAZ_LISTE_FILE, "r") as f:
            try:
                BEYAZ_LISTE = json.load(f).get("ids", [])
            except:
                BEYAZ_LISTE = []
    else:
        BEYAZ_LISTE = []


def save_white_list():
    with open(BEYAZ_LISTE_FILE, "w") as f:
        json.dump({"ids": BEYAZ_LISTE}, f, indent=4)


# ── Invite Tracking ───────────────────────────────────────────────────────────────
invite_cache: dict[int, dict[str, discord.Invite]] = {}  # guild_id -> {code: invite}

def load_davet():
    if os.path.exists(DAVET_FILE):
        with open(DAVET_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_davet(data):
    with open(DAVET_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_yedek():
    if os.path.exists(YEDEK_FILE):
        with open(YEDEK_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_yedek(data):
    with open(YEDEK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_ses():
    if os.path.exists(SES_FILE):
        with open(SES_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}


def save_ses(data):
    with open(SES_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_siralama():
    global siralama_verileri
    if os.path.exists(SIRALAMA_FILE):
        with open(SIRALAMA_FILE, "r", encoding="utf-8") as f:
            try:
                siralama_verileri = json.load(f)
                if "mesaj_ids" not in siralama_verileri:
                    siralama_verileri["mesaj_ids"] = {}
            except:
                pass


def save_siralama():
    with open(SIRALAMA_FILE, "w", encoding="utf-8") as f:
        json.dump(siralama_verileri, f, indent=4, ensure_ascii=False)


def load_levels():
    global levels
    if os.path.exists(LEVEL_FILE):
        with open(LEVEL_FILE, "r") as f:
            try:
                levels = json.load(f)
            except:
                levels = {}
    else:
        levels = {}


def save_levels():
    with open(LEVEL_FILE, "w") as f:
        json.dump(levels, f, indent=4)


def load_economy():
    global economy
    if os.path.exists(ECONOMY_FILE):
        with open(ECONOMY_FILE, "r") as f:
            try:
                economy = json.load(f)
            except:
                economy = {}
    else:
        economy = {}


def save_economy():
    with open(ECONOMY_FILE, "w") as f:
        json.dump(economy, f, indent=4)


def check_user(u_id):
    if u_id not in economy:
        economy[u_id] = {"balance": 100, "last_daily": None}


def sure_formatla(saniye):
    h, r = divmod(int(saniye), 3600)
    m, s = divmod(r, 60)
    parcalar = []
    if h:
        parcalar.append(f"{h} hours")
    if m:
        parcalar.append(f"{m} minutes")
    if s or not parcalar:
        parcalar.append(f"{s} seconds")
    return " ".join(parcalar)
# --- PERMISSION CHECK FUNCTION ---


async def check_permissions(interaction: discord.Interaction, channel_id):
    user = interaction.user
    guild = interaction.guild

    target_channel = guild.get_channel(channel_id)
    if not target_channel or not target_channel.category or target_channel.category.id != CATEGORY_ID:
        return False, "❌ This channel is not in the private room category."

    if channel_id in TEMP_ROOMS and TEMP_ROOMS[channel_id] == user.id:
        return True, None

    if user.guild_permissions.administrator or user == guild.owner:
        if user.voice and user.voice.channel and user.voice.channel.id == channel_id:
            return True, None
        return False, "❌ You must be in the voice channel of this room to manage it. (Admin Permission)"

    return False, "❌ This room does not belong to you."


# --- MODAL CLASSES ---
class RoomNameModal(discord.ui.Modal, title="Update Room Name"):
    name_input = discord.ui.TextInput(
        label="New Room Name", placeholder="e.g. Chat Room", max_length=50, required=True)

    def __init__(self, kanal_id):
        super().__init__()
        self.kanal_id = kanal_id

    async def on_submit(self, interaction: discord.Interaction):
        permitted, reason = await check_permissions(interaction, self.kanal_id)
        if not permitted:
            return await interaction.response.send_message(reason, ephemeral=True)

        kanal = interaction.guild.get_channel(self.kanal_id)
        if not kanal:
            return await interaction.response.send_message("❌ Channel not found.", ephemeral=True)

        await kanal.edit(name=self.name_input.value)
        await interaction.response.send_message(f"✅ Name updated to **{self.name_input.value}**.", ephemeral=True)


class RoomLimitModal(discord.ui.Modal, title="Update Room Limit"):
    limit_input = discord.ui.TextInput(
        label="Number of People (0-99)", placeholder="e.g. 10 (0 for Unlimited)", max_length=2, required=True)

    def __init__(self, kanal_id):
        super().__init__()
        self.kanal_id = kanal_id

    async def on_submit(self, interaction: discord.Interaction):
        permitted, reason = await check_permissions(interaction, self.kanal_id)
        if not permitted:
            return await interaction.response.send_message(reason, ephemeral=True)

        kanal = interaction.guild.get_channel(self.kanal_id)
        if not kanal:
            return await interaction.response.send_message("❌ Channel not found.", ephemeral=True)

        try:
            l = int(self.limit_input.value)
            if not (0 <= l <= 99):
                raise ValueError
            await kanal.edit(user_limit=l)
            await interaction.response.send_message(
                f"✅ Room limit updated to **{l if l > 0 else 'Unlimited'}**.", ephemeral=True
            )
        except ValueError:
            await interaction.response.send_message("❌ Please enter a number between 0 and 99.", ephemeral=True)


# --- USER SELECT VIEW CLASSES ---
class UserSelectView(discord.ui.View):
    def __init__(self, kanal_id, action):
        super().__init__(timeout=60)
        self.kanal_id = kanal_id
        self.action = action

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="Select a user...")
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        permitted, reason = await check_permissions(interaction, self.kanal_id)
        if not permitted:
            return await interaction.response.send_message(reason, ephemeral=True)

        selected_user = select.values[0]
        if selected_user.bot:
            return await interaction.response.send_message("❌ You cannot perform operations on bots.", ephemeral=True)

        kanal = interaction.guild.get_channel(self.kanal_id)
        if not kanal:
            return await interaction.response.send_message("❌ Channel not found.", ephemeral=True)

        owner_id = TEMP_ROOMS.get(self.kanal_id)

        if self.action == "add":
            await kanal.set_permissions(selected_user, connect=True, view_channel=True)
            await interaction.response.send_message(f"✅ Granted entry permission to {selected_user.mention}.", ephemeral=True)

        elif self.action == "kick":
            if owner_id and selected_user.id == owner_id:
                return await interaction.response.send_message(
                    "❌ You cannot ban the room owner. Transfer ownership first.", ephemeral=True
                )
            await kanal.set_permissions(selected_user, connect=False, view_channel=True)
            if selected_user in kanal.members:
                await selected_user.move_to(None)
            await interaction.response.send_message(f"✅ {selected_user.mention} was banned from the room.", ephemeral=True)

        elif self.action == "transfer":
            if owner_id and selected_user.id == owner_id:
                return await interaction.response.send_message("❌ Ownership is already with this user.", ephemeral=True)

            # Reset old owner's permissions
            eski_sahip = interaction.guild.get_member(owner_id)
            if eski_sahip:
                await kanal.set_permissions(eski_sahip, overwrite=None)

            TEMP_ROOMS[self.kanal_id] = selected_user.id
            await kanal.set_permissions(
                selected_user,
                connect=True,
                view_channel=True,
                manage_channels=True,
                mute_members=True,      # ← NEW
                deafen_members=True     # ← NEW
            )
            await interaction.response.send_message(
                f"👑 Room ownership successfully transferred to {selected_user.mention}.", ephemeral=True
            )


# --- MAIN PANEL VIEW CLASS ---
class RoomPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def get_interacted_room(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator or interaction.user == interaction.guild.owner:
            if (interaction.user.voice and interaction.user.voice.channel
                    and interaction.user.voice.channel.id in TEMP_ROOMS):
                return interaction.user.voice.channel.id

        for r_id, o_id in TEMP_ROOMS.items():
            if o_id == interaction.user.id:
                return r_id
        return None

    @discord.ui.button(label="Hide & Lock", emoji="💀", style=discord.ButtonStyle.danger, custom_id="btn_skull", row=0)
    async def btn_skull(self, interaction: discord.Interaction, button: discord.ui.Button):
        r_id = self.get_interacted_room(interaction)
        if not r_id:
            return await interaction.response.send_message(
                "❌ No active room found where you have permission. (Admin Permission: Must be in the room)", ephemeral=True
            )
        kanal = interaction.guild.get_channel(r_id)
        default_perm = kanal.overwrites_for(interaction.guild.default_role)
        view_state = False if default_perm.view_channel is True else True
        connect_state = False if default_perm.connect is True else True
        await kanal.set_permissions(interaction.guild.default_role, view_channel=view_state, connect=connect_state)
        await interaction.response.send_message(
            "👁️🔒 Room is both hidden and locked." if not view_state else "👁️🔓 Room is both visible and unlocked.",
            ephemeral=True
        )

    @discord.ui.button(label="Change Name", emoji="✏️", style=discord.ButtonStyle.primary, custom_id="btn_edit", row=0)
    async def btn_edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        r_id = self.get_interacted_room(interaction)
        if not r_id:
            return await interaction.response.send_message("❌ No active room found where you have permission.", ephemeral=True)
        await interaction.response.send_modal(RoomNameModal(r_id))

    @discord.ui.button(label="Update Limit", emoji="⬆️", style=discord.ButtonStyle.primary, custom_id="btn_limit", row=0)
    async def btn_limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        r_id = self.get_interacted_room(interaction)
        if not r_id:
            return await interaction.response.send_message("❌ No active room found where you have permission.", ephemeral=True)
        await interaction.response.send_modal(RoomLimitModal(r_id))

    @discord.ui.button(label="Lock", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="btn_lock", row=1)
    async def btn_lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        r_id = self.get_interacted_room(interaction)
        if not r_id:
            return await interaction.response.send_message("❌ No active room found where you have permission.", ephemeral=True)
        kanal = interaction.guild.get_channel(r_id)
        current_connect = kanal.overwrites_for(
            interaction.guild.default_role).connect
        new_state = False if current_connect is True else True
        await kanal.set_permissions(interaction.guild.default_role, connect=new_state)
        await interaction.response.send_message(
            "🔓 Room is unlocked to the outside." if new_state else "🔒 Room is locked to the outside.", ephemeral=True
        )

    @discord.ui.button(label="Permit", emoji="👥", style=discord.ButtonStyle.success, custom_id="btn_add", row=1)
    async def btn_add(self, interaction: discord.Interaction, button: discord.ui.Button):
        r_id = self.get_interacted_room(interaction)
        if not r_id:
            return await interaction.response.send_message("❌ No active room found where you have permission.", ephemeral=True)
        await interaction.response.send_message("Select the user to grant entry permission:", view=UserSelectView(r_id, "add"), ephemeral=True)

    @discord.ui.button(label="Ban", emoji="🚫", style=discord.ButtonStyle.danger, custom_id="btn_kick", row=1)
    async def btn_kick(self, interaction: discord.Interaction, button: discord.ui.Button):
        r_id = self.get_interacted_room(interaction)
        if not r_id:
            return await interaction.response.send_message("❌ No active room found where you have permission.", ephemeral=True)
        await interaction.response.send_message("Select the user you want to ban:", view=UserSelectView(r_id, "kick"), ephemeral=True)

    @discord.ui.button(label="Make Invisible", emoji="👁️", style=discord.ButtonStyle.secondary, custom_id="btn_hide", row=2)
    async def btn_hide(self, interaction: discord.Interaction, button: discord.ui.Button):
        r_id = self.get_interacted_room(interaction)
        if not r_id:
            return await interaction.response.send_message("❌ No active room found where you have permission.", ephemeral=True)
        kanal = interaction.guild.get_channel(r_id)
        current_view = kanal.overwrites_for(
            interaction.guild.default_role).view_channel
        new_state = False if current_view is True else True
        await kanal.set_permissions(interaction.guild.default_role, view_channel=new_state)
        await interaction.response.send_message(
            "👁️ Room made visible." if new_state else "🙈 Room made invisible.", ephemeral=True
        )

    @discord.ui.button(label="Transfer", emoji="👑", style=discord.ButtonStyle.primary, custom_id="btn_crown", row=2)
    async def btn_crown(self, interaction: discord.Interaction, button: discord.ui.Button):
        r_id = self.get_interacted_room(interaction)
        if not r_id:
            return await interaction.response.send_message("❌ No active room found where you have permission.", ephemeral=True)

        if TEMP_ROOMS.get(r_id) != interaction.user.id:
            return await interaction.response.send_message(
                "❌ Only the actual owner can transfer the room ownership to someone else.", ephemeral=True
            )
        await interaction.response.send_message(
            "Select the user you want to transfer the room ownership to:",
            view=UserSelectView(r_id, "transfer"),
            ephemeral=True
        )

    @discord.ui.button(label="Delete Room", emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="btn_delete", row=2)
    async def btn_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        r_id = self.get_interacted_room(interaction)
        if not r_id:
            return await interaction.response.send_message("❌ No active room found where you have permission.", ephemeral=True)

        kanal = interaction.guild.get_channel(r_id)
        if kanal:
            TEMP_ROOMS.pop(r_id, None)
            await interaction.response.send_message("🗑️ Your room was successfully deleted.", ephemeral=True)
            await kanal.delete()


# ─────────────────────────────────────────────────────────────────────────────
# BOT + INTENTS
# ─────────────────────────────────────────────────────────────────────────────
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())

# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS  (business logic not changed)
# ─────────────────────────────────────────────────────────────────────────────


async def send_log(guild, message=None, color=discord.Color.blue(), embed=None):
    log_channel = discord.utils.get(guild.text_channels, name=LOG_KANAL_ADI)
    if not log_channel:
        return
    if embed:
        await log_channel.send(embed=embed)
    elif message:
        new_embed = BotUI.embed(
            title="System Log",
            desc=message, 
            color=color.value if isinstance(color, discord.Color) else color
        )
        await log_channel.send(embed=new_embed)


async def koruma_kontrol(guild, user, islem_tipi):
    if user.id in (guild.owner_id, bot.user.id) or user.id in BEYAZ_LISTE:
        return
    simdi = discord.utils.utcnow()
    user_key = f"{user.id}_{islem_tipi}"
    kullanici_takip.setdefault(user_key, [])
    kullanici_takip[user_key] = [
        t for t in kullanici_takip[user_key]
        if t > simdi - timedelta(seconds=ZAMAN_ASIMI)
    ]
    kullanici_takip[user_key].append(simdi)
    limit = LIMITLER.get(islem_tipi, 3)
    if len(kullanici_takip[user_key]) > limit:
        try:
            await guild.ban(user, reason=f"Anti-Nuke: {islem_tipi} limit exceeded! @here")
            await send_log(guild, f"🚨 **ATTACK PREVENTED:** {user.mention} ({user.id}) was banned from the server for exceeding the **{islem_tipi}** limit! @here", discord.Color.red())
        except:
            try:
                await user.edit(roles=[r for r in user.roles if r.is_default()])
                await send_log(guild, f"⚠️ **PERMISSION REVOKED:** {user.mention} could not be banned, but all their permissions were revoked. @here", discord.Color.orange())
            except:
                await send_log(guild, f"❌ **CRITICAL:** {user.mention} cannot be stopped! Insufficient permission! @here", discord.Color.dark_red())
# ─────────────────────────────────────────────────────────────────────────────
# STATUS LOOP (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

durum_index = 0

@tasks.loop(seconds=15)
async def durum_dongusu():
    global durum_index
    durumlar = [
            "made by z3itt 🔥",
            "z3itt ♡ Github 😆",
            "@z3itt 😁"
            ]
    await bot.change_presence(
        activity=discord.Streaming(
            name=durumlar[durum_index % len(durumlar)],
            url="https://www.twitch.tv/901sistem"
        )
    )
    durum_index += 1

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            BotUI.warn(f"Wait **{error.retry_after:.1f} seconds** to use this command again!"),
            ephemeral=True
        )
    elif isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            BotUI.error("You don't have permission to use this command!"), ephemeral=True
        )
    elif isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            BotUI.error("You don't have permission to use this command!"), ephemeral=True
        )
    else:
        print(f"Command error [{interaction.command}]: {error}")
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(BotUI.error("An unexpected error occurred!"), ephemeral=True)
            else:
                await interaction.followup.send(BotUI.error("An unexpected error occurred!"), ephemeral=True)
        except:
            pass
# ─────────────────────────────────────────────────────────────────────────────
# ON_READY — SYNC COMMAND TREE
# ─────────────────────────────────────────────────────────────────────────────


@bot.event
async def on_ready():
    """
    SYNC NOTE:
      • Global sync → all servers (changes delayed by ~1 hour)
      • Guild sync  → only test server (instant)

      For testing, replace GUILD_ID with your own server's, then
      remove the guild parameter when going live (global sync).
    """
    load_levels()
    load_economy()
    load_white_list()
    load_giveaways()
    load_siralama()
    bot.add_view(GiveawayView())  # Keep buttons alive on bot restart
    if not giveaway_kontrol.is_running():
        giveaway_kontrol.start()
    bot.add_view(RoomPanelView())

    # ── SLASH COMMAND SYNC ────────────────────────────────────────────────
    try:
        # GLOBAL SYNC (live environment)
        synced = await bot.tree.sync()

        # GUILD SYNC (test — instant):
        # TEST_GUILD = discord.Object(id=YourGuildID)
        # synced = await bot.tree.sync(guild=TEST_GUILD)

        print(f"✅ {len(synced)} slash commands synced.")
    except Exception as e:
        print(f"❌ Sync error: {e}")

    if not durum_dongusu.is_running():
        durum_dongusu.start()
    if not gunluk_ses_siralama.is_running():
        gunluk_ses_siralama.start()

    for guild in bot.guilds:
        for vc in guild.voice_channels:
            for member in vc.members:
                if not member.bot:
                    ses_giris_takip[member.id] = time.time()
                    if member.voice and member.voice.self_stream:
                        yayin_giris_takip[member.id] = time.time()

    # Load Invite cache
    for guild in bot.guilds:
        try:
            invites = await guild.invites()
            invite_cache[guild.id] = {inv.code: inv for inv in invites}
        except Exception as e:
            print(f"Could not load invite cache ({guild.name}): {e}")

    print(f"✅ {bot.user.name} is ready! All systems active.")

# ─────────────────────────────────────────────────────────────────────────────
# EVENTS  (unchanged — business logic is the same)
# ─────────────────────────────────────────────────────────────────────────────


@bot.event
async def on_webhooks_update(channel):
    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.webhook_create):
        if entry.user.id not in BEYAZ_LISTE and entry.user.id != channel.guild.owner_id:
            await koruma_kontrol(channel.guild, entry.user, "Webhook Creation")
            webhooks = await channel.webhooks()
            for webhook in webhooks:
                await webhook.delete(reason="Anti-Nuke: Unauthorized Webhook Deleted. @here")
            await send_log(channel.guild, f"⚠️ **Unauthorized Webhook:** Webhook created by {entry.user.mention} has been deleted! @here", discord.Color.red())


@bot.event
async def on_member_ban(guild, user):
    try:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                await koruma_kontrol(guild, entry.user, "Member Ban")
                break
    except:
        pass


@bot.event
async def on_guild_invite_create(invite):
    gid = invite.guild.id
    if gid not in invite_cache:
        invite_cache[gid] = {}
    invite_cache[gid][invite.code] = invite


@bot.event
async def on_guild_invite_delete(invite):
    gid = invite.guild.id
    invite_cache.get(gid, {}).pop(invite.code, None)


@bot.event
async def on_guild_channel_delete(channel):
    guild = channel.guild
    await asyncio.sleep(1)
    try:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            responsible_user = entry.user
            if responsible_user.id in (bot.user.id, guild.owner_id) or responsible_user.id in BEYAZ_LISTE:
                await send_log(guild, f"🗑️ **Channel Deleted:** #{channel.name} | Safe Action", discord.Color.blue())
                return
            await koruma_kontrol(guild, responsible_user, "Channel Deletion")
            await send_log(guild, f"🚫 **Channel Deleted:** #{channel.name} | Responsible: {responsible_user.mention}", discord.Color.red())
            break
    except Exception as e:
        print(f"Error: {e}")


@bot.event
async def on_guild_channel_create(channel):
    guild = channel.guild
    kategori_adi = channel.category.name if channel.category else "Uncategorized"

    try:
        await asyncio.sleep(1)

        sorumlu = None
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
                sorumlu = entry.user
                break
        except Exception as e:
            print(f"[on_guild_channel_create] audit_logs error: {e}")

        if sorumlu is None:
            await send_log(guild, f"🆕 Channel Created: {channel.mention} | Category: **{kategori_adi}**", discord.Color.orange())
            return

        if sorumlu.id in (bot.user.id, guild.owner_id) or sorumlu.id in BEYAZ_LISTE:
            await send_log(guild, f"🆕 Channel Created: {channel.mention} | Category: **{kategori_adi}** | {sorumlu.mention} | Safe Action", discord.Color.orange())
            return

        await koruma_kontrol(guild, sorumlu, "Channel Creation")
        user_key = f"{sorumlu.id}_Channel Creation"
        islem_sayisi = len(kullanici_takip.get(user_key, []))
        if islem_sayisi > 3:
            try:
                await channel.delete(reason="Anti-Nuke: Channel limit exceeded.")
                await send_log(guild, f"🚫 Limit Exceeded: {sorumlu.mention}", discord.Color.red())
            except:
                pass
        else:
            await send_log(guild, f"🆕 Channel Created: {channel.mention} | Category: **{kategori_adi}** | {sorumlu.mention} | {islem_sayisi}/3", discord.Color.orange())

    except Exception as e:
        print(f"[on_guild_channel_create] general error: {e}")
        try:
            await send_log(guild, f"🆕 Channel Created: {channel.mention} | Category: **{kategori_adi}**", discord.Color.orange())
        except Exception:
            pass


async def _kanal_update_sorumlu(guild, channel_id):
    """Finds the user who made the last action on this channel from channel_update audit logs."""
    try:
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_update):
            target_id = entry.target.id if entry.target else None
            if target_id == channel_id:
                return entry.user
    except Exception as e:
        print(f"[on_guild_channel_update] audit_logs error: {e}")
    return None


@bot.event
async def on_guild_channel_update(before, after):
    guild = after.guild
    await asyncio.sleep(1)

    if before.name != after.name:
        sorumlu = await _kanal_update_sorumlu(guild, after.id)
        ek = f" | {sorumlu.mention}" if sorumlu else ""
        await send_log(guild, f"📑 Channel Name Changed: #{before.name} → #{after.name}{ek}", discord.Color.gold())

    if before.category_id != after.category_id:
        once_kategori = before.category.name if before.category else "Uncategorized"
        sonra_kategori = after.category.name if after.category else "Uncategorized"
        sorumlu = await _kanal_update_sorumlu(guild, after.id)
        ek = f" | {sorumlu.mention}" if sorumlu else ""
        await send_log(guild, f"📂 Channel Moved: {after.mention} | **{once_kategori}** → **{sonra_kategori}**{ek}", discord.Color.gold())

    if before.position != after.position and before.category_id == after.category_id:
        sorumlu = await _kanal_update_sorumlu(guild, after.id)
        ek = f" | {sorumlu.mention}" if sorumlu else ""
        await send_log(guild, f"↕️ Channel Order Changed: {after.mention}{ek}", discord.Color.gold())


@bot.event
async def on_guild_update(before, after):
    if before.name != after.name:
        async for entry in after.audit_logs(limit=1, action=discord.AuditLogAction.guild_update):
            await send_log(after, f"🏰 Server Name: {before.name} → {after.name} | {entry.user.mention}", discord.Color.gold())
            break
    if before.icon != after.icon:
        async for entry in after.audit_logs(limit=1, action=discord.AuditLogAction.guild_update):
            await send_log(after, f"🖼️ Server Photo Changed | {entry.user.mention}", discord.Color.purple())
            break

    if before.vanity_url_code != after.vanity_url_code:
        eski_kod = before.vanity_url_code
        yeni_kod = after.vanity_url_code

        sorumlu = None
        async for entry in after.audit_logs(limit=5, action=discord.AuditLogAction.guild_update):
            sorumlu = entry.user
            break

        ek = f" | {sorumlu.mention}" if sorumlu else ""
        uyari = ""
        if sorumlu and sorumlu.id not in (after.owner_id,) and sorumlu.id not in BEYAZ_LISTE:
            uyari = "\n⚠️ **Due to Discord API restrictions, the bot cannot automatically restore the old link. Please restore it manually from server settings.**"

        await send_log(
            after,
            f"🔗 Invite Protection: Custom Invite Link changed! `{eski_kod}` → `{yeni_kod}`{ek}{uyari}",
            discord.Color.red()
        )


@bot.event
async def on_guild_role_create(role):
    async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
        await send_log(role.guild, f"✨ New Role: {role.name} | {entry.user.mention}", discord.Color.green())
        break


@bot.event
async def on_guild_role_delete(role):
    async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        await send_log(role.guild, f"🔥 Role Deleted: {role.name} | {entry.user.mention}", discord.Color.red())
        break


@bot.event
async def on_guild_role_update(before, after):
    guild = after.guild
    if before.permissions != after.permissions:
        kritik_yetkiler = ["administrator",
                           "manage_roles", "manage_guild", "ban_members"]
        added_perms = [p for p, v in after.permissions if v and not dict(
            before.permissions)[p]]
        if any(p in kritik_yetkiler for p in added_perms):
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
                sorumlu = entry.user
                sorumlu_member = guild.get_member(sorumlu.id)
                is_whitelisted = sorumlu.id in BEYAZ_LISTE
                is_admin = sorumlu_member is not None and sorumlu_member.guild_permissions.administrator
                if not (is_whitelisted or is_admin):
                    try:
                        await after.edit(permissions=before.permissions, reason="Unauthorized permission addition!")
                        await koruma_kontrol(guild, sorumlu, "Role Permission Update")
                        await send_log(guild, f"⚠️ **PERMISSION INCREASE PREVENTED:** {sorumlu.mention} added critical permissions to the `{after.name}` role!", discord.Color.dark_red())
                    except:
                        pass
                break

    # --- ROLE MODIFICATION LOGS ---
    isim_degisti = before.name != after.name
    yetki_degisti = before.permissions != after.permissions

    if isim_degisti or yetki_degisti:
        sorumlu_yetkili = "Unknown"
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
            if entry.target.id == after.id:
                sorumlu_yetkili = entry.user.mention
                break

        log_mesaji = f"🛡️ **Role Updated: {before.name}**\n"
        log_mesaji += f"👤 **Responsible:** {sorumlu_yetkili}\n"

        if isim_degisti:
            log_mesaji += f"📝 **Name Change:** `{before.name}` ➔ `{after.name}`\n"

        if yetki_degisti:
            log_mesaji += "⚠️ **Permission Changes:**\n"
            old_perms = set(cap for cap, val in before.permissions if val)
            new_perms = set(cap for cap, val in after.permissions if val)
            eklenenler = new_perms - old_perms
            cikarilanlar = old_perms - new_perms
            if eklenenler:
                log_mesaji += f"✅ **Added:** `{', '.join(eklenenler)}`\n"
            if cikarilanlar:
                log_mesaji += f"❌ **Removed:** `{', '.join(cikarilanlar)}`\n"

        try:
            await send_log(guild, message=log_mesaji, color=discord.Color.blue())
        except Exception as e:
            print(f"Log error: {e}")


@bot.event
async def on_member_update(before, after):
    guild = after.guild
    if len(before.roles) < len(after.roles):
        new_role = next(r for r in after.roles if r not in before.roles)
        kritik_yetkiler = ["administrator", "manage_roles",
                           "manage_channels", "ban_members", "kick_members"]
        is_critical = any(dict(new_role.permissions).get(p)
                          for p in kritik_yetkiler)
        if is_critical:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                if entry.target.id == after.id:
                    sorumlu = entry.user
                    sorumlu_member = guild.get_member(sorumlu.id)
                    is_whitelisted = sorumlu.id in BEYAZ_LISTE
                    is_admin = sorumlu_member is not None and sorumlu_member.guild_permissions.administrator
                    if not (is_whitelisted or is_admin):
                        try:
                            await after.remove_roles(new_role, reason="Unauthorized staff role!")
                            await koruma_kontrol(guild, sorumlu, "Giving Staff Role")
                            await send_log(guild, f"🚨 Unauthorized Permission Prevented: {sorumlu.mention} → {after.mention} | {new_role.name}", discord.Color.red())
                            return
                        except:
                            pass
                    break
        if len(after.roles) > 12:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                if entry.target.id == after.id:
                    sorumlu = entry.user
                    sorumlu_member = guild.get_member(sorumlu.id)
                    is_whitelisted = sorumlu.id in BEYAZ_LISTE
                    is_admin = sorumlu_member is not None and sorumlu_member.guild_permissions.administrator
                    if not (is_whitelisted or is_admin):
                        try:
                            await after.remove_roles(new_role, reason="9 Role Limit")
                            lk = discord.utils.get(
                                guild.text_channels, name="log")
                            if lk:
                                await lk.send(f"⚠️ {after.mention} has reached the role limit, `{new_role.name}` was removed.")
                        except:
                            pass
                    break
    if len(before.roles) != len(after.roles):
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
            if entry.target.id == after.id:
                sorumlu = entry.user
                if len(before.roles) < len(after.roles):
                    new_role = next(
                        r for r in after.roles if r not in before.roles)
                    if new_role.name != OTO_ROL_ADI:
                        await send_log(guild, f"👤 {after.mention} → `{new_role.name}` given. | {sorumlu.mention}", discord.Color.green())
                else:
                    removed_role = next(
                        r for r in before.roles if r not in after.roles)
                    await send_log(guild, f"👤 {after.mention} → `{removed_role.name}` removed. | {sorumlu.mention}", discord.Color.red())
                break
    if before.display_name != after.display_name:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
            if entry.target.id == after.id:
                await send_log(guild, f"👤 Name: {before.display_name} → {after.display_name} | {entry.user.mention}", discord.Color.blue())
                break
    if before.timed_out_until != after.timed_out_until:
        yetkili = "Unknown"
        try:
            async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                if entry.target.id == after.id:
                    yetkili = entry.user.mention
                    break
        except:
            pass
        if after.timed_out_until is None:
            embed = discord.Embed(title="🔓 Mute Removed",
                                  description=f"**User:** {after.mention}\n**Staff:** {yetkili}", color=discord.Color.green(), timestamp=discord.utils.utcnow())
            embed.set_thumbnail(url=after.display_avatar.url)
            await send_log(after.guild, embed=embed)
        else:
            simdi_utc = discord.utils.utcnow()
            saniye = (after.timed_out_until - simdi_utc).total_seconds()
            if saniye > 86400:
                sure_metni = f"{round(saniye/86400)} days"
            elif saniye > 3600:
                sure_metni = f"{round(saniye/3600)} hours"
            else:
                sure_metni = f"{round(saniye/60)} minutes"
            embed = discord.Embed(
                title="🚫 Manual Mute", description=f"**User:** {after.mention}\n**Staff:** {yetkili}\n**Duration:** {sure_metni}", color=discord.Color.red(), timestamp=discord.utils.utcnow())
            embed.set_thumbnail(url=after.display_avatar.url)
            await send_log(after.guild, embed=embed)


@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    await send_log(message.guild, f"🗑️ **Message Deleted** | {message.author.mention} | {message.channel.mention} | {message.content}", discord.Color.red())


@bot.event
async def on_message_edit(before, after):
    if before.author.bot or before.content == after.content:
        return
    await send_log(before.guild, f"📝 **Edit** | {before.author.mention} | Old: {before.content} | New: {after.content}", discord.Color.blue())


@bot.event
async def on_member_join(member):
    if member.bot:
        async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
            if entry.target.id == member.id:
                davet_eden = entry.user
                if davet_eden.id not in BEYAZ_LISTE and davet_eden.id != member.guild.owner_id:
                    try:
                        await member.ban(reason=f"Unauthorized bot: {davet_eden.name}")
                        await send_log(member.guild, f"🚫 Unauthorized Bot Prevented: {member.name} | Invited by: {davet_eden.mention}", discord.Color.red())
                        return
                    except Exception as e:
                        print(f"Bot prevention error: {e}")
                break
    guild = member.guild
    h_kanal = discord.utils.get(
        member.guild.text_channels, name=HOSGELDIN_KANAL_ADI)
    if h_kanal:
        embed = discord.Embed(title="📥 Someone New Joined Us!",
                              description=f"🎉 Welcome {member.mention}! We have reached **{guild.member_count}** members.", color=discord.Color.green(), timestamp=discord.utils.utcnow())
        embed.add_field(name="👤 User", value=member.name, inline=True)
        embed.add_field(name="🆔 ID", value=f"`{member.id}`", inline=True)
        embed.add_field(name="🚀 Member Count",
                        value=f"**{guild.member_count}**", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"{guild.name} Management System",
                         icon_url=guild.icon.url if guild.icon else None)
        await h_kanal.send(content=f"🌟 **{member.name}** joined the server! {member.mention}", embed=embed)

    # Ping in specified channel, delete after 4 seconds
    etiket_kanal = discord.utils.get(member.guild.text_channels, name=HOSGELDIN_ETIKET_KANAL_ADI)
    if etiket_kanal:
        try:
            await etiket_kanal.send(
                content=f"👋 Welcome {member.mention}! 🎉",
                delete_after=4
            )
        except Exception:
            pass

    rol = discord.utils.get(member.guild.roles, name=OTO_ROL_ADI)
    if rol:
        try:
            await member.add_roles(rol)
            await send_log(member.guild, f"✅ Auto-Role Given: {member.mention}", discord.Color.green())
        except:
            await send_log(member.guild, f"❌ Could not give `{OTO_ROL_ADI}`!", discord.Color.red())

    # ── Invite Tracking ──────────────────────────────────────────────────────────
    if not member.bot:
        guild = member.guild
        davet_data = load_davet()
        davet_eden_id = None

        try:
            yeni_invites = await guild.invites()
            yeni_cache   = {inv.code: inv for inv in yeni_invites}
            eski_cache   = invite_cache.get(guild.id, {})

            for code, yeni_inv in yeni_cache.items():
                eski_inv = eski_cache.get(code)
                if eski_inv and yeni_inv.uses > eski_inv.uses:
                    davet_eden_id = str(yeni_inv.inviter.id) if yeni_inv.inviter else None
                    break

            # Could be joined with Vanity URL
            if davet_eden_id is None and guild.vanity_url_code:
                try:
                    vanity = await guild.vanity_invite()
                    eski_vanity = eski_cache.get("__vanity__")
                    if eski_vanity is None or vanity.uses > eski_vanity.uses:
                        davet_eden_id = "__vanity__"
                    yeni_cache["__vanity__"] = vanity
                except Exception:
                    pass

            invite_cache[guild.id] = yeni_cache

        except Exception as e:
            print(f"[davet_takip] invite fetch error: {e}")

        if davet_eden_id and davet_eden_id != "__vanity__":
            uid_str = davet_eden_id
            if uid_str not in davet_data:
                davet_data[uid_str] = {"toplam": 0, "getirdikleri": []}
            davet_data[uid_str]["toplam"] += 1
            if str(member.id) not in davet_data[uid_str]["getirdikleri"]:
                davet_data[uid_str]["getirdikleri"].append(str(member.id))
            save_davet(davet_data)

            davet_kanal = discord.utils.get(guild.text_channels, name=DAVET_TAKIP_KANAL_ADI)
            if davet_kanal:
                davet_eden = guild.get_member(int(davet_eden_id))
                davet_eden_mention = davet_eden.mention if davet_eden else f"<@{davet_eden_id}>"
                toplam = davet_data[uid_str]["toplam"]
                await davet_kanal.send(
                    embed=discord.Embed(
                        description=f"📨 {member.mention} joined the server!\n👤 Invited by: {davet_eden_mention} (Total: **{toplam}** invites)",
                        color=discord.Color.green(),
                        timestamp=discord.utils.utcnow()
                    )
                )
        elif davet_eden_id == "__vanity__":
            davet_kanal = discord.utils.get(guild.text_channels, name=DAVET_TAKIP_KANAL_ADI)
            if davet_kanal:
                await davet_kanal.send(
                    embed=discord.Embed(
                        description=f"📨 {member.mention} joined the server using the custom invite link.",
                        color=discord.Color.blurple(),
                        timestamp=discord.utils.utcnow()
                    )
                )


@bot.event
async def on_member_remove(member):
    guild = member.guild
    h_kanal = discord.utils.get(
        member.guild.text_channels, name=HOSGELDIN_KANAL_ADI)
    if h_kanal:
        embed = discord.Embed(title="📤 A Member Left", description=f"{member.mention} has left.\n🆔 `{member.id}`", color=discord.Color.red(
        ), timestamp=discord.utils.utcnow())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"{guild.name} Join-Leave",
                         icon_url=guild.icon.url if guild.icon else None)
        await h_kanal.send(content=f"📤 **{member.name}** said goodbye.", embed=embed)
    await asyncio.sleep(1)
    is_kicked = False
    try:
        async for entry in member.guild.audit_logs(limit=3, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 15:
                is_kicked = True
                await koruma_kontrol(member.guild, entry.user, "Member Kick")
                await send_log(member.guild, f"👢 Kicked: {member.name} | {entry.user.mention}", discord.Color.red())
                break
    except:
        pass
    if not is_kicked:
        await send_log(member.guild, f"📤 Left: {member.name}", discord.Color.orange())


@bot.event
async def on_voice_state_update(member, before, after):
    if not ses_data_cache:
        ses_data_cache.update(load_ses())
    ses_data = ses_data_cache
    uid = str(member.id)
    if uid not in ses_data:
        ses_data[uid] = {"toplam_saniye": 0}

    # ── MUTE / DEAF LOG ─────────────────────────────────────────────────────
    async def mute_log_gonder(mesaj, renk):
        mute_kanal = discord.utils.get(member.guild.text_channels, name=MUTE_LOG_KANAL_ADI)
        if mute_kanal:
            try:
                await mute_kanal.send(embed=discord.Embed(
                    description=mesaj,
                    color=renk,
                    timestamp=discord.utils.utcnow()
                ).set_thumbnail(url=member.display_avatar.url))
            except Exception:
                pass

    # Server mute
    if before.mute != after.mute:
        if after.mute:
            await asyncio.sleep(1)
            sorumlu_mention = ""
            try:
                async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_update):
                    if entry.target.id == member.id:
                        sorumlu_mention = f" | Staff: {entry.user.mention}"
                        break
            except Exception:
                pass
            await mute_log_gonder(f"🔇 **Server Mute:** {member.mention} was muted{sorumlu_mention}", discord.Color.red())
        else:
            await asyncio.sleep(1)
            sorumlu_mention = ""
            try:
                async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_update):
                    if entry.target.id == member.id:
                        sorumlu_mention = f" | Staff: {entry.user.mention}"
                        break
            except Exception:
                pass
            await mute_log_gonder(f"🔊 **Server Mute Removed:** {member.mention}{sorumlu_mention}", discord.Color.green())

    # Server deafen
    if before.deaf != after.deaf:
        if after.deaf:
            await asyncio.sleep(1)
            sorumlu_mention = ""
            try:
                async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_update):
                    if entry.target.id == member.id:
                        sorumlu_mention = f" | Staff: {entry.user.mention}"
                        break
            except Exception:
                pass
            await mute_log_gonder(f"🔕 **Server Deafen:** {member.mention} was deafened{sorumlu_mention}", discord.Color.red())
        else:
            await asyncio.sleep(1)
            sorumlu_mention = ""
            try:
                async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_update):
                    if entry.target.id == member.id:
                        sorumlu_mention = f" | Staff: {entry.user.mention}"
                        break
            except Exception:
                pass
            await mute_log_gonder(f"🔔 **Server Deafen Removed:** {member.mention}{sorumlu_mention}", discord.Color.green())

    # Self mute
    if before.self_mute != after.self_mute:
        if after.self_mute:
            await mute_log_gonder(f"🎙️ **Self Muted:** {member.mention}", discord.Color.orange())
        else:
            await mute_log_gonder(f"🎙️ **Self Mute Removed:** {member.mention}", discord.Color.blue())

    # Self deafen
    if before.self_deaf != after.self_deaf:
        if after.self_deaf:
            await mute_log_gonder(f"🎧 **Self Deafened:** {member.mention}", discord.Color.orange())
        else:
            await mute_log_gonder(f"🎧 **Self Deafen Removed:** {member.mention}", discord.Color.blue())

    # ── STREAM TRACKING ──────────────────────────────────────────────────────
    if not before.self_stream and after.self_stream:
        yayin_giris_takip[member.id] = time.time()
    elif before.self_stream and not after.self_stream:
        if member.id in yayin_giris_takip:
            gecen_sure = int(time.time() - yayin_giris_takip[member.id])
            del yayin_giris_takip[member.id]
            if gecen_sure > 0:
                siralama_verileri.setdefault("yayin", {})
                uid_str = str(member.id)
                siralama_verileri["yayin"][uid_str] = siralama_verileri["yayin"].get(uid_str, 0) + gecen_sure
                save_siralama()

    # ── 1) ENTERED CHANNEL ──────────────────────────────────────────────────
    if before.channel is None and after.channel is not None:
        ses_giris_takip[member.id] = time.time()
        # return NONE — let the room creation code below run

    # ── 2) CHANGED CHANNEL ─────────────────────────────────────────────
    elif before.channel is not None and after.channel is not None:
        # ← IF IT IS THE SAME CHANNEL, DO NOTHING
        if before.channel.id == after.channel.id:
            pass
        else:
            gecen_sure = 0
            if member.id in ses_giris_takip:
                gecen_sure = int(time.time() - ses_giris_takip[member.id])
            ses_giris_takip[member.id] = time.time()
            if gecen_sure > 0:
                ses_data[uid]["toplam_saniye"] += gecen_sure
                save_ses(ses_data)
                await _ses_embed_gonder(member, before.channel.name, after.channel, gecen_sure, ses_data[uid]["toplam_saniye"])
    # ── 3) LEFT CHANNEL ────────────────────────────────────────────────
    elif before.channel is not None and after.channel is None:
        gecen_sure = 0
        if member.id in ses_giris_takip:
            gecen_sure = int(time.time() - ses_giris_takip[member.id])
            del ses_giris_takip[member.id]
        if gecen_sure > 0:
            ses_data[uid]["toplam_saniye"] += gecen_sure
            save_ses(ses_data)
            await _ses_embed_gonder(member, before.channel.name, None, gecen_sure, ses_data[uid]["toplam_saniye"])

    # ── ROOM CREATION ────────────────────────────────────────────────────
    if after.channel and after.channel.id == CREATE_VC_ID:
        guild = member.guild
        kategori = guild.get_channel(CATEGORY_ID)
        if not kategori or not isinstance(kategori, discord.CategoryChannel):
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=True),
            member: discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                manage_channels=True,
                mute_members=True,
                deafen_members=True
            )
        }

        try:
            yeni_kanal = await guild.create_voice_channel(
                name=f"🔊{member.display_name}",
                category=kategori,
                overwrites=overwrites
            )
            await member.move_to(yeni_kanal)
            TEMP_ROOMS[yeni_kanal.id] = member.id
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass

    # ── ROOM DELETION ────────────────────────────────────────────────────────
    if before.channel and before.channel.id in TEMP_ROOMS:
        if len(before.channel.members) == 0:
            try:
                await before.channel.delete()
                TEMP_ROOMS.pop(before.channel.id, None)
            except (discord.Forbidden, discord.HTTPException):
                pass
async def _ses_embed_gonder(member, onceki_kanal_adi, sonraki_kanal, gecen_sure, toplam):
    sessaat_kanali = discord.utils.get(
        member.guild.text_channels, name="ses-saat")
    if not sessaat_kanali:
        return

    if sonraki_kanal is not None:
        baslik = "🔄 Voice Channel Changed"
        alan_adi = "📢 Channel Switch"
        aciklama = f"`{onceki_kanal_adi}` → `{sonraki_kanal.name}`"
    else:
        baslik = "🎙️ Voice Channel Summary"
        alan_adi = "📢 Left Channel"
        aciklama = f"`{onceki_kanal_adi}`"

    embed = discord.Embed(
        title=baslik, color=discord.Color.blurple(), timestamp=discord.utils.utcnow())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="👤 Member",
                    value=member.mention,              inline=True)
    embed.add_field(name=alan_adi,              value=aciklama,
                    inline=True)
    embed.add_field(name="⏱️ Duration This Time",
                    value=f"**{sure_formatla(gecen_sure)}**", inline=True)
    embed.add_field(name="📊 Total Voice Duration",
                    value=f"**{sure_formatla(toplam)}**",    inline=False)
    embed.set_footer(
        text=f"{member.guild.name} Voice System",
        icon_url=member.guild.icon.url if member.guild.icon else None
    )
    await sessaat_kanali.send(embed=embed)


@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return
    if message.channel.id in MUAF_KANAL_IDLERI:
        return

    content = message.content.lower()
    u_id = message.author.id
    simdi = datetime.now()
    spam_tespit = False

    # ── ADVERTISEMENT CHECK ──────────────────────────────────────────────────────
    if not message.author.guild_permissions.administrator:
        if any(reklam in content for reklam in REKLAM_UZANTILARI):
            try:
                await message.delete()
                await message.channel.send(
                    f"⚠️ {message.author.mention}, advertising is forbidden!",
                    delete_after=5
                )
                await send_log(
                    message.guild,
                    f"🚫 Advertisement Blocked: {message.author.mention}",
                    discord.Color.red()
                )
                spam_tespit = True
            except Exception as e:
                print(f"Advertisement deletion error: {e}")

    # ── BOT COMMAND CHANNEL CHECK ─────────────────────────────────────────────
    is_command = any(content.startswith(prefix) for prefix in KOMUT_ISARETLERI)
    if is_command:
        is_admin = message.author.guild_permissions.administrator
        is_whitelisted = u_id in BEYAZ_LISTE
        if not (is_admin or is_whitelisted) and message.channel.id not in [BOT_KANAL_ID, BOT_KANAL_ID2]:
            try:
                await message.delete()
                uyari = await message.channel.send(
                    f"⚠️ {message.author.mention}, you can only use bot commands in the "
                    f"<#{BOT_KANAL_ID}> channel!"
                )
                await asyncio.sleep(5)
                await uyari.delete()
                return
            except Exception as e:
                print(f"Command channel error: {e}")

    # ── LONG MESSAGE CHECK ──────────────────────────────────────────────────
    if not message.author.guild_permissions.administrator:
        if len(message.content) > 500:
            try:
                await message.delete()
                await message.channel.send(
                    f"⚠️ {message.author.mention}, message too long!",
                    delete_after=5
                )
                await send_log(
                    message.guild,
                    f"🚫 Long Message: {message.author.mention}",
                    discord.Color.orange()
                )
                spam_tespit = True
            except Exception as e:
                print(f"Long message deletion error: {e}")

    # ── WORD REPETITION CHECK ───────────────────────────────────────────────
    if not message.author.guild_permissions.administrator:
        kelimeler = message.content.lower().split()
        if len(kelimeler) > 5:
            for kelime in set(kelimeler):
                tekrar = kelimeler.count(kelime)
                if tekrar > 10 or (tekrar / len(kelimeler)) > 0.5:
                    try:
                        await message.delete()
                        await message.channel.send(
                            f"⚠️ {message.author.mention}, word repetition is forbidden!",
                            delete_after=5
                        )
                        await send_log(
                            message.guild,
                            f"🚫 Word Repetition: {message.author.mention} '{kelime}' {tekrar}x",
                            discord.Color.orange()
                        )
                        spam_tespit = True
                    except Exception as e:
                        print(f"Word repetition deletion error: {e}")
                    break

    # ── SPAM COUNTER (fixed with total_seconds()) ──────────────────────────
    spam_takip.setdefault(u_id, [])
    spam_takip[u_id] = [
        t for t in spam_takip[u_id]
        # .seconds → .total_seconds()
        if (simdi - t).total_seconds() < SPAM_ZAMANI
    ]
    spam_takip[u_id].append(simdi)

    # ── SPAM LIMIT CHECK (works independently of spam_tespit) ───────────────
    if not message.author.guild_permissions.administrator:
        if len(spam_takip[u_id]) > SPAM_LIMIT:
            spam_tespit = True
            try:
                await message.channel.purge(
                    limit=SPAM_LIMIT + 1,
                    check=lambda m: m.author == message.author,
                    bulk=True
                )
            except Exception as e:
                print(f"Purge error: {e}")

    # ── PENALTY BLOCK ────────────────────────────────────────────────────────────
    if spam_tespit:
        # Prevent double penalty lock
        if u_id in ceza_kilidi and (simdi - ceza_kilidi[u_id]).total_seconds() < 5:
            return
        ceza_kilidi[u_id] = simdi

        spam_ceza_takip.setdefault(u_id, [])
        spam_ceza_takip[u_id] = [
            t for t in spam_ceza_takip[u_id]
            if (simdi - t).total_seconds() < 86400
        ]
        spam_ceza_takip[u_id].append(simdi)
        ihlal_sayisi = len(spam_ceza_takip[u_id])

        if ihlal_sayisi >= 3:
            # 7-day ban on 3rd violation
            spam_ceza_takip[u_id] = []
            if u_id in spam_takip:
                spam_takip[u_id] = []
            try:
                await message.author.timeout(timedelta(days=7), reason="3rd Violation")
                await message.channel.send(
                    f"🛑 {message.author.mention}, 3rd violation — muted for **7 DAYS**!"
                )
                await send_log(
                    message.guild,
                    f"🚫 7 Days Penalty: {message.author.mention}",
                    discord.Color.red()
                )
            except Exception as e:
                print(f"7 days timeout error: {e}")
        else:
            # 10 minutes on 1st and 2nd violation
            try:
                await message.author.timeout(timedelta(minutes=10), reason="Spam/Violation")
                await message.channel.send(
                    f"⚠️ {message.author.mention}, muted for 10 mins! ({ihlal_sayisi}/3)",
                    delete_after=10
                )
                await send_log(
                    message.guild,
                    f"⚠️ 10 Mins Penalty: {message.author.mention} ({ihlal_sayisi}/3)",
                    discord.Color.orange()
                )
            except Exception as e:
                print(f"10 mins timeout error: {e}")
        return

    # ── BOT RESPONSES ─────────────────────────────────────────────────────────
    bot_isimlari = ["bot", "z3ittanistan", bot.user.mention]
    bota_mi_soylendi = any(isim in content for isim in bot_isimlari)

    if content == "sa":
        await message.channel.send(f"cami mi bura oç {message.author.mention}!")

    if any(k in content for k in ["selam", "selamun aleyküm", "sea", "selamlar"]):
        await message.channel.send(f"cami mi bura oç {message.author.mention}!")

    if bota_mi_soylendi:
        if "amina koyim" in content or "amına koyim" in content:
            await message.channel.send(f"Ben senin amına koyim {message.author.mention}")
        if any(k in content for k in ["ananın amı", "anayın amı", "ananin ami", "anayin ami"]):
            await message.channel.send(f"Senin ananın amı {message.author.mention}")
        if any(k in content for k in [
            "ananı sikeyim", "anani sikeyim", "oç", "ananı sikerim", "anani sikerim",
            "orospu evladı", "oc", "orospu çocuğu", "orospu cocugu",
            "ananı sikiyim", "anani sikiyim", "anani sikim", "ananı sikim"
        ]):
            yanit = random.choice([
                f"😤 Gel baş kaldır bana {message.author.mention}!",
                f"👀 Gel bana bakış at {message.author.mention}",
                f"🤫 Konuşma salağın amından çıkma {message.author.mention}",
                f"😂 Yeni yetme orospu evladı seni {message.author.mention}",
                f"🙏 Anan sikilir inşallah {message.author.mention}",
                f"💀 Sevgilimin oğluna bak sen hele {message.author.mention}",
                f"Senin ananı sikeyim orospu evladı {message.author.mention}",
            ])
            await message.channel.send(yanit)
        elif "amk" in content:
            await message.channel.send(f"Senin amk {message.author.mention}")

    # ── LEADERBOARD (MESSAGE) ──────────────────────────────────────────────
    uid_str = str(message.author.id)
    siralama_verileri.setdefault("mesajlar", {})
    siralama_verileri["mesajlar"][uid_str] = siralama_verileri["mesajlar"].get(uid_str, 0) + 1
    save_siralama()

    # ── LEVEL + ECONOMY ───────────────────────────────────────────────────────
    levels.setdefault(uid_str, {"xp": 0, "level": 0})
    levels[uid_str]["xp"] += 2
    lvl = levels[uid_str]["level"]
    next_lvl_xp = (lvl + 1) * 70

    if levels[uid_str]["xp"] >= next_lvl_xp:
        levels[uid_str]["level"] += 1
        yeni_lvl = levels[uid_str]["level"]
        check_user(uid_str)
        economy[uid_str]["balance"] += yeni_lvl * 100
        save_economy()
        if str(yeni_lvl) in LEVEL_ROLLER:
            rol_adi = LEVEL_ROLLER[str(yeni_lvl)]
            rol = discord.utils.get(message.guild.roles, name=rol_adi)
            if rol:
                try:
                    await message.author.add_roles(rol, reason="Level System")
                    await send_log(
                        message.guild,
                        f"🎖️ Level Role: {message.author.mention} → {rol_adi}",
                        discord.Color.gold()
                    )
                except Exception as e:
                    print(f"Role granting error: {e}")
        save_levels()

    await bot.process_commands(message)


@bot.event
async def on_audit_log_entry_create(entry):
    if entry.action == discord.AuditLogAction.ban:
        target = entry.target
        user = entry.user
        reason = entry.reason or "No reason provided."
        embed = discord.Embed(title="🔨 Manual Ban", color=discord.Color.red())
        embed.add_field(name="Banned User",
                        value=f"{target.name} ({target.id})", inline=False)
        embed.add_field(name="Banned By", value=user.mention, inline=False)
        embed.add_field(name="Reason",      value=reason, inline=False)
        await send_log(entry.guild, embed=embed)


# ─────────────────────────────────────────────────────────────────────────────
# BLACKJACK VIEW  (unmodified)
# ─────────────────────────────────────────────────────────────────────────────
class BlackjackView(View):
    """
    MIGRATION NOTE:
      This View class can be preserved entirely when switching from 
      a prefix command to a slash command. Buttons continue to work via interaction.
      Only change: Storing 'author' identity instead of the ctx parameter.
    """

    def __init__(self, author_id, oyuncu_el, kasa_el, deck, ranks,
                 get_card, calculate, format_hand, bahis, economy, u_id):
        super().__init__(timeout=60.0)
        self.author_id = author_id       # ← instead of ctx.author.id
        self.oyuncu_el = oyuncu_el
        self.kasa_el = kasa_el
        self.deck = deck
        self.ranks = ranks
        self.get_card = get_card
        self.calculate = calculate
        self.format_hand = format_hand
        self.bahis = bahis
        self.economy = economy
        self.u_id = u_id

    async def finalize_game(self, interaction):
        o_skor = self.calculate(self.oyuncu_el)
        while self.calculate(self.kasa_el) < 17 and o_skor <= 21:
            self.kasa_el.append(self.get_card())
        k_skor = self.calculate(self.kasa_el)

        if o_skor > 21:
            txt = f"💥 **Bust!** -{self.bahis} Coin"
            self.economy[self.u_id]["balance"] -= self.bahis
            final_color = discord.Color.red()
        elif k_skor > 21 or o_skor > k_skor:
            txt = f"🎉 **You Won!** +{self.bahis} Coin"
            self.economy[self.u_id]["balance"] += self.bahis
            final_color = discord.Color.green()
        elif o_skor < k_skor:
            txt = f"💀 **You Lost!** -{self.bahis} Coin"
            self.economy[self.u_id]["balance"] -= self.bahis
            final_color = discord.Color.red()
        else:
            txt = "🤝 **Draw!**"
            final_color = discord.Color.gold()

        save_economy()

        embed = discord.Embed(title="🃏 Game Result", description=txt, color=final_color)
        embed.add_field(name=f"Dealer [{k_skor}]", value=self.format_hand(self.kasa_el), inline=True)
        embed.add_field(name=f"You [{o_skor}]", value=self.format_hand(self.oyuncu_el), inline=True)

        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

    @discord.ui.button(label="👊 Hit", style=discord.ButtonStyle.green)
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ This is not your game!", ephemeral=True)

        # Do not throw error if deck is empty
        if not self.deck:
            return await interaction.response.send_message("❌ Deck is empty!", ephemeral=True)

        self.oyuncu_el.append(self.get_card())
        score = self.calculate(self.oyuncu_el)

        if score >= 21:
            await self.finalize_game(interaction)
        else:
            embed = discord.Embed(title="🃏 Blackjack Table", color=discord.Color.blue())
            embed.add_field(
                name=f"Dealer [{self.ranks[self.kasa_el[0][0]]}]",
                value=f"`{self.kasa_el[0][0]}{self.kasa_el[0][1]}` ❓",
                inline=True
            )
            embed.add_field(
                name=f"You [{score}]",
                value=self.format_hand(self.oyuncu_el),
                inline=True
            )
            await interaction.response.edit_message(embed=embed, view=self)  # ← view=self ADDED

    @discord.ui.button(label="🛑 Stand", style=discord.ButtonStyle.red)
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ This is not your game!", ephemeral=True)

        await self.finalize_game(interaction)


# ═════════════════════════════════════════════════════════════════════════════
#  COG 1 — MANAGEMENT (Whitelist & Money Management)
# ═════════════════════════════════════════════════════════════════════════════
class AdminCog(commands.Cog):

    admin_group = app_commands.Group(
        name="admin", description="Admin commands")

    @admin_group.command(name="whitelist", description="Adds or removes a member from the whitelist")
    @app_commands.describe(
        islem="add or remove",
        hedef="Member mention (@member) or ID"
    )
    async def beyazliste(self, interaction: discord.Interaction,
                         islem: str, hedef: str):
        if interaction.user.id != OZEL_SAHIP_ID:
            return await interaction.response.send_message(
                "🚫 **Permission Denied:** This command is exclusive to the bot owner!", ephemeral=True
            )

        # Extract user ID from ID or mention
        try:
            uid = int(re.sub(r"[<@!>]", "", hedef))
        except ValueError:
            return await interaction.response.send_message("❌ Enter a valid user mention or ID!", ephemeral=True)

        # Fetch the user (even if not in the server)
        try:
            user = interaction.guild.get_member(uid) or await interaction.client.fetch_user(uid)
        except discord.NotFound:
            return await interaction.response.send_message("❌ User with this ID could not be found!", ephemeral=True)

        islem = islem.lower().strip()

        if islem in ["ekle", "add"]:
            if uid in BEYAZ_LISTE:
                return await interaction.response.send_message("❌ Already in the list.", ephemeral=True)
            BEYAZ_LISTE.append(uid)
            save_white_list()  # ← save to disk
            await interaction.response.send_message(f"✅ {user.mention} (`{uid}`) has been added to the whitelist.")
            await send_log(interaction.guild, f"🛡️ Whitelist: {user.mention} (`{uid}`) added.", discord.Color.green())

        elif islem in ["cikar", "çıkar", "kaldir", "kaldır", "remove"]:
            if uid not in BEYAZ_LISTE:
                return await interaction.response.send_message("❌ This user is not in the list.", ephemeral=True)
            BEYAZ_LISTE.remove(uid)
            save_white_list()  # ← save to disk
            await interaction.response.send_message(f"✅ {user.mention} (`{uid}`) has been removed from the whitelist.")
            await send_log(interaction.guild, f"🛡️ Whitelist: {user.mention} (`{uid}`) removed.", discord.Color.red())

        else:
            await interaction.response.send_message("❓ You must type `add` or `remove`.", ephemeral=True)
    # ── /admin whitelistlist ─────────────────────────────────────────────
    # OLD: .beyazlisteliste
    @admin_group.command(name="whitelistlist", description="Shows the members in the whitelist")
    async def beyazlisteliste(self, interaction: discord.Interaction):
        if interaction.user.id != OZEL_SAHIP_ID and interaction.user.id not in BEYAZ_LISTE:
            return await interaction.response.send_message("🚫 You do not have permission!", ephemeral=True)
        liste_metni = "\n".join(
            [f"• <@{uid}> (`{uid}`)" for uid in BEYAZ_LISTE]) or "List is empty."
        embed = discord.Embed(title="🛡️ Whitelist Records",
                              description=liste_metni, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

    # ── /admin addmoney ─────────────────────────────────────────────────────
    # OLD: .parabas / .ekle / .paraver
    @admin_group.command(name="addmoney", description="Adds coin to a member (Whitelist)")
    @app_commands.describe(member="Recipient member", miktar="Amount of coin to add")
    async def parabas(self, interaction: discord.Interaction,
                      member: discord.Member, miktar: int):
        if interaction.user.id not in BEYAZ_LISTE and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("🚫 No Permission!", ephemeral=True)
        SINIR = 10_000_000
        if miktar > SINIR:
            return await interaction.response.send_message(f"⚠️ Max {SINIR:,} Coin at once!", ephemeral=True)
        if miktar <= 0:
            return await interaction.response.send_message("⚠️ Enter a valid amount!", ephemeral=True)
        u_id = str(member.id)
        check_user(u_id)
        economy[u_id]["balance"] += miktar
        save_economy()
        embed = discord.Embed(
            title="💸 Money Printed!", description=f"{interaction.user.mention} added **{miktar} Coin** to {member.mention}'s account!", color=discord.Color.gold(), timestamp=discord.utils.utcnow())
        await interaction.response.send_message(embed=embed)
        await send_log(interaction.guild, f"💰 Money Printed: {interaction.user.mention} → {member.mention} | {miktar} Coin", discord.Color.gold())

    # ── /admin removemoney ─────────────────────────────────────────────────────
    # OLD: .parasil / .bakiyesifirla / .paracep
    @admin_group.command(name="removemoney", description="Removes coin from a member (Whitelist / Owner)")
    @app_commands.describe(member="Target member", miktar="Amount of coin to remove")
    async def parasil(self, interaction: discord.Interaction,
                      member: discord.Member, miktar: int):
        if interaction.user.id != OZEL_SAHIP_ID and interaction.user.id not in BEYAZ_LISTE:
            return await interaction.response.send_message("🚫 No Permission!", ephemeral=True)
        u_id = str(member.id)
        check_user(u_id)
        mevcut = economy[u_id]["balance"]
        if miktar > mevcut:
            miktar = mevcut
        economy[u_id]["balance"] -= miktar
        save_economy()
        embed = discord.Embed(
            title="📉 Money Removed!", description=f"**{miktar} Coin** has been removed from {member.mention}'s account.\nNew Balance: `{economy[u_id]['balance']}` Coin", color=discord.Color.red(), timestamp=discord.utils.utcnow())
        await interaction.response.send_message(embed=embed)
        await send_log(interaction.guild, f"🔻 Money Removed: {interaction.user.mention} → {member.mention} | {miktar} Coin", discord.Color.red())

    # ── /announcement ──────────────────────────────────────────────────────────────
    @app_commands.command(name="announcement", description="Sends an announcement to the server with a stylish embed (pings @everyone)")
    @app_commands.describe(
        mesaj="Announcement text (You can use \\n to go to a new line)",
        baslik="Embed title (optional)"
    )
    async def duyuru(self, interaction: discord.Interaction, mesaj: str, baslik: str = None):
        if not interaction.user.guild_permissions.administrator and interaction.user.id not in BEYAZ_LISTE:
            return await interaction.response.send_message("🚫 You do not have permission to use this command!", ephemeral=True)
            
        mesaj_temiz = mesaj.replace("\\n", "\n")
        
        embed = BotUI.embed(
            title=baslik,
            desc=mesaj_temiz,
            color=0x5865F2  # Blurple / Blue color (like the example)
        )
        
        await interaction.response.send_message("✅ Announcement is being sent...", ephemeral=True)
        await interaction.channel.send(content="@everyone", embed=embed)

    # ── /dm ──────────────────────────────────────────────────────────────────
    @app_commands.command(name="dm", description="Sends a DM to a specific person or everyone on the server")
    @app_commands.describe(
        hedef="Member to send DM to (if left empty, it will be sent to everyone on the server)",
        mesaj="Message to be sent (You can use \\n for a new line)",
        baslik="Embed title (optional)"
    )
    async def dm_gonder(self, interaction: discord.Interaction, mesaj: str, hedef: discord.Member = None, baslik: str = None):
        if not interaction.user.guild_permissions.administrator and interaction.user.id not in BEYAZ_LISTE:
            return await interaction.response.send_message("🚫 You do not have permission to use this command!", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        mesaj_temiz = mesaj.replace("\\n", "\n")

        if hedef:
            # DM to a single person
            embed = BotUI.embed(
                title=baslik or "📬 Server Message",
                desc=f"{hedef.mention}\n\n{mesaj_temiz}",
                color=0x5865F2
            )
            embed.set_footer(text=f"Sent from {interaction.guild.name} server")
            try:
                await hedef.send(embed=embed)
                await interaction.followup.send(
                    BotUI.success(f"DM successfully sent to {hedef.mention}."),
                    ephemeral=True
                )
                await send_log(interaction.guild,
                    f"📬 DM Sent: {interaction.user.mention} → {hedef.mention}",
                    discord.Color.blurple())
            except discord.Forbidden:
                await interaction.followup.send(
                    BotUI.error(f"{hedef.mention}'s DMs are closed, the message could not be sent."),
                    ephemeral=True
                )
        else:
            # DM to everyone on the server
            await interaction.followup.send(
                BotUI.warn(f"Sending DMs to all members in the server... This might take a while."),
                ephemeral=True
            )
            basarili = 0
            basarisiz = 0
            for member in interaction.guild.members:
                if member.bot:
                    continue
                embed = BotUI.embed(
                    title=baslik or "📬 Server Announcement",
                    desc=f"{member.mention}\n\n{mesaj_temiz}",
                    color=0x5865F2
                )
                embed.set_footer(text=f"Sent from {interaction.guild.name} server")
                try:
                    await member.send(embed=embed)
                    basarili += 1
                    await asyncio.sleep(0.5)  # Rate limit protection
                except discord.Forbidden:
                    basarisiz += 1
                except Exception:
                    basarisiz += 1
            await interaction.channel.send(
                BotUI.success(f"Mass DM completed! ✅ {basarili} successful | ❌ {basarisiz} failed (DM closed)")
            )
            await send_log(interaction.guild,
                f"📬 Mass DM: Sent by {interaction.user.mention} | ✅ {basarili} | ❌ {basarisiz}",
                discord.Color.blurple())



# ═════════════════════════════════════════════════════════════════════════════
#  COG 2 — ECONOMY
# ═════════════════════════════════════════════════════════════════════════════
class EkonomiCog(commands.Cog):



    # ── /economy balance ────────────────────────────────────────────────────
    # OLD: .bakiye [@member]
    @app_commands.command(name="balance", description="Shows the coin balance")
    @app_commands.describe(member="Member to check balance for (empty = you)")
    async def bakiye(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user  # MIGRATION: ctx.author → interaction.user
        u_id = str(member.id)
        check_user(u_id)
        embed = BotUI.embed(
            title="💰 Balance Info", 
            desc=f"{member.mention}'s current balance:\n\n🪙 **{economy[u_id]['balance']:,} Coin**",
            color=BotUI.COLOR_INFO,
            user=interaction.user
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    # ── /economy daily ─────────────────────────────────────────────────────
    # OLD: .daily / .günlük / .gunluk
    # MIGRATION: commands.cooldown → app_commands.checks.cooldown
    @app_commands.command(name="daily", description="Claim your daily 5000 Coin reward")
    @app_commands.checks.cooldown(1, 86400, key=lambda i: i.user.id)
    async def daily(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        check_user(u_id)
        odul = 5000
        economy[u_id]["balance"] += odul
        save_economy()
        embed = BotUI.embed(
            title="💸 Daily Reward", 
            desc=f"Congratulations {interaction.user.mention}!\n**{odul:,} Coin** has been added to your account as a daily login reward.", 
            color=BotUI.COLOR_SUCCESS,
            user=interaction.user
        )
        await interaction.response.send_message(embed=embed)

    # ── /economy coinflip ──────────────────────────────────────────────────
    # OLD: .coinflip / .yt / .yazitura / .cf
    @app_commands.command(name="cf", description="Play Coinflip")
    @app_commands.describe(miktar="Bet amount or 'all'")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.user.id)
    async def coinflip(self, interaction: discord.Interaction, miktar: str):
        u_id = str(interaction.user.id)
        check_user(u_id)
        if miktar.lower() == "all":
            bahis = economy[u_id]["balance"]
        else:
            try:
                bahis = int(miktar)
            except:
                return await interaction.response.send_message(BotUI.error("Enter a valid amount or type `all`!"), ephemeral=True)
        if bahis <= 0:
            return await interaction.response.send_message(BotUI.error("You can play with at least 1 Coin!"), ephemeral=True)
        if economy[u_id]["balance"] < bahis:
            return await interaction.response.send_message(BotUI.error(f"Insufficient balance! (Current: **{economy[u_id]['balance']} Coin**)"), ephemeral=True)

        await interaction.response.defer()

        # Animation frames
        animasyon = ["🪙", "✨🪙✨", "💫🪙💫", "⭐🪙⭐", "🌟🪙🌟"]
        embed = discord.Embed(title="🪙 Coinflip", description="The coin is flipped in the air...", color=discord.Color.gold())
        embed.add_field(name="Bet", value=f"**{bahis} Coin**", inline=True)
        mesaj = await interaction.followup.send(embed=embed)

        for kare in animasyon:
            embed.description = f"{kare} Flipping coin... {kare}"
            await mesaj.edit(embed=embed)
            await asyncio.sleep(0.6)

        # Result
        sonuc = random.choice(["kazandın", "kaybettin"])
        if sonuc == "kazandın":
            economy[u_id]["balance"] += bahis
            embed.title = "🎉 YOU WON!"
            embed.description = f"It landed on **HEADS**!"
            embed.color = discord.Color.green()
            embed.set_field_at(0, name="Earnings", value=f"**+{bahis} Coin**", inline=True)
            embed.add_field(name="💰 New Balance", value=f"**{economy[u_id]['balance']} Coin**", inline=True)
        else:
            economy[u_id]["balance"] -= bahis
            embed.title = "💀 YOU LOST!"
            embed.description = f"It landed on **TAILS**!"
            embed.color = discord.Color.red()
            embed.set_field_at(0, name="Loss", value=f"**-{bahis} Coin**", inline=True)
            embed.add_field(name="💰 Remaining Balance", value=f"**{economy[u_id]['balance']} Coin**", inline=True)

        save_economy()
        await mesaj.edit(embed=embed)
    # ── /economy slot ──────────────────────────────────────────────────────
    # OLD: .slot [miktar]
    @app_commands.command(name="slot", description="Spin the slot machine")
    @app_commands.describe(miktar="Bet amount or 'all'")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.user.id)
    async def slot(self, interaction: discord.Interaction, miktar: str):
        u_id = str(interaction.user.id)
        check_user(u_id)
        if miktar.lower() == "all":
            bahis = economy[u_id]["balance"]
        else:
            try:
                bahis = int(miktar)
            except:
                return await interaction.response.send_message("❌ Enter an amount or type `all`!", ephemeral=True)
        if bahis <= 0 or economy[u_id]["balance"] < bahis:
            return await interaction.response.send_message("❌ Insufficient balance!", ephemeral=True)

        emoji_list = ["🍒", "🍋", "🔔", "💎", "🎰", "🍎"]
        await interaction.response.defer()

        # Initial embed
        embed = discord.Embed(title="🎰 SLOT MACHINE", color=discord.Color.gold())
        embed.add_field(name="Bet", value=f"**{bahis} Coin**", inline=False)
        embed.add_field(name="Reel", value="🎰 | 🎰 | 🎰", inline=False)
        mesaj = await interaction.followup.send(embed=embed)

        # Pre-determine results
        a = random.choice(emoji_list)
        b = random.choice(emoji_list)
        c = random.choice(emoji_list)

        # Animation — each reel stopping in turn
        for i in range(6):
            if i < 3:
                s1 = random.choice(emoji_list)
                s2 = random.choice(emoji_list)
                s3 = random.choice(emoji_list)
                embed.set_field_at(1, name="Reel", value=f"{s1} | {s2} | {s3}", inline=False)
            elif i == 3:
                # First reel stopped
                s2 = random.choice(emoji_list)
                s3 = random.choice(emoji_list)
                embed.set_field_at(1, name="Reel", value=f"**{a}** | {s2} | {s3}", inline=False)
            elif i == 4:
                # Second reel stopped
                s3 = random.choice(emoji_list)
                embed.set_field_at(1, name="Reel", value=f"**{a}** | **{b}** | {s3}", inline=False)
            else:
                # Third reel stopped
                embed.set_field_at(1, name="Reel", value=f"**{a}** | **{b}** | **{c}**", inline=False)

            await mesaj.edit(embed=embed)
            await asyncio.sleep(0.5)

        # Calculate result
        if a == b == c:
            kazanc = bahis * 5
            economy[u_id]["balance"] += kazanc
            embed.title = "🎊 JACKPOT!"
            embed.color = discord.Color.from_rgb(255, 215, 0)
            sonuc_txt = f"✅ **+{kazanc} Coin** (5x)"
        elif a == b or b == c or a == c:
            kazanc = int(bahis * 1.5)
            economy[u_id]["balance"] += kazanc
            embed.title = "✨ Double!"
            embed.color = discord.Color.green()
            sonuc_txt = f"✅ **+{kazanc} Coin** (1.5x)"
        else:
            economy[u_id]["balance"] -= bahis
            embed.title = "💀 You Lost!"
            embed.color = discord.Color.red()
            sonuc_txt = f"❌ **-{bahis} Coin**"

        save_economy()
        embed.set_field_at(1, name=f"[ {a} | {b} | {c} ]", value=sonuc_txt, inline=False)
        embed.add_field(name="💰 Balance", value=f"**{economy[u_id]['balance']} Coin**", inline=False)
        await mesaj.edit(embed=embed)

    # ── /economy send ────────────────────────────────────────────────────
    # OLD: .gonder / .gönder / .send
    @app_commands.command(name="send", description="Send coin to someone else")
    @app_commands.describe(member="Recipient member", miktar="Coin to send")
    async def gonder(self, interaction: discord.Interaction,
                     member: discord.Member, miktar: int):
        u_id = str(interaction.user.id)
        t_id = str(member.id)
        check_user(u_id)
        check_user(t_id)
        if miktar <= 0 or economy[u_id]["balance"] < miktar:
            return await interaction.response.send_message("❌ Invalid amount or insufficient balance!", ephemeral=True)
        economy[u_id]["balance"] -= miktar
        economy[t_id]["balance"] += miktar
        save_economy()
        await interaction.response.send_message(f"✅ **{miktar} Coin** has been sent to {member.mention}.")

    # ── /economy rob ───────────────────────────────────────────────────────
    # OLD: .soy @member
    @app_commands.command(name="rob", description="Rob someone (warning: you might get caught!)")
    @app_commands.describe(member="Member to rob")
    @app_commands.checks.cooldown(1, 600, key=lambda i: i.user.id)
    async def soy(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("You can't rob yourself! 😂", ephemeral=True)
        if member.id in BEYAZ_LISTE:
            return await interaction.response.send_message(f"🛡️ {member.mention} is under protection!", ephemeral=True)
        u_id = str(interaction.user.id)
        t_id = str(member.id)
        check_user(u_id)
        check_user(t_id)
        if economy[t_id]["balance"] < 100:
            return await interaction.response.send_message("This person has no money, not worth robbing.", ephemeral=True)
        await interaction.response.defer()
        if random.randint(1, 100) <= 40:
            ust_limit = int(economy[t_id]["balance"] * 0.2)
            calinan = random.randint(50, ust_limit) if ust_limit > 50 else 50
            economy[t_id]["balance"] -= calinan
            economy[u_id]["balance"] += calinan
            save_economy()
            await interaction.followup.send(f"🥷 {interaction.user.mention} robbed {member.mention}! **+{calinan} Coin**")
        else:
            try:
                await interaction.user.timeout(timedelta(minutes=2), reason="Caught while robbing!")
                await interaction.followup.send(f"🚨 **CAUGHT!** {interaction.user.mention}, muted for 2 minutes!")
            except:
                await interaction.followup.send(f"🚨 You got caught! (I don't have enough permission.)")
            await send_log(interaction.guild, f"🚫 Robbery Attempt: {interaction.user.mention} got caught.", discord.Color.red())

    # ── /economy sweetbonanza ──────────────────────────────────────────────
    # OLD: .sweetbonanza / .sweet / .bonanza / .sb
    @app_commands.command(name="sweetbonanza", description="🍭 Sweet Bonanza slot game")
    @app_commands.describe(miktar="Bet amount or 'all'")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.user.id)
    async def sweetbonanza(self, interaction: discord.Interaction, miktar: str):
        u_id = str(interaction.user.id)
        check_user(u_id)
        if miktar.lower() == "all":
            bahis = economy[u_id]["balance"]
        else:
            try:
                bahis = int(miktar)
            except:
                return await interaction.response.send_message("❌ Enter a valid amount or type `all`!", ephemeral=True)
        if bahis < 10:
            return await interaction.response.send_message("❌ Min 10 Coin!", ephemeral=True)
        if economy[u_id]["balance"] < bahis:
            return await interaction.response.send_message("❌ Insufficient balance!", ephemeral=True)

        semboller = ["🍎", "🍇", "🍉", "🍌", "🟦", "🟪", "❤️"]
        seker = "🍭"
        await interaction.response.defer()

        # Initial embed
        embed = discord.Embed(title="🍭 SWEET BONANZA", color=discord.Color.from_rgb(255, 20, 147))
        embed.add_field(name="Bet", value=f"**{bahis} Coin**", inline=False)
        embed.add_field(name="Reel", value="🍭 | 🍭 | 🍭 | 🍭", inline=False)
        mesaj = await interaction.followup.send(embed=embed)

        # Pre-determine results
        s1 = random.choice(semboller + [seker])
        s2 = random.choice(semboller + [seker])
        s3 = random.choice(semboller + [seker])
        s4 = random.choice(semboller + [seker])
        sonuc = [s1, s2, s3, s4]

        # Animation — reels stop in turn
        for i in range(7):
            if i < 3:
                # All spinning
                r = [random.choice(semboller + [seker]) for _ in range(4)]
                embed.set_field_at(1, name="Reel", value=f"{r[0]} | {r[1]} | {r[2]} | {r[3]}", inline=False)
            elif i == 3:
                r = [random.choice(semboller + [seker]) for _ in range(3)]
                embed.set_field_at(1, name="Reel", value=f"**{s1}** | {r[0]} | {r[1]} | {r[2]}", inline=False)
            elif i == 4:
                r = [random.choice(semboller + [seker]) for _ in range(2)]
                embed.set_field_at(1, name="Reel", value=f"**{s1}** | **{s2}** | {r[0]} | {r[1]}", inline=False)
            elif i == 5:
                r = random.choice(semboller + [seker])
                embed.set_field_at(1, name="Reel", value=f"**{s1}** | **{s2}** | **{s3}** | {r}", inline=False)
            else:
                embed.set_field_at(1, name="Reel", value=f"**{s1}** | **{s2}** | **{s3}** | **{s4}**", inline=False)

            await mesaj.edit(embed=embed)
            await asyncio.sleep(0.5)

        # Calculate result
        seker_sayisi = sonuc.count(seker)
        kalp_sayisi = sonuc.count("❤️")
        ayni_sembol = max([sonuc.count(s) for s in semboller]) if semboller else 0
        carpan = 0

        if seker_sayisi >= 3:
            carpan = 10 if seker_sayisi == 3 else 25
            durum = "🍭 **SCATTER! JACKPOT!**"
            embed.color = discord.Color.from_rgb(255, 215, 0)
        elif kalp_sayisi >= 3:
            carpan = 6
            durum = "❤️ **HEARTS POPPED!**"
            embed.color = discord.Color.red()
        elif ayni_sembol == 4:
            carpan = 5
            durum = "✨ **FULL COMBO!**"
            embed.color = discord.Color.green()
        elif seker_sayisi == 2 or ayni_sembol == 3:
            carpan = 2
            durum = "🍬 **NICE POP!**"
            embed.color = discord.Color.green()
        elif seker_sayisi == 1:
            carpan = 1.2
            durum = "🍭 **CANDY CONSOLATION**"
            embed.color = discord.Color.blurple()
        else:
            durum = "💀 **DISAPPOINTMENT...**"
            embed.color = discord.Color.red()

        if carpan > 0:
            kazanc = int(bahis * carpan)
            economy[u_id]["balance"] += (kazanc - bahis)
            son_msg = f"✅ **+{kazanc} Coin** ({carpan}x)"
        else:
            economy[u_id]["balance"] -= bahis
            son_msg = f"❌ **-{bahis} Coin**"

        save_economy()

        embed.title = "🍭 SWEET BONANZA"
        embed.set_field_at(1, name=f"[ {s1} | {s2} | {s3} | {s4} ]", value=f"{durum}\n\n{son_msg}", inline=False)
        embed.add_field(name="💰 Wallet", value=f"**{economy[u_id]['balance']} Coin**", inline=False)
        await mesaj.edit(embed=embed)

    # ── /economy blackjack ─────────────────────────────────────────────────
    # OLD: .blackjackyeni / .bj / .blackjack
    @app_commands.command(name="blackjack", description="🃏 Join the blackjack table")
    @app_commands.describe(bahis="Bet amount or 'all'")
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.user.id)
    async def blackjack(self, interaction: discord.Interaction, bahis: str):
        u_id = str(interaction.user.id)
        check_user(u_id)
        current_balance = economy[u_id]["balance"]
        if bahis.lower() == "all":
            bahis_miktari = current_balance
        else:
            try:
                bahis_miktari = int(bahis)
            except:
                return await interaction.response.send_message("Enter a valid number or `all`!", ephemeral=True)
        if bahis_miktari < 10:
            return await interaction.response.send_message("Min 10 Coin!", ephemeral=True)
        if current_balance < bahis_miktari:
            return await interaction.response.send_message(f"You don't have money! ({current_balance} Coin)", ephemeral=True)

        ranks = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
                 '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}
        suits = ['♠️', '♥️', '♦️', '♣️']
        deck = [(r, s) for r in ranks for s in suits]
        random.shuffle(deck)

        def get_card(): return deck.pop()

        def calculate(hand):
            score = sum(ranks[c[0]] for c in hand)
            aces = sum(1 for c in hand if c[0] == 'A')
            while score > 21 and aces:
                score -= 10
                aces -= 1
            return score

        def format_hand(hand): return " ".join(
            [f"`{c[0]}{c[1]}`" for c in hand])

        oyuncu_el = [get_card(), get_card()]
        kasa_el = [get_card(), get_card()]
        embed = discord.Embed(title="🃏 Blackjack Table",
                              color=discord.Color.blue())
        embed.add_field(name=f"Dealer [{ranks[kasa_el[0][0]]}]",
                        value=f"`{kasa_el[0][0]}{kasa_el[0][1]}` ❓", inline=True)
        embed.add_field(name=f"You [{calculate(oyuncu_el)}]",  value=format_hand(
            oyuncu_el), inline=True)

        # MIGRATION: Sending interaction.user.id instead of ctx.author.id
        view = BlackjackView(
            interaction.user.id, oyuncu_el, kasa_el, deck,
            ranks, get_card, calculate, format_hand, bahis_miktari, economy, u_id
        )
        await interaction.response.send_message(embed=embed, view=view)

    # ── /economy gambler ──────────────────────────────────────────────────
    # OLD: .kumarbaz
    @app_commands.command(name="gambler", description="Buy SWEETBONANZA role with 50.000 Coin")
    async def kumarbaz(self, interaction: discord.Interaction):
        u_id = str(interaction.user.id)
        check_user(u_id)
        fiyat = 50_000
        rol_adi = "SWEETBONANZA"
        if economy[u_id]["balance"] < fiyat:
            kalan = fiyat - economy[u_id]["balance"]
            return await interaction.response.send_message(f"❌ You need **{kalan} Coin** more!", ephemeral=True)
        rol = discord.utils.get(interaction.guild.roles, name=rol_adi)
        if not rol:
            return await interaction.response.send_message(f"❌ Role `{rol_adi}` could not be found!", ephemeral=True)
        if rol in interaction.user.roles:
            return await interaction.response.send_message("You are already a gambler!", ephemeral=True)
        try:
            economy[u_id]["balance"] -= fiyat
            save_economy()
            await interaction.user.add_roles(rol)
            embed = discord.Embed(title="🎰 A NEW GAMBLER!",
                                  description=f"{interaction.user.mention} bought the `{rol_adi}` role by paying **{fiyat} Coin**!", color=discord.Color.purple())
            await interaction.response.send_message(embed=embed)
            await send_log(interaction.guild, f"💸 Market: {interaction.user.mention} bought `{rol_adi}`.", discord.Color.purple())
        except:
            await interaction.response.send_message("🚨 Role could not be given!", ephemeral=True)
# ═════════════════════════════════════════════════════════════════════════════
#  COG 3 — MODERATION
# ═════════════════════════════════════════════════════════════════════════════
class ModerasyonCog(commands.Cog):
    mod_group = app_commands.Group(
        name="mod", description="Moderation commands")

    @mod_group.command(name="ban", description="Bans multiple members (ID or Mention)")
    @app_commands.describe(targets="Members to ban (ID or Mention, separate with spaces)", sebep="Ban reason")
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction,
                  targets: str,
                  sebep: str = "Banned by Z 3 İ T T System"):

        await interaction.response.defer(ephemeral=True)

        user_ids = list(set(re.findall(r'\d+', targets)))

        if not user_ids:
            return await interaction.followup.send(BotUI.error("No valid User ID or Mention found."))

        author_id = interaction.user.id
        simdi = datetime.now()

        if author_id not in BEYAZ_LISTE:
            ban_takip.setdefault(author_id, [])
            ban_takip[author_id] = [t for t in ban_takip[author_id]
                                    if (simdi - t).total_seconds() < BAN_LIMIT_SURESI * 60]

            if len(ban_takip[author_id]) + len(user_ids) > BAN_LIMIT_SAYISI:
                return await interaction.followup.send(BotUI.warn(f"Operation cancelled. Ban limit ({BAN_LIMIT_SAYISI}) will be exceeded."))

        success_count = 0
        failed_targets = []

        for uid in user_ids:
            try:
                target_id = int(uid)
                member = interaction.guild.get_member(target_id) or await interaction.client.fetch_user(target_id)

                # OZEL_SAHIP_ID can ban anyone
                if author_id != OZEL_SAHIP_ID:
                    if target_id in BEYAZ_LISTE or target_id == interaction.client.user.id:
                        failed_targets.append(f"{uid} (Whitelist)")
                        continue

                    if isinstance(member, discord.Member):
                        if interaction.user != interaction.guild.owner and interaction.user.top_role.position <= member.top_role.position:
                            failed_targets.append(f"{member.name} (Role Hierarchy)")
                            continue
                else:
                    # Even OZEL_SAHIP_ID cannot ban the bot
                    if target_id == interaction.client.user.id:
                        failed_targets.append(f"{uid} (Bot)")
                        continue

                await interaction.guild.ban(member, reason=sebep)
                success_count += 1

                if author_id not in BEYAZ_LISTE:
                    ban_takip[author_id].append(datetime.now())

            except Exception as e:
                failed_targets.append(f"{uid} (Error: {str(e)})")

        report = f"**{success_count}** members were banned."
        if failed_targets:
            report += f"\n> ❌ **Failed:** {', '.join(failed_targets)}"

        await interaction.followup.send(BotUI.success(report))
        if success_count > 0:
            if success_count == 1:
                # Single ban — write name and ID
                basarili_id = next(
                    uid for uid in user_ids
                    if f"{uid} (" not in " ".join(failed_targets)
                )
                try:
                    basarili_user = await interaction.client.fetch_user(int(basarili_id))
                    log_msg = f"🔨 Ban: **{basarili_user.name}** (`{basarili_id}`) | Reason: {sebep} | Moderator: {interaction.user.mention}"
                except:
                    log_msg = f"🔨 Ban: `{basarili_id}` | Reason: {sebep} | Moderator: {interaction.user.mention}"
            else:
                # Mass ban — write only count
                log_msg = f"🔨 Mass Ban: **{success_count}** members | Reason: {sebep} | Moderator: {interaction.user.mention}"

            await send_log(interaction.guild, log_msg, discord.Color.red())
    @mod_group.command(name="unban", description="Unbans multiple members (ID or Mention)")
    @app_commands.describe(targets="Members to unban (ID, separate with spaces)", sebep="Reason")
    @app_commands.default_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction,
                    targets: str,
                    sebep: str = "Unbanned by Z 3 İ T T System"):
        await interaction.response.defer(ephemeral=True)

        user_ids = list(set(re.findall(r'\d+', targets)))
        if not user_ids:
            return await interaction.followup.send(BotUI.error("No valid User ID found."))

        success_count = 0
        failed_targets = []

        for uid in user_ids:
            try:
                target_id = int(uid)
                user = await interaction.client.fetch_user(target_id)
                await interaction.guild.unban(user, reason=sebep)
                success_count += 1
            except discord.NotFound:
                failed_targets.append(f"{uid} (Not banned)")
            except discord.Forbidden:
                failed_targets.append(f"{uid} (Insufficient permissions)")
            except Exception as e:
                failed_targets.append(f"{uid} (Error: {str(e)})")

        report = f"**{success_count}** members were unbanned."
        if failed_targets:
            report += f"\n> ❌ **Failed:** {', '.join(failed_targets)}"

        await interaction.followup.send(BotUI.success(report))
        if success_count > 0:
            await send_log(
                interaction.guild,
                f"🔓 Mass Unban: {success_count} members | Moderator: {interaction.user.mention}",
                discord.Color.green()
            )
    # ── /mod kick ──────────────────────────────────────────────────────────
    # OLD: .kick @member [reason]

    @mod_group.command(name="kick", description="Kicks a member from the server")
    @app_commands.describe(member="Member to kick", sebep="Reason")
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction,
                   member: discord.Member,
                   sebep: str = "Kicked by Z 3 İ T T System"):
        if interaction.user.id not in BEYAZ_LISTE:
            simdi = datetime.now()
            kick_takip.setdefault(interaction.user.id, [])
            kick_takip[interaction.user.id] = [t for t in kick_takip[interaction.user.id] if (
                simdi - t).total_seconds() < KICK_LIMIT_SURESI * 60]
            if len(kick_takip[interaction.user.id]) >= KICK_LIMIT_SAYISI:
                return await interaction.response.send_message(BotUI.warn(f"Kick limit ({KICK_LIMIT_SAYISI}) exceeded!"), ephemeral=True)
        if member.id in BEYAZ_LISTE or member.id == bot.user.id:
            return await interaction.response.send_message(BotUI.warn(f"{member.name} is in the Whitelist!"), ephemeral=True)
        if interaction.user != interaction.guild.owner and interaction.user.top_role.position <= member.top_role.position:
            return await interaction.response.send_message(BotUI.error(f"{member.name} is in the same or higher role as you!"), ephemeral=True)
        try:
            await interaction.guild.kick(member, reason=f"{interaction.user} | {sebep}")
            if interaction.user.id not in BEYAZ_LISTE:
                kick_takip[interaction.user.id].append(datetime.now())
            await interaction.response.send_message(BotUI.success(f"**{member.name}** was kicked from the server."))
        except Exception as e:
            await interaction.response.send_message(BotUI.error(f"Error: {e}"), ephemeral=True)

    # ── /mod mute ────────────────────────────────────────────────────────
    # OLD: .sustur / .mute @member1 @member2 [minutes] [reason]
    @mod_group.command(name="mute", description="Temporarily mutes a member")
    @app_commands.describe(member="Member to mute", sure="Duration in minutes", sebep="Reason")
    @app_commands.default_permissions(moderate_members=True)
    async def sustur(self, interaction: discord.Interaction,
                     member: discord.Member,
                     sure: int = 10,
                     sebep: str = "Rule Violation"):
        if member.id in BEYAZ_LISTE:
            return await interaction.response.send_message(BotUI.warn(f"{member.mention} is in the Whitelist!"), ephemeral=True)
        if interaction.user != interaction.guild.owner and interaction.user.top_role.position <= member.top_role.position:
            return await interaction.response.send_message(BotUI.error(f"{member.name} is in the same or higher role as you!"), ephemeral=True)
        try:
            await member.timeout(timedelta(minutes=sure), reason=sebep)
            await interaction.response.send_message(BotUI.success(f"**{member.name}** was muted for {sure} minutes."))
        except Exception as e:
            await interaction.response.send_message(BotUI.error(f"Error: {e}"), ephemeral=True)

    # ── /mod unmute ──────────────────────────────────────────────────
    # OLD: .susturkaldir / .unmute / .susturkaldır
    @mod_group.command(name="unmute", description="Unmutes a member")
    @app_commands.describe(member="Member to unmute")
    @app_commands.default_permissions(moderate_members=True)
    async def susturkaldir(self, interaction: discord.Interaction, member: discord.Member):
        if interaction.user != interaction.guild.owner and interaction.user.top_role.position <= member.top_role.position:
            return await interaction.response.send_message(BotUI.warn(f"Hierarchy block: {member.mention}"), ephemeral=True)
        try:
            await member.timeout(None)
            await interaction.response.send_message(BotUI.success(f"**{member.name}** was unmuted."))
            await send_log(interaction.guild, f"🔊 Unmuted: {member.name} | {interaction.user.mention}", discord.Color.green())
        except Exception as e:
            await interaction.response.send_message(BotUI.error(f"Error: {e}"), ephemeral=True)

    # ── /mod clear ───────────────────────────────────────────────────────
    # OLD: .temizle / .sil / .purge / .clear [amount]
    @mod_group.command(name="clear", description="Clears messages from the channel (max 100)")
    @app_commands.describe(miktar="Number of messages to delete (1-100)")
    @app_commands.default_permissions(manage_messages=True)
    async def sil(self, interaction: discord.Interaction, miktar: int):
        if not 1 <= miktar <= 100:
            return await interaction.response.send_message(BotUI.warn("You must enter a number between 1-100!"), ephemeral=True)
        # defer: purge can take a long time
        await interaction.response.defer(ephemeral=True)
        try:
            deleted = await interaction.channel.purge(limit=miktar)
            await interaction.followup.send(BotUI.success(f"**{len(deleted)}** messages successfully deleted!"), ephemeral=True)
            await send_log(interaction.guild, f"🧹 Clear: {interaction.channel.mention} | {len(deleted)} messages | {interaction.user.mention}", discord.Color.blue())
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
    @mod_group.command(name="clear_member", description="Deletes the last X messages of specified member(s) in the channel")
    @app_commands.describe(
        hedefler="Mentions or IDs of members whose messages will be deleted (separated by spaces)",
        miktar="Number of messages to delete (Maximum 100)"
    )
    @app_commands.default_permissions(manage_messages=True)
    async def siluye(self, interaction: discord.Interaction, hedefler: str, miktar: int):
        if not 1 <= miktar <= 100:
            return await interaction.response.send_message(BotUI.warn("You must enter a number between 1-100!"), ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        # ID Set creation for O(1) Performance
        hedef_ids = set()
        for hedef in hedefler.split():
            try:
                uid = int(re.sub(r"[<@!>]", "", hedef))
                hedef_ids.add(uid)
            except ValueError:
                continue

        if not hedef_ids:
            return await interaction.followup.send(BotUI.error("You did not enter a valid user mention or ID!"), ephemeral=True)

        silinen_sayac = 0

        # We manage the check function inside purge with a dynamic counter
        def kontrol(message: discord.Message):
            nonlocal silinen_sayac
            # If we reached our target count, do not return true anymore (stop deleting)
            if silinen_sayac >= miktar:
                return False

            if message.author.id in hedef_ids:
                silinen_sayac += 1
                return True
            return False

        try:
            # We keep the search depth (limit) high (e.g. search 500 messages back)
            # But the deletion list will be full as soon as the `check` function reaches `miktar`.
            deleted = await interaction.channel.purge(limit=500, check=kontrol)

            etiketler_str = ", ".join([f"<@{uid}>" for uid in hedef_ids])
            await interaction.followup.send(BotUI.success(f"Found and cleared the last **{len(deleted)}** messages of the specified members from history!"), ephemeral=True)

            asyncio.create_task(send_log(
                interaction.guild, 
                f"🧹 Member Message Clear: {interaction.channel.mention} | Targets: {etiketler_str} | Deleted: {len(deleted)} messages | Moderator: {interaction.user.mention}", 
                discord.Color.red()
            ))
        except discord.Forbidden:
            await interaction.followup.send(BotUI.error("I don't have the necessary permissions to delete messages!"), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(BotUI.error(f"Error: {e}"), ephemeral=True)
    # ── /mod clearall ──────────────────────────────────────────────────────
    # OLD: .clearall / .kanalisifirla / .nuke
    @mod_group.command(name="nuke", description="Resets the channel (nuke) — Whitelist required")
    @app_commands.default_permissions(administrator=True)
    async def nuke(self, interaction: discord.Interaction):
        if interaction.user.id not in BEYAZ_LISTE and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message(BotUI.warn("Whitelist required!"), ephemeral=True)
        kanal = interaction.channel
        pozisyon = kanal.position
        kategori = kanal.category
        izinler = kanal.overwrites
        isim = kanal.name
        await interaction.response.send_message(BotUI.warn(f"**{isim}** is being reset..."))
        try:
            await kanal.delete(reason="Nuke")
            yeni_kanal = await interaction.guild.create_text_channel(
                name=isim, category=kategori,
                overwrites=izinler, position=pozisyon, reason="Channel reset"
            )
            embed = BotUI.embed(
                title="✨ Channel Reset", desc=f"Successfully cleared by {interaction.user.mention}.", color=BotUI.COLOR_SUCCESS)
            await yeni_kanal.send(embed=embed)
            await yeni_kanal.send("https://tenor.com/view/kaboom-boom-gif-4090446168494834371")
            await send_log(interaction.guild, f"💥 CHANNEL RESET: #{isim} | {interaction.user.mention}", discord.Color.dark_red())
        except Exception as e:
            print(f"Clear All Error: {e}")

    # ── /mod giverole ────────────────────────────────────────────────────────
    # OLD: .rolver @member @role
    @mod_group.command(name="giverole", description="Give a role to a member")
    @app_commands.describe(member="Target member", role="Role to give")
    @app_commands.default_permissions(manage_roles=True)
    async def rolver(self, interaction: discord.Interaction,
                     member: discord.Member, role: discord.Role):
        if role >= interaction.guild.me.top_role:
            return await interaction.response.send_message(BotUI.error("Bot's permission is not enough to give this role!"), ephemeral=True)
        if interaction.user.top_role <= role and interaction.user != interaction.guild.owner:
            return await interaction.response.send_message(BotUI.error("You cannot give a role higher or equal to your own role!"), ephemeral=True)
        await member.add_roles(role)
        await interaction.response.send_message(BotUI.success(f"Gave the `{role.name}` role to user {member.mention}."))

    # ── /mod takerole ─────────────────────────────────────────────────────────
    # OLD: .rolal @member @role  or  .rolal @member all
    @mod_group.command(name="takerole", description="Take a role from a member (or type 'all' to take all)")
    @app_commands.describe(member="Target member", secim="Mention a role or type 'all'")
    @app_commands.default_permissions(manage_roles=True)
    async def rolal(self, interaction: discord.Interaction,
                    member: discord.Member, secim: str):
        if member.id in BEYAZ_LISTE:
            return await interaction.response.send_message(BotUI.warn("You cannot touch the roles of a user in the whitelist!"), ephemeral=True)
        if interaction.user.id != interaction.guild.owner_id and interaction.user.top_role <= member.top_role:
            return await interaction.response.send_message(BotUI.error("Insufficient permissions! You cannot perform actions on someone with a higher or equal position."), ephemeral=True)
        if secim.lower() == "all":
            await interaction.response.defer()
            alinanlar = 0
            for role in member.roles:
                if role.name == "@everyone" or role >= interaction.guild.me.top_role:
                    continue
                try:
                    await member.remove_roles(role)
                    alinanlar += 1
                except:
                    pass
            return await interaction.followup.send(f"🧹 Cleared all roles of {member.mention}! ({alinanlar} roles)")
        try:
            ctx_fake_role = discord.utils.get(interaction.guild.roles, name=secim) or \
                interaction.guild.get_role(int(secim.strip("<@&>")))
            if not ctx_fake_role:
                return await interaction.response.send_message("❌ Role not found!", ephemeral=True)
            if ctx_fake_role >= interaction.guild.me.top_role:
                return await interaction.response.send_message("❌ Bot permission is not enough!", ephemeral=True)
            await member.remove_roles(ctx_fake_role)
            await interaction.response.send_message(f"✅ {member.mention} → `{ctx_fake_role.name}` was taken.")
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

    # ── /mod giveroleall ─────────────────────────────────────────────────────
    # OLD: .rolverall @role
    @mod_group.command(name="giveroleall", description="Give specified role to everyone (Whitelist)")
    @app_commands.describe(role="Role to give")
    async def rolverall(self, interaction: discord.Interaction, role: discord.Role):
        if interaction.user.id not in BEYAZ_LISTE and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("❌ You are not in the whitelist!", ephemeral=True)
        await interaction.response.defer()
        basarili = 0
        for uye in interaction.guild.members:
            if not uye.bot and role not in uye.roles:
                try:
                    await uye.add_roles(role)
                    basarili += 1
                except:
                    pass
        await interaction.followup.send(f"✅ `{role.name}` was given to **{basarili}** people.")

# ── /mod lock ─────────────────────────────────────────────────────────
    @mod_group.command(name="lock", description="Locks and hides the channel")
    @app_commands.default_permissions(manage_channels=True)
    async def kilit(self, interaction: discord.Interaction):
        everyone_role = interaction.guild.default_role
        ozel_rol = discord.utils.get(interaction.guild.roles, name=OTO_ROL_ADI)

        # Disable channel viewing for @everyone, reset message sending
        overwrite = interaction.channel.overwrites_for(everyone_role)
        overwrite.view_channel = False
        overwrite.send_messages = None
        await interaction.channel.set_permissions(everyone_role, overwrite=overwrite)

        # Disable channel viewing for the special role, reset message sending
        if ozel_rol:
            ow2 = interaction.channel.overwrites_for(ozel_rol)
            ow2.view_channel = False
            ow2.send_messages = None
            await interaction.channel.set_permissions(ozel_rol, overwrite=ow2)

        embed = discord.Embed(
            title="🔒 Channel Hidden and Locked",
            description=f"Access disabled for @everyone and {OTO_ROL_ADI} role.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        await send_log(interaction.guild, f"🔒 Channel Hidden/Locked: {interaction.channel.mention} | {interaction.user.mention}", discord.Color.orange())
    @mod_group.command(name="rename", description="Changes the server nickname of multiple members")
    @app_commands.describe(
        hedefler="Member mentions (@member1 @member2) or IDs (type separated by spaces)",
        yeni_isim="New server nickname (leave blank to return to original name)"
    )
    @app_commands.default_permissions(manage_nicknames=True)
    async def rename(self, interaction: discord.Interaction, hedefler: str, yeni_isim: str = None):
        # We defer the interaction because the process might take a long time (prevent API timeout)
        await interaction.response.defer(ephemeral=True)

        # Split the input by spaces and clean it
        hedef_listesi = [h.strip() for h in hedefler.split() if h.strip()]
        if not hedef_listesi:
            return await interaction.followup.send("❌ You must enter at least one valid user mention or ID!")

        basarili = []
        hatali = []
        is_admin_or_whitelisted = interaction.user == interaction.guild.owner or interaction.user.id in BEYAZ_LISTE

        for hedef in hedef_listesi:
            try:
                uid = int(re.sub(r"[<@!>]", "", hedef))
            except ValueError:
                hatali.append(f"{hedef} (Invalid format)")
                continue

            member = interaction.guild.get_member(uid)
            if not member:
                hatali.append(f"<@{uid}> (Not found in server)")
                continue

            # Hierarchy check
            if not is_admin_or_whitelisted:
                if interaction.user.top_role.position <= member.top_role.position:
                    hatali.append(f"{member.mention} (Insufficient permission/Hierarchy)")
                    continue

            eski_isim = member.display_name
            try:
                await member.edit(nick=yeni_isim)
                basarili.append(f"✅ {member.mention} (`{eski_isim}` → `{yeni_isim or member.name}`)")

                # We put the log sending process to asynchronous background (So it doesn't slow down the loop)
                asyncio.create_task(send_log(
                    interaction.guild,
                    f"✏️ Mass Nickname Changed: {member.mention} | `{eski_isim}` → `{yeni_isim or member.name}` | Moderator: {interaction.user.mention}",
                    discord.Color.blue()
                ))
            except discord.Forbidden:
                hatali.append(f"{member.mention} (Bot's permission insufficient)")
            except Exception as e:
                hatali.append(f"{member.mention} (Error: {str(e)})")

        # Reporting Stage
        rapor = []
        if basarili:
            rapor.append("**Successful Operations:**\n" + "\n".join(basarili))
        if hatali:
            rapor.append("**Failed Operations:**\n" + "\n".join(hatali))

        # Join so we don't exceed Discord's 2000 character limit
        tam_rapor = "\n\n".join(rapor)
        if len(tam_rapor) > 2000:
            tam_rapor = tam_rapor[:1990] + "\n...and more"

        await interaction.followup.send(tam_rapor)
    # ── /mod unlock ───────────────────────────────────────────────────────
    @mod_group.command(name="unlock", description="Unlocks the channel. If you type 'all', unlocks all channels except the log category")
    @app_commands.describe(hedef="Channel to unlock (blank = this channel) or 'all' (all channels)")
    @app_commands.default_permissions(manage_channels=True)
    async def kilitac(self, interaction: discord.Interaction, hedef: str = None):
        await interaction.response.defer(ephemeral=True)

        everyone_role = interaction.guild.default_role
        ozel_rol = discord.utils.get(interaction.guild.roles, name=OTO_ROL_ADI)

        # Find the log category
        log_kategori = None
        for kategori in interaction.guild.categories:
            if LOG_KANAL_ADI.lower() in kategori.name.lower():
                log_kategori = kategori
                break

        async def kanal_ac(kanal: discord.TextChannel):
            """Unlock the given channel: grant view + read message history permission"""
            overwrite = kanal.overwrites_for(everyone_role)
            overwrite.view_channel = True
            overwrite.read_message_history = True
            await kanal.set_permissions(everyone_role, overwrite=overwrite)

            if ozel_rol:
                ow2 = kanal.overwrites_for(ozel_rol)
                ow2.view_channel = True
                ow2.read_message_history = True
                await kanal.set_permissions(ozel_rol, overwrite=ow2)

        if hedef and hedef.strip().lower() == "all":
            # Unlock all text and voice channels (except protected categories)
            acilan = []

            # Text channels
            for kanal in interaction.guild.text_channels:
                # Skip channels in the fixed protected category list
                if kanal.category_id and kanal.category_id in KORUNAN_KATEGORI_IDLERI:
                    continue
                # Also skip the log channel by name (if it has no category)
                if kanal.name == LOG_KANAL_ADI:
                    continue
                try:
                    await kanal_ac(kanal)
                    acilan.append(kanal.mention)
                except Exception:
                    pass

            embed = discord.Embed(
                title="🔓 All Channels Unlocked",
                description=(
                    f"**{len(acilan)}** channels unlocked except protected categories.\n"
                    f"View and read message history permissions granted."
                ),
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            await send_log(
                interaction.guild,
                f"🔓 Mass Channel Unlock: **{len(acilan)}** channels unlocked (except protected categories) | {interaction.user.mention}",
                discord.Color.green()
            )

        else:
            # Single channel: specified channel or current channel
            if hedef:
                # Extract ID from channel mention or find by name
                try:
                    kanal_id = int(re.sub(r"[<#>]", "", hedef))
                    kanal = interaction.guild.get_channel(kanal_id)
                except ValueError:
                    kanal = discord.utils.get(interaction.guild.text_channels, name=hedef.strip())
                if not kanal:
                    return await interaction.followup.send("❌ Channel not found!", ephemeral=True)
            else:
                kanal = interaction.channel

            await kanal_ac(kanal)

            embed = discord.Embed(
                title="🔓 Channel Unlocked",
                description=f"View restrictions removed for {kanal.mention} channel.\nView and read message history permissions granted.",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            await send_log(
                interaction.guild,
                f"🔓 Channel Unlocked: {kanal.mention} | {interaction.user.mention}",
                discord.Color.green()
            )

    # ── /mod unlockann ────────────────────────────────────────────────────
    @mod_group.command(name="unlockann", description="Enables announcement channel mode: send messages disabled, view + history open")
    @app_commands.describe(hedef="Channel to put in announcement mode (blank = this channel)")
    @app_commands.default_permissions(manage_channels=True)
    async def kilitacanc(self, interaction: discord.Interaction, hedef: str = None):
        await interaction.response.defer(ephemeral=True)

        everyone_role = interaction.guild.default_role
        ozel_rol = discord.utils.get(interaction.guild.roles, name=OTO_ROL_ADI)

        # Determine the target channel
        if hedef:
            try:
                kanal_id = int(re.sub(r"[<#>]", "", hedef))
                kanal = interaction.guild.get_channel(kanal_id)
            except ValueError:
                kanal = discord.utils.get(interaction.guild.text_channels, name=hedef.strip())
            if not kanal:
                return await interaction.followup.send("❌ Channel not found!", ephemeral=True)
        else:
            kanal = interaction.channel

        # @everyone: send messages disabled, view + history open
        overwrite = kanal.overwrites_for(everyone_role)
        overwrite.send_messages = False
        overwrite.view_channel = True
        overwrite.read_message_history = True
        await kanal.set_permissions(everyone_role, overwrite=overwrite)

        # Same for special role
        if ozel_rol:
            ow2 = kanal.overwrites_for(ozel_rol)
            ow2.send_messages = False
            ow2.view_channel = True
            ow2.read_message_history = True
            await kanal.set_permissions(ozel_rol, overwrite=ow2)

        embed = discord.Embed(
            title="📢 Announcement Mode Active",
            description=(
                f"{kanal.mention} channel set to **announcement mode**.\n\n"
                "✅ View channel → **Open**\n"
                "✅ Read message history → **Open**\n"
                "❌ Send messages → **Closed**"
            ),
            color=discord.Color.orange()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        await send_log(
            interaction.guild,
            f"📢 Announcement Mode: {kanal.mention} | View+History open, Send messages closed | {interaction.user.mention}",
            discord.Color.orange()
        )
# ═════════════════════════════════════════════════════════════════════════════
#  COG 4 — VOICE SYSTEM
# ═════════════════════════════════════════════════════════════════════════════


class SesCog(commands.Cog):

    ses_group = app_commands.Group(
        name="voice", description="Voice channel commands")

    # ── /voice join ───────────────────────────────────────────────────────────
    # OLD: .gir
    @ses_group.command(name="join", description="Connects the bot to the voice channel (Whitelist)")
    async def gir(self, interaction: discord.Interaction):
        if interaction.user.id not in BEYAZ_LISTE and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("🚫 Whitelist required!", ephemeral=True)
        if interaction.guild.voice_client:
            return await interaction.response.send_message(
                f"❌ I'm already in the `{interaction.guild.voice_client.channel.name}` channel!", ephemeral=True
            )
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ Join a voice channel first!", ephemeral=True)

        await interaction.response.defer()  # ← extends the 3-second limit
        await interaction.user.voice.channel.connect()
        await interaction.followup.send(f"🔊 Joined the `{interaction.user.voice.channel.name}` channel!")

    @ses_group.command(name="leave", description="Disconnects the bot from the voice channel (Whitelist)")
    async def cik(self, interaction: discord.Interaction):
        if interaction.user.id not in BEYAZ_LISTE and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("🚫 Whitelist required!", ephemeral=True)
        if not interaction.guild.voice_client:
            return await interaction.response.send_message("❌ I'm not in a voice channel anyway!", ephemeral=True)

        await interaction.response.defer()  # ← here too
        await interaction.guild.voice_client.disconnect()
        await interaction.followup.send("👋 Left the voice channel.")

    # ── /voice duration ──────────────────────────────────────────────────────────
    # OLD: .sessurem / .vctime [@member]
    @ses_group.command(name="duration", description="Shows the total voice channel duration")
    @app_commands.describe(member="Member to check duration (blank = you)")
    async def sure(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user   # MIGRATION: ctx.author → interaction.user
        ses_data = load_ses()
        toplam = ses_data.get(str(target.id), {}).get("toplam_saniye", 0)
        if target.id in ses_giris_takip:
            toplam += int(time.time() - ses_giris_takip[target.id])
        embed = discord.Embed(title="🎙️ Voice Channel Duration",
                              color=discord.Color.blurple())
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name=target.display_name,
                        value=f"**{sure_formatla(toplam)}**")
        await interaction.response.send_message(embed=embed)

    # ── /voice leaderboard ──────────────────────────────────────────────────────
    # OLD: .sessıralama / .seslb [top]
    @ses_group.command(name="leaderboard", description="Voice channel leaderboard")
    @app_commands.describe(top="Number of people to show (default 10)")
    async def siralama(self, interaction: discord.Interaction, top: int = 10):
        await interaction.response.defer()
        ses_data = load_ses()
        skorlar = []
        for uid_str, info in ses_data.items():
            toplam = info["toplam_saniye"]
            uid = int(uid_str)
            if uid in ses_giris_takip:
                toplam += int(time.time() - ses_giris_takip[uid])
            skorlar.append((uid, toplam))
        skorlar.sort(key=lambda x: x[1], reverse=True)
        madalyalar = ["🥇", "🥈", "🥉"]
        satirlar = []
        i = 0
        for uid, sn in skorlar:
            if i >= top:
                break
            m = interaction.guild.get_member(uid)
            if not m:
                continue  # Users not in the server won't be shown
            ikon = madalyalar[i] if i < 3 else f"`{i+1}.`"
            satirlar.append(f"{ikon} {m.mention} — {sure_formatla(sn)}")
            i += 1
        embed = discord.Embed(title="🏆 Voice Channel Leaderboard", description="\n".join(
            satirlar) or "No data.", color=discord.Color.gold())
        await interaction.followup.send(embed=embed)

    # ── /voice lock ─────────────────────────────────────────────────────────
    # OLD: .seskilit all/#channel
    @ses_group.command(name="lock", description="Locks voice channels (Whitelist)")
    @app_commands.describe(hedef="'all' or channel ID")
    async def seskilit(self, interaction: discord.Interaction, hedef: str = "all"):
        if interaction.user.id not in BEYAZ_LISTE:
            return await interaction.response.send_message("❌ Whitelist required!", ephemeral=True)
        await interaction.response.defer()
        everyone = interaction.guild.default_role
        oto_rol = discord.utils.get(interaction.guild.roles, name=OTO_ROL_ADI)
        overwrites = {everyone: discord.PermissionOverwrite(
            view_channel=False, connect=False)}
        if oto_rol:
            overwrites[oto_rol] = discord.PermissionOverwrite(
                view_channel=False, connect=False)
        if hedef == "all":
            count = 0
            for channel in interaction.guild.voice_channels:
                await channel.edit(overwrites=overwrites)
                count += 1
            await interaction.followup.send(f"🔇 **{count}** voice channels locked!")
        else:
            try:
                cid = int(hedef.replace("<#", "").replace(">", ""))
                channel = interaction.guild.get_channel(cid)
                if isinstance(channel, discord.VoiceChannel):
                    await channel.edit(overwrites=overwrites)
                    await interaction.followup.send(f"🔒 **{channel.name}** locked.")
                else:
                    await interaction.followup.send("That is not a voice channel.", ephemeral=True)
            except:
                await interaction.followup.send("Enter a valid channel ID or type `all`!", ephemeral=True)

    # ── /voice unlock ───────────────────────────────────────────────────────
    # OLD: .seskilitac all/#channel
    @ses_group.command(name="unlock", description="Unlocks voice channel (Whitelist)")
    @app_commands.describe(hedef="'all' or channel ID")
    async def seskilitac(self, interaction: discord.Interaction, hedef: str = "all"):
        if interaction.user.id not in BEYAZ_LISTE:
            return await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        await interaction.response.defer()
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(
                view_channel=None, connect=None)
        }
        oto_rol = discord.utils.get(interaction.guild.roles, name=OTO_ROL_ADI)
        if oto_rol:
            overwrites[oto_rol] = discord.PermissionOverwrite(
                view_channel=None, connect=None)
        if hedef == "all":
            for channel in interaction.guild.voice_channels:
                await channel.edit(overwrites=overwrites)
            await interaction.followup.send("🔓 All voice channels unlocked!")
        else:
            try:
                cid = int(hedef.replace("<#", "").replace(">", ""))
                channel = interaction.guild.get_channel(cid)
                if isinstance(channel, discord.VoiceChannel):
                    await channel.edit(overwrites=overwrites)
                    await interaction.followup.send(f"🔓 **{channel.name}** unlocked.")
                else:
                    await interaction.followup.send("That is not a voice channel.", ephemeral=True)
            except:
                await interaction.followup.send("Enter a valid channel ID or type `all`!", ephemeral=True)

    # ── /voice pull ───────────────────────────────────────────────────────────
    # OLD: .cek all / .cek @member
    @ses_group.command(name="pull", description="Pulls members to your voice channel")
    @app_commands.describe(hedef="'all' or @member mention")
    async def cek(self, interaction: discord.Interaction,
                  hedef: str = "all",
                  member: discord.Member = None):
        if not (interaction.user.id == interaction.guild.owner_id or
                interaction.user.guild_permissions.adminastator):
            return await interaction.response.send_message("Insufficient permissions! ❌", ephemeral=True)
        if not interaction.user.voice:
            return await interaction.response.send_message("Join a voice channel first! ❌", ephemeral=True)
        kanal = interaction.user.voice.channel
        cekilen_sayisi = 0
        await interaction.response.defer()
        if hedef == "all":
            for uye in interaction.guild.members:
                if not uye.bot and uye.voice and uye.voice.channel != kanal:
                    try:
                        await uye.move_to(kanal)
                        cekilen_sayisi += 1
                    except:
                        pass
            await interaction.followup.send(f"🚀 Pulled **{cekilen_sayisi}** members!")
        elif member:
            if member.voice and member.voice.channel != kanal:
                try:
                    await member.move_to(kanal)
                    await interaction.followup.send(f"✅ {member.mention} was pulled.")
                except:
                    await interaction.followup.send(f"❌ {member.mention} could not be pulled.")
            else:
                await interaction.followup.send(f"{member.mention} is not in a voice channel or already with you.", ephemeral=True)
        else:
            await interaction.followup.send("Usage: `/voice pull all` or `/voice pull member:@member`", ephemeral=True)
class DynamicHelpSelect(discord.ui.Select):
    def __init__(self, mapping: dict[str, list[str]], is_admin: bool = False) -> None:
        self.mapping = mapping
        self.is_admin = is_admin
        
        # Maps raw database/tree terms to production-grade UI presentation layers
        self.meta = {
            "Ekonomi": {"emoji": "💰", "desc": "Balance, casino games and transfers"},
            "Mod": {"emoji": "🛡️", "desc": "Server management and moderation tools"},
            "Ses": {"emoji": "🎙️", "desc": "Voice statistics and private room locks"},
            "Genel Komutlar": {"emoji": "👤", "desc": "Profile, invite ranking and user data"},
            "Admin": {"emoji": "👑", "desc": "Minting, deleting and whitelist management"}
        }

        options = []
        for category, cmds in mapping.items():
            info = self.meta.get(category, {"emoji": "📁", "desc": f"Contains {len(cmds)} commands."})
            options.append(
                discord.SelectOption(
                    label=category if category != "Mod" else "Moderation",
                    description=info["desc"],
                    value=category,
                    emoji=info["emoji"]
                )
            )
        
        super().__init__(
            placeholder="Select the category you want to inspect..." if not is_admin else "Select the admin panel...",
            min_values=1,
            max_values=1,
            options=options[:25]
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        selected: str = self.values[0]
        cmds: list[str] = self.mapping[selected]
        
        color = 0x8B0000 if selected == "Admin" else 0x2b2d31
        title = f"{self.meta.get(selected, {}).get('emoji', '📁')} {selected} Category"
        
        embed = discord.Embed(
            title=title,
            description="\n".join(cmds),
            color=color
        )
        embed.set_footer(text=f"Queried by: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.edit_message(embed=embed)


class DynamicHelpView(discord.ui.View):
    def __init__(self, mapping: dict[str, list[str]], is_admin: bool = False) -> None:
        super().__init__(timeout=90)
        self.add_item(DynamicHelpSelect(mapping, is_admin))
            
# ═════════════════════════════════════════════════════════════════════════════
#  COG 5 — INFO (rank, stats, profile, owner, help, adminmenu)
# ═════════════════════════════════════════════════════════════════════════════
class BilgiCog(commands.Cog):

    # ── /rank ──────────────────────────────────────────────────────────────
    # OLD: .rank [@user]
    @app_commands.command(name="rank", description="Shows level and XP status")
    @app_commands.describe(member="Member to check (empty = you)")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        u_id = str(member.id)
        user_data = levels.get(u_id, {"xp": 0, "level": 0})
        xp = user_data["xp"]
        lvl = user_data["level"]
        next_xp = (lvl + 1) * 70
        embed = BotUI.embed(
            title=f"📊 {member.display_name} Statistics", color=BotUI.COLOR_INFO, user=interaction.user)
        embed.add_field(name="Level", value=f"**{lvl}**", inline=True)
        embed.add_field(name="XP",    value=f"**{xp}/{next_xp}**", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    # ── /stats ─────────────────────────────────────────────────────────────
    # OLD: .stats
    @app_commands.command(name="stats", description="Shows server statistics")
    async def stats(self, interaction: discord.Interaction):
        guild = interaction.guild
        toplam_uye = guild.member_count
        online = len(
            [m for m in guild.members if m.status != discord.Status.offline])
        botlar = len([m for m in guild.members if m.bot])
        insanlar = toplam_uye - botlar
        kurulus = guild.created_at.strftime("%d %B %Y")
        embed = BotUI.embed(title=f"📊 {guild.name} Statistics",
                              color=BotUI.COLOR_WARN, user=interaction.user)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(
            name="👥 Members", value=f"Total: **{toplam_uye}**\nHuman: **{insanlar}**\nBot: **{botlar}**", inline=True)
        embed.add_field(
            name="🟢 Status",  value=f"Online: **{online}**\nOffline: **{toplam_uye-online}**", inline=True)
        embed.add_field(
            name="💬 Channels", value=f"Text: **{len(guild.text_channels)}**\nVoice: **{len(guild.voice_channels)}**", inline=True)
        embed.add_field(name="📅 Created", value=f"**{kurulus}**", inline=False)
        embed.add_field(name="👑 Server Owner",
                        value=f"{guild.owner.mention}", inline=True)
        embed.add_field(
            name="🛡️ Security", value=f"**{str(guild.verification_level).upper()}**", inline=True)

        await interaction.response.send_message(embed=embed)

    # ── /profile ────────────────────────────────────────────────────────────
    # OLD: .profil / .userinfo / .me / .p [@user]
    @app_commands.command(name="profile", description="Shows member profile information")
    @app_commands.describe(member="Member whose profile will be viewed (empty = you)")
    async def profil(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        u_id = str(member.id)
        bakiye = economy.get(u_id, {}).get("balance", 0)
        xp = levels.get(u_id, {}).get("xp", 0)
        level = levels.get(u_id, {}).get("level", 1)
        next_xp = level * 100
        embed = BotUI.embed(title=f"👤 {member.display_name} Profile",
                              color=BotUI.COLOR_INFO, user=interaction.user)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="💰 Balance",
                        value=f"`{bakiye}` Coin", inline=True)
        embed.add_field(name="⭐ Level",
                        value=f"Level `{level}`", inline=True)
        embed.add_field(name="📈 Progress",
                        value=f"`{xp}/{next_xp}` XP", inline=True)
        embed.add_field(name="📅 Joined", value=member.joined_at.strftime(
            "%d/%m/%Y"), inline=True)
        embed.add_field(name="🚀 Discord", value=member.created_at.strftime(
            "%d/%m/%Y"), inline=True)
        roller = [r.mention for r in reversed(
            member.roles) if r.name != "@everyone"]
        if roller:
            embed.add_field(name=f"🛡️ Roles ({len(roller)})", value=" ".join(
                roller[:5]) + ("..." if len(roller) > 5 else ""), inline=False)

        await interaction.response.send_message(embed=embed)

    # ── /owner ─────────────────────────────────────────────────────────────
    # OLD: .owner / .kurucu / .sahip
    @app_commands.command(name="owner", description="Shows server owner information")
    async def owner(self, interaction: discord.Interaction):
        owner = interaction.guild.owner or await interaction.guild.fetch_member(interaction.guild.owner_id)
        durum = "✅ Secure (Whitelisted)" if owner.id in BEYAZ_LISTE else "⚠️ Not Whitelisted"
        embed = discord.Embed(title="👑 Server Owner", description=f"{owner.mention} wears the crown!", color=discord.Color.gold(
        ), timestamp=discord.utils.utcnow())
        embed.set_thumbnail(url=owner.display_avatar.url)
        embed.set_image(url=owner.display_avatar.url)
        embed.add_field(name="🏷️ Username",
                        value=f"`{owner.name}`", inline=True)
        embed.add_field(name="🆔 ID",
                        value=f"`{owner.id}`", inline=True)
        embed.add_field(name="📅 Joined Server",
                        value=owner.joined_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="🚀 Joined Discord",
                        value=owner.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="🛡️ Protection Status",
                        value=f"`{durum}`", inline=False)
        embed.set_footer(text=f"{interaction.guild.name}",
                         icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        await interaction.response.send_message(embed=embed)

    # ── /help ────────────────────────────────────────────────────────────
    # OLD: .yardım / .yardim
    @app_commands.command(name="help", description="Lists all current and active commands of the bot.")
    async def yardim(self, interaction: discord.Interaction) -> None:
        mapping: dict[str, list[str]] = {}
        
        # Safely walk through the entire live command tree at runtime
        for cmd in interaction.client.tree.walk_commands():
            # Enforce Zero-Trust isolation: Isolate admin commands entirely from public eyes
            if cmd.name == "admin" or (cmd.parent and cmd.parent.name == "admin"):
                continue
                
            if isinstance(cmd, app_commands.Command):
                # Parse structural group naming logic
                if cmd.parent:
                    category = cmd.parent.name.capitalize()
                    cmd_name = f"{cmd.parent.name} {cmd.name}"
                else:
                    category = "Genel Komutlar"
                    cmd_name = cmd.name
                    
                if category not in mapping:
                    mapping[category] = []
                    
                desc = cmd.description or "No description provided."
                mapping[category].append(f"`/{cmd_name}` - {desc}")

        embed = discord.Embed(
            title="🤖 Z 3 İ T T System Bot | User Help Menu",
            description="You can review all active submodules, casino games and statistics commands using the dropdown menu below.",
            color=0x2b2d31
        )
        await interaction.response.send_message(embed=embed, view=DynamicHelpView(mapping, is_admin=False), ephemeral=True)


    @app_commands.command(name="adminmenu", description="Dynamic permission panel for system administrators.")
    @app_commands.default_permissions(administrator=True)
    async def adminmenu(self, interaction: discord.Interaction) -> None:
        admin_mapping: dict[str, list[str]] = {"Admin": []}
        
        for cmd in interaction.client.tree.walk_commands():
            # Capture only grouped admin logic or explicit endpoints tied to admin rights
            if cmd.name == "admin" or (cmd.parent and cmd.parent.name == "admin"):
                if isinstance(cmd, app_commands.Command):
                    cmd_name = f"{cmd.parent.name} {cmd.name}" if cmd.parent else cmd.name
                    desc = cmd.description or "Authorized system intervention."
                    admin_mapping["Admin"].append(f"`/{cmd_name}` - {desc}")

        embed = discord.Embed(
            title="⚙️ Z 3 İ T T System | Admin Control Panel",
            description="This panel can only be viewed by accounts with **Administrator** permission.\nSupply and whitelist manipulation tools are below:",
            color=0x8B0000
        )
        await interaction.response.send_message(embed=embed, view=DynamicHelpView(admin_mapping, is_admin=True), ephemeral=True)

    @app_commands.command(name="ship", description="Matchmaking command 💘")
    @app_commands.describe(
        uye="The member you want to match with",
        rastgele="Type 'random' to match the member with a random person"
    )
    async def ship(
        self,
        interaction: discord.Interaction,
        uye: discord.Member = None,
        rastgele: str = None
    ):
        # ✅ defer() MOVED TO THE TOP — Discord expects a response within 3 seconds
        await interaction.response.defer()

        adaylar = [m for m in interaction.guild.members if not m.bot]

        try:
            if uye is None:
                kisi1 = interaction.user
                havuz = [m for m in adaylar if m.id != kisi1.id]
                if not havuz:
                    return await interaction.followup.send("😢 There is no one else I can match you with!", ephemeral=True)
                kisi2 = random.choice(havuz)

            elif rastgele is None:
                if uye.id == interaction.user.id:
                    return await interaction.followup.send("😅 You can't ship yourself!", ephemeral=True)
                kisi1 = interaction.user
                kisi2 = uye

            else:
                kisi1 = uye
                havuz = [m for m in adaylar if m.id != kisi1.id]
                if not havuz:
                    return await interaction.followup.send("😢 There is no one else I can match you with!", ephemeral=True)
                kisi2 = random.choice(havuz)

            uyum_puani = random.randint(1, 100)

            if uyum_puani >= 90:
                kalpler = "💞💞💞"
                yorum = "A perfect couple! Get married already 💍"
                bar_renk = discord.Color.from_rgb(255, 20, 147)
            elif uyum_puani >= 70:
                kalpler = "💖💖"
                yorum = "There is a wonderful harmony between you! 🥰"
                bar_renk = discord.Color.from_rgb(255, 105, 180)
            elif uyum_puani >= 50:
                kalpler = "💕"
                yorum = "Not bad, you have a chance! 😊"
                bar_renk = discord.Color.from_rgb(255, 182, 193)
            elif uyum_puani >= 30:
                kalpler = "💔"
                yorum = "A bit challenging but not impossible... 😬"
                bar_renk = discord.Color.orange()
            else:
                kalpler = "🖤"
                yorum = "This relationship... would be a disaster. 💀"
                bar_renk = discord.Color.red()

            dolu = round(uyum_puani / 10)
            bar = "█" * dolu + "░" * (10 - dolu)
            isim1 = kisi1.display_name
            isim2 = kisi2.display_name
            ship_adi = isim1[:max(1, len(isim1) // 2)] + \
                isim2[max(0, len(isim2) // 2):]

            # ── Visual ────────────────────────────────────────────────────────────
            # ✅ Fetch both avatars with a single session (faster, safer)
            AV = 160  # avatar size

            async def fetch_avatar(session: aiohttp.ClientSession, url: str) -> Image.Image:
                async with session.get(url) as resp:
                    data = await resp.read()
                img = Image.open(BytesIO(data)).convert("RGBA").resize((AV, AV), Image.LANCZOS)
                mask = Image.new("L", (AV, AV), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, AV, AV), fill=255)
                result = Image.new("RGBA", (AV, AV), (0, 0, 0, 0))
                result.paste(img, (0, 0), mask)
                return result

            async with aiohttp.ClientSession() as session:
                av1, av2 = await asyncio.gather(
                    fetch_avatar(session, kisi1.display_avatar.with_format("png").with_size(256).url),
                    fetch_avatar(session, kisi2.display_avatar.with_format("png").with_size(256).url),
                )

            # Color
            if uyum_puani >= 70:
                bg_color = (255, 225, 235)
                accent   = (210, 60, 100)
            elif uyum_puani >= 40:
                bg_color = (255, 240, 220)
                accent   = (200, 110, 50)
            else:
                bg_color = (220, 220, 235)
                accent   = (90, 90, 150)

            # Canvas dimensions — calculate so everything fits
            # Layout: [20px pad] [AV=160] [20px gap] [mid=120] [20px gap] [AV=160] [20px pad] = 520px
            # Height: 20 pad + 160 avatar + 20 name area + 16 name text + 20 bar area + 14 bar + 20 pad = 270px
            W, H = 520, 270

            canvas = Image.new("RGB", (W, H), bg_color)
            draw = ImageDraw.Draw(canvas)

            # Load font
            try:
                font_pct  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
                font_name = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
                font_bar  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
            except:
                font_pct = font_name = font_bar = ImageFont.load_default()

            # Positions
            AV_Y    = 20                      # avatar top edge
            AV1_X   = 20                      # left avatar left edge
            AV2_X   = W - 20 - AV            # right avatar left edge
            MID_X   = W // 2                  # middle point
            NAME_Y  = AV_Y + AV + 10         # name y (below avatar + 10px gap)
            BAR_Y   = NAME_Y + 22            # bar y (below name + 22px)
            BAR_H   = 12
            BAR_X   = 20
            BAR_W   = W - 40

            # Avatar shadows
            shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sd = ImageDraw.Draw(shadow)
            sd.ellipse((AV1_X+4, AV_Y+4, AV1_X+AV+4, AV_Y+AV+4), fill=(0, 0, 0, 50))
            sd.ellipse((AV2_X+4, AV_Y+4, AV2_X+AV+4, AV_Y+AV+4), fill=(0, 0, 0, 50))
            canvas.paste(Image.alpha_composite(
                Image.new("RGBA", (W, H), (*bg_color, 255)), shadow
            ).convert("RGB"), (0, 0))
            draw = ImageDraw.Draw(canvas)

            # Paste avatars
            canvas.paste(av1, (AV1_X, AV_Y), av1)
            canvas.paste(av2, (AV2_X, AV_Y), av2)
            draw = ImageDraw.Draw(canvas)

            # Middle heart
            try:
                font_heart = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            except:
                font_heart = ImageFont.load_default()

            HEART_Y = AV_Y + AV // 2 - 30
            draw.text((MID_X+2, HEART_Y+2), "♥", font=font_heart, fill=(*accent, 60), anchor="mt")
            draw.text((MID_X, HEART_Y), "♥", font=font_heart, fill=accent, anchor="mt")

            # Score pill
            pct_txt = f"{uyum_puani}%"
            pb = draw.textbbox((0, 0), pct_txt, font=font_pct)
            pw, ph = pb[2]-pb[0], pb[3]-pb[1]
            pill_pad = 10
            pill_x1 = MID_X - pw//2 - pill_pad
            pill_y1 = HEART_Y + 54
            pill_x2 = MID_X + pw//2 + pill_pad
            pill_y2 = pill_y1 + ph + 8
            draw.rounded_rectangle((pill_x1, pill_y1, pill_x2, pill_y2), radius=12, fill=accent)
            draw.text((MID_X, pill_y1 + 4), pct_txt, font=font_pct, fill=(255, 255, 255), anchor="mt")

            # Names — centered under avatar
            name1 = kisi1.display_name[:16]
            name2 = kisi2.display_name[:16]
            draw.text((AV1_X + AV//2, NAME_Y), name1, font=font_name, fill=accent, anchor="mt")
            draw.text((AV2_X + AV//2, NAME_Y), name2, font=font_name, fill=accent, anchor="mt")

            # Bar background
            draw.rounded_rectangle((BAR_X, BAR_Y, BAR_X+BAR_W, BAR_Y+BAR_H), radius=6, fill=(0,0,0,40))
            # Bar fill
            dolu_w = max(int(BAR_W * uyum_puani / 100), BAR_H)
            draw.rounded_rectangle((BAR_X, BAR_Y, BAR_X+dolu_w, BAR_Y+BAR_H), radius=6, fill=accent)

            buf = BytesIO()
            canvas.save(buf, format="PNG")
            buf.seek(0)
            file = discord.File(buf, filename="ship.png")

            # ── Embed ─────────────────────────────────────────────────────────────
            embed = discord.Embed(
                title=f"💘 Ship: {ship_adi}", color=bar_renk, timestamp=discord.utils.utcnow())
            embed.add_field(
                name="Couple",       value=f"{kisi1.mention} {kalpler} {kisi2.mention}", inline=False)
            embed.add_field(
                name="Match Score", value=f"`{bar}` **{uyum_puani}%**",                 inline=False)
            embed.add_field(name="Comment",      value=yorum,
                            inline=False)
            embed.set_image(url="attachment://ship.png")
            embed.set_footer(
                text=f"Destiny chose you! | {interaction.guild.name}", icon_url=kisi2.display_avatar.url)

            await interaction.followup.send(embed=embed, file=file)

        except Exception as e:
            # ✅ If there is an error, interaction won't hang, user gets informed
            print(f"Ship command error: {e}")
            await interaction.followup.send("❌ An error occurred, please try again!", ephemeral=True)

@bot.tree.command(name="setuppanel", description="Creates the private room panel in the channel 🎙️")
@app_commands.checks.has_permissions(administrator=True)
async def panelkur(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    kanal = bot.get_channel(PANEL_CHANNEL_ID)
    if not kanal or not isinstance(kanal, discord.TextChannel):
        return await interaction.followup.send("❌ Panel channel ID is invalid.", ephemeral=True)

    embed = BotUI.embed(title="⚔️ PRIVATE ROOM CONTROL", color=BotUI.COLOR_PREMIUM)
    embed.description = (
        "Hello esteemed **Z 3 İ T T** members,\n"
        "You can create your own private voice channel on our server! 🎵✨\n\n"
        "> 🔊 By entering the **Create private room👑** voice channel, you can instantly create your own voice channel.\n"
        "After creating your channel, you can manage it however you like using the buttons below.\n\n"
    )

    embed.add_field(name="⚙️ Update Your Room", value=(
        "💀 **Hide & Lock:** Hides the room and closes it to entries.\n"
        "✏️ **Change Name:** Updates your room's name.\n"
        "⬆️ **Update Limit:** Sets the capacity of your room."
    ), inline=False)

    embed.add_field(name="🛡️ Access Control", value=(
        "🔒 **Lock:** Closes your room completely to the outside.\n"
        "👥 **Allow:** Allows a specified user to enter the room.\n"
        "🚫 **Ban:** Bans a specified user from entering the room."
    ), inline=False)

    embed.add_field(name="✨ Other Settings", value=(
        "👁️ **Make Invisible:** Hides your room from the list.\n"
        "👑 **Transfer:** Transfers the room ownership to someone else in the room.\n"
        "🗑️ **Delete Room:** Permanently deletes your room."
    ), inline=False)

    embed.set_footer(text="Private Room System #z3ittANİSTAN")

    await kanal.send(embed=embed, view=RoomPanelView())
    await interaction.followup.send(BotUI.success("Room control panel has been set up successfully."), ephemeral=True)
# ─────────────────────────────────────────────────────────────────────────────
# GIVEAWAY SYSTEM
# ─────────────────────────────────────────────────────────────────────────────

GIVEAWAY_FILE = "cekilisler.json"


def save_giveaways():
    """Save giveaways to disk (so they aren't lost on bot restart)."""
    kayit = {}
    for mid, v in aktif_cekilisler.items():
        kayit[str(mid)] = {**v, "bitis": v["bitis"].isoformat()}
    with open(GIVEAWAY_FILE, "w") as f:
        json.dump(kayit, f, indent=4)


def load_giveaways():
    """Load giveaways from disk."""
    if not os.path.exists(GIVEAWAY_FILE):
        return
    with open(GIVEAWAY_FILE, "r") as f:
        try:
            kayit = json.load(f)
        except:
            return
    for mid_str, v in kayit.items():
        v["bitis"] = datetime.fromisoformat(v["bitis"])
        aktif_cekilisler[int(mid_str)] = v


def sure_parse(sure: str) -> int | None:
    """Converts a time string to seconds. Returns None if invalid."""
    sure_map = {"s": 1, "d": 60, "h": 3600, "m": 86400}
    sure = sure.strip().lower()
    if len(sure) < 2 or sure[-1] not in sure_map:
        return None
    try:
        deger = int(sure[:-1])
        return deger * sure_map[sure[-1]] if deger > 0 else None
    except ValueError:
        return None


def build_giveaway_embed(veri: dict, bitti: bool = False) -> discord.Embed:
    renk = discord.Color.red() if bitti else discord.Color.green()
    baslik = f"🎉 GIVEAWAY {'ENDED' if bitti else 'STARTED'}!"
    embed = discord.Embed(title=baslik, color=renk, timestamp=discord.utils.utcnow())
    embed.add_field(name="🏆 Prize", value=f"**{veri['odul']}**", inline=False)
    embed.add_field(name="🎟️ Winners Count", value=f"**{veri['kazanan_sayisi']}** people", inline=True)
    embed.add_field(name="👥 Participants", value=f"**{len(veri['katilimcilar'])}** people", inline=True)

    if not bitti:
        bitis_ts = int(veri["bitis"].timestamp())
        embed.add_field(name="⏰ Ends", value=f"<t:{bitis_ts}:R>", inline=False)
        embed.add_field(name="📅 End Date", value=f"<t:{bitis_ts}:F>", inline=False)

    embed.set_footer(text=f"Hosted by: {veri['duzenleyen']} | Giveaway System")
    return embed


async def cekilisi_bitir(mesaj_id: int, veri: dict):
    """Ends the giveaway, selects winners, updates the embed."""
    kanal = bot.get_channel(veri["kanal_id"])
    if not kanal:
        return

    try:
        mesaj = await kanal.fetch_message(mesaj_id)
    except (discord.NotFound, discord.HTTPException):
        return

    katilimcilar = veri["katilimcilar"]
    k_sayisi = min(veri["kazanan_sayisi"], len(katilimcilar))

    if katilimcilar and k_sayisi > 0:
        kazananlar = random.sample(katilimcilar, k_sayisi)
        k_mentions = " ".join([f"<@{uid}>" for uid in kazananlar])
        sonuc_txt = f"🎊 Congratulations! They won **{veri['odul']}**:\n{k_mentions}"
    else:
        k_mentions = "—"
        sonuc_txt = "😔 Could not select a winner due to not enough participants."

    bitis_embed = build_giveaway_embed(veri, bitti=True)
    bitis_embed.add_field(name="🏅 Winners", value=k_mentions, inline=False)

    bitis_view = discord.ui.View()
    bitis_view.add_item(discord.ui.Button(
        label="🎉 Giveaway Ended", style=discord.ButtonStyle.grey, disabled=True
    ))

    try:
        await mesaj.edit(embed=bitis_embed, view=bitis_view)
        await kanal.send(
            content=f"🎉 **GIVEAWAY ENDED!** — {sonuc_txt}",
            reference=mesaj
        )
    except (discord.NotFound, discord.HTTPException):
        pass

    await send_log(
        kanal.guild,
        f"🎉 Giveaway ended: **{veri['odul']}** | Winners: {k_mentions} | Hosted by: {veri['duzenleyen']}",
        discord.Color.gold()
    )


class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎉 Join",
        style=discord.ButtonStyle.green,
        custom_id="giveaway_join"
    )
    async def katil(self, interaction: discord.Interaction, button: discord.ui.Button):
        mesaj_id = interaction.message.id
        if mesaj_id not in aktif_cekilisler:
            return await interaction.response.send_message(
                "❌ This giveaway is no longer active.", ephemeral=True
            )

        veri = aktif_cekilisler[mesaj_id]
        katilimci = str(interaction.user.id)

        if katilimci in veri["katilimcilar"]:
            veri["katilimcilar"].remove(katilimci)
            mesaj = "💨 You have **left** the giveaway."
        else:
            veri["katilimcilar"].append(katilimci)
            mesaj = "✅ You have **joined** the giveaway! Good luck 🍀"

        save_giveaways()

        # Update both button + embed
        button.label = f"🎉 Join ({len(veri['katilimcilar'])})"
        yeni_embed = build_giveaway_embed(veri)
        await interaction.response.send_message(mesaj, ephemeral=True)
        await interaction.message.edit(embed=yeni_embed, view=self)

    @discord.ui.button(
        label="👥 Participants",
        style=discord.ButtonStyle.blurple,
        custom_id="giveaway_list"
    )
    async def liste(self, interaction: discord.Interaction, button: discord.ui.Button):
        mesaj_id = interaction.message.id
        if mesaj_id not in aktif_cekilisler:
            return await interaction.response.send_message("❌ Giveaway not found.", ephemeral=True)

        veri = aktif_cekilisler[mesaj_id]
        if not veri["katilimcilar"]:
            return await interaction.response.send_message("📭 No one has joined yet.", ephemeral=True)

        # If there are more than 25 people, do not show all, there is a Discord limit
        kisiler = "\n".join([f"• <@{uid}>" for uid in veri["katilimcilar"][:25]])
        if len(veri["katilimcilar"]) > 25:
            kisiler += f"\n... and {len(veri['katilimcilar']) - 25} more people"

        embed = discord.Embed(
            title=f"👥 Participants ({len(veri['katilimcilar'])} people)",
            description=kisiler,
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
@tasks.loop(seconds=15)
async def giveaway_kontrol():
    biten = [mid for mid, v in list(aktif_cekilisler.items())
             if discord.utils.utcnow() >= v["bitis"]]
    for mesaj_id in biten:
        veri = aktif_cekilisler.pop(mesaj_id)
        save_giveaways()
        await cekilisi_bitir(mesaj_id, veri)


@tasks.loop(time=dt_time(hour=21, minute=0, tzinfo=timezone.utc))  # Midnight in Turkey time (UTC+3 = 21:00 UTC)
async def gunluk_ses_siralama():
    """Updates 3 different leaderboards in the leaderboard channel every day at midnight (TRT 00:00)."""
    ses_data = load_ses()
    
    # Current date (TRT)
    tz = timezone(timedelta(hours=3))
    simdi = datetime.now(tz).strftime("%d.%m.%Y %H:%M")

    for guild in bot.guilds:
        kanal = discord.utils.get(guild.text_channels, name=LIDERLIK_KANAL_ADI)
        if not kanal:
            continue
            
        thumb_url = guild.icon.url if guild.icon else None

        # 1. VOICE LEADERBOARD
        ses_skorlar = []
        for uid_str, info in ses_data.items():
            toplam = info["toplam_saniye"]
            uid = int(uid_str)
            if uid in ses_giris_takip:
                toplam += int(time.time() - ses_giris_takip[uid])
            ses_skorlar.append((uid, toplam))
        ses_skorlar.sort(key=lambda x: x[1], reverse=True)

        ses_satirlar = []
        i = 1
        for uid, sn in ses_skorlar:
            if i > 10: break
            m = guild.get_member(uid)
            if not m: continue
            dakika = sn // 60
            saat = dakika // 60
            kalan_dakika = dakika % 60
            sure_str = f"{saat} hours {kalan_dakika} mins" if saat > 0 else f"{kalan_dakika} mins"
            ses_satirlar.append(f"`{i}.` {m.mention}: `{sure_str}`")
            i += 1

        embed_ses = BotUI.embed(
            title="🔊 Voice Leaderboard",
            desc="\n".join(ses_satirlar) or "No data yet.",
            color=0x2b2d31
        )
        if thumb_url: embed_ses.set_thumbnail(url=thumb_url)
        embed_ses.add_field(name="Last edited", value=f"`{simdi}`", inline=False)

        # 2. MESSAGE LEADERBOARD
        mesaj_skorlar = []
        mesaj_verileri = siralama_verileri.get("mesajlar", {})
        for uid_str, sayi in mesaj_verileri.items():
            mesaj_skorlar.append((int(uid_str), sayi))
        mesaj_skorlar.sort(key=lambda x: x[1], reverse=True)

        mesaj_satirlar = []
        i = 1
        for uid, sayi in mesaj_skorlar:
            if i > 10: break
            m = guild.get_member(uid)
            if not m: continue
            mesaj_satirlar.append(f"`{i}.` {m.mention}: `{sayi} messages`")
            i += 1

        embed_mesaj = BotUI.embed(
            title="💬 Message Leaderboard",
            desc="\n".join(mesaj_satirlar) or "No data yet.",
            color=0x2b2d31
        )
        if thumb_url: embed_mesaj.set_thumbnail(url=thumb_url)
        embed_mesaj.add_field(name="Last edited", value=f"`{simdi}`", inline=False)

        # 3. STREAM LEADERBOARD
        yayin_skorlar = []
        yayin_verileri = siralama_verileri.get("yayin", {})
        for uid_str, sn in yayin_verileri.items():
            toplam = sn
            uid = int(uid_str)
            if uid in yayin_giris_takip:
                toplam += int(time.time() - yayin_giris_takip[uid])
            yayin_skorlar.append((uid, toplam))
        yayin_skorlar.sort(key=lambda x: x[1], reverse=True)

        yayin_satirlar = []
        i = 1
        for uid, sn in yayin_skorlar:
            if i > 10: break
            m = guild.get_member(uid)
            if not m: continue
            dakika = sn // 60
            saat = dakika // 60
            kalan_dakika = dakika % 60
            sure_str = f"{saat} hours {kalan_dakika} mins" if saat > 0 else f"{kalan_dakika} mins"
            yayin_satirlar.append(f"`{i}.` {m.mention}: `{sure_str}`")
            i += 1

        embed_yayin = BotUI.embed(
            title="💻 Stream Leaderboard",
            desc="\n".join(yayin_satirlar) or "No data yet.",
            color=0x2b2d31
        )
        if thumb_url: embed_yayin.set_thumbnail(url=thumb_url)
        embed_yayin.add_field(name="Last edited", value=f"`{simdi}`", inline=False)

        # SEND / UPDATE MESSAGES
        siralama_verileri.setdefault("mesaj_ids", {})
        
        async def mesaj_isleme(mesaj_tipi, embed_obj):
            mesaj_id = siralama_verileri["mesaj_ids"].get(mesaj_tipi)
            if mesaj_id:
                try:
                    msg = await kanal.fetch_message(mesaj_id)
                    await msg.edit(embed=embed_obj)
                    return
                except discord.NotFound:
                    siralama_verileri["mesaj_ids"].pop(mesaj_tipi, None)
                except Exception as e:
                    print(f"Could not update leaderboard message ({mesaj_tipi}): {e}")
            # Send a new one if not found or if there's an error
            try:
                msg = await kanal.send(embed=embed_obj)
                siralama_verileri["mesaj_ids"][mesaj_tipi] = msg.id
                save_siralama()
            except Exception as e:
                print(f"Could not send leaderboard message ({mesaj_tipi}): {e}")

        await mesaj_isleme("mesaj", embed_mesaj)
        await mesaj_isleme("ses", embed_ses)
        await mesaj_isleme("yayin", embed_yayin)


@bot.tree.command(name="leaderboard", description="Sends the current leaderboard (voice, message, stream) to the leaderboard channel")
async def leaderboard_komut(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator and interaction.user.id not in BEYAZ_LISTE:
        return await interaction.response.send_message("🚫 You don't have permission to use this command!", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild

    kanal = discord.utils.get(guild.text_channels, name=LIDERLIK_KANAL_ADI)
    if not kanal:
        return await interaction.followup.send(
            BotUI.error(f"Could not find a channel named `{LIDERLIK_KANAL_ADI}`! Please create a channel with this name on the server."),
            ephemeral=True
        )

    ses_data = load_ses()
    tz = timezone(timedelta(hours=3))
    simdi = datetime.now(tz).strftime("%d.%m.%Y %H:%M")
    thumb_url = guild.icon.url if guild.icon else None

    # VOICE
    ses_skorlar = []
    for uid_str, info in ses_data.items():
        toplam = info["toplam_saniye"]
        uid = int(uid_str)
        if uid in ses_giris_takip:
            toplam += int(time.time() - ses_giris_takip[uid])
        ses_skorlar.append((uid, toplam))
    ses_skorlar.sort(key=lambda x: x[1], reverse=True)

    ses_satirlar = []
    i = 1
    for uid, sn in ses_skorlar:
        if i > 10: break
        m = guild.get_member(uid)
        if not m: continue
        dakika = sn // 60; saat = dakika // 60; kalan_dakika = dakika % 60
        sure_str = f"{saat} hours {kalan_dakika} mins" if saat > 0 else f"{kalan_dakika} mins"
        ses_satirlar.append(f"`{i}.` {m.mention}: `{sure_str}`")
        i += 1

    lb_embed_ses = BotUI.embed(title="🔊 Voice Leaderboard", desc="\n".join(ses_satirlar) or "No data yet.", color=0x2b2d31)
    if thumb_url: lb_embed_ses.set_thumbnail(url=thumb_url)
    lb_embed_ses.add_field(name="Last edited", value=f"`{simdi}`", inline=False)

    # MESSAGE
    mesaj_skorlar = sorted([(int(k), v) for k, v in siralama_verileri.get("mesajlar", {}).items()], key=lambda x: x[1], reverse=True)
    mesaj_satirlar = []
    i = 1
    for uid, sayi in mesaj_skorlar:
        if i > 10: break
        m = guild.get_member(uid)
        if not m: continue
        mesaj_satirlar.append(f"`{i}.` {m.mention}: `{sayi} messages`")
        i += 1

    lb_embed_mesaj = BotUI.embed(title="💬 Message Leaderboard", desc="\n".join(mesaj_satirlar) or "No data yet.", color=0x2b2d31)
    if thumb_url: lb_embed_mesaj.set_thumbnail(url=thumb_url)
    lb_embed_mesaj.add_field(name="Last edited", value=f"`{simdi}`", inline=False)

    # STREAM
    yayin_skorlar = []
    for uid_str, sn in siralama_verileri.get("yayin", {}).items():
        toplam = sn
        uid = int(uid_str)
        if uid in yayin_giris_takip:
            toplam += int(time.time() - yayin_giris_takip[uid])
        yayin_skorlar.append((uid, toplam))
    yayin_skorlar.sort(key=lambda x: x[1], reverse=True)

    yayin_satirlar = []
    i = 1
    for uid, sn in yayin_skorlar:
        if i > 10: break
        m = guild.get_member(uid)
        if not m: continue
        dakika = sn // 60; saat = dakika // 60; kalan_dakika = dakika % 60
        sure_str = f"{saat} hours {kalan_dakika} mins" if saat > 0 else f"{kalan_dakika} mins"
        yayin_satirlar.append(f"`{i}.` {m.mention}: `{sure_str}`")
        i += 1

    lb_embed_yayin = BotUI.embed(title="💻 Stream Leaderboard", desc="\n".join(yayin_satirlar) or "No data yet.", color=0x2b2d31)
    if thumb_url: lb_embed_yayin.set_thumbnail(url=thumb_url)
    lb_embed_yayin.add_field(name="Last edited", value=f"`{simdi}`", inline=False)

    siralama_verileri.setdefault("mesaj_ids", {})

    async def lb_gonder(mesaj_tipi, embed_obj):
        mesaj_id = siralama_verileri["mesaj_ids"].get(mesaj_tipi)
        if mesaj_id:
            try:
                msg = await kanal.fetch_message(mesaj_id)
                await msg.edit(embed=embed_obj)
                return
            except discord.NotFound:
                siralama_verileri["mesaj_ids"].pop(mesaj_tipi, None)
            except Exception:
                pass
        try:
            msg = await kanal.send(embed=embed_obj)
            siralama_verileri["mesaj_ids"][mesaj_tipi] = msg.id
            save_siralama()
        except Exception as e:
            print(f"[/leaderboard] Could not send message ({mesaj_tipi}): {e}")

    await lb_gonder("mesaj", lb_embed_mesaj)
    await lb_gonder("ses", lb_embed_ses)
    await lb_gonder("yayin", lb_embed_yayin)

    await interaction.followup.send(
        BotUI.success(f"Leaderboards have been sent / updated in the <#{kanal.id}> channel."),
        ephemeral=True
    )


@bot.tree.command(name="giveaway", description="Starts a new giveaway (Admin / Whitelist)")
@app_commands.describe(
    odul="Giveaway prize",
    sure="Duration: 30s=seconds, 5d=minutes, 2h=hours, 1m=days",
    kazanan="How many winners (default 1)",
    kanal="Channel to host the giveaway in (empty = this channel)"
)
async def giveaway(
    interaction: discord.Interaction,
    odul: str,
    sure: str,
    kazanan: int = 1,
    kanal: discord.TextChannel = None
):
    if (interaction.user.id != OZEL_SAHIP_ID
            and interaction.user.id not in BEYAZ_LISTE
            and not interaction.user.guild_permissions.administrator):
        return await interaction.response.send_message("🚫 You don't have permission!", ephemeral=True)
    toplam_sn = sure_parse(sure)
    if not toplam_sn:
        return await interaction.response.send_message(
            "❌ Invalid duration!\nExamples: `30s` (seconds) `5d` (minutes) `2h` (hours) `1m` (days)",
            ephemeral=True
        )

    if kazanan < 1:
        return await interaction.response.send_message("❌ Winner count must be at least 1!", ephemeral=True)

    hedef_kanal = kanal or interaction.channel
    veri = {
        "odul": odul,
        "bitis": discord.utils.utcnow() + timedelta(seconds=toplam_sn),
        "kazanan_sayisi": kazanan,
        "katilimcilar": [],
        "kanal_id": hedef_kanal.id,
        "duzenleyen": interaction.user.display_name,
    }

    embed = build_giveaway_embed(veri)
    mesaj = await hedef_kanal.send(embed=embed, view=GiveawayView())

    aktif_cekilisler[mesaj.id] = veri
    save_giveaways()

    await interaction.response.send_message(
        f"✅ Giveaway started in **{hedef_kanal.mention}**!", ephemeral=True
    )
    await send_log(
        interaction.guild,
        f"🎉 New Giveaway: **{odul}** | Duration: `{sure}` | Winners: {kazanan} | {interaction.user.mention}",
        discord.Color.gold()
    )


@bot.tree.command(name="cancelgiveaway", description="Cancels an active giveaway")
@app_commands.describe(mesaj_id="Message ID of the giveaway to cancel")
async def giveaway_iptal(interaction: discord.Interaction, mesaj_id: str):
    if (interaction.user.id != OZEL_SAHIP_ID
            and interaction.user.id not in BEYAZ_LISTE
            and not interaction.user.guild_permissions.administrator):
        return await interaction.response.send_message("🚫 You don't have permission!", ephemeral=True)

    try:
        mid = int(mesaj_id)
    except ValueError:
        return await interaction.response.send_message("❌ Enter a valid message ID!", ephemeral=True)

    if mid not in aktif_cekilisler:
        return await interaction.response.send_message("❌ Active giveaway not found!", ephemeral=True)

    veri = aktif_cekilisler.pop(mid)
    save_giveaways()

    kanal = bot.get_channel(veri["kanal_id"])
    if kanal:
        try:
            mesaj = await kanal.fetch_message(mid)
            iptal_embed = build_giveaway_embed(veri, bitti=True)
            iptal_embed.title = "🚫 GIVEAWAY CANCELLED"
            iptal_embed.color = discord.Color.red()
            iptal_view = discord.ui.View()
            iptal_view.add_item(discord.ui.Button(
                label="❌ Cancelled", style=discord.ButtonStyle.grey, disabled=True
            ))
            await mesaj.edit(embed=iptal_embed, view=iptal_view)
            await kanal.send(
                f"🚫 The **{veri['odul']}** giveaway was cancelled by {interaction.user.mention}.",
                reference=mesaj
            )
        except (discord.NotFound, discord.HTTPException):
            pass

    await interaction.response.send_message("✅ Giveaway cancelled.", ephemeral=True)
    await send_log(
        interaction.guild,
        f"🚫 Giveaway Cancelled: **{veri['odul']}** | {interaction.user.mention}",
        discord.Color.red()
    )


@bot.tree.command(name="listgiveaways", description="Lists active giveaways")
async def giveaway_listele(interaction: discord.Interaction):
    if not aktif_cekilisler:
        return await interaction.response.send_message("📭 There are no active giveaways right now.", ephemeral=True)

    embed = discord.Embed(
        title="🎉 Active Giveaways",
        color=discord.Color.green(),
        timestamp=discord.utils.utcnow()
    )
    for mid, v in aktif_cekilisler.items():
        embed.add_field(
            name=f"🏆 {v['odul']}",
            value=(
                f"Participants: **{len(v['katilimcilar'])}**\n"
                f"Winners: **{v['kazanan_sayisi']}**\n"
                f"Ends: <t:{int(v['bitis'].timestamp())}:R>\n"
                f"[Go to Message](https://discord.com/channels/{interaction.guild.id}/{v['kanal_id']}/{mid})"
            ),
            inline=True
        )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="rerollgiveaway", description="Rerolls a finished giveaway")
@app_commands.describe(
    mesaj_id="Message ID of the giveaway to reroll",
    kanal="Channel where the message is located (empty = this channel)"
)
async def giveaway_yeniden(
    interaction: discord.Interaction,
    mesaj_id: str,
    kanal: discord.TextChannel = None
):
    if (interaction.user.id != OZEL_SAHIP_ID
            and interaction.user.id not in BEYAZ_LISTE
            and not interaction.user.guild_permissions.administrator):
        return await interaction.response.send_message("🚫 You don't have permission!", ephemeral=True)

    # Search in active giveaways
    try:
        mid = int(mesaj_id)
    except ValueError:
        return await interaction.response.send_message("❌ Enter a valid message ID!", ephemeral=True)

    if mid not in aktif_cekilisler:
        return await interaction.response.send_message(
            "❌ There is no active giveaway with this ID. Rerolls can only be done on active giveaways.",
            ephemeral=True
        )

    veri = aktif_cekilisler[mid]
    katilimcilar = veri["katilimcilar"]
    k_sayisi = min(veri["kazanan_sayisi"], len(katilimcilar))

    if not katilimcilar or k_sayisi == 0:
        return await interaction.response.send_message("❌ Not enough participants!", ephemeral=True)

    kazananlar = random.sample(katilimcilar, k_sayisi)
    k_mentions = " ".join([f"<@{uid}>" for uid in kazananlar])

    await interaction.response.send_message(
        f"🔁 **Rerolled!** — New winners for **{veri['odul']}**:\n{k_mentions}"
    )
    await send_log(
        interaction.guild,
        f"🔁 Reroll: **{veri['odul']}** | Winners: {k_mentions} | {interaction.user.mention}",
        discord.Color.gold()
    )





# ══════════════════════════════════════════════════════════════════════════════
# BACKUP COG
# ══════════════════════════════════════════════════════════════════════════════
class YedekCog(commands.Cog):
    yedek_group = app_commands.Group(name="backup", description="Server backup system (Whitelist)")

    def _beyaz_liste_kontrol(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id in BEYAZ_LISTE or interaction.user.id == interaction.guild.owner_id

    # ── /backup create ─────────────────────────────────────────────────────────────
    @yedek_group.command(name="create", description="Backups the server's channels, categories, and role structure")
    async def yedek_al(self, interaction: discord.Interaction):
        if not self._beyaz_liste_kontrol(interaction):
            return await interaction.response.send_message("🚫 You don't have permission to use this command!", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        # Save roles (manageable ones)
        roller = []
        for rol in guild.roles:
            if rol.is_default() or rol.managed:
                continue
            roller.append({
                "id": rol.id,
                "name": rol.name,
                "color": rol.color.value,
                "hoist": rol.hoist,
                "mentionable": rol.mentionable,
                "position": rol.position,
                "permissions": rol.permissions.value
            })

        # Save categories and channels
        kategoriler = []
        for kat in guild.categories:
            kat_izinler = []
            for target, overwrite in kat.overwrites.items():
                allow, deny = overwrite.pair()
                kat_izinler.append({
                    "id": target.id,
                    "type": "role" if isinstance(target, discord.Role) else "member",
                    "allow": allow.value,
                    "deny": deny.value
                })
            kanallar = []
            for kanal in kat.channels:
                kanal_izinler = []
                for target, overwrite in kanal.overwrites.items():
                    allow, deny = overwrite.pair()
                    kanal_izinler.append({
                        "id": target.id,
                        "type": "role" if isinstance(target, discord.Role) else "member",
                        "allow": allow.value,
                        "deny": deny.value
                    })
                kanallar.append({
                    "id": kanal.id,
                    "name": kanal.name,
                    "type": str(kanal.type),
                    "position": kanal.position,
                    "overwrites": kanal_izinler,
                    "topic": getattr(kanal, "topic", None),
                    "slowmode": getattr(kanal, "slowmode_delay", 0),
                    "nsfw": getattr(kanal, "nsfw", False)
                })
            kategoriler.append({
                "id": kat.id,
                "name": kat.name,
                "position": kat.position,
                "overwrites": kat_izinler,
                "kanallar": kanallar
            })

        # Save channels without a category
        kategorisiz = []
        for kanal in guild.channels:
            if kanal.category is not None:
                continue
            if isinstance(kanal, discord.CategoryChannel):
                continue
            kanal_izinler = []
            for target, overwrite in kanal.overwrites.items():
                allow, deny = overwrite.pair()
                kanal_izinler.append({
                    "id": target.id,
                    "type": "role" if isinstance(target, discord.Role) else "member",
                    "allow": allow.value,
                    "deny": deny.value
                })
            kategorisiz.append({
                "id": kanal.id,
                "name": kanal.name,
                "type": str(kanal.type),
                "position": getattr(kanal, "position", 0),
                "overwrites": kanal_izinler
            })

        yedek_id = str(int(discord.utils.utcnow().timestamp()))
        yedek = {
            "tarih": discord.utils.utcnow().strftime("%d.%m.%Y %H:%M"),
            "alan": interaction.user.name,
            "roller": roller,
            "kategoriler": kategoriler,
            "kategorisiz": kategorisiz
        }

        data = load_yedek()

        # Keep max 5 backups
        if len(data) >= 5:
            en_eski = sorted(data.keys())[0]
            del data[en_eski]

        data[yedek_id] = yedek
        save_yedek(data)

        embed = discord.Embed(
            title="✅ Backup Created",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Backup ID", value=f"`{yedek_id}`", inline=True)
        embed.add_field(name="Role Count", value=str(len(roller)), inline=True)
        embed.add_field(name="Category Count", value=str(len(kategoriler)), inline=True)
        embed.add_field(name="Channel Count", value=str(sum(len(k["kanallar"]) for k in kategoriler) + len(kategorisiz)), inline=True)
        await interaction.followup.send(embed=embed, ephemeral=True)
        await send_log(guild, f"💾 Server Backup Created | ID: `{yedek_id}` | {interaction.user.mention}", discord.Color.green())

    # ── /backup list ──────────────────────────────────────────────────────────
    @yedek_group.command(name="list", description="Lists saved backups")
    async def yedek_liste(self, interaction: discord.Interaction):
        if not self._beyaz_liste_kontrol(interaction):
            return await interaction.response.send_message("🚫 You don't have permission to use this command!", ephemeral=True)

        data = load_yedek()
        if not data:
            return await interaction.response.send_message("📭 No saved backups.", ephemeral=True)

        embed = discord.Embed(title="💾 Saved Backups", color=discord.Color.blurple())
        for yid, yedek in sorted(data.items(), reverse=True):
            rol_say = len(yedek.get("roller", []))
            kat_say = len(yedek.get("kategoriler", []))
            kanal_say = sum(len(k["kanallar"]) for k in yedek.get("kategoriler", [])) + len(yedek.get("kategorisiz", []))
            embed.add_field(
                name=f"📅 {yedek['tarih']} | ID: `{yid}`",
                value=f"Created by: **{yedek['alan']}** | {rol_say} roles, {kat_say} categories, {kanal_say} channels",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /backup load ──────────────────────────────────────────────────────────
    @yedek_group.command(name="load", description="Loads the selected backup (fixes missing/changed channels and roles)")
    @app_commands.describe(
        yedek_id="ID of the backup to load (view with /backup list)",
        eski_kanallari_sil="Should old channels be deleted?"
    )
    @app_commands.choices(eski_kanallari_sil=[
        app_commands.Choice(name="Yes", value="evet"),
        app_commands.Choice(name="No", value="hayir")
    ])
    async def yedek_yukle(self, interaction: discord.Interaction, yedek_id: str, eski_kanallari_sil: str = "hayir"):
        if not self._beyaz_liste_kontrol(interaction):
            return await interaction.response.send_message("🚫 You don't have permission to use this command!", ephemeral=True)

        data = load_yedek()
        if yedek_id not in data:
            return await interaction.response.send_message("❌ Backup with this ID not found!", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        yedek = data[yedek_id]

        olusturulan_rol = 0
        olusturulan_kat = 0
        olusturulan_kanal = 0
        duzeltilen_izin = 0

        # ── DELETE CHANNELS (OPTIONAL) ──────────────────────────────────
        if eski_kanallari_sil == "evet":
            for c in guild.channels:
                if c.id != interaction.channel.id:
                    try:
                        await c.delete()
                    except:
                        pass
            await asyncio.sleep(2)

        # ── LOAD ROLES ─────────────────────────────────────────────────
        mevcut_rol_isimleri = {r.name for r in guild.roles}
        rol_id_map = {r.id: r for r in guild.roles}

        for rol_data in sorted(yedek.get("roller", []), key=lambda x: x["position"], reverse=True):
            mevcut = discord.utils.get(guild.roles, name=rol_data["name"])
            if mevcut is None:
                try:
                    await guild.create_role(
                        name=rol_data["name"],
                        color=discord.Color(rol_data["color"]),
                        hoist=rol_data["hoist"],
                        mentionable=rol_data["mentionable"],
                        permissions=discord.Permissions(rol_data["permissions"])
                    )
                    olusturulan_rol += 1
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"[yedek_yukle] Error creating role ({rol_data['name']}): {e}")
            else:
                # Fix permissions if different
                if mevcut.permissions.value != rol_data["permissions"]:
                    try:
                        await mevcut.edit(permissions=discord.Permissions(rol_data["permissions"]))
                        duzeltilen_izin += 1
                        await asyncio.sleep(0.3)
                    except Exception:
                        pass

        # Refresh guild roles
        await asyncio.sleep(1)
        rol_isim_map = {r.name: r for r in guild.roles}

        def overwrite_olustur(izin_listesi):
            overwrites = {}
            for izin in izin_listesi:
                target = guild.get_role(izin["id"]) or guild.get_member(izin["id"])
                if target is None:
                    target = rol_isim_map.get(next(
                        (r["name"] for r in yedek.get("roller", []) if r["id"] == izin["id"]), None
                    ))
                if target is None:
                    continue
                allow = discord.Permissions(izin["allow"])
                deny = discord.Permissions(izin["deny"])
                ow = discord.PermissionOverwrite.from_pair(allow, deny)
                overwrites[target] = ow
            return overwrites

        # ── LOAD CATEGORIES ────────────────────────────────────────────
        mevcut_kat_isimleri = {c.name: c for c in guild.categories}

        for kat_data in sorted(yedek.get("kategoriler", []), key=lambda x: x["position"]):
            overwrites = overwrite_olustur(kat_data["overwrites"])

            if kat_data["name"] not in mevcut_kat_isimleri:
                try:
                    yeni_kat = await guild.create_category(
                        name=kat_data["name"],
                        overwrites=overwrites
                    )
                    olusturulan_kat += 1
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"[yedek_yukle] Error creating category ({kat_data['name']}): {e}")
                    yeni_kat = None
            else:
                yeni_kat = mevcut_kat_isimleri[kat_data["name"]]
                # Update category permissions
                try:
                    await yeni_kat.edit(overwrites=overwrites)
                    duzeltilen_izin += 1
                    await asyncio.sleep(0.3)
                except Exception:
                    pass

            if yeni_kat is None:
                continue

            # Load channels in category
            mevcut_kanal_isimleri = {c.name: c for c in yeni_kat.channels}
            for kanal_data in sorted(kat_data.get("kanallar", []), key=lambda x: x["position"]):
                kanal_overwrites = overwrite_olustur(kanal_data["overwrites"])

                if kanal_data["name"] not in mevcut_kanal_isimleri:
                    try:
                        tip = kanal_data["type"]
                        if "voice" in tip:
                            await guild.create_voice_channel(
                                name=kanal_data["name"],
                                category=yeni_kat,
                                overwrites=kanal_overwrites
                            )
                        elif "forum" in tip:
                            await guild.create_forum(
                                name=kanal_data["name"],
                                category=yeni_kat,
                                overwrites=kanal_overwrites
                            )
                        else:
                            await guild.create_text_channel(
                                name=kanal_data["name"],
                                category=yeni_kat,
                                overwrites=kanal_overwrites,
                                topic=kanal_data.get("topic"),
                                slowmode_delay=kanal_data.get("slowmode", 0),
                                nsfw=kanal_data.get("nsfw", False)
                            )
                        olusturulan_kanal += 1
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        print(f"[yedek_yukle] Error creating channel ({kanal_data['name']}): {e}")
                else:
                    # Channel exists, fix permissions
                    mevcut_kanal = mevcut_kanal_isimleri[kanal_data["name"]]
                    try:
                        await mevcut_kanal.edit(overwrites=kanal_overwrites)
                        duzeltilen_izin += 1
                        await asyncio.sleep(0.3)
                    except Exception:
                        pass

        embed = discord.Embed(
            title="✅ Backup Loaded",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Roles Created", value=str(olusturulan_rol), inline=True)
        embed.add_field(name="Categories Created", value=str(olusturulan_kat), inline=True)
        embed.add_field(name="Channels Created", value=str(olusturulan_kanal), inline=True)
        embed.add_field(name="Permissions Fixed", value=str(duzeltilen_izin), inline=True)
        await interaction.followup.send(embed=embed, ephemeral=True)
        await send_log(guild, f"♻️ Backup Loaded | ID: `{yedek_id}` | {interaction.user.mention}\n✅ {olusturulan_rol} roles, {olusturulan_kat} categories, {olusturulan_kanal} channels created | {duzeltilen_izin} permissions fixed", discord.Color.orange())

    # ── /backup delete ────────────────────────────────────────────────────────────
    @yedek_group.command(name="delete", description="Deletes the specified backup")
    @app_commands.describe(yedek_id="ID of the backup to delete")
    async def yedek_sil(self, interaction: discord.Interaction, yedek_id: str):
        if not self._beyaz_liste_kontrol(interaction):
            return await interaction.response.send_message("🚫 You don't have permission to use this command!", ephemeral=True)

        data = load_yedek()
        if yedek_id not in data:
            return await interaction.response.send_message("❌ Backup with this ID not found!", ephemeral=True)

        tarih = data[yedek_id]["tarih"]
        del data[yedek_id]
        save_yedek(data)

        await interaction.response.send_message(f"🗑️ Backup from `{tarih}` was deleted.", ephemeral=True)
        await send_log(interaction.guild, f"🗑️ Backup Deleted | ID: `{yedek_id}` | {interaction.user.mention}", discord.Color.red())
# ─────────────────────────────────────────────────────────────────────────────
# REGISTER AND START COGS
# ─────────────────────────────────────────────────────────────────────────────

async def setup_cogs():
    await bot.add_cog(AdminCog())
    await bot.add_cog(EkonomiCog())
    await bot.add_cog(ModerasyonCog())
    await bot.add_cog(SesCog())
    await bot.add_cog(BilgiCog())
    await bot.add_cog(DavetCog())
    await bot.add_cog(YedekCog())

# ══════════════════════════════════════════════════════════════════════════════
# INVITE TRACKER COG
# ══════════════════════════════════════════════════════════════════════════════
class DavetCog(commands.Cog):


    @app_commands.command(name="invite", description="Shows invite statistics")
    @app_commands.describe(uye="The member you want to see (empty = yourself)")
    async def davet(self, interaction: discord.Interaction, uye: discord.Member = None):
        hedef = uye or interaction.user
        davet_data = load_davet()
        uid_str = str(hedef.id)
        bilgi = davet_data.get(uid_str, {"toplam": 0, "getirdikleri": []})
        toplam = bilgi["toplam"]
        getirdikleri = bilgi["getirdikleri"]

        getirilen_list = []
        for mid in getirdikleri[-10:]:
            m = interaction.guild.get_member(int(mid))
            if m:
                getirilen_list.append(m.mention)

        embed = discord.Embed(
            title=f"📨 {hedef.display_name} — Invite Statistics",
            color=discord.Color.green() if hedef == interaction.user else discord.Color.blurple()
        )
        embed.add_field(name="Total Invites", value=f"**{toplam}**", inline=True)
        embed.add_field(name="Brought Members (last 10)", value=", ".join(getirilen_list) or "None", inline=False)
        embed.set_thumbnail(url=hedef.display_avatar.url)
        ephemeral = hedef == interaction.user
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

    @app_commands.command(name="invite_leaderboard", description="Shows the top 10 people with the most invites")
    async def davet_siralama(self, interaction: discord.Interaction):
        davet_data = load_davet()
        skorlar = []
        for uid_str, bilgi in davet_data.items():
            m = interaction.guild.get_member(int(uid_str))
            if not m:
                continue
            skorlar.append((m, bilgi["toplam"]))
        skorlar.sort(key=lambda x: x[1], reverse=True)

        madalyalar = ["🥇", "🥈", "🥉"]
        satirlar = []
        for i, (m, toplam) in enumerate(skorlar[:10]):
            ikon = madalyalar[i] if i < 3 else f"`{i+1}.`"
            satirlar.append(f"{ikon} {m.mention} — **{toplam}** invites")

        embed = discord.Embed(
            title="🏆 Invite Leaderboard (Top 10)",
            description="\n".join(satirlar) or "No invite data yet.",
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=embed)

# Setup cogs before on_ready


async def main():
    async with bot:
        await setup_cogs()
        await bot.start(TOKEN)

asyncio.run(main())
