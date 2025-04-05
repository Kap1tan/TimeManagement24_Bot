import telebot
import schedule
import time
import threading
from telebot.types import ChatPermissions
from datetime import datetime
import pytz

# Константы
BOT_TOKEN = "8042834324:AAGOiIjWcGKckps2ZSbvjMW1A7u00hvJPNc"
ADMIN_IDS = {804644988, 1465809468}  # ID админов
krasnoyarsk_tz = pytz.timezone('Asia/Krasnoyarsk')  # Часовой пояс не изменился, но время будет уменьшено на 8 часов в функциях

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)
chat_id = None  # ID администрируемого чата

@bot.message_handler(commands=['start'])
def start_admin_mode(message):
    global chat_id
    if message.from_user.id in ADMIN_IDS:
        chat_id = message.chat.id
        bot.send_message(chat_id, "Бот запущен в этом чате. Управление доступом по расписанию активировано.")
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
        check_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M').replace(tzinfo=krasnoyarsk_tz)
        status = "Чат будет закрыт" if is_chat_closed(check_time) else "Чат будет открыт"
        bot.send_message(message.chat.id, f"На {time_str} {status}.")
    except Exception:
        bot.send_message(message.chat.id, "Неверный формат. Используйте: /checktime YYYY-MM-DD HH:MM")

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    bot.send_message(message.chat.id, "Добро пожаловать. Чат управляется автоматически.")
    check_and_set_chat_permissions()

def check_and_set_chat_permissions():
    now = datetime.now(krasnoyarsk_tz)
    if is_chat_closed(now):
        close_chat()
    else:
        open_chat()

def is_chat_closed(check_time):
    # Уменьшаем время на 8 часов для проверки
    adjusted_hour = (check_time.hour - 8) % 24
    return check_time.weekday() in [5, 6] or adjusted_hour >= 18 or adjusted_hour < 9

def close_chat():
    if chat_id:
        bot.set_chat_permissions(chat_id, ChatPermissions(can_send_messages=False))
        bot.send_message(chat_id, "Чат закрыт. Отправка сообщений временно недоступна.")

def open_chat():
    if chat_id:
        bot.set_chat_permissions(chat_id, ChatPermissions(can_send_messages=True))
        bot.send_message(chat_id, "Чат открыт. Отправка сообщений доступна.")

def notify_closing():
    if chat_id:
        bot.send_message(chat_id, "Чат будет закрыт через 20 минут. Следующее открытие в 9:00.")

# Скорректированное расписание с учетом -8 часов
schedule.every().day.at("13:40").do(notify_closing)  # 21:40 - 8 = 13:40
schedule.every().day.at("14:00").do(close_chat)      # 22:00 - 8 = 14:00
schedule.every().monday.at("05:00").do(open_chat)    # 13:00 - 8 = 05:00
schedule.every().tuesday.at("05:00").do(open_chat)   # 13:00 - 8 = 05:00
schedule.every().wednesday.at("05:00").do(open_chat) # 13:00 - 8 = 05:00
schedule.every().thursday.at("05:00").do(open_chat)  # 13:00 - 8 = 05:00
schedule.every().friday.at("05:00").do(open_chat)    # 13:00 - 8 = 05:00

def schedule_checker():
    while True:
        schedule.run_pending()
        time.sleep(30)

threading.Thread(target=schedule_checker, daemon=True).start()
check_and_set_chat_permissions()
bot.polling(none_stop=True)
