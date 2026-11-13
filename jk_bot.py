import os, random, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from supabase import create_client

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

TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"
SUPABASE_URL = "https://ilwllhmxugtyrztybyer.supabase.co"
SUPABASE_KEY = "sb_publishable__N4Wb0jaK1zD2ZGWwxEMvA_-jCeCN7j"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

LINKS = [
    "https://whatsapp.com/channel/0029VbEN1ghKbYMV6vRhr407",
    "https://t.me/jk_coins",
    "https://youtube.com/@jungkookjeon40330?si=kPk-qdcINbMZrOPf",
    "https://www.tiktok.com/@justmeet06",
    "https://t.me/update_3334",
]

def load():
    try:
        res = supabase.table("users").select("*").execute()
        data = {}
        for row in res.data:
            data[str(row["id"])] = row["data"]
        return data
    except:
        return {}

def save(data):
    for uid, udata in data.items():
        try:
            supabase.table("users").upsert({"id": str(uid), "data": udata}).execute()
        except:
            pass

def get_user(data, uid):
    uid = str(uid)
    if uid not in data:
        data[uid] = {"balance": 0, "spins": 3, "referred": [], "followed": False, "username": ""}
    return data[uid]

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎰 SPIN NOW", callback_data="spin")],
        [InlineKeyboardButton("🎲 DICE GAME", callback_data="dice")],
        [InlineKeyboardButton("🪙 COIN FLIP", callback_data="coin")],
        [InlineKeyboardButton("🔢 GUESS NUMBER", callback_data="guess")],
        [InlineKeyboardButton("📋 FOLLOW 5 LINKS (UNLOCK)", callback_data="tasks")],
        [InlineKeyboardButton("💰 BALANCE", callback_data="balance")],
        [InlineKeyboardButton("💸 WITHDRAW", callback_data="withdraw")],
    ])

