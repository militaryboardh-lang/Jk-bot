import os
import json
import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# =========================
# BOT CONFIGURATION
# =========================

TOKEN = os.getenv("BOT_TOKEN", "").strip()

DB_FILE = "users.json"

REFERRAL_REWARD = 1000
MIN_WITHDRAWAL = 10000
MIN_REFERRALS = 3
SPIN_COOLDOWN = 60

# =========================
# CHANNEL LINKS
# =========================

LINKS = [
    "Follow the Jk Coin channel on WhatsApp: https://whatsapp.com/channel/0029VbEN1ghKbYMV6vRhr407",
    "https://t.me/jk_coins",
    "https://youtube.com/@jungkookjeon...",
    "https://www.tiktok.com/@justmeet...",
    "https://t.me/update_3334",
]

# =========================
# DATABASE
# =========================

def load():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            print("Database could not be loaded.")
    return {}

def save(data):
    temporary_file = DB_FILE + ".tmp"
    with open(temporary_file, "w") as f:
        json.dump(data, f, indent=4)
    os.replace(temporary_file, DB_FILE)

def get_user(data, user_id, username=""):
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "balance": 0,
            "referred": [],
            "followed": False,
            "username": username,
            "last_spin": 0
        }
        save(data)
    if "last_spin" not in data[uid]:
        data[uid]["last_spin"] = 0
    return data[uid]

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("✅ I don follow all", callback_data="check_follow")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Referral", callback_data="referral")],
        [InlineKeyboardButton("🎡 Spin", callback_data="spin")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")]])

# =========================
# START / MENU COMMAND
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load()
    user = update.effective_user
    me = get_user(data, user.id, user.username or "")

    if context.args:
        referrer_id = str(context.args[0])
        user_id = str(user.id)
        if (
            referrer_id != user_id
            and referrer_id in data
            and user_id not in data[referrer_id]["referred"]
        ):
            data[referrer_id]["referred"].append(user_id)
            data[referrer_id]["balance"] += REFERRAL_REWARD
            save(data)

    text = (
        f"Welcome {user.first_name} to JK Coins Bot! 🪙\n\n"
        "Follow all our channels to earn.\n"
        "Invite friends and earn 1,000 coins per referral.\n\n"
        f"Your Balance: {me['balance']} 🪙\n"
        f"Your Referrals: {len(me['referred'])}\n\n"
        "Links to follow:\n"
        + "\n".join(LINKS)
    )
    await update.message.reply_text(text, reply_markup=main_menu_keyboard())

# =========================
# BUTTON HANDLER
# =========================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load()
    user = query.from_user
    me = get_user(data, user.id, user.username or "")

    if query.data == "menu":
        text = (
            f"Welcome {user.first_name} to JK Coins Bot! 🪙\n\n"
            "Follow all our channels to earn.\n"
            "Invite friends and earn 1,000 coins per referral.\n\n"
            f"Your Balance: {me['balance']} 🪙\n"
            f"Your Referrals: {len(me['referred'])}\n\n"
            "Links to follow:\n"
            + "\n".join(LINKS)
        )
        await query.edit_message_text(text, reply_markup=main_menu_keyboard())
        return

    if query.data == "balance":
        await query.edit_message_text(
            f"💰 Your Balance: {me['balance']} coins\n\n"
            f"👥 Total Referrals: {len(me['referred'])}",
            reply_markup=back_keyboard()
        )
        return

    if query.data == "referral":
        bot_info = await context.bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={user.id}"
        await query.edit_message_text(
            "👥 YOUR REFERRAL LINK\n\n"
            f"{link}\n\n"
            "Share this link with your friends.\n"
            "You earn 1,000 coins for every successful referral. 🪙",
            reply_markup=back_keyboard()
        )
        return

    if query.data == "spin":
        now = int(time.time())
        remaining = SPIN_COOLDOWN - (now - me.get("last_spin", 0))
        if remaining > 0:
            await query.edit_message_text(
                f"⏳ Wait {remaining} seconds before you spin again!\n\n"
                f"Your Balance: {me['balance']} coins",
                reply_markup=back_keyboard()
            )
            return

        reward = random.choice([50, 100, 100, 200, 200, 500, 1000, 0])
        me["balance"] += reward
        me["last_spin"] = now
        save(data)

        if reward == 0:
            msg = "😢 You spin and win 0 coins. Try again!"
        else:
            msg = f"🎉 You spin and win {reward} coins!"

        await query.edit_message_text(
            f"🎡 SPIN RESULT\n\n{msg}\n\n💰 New Balance: {me['balance']} coins",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎡 Spin Again", callback_data="spin")],
                [InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")]
            ])
        )
        return

    if query.data == "check_follow":
        me["followed"] = True
        save(data)
        await query.edit_message_text(
            "✅ Thank you!\n\n"
            "Your follow confirmation has been recorded.\n\n"
            "Use the menu to check your balance or withdrawal eligibility.",
            reply_markup=back_keyboard()
        )
        return

    if query.data == "withdraw":
        if me["balance"] < MIN_WITHDRAWAL:
            await query.edit_message_text(
                "❌ WITHDRAWAL NOT AVAILABLE\n\n"
                f"Your balance: {me['balance']} coins\n"
                f"Minimum balance: {MIN_WITHDRAWAL} coins",
                reply_markup=back_keyboard()
            )
            return
        if len(me["referred"]) < MIN_REFERRALS:
            await query.edit_message_text(
                "❌ NOT ENOUGH REFERRALS\n\n"
                f"Your referrals: {len(me['referred'])}\n"
                f"Required referrals: {MIN_REFERRALS}",
                reply_markup=back_keyboard()
            )
            return
        if not me["followed"]:
            await query.edit_message_text(
                "❌ Please confirm that you have followed all channels first.",
                reply_markup=back_keyboard()
            )
            return
        await query.edit_message_text(
            "🎉 CONGRATULATIONS!\n\n"
            "You qualify for withdrawal!\n\n"
            "Please contact the administrator privately "
            "to submit your withdrawal request.",
            reply_markup=back_keyboard()
        )
        return

# =========================
# DONE COMMAND
# =========================

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load()
    user = update.effective_user
    me = get_user(data, user.id, user.username or "")
    me["followed"] = True
    save(data)
    await update.message.reply_text(
        "✅ Follow confirmation recorded!\n\n"
        "You can now check your balance and withdrawal eligibility."
    )

# =========================
# BOT STARTUP
# =========================

def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN is missing from Render Environment Variables!")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CallbackQueryHandler(button))
    print("JK Coins Bot dey run successfully!")
    app.run_polling()

if __name__ == "__main__":
    main()
