import random
import discord
from database import get_user, update_balance, update_stats

async def play_coinflip(interaction, bet: float, choice: str):
    choice = choice.lower()
    if choice not in ["heads", "tails"]:
        return await interaction.response.send_message("❌ Choose heads or tails!")

    user = get_user(interaction.user.id)
    if bet > user["balance"]:
        return await interaction.response.send_message("❌ Not enough balance!")
    update_balance(interaction.user.id, -bet)

    result = random.choice(["heads", "tails"])
    if choice == result:
        win = bet * 2
        update_balance(interaction.user.id, win)
        update_stats(interaction.user.id, bet=bet, won=win)
        msg = f"✅ It's {result}! You won ${win}"
        color = 0x00ff00
    else:
        update_stats(interaction.user.id, bet=bet, won=0)
        msg = f"💥 It's {result}! You lost ${bet}"
        color = 0xff0000

    embed = discord.Embed(title="🪙 Coinflip", description=msg, color=color)
    await interaction.response.send_message(embed=embed)
