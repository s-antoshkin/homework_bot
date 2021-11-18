import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv
from requests.exceptions import (
    ConnectionError, HTTPError, RequestException, Timeout
)

load_dotenv()

PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_TIME = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}

HOMEWORK_STATUSES = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def send_message(bot, message):
    """Отправка сообщения в чат."""
    logger.info(f"Бот отправил сообщение: {message}")
    return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(current_timestamp):
    """Запрос к эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {"from_date": timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        # response.raise_for_status()
        if response.status_code != 200:
            raise logger.error(f"Ошибка, Код ответа: {response.status_code}")
        return response.json()
    except ConnectionError as e:
        logger.error(
            f"Ошибка соединения. Проверьте подключение к интернету - {e}"
        )
    except Timeout as e:
        logger.error(f"Время ожидания запроса истекло - {e}")
    except HTTPError as e:
        logger.error(f"Http Error - {e}")
    except RequestException as e:
        logger.error(f"Что-то пошло не так - {e}")


def check_response(response):
    """Проверка ответа API на корректность."""
    if "homeworks" not in response:
        raise logger.error("В ответе от API отсутствует homeworks")
    elif not isinstance(response["homeworks"], list):
        raise logger.error("Неверный тип данных у элемента homeworks")
    else:
        return response.get("homeworks")


def parse_status(homework):
    """Извлечение статуса работы."""
    homework_name = homework["homework_name"]
    homework_status = homework["status"]
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности переменных окружения."""
    if (
        PRACTICUM_TOKEN is None
        or TELEGRAM_TOKEN is None
        or TELEGRAM_CHAT_ID is None
    ):
        logger.critical("Отсутствие обязательных переменных окружения!")
        return False
    else:
        return True


def main():
    """Основная логика работы бота."""
    current_homework = {}
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if len(homeworks) > 0:
                if current_homework == {} or current_homework != homeworks[0]:
                    current_homework = homeworks[0]
                    lesson_name = current_homework["lesson_name"]
                    send_message(
                        bot,
                        lesson_name + ". " + parse_status(current_homework)
                    )
            current_timestamp = response.get("current_date")
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logger.error(message)
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == "__main__":
    if check_tokens():
        main()
    else:
        SystemExit()
