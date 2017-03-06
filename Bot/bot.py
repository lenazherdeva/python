import telebot
import config
import pyowm
from pyowm import timeutils
import datetime
import urllib
import urllib.parse
import json
import http.client
import urllib.request
import urllib.parse
import urllib.error
import random


bot = telebot.TeleBot(config.token)


def set_params(status, city):
    query = 'погода ' + status + " " + city
    headers = {
        'Ocp-Apim-Subscription-Key': config.BINGAPI
    }
    params = urllib.parse.urlencode({
        'q': query,
        'count': '1',
        'mkt': 'ru-RU',
        'safeSearch': 'Moderate',
    })
    return query, params, headers


def search(query, params, headers):
    conn = http.client.HTTPSConnection('api.cognitive.microsoft.com')
    conn.request("GET", "/bing/v5.0/images/search?%s" % params,
                 query.encode('utf-8'), headers)
    response = conn.getresponse()
    string = response.read().decode('utf-8')
    json_obj = json.loads(string)
    img_url = json_obj['value'][0]['contentUrl']
    conn.close()
    return img_url


def bing_search(status, city):
    query, params, headers = set_params(status, city)
    try:
        img_url = search(query, params, headers)
    except IndexError:
        query, params, headers = set_params(status, '')
        img_url = search(query, params, headers)
    return img_url


def find_in_base(poems_base, word):
    num_poems = len(poems_base[word])
    return poems_base[word][random.randint(0, num_poems - 1)]


def get_poem(key_word):
    word_list = key_word.split(' ')
    if len(word_list) > 1:
        key_word = word_list[1]
    with open('poems_base.json') as data_file:
        poems_base = json.load(data_file)
    if key_word == 'снегопад':
        poem = find_in_base(poems_base, 'снегопад')
    elif key_word == 'ясно':
        poem = find_in_base(poems_base, 'солнечно')
    elif key_word == 'облачно':
        poem = find_in_base(poems_base, 'облачно')
    else:
        poem = find_in_base(poems_base, 'дождь')
    return poem


@bot.message_handler(commands=["start"])
def handle_start(message):
    bot.send_message(message.from_user.id, 'Привет!\nЯ предсказываю погоду '
                                           'в заданный день, '
                                           'показываю картинки и '
                                           'отпраляю стишок\n Чтобы узнать, '
                                           'как мной пользоваться нажми /help')


@bot.message_handler(commands=["help"])
def handle_help(message):
    bot.send_message(message.from_user.id, 'Я поддерживаю запросы вида:\n'
                                           '[Москва]\n'
                                           '[Москва завтра]\n'
                                           '[Москва вечером]\n'
                                           '[Москва через 5 дней]\n'
                                           '[Москва в четверг]\n'
                                           'И делаю прогноз максимум'
                                           ' на 2 недели вперед')


def parse(query, owm):
    week = {'понедельник': 0, 'вторник': 1, 'среду': 2, 'четверг': 3,
            'пятницу': 4, 'субботу': 5, 'воскресенье': 6}
    city = query[0]
    fc = owm.daily_forecast(city, limit=16)
    if len(query) == 1:
        data = timeutils.now().replace(microsecond=0, tzinfo=None)
    elif query[1] == 'завтра':
        data = timeutils.tomorrow()
    elif query[1] == 'сегодня':
        data = timeutils.now().replace(microsecond=0, tzinfo=None)
    elif query[1] == 'вечером' or query[1] == 'днем'\
            or query[1] == 'утром' or query[1] == 'ночью':
        data = timeutils.now().replace(microsecond=0, tzinfo=None)
    elif query[1] == 'в' or query[1] == 'во':
        day = query[2]
        period = week[day]
        today = datetime.datetime.today().weekday()
        diff = period - today
        if diff == 0:
            data = timeutils.now().replace(microsecond=0, tzinfo=None)
        else:
            data = timeutils._timedelta_days(diff % 6 + 1).\
                replace(microsecond=0, tzinfo=None)
    elif query[1] == 'через':
        if query[2] == 'неделю':
            data = timeutils._timedelta_days(7).\
                replace(microsecond=0, tzinfo=None)
        else:
            period = int(query[2])
            if query[3] == 'дней' or query[3] == 'дня' or query[3] == 'день':
                data = timeutils._timedelta_days(period).\
                    replace(microsecond=0, tzinfo=None)
            elif query[3] == 'недели' or query[3] == 'неделю':
                if period == 1:
                    data = timeutils._timedelta_days(7).\
                        replace(microsecond=0, tzinfo=None)
                elif period == 2:
                    data = timeutils._timedelta_days(14).\
                        replace(microsecond=0, tzinfo=None)
    try:
        weather = fc.get_weather_at(data)
    except:
        return None
    status = weather.get_detailed_status()
    img_url = bing_search(status, city)
    poem = get_poem(status)
    temp = weather.get_temperature('celsius')
    temperature = {'morn': int(temp['morn']), 'day': int(temp['day']),
                   'eve': int(temp['eve']), 'night': int(temp['night'])}
    return data, city, temperature, status, img_url, poem


@bot.message_handler(content_types=["text"])
def handle_t(message):
    owm = pyowm.OWM(config.APIKEY, language='ru')
    query = message.text.split(' ')
    try:
        time, city, temp, status, img_url, poem = parse(query, owm)
        if len(query) > 1:
            if query[1] == 'вечером':
                bot.send_message(message.chat.id, "Погода на {} в городе {}:"
                                                  " \n температура вечером  :"
                                                  " {} °C \n {}".
                                 format(time, city, temp['eve'], status))
            elif query[1] == 'днем':
                bot.send_message(message.chat.id, "Погода на {} в городе {}: "
                                                  "\n температура днем : {}"
                                                  " °C" " \n {}".
                                 format(time, city, temp['day'], status))
            elif query[1] == 'утром':
                bot.send_message(message.chat.id, "Погода на {} в городе {}: "
                                                  "\n температура утром : {}"
                                                  " °C \n {}".
                                 format(time, city, temp['morn'], status))
            elif query[1] == 'ночью':
                bot.send_message(message.chat.id, "Погода на {} в городе {}:"
                                                  " \n температура ночью : "
                                                  "{} °C \n {}".
                                 format(time, city, temp['night'], status))
            else:
                bot.send_message(message.chat.id, "Погода на {} в городе {}: "
                                                  "\n температура: \n утром :"
                                                  " {} °C \n днем: "
                                                  "{} °C \n вечером :"
                                                  " {} °C \n ночью: {} °C "
                                                  " \n {}".
                                 format(time, city, temp['morn'], temp['day'],
                                        temp['eve'], temp['night'], status))
        else:
            bot.send_message(message.chat.id, "Погода на {} в городе {}:"
                                              " \n температура: \n утром :"
                                              " {} °C \n днем: "
                                              "{} °C \n вечером : {} °C \n"
                                              " ночью: {} °C  \n {}".
                             format(time, city, temp['morn'],
                                    temp['day'], temp['eve'], temp['night'],
                                    status))
        bot.send_photo(chat_id=message.chat.id, photo=img_url)
        bot.send_message(message.chat.id, poem)
    except TypeError:
        bot.send_message(message.chat.id, 'Запрошенная дата за пределами '
                                          'возможного прогноза')
    except:
        bot.send_message(message.chat.id, 'Такого города не существует или'
                                          ' формат ввода неверен')


if __name__ == '__main__':
    bot.polling(none_stop=True)
