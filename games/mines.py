import random
import discord
from discord.ui import View, Button
from database import get_user, update_balance, update_stats

async def play_mines(interaction, bet: float, mines_count: int):
    user = get_user(interaction.user.id)
    if bet > user["balance"]:
        return await interaction.response.send_message("❌ Not enough balance!")
    update_balance(interaction.user.id, -bet)

    size = 5  # 5x5 grid
    total_cells = size * size
    if mines_count >= total_cells:
        mines_count = total_cells - 1
    mine_positions = random.sample(range(total_cells), mines_count)

    embed = discord.Embed(title="💣 Mines Game", color=0xffdd00)
    embed.description = (
        f"Bet: ${bet}\n"
        f"Mines: {mines_count}\n"
        "Click **Reveal Cell** to pick a cell. Avoid mines!"
    )
    msg = await interaction.response.send_message(embed=embed)

    class MinesView(View):
        def __init__(self):
            super().__init__(timeout=None)
            self.revealed = 0

        @discord.ui.button(label="Reveal Cell", style=discord.ButtonStyle.green)
        async def reveal(self, button: Button, inter: discord.Interaction):
            pos = random.randint(0, total_cells-1)
            if pos in mine_positions:
                update_stats(interaction.user.id, bet=bet, won=0)
                await inter.response.edit_message(embed=discord.Embed(
                    title="💥 Boom!",
                    description=f"You hit a mine and lost ${bet}!", color=0xff0000))
                self.stop()
            else:
                self.revealed += 1
                if self.revealed == total_cells - mines_count:
                    win = bet * 2
                    update_balance(interaction.user.id, win)
                    update_stats(interaction.user.id, bet=bet, won=win)
                    await inter.response.edit_message(embed=discord.Embed(
                        title="✅ You cleared all safe cells!",
                        description=f"You won ${win}", color=0x00ff00))
                    self.stop()
                else:
                    await inter.response.edit_message(embed=discord.Embed(
                        title="🟢 Safe!",
                        description=f"Safe cell! Revealed {self.revealed}/{total_cells - mines_count}",
                        color=0x00ff00))
    await msg.edit(view=MinesView())
