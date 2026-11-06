import os
import random
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- FAKE WEB SERVER FOR RENDER FREE ---
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"JK Bot is alive!")
    def log_message(self, *args):
        pass

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

keep_alive()

# --- CONFIG ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
REQUIRED_CHANNELS = ["@jkcoinschannel", "@jkcoinsgroup"]  # CHANGE AM
CHANNEL_LINKS = ["https://t.me/jkcoinschannel", "https://t.me/jkcoinsgroup"] # CHANGE AM

users = {}
# Quiz questions
QUIZ = [
    ("What is the capital of Nigeria?", "Abuja", ["Lagos", "Abuja", "Kano", "Port Harcourt"]),
    ("2 + 2 x 2 = ?", "6", ["4", "6", "8", "10"]),
    ("Which coin is JK Coins?", "JK", ["BTC", "JK", "ETH", "DOGE"]),
    ("What colour is the sky?", "Blue", ["Red", "Blue", "Green", "Yellow"]),
]

def get_user(user_id, username):
    if user_id not in users:
        users[user_id] = {"username": username, "balance": 0, "referrals": 0}
    return users[user_id]

async def check_joined(context, user_id):
    for ch in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked", "banned"]:
                return False
        except:
            return False
    return True

async def show_join_message(query_or_update, context, is_query=False):
    keyboard = []
    for i, link in enumerate(CHANNEL_LINKS):
        keyboard.append([InlineKeyboardButton(f"📢 Join Channel {i+1}", url=link)])
    keyboard.append([InlineKeyboardButton("✅ I Have Joined - Verify Me", callback_data="verify_join")])
    markup = InlineKeyboardMarkup(keyboard)
    text = "⛔ STRICT RULE: You MUST join all our channels to use JK Coins Bot.\n\n1. Join all.\n2. Tap 'I Have Joined'."
    if is_query:
        await query_or_update.edit_message_text(text, reply_markup=markup)
    else:
        await query_or_update.message.reply_text(text, reply_markup=markup)

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 My Balance", callback_data="balance")],
        [InlineKeyboardButton("🎁 Earn Coins", callback_data="earn")],
        [InlineKeyboardButton("🎮 Play Games", callback_data="games")],
        [InlineKeyboardButton("👥 Refer & Earn", callback_data="refer")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
    ])

def games_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Dice Game", callback_data="game_dice")],
        [InlineKeyboardButton("🪙 Coin Flip", callback_data="game_coin")],
        [InlineKeyboardButton("🎡 Spin Wheel", callback_data="game_spin")],
        [InlineKeyboardButton("🔢 Guess Number", callback_data="game_guess")],
        [InlineKeyboardButton("🧠 Quiz Game", callback_data="game_quiz")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = get_user(user.id, user.username or user.first_name)
    if not await check_joined(context, user.id):
        await show_join_message(update, context, is_query=False)
        return
    if context.args:
        try:
            ref_id = int(context.args[0])
            if ref_id != user.id and ref_id in users:
                users[ref_id]["balance"] += 50
                users[ref_id]["referrals"] += 1
        except:
            pass
    await update.message.reply_text(
        f"Welcome to JK Coins Bot, {user.first_name}! 🪙\n\nBalance: {data['balance']} JK Coins\nReferrals: {data['referrals']}\n\nPlay games to earn more!",
        reply_markup=main_menu()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = get_user(user.id, user.username or user.first_name)

    if query.data == "verify_join":
        if await check_joined(context, user.id):
            await query.edit_message_text("✅ Verified! Tap /start to continue.")
        else:
            await show_join_message(query, context, is_query=True)
        return

    if not await check_joined(context, user.id):
        await show_join_message(query, context, is_query=True)
        return

    # --- MAIN MENU ---
    if query.data == "back":
        await query.edit_message_text(f"Balance: {data['balance']} JK Coins", reply_markup=main_menu())
    elif query.data == "balance":
        await query.edit_message_text(f
