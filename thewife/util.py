from datetime import datetime
from time import sleep


def wait(amount):
    amount = amount.lower()

    if 'h' in amount:
        waittime = int(amount.replace('h', ''))

        while True:
            now = datetime.now()
            if (now.hour %
                    waittime) == 0 and now.minute == 0 and now.second == 1:
                break

            sleep(1)

    elif 'm' in amount:
        waittime = int(amount.replace('m', ''))

        while True:
            now = datetime.now()
            if (now.minute % waittime) == 0 and now.second == 1:
                break

            sleep(1)

    else:
        raise ValueError(amount)
