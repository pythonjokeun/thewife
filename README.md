# The Wife

> ***Behind every great man there stands a great wife*** ~ Unknown

## Overview

**Wife** is a crypto trading bot that reacts to optimized **RSI** signal. Basically, bot will place a buy order when it reach **RSI** lower threshold (oversold) and will place a sell order when it reach **RSI** upper threshold (overbought). All of the **RSI** settings are automatically optimized for optimal profit via [hyperopt](https://github.com/hyperopt/hyperopt) library.

## Disclaimer

- USE THIS BOT AT YOUR OWN RISK!
- DO NOT RISK THE MONEY YOU AFRAID TO LOSE!
- THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS!

## Installation

`pip install git+https://github.com/pythonjokeun/thewife`

## Usage

This bot only works on **Python 3**.

1. Setup a `.yaml` configuration file, for example `my-config-file.yaml`.

2. Simply run `wife --config my-config-file.yaml`, where `my-config-file.yaml` is the configuration file that you've setup from the first step.

## Configuration File:

In order to start the bot you need a configuration file. Below, is the structure of configuration file.

```
creds:
  account:
    exchange: '...'
    apikey: '...'
    apisec: '...'
  pushbullet:
    token: '...'

trade:
  pair: '...'
  funds: ...
  candlestick: '...'
  history: ...
  ordercheck: ...
```

Fields surrounded with quotes (`'...'`) are expecting string as input, and without quotes (`...`) are expecting numeric value as input.

Since this bot uses [ccxt](https://github.com/ccxt/ccxt) to interact with exchanges' APIs, some of the configuration values for this bot are inherited from [ccxt](https://github.com/ccxt/ccxt) configuration values. For possible values for all of these fields below, refer to the linked page.

- [exchange](https://github.com/ccxt/ccxt/wiki/Manual#exchanges), contains name of the trading exchange (e.g **binance**).
- [pair](https://github.com/ccxt/ccxt/wiki/Manual#symbols-and-market-ids), contains name of trading pair (e.g **BTC/USDT**).
- [candlestick](https://github.com/ccxt/ccxt/wiki/Manual#ohlcv-candlestick-charts), contains size of the candlestick (e.g **1h**).
- [history](https://github.com/ccxt/ccxt/wiki/Manual#ohlcv-candlestick-charts), contains candlestick history size (e.g **100**).

The rest of configuration fields are explained below.

- `token`, contains your [pushbullet](https://www.pushbullet.com/) API access token.
- `funds`, contains amount of base currency you would like to trade.
- `ordercheck`, contains seconds interval for checking placed order.

Notice that, [pushbullet](https://www.pushbullet.com/) API access token is mandatory at the moment, so any buy / sell activity won't out of your sight.

## Tested Exchange

- [x] Binance

## Credits

Hats off to [hyperopt](https://github.com/hyperopt/hyperopt) and [ccxt](https://github.com/ccxt/ccxt) authors! Without them, this bot won't be available! 🙏🙏🙏

## Tip Jar

If this bot helped you in any way, you can always leave me a tip at:

- BTC: `1NpuZv5vzhV3JobdAsFExvW617BimFQ6i5`
- ETH: `0x7d9640a7107b344ea9784ffc54dafbb85d6e052c`
