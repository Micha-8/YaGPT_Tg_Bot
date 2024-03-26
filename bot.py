import json
import logging

import telebot
from telebot.types import Message

import db
from config import ADMINS, LOGS_PATH, MAX_TOKENS_PER_SESSION, MAX_SESSIONS, MAX_USERS, MAX_MODEL_TOKENS, BOT_TOKEN
from gpt import ask_gpt_helper, count_tokens_in_dialogue, create_prompt
from utils import create_keyboard
from info import END_STORY, CONTINUE_STORY

# Инициируем логгер по пути константы с уровнем логгирования debug
logging.basicConfig(
    filename=LOGS_PATH,
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
    filemode="w",
)

# Создаем клиент нашего бота
bot = telebot.TeleBot(BOT_TOKEN)

# Создаем базу и табличку в ней
db.create_db()
db.create_table()

# Определяем списки предметов и уровней сложности
genre_list = ["Комедия", "Фантастика", "Боевик", "Хоррор"]
character_list = ['Майкл джордан', 'Гермиона Грейнджер', 'Леонель Месси']
setting_list = ["Будущее", "Далекое прошлое", "В волшебном мире"]


def send_answer(answer, user_id):
    if answer is None:
        bot.send_message(
            user_id,
            "Не могу получить ответ от GPT :(",
            reply_markup=create_keyboard(
                [
                    'Закончить историю'
                ]
            ),
        )
    elif answer == "":
        bot.send_message(
            user_id,
            "Я не могу ничего придумать давай заново",
            reply_markup=create_keyboard(
                [
                    'Закончить историю'
                ]
            ),
        )
    else:
        bot.send_message(
            user_id,
            answer,
            reply_markup=create_keyboard(
                [
                    'Закончить историю'
                ]
            ),
        )


@bot.message_handler(commands=["start"])
def start(message):
    user_name = message.from_user.first_name  # Получаем имя пользователя
    user_id = message.from_user.id  # Получаем id пользователя

    if not db.is_user_in_db(user_id):  # Если пользователя в базе нет
        if len(db.get_all_users_data()) < MAX_USERS:  # Если число зарегистрированных пользователей меньше допустимого
            db.add_new_user(user_id)  # Регистрируем нового пользователя
        else:
            # Если уперлись в лимит пользователей, отправляем соответствующее письмо
            bot.send_message(
                user_id,
                "К сожалению, лимит пользователей исчерпан. "
                "Вы не сможете воспользоваться ботом:("
            )
            return  # Прерываем здесь функцию, чтобы дальнейший код не выполнялся

    # Этот блок срабатывает только для зарегистрированных пользователей
    bot.send_message(
        user_id,
        f"Привет, {user_name}! Я бот-сценарист и я буду придумывать с тобой различные истории!\n"
        f"Ты можешь выбрать жанр, персонажа и сеттинг, а я придумаю историю основываясь на твой выбор.\n"
        f"Чтобы начать новую историю нажми /new_scene",
        reply_markup=create_keyboard(["/new_scene"]),
    )


@bot.message_handler(commands=["new_scene"])
def new_scene(message):
    user_name = message.from_user.first_name  # Получаем имя пользователя
    user_id = message.from_user.id  # Получаем id пользователя

    if not db.is_user_in_db(user_id):  # Если пользователя в базе нет
        if len(db.get_all_users_data()) < MAX_USERS:  # Если число зарегистрированных пользователей меньше допустимого
            db.add_new_user(user_id)  # Регистрируем нового пользователя
        else:
            # Если уперлись в лимит пользователей, отправляем соответствующее письмо
            bot.send_message(
                user_id,
                "К сожалению, лимит пользователей исчерпан. "
                "Вы не сможете воспользоваться ботом:("
            )
            return  # Прерываем здесь функцию, чтобы дальнейший код не выполнялся

    # Этот блок срабатывает только для зарегистрированных пользователей
    bot.send_message(
        user_id,
        f"Привет, {user_name}!\n"
        f"Я вижу ты готов начать историю тогда давай выберем жанр\n",
        reply_markup=create_keyboard(["Выбрать жанр"]),
    )

    bot.register_next_step_handler(message, choose_genre)


def filter_choose_genre(message: Message) -> bool:
    user_id = message.from_user.id
    if db.is_user_in_db(user_id):  # Отработает только для зарегистрированных пользователей
        return message.text in ["Выбрать жанр"]


