from functools import cache
from dataclasses import dataclass

import pandas as pd

from tinkoff.invest import RequestError
from tinkoff.invest.sandbox.client import SandboxClient
from tinkoff.invest.sandbox.async_client import AsyncSandboxClient
from tinkoff.invest.schemas import *

from imports import *

from api import crud, models
from api.database import *
from utils_funcs import utils_funcs

@cache
def is_open_account(account: Account) -> bool:
    if account.status == AccountStatus.ACCOUNT_STATUS_OPEN:
        return True
    else:
        return False

@cache
def status_to_string(status: AccountStatus) -> str:
    if status == AccountStatus.ACCOUNT_STATUS_UNSPECIFIED:
        return 'UNSPECIFIED'
    elif status == AccountStatus.ACCOUNT_STATUS_OPEN:
        return 'OPEN'
    elif status == AccountStatus.ACCOUNT_STATUS_CLOSED:
        return 'CLOSED'
    elif status == AccountStatus.ACCOUNT_STATUS_NEW:
        return 'NEW'


@dataclass
class AccountInfo:
    id_account: str
    status: str

@dataclass
class Balance:
    full_amount: float
    free_money: float
    shares_amount: float
    bonds_amount: float
    etf_amount: float
    profit: float

@dataclass
class InstrumentInfo:
    ticker: str
    uid: str
    name: str
    exchange: str
    currency: str
    sector: str
    tool_type: str

@dataclass
class PositionInfo:
    ticker: str
    uid: str
    name: str
    price: float
    count_of_lots: int
    cnt: int
    total_amount: float

def get_accounts() -> list[AccountInfo]:
    accounts = list([])
    with SandboxClient(TOKEN) as client:                    # Запускаем клиент тинькофф-песочницы
        accounts_info = client.users.get_accounts()         # получаем информацию о счете

        for account in accounts_info.accounts:
            if is_open_account(account):
                account_obj = AccountInfo(id_account=account.id, status=status_to_string(account.status))
                accounts.append(account_obj)
    return accounts

def open_account() -> AccountInfo:
    new_account = None
    with SandboxClient(TOKEN) as client:                               # Запускаем клиент тинькофф-песочницы
        resp = client.sandbox.open_sandbox_account()     # создаем счет в песочнице
        new_account = AccountInfo(id_account=resp.account_id, status='OPEN')
    return new_account

def close_account(id_accounts: list[str]):
    with SandboxClient(TOKEN) as client:
        for id_account in id_accounts:
            client.sandbox.close_sandbox_account(account_id=id_account)

def pay_in(sum: float, id_account: str):

    """ Пополнение счета в песочнице """
    with SandboxClient(TOKEN) as client:
        # Получаем целую и дробную часть суммы
        pay_sum = utils_funcs.reverse_money_mv(sum)
        client.sandbox.sandbox_pay_in(account_id=id_account, amount=pay_sum)

@cache
def get_portfolio(id_account: str) -> Balance:
    balance = None
    with SandboxClient(TOKEN) as client:
        resp = client.sandbox.get_sandbox_portfolio(account_id=id_account)
        total = utils_funcs.cast_money(resp.total_amount_portfolio)
        free = utils_funcs.cast_money(resp.total_amount_currencies)
        shares = utils_funcs.cast_money(resp.total_amount_shares)
        bonds = utils_funcs.cast_money(resp.total_amount_bonds)
        etf = utils_funcs.cast_money(resp.total_amount_etf)
        exp_profit = utils_funcs.cast_money(resp.expected_yield)
        balance = Balance(full_amount=total, free_money=free, shares_amount=shares,
                          bonds_amount=bonds, etf_amount=etf, profit=exp_profit)
    return balance

def get_instruments(**kwargs) -> list[InstrumentInfo]:
    """
    :param kwargs:
        sector_name: str - название сектора
        exchange_name: str - название биржи
        currency_name: str - название валюты
    :return:
    """
    sector, currency, exchange = None, None, None
    sector_id, currency_id, exchange_id = 1, 1, 1
    db = SessionLocal()
    res_tools = list([])
    if 'sector_name' in kwargs.keys():
        if kwargs['sector_name'] != 'undefined':
            db_sector = crud.get_sector_by_name(db, kwargs['sector_name'])
            sector_id = db_sector.id
        else:
            sector_id = 0
    if 'currency_name' in kwargs.keys():
        if kwargs['currency_name'] != 'undefined':
            db_currency = crud.get_currency_by_name(db, kwargs['currency_name'])
            currency_id = db_currency.id
        else:
            currency_id = 0
    if 'exchange_name' in kwargs.keys():
        if kwargs['exchange_name'] != 'undefined':
            db_exchange = crud.get_exchange_by_name(db, kwargs['exchange_name'])
            exchange_id = db_exchange.id
        else:
            exchange_id = 0
    instrument_hash = {kwargs['sector_name']: sector_id, kwargs['currency_name']: currency_id,
                       kwargs['exchange_name']: exchange_id}
    tools_info = dict()
    tools = crud.get_instruments_filtered_list(db, exchange_id, sector_id, currency_id)
    if tools:
        tools_info['ticker'] = [tool.ticker for tool in tools]
        tools_info['uid'] = [tool.uid for tool in tools]
        tools_info['name'] = [tool.name for tool in tools]
        tools_info['sector'] = [kwargs['sector_name']] * len(tools)
        tools_info['currency'] = [kwargs['currency_name']] * len(tools)
        tools_info['exchange'] = list([])
        tools_info['type'] = list([])
        for tool in tools:
            exchange = crud.get_exchange(db, tool.exchange_id)
            tools_info['exchange'].append(exchange.name)
            type_tool = crud.get_instrument_type(db, tool.type_id)
            tools_info['type'].append(type_tool.name)
    if tools_info:
        df = pd.DataFrame(tools_info)
        sorted_df = df.sort_values(by='name')
        names = sorted_df['name']
        for i in range(sorted_df.shape[0]):
            tool_tip = sorted_df['type'].iloc[i]
            match tool_tip:
                case 'SHARE': tool_tip = 'Акция'
                case 'BOND': tool_tip = 'Облигация'
                case 'ETF': tool_tip = 'ETF'
            tool = InstrumentInfo(ticker=sorted_df['ticker'].iloc[i], uid=sorted_df['uid'].iloc[i],
                                  name=sorted_df['name'].iloc[i], sector=sorted_df['sector'].iloc[i],
                                  currency=sorted_df['currency'].iloc[i],
                                  exchange=sorted_df['exchange'].iloc[i], tool_type=tool_tip)
            res_tools.append(tool)
    return res_tools

@cache
def get_postions(id_account: str):
    res_positions = list([])
    db = SessionLocal()
    with SandboxClient(TOKEN) as client:
        resp = client.sandbox.get_sandbox_positions(account_id=id_account)
        tools = resp.securities
        for tool in tools:
            uid_tool = tool.instrument_uid
            instrument = crud.get_instrument(db, uid_tool)
            count = tool.balance
            count_lots = count // instrument.lot
            price_resp = client.market_data.get_last_prices(instrument_id=[uid_tool])
            last_price = utils_funcs.cast_money(price_resp.last_prices[0].price)
            total = last_price * count
            pos_info = PositionInfo(ticker=instrument.ticker, uid=uid_tool, name=instrument.name,
                                   price=last_price, count_of_lots=count_lots, cnt=count,
                                   total_amount=total)
            res_positions.append(pos_info)
    return res_positions