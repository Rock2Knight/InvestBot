import unittest
from work.functional import cast_money, getAccounts
from tinkoff.invest.schemas import Quotation

from telebot.types import Message, User, Chat

class FunctionalTest(unittest.TestCase):
    def test_cast_money(self):
        self.assertEqual(cast_money(Quotation(50, 140000000)), 50.15)  # add assertion here

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

if __name__ == '__main__':
    unittest.main()
