import unittest
from work.functional import cast_money
from tinkoff.invest.schemas import Quotation

class FunctionalTest(unittest.TestCase):
    def test_cast_money(self):
        self.assertEqual(cast_money(Quotation(50, 140000000)), 50.15)  # add assertion here


if __name__ == '__main__':
    unittest.main()
