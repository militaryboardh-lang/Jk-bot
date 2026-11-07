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
    ranked = sorted(data.items(), key=lambda x: (len(x[1].get("referred", [])), x[1].get("balance", 0)), reverse=True)
    return ranked[:50]

# --- DOUBLE LOCK CHECK ---
def is_locked(me):
    # If never follow 5 links -> LOCKED
    if not me.get("followed", False):
        return True
    # If never get 5 referrals -> LOCKED
    if len(me.get("referred", [])) < 5:
        return True
    return False

def locked_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("FOLLOW 5 LINKS", callback_data="tasks")],
        [InlineKeyboardButton("SHARE MY LINK - REFER 5 PEOPLE", callback_data="refer")],
        [InlineKeyboardButton("CHECK IF I DON UNLOCK", callback_data="check_unlock")],
    ])

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("SPIN NOW", callback_data="spin")],
        [InlineKeyboardButton("DICE GAME", callback_data="dice")],
        [InlineKeyboardButton("COIN FLIP", callback_data="coin_choice")],
        [InlineKeyboardButton("LUCKY NUMBER", callback_data="lucky")],
        [InlineKeyboardButton("DAILY BONUS", callback_data="daily")],
        [InlineKeyboardButton("TOP 50 LEADERBOARD", callback_data="leaderboard")],
        [InlineKeyboardButton("FOLLOW 5 LINKS", callback_data="tasks")],
        [InlineKeyboardButton("BALANCE", callback_data="balance")],
        [InlineKeyboardButton("WITHDRAW", callback_data="withdraw")],
    ])

def back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("BACK TO MENU", callback_data="menu")]])

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
                await context.bot.send_message(chat_id=int(referrer_id), text="New person join with your link! You don get +1 Spin. Spins: " + str(ref["spins"]) + ". Referrals: " + str(len(ref["referred"])))
    save(data)
    bot
