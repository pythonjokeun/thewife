import attr
import ccxt
import numpy

from pandas import DataFrame as df
from datetime import datetime as dt
from pyti.relative_strength_index import relative_strength_index as rsi
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
            'lower': range(0, 50),
            'upper': range(51, 100)
        }

        self.setting = self.__optimize_signal(possible_setting)

    @retry(wait=wait_fixed(9))
    def __fetch_ohlcv(self):
        logger.info('Fetch candlestick data')
        try:
            result = getattr(ccxt, self.exchange)().fetch_ohlcv(
                symbol=self.pair, timeframe=self.interval, limit=self.history)

            def totime(x):
                result = float(x) / 1000
                result = int(result)
                return dt.fromtimestamp(result).strftime('%Y-%m-%d %H:%M:%S')

            result = df.from_dict({
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

            result = result.loc[:, [
                'time', 'open', 'high', 'low', 'close', 'volume'
            ]]

            return result
        except Exception as e:
            logger.exception(e)

    def __compute_indicator(self, period, lower, upper):
        try:
            data = self.ohlcv.copy()
            indicator = rsi(data.close, int(period))
            data.loc[:, 'indicator'] = indicator

            return data
        except Exception as e:
            logger.exception(e)

    def __optimize_signal(self, possibilities):
        logger.info('Optimize indicator parameters')
        try:

            def compute_profit(params):
                if self.verbose == 1:
                    logger.info('Indicator parameter:')
                    logger.info('\tPeriod: ' + str(params['period']))
                    logger.info('\tLower threshold: ' + str(params['lower']))
                    logger.info('\tUpper threshold: ' + str(params['upper']))
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
                max_evals=1000,
                trials=trials)

            params = space_eval(possibilities, hyperopt_result)
            profit = compute_profit(params)
            profit = '{0:.1f}'.format(profit)
            result = {'parameter': params, 'profit': profit}

            logger.info('Parameter optimization result:')
            logger.info('\tPeriod: ' + str(params['period']))
            logger.info('\tUpper threshold: ' + str(params['upper']))
            logger.info('\tLower threshold: ' + str(params['lower']))
            logger.info('\tProfit: ' + profit + ' %')

            return result
        except Exception as e:
            logger.exception(e)

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
