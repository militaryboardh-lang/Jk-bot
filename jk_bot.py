
import os
import json
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
MIN_REFERRALS = 5


# =========================
# CHANNEL LINKS
# =========================

LINKS = [
    "https://whatsapp.com/channel/0029VbEN1ghKbYMV6vRhr407",
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
            "username": username
        }
        save(data)

    return data[uid]


# =========================
# START COMMAND
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = load()

    user = update.effective_user

    me = get_user(
        data,
        user.id,
        user.username or ""
    )

    # REFERRAL SYSTEM

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

    # MAIN MENU

    keyboard = [

        [
            InlineKeyboardButton(
                "✅ I don follow all",
                callback_data="check_follow"
            )
        ],

        [
            InlineKeyboardButton(
                "💰 Balance",
                callback_data="balance"
            )
        ],

        [
            InlineKeyboardButton(
                "👥 Referral",
                callback_data="referral"
            )
        ],

        [
            InlineKeyboardButton(
                "💸 Withdraw",
                callback_data="withdraw"
            )
        ]

    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"Welcome {user.first_name} to JK Coins Bot! 🪙\n\n"

        "Follow all our channels to earn.\n"
        "Invite friends and earn 1,000 coins per referral.\n\n"

        f"Your Balance: {me['balance']} 🪙\n"
        f"Your Referrals: {len(me['referred'])}\n\n"

        "Links to follow:\n"
        + "\n".join(LINKS)
    )

    await update.message.reply_text(
        text,
        reply_markup=reply_markup
    )


# =========================
# BUTTON HANDLER
# =========================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    data = load()

    user = query.from_user

    me = get_user(
        data,
        user.id,
        user.username or ""
    )

    # BALANCE

    if query.data == "balance":

        await query.edit_message_text(

            f"💰 Your Balance: {me['balance']} coins\n\n"

            f"👥 Total Referrals: {len(me['referred'])}"

        )

        return

    # REFERRAL

    if query.data == "referral":

        bot_info = await context.bot.get_me()

        link = (
            f"https://t.me/{bot_info.username}"
            f"?start={user.id}"
        )

        await query.edit_message_text(

            "👥 YOUR REFERRAL LINK\n\n"

            f"{link}\n\n"

            "Share this link with your friends.\n"
            "You earn 1,000 coins for every successful referral. 🪙"

        )

        return

    # FOLLOW CONFIRMATION

    if query.data == "check_follow":

        me["followed"] = True

        save(data)

        await query.edit_message_text(

            "✅ Thank you!\n\n"

            "Your follow confirmation has been recorded.\n\n"

            "Use the menu to check your balance or withdrawal eligibility."

        )

        return

    # WITHDRAWAL

    if query.data == "withdraw":

        if me["balance"] < MIN_WITHDRAWAL:

            await query.edit_message_text(

                "❌ WITHDRAWAL NOT AVAILABLE\n\n"

                f"Your balance: {me['balance']} coins\n"

                f"Minimum balance: {MIN_WITHDRAWAL} coins"

            )

            return

        if len(me["referred"]) < MIN_REFERRALS:

            await query.edit_message_text(

                "❌ NOT ENOUGH REFERRALS\n\n"

                f"Your referrals: {len(me['referred'])}\n"

                f"Required referrals: {MIN_REFERRALS}"

            )

            return

        if not me["followed"]:

            await query.edit_message_text(

                "❌ Please confirm that you have followed all channels first."

            )

            return

        await query.edit_message_text(

            "🎉 CONGRATULATIONS!\n\n"

            "You qualify for withdrawal!\n\n"

            "Please contact the administrator privately "
            "to submit your withdrawal request."

        )

        return


# =========================
# DONE COMMAND
# =========================

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = load()

    user = update.effective_user

    me = get_user(
        data,
        user.id,
        user.username or ""
    )

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

        raise ValueError(
            "BOT_TOKEN is missing from Render Environment Variables!"
        )

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("done", done)
    )

    app.add_handler(
        CallbackQueryHandler(button)
    )

    print("JK Coins Bot dey run successfully!")

    app.run_polling()


if __name__ == "__main__":

    main()
