import json, random, os, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

LINKS = [
    "https://whatsapp.com/channel/0029Vb...",
    "https://t.me/jk_coins",
    "https://youtube.com/@jungkookjeon...",
    "https://www.tiktok.com/@justmeet...",
    "https://t.me/update_3334",
]

DB_FILE = "users.json"

def load():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

def get_user(data, user_id, username=""):
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"balance": 0, "referred": [], "followed": False, "username": username}
        save(data)
    return data[uid]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load()
    user = update.effective_user
    me = get_user(data, user.id, user.username or "")

    # Referral: /start 123456789
    if context.args:
        try:
            referrer_id = str(context.args[0])
            if referrer_id != str(user.id) and referrer_id in data:
                if str(user.id) not in data[referrer_id]["referred"]:
                    data[referrer_id]["referred"].append(str(user.id))
                    data[referrer_id]["balance"] += 1000
                    save(data)
        except:
            pass

    keyboard = [
        [InlineKeyboardButton("✅ I don follow all", callback_data="check_follow")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Referral", callback_data="referral")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"Welcome {user.first_name} to JK Coins Bot! 🪙\n\n"
        f"Follow all our channels to earn.\n"
        f"Invite friends to earn 1000 per referral.\n\n"
        f"Your Balance: {me['balance']}\n"
        f"Your Referrals: {len(me['referred'])}\n\n"
        f"Links to follow:\n" + "\n".join(LINKS)
    )
    await update.message.reply_text(text, reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = load()
    me = get_user(data, q.from_user.id, q.from_user.username or "")

    if q.data == "balance":
        await q.edit_message_text(f"Balance: {me['balance']} 🪙\nReferrals: {len(me['referred'])}")
        return

    if q.data == "referral":
        link = f"https://t.me/{context.bot.username}?start={q.from_user.id}"
        await q.edit_message_text(f"Your referral link:\n{link}\n\nShare am, you go get 1000 per person.")
        return

    if q.data == "check_follow":
        me["followed"] = True
        save(data)
        await q.edit_message_text("Good! You don follow. Now use /done to confirm.")
        return

    if q.data == "withdraw":
        if me["balance"] < 10000:
            await q.edit_message_text(f"Balance too low. You get {me['balance']}, you need 10000 to withdraw.")
            return
        if len(me["referred"]) < 5:
            await q.edit_message_text(f"You need 5 referrals. You get {len(me['referred'])} now.")
            return
        if not me["followed"]:
            await q.edit_message_text("You never follow all channels. Follow first then click /done.")
            return
        await q.edit_message_text("You don qualify for withdraw! Send your wallet / account details to admin.")
        return

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load()
    me = get_user(data, update.effective_user.id, update.effective_user.username or "")
    me["followed"] = True
    save(data)
    await update.message.reply_text("Good! You don follow all channels. ✅\nNow you fit check Balance / Withdraw.")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot dey run...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
