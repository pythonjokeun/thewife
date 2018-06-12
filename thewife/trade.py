import ccxt
import attr

from logzero import logger
from time import sleep
from tenacity import retry, wait_fixed
from notifiers import get_notifier


@attr.s
class Trade:
    exchange = attr.ib()
    apikey = attr.ib()
    apisec = attr.ib()
    pair = attr.ib()
    funds = attr.ib()
    refreshrate = attr.ib()
    pbtoken = attr.ib()

    def __attrs_post_init__(self):
        self.__pushbullet = get_notifier('pushbullet')

    @property
    @retry(wait=wait_fixed(3))
    def __auth(self):
        auth = getattr(ccxt, self.exchange)()
        auth.apiKey = self.apikey
        auth.secret = self.apisec
        auth.adjustForTimeDifference = True
        auth.recvWindow = 10000000

        # Initialize markets data
        auth.load_markets()

        return auth

    @property
    @retry(wait=wait_fixed(3))
    def __market(self):
        return self.__auth.load_markets()[self.pair]

    @property
    @retry(wait=wait_fixed(3))
    def __sell_price(self):
        min_price = self.__market['limits']['price']['min']
        precision = self.__market['precision']['price']
        top_price = self.__auth.fetch_order_book(self.pair)['asks'][0][0]

        return round(top_price - min_price, precision)

    @property
    @retry(wait=wait_fixed(3))
    def __buy_price(self):
        min_price = self.__market['limits']['price']['min']
        precision = self.__market['precision']['price']
        top_price = self.__auth.fetch_order_book(self.pair)['bids'][0][0]

        return round(top_price + min_price, precision)

    def __notify(self, message):
        return self.__pushbullet.notify(message=message, token=self.pbtoken)

    def buy(self):
        try:
            target = self.pair.split('/')[0]
            base = self.pair.split('/')[1]

            def amount(x):
                if x <= 0:
                    bal = self.__auth.fetch_free_balance()
                    x = bal[base]

                amount_target = x / price
                amount_target = self.__auth.amount_to_precision(
                    self.pair, amount_target)

                return amount_target

            price = self.__buy_price

            try:
                logger.info('[' + self.pair + '] ' + 'Attempt to buy ' + target
                            + ' @ ' + '{0:.8f}'.format(price) + ' ' + base)

                self.__notify('Attempt to BUY ' + target + ' @ ' +
                              '{0:.8f}'.format(price) + ' ' + base)

                left = self.funds
                order = self.__auth.create_limit_buy_order(
                    self.pair, amount(self.funds), price)

                sleep(self.refreshrate)

                while True:
                    logger.info(
                        '[' + self.pair + '] ' + 'Check buy order status')
                    order_status = self.__auth.fetch_order(
                        id=order['id'], symbol=order['symbol'])

                    remaining = order_status['remaining']
                    left = abs(left - order_status['cost'])
                    logger.info('[' + self.pair + '] ' + 'Remaining: ' +
                                str(remaining))

                    if (remaining != 0.0 or remaining != 0):
                        logger.info('[' + self.pair + '] ' +
                                    'Buy order was partially filled')
                        logger.info('[' + self.pair + '] ' +
                                    'Cancel previous buy order')

                        self.__auth.cancel_order(
                            id=order_status['id'],
                            symbol=order_status['symbol'])

                        price = self.__buy_price

                        logger.info(
                            '[' + self.pair + '] ' + 'Attempt to buy ' + target
                            + ' @ ' + '{0:.8f}'.format(price) + ' ' + base)

                        order = self.__auth.create_limit_buy_order(
                            order_status['symbol'], amount(left), price)
                    elif (remaining == 0.0 or remaining == 0):
                        logger.info('[' + self.pair + '] ' +
                                    'Successfully bought ' + target)
                        self.__notify('Successfully bought ' + target + ' @ ' +
                                      '{0:.8f}'.format(price) + ' ' + base)
                        break

                    sleep(self.refreshrate)
            except (ccxt.InvalidOrder, ccxt.InsufficientFunds):
                logger.info(
                    '[' + self.pair + '] ' + 'Invalid order or quantity')
                logger.info(
                    '[' + self.pair + '] ' + 'Funds: ' + str(self.funds))
                logger.info('[' + self.pair + '] ' + 'Amount: ' +
                            str(amount(self.funds)))
        except Exception as e:
            logger.exception('[' + self.pair + '] ' + e)

    def sell(self):
        try:
            target = self.pair.split('/')[0]
            base = self.pair.split('/')[1]

            def balance():
                bal = self.__auth.fetch_free_balance()
                return self.__auth.amount_to_precision(self.pair, bal[target])

            price = self.__sell_price

            try:
                logger.info(
                    '[' + self.pair + '] ' + 'Attempt to sell ' + target +
                    ' @ ' + '{0:.8f}'.format(price) + ' ' + base)

                self.__notify('Attempt to SELL ' + target + ' @ ' +
                              '{0:.8f}'.format(price) + ' ' + base)

                order = self.__auth.create_limit_sell_order(
                    self.pair, balance(), price)

                sleep(self.refreshrate)

                while True:
                    logger.info(
                        '[' + self.pair + '] ' + 'Check sell order status')
                    order_id = order['info']['orderId']
                    order_status = self.__auth.fetch_order(
                        id=order_id, symbol=self.pair)

                    remaining = order_status['remaining']
                    logger.info('[' + self.pair + '] ' + 'Remaining: ' +
                                str(remaining))

                    if remaining != 0.0 or remaining != 0:
                        logger.info('[' + self.pair + '] ' +
                                    'Sell order was partially filled')
                        logger.info('[' + self.pair + '] ' +
                                    'Cancel previous sell order')
                        self.__auth.cancel_order(id=order_id, symbol=self.pair)

                        price = self.__sell_price

                        logger.info('[' + self.pair + '] ' +
                                    'Attempt to sell ' + target + ' @ ' +
                                    '{0:.8f}'.format(price) + ' ' + base)

                        order = self.__auth.create_limit_sell_order(
                            self.pair, balance(), price)
                    elif remaining == 0.0 or remaining == 0:
                        logger.info('[' + self.pair + '] ' +
                                    'Successfully sold ' + target)
                        self.__notify('Successfully sold ' + target + ' @ ' +
                                      '{0:.8f}'.format(price) + ' ' + base)
                        break

                    sleep(self.refreshrate)
            except (ccxt.InvalidOrder, ccxt.InsufficientFunds):
                logger.info(
                    '[' + self.pair + '] ' + 'Invalid order or quantity')
                logger.info(
                    '[' + self.pair + '] ' + 'Balance: ' + str(balance()))
        except Exception as e:
            logger.exception('[' + self.pair + '] ' + e)
