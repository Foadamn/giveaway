import sqlite3
import random
import time
from telebot import TeleBot, types

# -----------------------
# تنظیمات اولیه
# -----------------------
TOKEN = "8176985504:AAGdofFxnD_kg8G7ttsERtskB-lUqfTVL4c"
ADMIN_ID = 1946672017
CHANNEL_USERNAME = "FonorYT"

bot = TeleBot(TOKEN)

# -----------------------
# دیتابیس
# -----------------------
conn = sqlite3.connect("lottery.db", check_same_thread=False)
cursor = conn.cursor()

# ایجاد جداول
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS participants (
    user_id INTEGER PRIMARY KEY,
    username TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS lottery_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    winner_username TEXT,
    winner_user_id INTEGER,
    prize_amount REAL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS current_lottery (
    id INTEGER PRIMARY KEY,
    is_active INTEGER DEFAULT 0,
    prize_amount REAL DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS winner_info (
    user_id INTEGER PRIMARY KEY,
    winner_username TEXT,
    card_info TEXT,
    is_paid INTEGER DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS states (
    user_id INTEGER PRIMARY KEY,
    state TEXT
)
""")
conn.commit()

# -----------------------
# توابع کمکی
# -----------------------
def set_state(user_id: int, state: str):
    cursor.execute("REPLACE INTO states (user_id, state) VALUES (?, ?)", (user_id, state))
    conn.commit()

def get_state(user_id: int):
    cursor.execute("SELECT state FROM states WHERE user_id = ?", (user_id,))
    r = cursor.fetchone()
    return r[0] if r else None

def clear_state(user_id: int):
    cursor.execute("DELETE FROM states WHERE user_id = ?", (user_id,))
    conn.commit()

def is_user_member(user_id: int) -> bool:
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        return False

# -----------------------
# کیبوردها
# -----------------------
# دکمه عضویت در کانال (برای وقتی که کاربر عضو نیست و میخواد شرکت کنه)
def get_channel_lock_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(text="عضویت در کانال 📢", url=f"https://t.me/{CHANNEL_USERNAME}"))
    # دکمه بررسی مجدد نمی‌ذاریم چون کاربر باید دوباره روی "شرکت کردن" اصلی کلیک کنه، اینجوری ساده‌تره
    return markup

def get_support_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(text="پشتیبانی💬", url="https://t.me/FonorYT_support"))
    return markup

def get_youtube_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(text="چنل یوتیوب▶", url="https://www.youtube.com/@FONORAM"))
    return markup

def get_join_button():
    cursor.execute("SELECT is_active FROM current_lottery WHERE id=1")
    row = cursor.fetchone()
    kb = types.InlineKeyboardMarkup(row_width=1)
    if row and row[0] == 1:
        kb.add(types.InlineKeyboardButton(text="شرکت کردن🙋‍♂️", callback_data="join_lottery"))
    # دکمه‌های عمومی رو هم زیر دکمه شرکت کردن اضافه می‌کنیم که همیشه باشن
    kb.add(types.InlineKeyboardButton(text="چنل یوتیوب▶", url="https://www.youtube.com/@FONORAM"))
    kb.add(types.InlineKeyboardButton(text="پشتیبانی💬", url="https://t.me/FonorYT_support"))
    return kb

def get_main_menu():
    # منوی اصلی وقتی قرعه کشی نیست
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(text="چنل یوتیوب▶", url="https://www.youtube.com/@FONORAM"))
    kb.add(types.InlineKeyboardButton(text="پشتیبانی💬", url="https://t.me/FonorYT_support"))
    return kb

# ==============================================================================
#  بخش دستورات (Commands)
# ==============================================================================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    # همیشه کاربر را ذخیره می‌کنیم تا پیام‌های اطلاع‌رسانی را بگیرد
    cursor.execute("INSERT OR REPLACE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    clear_state(user_id)

    # چک می‌کنیم قرعه‌کشی فعال است یا نه
    cursor.execute("SELECT is_active, prize_amount FROM current_lottery WHERE id=1")
    row = cursor.fetchone()

    # بدون چک کردن عضویت، منو را نمایش می‌دهیم
    if row and row[0] == 1:
        prize = row[1]
        bot.send_message(message.chat.id, 
                         f"سلام {message.from_user.first_name} عزیز! ❤️\nبه ربات قرعه‌کشی Fonor خوش اومدی.\n\n🎉 یک قرعه‌کشی فعال با جایزه {prize} داریم!\nبرای برنده شدن کافیه روی دکمه زیر بزنی👇", 
                         reply_markup=get_join_button())
    else:
        bot.send_message(message.chat.id, 
                         f"سلام {message.from_user.first_name} عزیز! ❤️\nبه ربات قرعه‌کشی Fonor خوش اومدی.\n\nدر حال حاضر قرعه‌کشی فعالی نداریم، اما به محض شروع بهت خبر میدیم! 👀", 
                         reply_markup=get_main_menu())

@bot.message_handler(commands=['about'])
def about(message):
    bot.reply_to(message, "ما هر چند وقت یه بار داخل ویدیو های یوتیوب جوایز مختلف میزاریم. چنل رو ساب کن تا از دست ندی!", reply_markup=get_youtube_keyboard())

@bot.message_handler(commands=['support'])
def support_cmd(message):
    bot.reply_to(message, "برای ارتباط با پشتیبانی یا گزارش مشکل کلیک کنید:", reply_markup=get_support_keyboard())

# --- دستورات ادمین ---

@bot.message_handler(commands=['start_lottery'])
def start_lottery(message):
    if message.from_user.id != ADMIN_ID: return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "فرمت: /start_lottery <مبلغ>\nمثال: /start_lottery 100000")
        return
    try:
        amount = float(parts[1])
        cursor.execute("INSERT OR REPLACE INTO current_lottery (id, is_active, prize_amount) VALUES (1, 1, ?)", (amount,))
        cursor.execute("DELETE FROM participants")
        conn.commit()
        
        # اطلاع رسانی به همه کاربران (چه عضو باشند چه نباشند)
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        count = 0
        for (u_id,) in users:
            try:
                bot.send_message(u_id, f"🚨 توجه توجه!\n\n🎉 قرعه‌کشی بزرگ جدید با جایزه {amount} شروع شد!\nهمین الان دکمه زیر رو بزن تا جا نمونی👇", reply_markup=get_join_button())
                count += 1
                time.sleep(0.05)
            except: pass
        bot.reply_to(message, f"✅ قرعه‌کشی فعال شد و به {count} نفر اطلاع داده شد.")
    except ValueError:
        bot.reply_to(message, "مبلغ باید عدد باشد.")

@bot.message_handler(commands=['end_lottery'])
def end_lottery(message):
    if message.from_user.id != ADMIN_ID: return
    
    cursor.execute("SELECT user_id, username FROM participants")
    participants = cursor.fetchall()
    
    if not participants:
        bot.reply_to(message, "❌ هیچکس شرکت نکرده است.")
        return

    winner = random.choice(participants)
    winner_id = winner[0]
    winner_username = winner[1] if winner[1] else "No Username"
    
    cursor.execute("SELECT prize_amount FROM current_lottery WHERE id=1")
    row = cursor.fetchone()
    prize = row[0] if row else 0

    cursor.execute("INSERT INTO lottery_history (winner_username, winner_user_id, prize_amount) VALUES (?, ?, ?)", 
                   (winner_username, winner_id, prize))
    conn.commit()

    bot.reply_to(message, "⏳ در حال اعلام نتایج...")
    
    # اطلاع رسانی به شرکت‌کنندگان
    for part_id, part_username in participants:
        try:
            if part_id != winner_id:
                bot.send_message(part_id, f"📣 قرعه‌کشی تمام شد.\n🏆 برنده: @{winner_username}\n💰 جایزه: {prize}\n\nشانست رو تو قرعه‌کشی بعدی امتحان کن! ❤️")
            time.sleep(0.05) 
        except Exception as e: pass
    
    # پیام به برنده
    try:
        bot.send_message(winner_id, f"🎉 تبریک!!! شما برنده جایزه {prize} شدید! 🎁\n\nلطفاً شماره کارت و نام صاحب کارت را همینجا ارسال کنید.")
        cursor.execute("INSERT OR REPLACE INTO winner_info (user_id, winner_username, card_info, is_paid) VALUES (?, ?, NULL, 0)", (winner_id, winner_username))
        conn.commit()
        set_state(winner_id, "wait_card")
    except Exception as e:
        bot.reply_to(message, f"⚠️ نتوانستم به برنده پیام بدم: {e}")

    cursor.execute("UPDATE current_lottery SET is_active = 0 WHERE id=1")
    cursor.execute("DELETE FROM participants")
    conn.commit()

    bot.reply_to(message, f"✅ پایان قرعه‌کشی.\nبرنده: @{winner_username}")

@bot.message_handler(commands=['confirm'])
def confirm_payment(message):
    if message.from_user.id != ADMIN_ID: return
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "فرمت: /confirm <user_id>")
        return
    try:
        target_id = int(parts[1])
        cursor.execute("UPDATE winner_info SET is_paid=1 WHERE user_id=?", (target_id,))
        if cursor.rowcount > 0:
            conn.commit()
            bot.reply_to(message, "✅ تایید شد.")
            try:
                bot.send_message(target_id, "✅ جایزه شما واریز شد! مبارکتون باشه 🌹")
            except: pass
        else:
            bot.reply_to(message, "❌ کاربر یافت نشد.")
    except ValueError:
        bot.reply_to(message, "آیدی نامعتبر است.")

@bot.message_handler(commands=['list'])
def list_participants(message):
    if message.from_user.id != ADMIN_ID: return
    cursor.execute("SELECT username, user_id FROM participants")
    rows = cursor.fetchall()
    msg = f"👥 تعداد شرکت‌کنندگان: {len(rows)}\n------------------\n"
    for r in rows:
        msg += f"- {r[0]} ({r[1]})\n"
    if len(msg) > 4000: bot.reply_to(message, msg[:4000])
    else: bot.reply_to(message, msg)

@bot.message_handler(commands=['history'])
def show_history(message):
    if message.from_user.id != ADMIN_ID: return
    cursor.execute("SELECT winner_username, prize_amount, date FROM lottery_history ORDER BY id DESC LIMIT 10")
    rows = cursor.fetchall()
    msg = "📜 10 قرعه‌کشی اخیر:\n\n"
    for r in rows:
        msg += f"👤 {r[0]} | 💰 {r[1]} | 📅 {r[2]}\n"
    bot.reply_to(message, msg)

# ==============================================================================
#  بخش عملیات خاص
# ==============================================================================

@bot.message_handler(commands=['broadcast'])
def start_broadcast_command(message):
    if message.from_user.id != ADMIN_ID: return
    set_state(ADMIN_ID, "broadcast")
    bot.reply_to(message, "📣 پیام خود را بفرستید تا برای همه ارسال شود (/cancel برای لغو).")

@bot.message_handler(func=lambda m: get_state(m.from_user.id) == "broadcast" and m.from_user.id == ADMIN_ID, content_types=['text','photo','video','document','voice','animation'])
def execute_broadcast(message):
    clear_state(ADMIN_ID)
    if message.content_type == 'text' and message.text == '/cancel':
        bot.reply_to(message, "لغو شد.")
        return
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    bot.reply_to(message, f"⏳ ارسال به {len(users)} نفر...")
    for (u_id,) in users:
        try:
            bot.copy_message(u_id, message.chat.id, message.message_id)
            time.sleep(0.04)
        except: pass
    bot.reply_to(message, "✅ تمام شد.")

@bot.message_handler(func=lambda m: get_state(m.from_user.id) == "wait_card", content_types=['text'])
def get_winner_card(message):
    user_id = message.from_user.id
    card_text = message.text
    cursor.execute("UPDATE winner_info SET card_info = ? WHERE user_id = ?", (card_text, user_id))
    conn.commit()
    clear_state(user_id)
    bot.reply_to(message, "✅ دریافت شد. بزودی مبلغ جایزه براتون واریز و اطلاع داده میشه!")
    bot.send_message(ADMIN_ID, f"💳 کارت برنده (ID: {user_id}):\n\n{card_text}\n\nتایید: /confirm {user_id}")

# ==============================================================================
#  کالبک (منطق اصلی قفل جوین)
# ==============================================================================

@bot.callback_query_handler(func=lambda call: call.data == "join_lottery")
def callback_join(call):
    user_id = call.from_user.id
    username = call.from_user.username
    
    # 1. بررسی فعال بودن قرعه‌کشی
    cursor.execute("SELECT is_active, prize_amount FROM current_lottery WHERE id=1")
    lottery = cursor.fetchone()
    
    if not lottery or lottery[0] == 0:
        bot.answer_callback_query(call.id, "مهلت قرعه‌کشی تمام شده!", show_alert=True)
        return

    # 2. بررسی عضویت در کانال (اینجا قفل می‌ذاریم)
    if not is_user_member(user_id):
        bot.answer_callback_query(call.id, "❌ شما عضو کانال نیستید!", show_alert=True)
        bot.send_message(call.message.chat.id, 
                         "⛔ برای شرکت در قرعه‌کشی ابتدا باید عضو کانال ما باشید.\nلطفاً عضو شوید و دوباره دکمه شرکت کردن را بزنید:", 
                         reply_markup=get_channel_lock_keyboard())
        return

    # 3. ثبت نام (اگر عضو بود)
    cursor.execute("SELECT * FROM participants WHERE user_id=?", (user_id,))
    if cursor.fetchone():
        bot.answer_callback_query(call.id, "شما قبلاً ثبت‌نام کرده‌اید خیالت راحت! 😉", show_alert=True)
    else:
        cursor.execute("INSERT INTO participants (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
        bot.answer_callback_query(call.id, "✅ ثبت شد!", show_alert=False)
        bot.send_message(call.message.chat.id, f"🎉 تبریک! نام شما برای جایزه {lottery[1]} ثبت شد.")

# ==============================================================================
#  هندلر عمومی
# ==============================================================================

@bot.message_handler(func=lambda m: True)
def handle_all_other_messages(message):
    if message.chat.type == 'private':
        # پاسخ هوشمندانه‌تر
        bot.reply_to(message, "دستور را متوجه نشدم.\nاگر سوالی دارید از دکمه پشتیبانی استفاده کنید یا /start را بزنید.")

# -----------------------
# اجرا
# -----------------------
print("Bot Running with Join-Lock Logic...")
bot.infinity_polling(skip_pending=True)