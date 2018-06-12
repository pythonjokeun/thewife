import attr
import ccxt
import numpy

from pandas import DataFrame as df
from datetime import datetime as dt
from pyti.money_flow_index import money_flow_index as mfi
from hyperopt import fmin, hp, tpe, Trials, STATUS_OK, space_eval
from pandas import set_option
from logzero import logger
from tenacity import retry, wait_fixed

set_option('precision', 8)


@attr.s
class Indicator:
    exchange = attr.ib()
    pair = attr.ib()
    interval = attr.ib()
    history = attr.ib()
    verbose = attr.ib()
    ohlcv = attr.ib(init=False)
    setting = attr.ib(init=False)

    def __attrs_post_init__(self):
        self.ohlcv = self.__fetch_ohlcv()

        possible_setting = {
            'period': range(2, 15),
            'lower': range(20, 51),
            'upper': range(51, 81)
        }

        self.setting = self.__optimize_signal(possible_setting)

    @retry(wait=wait_fixed(9))
    def __fetch_ohlcv(self):
        logger.info('[' + self.pair + '] ' + 'Fetch candlestick data')
        try:
            result = getattr(ccxt, self.exchange)().fetch_ohlcv(
                symbol=self.pair, timeframe=self.interval, limit=self.history)

            def totime(x):
                result = float(x) / 1000
                result = int(result)
                return dt.fromtimestamp(result).strftime('%Y-%m-%d %H:%M:%S')

            ohlcv = df.from_dict({
                'time':
                list(map(lambda c: totime(c[0]), result)),
                'open':
                list(map(lambda c: float(c[1]), result)),
                'high':
                list(map(lambda c: float(c[2]), result)),
                'low':
                list(map(lambda c: float(c[3]), result)),
                'close':
                list(map(lambda c: float(c[4]), result)),
                'volume':
                list(map(lambda c: float(c[5]), result))
            })

            ohlcv_copy = ohlcv.copy()

            ohlcv_copy.loc[:, 'ha_close'] = (
                ohlcv_copy.loc[:, 'open'] + ohlcv_copy.loc[:, 'high'] +
                ohlcv_copy.loc[:, 'low'] + ohlcv_copy.loc[:, 'close']) / 4

            ohlcv_copy.loc[:, 'ha_open'] = (ohlcv_copy.loc[:, 'open'].shift(
                1) + ohlcv_copy.loc[:, 'close'].shift(1)) / 2

            ohlcv_copy.loc[:1, 'ha_open'] = ohlcv_copy.loc[:, 'open'].values[0]

            ohlcv_copy.loc[1:, 'ha_open'] = (
                (ohlcv_copy.loc[:, 'ha_open'].shift(1) +
                 ohlcv_copy.loc[:, 'ha_close'].shift(1)) / 2)[1:]

            ohlcv_copy.loc[:, 'ha_high'] = ohlcv_copy.loc[:, [
                'high', 'ha_open', 'ha_close'
            ]].max(axis=1)

            ohlcv_copy.loc[:, 'ha_low'] = ohlcv_copy.loc[:, [
                'low', 'ha_open', 'ha_close'
            ]].min(axis=1)

            result = df.from_dict({
                'time': ohlcv_copy.loc[:, 'time'],
                'open': ohlcv_copy.loc[:, 'ha_open'],
                'high': ohlcv_copy.loc[:, 'ha_high'],
                'low': ohlcv_copy.loc[:, 'ha_low'],
                'close': ohlcv_copy.loc[:, 'ha_close'],
                'volume': ohlcv_copy.loc[:, 'volume']
            })

            return result
        except Exception as e:
            logger.exception('[' + self.pair + '] ' + e)

    def __compute_indicator(self, period, lower, upper):
        try:
            data = self.ohlcv.copy()
            indicator = mfi(data.close, data.high, data.low, data.volume,
                            int(period))
            data.loc[:, 'indicator'] = indicator

            return data
        except Exception as e:
            logger.exception('[' + self.pair + '] ' + e)

    def __optimize_signal(self, possibilities):
        logger.info('[' + self.pair + '] ' + 'Optimize indicator parameters')
        try:

            def compute_profit(params):
                if self.verbose == 1:
                    logger.info(
                        '[' + self.pair + '] ' + 'Indicator parameter:')
                    logger.info('[' + self.pair + '] ' + '\tPeriod: ' +
                                str(params['period']))
                    logger.info('[' + self.pair + '] ' +
                                '\tLower threshold: ' + str(params['lower']))
                    logger.info('[' + self.pair + '] ' +
                                '\tUpper threshold: ' + str(params['upper']))
                else:
                    pass

                data = self.__compute_indicator(
                    period=params['period'],
                    lower=params['lower'],
                    upper=params['upper'])

                signal = numpy.where(
                    data.indicator <= params['lower'], 'buy',
                    numpy.where(data.indicator >= params['upper'], 'sell',
                                'hold'))

                lastsignal = 'hold'

                for i in range(len(signal)):
                    if signal[i] == 'buy' and lastsignal != 'buy':
                        signal[i] = 'buy'
                        lastsignal = 'buy'
                    elif signal[i] == 'sell' and lastsignal != 'sell':
                        signal[i] = 'sell'
                        lastsignal = 'sell'
                    else:
                        signal[i] = 'hold'

                data.loc[:, 'signal'] = signal
                data = data.loc[:, ['close', 'signal']]

                # filter only rows that contain buy or sell signal
                data = data.query('signal == "buy" or signal == "sell"')

                nsignal = data.signal.tolist()
                nsignal = len(nsignal)

                if nsignal >= 2:
                    # if last signal == 'buy', remove it
                    if data.tail(1).signal.values == 'buy':
                        data = data.iloc[:-1]

                    # if first signal == 'sell', remove it
                    if data.head(1).signal.values == 'sell':
                        data = data.iloc[1:]

                    # calculate buy and sell profit
                    data = data.assign(shifted=data.close.shift(1))

                    # profit = 100 * (sell price - buy price) / sell price
                    profit = 100 * (data.shifted - data.close) / data.shifted
                    data = data.assign(profit=profit)

                    # fill na with 0
                    data = data.fillna(0)

                    # calculate total profit
                    result = numpy.sum(data.profit.values)
                else:
                    result = 0

                return result

            def f(params):
                profit = compute_profit(params)
                return {'loss': -profit, 'status': STATUS_OK}

            for key, val in possibilities.items():
                possibilities[key] = hp.choice(key, val)

            trials = Trials()

            hyperopt_result = fmin(
                f,
                possibilities,
                algo=tpe.suggest,
                max_evals=500,
                trials=trials)

            params = space_eval(possibilities, hyperopt_result)
            profit = compute_profit(params)
            profit = '{0:.1f}'.format(profit)
            result = {'parameter': params, 'profit': profit}

            logger.info(
                '[' + self.pair + '] ' + 'Parameter optimization result:')
            logger.info(
                '[' + self.pair + '] ' + '\tPeriod: ' + str(params['period']))
            logger.info('[' + self.pair + '] ' + '\tUpper threshold: ' +
                        str(params['upper']))
            logger.info('[' + self.pair + '] ' + '\tLower threshold: ' +
                        str(params['lower']))
            logger.info('[' + self.pair + '] ' + '\tProfit: ' + profit + ' %')

            return result
        except Exception as e:
            logger.exception('[' + self.pair + '] ' + e)

    @property
    def indicator(self):
        # refresh candlestick
        self.ohlcv = self.__fetch_ohlcv()

        # compute signal with best parameter
        data = self.__compute_indicator(
            period=self.setting['parameter']['period'],
            lower=self.setting['parameter']['lower'],
            upper=self.setting['parameter']['upper'])

        return data
