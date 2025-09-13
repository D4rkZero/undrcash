import requests
from database import update_balance, c, conn
from config import BLOCKCYPHER_TOKEN, XPUB, DEPOSIT_WEBHOOK

def get_ltc_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd"
    res = requests.get(url).json()
    return res["litecoin"]["usd"]

def fetch_transactions():
    url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{XPUB}/full"
    res = requests.get(url, params={"token": BLOCKCYPHER_TOKEN}).json()
    return res.get("txs", [])

def notify_deposit(user_id, amount, txid):
    data = {
        "content": f"✅ **Deposit:** User <@{user_id}> has deposited **${amount}** (txid: {txid})"
    }
    requests.post(DEPOSIT_WEBHOOK, json=data)

def process_deposits(user_id):
    txs = fetch_transactions()
    new_deposits = []

    for tx in txs:
        txid = tx.get("hash")
        confirmations = tx.get("confirmations", 0)
        amount = sum([out.get("value", 0) for out in tx.get("outputs", [])]) / 100000000

        # Skip if already recorded
        c.execute("SELECT * FROM deposits WHERE txid = ?", (txid,))
        if c.fetchone():
            continue

        # Save tx
        c.execute("INSERT INTO deposits (txid, user_id, amount, confirmed) VALUES (?, ?, ?, ?)",
                  (txid, user_id, amount, confirmations))
        conn.commit()

        # Credit balance if confirmed
        if confirmations >= 1:
            usd_rate = get_ltc_price()
            usd_amount = round(amount * usd_rate, 2)
            update_balance(user_id, usd_amount)
            notify_deposit(user_id, usd_amount, txid)  # send webhook
            new_deposits.append((txid, usd_amount))

    return new_deposits