@bot.message_handler(func=filter_choose_genre)
def choose_genre(message: Message):
    user_id = message.from_user.id
    sessions = db.get_user_data(user_id)["sessions"]  # Получаем из БД актуальное количество сессий пользователя
    if sessions < MAX_SESSIONS:  # Если число сессий пользователя не достигло предела
        db.update_row(user_id, "sessions", sessions + 1)  # Накручиваем ему +1 сессию
        db.update_row(user_id, "tokens", MAX_TOKENS_PER_SESSION)  # И обновляем его токены
        bot.send_message(
            user_id,
            "Выбери жанр, по которому тебе будет придумана история:",
            reply_markup=create_keyboard(genre_list),  # Создаем клавиатуру из списка предметов
        )
        bot.register_next_step_handler(message, genre_selection)

    else:  # Если число сессий достигло лимита
        bot.send_message(
            user_id,
            "К сожалению, лимит твоих вопросов исчерпан:("
        )


def genre_selection(message: Message):
    user_id = message.from_user.id
    user_choice = message.text
    if user_choice in genre_list:  # Проверим, что предмет есть в жанр. Это исключит вариант, если пользователь
        # захочет ввести собственный предмет, вместо того, чтобы выбрать из кнопок на клавиатуре
        db.update_row(user_id, "genre", user_choice)  # Обновим значение предмета в БД
        bot.send_message(
            user_id,
            f"Отлично, {message.from_user.first_name}, теперь история будет в жанре '{user_choice}'!"
            f"Давай теперь выберем главного героя этой замечательной истории.",
            reply_markup=create_keyboard(character_list),
        )
        bot.register_next_step_handler(message, character_selection)

    else:  # Если был выбран предмет не из нашего списка
        bot.send_message(
            user_id,
            "К сожалению, по такому жанру я не могу придумать историю",
            reply_markup=create_keyboard(genre_list),
        )
        bot.register_next_step_handler(message, genre_selection)  # Снова отправляем его в эту же функцию


def character_selection(message: Message):
    user_id = message.from_user.id
    user_choice = message.text
    if user_choice in character_list:
        db.update_row(user_id, "character", user_choice)
        bot.send_message(
            user_id,
            f"Принято, {message.from_user.first_name}! Теперь главным героем будет: '{user_choice}'."
            f"Давай теперь выберем сеттинг этой замечательной истории.",
            reply_markup=create_keyboard(setting_list),
        )
        bot.register_next_step_handler(message, setting_selection)
    else:
        bot.send_message(
            user_id,
            "Пожалуйста, выбери персонажа из предложенных:",
            reply_markup=create_keyboard(character_list),
        )
        bot.register_next_step_handler(message, character_selection)


def setting_selection(message: Message):
    user_id = message.from_user.id
    user_choice = message.text
    if user_choice in setting_list:
        db.update_row(user_id, "setting", user_choice)
        bot.send_message(
            user_id,
            f"Принято, {message.from_user.first_name}! Теперь сеттингом истории будем: '{user_choice}'. "
            f"А теперь добавь что-то если хочешь, если нечего добавить пиши просто ничего",
        )
        bot.register_next_step_handler(message, additional_info_selection)
    else:
        bot.send_message(
            user_id,
            "Пожалуйста, выбери сеттинг из предложенных:",
            reply_markup=create_keyboard(setting_list),
        )
        bot.register_next_step_handler(message, setting_selection)


def additional_info_selection(message: Message):
    user_id = message.from_user.id
    user_choice = message.text

    db.update_row(user_id, "additional_info", user_choice)
    bot.send_message(
        user_id,
        f"Принято, нажми 'готов' чтобы начать(или что-то другое если хочешь) ",
        reply_markup=create_keyboard(['готов']),
    )
    bot.register_next_step_handler(message, start_scene)


def start_scene(message: Message):
    user_id = message.from_user.id
    user_tokens = db.get_user_data(user_id)["tokens"]  # Получаем актуальное количество токенов пользователя из БД
    genre = db.get_user_data(user_id)["genre"]  # Получаем выбранный предмет из БД
    character = db.get_user_data(user_id)["character"]  # Получаем выбранную сложность из БД
    setting = db.get_user_data(user_id)["setting"]
    additional_info = db.get_user_data(user_id)["additional_info"]

    system_content = create_prompt(genre, character, setting,
                                   additional_info)  # Формируем system_content из предмета и сложности

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": 'Начинай'}
    ]  # Приводим контент к стандартизированному виду - списку из словарей сообщений
    tokens_messages = count_tokens_in_dialogue(messages)  # Посчитаем вес запроса в токенах

    if tokens_messages + MAX_MODEL_TOKENS <= user_tokens:  # Проверим что вес запроса + максимального ответа меньше, чем
        # оставшееся количество токенов у пользователя, чтобы пользователю хватило и на запрос и на максимальный ответ
        bot.send_message(message.from_user.id, "Начинаю...")
        answer = ask_gpt_helper(messages)  # Получаем ответ от GPT
        messages.append({"role": "assistant", "content": answer})  # Добавляем в наш словарик ответ GPT

        user_tokens -= count_tokens_in_dialogue([{"role": "assistant", "content": answer}])  # Получаем новое значение
        # оставшихся токенов пользователя - вычитаем стоимость запроса и ответа
        db.update_row(user_id, "tokens", user_tokens)  # Записываем новое значение в БД

        json_string = json.dumps(messages, ensure_ascii=False)  # Преобразуем список словарей сообщений к виду json
        # строки для хранения в одной ячейке БД
        db.update_row(user_id, "messages", json_string)  # Записываем получившуюся строку со всеми
        # сообщениями в ячейку 'messages'

        send_answer(answer, user_id)

    else:  # Если у пользователя не хватает токенов на запрос + ответ
        bot.send_message(
            message.from_user.id,
            "Токенов на ответ может не хватить:( Начни новую сессию",
            reply_markup=create_keyboard(["/new_scene"])  # Предлагаем ему начать новую сессию через кнопку
        )
        logging.info(
            f"Отправлено: {message.text}\nПолучено: Предупреждение о нехватке токенов"
        )


