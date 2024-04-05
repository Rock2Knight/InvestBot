import unittest
from datetime import datetime
from work.functional import cast_money
from tinkoff.invest.schemas import Quotation
from time import perf_counter

from telebot.types import Message, User, Chat

class FunctionalTest(unittest.TestCase):
    def test_cast_money(self):
        t1 = perf_counter()
        self.assertEqual(cast_money(Quotation(92, 156000000)), 92.156)  # add assertion here
        t2 = perf_counter()
        print(f"Time of work cast_money(): {t2-t1:.9f} sec")

    '''
        def test_getAccounts(self):
        chat: Chat = Chat(id=1180010933, type="private")
        user: User = User(id=1180010933, is_bot=False,
                          first_name="Ilshat", last_name="Gibadullin",
                          username="SnowyFenix", language_code="en")
        message: Message = Message(message_id=170, from_user=user,
                                   date=1694114519, chat=chat,
                                   content_type=["text"], options={},
                                   json_string="")

        self.assertEqual(getAccounts(message), )
    '''

if __name__ == '__main__':
    unittest.main()
