import random
import discord
from database import get_user, update_balance, update_stats

def calculate_hand(hand):
    total = 0
    aces = 0
    for card in hand:
        if card in ["J", "Q", "K"]:
            total += 10
        elif card == "A":
            aces += 1
            total += 11
        else:
            total += int(card)
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total

async def play_blackjack(interaction, bet: float):
    user = get_user(interaction.user.id)
    if bet > user["balance"]:
        return await interaction.response.send_message("❌ Not enough balance!")
    update_balance(interaction.user.id, -bet)

    cards = [str(x) for x in range(2,11)] + ["J","Q","K","A"]
    player_hand = [random.choice(cards), random.choice(cards)]
    dealer_hand = [random.choice(cards), random.choice(cards)]

    player_total = calculate_hand(player_hand)
    dealer_total = calculate_hand(dealer_hand)

    if player_total > dealer_total:
        win = bet * 2
        update_balance(interaction.user.id, win)
        update_stats(interaction.user.id, bet=bet, won=win)
        result = f"You win! ${win}"
        color = 0x00ff00
    elif player_total == dealer_total:
        update_balance(interaction.user.id, bet)
        result = "Draw! Your bet is returned."
        color = 0xffff00
        update_stats(interaction.user.id, bet=bet, won=0)
    else:
        result = f"You lose ${bet}!"
        color = 0xff0000
        update_stats(interaction.user.id, bet=bet, won=0)

    embed = discord.Embed(title="🃏 Blackjack", color=color)
    embed.add_field(name="Your Hand", value=f"{player_hand} = {player_total}", inline=True)
    embed.add_field(name="Dealer Hand", value=f"{dealer_hand} = {dealer_total}", inline=True)
    embed.add_field(name="Result", value=result, inline=False)
    await interaction.response.send_message(embed=embed)
