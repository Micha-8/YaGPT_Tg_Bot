import logging
import time
import requests
import http

from config import GPT_URL, LOGS_PATH, MAX_MODEL_TOKENS, MODEL_NAME, FOLDER_ID, TEMPERATURE
from info import SYSTEM_PROMPT

logging.basicConfig(
    filename=LOGS_PATH,
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
    filemode="w",
)


def create_token():
    url = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"
    headers = {'Metadata-Flavor': 'Google'}
    response = requests.get(url=url, headers=headers)
    iam_token = response.json()['access_token']
    expires_at = response.json()['expires_in'] + time.time()
    return iam_token, expires_at


def get_creds():
    token, expires_at = create_token()
    if time.time() > expires_at:
        token, expires_at = create_token()
        return token
    else:
        return token

    # вот тут не уверен


# Функция для подсчета токенов в истории сообщений. На вход обязательно принимает список словарей, а не строку!
def count_tokens_in_dialogue(messages: list) -> int:
    token, folder_id = get_creds(), FOLDER_ID
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{folder_id}/{MODEL_NAME}/latest",
        "maxTokens": MAX_MODEL_TOKENS,
        "messages": []
    }

    for row in messages:  # Меняет ключ "content" на "text" в словарях списка для корректного запроса
        data["messages"].append(
            {
                "role": row["role"],
                "text": row["content"]
            }
        )

    return len(
        requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenizeCompletion",
            json=data,
            headers=headers
        ).json()["tokens"]
    )


def create_prompt(genre, character, setting, additional_info, next_step=''):
    # Начальный текст для нашей истории - это типа вводная часть
    prompt = SYSTEM_PROMPT

    # Добавляем в начало истории инфу о жанре и главном герое, которых выбрал пользователь
    prompt += (f"\nНапиши начало истории в стиле {genre} "
               f"с главным героем {character}. "
               f"Вот начальный сеттинг: \n{setting}. \n"
               "Начало должно быть коротким, 1-3 предложения.\n"
               f"Также пользователь попросил учесть "
               f"следующую дополнительную информацию: {additional_info} "
               'Не пиши никакие подсказки пользователю, что делать дальше. Он сам знает')

    prompt += next_step

    # Возвращаем сформированный текст истории
    return prompt


def ask_gpt_helper(messages) -> str:
    token, folder_id = get_creds(), FOLDER_ID
    url = f"{GPT_URL}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {

        "modelUri": f"gpt://{folder_id}/{MODEL_NAME}/latest",
        "completionOptions": {
            "stream": False,
            "temperature": TEMPERATURE,
            "maxTokens": f"{MAX_MODEL_TOKENS}"
        },
        "messages": messages
    }

    try:
        response = requests.post(url=url, headers=headers, json=data)
        if response.status_code != http.HTTPStatus.OK:
            logging.debug(f'Response {response.json()} Status code: {response.status_code} Message {response.text}')
            result = f'Status code: {response.status_code}. смотри в логи'
            return result
        result = response.json()["choices"][0]["message"]["content"]
        logging.info(f'Request: {response.request.url}\n'
                     f'Response {response.status_code}\n'
                     f'Response Body {response.text}\n'
                     f'Processed Result: {result}')
    except Exception as e:
        logging.error(f'Am unexpected error occures: {e}')
        result = 'Произошла ошибка смотри в логах'

    return result
