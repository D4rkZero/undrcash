import discord
from discord.ext import tasks, commands
from discord import app_commands
from database import get_user, update_balance, c, conn
from deposit import process_deposits
from config import DISCORD_TOKEN, WITHDRAW_WEBHOOK
import requests
import matplotlib.pyplot as plt
import io

# Import games (no code here, just imports)
from games import mines, dragontower, chickenroad, blackjack, coinflip, limbo

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="$", intents=intents)
tree = bot.tree

# --- Auto deposit checker ---
@tasks.loop(minutes=2)
async def check_deposits():
    for guild in bot.guilds:
        for member in guild.members:
            get_user(member.id)
            new_deposits = process_deposits(member.id)
            for txid, usd_amount in new_deposits:
                try:
                    await member.send(f"✅ Deposit of ${usd_amount} credited! (txid: {txid})")
                except:
                    # Ignore if DM fails
                    pass

# --- Balance ---
@tree.command(name="balance", description="Show your account balance")
async def balance(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    embed = discord.Embed(title=f"💰 Balance for {interaction.user}", color=0x00ff99)
    embed.add_field(name="USD", value=f"${user['balance']}", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- Withdraw ---
def notify_withdraw(user_id, amount, currency):
    data = {
        "content": f"📩 **Withdraw Request:** User <@{user_id}> requested **{amount} {currency.upper()}**"
    }
    requests.post(WITHDRAW_WEBHOOK, json=data)

@tree.command(name="withdraw", description="Withdraw money from your balance")
@app_commands.describe(amount="Amount to withdraw", currency="Currency code (USD)")
async def withdraw(interaction: discord.Interaction, amount: float, currency: str = "USD"):
    user = get_user(interaction.user.id)
    if user["balance"] < amount:
        return await interaction.response.send_message("❌ Not enough balance!", ephemeral=True)
    update_balance(interaction.user.id, -amount)
    c.execute("INSERT INTO withdraws (user_id, amount, currency) VALUES (?, ?, ?)",
              (str(interaction.user.id), amount, currency.upper()))
    conn.commit()
    notify_withdraw(interaction.user.id, amount, currency)
    await interaction.response.send_message(f"📩 Withdraw request of {amount} {currency.upper()} submitted.", ephemeral=True)

# --- Add dollars (admin) ---
@tree.command(name="adddollars", description="Add dollars to a user's balance (Admin)")
@app_commands.describe(user="Target user", amount="Amount to add")
async def adddollars(interaction: discord.Interaction, user: discord.Member, amount: float):
    update_balance(user.id, amount)
    await interaction.response.send_message(f"✅ Added ${amount} to {user.mention}'s balance.", ephemeral=True)

# --- Help ---
@tree.command(name="help", description="Show all commands and instructions")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="🎰 Casino Bot Help", color=0x00ff99)
    embed.add_field(name="💰 Account",
                    value="/balance — Show balance\n/withdraw <amount> <currency> — Withdraw money",
                    inline=False)
    embed.add_field(name="🎮 Games",
                    value="/mines <bet> <mines>\n"
                          "/dragontower <bet>\n"
                          "/chickenroad <bet> <difficulty>\n"
                          "/blackjack <bet>\n"
                          "/coinflip <bet> <choice>\n"
                          "/limbo <bet>",
                    inline=False)
    embed.add_field(name="📊 Stats",
                    value="/statistics — Show leaderboard and charts",
                    inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- Statistics ---
@tree.command(name="statistics", description="Show top 5 players and a chart")
async def statistics(interaction: discord.Interaction):
    c.execute("SELECT user_id, total_won FROM stats ORDER BY total_won DESC LIMIT 5")
    data = c.fetchall()
    if not data:
        return await interaction.response.send_message("No stats available yet.", ephemeral=True)

    names = [str(bot.get_user(int(uid))) if bot.get_user(int(uid)) else uid for uid, _ in data]
    wins = [won for _, won in data]

    embed = discord.Embed(title="📊 Top 5 Players", color=0x00ff99)
    for name, won in zip(names, wins):
        embed.add_field(name=name, value=f"${won}", inline=False)

    # Create chart
    plt.bar(names, wins, color='purple')
    plt.ylabel("Total Won ($)")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    file = discord.File(buf, filename="chart.png")
    embed.set_image(url="attachment://chart.png")
    await interaction.response.send_message(embed=embed, file=file)
    buf.close()
    plt.clf()

# --- Games slash commands (no game code here) ---
@tree.command(name="mines", description="Play Mines")
@app_commands.describe(bet="Bet amount", mines="Number of mines")
async def cmd_mines(interaction: discord.Interaction, bet: float, mines: int):
    await mines.play_mines(interaction, bet, mines)

@tree.command(name="dragontower", description="Play Dragon Tower")
@app_commands.describe(bet="Bet amount")
async def cmd_dragontower(interaction: discord.Interaction, bet: float):
    await dragontower.play_dragontower(interaction, bet)

@tree.command(name="chickenroad", description="Play Chicken Road")
@app_commands.describe(bet="Bet amount", difficulty="easy, mid, hard, extreme")
async def cmd_chickenroad(interaction: discord.Interaction, bet: float, difficulty: str = "easy"):
    await chickenroad.play_chickenroad(interaction, bet, difficulty)

@tree.command(name="blackjack", description="Play Blackjack")
@app_commands.describe(bet="Bet amount")
async def cmd_blackjack(interaction: discord.Interaction, bet: float):
    await blackjack.play_blackjack(interaction, bet)

@tree.command(name="coinflip", description="Play Coinflip")
@app_commands.describe(bet="Bet amount", choice="heads or tails")
async def cmd_coinflip(interaction: discord.Interaction, bet: float, choice: str):
    await coinflip.play_coinflip(interaction, bet, choice)

@tree.command(name="limbo", description="Play Limbo")
@app_commands.describe(bet="Bet amount")
async def cmd_limbo(interaction: discord.Interaction, bet: float):
    await limbo.play_limbo(interaction, bet)

# --- Events ---
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    check_deposits.start()
    await tree.sync()

bot.run(DISCORD_TOKEN)
