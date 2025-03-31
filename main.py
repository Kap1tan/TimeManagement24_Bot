import telebot
import schedule
import time
import threading
from telebot.types import ChatPermissions
from datetime import datetime
import pytz

# Константы
BOT_TOKEN = "8042834324:AAF8OI-FrONvnEc2EpALNYulq7zIvXXbbm8"
ADMIN_IDS = {804644988, 1465809468}  # ID админов
krasnoyarsk_tz = pytz.timezone('Asia/Krasnoyarsk')

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)
chat_id = None  # ID администрируемого чата

@bot.message_handler(commands=['start'])
def start_admin_mode(message):
    global chat_id
    if message.from_user.id in ADMIN_IDS:
        chat_id = message.chat.id
        bot.send_message(chat_id, "Бот запущен в этом чате! Теперь он будет управлять доступом по расписанию.")
        check_and_set_chat_permissions()

@bot.message_handler(commands=['time'])
def get_current_time(message):
    now = datetime.now(krasnoyarsk_tz)
    status = "Чат закрыт" if is_chat_closed(now) else "Чат открыт"
    bot.send_message(message.chat.id, f"Дата и время: {now.strftime('%Y-%m-%d %H:%M:%S')}\nДень недели: {now.strftime('%A')}\nСостояние: {status}")

@bot.message_handler(commands=['checktime'])
def check_time_status(message):
    try:
        _, time_str = message.text.split(maxsplit=1)
        check_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M').replace(tzinfo=moscow_tz)
        status = "Чат будет закрыт" if is_chat_closed(check_time) else "Чат будет открыт"
        bot.send_message(message.chat.id, f"На {time_str} {status}.")
    except Exception:
        bot.send_message(message.chat.id, "Неверный формат. Используйте: /checktime YYYY-MM-DD HH:MM")

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    bot.send_message(message.chat.id, "Привет! Этот чат управляется ботом.")
    check_and_set_chat_permissions()

def check_and_set_chat_permissions():
    now = datetime.now(krasnoyarsk_tz)
    if is_chat_closed(now):
        close_chat()
    else:
        open_chat()

def is_chat_closed(check_time):
    return check_time.weekday() in [5, 6] or check_time.hour >= 18 or check_time.hour < 9

def close_chat():
    if chat_id:
        bot.set_chat_permissions(chat_id, ChatPermissions(can_send_messages=False))
        bot.send_message(chat_id, "Чат закрыт. В данном чате запрещено отправлять сообщения до следующего открытия.")

def open_chat():
    if chat_id:
        bot.set_chat_permissions(chat_id, ChatPermissions(can_send_messages=True))
        bot.send_message(chat_id, "Доброе утро заказчики и подрядчики Krasbau.\nВы снова можете задавать свои вопросы и делиться фотоотчетом.")

def notify_closing():
    if chat_id:
        weekday = datetime.now(krasnoyarsk_tz).weekday()
        open_date = "в понедельник" if weekday == 4 else "завтра"
        bot.send_message(chat_id, f"Уважаемые заказчики и подрядчики Krasbau.\nЧат закрывается через 20 минут, откроется {open_date} в 9:00 и сможете снова задать свои вопросы и делиться фотоотчетом.")

schedule.every().day.at("17:40").do(notify_closing)
schedule.every().day.at("18:00").do(close_chat)
schedule.every().monday.at("09:00").do(open_chat)
schedule.every().tuesday.at("09:00").do(open_chat)
schedule.every().wednesday.at("09:00").do(open_chat)
schedule.every().thursday.at("09:00").do(open_chat)
schedule.every().friday.at("09:00").do(open_chat)

def schedule_checker():
    while True:
        schedule.run_pending()
        time.sleep(30)

threading.Thread(target=schedule_checker, daemon=True).start()
check_and_set_chat_permissions()
bot.polling(none_stop=True)
