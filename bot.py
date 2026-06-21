import sqlite3
import random, string
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters


TOKEN = "8770070950:AAGd3q4Eg-EImiSBCc-67I77UFwk3vsjRQA"
CHANNEL = "@iranmusic49"
ADMIN_ID = 123456789


# =========================
# 🧠 DATABASE
# =========================

def db():
    return sqlite3.connect("bot.db")


def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        join_date TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        plan TEXT,
        username TEXT,
        status TEXT,
        receipt TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def add_user(user_id, username):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO users (user_id, username, join_date)
    VALUES (?, ?, ?)
    """, (user_id, username, str(datetime.now())))

    conn.commit()
    conn.close()


def add_order(user_id, plan, username):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO orders (user_id, plan, username, status, receipt, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, plan, username, "pending", "", str(datetime.now())))

    conn.commit()
    conn.close()


def update_receipt(user_id, receipt):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
    UPDATE orders
    SET receipt = ?, status = ?
    WHERE user_id = ? AND status = 'pending'
    """, (receipt, "waiting_admin", user_id))

    conn.commit()
    conn.close()


# =========================
# 🔍 MEMBERSHIP
# =========================

async def is_member(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# =========================
# 🧲 KEYBOARDS
# =========================

def join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 عضویت در کانال", url="https://t.me/iranmusic49")],
        [InlineKeyboardButton("✅ بررسی عضویت", callback_data="check")]
    ])


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 خرید سرویس ⚡️", callback_data="buy")]
    ])


# =========================
# 🚀 START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"

    add_user(user_id, username)

    text = (
        "👋 سلام به ربات vpnbarato🐆 خوش اومدی\n\n"
        "⚡️ به تبلیغات توجه نکن\n\n"
        "📌 برای ادامه باید عضو کانال باشی"
    )

    if await is_member(user_id, context):
        await update.message.reply_text(text, reply_markup=main_menu())
    else:
        await update.message.reply_text(text, reply_markup=join_keyboard())


# =========================
# 🔘 BUTTONS
# =========================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id


    # check member
    if query.data == "check":

        if await is_member(user_id, context):
            await query.message.edit_text("✅ تایید شد", reply_markup=main_menu())
        else:
            await query.message.edit_text("❌ هنوز عضو نیستی", reply_markup=join_keyboard())


    # BUY
    elif query.data == "buy":

        keyboard = [
            [InlineKeyboardButton("⚡️ V2RAYng", callback_data="v2rayng")]
        ]

        await query.message.edit_text(
            "🛒 یکی از سرویس‌ها رو انتخاب کن",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    # PRODUCT
    elif query.data == "v2rayng":

        keyboard = [
            [InlineKeyboardButton("⚡️ V2ray پرسرعت", callback_data="fast")]
        ]

        await query.message.edit_text(
            "⚡️ سرویس انتخاب شد",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    # PLANS
    elif query.data == "fast":

        keyboard = [
            [InlineKeyboardButton("10GB - 150k", callback_data="p1")],
            [InlineKeyboardButton("20GB - 250k", callback_data="p2")],
            [InlineKeyboardButton("30GB - 350k", callback_data="p3")],
            [InlineKeyboardButton("40GB - 450k", callback_data="p4")],
            [InlineKeyboardButton("50GB - 550k", callback_data="p5")]
        ]

        await query.message.edit_text(
            "💰 پلن رو انتخاب کن",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    # PLAN SELECT
    elif query.data.startswith("p"):

        context.user_data["plan"] = query.data

        keyboard = [
            [InlineKeyboardButton("🎲 رندوم", callback_data="random")],
            [InlineKeyboardButton("✏️ دلخواه", callback_data="custom")]
        ]

        await query.message.edit_text(
            "📃 نام کاربری رو انتخاب کن",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    # RANDOM USER
    elif query.data == "random":

        username = "user" + ''.join(random.choices(string.ascii_lowercase, k=5))

        context.user_data["username"] = username

        add_order(user_id, context.user_data["plan"], username)

        await send_payment(query, context)


    # CUSTOM USER
    elif query.data == "custom":

        context.user_data["step"] = "username"

        await query.message.edit_text(
            "✏️ نام کاربری رو بفرست"
        )


# =========================
# 💳 PAYMENT
# =========================

async def send_payment(query, context):

    prices = {
        "p1": "150,000",
        "p2": "250,000",
        "p3": "350,000",
        "p4": "450,000",
        "p5": "550,000"
    }

    plan = context.user_data.get("plan")

    text = (
        "💳 مرحله پرداخت\n\n"
        f"💰 مبلغ: {prices.get(plan)} تومان\n\n"
        "🏦 کارت:\n1234-5678-9012-3456\n\n"
        "🏦 کارت دوم:\n9876-5432-1098-7654\n\n"
        "📌 رسید رو ارسال کن"
    )

    await query.message.edit_text(text)


# =========================
# 📨 MESSAGES
# =========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    text = update.message.text


    # username custom
    if context.user_data.get("step") == "username":

        if len(text) > 10 or not text.isalnum():
            await update.message.reply_text("❌ نام کاربری اشتباهه")
            return

        context.user_data["username"] = text

        add_order(user_id, context.user_data["plan"], text)

        await update.message.reply_text("✅ ثبت شد")

        await update.message.reply_text("💳 حالا رسید رو ارسال کن")


    # receipt
    else:

        update_receipt(user_id, text)

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🛒 سفارش جدید\nUser: {user_id}\nPlan: {context.user_data.get('plan')}"
        )

        await update.message.reply_text("📩 رسید دریافت شد")


# =========================
# 🚀 RUN
# =========================

init_db()

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()