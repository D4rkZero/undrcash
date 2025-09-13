import random
import discord
from discord.ui import View, Button
from database import get_user, update_balance, update_stats

async def play_limbo(interaction, bet: float):
    user = get_user(interaction.user.id)
    if bet > user["balance"]:
        return await interaction.response.send_message("❌ Not enough balance!")
    update_balance(interaction.user.id, -bet)

    crash_multiplier = round(random.uniform(1.2, 10.0), 2)

    embed = discord.Embed(title="🎲 Limbo Game", color=0xffaa00)
    embed.description = f"Bet: ${bet}\nCrash point unknown!\nClick Cash Out to stop before crash."
    msg = await interaction.response.send_message(embed=embed)

    class LimboView(View):
        def __init__(self):
            super().__init__(timeout=None)
            self.cashed_out = False

        @discord.ui.button(label="Cash Out", style=discord.ButtonStyle.green)
        async def cash_out(self, button: Button, inter: discord.Interaction):
            if self.cashed_out:
                return
            self.cashed_out = True
            current_multiplier = round(random.uniform(1.0, crash_multiplier), 2)
            win = round(bet * current_multiplier, 2)
            update_balance(interaction.user.id, win)
            update_stats(interaction.user.id, bet=bet, won=win)
            embed = discord.Embed(title="✅ Cashed Out!", description=f"You cashed out at {current_multiplier}x and won ${win}!", color=0x00ff00)
            await inter.response.edit_message(embed=embed)
            self.stop()

    await msg.edit(view=LimboView())
