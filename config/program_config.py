from configparser import ConfigParser

from tinkoff.invest.schemas import IndicatorType

__all__ = ("ProgramConfiguration")


class ProgramConfiguration:
    """
    Represent all bot configuration
    """
    def __init__(self, file_name: str) -> None:
        # classic ini file
        self.config = ConfigParser()
        self.config.read(file_name)

        self._max_cnt_ticks = int(self.config['MODELING_SETTINGS']['MAX_CNT_TICKS'])
        self._excel_filename = self.config['MODELING_SETTINGS']['EXCEL_FILENAME']
        self._start_portfolio = float(self.config['MODELING_SETTINGS']['START_ACCOUNT_PORTFOLIO'])
        self._start_lot_count = float(self.config['MODELING_SETTINGS']['START_LOT_COUNT'])

        self._stop_account = float(self.config['TRADING_SETTINGS']['STOP_ACCOUNT'])
        self._timeframe = self.config['TRADING_SETTINGS']['TIMEFRAME']
        self.user_return = float(self.config['TRADING_SETTINGS']['USER_RETURN'])
        self.user_risk = float(self.config['TRADING_SETTINGS']['USER_RISK'])

        self._strategies = dict()

        for section in self.config.sections():
            if section.startswith('STRATEGY'):
                name = section.split('_')[1]
                self._strategies[name] = dict()
                self._strategies[name]['uid'] = self.config[section]['UID']
                self._strategies[name]['max_lots_per_order'] = self.config[section]['MAX_LOTS_PER_ORDER']
                if self._strategies[name]['max_lots_per_order']:
                    self._strategies[name]['max_lots_per_order'] = int(self._strategies[name]['max_lots_per_order'])
                self._strategies[name]['stop_loss'] = float(self.config[section]['STOP_LOSS'])
                self._strategies[name]['take_profit'] = float(self.config[section]['TAKE_PROFIT'])
                self._strategies[name]['ma_type'] = self.config[section]['MA_TYPE']
                if self._strategies[name]['ma_type'] == 'SMA':
                    self._strategies[name]['ma_type'] = IndicatorType.INDICATOR_TYPE_SMA
                else:
                    self._strategies[name]['ma_type'] = IndicatorType.INDICATOR_TYPE_EMA
                self._strategies[name]['ma_interval'] = int(self.config[section]['MA_INTERVAL'])
                self._strategies[name]['rsi_interval'] = int(self.config[section]['RSI_INTERVAL'])
                self._strategies[name]['max_inter'] = int(self.config[section]['MAX_INTER'])
                self._strategies[name]['weight'] = float(self.config[section]['WEIGHT'])

    @property
    def max_cnt_ticks(self):
        return self._max_cnt_ticks

    @property
    def excel_filename(self):
        return self._excel_filename

    @property
    def start_portfolio(self):
        return self._start_portfolio

    @property
    def start_lot_count(self):
        return self._start_lot_count

    @property
    def stop_account(self):
        return self._stop_account

    @property
    def timeframe(self):
        return self._timeframe

    @property
    def strategies(self):
        return self._strategies