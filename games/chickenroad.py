import random
import discord
from database import get_user, update_balance, update_stats

DIFFICULTY = {
    "easy": {"steps": 5, "fail_chance": 0.1},
    "mid": {"steps": 7, "fail_chance": 0.2},
    "hard": {"steps": 10, "fail_chance": 0.3},
    "extreme": {"steps": 15, "fail_chance": 0.4},
}

async def play_chickenroad(interaction, bet: float, difficulty: str = "easy"):
    difficulty = difficulty.lower()
    if difficulty not in DIFFICULTY:
        return await interaction.response.send_message("❌ Invalid difficulty! Choose easy, mid, hard, extreme.")

    user = get_user(interaction.user.id)
    if bet > user["balance"]:
        return await interaction.response.send_message("❌ Not enough balance!")

    update_balance(interaction.user.id, -bet)
    steps = DIFFICULTY[difficulty]["steps"]
    fail_chance = DIFFICULTY[difficulty]["fail_chance"]

    embed = discord.Embed(title=f"🐔 Chicken Road - {difficulty.capitalize()}", color=0xffdd00)
    embed.description = f"Bet: ${bet}\nSteps to cross: {steps}\nChance to get hit per step: {int(fail_chance*100)}%\nClick Step Forward to move."
    msg = await interaction.response.send_message(embed=embed)

    class ChickenView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            self.remaining_steps = steps

        @discord.ui.button(label="Step Forward", style=discord.ButtonStyle.green)
        async def step(self, button: discord.ui.Button, inter: discord.Interaction):
            self.remaining_steps -= 1
            if random.random() < fail_chance:
                update_stats(interaction.user.id, bet=bet, won=0)
                await inter.response.edit_message(embed=discord.Embed(
                    title="💥 Chicken got hit!", description=f"You lost ${bet}!", color=0xff0000))
                self.stop()
            elif self.remaining_steps <= 0:
                win = bet * 2
                update_balance(interaction.user.id, win)
                update_stats(interaction.user.id, bet=bet, won=win)
                await inter.response.edit_message(embed=discord.Embed(
                    title="✅ You crossed safely!", description=f"You won ${win}", color=0x00ff00))
                self.stop()
            else:
                await inter.response.edit_message(embed=discord.Embed(
                    title=f"🐔 Step Forward - {difficulty.capitalize()}",
                    description=f"Steps left: {self.remaining_steps}", color=0x00ff00))
    await msg.edit(view=ChickenView())
