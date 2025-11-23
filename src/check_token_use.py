import json
from datetime import datetime, date


class TokenManager:
    def __init__(self, filename):
        """
        Инициализация менеджера токенов.

        :param filename: Имя файла для хранения токенов в формате JSON.
        """
        self.filename = filename
        self.token_dict = self.load_tokens()
        self.current_date = date.today()

    def load_tokens(self):
        """Загрузить токены из JSON файла."""
        try:
            with open(self.filename, 'r') as file:
                token_dict = json.load(file)
                # Преобразуем дату из строки в объект date
                for token in token_dict.keys():
                    usage_count = token_dict[token][0]
                    last_used_date = datetime.strptime(token_dict[token][1], "%Y-%m-%d").date()
                    token_dict[token] = (usage_count, last_used_date)
                return token_dict
        except (FileNotFoundError, json.JSONDecodeError):
            # Если файл не найден или есть ошибка в формате, возвращаем пустой словарь
            return {}

    def save_tokens(self):
        """Сохранить токены в JSON файл."""
        with open(self.filename, 'w') as file:
            token_dict_to_save = {
                token: (usage_count, last_used_date.strftime("%Y-%m-%d"))
                for token, (usage_count, last_used_date) in self.token_dict.items()
            }
            json.dump(token_dict_to_save, file, indent=4)

    def reset_usage_counts(self):
        """
        Сбросить счетчики использований для токенов, которые были использованы в предыдущий день.
        """
        for token, (usage_count, last_used_date) in self.token_dict.items():
            if last_used_date < self.current_date:
                self.token_dict[token] = (0, self.current_date)

    def get_unused_token(self):
        """
        Получить токен, который использовался менее 50 раз.

        :return: Название токена, который можно использовать, или None, если все токены использованы более 50 раз.
        """
        self.reset_usage_counts()

        for token, (usage_count, last_used_date) in self.token_dict.items():
            if usage_count < 50:
                return token

        return None  # Все токены использованы более 50 раз

    def increment_usage_count(self, token: str, additional_requests: int):
        """
        Увеличить счётчик использований для указанного токена на указанное количество запросов.

        :param token: Название токена, который нужно обновить.
        :param additional_requests: Количество запросов, на которое нужно увеличить полное использование.
        :return: True, если операция успешна, иначе False (например, если токен не существует).
        """
        if token in self.token_dict:
            usage_count, last_used_date = self.token_dict[token]
            self.token_dict[token] = (usage_count + additional_requests, self.current_date)
            self.save_tokens()  # Сохраняем изменения в файл

            return True
        return False  # Токен не найден
