""" Классы исключений бота """

__all__ = ['InvestBotValueError']

class InvestBotValueError(ValueError):
    def __init__(self, message):
        super().__init__(message)
        self.msg = message