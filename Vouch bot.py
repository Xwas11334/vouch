import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

# ─────────────────────────────────────────────
#  CONFIG – passe diese Werte an
# ─────────────────────────────────────────────
BOT_TOKEN        = "MTQ4NjQyNjQ2NDgzMTE0ODA1Mg.G37IE9.dnGfvBLzkTAzfU0MeCyct5nHhGlH8gS4cEyk5o"   # Bot-Token aus dem Discord Developer Portal
VOUCH_CHANNEL_ID = 1455376272627863572      # ID des Vouch-Channels (Rechtsklick → ID kopieren)
VOUCH_FILE       = "vouches.json"           # Datei zum Speichern aller Vouches
# ─────────────────────────────────────────────

BRAND_COLOR  = 0x9B59B6   # Lila – passend zu "Fusion Projects"
STAR_FILLED  = "⭐"
FOOTER_ICON  = "https://cdn.discordapp.com/embed/avatars/0.png"  # optional: eigenes Logo-URL


# ── Daten-Helpers ──────────────────────────────────────────────
def load_vouches() -> list:
    if os.path.exists(VOUCH_FILE):
        with open(VOUCH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_vouches(data: list):
    with open(VOUCH_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def count_user_vouches(user_id: int) -> int:
    return sum(1 for v in load_vouches() if v["target_id"] == user_id)


# ── Bot-Setup ──────────────────────────────────────────────────
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


@bot.event
async def on_ready():
    await tree.sync()
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Fusion Projects 🛒"
        )
    )
    print(f"✅  Eingeloggt als {bot.user}  |  {len(bot.guilds)} Server")


# ── /vouch ─────────────────────────────────────────────────────
@tree.command(name="vouch", description="Hinterlasse einen Vouch für einen Nutzer")
@app_commands.describe(
    nutzer  = "Für wen ist der Vouch?",
    sterne  = "Bewertung (1–5 Sterne)",
    produkt = "Welches Produkt / welcher Service?",
    text    = "Dein Kommentar zum Kauf"
)
@app_commands.choices(sterne=[
    app_commands.Choice(name="⭐ 1 Stern",   value=1),
    app_commands.Choice(name="⭐⭐ 2 Sterne", value=2),
    app_commands.Choice(name="⭐⭐⭐ 3 Sterne", value=3),
    app_commands.Choice(name="⭐⭐⭐⭐ 4 Sterne", value=4),
    app_commands.Choice(name="⭐⭐⭐⭐⭐ 5 Sterne", value=5),
])
async def vouch(
    interaction: discord.Interaction,
    nutzer:  discord.Member,
    sterne:  int,
    produkt: str,
    text:    str
):
    # ── Channel-Check ──────────────────────────────────────────
    if interaction.channel_id != VOUCH_CHANNEL_ID:
        channel = interaction.guild.get_channel(VOUCH_CHANNEL_ID)
        mention = channel.mention if channel else f"<#{VOUCH_CHANNEL_ID}>"
        await interaction.response.send_message(
            f"❌ Vouches können nur in {mention} abgegeben werden!",
            ephemeral=True
        )
        return

    # ── Selbst-Vouch verhindern ────────────────────────────────
    if nutzer.id == interaction.user.id:
        await interaction.response.send_message(
            "❌ Du kannst dich nicht selbst vouchen!",
            ephemeral=True
        )
        return

    # ── Daten speichern ────────────────────────────────────────
    now      = datetime.utcnow()
    ts_iso   = now.isoformat()
    ts_human = now.strftime("%d.%m.%Y %H:%M") + " UTC"

    entry = {
        "author_id":   interaction.user.id,
        "author_tag":  str(interaction.user),
        "target_id":   nutzer.id,
        "target_tag":  str(nutzer),
        "stars":       sterne,
        "product":     produkt,
        "text":        text,
        "timestamp":   ts_iso,
    }
    vouches = load_vouches()
    vouches.append(entry)
    save_vouches(vouches)

    total_vouches = count_user_vouches(nutzer.id)

    # ── Stars-String ───────────────────────────────────────────
    star_str = STAR_FILLED * sterne + "✩" * (5 - sterne)

    # ── Embed bauen ────────────────────────────────────────────
    embed = discord.Embed(
        title       = "✅  Neuer Vouch erstellt!",
        description = (
            f"{star_str}\n\n"
            f"**Produkt / Service:**\n"
            f"┃ {produkt}\n\n"
            f"**Kommentar:**\n"
            f"┃ {text}"
        ),
        color       = BRAND_COLOR,
        timestamp   = now
    )

    embed.add_field(
        name   = "Gevoucht für:",
        value  = f"{nutzer.mention}\n`{nutzer}`",
        inline = True
    )
    embed.add_field(
        name   = "Geoucht von:",
        value  = f"{interaction.user.mention}\n`{interaction.user}`",
        inline = True
    )
    embed.add_field(
        name   = "Geoucht am:",
        value  = f"`{ts_human}`",
        inline = True
    )
    embed.add_field(
        name   = "📊 Gesamt-Vouches für diesen Nutzer:",
        value  = f"`{total_vouches}` Vouche",
        inline = False
    )

    embed.set_thumbnail(url=nutzer.display_avatar.url)
    embed.set_author(
        name    = "Fusion Projects – Vouch System",
        icon_url= interaction.guild.icon.url if interaction.guild.icon else discord.Embed.Empty
    )
    embed.set_footer(
        text     = f"Fusion Projects Marketplace • Vouch #{len(vouches)}",
    )

    await interaction.response.send_message(embed=embed)