@bot.message_handler()
def continue_or_end_scene(message):
    user_id = message.from_user.id
    json_string_messages = db.get_user_data(user_id)["messages"]  # Достаем из базы все предыдущие сообщения
    # в виде json-строки
    messages = json.loads(json_string_messages)  # Преобразуем json-строку в нужный нам формат списка словарей
    if not messages:  # Если попытались продолжить, но запроса еще не было
        bot.send_message(
            user_id,
            "Для начала начни историю :",
            reply_markup=create_keyboard(["/new_scene"]),
        )
        return  # Прерываем выполнение функции
    genre = db.get_user_data(user_id)["genre"]  # Получаем выбранный предмет из БД
    character = db.get_user_data(user_id)["character"]  # Получаем выбранную сложность из БД
    setting = db.get_user_data(user_id)["setting"]
    additional_info = db.get_user_data(user_id)["additional_info"]
    if message.text == 'Закончить историю':
        system_content = create_prompt(genre, character, setting, additional_info, next_step=END_STORY)
    else:
        system_content = create_prompt(genre, character, setting, additional_info, next_step=CONTINUE_STORY)

    user_tokens = db.get_user_data(user_id)["tokens"]  # Получаем актуальное количество токенов пользователя
    tokens_messages = count_tokens_in_dialogue(messages)  # Считаем вес запроса в токенах из всех предыдущих сообщений
    messages.append(
        {"role": "system", "content": system_content},
        {"role": "user", "content": f'{message}'}
    )
    if tokens_messages + MAX_MODEL_TOKENS <= user_tokens and message.text == 'Закончить историю':
        bot.send_message(user_id, "Формулирую конец истории")
        answer = ask_gpt_helper(messages)
        messages.append({"role": "assistant", "content": answer})  # Добавляем очередной ответ в список сообщений

        user_tokens -= count_tokens_in_dialogue([{"role": "assistant", "content": answer}])  # Вычитаем токены
        db.update_row(user_id, "tokens", user_tokens)  # Сохраняем новое значение токенов в БД

        json_string_messages = json.dumps(messages, ensure_ascii=False)  # Преобразуем список сообщений в строку для БД
        db.update_row(user_id, "messages", json_string_messages)  # Сохраняем строку сообщений в БД

        send_answer(answer, user_id)

    elif tokens_messages + MAX_MODEL_TOKENS <= user_tokens:  # Проверяем хватает ли токенов на запрос + ответ
        bot.send_message(user_id, "Формулирую продолжение...")
        answer = ask_gpt_helper(messages)
        messages.append({"role": "assistant", "content": answer})  # Добавляем очередной ответ в список сообщений

        user_tokens -= count_tokens_in_dialogue([{"role": "assistant", "content": answer}])  # Вычитаем токены
        db.update_row(user_id, "tokens", user_tokens)  # Сохраняем новое значение токенов в БД

        json_string_messages = json.dumps(messages, ensure_ascii=False)  # Преобразуем список сообщений в строку для БД
        db.update_row(user_id, "messages", json_string_messages)  # Сохраняем строку сообщений в БД
        send_answer(answer, user_id)
        bot.register_next_step_handler(message, continue_or_end_scene)

    else:  # Если токенов на продолжение не хватило
        bot.send_message(
            message.from_user.id,
            "Токенов на ответ может не хватить:( предлагаю начать заново ",
            reply_markup=create_keyboard(["/new_scene"]),  # Предлагаем задать новый вопрос в рамках сессии
        )
        logging.info(
            f"Отправлено: {message.text}\nПолучено: Предупреждение о нехватке токенов")


@bot.message_handler(commands=["debug"])
def send_logs(message):
    user_id = message.from_user.id
    if user_id in ADMINS:
        with open(LOGS_PATH, "rb") as f:
            bot.send_document(message.from_user.id, f)


# немного напутал в конце и с токеном(IAM) возможно, жду ревью
bot.polling()
