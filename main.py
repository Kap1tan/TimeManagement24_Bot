import telebot
import schedule
import time
import threading
from telebot.types import ChatPermissions
from datetime import datetime
import pytz

# Константы
BOT_TOKEN = "8042834324:AAF8OI-FrONvnEc2EpALNYulq7zIvXXbbm8"
ADMIN_IDS = {804644988, 1465809468}  # Укажи ID админов
moscow_tz = pytz.timezone('Europe/Moscow')

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)
chat_id = None  # ID администрируемого чата


@bot.message_handler(commands=['start'])
def start_admin_mode(message):
    global chat_id
    if message.from_user.id in ADMIN_IDS:
        chat_id = message.chat.id
        bot.send_message(chat_id, "Бот запущен в этом чате! Теперь он будет управлять доступом по расписанию.")


@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    bot.send_message(message.chat.id, "Привет! Этот чат управляется ботом.")


@bot.message_handler(func=lambda msg: chat_id and msg.chat.id == chat_id and is_chat_closed())
def delete_messages_when_closed(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Ошибка удаления сообщения: {e}")


# Проверки времени

def is_chat_closed():
    now = datetime.now(moscow_tz)
    return now.weekday() in [5, 6] or now.hour >= 18 or now.hour < 9


def is_weekend():
    return datetime.now(moscow_tz).weekday() in [5, 6]


def is_friday():
    return datetime.now(moscow_tz).weekday() == 4


def is_monday():
    return datetime.now(moscow_tz).weekday() == 0


# Функции управления чатом

def close_chat():
    if chat_id:
        bot.set_chat_permissions(chat_id, ChatPermissions(False))
        bot.send_message(chat_id, "Чат закрыт. Сообщения удаляются автоматически.")


def open_chat():
    if chat_id:
        bot.set_chat_permissions(chat_id, ChatPermissions(True))
        bot.send_message(chat_id, "Доброе утро заказчики и подрядчики Krasbau. \nВы снова можете задавать свои вопросы и делиться фото отчетом.")


def notify_closing():
    if chat_id:
        if is_friday():
            bot.send_message(chat_id, "Уважаемые заказчики и подрядчики Krasbau. \nЧат закрывается через 20 минут, откроется в понедельник в 9:00 и сможете снова задать свои вопросы и делится фото отчетом.")
        else:
            bot.send_message(chat_id, "Уважаемые заказчики и подрядчики Krasbau. \nЧат закрывается через 20 минут, откроется завтра в 9:00 и сможете снова задать свои вопросы и делится фото отчетом.")


def notify_opening():
    if chat_id and is_monday():
        bot.send_message(chat_id, "Доброе утро заказчики и подрядчики Krasbau. \nВы снова можете задавать свои вопросы и делиться фото отчетом.")


# Планирование задач
schedule.every().day.at("17:40").do(notify_closing)
schedule.every().day.at("18:00").do(close_chat)
schedule.every().monday.at("09:00").do(open_chat)
schedule.every().tuesday.at("09:00").do(open_chat)
schedule.every().wednesday.at("09:00").do(open_chat)
schedule.every().thursday.at("09:00").do(open_chat)
schedule.every().friday.at("09:00").do(open_chat)


# Запуск фонового потока

def schedule_checker():
    while True:
        schedule.run_pending()
        time.sleep(30)


threading.Thread(target=schedule_checker, daemon=True).start()
bot.polling(none_stop=True)
