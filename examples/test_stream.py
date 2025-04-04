""" Пример работы со стримом """
import sys
import os
from dotenv import load_dotenv
import time
import multiprocessing as mp

from tinkoff.invest.schemas import *
from tinkoff.invest.sandbox.client import SandboxClient

load_dotenv()
main_path = os.getenv('MAIN_PATH')
sys.path.append(main_path)
sys.path.append(main_path+'app/')
TOKEN = os.getenv("TINKOFF_TOKEN")

from app import stream_client
from config import program_config

def main():
    def request_iterator():
        yield MarketDataRequest(
            subscribe_candles_request=SubscribeCandlesRequest(
                waiting_close=True,
                subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
                instruments=[
                    CandleInstrument(
                        instrument_id="e6123145-9665-43e0-8413-cd61b8aa9b13",
                        interval=SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_MINUTE,
                    )
                ],
            )
        )
        while True:
            time.sleep(1)

    with SandboxClient(TOKEN) as client:
        for marketdata in client.market_data_stream.market_data_stream(
            request_iterator()
        ):
            print(marketdata)


def do_something():
    print('lol')
    time.sleep(2)


if __name__ == "__main__":
    pr_config = program_config.ProgramConfiguration(main_path+"settings.ini")
    stream_client.setup_stream(pr_config)