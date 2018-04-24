from .indicator import Indicator
from .trade import Trade
from .util import wait

from yaml import load
from argparse import ArgumentParser
from pyfiglet import Figlet
from logzero import logger
from notifiers import get_notifier


def main():
    try:
        parser = ArgumentParser(description='Crypto trading bot ' +
                                'that reacts to optimized RSI signal')
        parser.add_argument(
            '--config',
            '-c',
            required=True,
            type=str,
            help='configuration file location')
        parser.add_argument(
            '--verbose',
            '-v',
            required=False,
            default=0,
            type=int,
            help='output verbosity')
        args = parser.parse_args()

        if args.verbose not in [1, 0]:
            raise ValueError('Only 0 or 1 allowed in --verbose!')

        figlet = Figlet(font='lean')
        welcome_banner = figlet.renderText('THE WIFE')
        print(welcome_banner)

        print('"Behind every great man there stands a great wife"' +
              ' ~ Unknown\n\n')

        print('DISCLAIMER:')
        print('USE THIS BOT AT YOUR OWN RISK. ' +
              'DO NOT RISK THE MONEY YOU AFRAID TO LOSE.\n' +
              'THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY ' +
              'FOR YOUR TRADING RESULTS\n\n')

        confloc = args.config

        with open(confloc) as f:
            conf = load(f)

        pushbullet = get_notifier('pushbullet')
        base = conf['trade']['pair'].split('/')[1]
        target = conf['trade']['pair'].split('/')[0]

        while True:
            indicator = Indicator(
                exchange=conf['creds']['account']['exchange'],
                pair=conf['trade']['pair'],
                interval=conf['trade']['candlestick'],
                history=conf['trade']['history'],
                verbose=args.verbose)

            trade = Trade(
                exchange=conf['creds']['account']['exchange'],
                apikey=conf['creds']['account']['apikey'],
                apisec=conf['creds']['account']['apisec'],
                pair=conf['trade']['pair'],
                funds=conf['trade']['funds'],
                refreshrate=conf['trade']['ordercheck'])

            last_act = 'sell'
            count = 1

            while True:
                wait(conf['trade']['candlestick'])

                candle = indicator.signal
                current_signal = candle.signal.tolist()[-1]
                current_indicator = candle.indicator.tolist()[-1]
                current_indicator = '{0:.2f}'.format(current_indicator)
                current_price = candle.close.tolist()[-1]
                current_price = '{0:.8f}'.format(current_price)

                logger.info('Current price: ' + current_price)
                logger.info('Current indicator: ' + current_indicator)
                logger.info('Current signal: ' + current_signal.capitalize())

                # buy when lower threshold passed on bot start
                if count == 1 and (float(current_indicator) <=
                                   indicator.setting['parameter']['lower']):
                    last_act = 'buy'
                    message = ('Attempt to BUY ' + target + ' @ ' +
                               current_price + ' ' + base)
                    pushbullet.notify(
                        message=message,
                        token=conf['creds']['pushbullet']['token'])
                    trade.buy()
                    count += 1
                # regular buy
                elif last_act == 'sell' and current_signal == 'buy':
                    last_act = 'buy'
                    message = ('Attempt to BUY ' + target + ' @ ' +
                               current_price + ' ' + base)
                    pushbullet.notify(
                        message=message,
                        token=conf['creds']['pushbullet']['token'])
                    trade.buy()
                    count += 1
                # regular sell
                elif last_act == 'buy' and current_signal == 'sell':
                    message = ('Attempt to SELL ' + target + ' @ ' +
                               current_price + ' ' + base)
                    pushbullet.notify(
                        message=message,
                        token=conf['creds']['pushbullet']['token'])
                    trade.sell()
                    break
                else:
                    count += 1
    except KeyboardInterrupt:
        quit()


if __name__ == '__main__':
    main()