# ── /vouches ───────────────────────────────────────────────────
@tree.command(name="vouches", description="Zeigt alle Vouches eines Nutzers an")
@app_commands.describe(nutzer="Welchen Nutzer nachschlagen?")
async def vouches_cmd(interaction: discord.Interaction, nutzer: discord.Member):
    data = [v for v in load_vouches() if v["target_id"] == nutzer.id]

    if not data:
        await interaction.response.send_message(
            f"❌ Keine Vouches für **{nutzer}** gefunden.",
            ephemeral=True
        )
        return

    avg   = sum(v["stars"] for v in data) / len(data)
    lines = []
    for i, v in enumerate(data[-10:], 1):   # letzte 10
        stars = STAR_FILLED * v["stars"]
        dt    = datetime.fromisoformat(v["timestamp"]).strftime("%d.%m.%Y")
        lines.append(f"`{i}.` {stars} — **{v['product']}** *von {v['author_tag']}* • {dt}")

    embed = discord.Embed(
        title       = f"📋  Vouches für {nutzer.display_name}",
        description = "\n".join(lines),
        color       = BRAND_COLOR
    )
    embed.add_field(name="📦 Gesamt",         value=f"`{len(data)}`",       inline=True)
    embed.add_field(name="⭐ Ø Bewertung",     value=f"`{avg:.1f} / 5.0`",  inline=True)
    embed.set_thumbnail(url=nutzer.display_avatar.url)
    embed.set_footer(text="Fusion Projects Marketplace")

    await interaction.response.send_message(embed=embed)


# ── /topvouched ────────────────────────────────────────────────
@tree.command(name="topvouched", description="Zeigt die Top-10 am meisten gevouchten Nutzer")
async def topvouched(interaction: discord.Interaction):
    from collections import Counter
    data    = load_vouches()
    counts  = Counter(v["target_id"] for v in data)
    top10   = counts.most_common(10)

    if not top10:
        await interaction.response.send_message("❌ Noch keine Vouches vorhanden.", ephemeral=True)
        return

    lines = []
    medals = ["🥇","🥈","🥉"]
    for i, (uid, count) in enumerate(top10):
        medal = medals[i] if i < 3 else f"`{i+1}.`"
        member = interaction.guild.get_member(uid)
        name   = member.mention if member else f"<@{uid}>"
        lines.append(f"{medal} {name} — **{count}** Vouche")

    embed = discord.Embed(
        title       = "🏆  Top Geoucht – Fusion Projects",
        description = "\n".join(lines),
        color       = BRAND_COLOR
    )
    embed.set_footer(text="Fusion Projects Marketplace")
    await interaction.response.send_message(embed=embed)


# ── Start ──────────────────────────────────────────────────────
bot.run("MTQ4NjQyNjQ2NDgzMTE0ODA1Mg.G37IE9.dnGfvBLzkTAzfU0MeCyct5nHhGlH8gS4cEyk5o")