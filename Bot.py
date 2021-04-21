#!/usr/bin/env python
# %pylab inline

import UserDataManager
import CreateAnswer
import Config

import requests
import os
import random
import time

import json

import os.path

from copy import deepcopy
from pprint import pprint

import logging
from logging import handlers

logging_handler = logging.handlers.RotatingFileHandler(
    filename='logs/system.log',
    encoding='utf8',
    mode='a'
)

logging.basicConfig(format='%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.INFO,
                    handlers=[logging_handler])


class GenericBotHandler:
    def __init__(self, ege_data, predmet_ids, users_dict, similar_tasks):
        self.ege_data = ege_data
        self.predmet_ids = predmet_ids
        self.users_dict = users_dict
        self.similar_tasks = similar_tasks

        self.api = self.Api()
        self.create_answer = CreateAnswer.CreateAnswer(ege_data, similar_tasks)
        self.api.api_url = None

    def send_message(self, chat_id, text):
        if type(text) == list:
            text = ', '.join(str(i) for i in sorted(text))
        self.api.send_message(chat_id, text)

    def send_photo(self, chat_id, photo):
        if not photo:
            return
        logging.info(f'Sended photo {photo}')
        print(f'Sended photo {photo}')
        self.api.send_photo(chat_id, photo)

    def send_messages(self, user_id, messages):
        for text in messages['message']:
            self.send_message(user_id, text)
        for photo in messages['photo']:
            self.send_photo(user_id, photo)

    def bot_answer(self, text_question, user_id, user_name):
        if user_id not in self.users_dict:
            self.users_dict[user_id] = UserDataManager.UserDataManager(user_name)
        question_num = str(self.users_dict[user_id].active_problem)

        if text_question in {"start", "/start", "/help"}:
            if text_question == "/start" or text_question == "start":
                self.send_message(user_id, "Вас приветствует бот для подготовки к экзаменам")
            self.send_message(user_id,
                              "/help - для вывода доступных команд\n"
                              "/rand_question - бот даст вам рандомное задание, основываясь на вашем опыте решения\n"
                              "/get_similar_task - бот даст вам задачу, похожую на последнюю решенную\n"
                              "/get_answer - бот покажет решение задачи\n"
                              "/stats - бот покажет ваши решенные задачи")
        elif text_question == '/stats':
            self.send_messages(user_id, self.create_answer.get_stats(self.users_dict, user_id))
        elif text_question == '/rand_question':
            self.send_messages(user_id, self.create_answer.choice_rand_question(self.users_dict, user_id))
        elif text_question == '/get_similar_task':
            self.send_messages(user_id, self.create_answer.choice_similar_task(self.users_dict, user_id))
        elif text_question == '/get_answer':
            self.send_messages(user_id, self.create_answer.get_answer(self.users_dict, user_id, question_num))
        else:
            self.send_messages(user_id,
                               self.create_answer.check_answer(self.users_dict, user_id, text_question, question_num))

    class Api:
        def __init__(self):
            self.key = None
            self.url = None
            self.version = None
            self.id = None

        def authorize(self):
            pass

        def get_updates(self, offset=None, timeout=30):
            return []

        def send_message(self, chat_id, text):
            pass

        def send_photo(self, chat_id, photo_url):
            pass

        def send_keyboard(self, chat_id, keyboard):
            pass

        def hide_keyboard(self, chat_id):
            pass


class TelegramBotHandler(GenericBotHandler):
    def __init__(self, ege_data, predmet_ids, users_dict, similar_tasks):
        super().__init__(ege_data, predmet_ids, users_dict, similar_tasks)

        self.api.key = Config.TG_API_KEY
        self.api.url = f"https://api.telegram.org/bot{self.api.key}/"

    class Api(GenericBotHandler.Api):
        def get_updates(self, offset=None, timeout=30):
            params = {"timeout": timeout, "offset": offset}
            resp = requests.get(self.url + "getUpdates", params).json()
            if "result" not in resp:
                return []

            logging.debug(resp)
            return [
                {
                    "chat_id": f'tg{update["message"]["chat"]["id"]}',
                    "text": update["message"]["text"] if "text" in update["message"] else None,
                    "update_id": update["update_id"],
                    "user_name":
                        update["message"]["chat"]["first_name"] +
                        (" " + update["message"]["chat"]["last_name"]
                         if "last_name" in update["message"]["chat"] else "")
                }
                for update in resp["result"]
            ]

        def send_message(self, chat_id, text):
            params = {"chat_id": chat_id[2:], "text": text}
            requests.post(self.url + "sendMessage", params)

        def send_photo(self, chat_id, photo_url):  # Отправка фото по ссылке
            params = {"chat_id": chat_id[2:], "photo": photo_url}
            return requests.post(self.url + "sendPhoto", params)


def main():
    with open("load.json", 'r', encoding="utf-8-sig") as f:
        ege_data = json.loads(f.read())
        logging.info('Have read load.json')
        print('Have read load.json')

    with open('predmet_ids.json', 'r', encoding="utf-8-sig") as f:
        predmet_ids = json.loads(f.read())
        logging.info('Have read predmet_ids.json')
        print('Have read predmet_ids.json')

    with open('similar_tasks.json', 'r', encoding="utf-8-sig") as f:
        similar_tasks = json.loads(f.read())
        logging.info('Have read similar_tasks.json')
        print('Have read similar_tasks.json')

    users_dict = UserDataManager.load_user_data_manager()

    tg_bot = TelegramBotHandler(ege_data, predmet_ids, deepcopy(users_dict), similar_tasks)
    tg_offset = 0
    if Config.TG_BOT_ACTIVE:
        logging.info('Tg bot created and will be used')
        print('Tg bot created and will be used')
    else:
        logging.info("Tg bot created, but won't be used")
        print("Tg bot created, but won't be used")

    logging.info('Bot is ready to use')
    print('Bot is ready to use')

    banned = set()
    msg_count = dict()
    last = time.time()
    while True:
        if Config.TG_BOT_ACTIVE:
            if time.time() - last > 10:
                with open("banned_users.txt", 'r', encoding="utf-8") as f:
                    banned = set(f.read().split(' '))
                for i in msg_count:
                    if msg_count[i] > 20:
                        banned.add(i)
                        with open("banned_users.txt", 'w', encoding="utf-8") as f:
                            f.write(' '.join(list(banned)))
                        logging.info(f"User {i} was banned")
                        print(f"User {i} was banned")
                msg_count = dict()
                last = time.time()

            tg_updates = tg_bot.api.get_updates(offset=tg_offset, timeout=1)
            for update in tg_updates:
                if update["chat_id"] in banned:
                    tg_offset = max(tg_offset, update['update_id'] + 1)
                    continue
                if update["chat_id"] not in msg_count:
                    msg_count[update["chat_id"]] = 1
                else:
                    msg_count[update["chat_id"]] += 1

                logging.info(f"Update: {update}")
                print(f"Update: {update}")

                chat_id = update["chat_id"]
                if update["text"]:
                    tg_bot.bot_answer(update["text"], str(chat_id), update['user_name'])
                tg_offset = max(tg_offset, update['update_id'] + 1)

        UserDataManager.put_new_users(tg_bot.users_dict)


if __name__ == "__main__":
    main()
