class ResponseException(Exception):
    """Исключение возникает из-за ошибок в запросе к сервису."""

    exceptions = {
        "ConnectionError":
            "Ошибка соединения. Проверьте подключение к интернету!",
        "Timeout": "Время ожидания запроса истекло!",
        "HTTPError": "Http Error!",
        "RequestException": "Что-то пошло не так!",
    }

    def __init__(self, error):
        """Конструктор принимает исключение."""
        super().__init__(error)
        self.error = error.__class__.__name__

    def __str__(self):
        """Строковое представление исключения с описанием."""
        description = ResponseException.exceptions[self.error]
        return f"{description} - {super().__str__()}"
