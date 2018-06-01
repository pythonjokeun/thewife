from datetime import datetime, timedelta
from time import sleep
from logzero import logger


def wait(amount):
    amount = amount.lower()

    if 'h' in amount:
        waittime = int(amount.replace('h', ''))
        nexttime = datetime.now() + timedelta(hours=waittime)

        while True:
            now = datetime.now()
            if (now.hour %
                    waittime) == 0 and now.minute == 0 and now.second == 1:
                nexttime = now + timedelta(hours=waittime)
                logger.info('Next run at: ' + nexttime.strftime('%H:%M:%S'))
                break

            sleep(1)

    elif 'm' in amount:
        waittime = int(amount.replace('m', ''))

        while True:
            now = datetime.now()
            if (now.minute % waittime) == 0 and now.second == 1:
                nexttime = now + timedelta(minutes=waittime)
                break

            sleep(1)

    else:
        raise ValueError(amount)
