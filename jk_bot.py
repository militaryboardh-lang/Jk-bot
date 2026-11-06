import json, random, os, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import threading
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")

LINKS = [
    "https://whatsapp.com/channel/0029VbEN1ghKbYMV6vRhr407",
    "https://t.me/jk_coins",
    "https://youtube.com/@jungkookjeon40330?si=kPk-qdcINbMZrOPf",
    "https://www.tiktok.com/@justmeet06",
    "https://t.me/update_3334",
]

DB_FILE = "users.json"

def load():
    if os.path.exists(DB_FILE):
        with open(DB_FILE) as f:
            return json.load(f)
    return {}

def save(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

def get_user(data, uid):
    uid = str(uid)
    if uid not in data:
        data[uid] = {"balance": 0, "spins": 3, "referred": [], "followed": False, "username": "", "last_bonus": 0}
    if "last_bonus" not in data[uid]:
        data[uid]["last_bonus"] = 0
    return data[uid]

def get_leaderboard(data):
    # Sort by referrals count, then balance
    ranked = sorted(data.items(), key=lambda x: (len(x[1].get("referred", [])), x[1].get("balance", 0)), reverse=True)
    return ranked[:50]

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎰 SPIN NOW", callback_data="spin")],
        [InlineKeyboardButton("🎲 DICE GAME", callback_data="dice")],
        [InlineKeyboardButton("🪙 COIN FLIP", callback_data="coin_choice")],
        [InlineKeyboardButton("🔢 LUCKY NUMBER", callback_data="lucky")],
        [InlineKeyboardButton("🎁 DAILY BONUS", callback_data="daily")],
        [InlineKeyboardButton("🏆 TOP 50 LEADERBOARD", callback_data="leaderboard")],
        [InlineKeyboardButton("FOLLOW 5 LINKS", callback_data="tasks")],
        [InlineKeyboardButton("BALANCE", callback_data="balance")],
        [InlineKeyboardButton("WITHDRAW", callback_data="withdraw")],
    ])

def back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ BACK TO MENU", callback_data="menu")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load()
    user = update.effective_user
    me = get_user(data, user.id)
    me["username"] = user.username or user.first_name
    if context.args:
        referrer_id = str(context.args[0])
        if referrer_id != str(user.id) and referrer_id in data:
            ref = data[referrer_id]
            if str(user.id) not in ref["referred"]:
                ref["referred"].append(str(user.id))
                ref["spins"] += 1
                await context.bot.send_message(chat_id=int(referrer_id), text=f"New person join with your link! You don get +1 Spin. Spins: {ref['spins']}. Referrals: {len(ref['referred'])}")
    save(data)
    text = (
        f"Welcome {user.first_name} to JK SPIN BOT\n\n"
        f"Balance: {me['balance']} / 10000\n"
        f"Spins Left: {me['spins']}\n"
        f"Referrals: {len(me['referred'])} / 5\n\n"
        f"HOW E DEY WORK:\n"
        f"1. Spin to win till you reach 10000 = 100,000 Naira\n"
        f"2. You get 3 free spins\n"
        f"3. 1 Invite = 1 Extra Spin\n"
        f"4. Follow 5 links + Refer 5 people before withdraw\n"
        f"5. Top 50 referrers go win prize every month end!\n\n"
        f"Your Invite Link:\nhttps://t.me/{context.bot.username}?start={user.id}"
    )
    await update.message.reply_text(text, reply_markup=main_menu())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = load()
    me = get_user(data, q.from_user.id)

    if q.data == "menu":
        await q.edit_message_text(f"JK SPIN BOT Menu\n\nBalance: {me['balance']} / 10000\nSpins Left: {me['spins']}\nReferrals: {len(me['referred'])} / 5", reply_markup=main_menu())
        return

    if q.data == "leaderboard":
        ranked = get_leaderboard(data)
        # Find my position
        my_pos = 0
        for i, (uid, u) in enumerate(ranked, 1):
            if uid == str(q.from_user.id):
                my_pos = i
                break
        # Top 10 show for first page, then prize info
        txt = "🏆 TOP 50 LEADERBOARD — Most Referrals\n"
        txt += "Month End Prizes:\n🥇 1st = +5000 coins\n🥈 2nd = +3000 coins\n🥉 3rd = +2000 coins\n🏅 4th-10th = +500 coins\n\n"
        medals = ["🥇","🥈","🥉"]
        for i, (uid, u) in enumerate(ranked[:20], 1):
            name = u.get("username") or f"User {uid[:4]}"
            medal = medals[i-1] if i <= 3 else f"{i}."
            txt += f"{medal} @{name} — {len(u.get('referred', []))} invites — {u.get('balance',0)} coins\n"
        if len(ranked) > 20:
            txt += f"\n... and {len(ranked)-20} more people for Top 50\n"
        if my_pos:
            txt += f"\n👉 You dey #{my_pos} with {len
