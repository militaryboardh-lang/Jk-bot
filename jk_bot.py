import json, random, os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

TOKEN = "9218454434:AAGM9fF85XyqZ26UkNAHBijA-Op5DijAU0c"

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
        data[uid] = {"balance": 0, "spins": 3, "referred": [], "followed": False, "username": ""}
    return data[uid]

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
        f"4. Follow 5 links + Refer 5 people before withdraw\n\n"
        f"Your Invite Link:\nhttps://t.me/{context.bot.username}?start={user.id}"
    )
    kb = [[InlineKeyboardButton("SPIN NOW", callback_data="spin")],
          [InlineKeyboardButton("FOLLOW 5 LINKS", callback_data="tasks")],
          [InlineKeyboardButton("BALANCE", callback_data="balance")],
          [InlineKeyboardButton("WITHDRAW", callback_data="withdraw")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = load()
    me = get_user(data, q.from_user.id)
    if q.data == "spin":
        if me["spins"] <= 0:
            await q.edit_message_text(f"No spin left! Invite 1 person = 1 spin.\nYour link: https://t.me/{context.bot.username}?start={q.from_user.id}")
            return
        me["spins"] -= 1
        win = random.randint(100, 800)
        me["balance"] += win
        save(data)
        await q.edit_message_text(f"You spin... You win +{win} points!\n\nBalance: {me['balance']} / 10000\nSpins Left: {me['spins']}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("SPIN AGAIN", callback_data="spin")]]))
    elif q.data == "tasks":
        txt = "Follow all 5 links, then come back:\n\n"
        for i, l in enumerate(LINKS, 1):
            txt += f"{i}. {l}\n"
        txt += "\nAfter you follow all, type /done"
        await q.edit_message_text(txt)
    elif q.data == "balance":
        await q.edit_message_text(f"Balance: {me['balance']} / 10000\nSpins: {me['spins']}\nReferrals: {len(me['referred'])} / 5")
    elif q.data == "withdraw":
        if me["balance"] < 10000:
            await q.edit_message_text(f"You never reach 10000 yet. You get {me['balance']}. Keep spinning!")
            return
        if len(me["referred"]) < 5:
            await q.edit_message_text(f"You need 5 referrals to withdraw. You get {len(me['referred'])} now.")
            return
        if not me["followed"]:
            await q.edit_message_text("You never follow the 5 links yet. Click FOLLOW 5 LINKS, follow all, then type /done")
            return
        await q.edit_message_text("You don qualify! Send your account details like this:\n\nBank - Account Number - Account Name\n\nExample: Opay - 1234567890 - John Doe")

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load()
    me = get_user(data, update.effective_user.id)
    me["followed"] = True
    save(data)
    await update.message.reply_text("Good! We don mark say you don follow the 5 links. Now go spin and refer.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot dey run...")
    app.run_polling()

if __name__ == "__main__":
    main()
