import os
import random
import telebot
from telebot import types
from flask import Flask, request

app = Flask(__name__)
bot = telebot.TeleBot(os.environ['BOT_TOKEN'])

users = {}

def get_user(user_id, username="Игрок"):
    if user_id not in users:
        users[user_id] = {"balance": 1000, "wins": 0, "name": username}
    return users[user_id]

def menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("/balance", "/game")
    markup.add("/top", "/help")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user = get_user(message.from_user.id, message.from_user.username or "Игрок")
    bot.send_message(message.chat.id,
        f"Привет, {user['name']}!\n\n"
        f"Баланс: {user['balance']} руб\n\n"
        f"НОВАЯ ИГРА → /game\n"
        f"Выбираешь число 1–12 → ставишь деньги\n"
        f"Угадал → ×10 выигрыш!\n\n"
        f"Пиши прямо в чат, например: 7 100", reply_markup=menu())

@bot.message_handler(commands=['balance'])
def balance(message):
    user = get_user(message.from_user.id)
    bot.reply_to(message, f"Баланс: {user['balance']} руб\nПобед: {user['wins']}")

@bot.message_handler(commands=['game', 'help'])
def game_help(message):
    bot.reply_to(message,
        "Как играть:\n"
        "Пиши: число ставка\n"
        "Например:\n"
        "5 50 → ставишь 50 руб на число 5\n"
        "12 200 → ставишь 200 руб на число 12\n\n"
        "Угадал → ×10 выигрыш!\n"
        "Не угадал → теряешь ставку")

@bot.message_handler(func=lambda m: True)
def play(message):
    user = get_user(message.from_user.id)
    try:
        parts = message.text.strip().split()
        if len(parts) != 2: return
        
        num = int(parts[0])
        bet = int(parts[1])
        
        if not (1 <= num <= 12):
            bot.reply_to(message, "Число от 1 до 12!")
            return
        if bet < 10:
            bot.reply_to(message, "Минимум 10 руб!")
            return
        if bet > user['balance']:
            bot.reply_to(message, "Не хватает денег!")
            return
            
        user['balance'] -= bet
        win_num = random.randint(1, 12)
        
        if num == win_num:
            win = bet * 10
            user['balance'] += win
            user['wins'] += 1
            bot.send_message(message.chat.id,
                f"ВЫПАЛО {win_num}!!!\n"
                f"Ты угадал → ×10 выигрыш!\n"
                f"+{win} руб\n"
                f"Баланс: {user['balance']} руб")
        else:
            bot.send_message(message.chat.id,
                f"Выпало: {win_num}\n"
                f"Ты выбрал: {num}\n"
                f"Проиграл {bet} руб\n"
                f"Осталось: {user['balance']} руб")
                
    except:
        pass

@bot.message_handler(commands=['top'])
def top(message):
    top5 = sorted(users.items(), key=lambda x: x[1]['balance'], reverse=True)[:5]
    text = "ТОП-5 игроков:\n"
    for i, (uid, data) in enumerate(top5, 1):
        text += f"{i}. @{data['name']} — {data['balance']} руб\n"
    bot.reply_to(message, text or "Пока никто не играл!")

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'OK', 200
    return 'ERROR', 403

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