def is_locked(me):
    return not me["followed"]

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
                await context.bot.send_message(chat_id=int(referrer_id), text=f"New person join with your link! You don get +1 Spin. Spins: {ref['spins']}")
    save(data)
    lock = "🔒 LOCKED - Follow 5 links to unlock games" if is_locked(me) else "✅ UNLOCKED - You fit play all games"
    text = (
        f"Welcome {user.first_name} to JK SPIN BOT\n\n"
        f"Balance: {me['balance']} / 10000\n"
        f"Spins Left: {me['spins']}\n"
        f"Referrals: {len(me['referred'])} / 5\n"
        f"Status: {lock}\n\n"
        f"HOW E DEY WORK:\n"
        f"1. Follow 5 links FIRST to unlock games\n"
        f"2. Spin / Play games to reach 10000 = 100,000 Naira\n"
        f"3. 1 Invite = 1 Extra Spin\n"
        f"4. Follow 5 links + Refer 5 people before withdraw\n\n"
        f"Your Invite Link:\nhttps://t.me/{context.bot.username}?start={user.id}"
    )
    await update.message.reply_text(text, reply_markup=main_menu())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = load()
    me = get_user(data, q.from_user.id)

    # LOCK CHECK - for all games
    if q.data in ["spin", "dice", "coin", "guess", "balance"]:
        if is_locked(me):
            await q.edit_message_text(
                "🔒 LOCKED!\n\nYou must follow all 5 links FIRST before you fit play.\n\nClick FOLLOW 5 LINKS below, follow all, then type /done to unlock.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 FOLLOW 5 LINKS TO UNLOCK", callback_data="tasks")]])
            )
            return

    if q.data == "spin":
        if me["spins"] <= 0:
            await q.edit_message_text(f"No spin left! Invite 1 person = 1 spin.\nYour link: https://t.me/{context.bot.username}?start={q.from_user.id}", reply_markup=main_menu())
            return
        me["spins"] -= 1
        win = random.randint(100, 800)
        me["balance"] += win
        save(data)
        await q.edit_message_text(f"🎰 You spin... You win +{win}!\n\nBalance: {me['balance']} / 10000\nSpins Left: {me['spins']}", reply_markup=main_menu())

    elif q.data == "dice":
        if me["spins"] <= 0:
            await q.edit_message_text("No spin left! Invite person to get spin.", reply_markup=main_menu())
            return
        me["spins"] -= 1
        dice = random.randint(1, 6)
        if dice == 6:
            win = 1000
            msg = f"🎲 You roll {dice} - JACKPOT! +{win}"
        elif dice >= 4:
            win = 400
            msg = f"🎲 You roll {dice} - Nice! +{win}"
        else:
            win = 50
            msg = f"🎲 You roll {dice} - Small win +{win}"
        me["balance"] += win
        save(data)
        await q.edit_message_text(f"{msg}\n\nBalance: {me['balance']} / 10000\nSpins: {me['spins']}", reply_markup=main_menu())

    elif q.data == "coin":
        kb = [[InlineKeyboardButton("🪙 HEAD", callback_data="coin_head")],
              [InlineKeyboardButton("🪙 TAIL", callback_data="coin_tail")],
              [InlineKeyboardButton("⬅️ BACK", callback_data="back")]]
        await q.edit_message_text("Pick Head or Tail - Win 500 if you correct!", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data in ["coin_head", "coin_tail"]:
        if me["spins"] <= 0:
            await q.edit_message_text("No spin left!", reply_markup=main_menu())
            return
        me["spins"] -= 1
        result = random.choice(["head", "tail"])
        pick = "head" if q.data == "coin_head" else "tail"
        if pick == result:
            me["balance"] += 500
            msg = f"🪙 E come {result.upper()}! You WIN +500!"
        else:
            me["balance"] += 50
            msg = f"🪙 E come {result.upper()}! You lose, small +50"
        save(data)
        await q.edit_message_text(f"{msg}\n\nBalance: {me['balance']}\nSpins: {me['spins']}", reply_markup=main_menu())

    elif q.data == "guess":
        kb = []
        for n in range(1, 11):
            kb.append([InlineKeyboardButton(f"{n}", callback_data=f"guess_{n}")])
        kb.append([InlineKeyboardButton("⬅️ BACK", callback_data="back")])
        await q.edit_message_text("Guess number 1-10. If you correct, +800!", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data.startswith("guess_"):
        if me["spins"] <= 0:
            await q.edit_message_text("No spin left!", reply_markup=main_menu())
            return
        me["spins"] -= 1
        pick = int(q.data.split("_")[1])
        real = random.randint(1, 10)
        if pick == real:
            me["balance"] += 800
            msg = f"🔢 Number na {real}! You guess correct! +800"
        else:
            me["balance"] += 50
            msg = f"🔢 Number na {real}, you guess {pick}. Small +50"
        save(data)
        await q.edit_message_text(f"{msg}\n\nBalance: {me['balance']}\nSpins: {me['spins']}", reply_markup=main_menu())

    elif q.data == "tasks":
        txt = "Follow all 5 links, then come back:\n\n"
        for i, l in enumerate(LINKS, 1):
            txt += f"{i}. {l}\n"
        txt += "\nAfter you follow all, type /done to UNLOCK games"
        await q.edit_message_text(txt, reply_markup=main_menu())

    elif q.data == "balance":
        await q.edit_message_text(f"Balance: {me['balance']} / 10000\nSpins: {me['spins']}\nReferrals: {len(me['referred'])} / 5\nStatus: {'✅ Unlocked' if me['followed'] else '🔒 Locked'}", reply_markup=main_menu())

    elif q.data == "withdraw":
        if me["balance"] < 10000:
            await q.edit_message_text(f"You never reach 10000 yet. You get {me['balance']}.", reply_markup=main_menu())
            return
        if len(me["referred"]) < 5:
            await q.edit_message_text(f"You need 5 referrals. You get {len(me['referred'])} now.", reply_markup=main_menu())
            return
        if not me["followed"]:
            await q.edit_message_text("You never follow the 5 links yet.", reply_markup=main_menu())
            return
        await q.edit_message_text("You don qualify! Send your account details:\n\nBank - Account Number - Account Name", reply_markup=main_menu())

    elif q.data == "back":
        await q.edit_message_text(f"Balance: {me['balance']} / 10000\nSpins: {me['spins']}", reply_markup=main_menu())

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load()
    me = get_user(data, update.effective_user.id)
    me["followed"] = True
    save(data)
    await update.message.reply_text("✅ UNLOCKED! You don follow the 5 links. Now you fit play SPIN, DICE, COIN FLIP and GUESS NUMBER.", reply_markup=main_menu())

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot dey run...")
    app.run_polling()

if __name__ == "__main__":
    main()
