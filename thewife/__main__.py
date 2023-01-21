from .indicator import Indicator
from .trade import Trade
from .util import wait

from yaml import load
from argparse import ArgumentParser
from pyfiglet import Figlet
from logzero import logger


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

        while True:
            with open(confloc) as f:
                conf = load(f)

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
                refreshrate=conf['trade']['ordercheck'],
                pbtoken=conf['creds']['pushbullet']['token'])

            last_act = 'sell'
            parameter = indicator.setting['parameter']

            while True:
                wait(conf['trade']['candlestick'])

                data = indicator.indicator
                current_indicator = data.indicator.tolist()[-1]

                logger.info('Current price: ' +
                            '{0:.8f}'.format(data.close.tolist()[-1]))
                logger.info('Current indicator: ' +
                            '{0:.2f}'.format(current_indicator))

                if last_act == 'sell' and (current_indicator <=
                                           parameter['lower']):
                    last_act = 'buy'
                    trade.buy()
                elif last_act == 'buy' and (current_indicator >=
                                            parameter['upper']):
                    trade.sell()
                    break
    except KeyboardInterrupt:
        quit()


if __name__ == '__main__':
    main()
