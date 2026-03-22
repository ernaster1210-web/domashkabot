import os
import telebot
from telebot import types
from groq import Groq
import psycopg2

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")
FREE_ANSWERS = 10
ADMIN_ID = 8497206375

bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)
waiting_users = set()

def get_db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            balance INT DEFAULT 10,
            premium BOOLEAN DEFAULT FALSE,
            used_ref BOOLEAN DEFAULT FALSE
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

def get_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT balance, premium, used_ref FROM users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    if not user:
        cur.execute("INSERT INTO users (user_id) VALUES (%s)", (user_id,))
        conn.commit()
        user = (FREE_ANSWERS, False, False)
    cur.close()
    conn.close()
    return user

def update_balance(user_id, amount):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (amount, user_id))
    conn.commit()
    cur.close()
    conn.close()

def set_premium(user_id, value):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET premium = %s WHERE user_id = %s", (value, user_id))
    conn.commit()
    cur.close()
    conn.close()

def set_used_ref(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET used_ref = TRUE WHERE user_id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

init_db()
user_history = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    user = get_user(user_id)
    balance, premium, used_ref = user
    args = message.text.split()
    if len(args) > 1:
        try:
            ref_id = int(args[1])
            if ref_id != user_id and not used_ref:
                set_used_ref(user_id)
                update_balance(ref_id, 3)
                bot.send_message(ref_id, "🎉 По твоей ссылке зашёл новый пользователь! +3 ответа!")
        except:
            pass
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("💰 Баланс"), types.KeyboardButton("💎 Подписка"))
    markup.add(types.KeyboardButton("🔗 Поделиться (+3 ответа)"))
    bot.send_message(message.chat.id,
        f"⭐️ Привет, {name}!\n\n"
        f"🤖 Я — УмникКЗ, твой умный помощник для учёбы!\n\n"
        f"📚 Объясню любую тему простым языком\n"
        f"✏️ Помогу с домашним заданием\n"
        f"🇬🇧 Переведу текст на английский и обратно\n"
        f"🔢 Решу задачи по математике и физике\n"
        f"💡 Отвечу на любой вопрос за секунды\n"
        f"⚡️ Работаю 24/7\n\n"
        f"💰 Баланс: {balance} ответов\n\n"
        f"✨ Просто напиши свой вопрос!",
        reply_markup=markup)

@bot.message_handler(commands=['myid'])
def my_id(message):
    bot.send_message(message.chat.id, f"Твой ID: {message.from_user.id}")

@bot.message_handler(commands=['premium'])
def give_premium(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У тебя нет прав!")
        return
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "Напиши: /premium ID_пользователя")
        return
    try:
        user_id = int(args[1])
        get_user(user_id)
        set_premium(user_id, True)
        bot.send_message(message.chat.id, f"✅ Пользователь {user_id} получил премиум!")
        bot.send_message(user_id, "💎 Тебе выдан премиум — безлимитные ответы!")
    except:
        bot.send_message(message.chat.id, "❌ Неверный ID")
                         
        @bot.message_handler(commands=['unpremium'])
def remove_premium(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У тебя нет прав!")
        return
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "Напиши: /unpremium ID_пользователя")
        return
    try:
        user_id = int(args[1])
        set_premium(user_id, False)
        bot.send_message(message.chat.id, f"✅ Премиум у пользователя {user_id} забран!")
        bot.send_message(user_id, "❌ Твой премиум закончился. Напиши @mxm1210 для продления.")
    except:
        bot.send_message(message.chat.id, "❌ Неверный ID")

@bot.message_handler(func=lambda m: m.text == "💰 Баланс")
def balance(message):
    user = get_user(message.from_user.id)
    balance, premium, _ = user
    if premium:
        bot.send_message(message.chat.id, "💎 У тебя премиум — безлимитные ответы!")
    else:
        bot.send_message(message.chat.id, f"💰 Твой баланс: {balance} ответов")

@bot.message_handler(func=lambda m: m.text == "💎 Подписка")
def subscription(message):
    bot.send_message(message.chat.id,
        "💎 Подписка — безлимитные ответы!\n\n"
        "💰 Стоимость: 500 тенге в месяц\n\n"
        "📩 Для оплаты напиши админу: @mxm1210")

@bot.message_handler(func=lambda m: m.text == "🔗 Поделиться (+3 ответа)")
def share(message):
    bot.send_message(message.chat.id,
        f"🔗 Поделись ботом с друзьями и получи +3 ответа!\n\n"
        f"Твоя ссылка: t.me/KazStudyBot?start={message.from_user.id}")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    if user_id in waiting_users:
        bot.send_message(message.chat.id, "⏳ Подожди, я ещё думаю...")
        return
    waiting_users.add(user_id)
    user = get_user(user_id)
    balance, premium, _ = user
    if balance <= 0 and not premium:
        waiting_users.discard(user_id)
        bot.send_message(message.chat.id,
            "❌ У тебя закончились ответы!\n\n"
            "💎 Купи подписку или поделись ботом!")
        return
    if not premium:
        update_balance(user_id, -1)
    bot.send_message(message.chat.id, "⏳ Смотрю на задание...")
    file_info = bot.get_file(message.photo[-1].file_id)
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "user", "content": [
                {"type": "text", "text": "Реши это задание. Объясни решение по шагам на русском языке. Не используй символы # * $ и другое форматирование."},
                {"type": "image_url", "image_url": {"url": file_url}}
            ]}
        ]
    )
    answer_text = response.choices[0].message.content
    answer_text = answer_text.replace("**", "").replace("##", "").replace("$", "").replace("#", "")
    user = get_user(user_id)
    remaining = user[0]
    waiting_users.discard(user_id)
    bot.send_message(message.chat.id,
        f"{answer_text}\n\n"
        f"💰 Осталось ответов: {remaining}")

@bot.message_handler(func=lambda message: True)
def answer(message):
    user_id = message.from_user.id
    if user_id in waiting_users:
        bot.send_message(message.chat.id, "⏳ Подожди, я ещё думаю...")
        return
    waiting_users.add(user_id)
    user = get_user(user_id)
    balance, premium, _ = user
    if balance <= 0 and not premium:
        waiting_users.discard(user_id)
        bot.send_message(message.chat.id,
            "❌ У тебя закончились ответы!\n\n"
            "💎 Купи подписку или поделись ботом!")
        return
    if not premium:
        update_balance(user_id, -1)
    if user_id not in user_history:
        user_history[user_id] = []
        user_history[user_id].append({"role": "user", "content": message.text})
    if len(user_history[user_id]) > 10:
        user_history[user_id] = user_history[user_id][-10:]
    bot.send_message(message.chat.id, "⏳ Думаю...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Ты умный помощник для казахстанских школьников. Отвечай на русском языке, простым и понятным языком. Не используй символы # * $ и другое форматирование."}
        ] + user_history[user_id]
    )
    answer_text = response.choices[0].message.content
    answer_text = answer_text.replace("**", "").replace("##", "").replace("$", "").replace("#", "")
    user_history[user_id].append({"role": "assistant", "content": answer_text})
    user = get_user(user_id)
    remaining = user[0]
    waiting_users.discard(user_id)
    bot.send_message(message.chat.id,
        f"{answer_text}\n\n"
        f"💰 Осталось ответов: {remaining}")

bot.polling()
