import json

from telebot.types import ReplyKeyboardMarkup


def load_data(path: str) -> dict:
    """
    Загружает данные из json по переданному пути и возвращает
    преобразованные данные в виде словаря.

    Если json по переданному
    пути не найден или его структура некорректна, то возвращает
    пустой словарь.
    """
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return {}


def save_data(data: dict, path: str) -> None:
    """
    Сохраняет переданный словарь в json по переданному пути.
    """
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def create_keyboard(buttons: list[str]) -> ReplyKeyboardMarkup:
    """
    Создает объект клавиатуры для бота по переданному списку строк.
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons)
    return keyboard
