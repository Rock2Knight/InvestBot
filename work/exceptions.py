""" Классы исключений бота """
from typing import Any

from grpc import StatusCode
from tinkoff.invest.exceptions import RequestError

__all__ = ['InvestBotValueError', 'InvestBotRequestError']

class InvestBotValueError(ValueError):
    def __init__(self, message):
        super().__init__(message)
        self.msg = message

class InvestBotRequestError(RequestError):
    def __init__(self, code: StatusCode, details: str, metadata: Any):
        super().__init__(code, details, metadata)
        self.code = code
        self.details = details
        self.metadata = metadata
        self.msg = "Error in GetCandles request\n"