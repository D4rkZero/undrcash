import random
import discord
from discord.ui import View, Button
from database import get_user, update_balance, update_stats

async def play_dragontower(interaction, bet: float):
    user = get_user(interaction.user.id)
    if bet > user["balance"]:
        return await interaction.response.send_message("❌ Not enough balance!")
    update_balance(interaction.user.id, -bet)

    embed = discord.Embed(title="🐉 Dragon Tower", color=0xff8800)
    embed.description = (
        f"Bet: ${bet}\n"
        "Climb the tower and avoid dragons!\nClick **Next Floor** to climb."
    )
    msg = await interaction.response.send_message(embed=embed)

    floors = 10
    class TowerView(View):
        def __init__(self):
            super().__init__(timeout=None)
            self.current = 0

        @discord.ui.button(label="Next Floor", style=discord.ButtonStyle.green)
        async def next_floor(self, button: Button, inter: discord.Interaction):
            self.current += 1
            if random.random() < 0.2:  # 20% chance dragon attacks
                update_stats(interaction.user.id, bet=bet, won=0)
                await inter.response.edit_message(embed=discord.Embed(
                    title="💥 Dragon Attack!",
                    description=f"You lost ${bet}!", color=0xff0000))
                self.stop()
            elif self.current >= floors:
                win = bet * 3
                update_balance(interaction.user.id, win)
                update_stats(interaction.user.id, bet=bet, won=win)
                await inter.response.edit_message(embed=discord.Embed(
                    title="🏆 Tower Completed!",
                    description=f"You won ${win}", color=0x00ff00))
                self.stop()
            else:
                await inter.response.edit_message(embed=discord.Embed(
                    title=f"🐉 Floor {self.current}",
                    description=f"Safe! Keep climbing.", color=0x00ff00))
    await msg.edit(view=TowerView())
