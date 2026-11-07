import json, random, os, time, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

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

def is_locked(me):
    if not me.get("followed", False):
        return True
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
    bot_name = str(context.bot.username)
    my_link = "https://t.me/" + bot_name + "?start=" + str(user.id)
    if is_locked(me):
        txt = "LOCKED! ⛔\n\nYou must complete BOTH before bot go open:\n\n1. Follow my 5 links: " + ("YES ✅" if me.get("followed") else "NO ❌ - Click FOLLOW 5 LINKS + type /done") + "\n\n2. Refer 5 people: " + str(len(me.get("referred", []))) + " / 5\n\nYour Invite Link:\n" + my_link
        await update.message.reply_text(txt, reply_markup=locked_menu())
        return
    text = "Welcome " + user.first_name + " to JK SPIN BOT\n\nBalance: " + str(me["balance"]) + " / 10000\nSpins Left: " + str(me["spins"]) + "\nReferrals: " + str(len(me["referred"])) + " / 5\n\nHOW E DEY WORK:\n1. Spin to win till you reach 10000 = 100,000 Naira\n2. You get 3 free spins\n3. 1 Invite = 1 Extra Spin\n4. Follow 5 links + Refer 5 people before withdraw\n5. Top 50 referrers go win prize every month end!\n\nYour Invite Link:\n" + my_link
    await update.message.reply_text(text, reply_markup=main_menu())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = load()
    me = get_user(data, q.from_user.id)
    my_id = str(q.from_user.id)
    my_refs = len(me.get("referred", []))
    my_bal = me.get("balance", 0)
    bot_name = str(context.bot.username)
    my_link = "https://t.me/" + bot_name + "?start=" + my_id
    if q.data == "tasks":
        txt = "Follow all 5 links, then come back:\n\n"
        for i, l in enumerate(LINKS, 1):
            txt += str(i) + ". " + l + "\n"
        txt += "\nAfter you follow all, type /done"
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("I DON FOLLOW - CHECK UNLOCK", callback_data="check_unlock")]]))
        return
    if q.data == "refer":
        await q.edit_message_text("Share this link, make 5 people join:\n\n" + my_link + "\n\nReferrals: " + str(my_refs) + " / 5\nFollowed 5 links: " + ("YES ✅" if me.get("followed") else "NO ❌"), reply_markup=locked_menu())
        return
    if q.data == "check_unlock":
        if is_locked(me):
            await q.edit_message_text("Still LOCKED! ⛔\n\nFollowed 5 links: " + ("YES ✅" if me.get("followed") else "NO ❌") + "\nReferrals: " + str(my_refs) + " / 5\n\nYour link:\n" + my_link, reply_markup=locked_menu())
        else:
            await q.edit_message_text("UNLOCKED! ✅ Send /start to see menu.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("OPEN MENU", callback_data="menu")]]))
        return
    if is_locked(me):
        await q.edit_message_text("LOCKED! ⛔\n\nWithout following my 5 links + 5 referrals, NOTHING go open.\n\nFollowed: " + ("YES ✅" if me.get("followed") else "NO ❌") + "\nReferrals: " + str(my_refs) + " / 5\n\nYour link:\n" + my_link, reply_markup=locked_menu())
        return
    if q.data == "menu":
        await q.edit_message_text("JK SPIN BOT Menu\n\nBalance: " + str(my_bal) + " / 10000\nSpins Left: " + str(me["spins"]) + "\nReferrals: " + str(my_refs) + " / 5", reply_markup=main_menu())
        return
    if q.data == "leaderboard":
        ranked = get_leaderboard(data)
        my_pos = 0
        for i, (uid, u) in enumerate(ranked, 1):
            if uid == my_id:
                my_pos = i
                break
        txt = "TOP 50 LEADERBOARD - Most Referrals\nMonth End Prizes:\n1st = +5000 coins\n2nd = +3000 coins\n3rd = +2000 coins\n4th-10th = +500 coins\n\n"
        for i, (uid, u) in enumerate(ranked[:20], 1):
            name = u.get("username") or ("User " + uid[:4])
            refs = len(u.get("referred", []))
            bal = u.get("balance", 0)
            txt += str(i) + ". @" + str(name) + " - " + str(refs) + " invites - " + str(bal) + " coins\n"
        if len(ranked) > 20:
            txt += "\n... and " + str(len(ranked)-20) + " more people for Top 50\n"
        if my_pos:
            txt += "\nYou dey #" + str(my_pos) + " with " + str(my_refs) + " invites"
        else:
            txt += "\nYou never enter Top 50 yet. You get " + str(my_refs) + " invites. Share your link!"
        txt += "\n\nYour link:\nhttps://t.me/" + bot_name + "?start=" + my_id
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("SEE TOP 21-50", callback_data="leaderboard2")],[InlineKeyboardButton("MENU", callback_data="menu")]]))
        return
    if q.data == "leaderboard2":
        ranked = get_leaderboard(data)
        txt = "TOP 50 LEADERBOARD - 21 to 50\n\n"
        for i, (uid, u) in enumerate(ranked, 1):
            if 21 <= i <= 50:
                name = u.get("username") or ("User " + uid[:4])
                refs = len(u.get("referred", []))
                bal = u.get("balance", 0)
                txt += str(i) + ". @" + str(name) + " - " + str(refs) + " invites - " + str(bal) + " coins\n"
        if len(ranked) < 21:
            txt += "Nobody dey here yet. Na you fit be first!"
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("BACK TO TOP 1-20", callback_data="leaderboard")],[InlineKeyboardButton("MENU", callback_data="menu")]]))
        return
    if q.data == "spin":
        if me["spins"] <= 0:
            await q.edit_message_text("No spin left! Invite 1 person = 1 spin.\nYour link: https://t.me/" + bot_name + "?start=" + my_id, reply_markup=back_menu())
            return
        me["spins"] -= 1
        win = random.randint(100, 800)
        me["balance"] += win
        save(data)
        await q.edit_message_text("You spin... You win +" + str(win) + " points!\n\nBalance: " + str(me["balance"]) + " / 10000\nSpins Left: " + str(me["spins"]), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("SPIN AGAIN", callback_data="spin")],[InlineKeyboardButton("MENU", callback_data="menu")]]))
        return
    if q.data == "dice":
        roll = random.randint(1, 6)
        if roll == 6:
            me["balance"] += 200
            txt = "You roll " + str(roll) + " - JACKPOT! +200 coins!\nBalance: " + str(me["balance"]) + " / 10000"
        elif roll >= 4:
            me["balance"] += 50
            txt = "You roll " + str(roll) + " - Nice! +50 coins\nBalance: " + str(me["balance"]) + " / 10000"
        else:
            txt = "You roll " + str(roll) + " - Oops, try again! No win.\nBalance: " + str(me["balance"]) + " / 10000"
        save(data)
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ROLL AGAIN", callback_data="dice")],[InlineKeyboardButton("MENU", callback_data="menu")]]))
        return
    if q.data == "coin_choice":
        kb = [[InlineKeyboardButton("HEAD", callback_data="coin_head"), InlineKeyboardButton("TAIL", callback_data="coin_tail")],[InlineKeyboardButton("MENU", callback_data="menu")]]
        await q.edit_message_text("Coin Flip - Pick one:", reply_markup=InlineKeyboardMarkup(kb))
        return
    if q.data in ["coin_head", "coin_tail"]:
        pick = "head" if q.data == "coin_head" else "tail"
        result = random.choice(["head", "tail"])
        if pick == result:
            me["balance"] += 100
            txt = "E land " + result.upper() + "! You win +100 coins!\nBalance: " + str(me["balance"]) + " / 10000"
        else:
            txt = "E land " + result.upper() + "! You lose, try again.\nBalance: " + str(me["balance"]) + " / 10000"
        save(data)
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("FLIP AGAIN", callback_data="coin_choice")],[InlineKeyboardButton("MENU", callback_data="menu")]]))
        return
    if q.data == "lucky":
        kb = []
        for i in range(1, 11):
            kb.append(InlineKeyboardButton(str(i), callback_data="lucky_" + str(i)))
        rows = [kb[0:5], kb[5:10], [InlineKeyboardButton("MENU", callback_data="menu")]]
        await q.edit_message_text("Lucky Number - Pick 1 to 10:\nIf you guess correct, you win +500 coins!", reply_markup=InlineKeyboardMarkup(rows))
        return
    if q.data.startswith("lucky_"):
        pick = int(q.data.split("_")[1])
        win_num = random.randint(1, 10)
        if pick == win_num:
            me["balance"] += 500
            txt = "Lucky Number na " + str(win_num) + ", you pick " + str(pick) + " - CORRECT! +500 coins!\nBalance: " + str(me["balance"]) + " / 10000"
        else:
            txt = "Lucky Number na " + str(win_num) + ", you pick " + str(pick) + " - Wrong o, try again!\nBalance: " + str(me["balance"]) + " / 10000"
        save(data)
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("PLAY AGAIN", callback_data="lucky")],[InlineKeyboardButton("MENU", callback_data="menu")]]))
        return
    if q.data == "daily":
        now = time.time()
        last = me.get("last_bonus", 0)
        if now - last < 86400:
            left = int((86400 - (now - last)) // 3600)
            await q.edit_message_text("You don collect today already! Come back in " + str(left) + " hours.", reply_markup=back_menu())
        else:
            me["balance"] += 50
            me["last_bonus"] = now
            save(data)
            await q.edit_message_text("Daily Bonus! +50 coins!\nBalance: " + str(me["balance"]) + " / 10000", reply_markup=back_menu())
        return
    elif q.data == "balance":
        await q.edit_message_text("Balance: " + str(me["balance"]) + " / 10000\nSpins: " + str(me["spins"]) + "\nReferrals: " + str(len(me["referred"])) + " / 5", reply_markup=back_menu())
    elif q.data == "withdraw":
        if me["balance"] < 10000:
            await q.edit_message_text("You never reach 10000 yet. You get " + str(me["balance"]) + ". Keep spinning!", reply_markup=back_menu())
            return
        if len(me["referred"]) < 5:
            await q.edit_message_text("You need 5 referrals to withdraw. You get " + str(len(me["referred"])) + " now.", reply_markup=back_menu())
            return
        if not me["followed"]:
            await q.edit_message_text("You never follow the 5 links yet. Click FOLLOW 5 LINKS, follow all, then type /done", reply_markup=back_menu())
            return
        await q.edit_message_text("You don qualify! Send your account details like this:\n\nBank - Account Number - Account Name\n\nExample: Opay - 1234567890 - John Doe", reply_markup=back_menu())

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load()
    me = get_user(data, update.effective_user.id)
    me["followed"] = True
    save(data)
    await update.message.reply_text("Good! We don mark say you don follow the 5 links. Now you still need 5 referrals to unlock. Send /start to check.")

async def leaderboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load()
    me = get_user(data, update.effective_user.id)
    if is_locked(me):
        await update.message.reply_text("LOCKED! Follow 5 links + Refer 5 people first. Send /start")
        return
    ranked = get_leaderboard(data)
    txt = "TOP 50 LEADERBOARD\n\n"
    for i, (uid, u) in enumerate(ranked[:10], 1):
        name = u.get("username") or ("User " + uid[:4])
        refs = len(u.get("referred", []))
        txt += str(i) + ". @" + str(name) + " - " + str(refs) + " invites\n"
    await update.message.reply_text(txt)

async def main():
    if not TOKEN:
        print("ERROR: BOT_TOKEN no dey!")
        return
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("leaderboard", leaderboard_cmd))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot dey run...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
