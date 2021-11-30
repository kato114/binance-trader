#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @vladyslav

import sys
import argparse

sys.path.insert(0, './app')

from Trading import Trading

if __name__ == '__main__':

    # Set parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--amount', type=float, help='Buy/Sell BTC Amount (Ex: 0.002 BTC)', default=1, required=True)
    parser.add_argument('--symbol', type=str, help='Market Symbol (Ex: XVGBTC - XVGETH)', required=True)

    parser.add_argument('--wait_time', type=float, help='Wait Time (seconds)', default=300)
    parser.add_argument('--debug', help='Debug True/False if set --debug flag, will output all messages every "--wait_time" ',
                        action="store_true", default=False) # 0=True, 1=False
    parser.add_argument('--direction', type=str, help='Order Direction (buy/sell)', default="buy", required=True)
    parser.add_argument('--split_amount', type=str, help='Split Amount', default=0.1, required=True)

    option = parser.parse_args()

    # Get start
    t = Trading(option)
    t.run()
