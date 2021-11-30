# -*- coding: UTF-8 -*-
# @yasinkuyu

# Define Python imports
import os
import sys
import time
import config
import threading
import math
import logging
import logging.handlers
import json

# from binance_f import RequestClient
# from binance_f.constant.test import *
# from binance_f.base.printobject import *
# from binance_f.model.constant import *

# request_client = RequestClient(api_key=config.api_key, secret_key=config.api_secret)

from BinanceAPI import BinanceAPI
client = BinanceAPI(config.api_key, config.api_secret)

# Define Custom imports
from Database import Database
from Orders import Orders


formater_str = '%(asctime)s,%(msecs)d %(levelname)s %(name)s: %(message)s'
formatter = logging.Formatter(formater_str)
datefmt="%Y-%b-%d %H:%M:%S"

LOGGER_ENUM = {'debug':'debug.log', 'trading':'trades.log','errors':'general.log'}
#LOGGER_FILE = LOGGER_ENUM['pre']
LOGGER_FILE = "binance-trader.log"
FORMAT = '%(asctime)-15s - %(levelname)s:  %(message)s'

logger = logging.basicConfig(filename=LOGGER_FILE, filemode='a',
                             format=formater_str, datefmt=datefmt,
                             level=logging.INFO)

# Aproximated value to get back the commision for sell and buy
TOKEN_COMMISION = 0.001
BNB_COMMISION   = 0.0005
#((eth*0.05)/100)


class Trading():

    # Define trade vars  
    order_id = 0
    
    # BTC amount
    amount = 0
    quantity = 0
    count = 0
    split_count = 0
    direction = None
    wait_time = 300
    minPrice = 0

    WAIT_TIME_CHECK = 2 # seconds

    # minNotional = 0

    def __init__(self, option):
        print("options: {0}".format(option))

        # Get argument parse options
        self.option = option

        # Define parser vars
        self.order_id = 0
        self.split_count = float(self.option.amount) / float(self.option.split_amount)
        self.count = 0

        self.wait_time = int(self.option.wait_time)
        self.direction = self.option.direction

        # BTC amount
        self.amount = self.option.amount
        self.quantity = self.option.split_amount

        # setup Logger
        self.logger =  self.setup_logger(self.option.symbol, debug=self.option.debug)

    def setup_logger(self, symbol, debug=True):
        """Function setup as many loggers as you want"""
        #handler = logging.FileHandler(log_file)
        #handler.setFormatter(formatter)
        #logger.addHandler(handler)
        logger = logging.getLogger(symbol)

        stout_handler = logging.StreamHandler(sys.stdout)
        if debug:
            logger.setLevel(logging.DEBUG)
            stout_handler.setLevel(logging.DEBUG)

        #handler = logging.handlers.SysLogHandler(address='/dev/log')
        #logger.addHandler(handler)
        stout_handler.setFormatter(formatter)
        logger.addHandler(stout_handler)
        return logger

    # def futureOrder(self, symbol, orderDirect, quantity):
    #     futureResult = request_client.post_order(symbol, orderDirect, OrderType.MARKET, None, quantity)
        
    #     jsonFutureResult = json.dumps(futureResult.__dict__)
    #     jsonFutureResult = json.loads(jsonFutureResult)
    #     print("json future result")
    #     print(jsonFutureResult)
    #     # PrintBasic.print_obj(futureResult)
    #     print(jsonFutureResult['orderId'])
    #     # exit(1)
    #     futureOrderId = jsonFutureResult['orderId']
        
    #     # exit()
    #     result = request_client.get_order(symbol=symbol, orderId=futureOrderId)
    #     print("future get order:")
    #     jsonResult = json.dumps(result.__dict__)
    #     jsonResult = json.loads(jsonResult)
    #     # print(result)
    #     while jsonResult['status'] != "FILLED":
    #         time.sleep(self.WAIT_TIME_CHECK)
    #         result = request_client.get_order(symbol=symbol, orderId=futureOrderId)
    #         jsonResult = json.dumps(result.__dict__)
    #         jsonResult = json.loads(jsonResult)

    #     self.action(symbol)
    def buy(self, symbol, quantity, buyPrice):
        # Do you have an open order?
        self.check_order()
        
        try:
            # Create order
            orderId = Orders.buy_limit(symbol, quantity, buyPrice)
            
            # Database log
            # Database.write([orderId, symbol, 0, buyPrice, 'BUY', quantity])
            # print('Buy order created id:%d, q:%.8f, p:%.8f' % (orderId, quantity, float(buyPrice)))
            self.logger.info('%s : Buy order created id:%d, q:%.8f, p:%.8f' % (symbol, orderId, quantity, float(buyPrice)))
            time.sleep(self.WAIT_TIME_CHECK)
            print("order ID: %d" % (orderId))

            self.order_id = orderId

            wait_time = self.wait_time - self.WAIT_TIME_CHECK

            startTime = time.time()
            period = 0
            flag = 0
            while (period <= wait_time):
                # time.sleep(self.WAIT_TIME_CHECK)
                order = Orders.get_order(symbol, orderId)
                if 'msg' in order:
                    endTime = time.time()
                    period = endTime - startTime
                    time.sleep(self.WAIT_TIME_CHECK)
                    continue
                if order['status'] == 'FILLED':
                    print("future order SUCESS______")
                    self.order_id = 0
                    self.count = self.count + 1
                    # actionTrader = threading.Thread(target=self.futureOrder, args=(symbol, OrderSide.SELL, quantity))
                    # actionTrader.start()
                    return
                    
                endTime = time.time()
                period = endTime - startTime
            
            self.cancel(symbol, orderId)
            self.order_id = 0
            # self.action(symbol)
        except Exception as e:
            #print('bl: %s' % (e))
            self.logger.debug('Buy order error: %s' % (e))
            return None

    def sell(self, symbol, quantity, sell_price):

        '''
        The specified limit will try to sell until it reaches.
        If not successful, the order will be canceled.
        '''
        
        self.check_order()
        try:
            sell_order = Orders.sell_limit(symbol, quantity, sell_price)

            time.sleep(self.WAIT_TIME_CHECK)
            sell_id = sell_order['orderId']
            self.order_id = sell_id

            print("order ID: %d" % (sell_id))
            # self.logger.info('Sell order create id: %d' % sell_id)
            self.logger.info('%s : Sell order created id:%d, q:%.8f, p:%.8f' % (symbol, sell_id, quantity, float(sell_price)))
            
            wait_time = self.wait_time - self.WAIT_TIME_CHECK

            startTime = time.time()
            period = 0
            flag = 0
            while (period <= wait_time):
                # time.sleep(self.WAIT_TIME_CHECK)
                order = Orders.get_order(symbol, sell_id)
                if 'msg' in order:
                    endTime = time.time()
                    period = endTime - startTime
                    time.sleep(self.WAIT_TIME_CHECK)
                    continue
                if order['status'] == 'FILLED':
                    self.order_id = 0
                    self.count = self.count + 1
                    print("future order SUCESS______")
                    # actionTrader = threading.Thread(target=self.futureOrder, args=(symbol, OrderSide.BUY, quantity))
                    # actionTrader.start()
                    return
                endTime = time.time()
                period = endTime - startTime
            
            self.cancel(symbol, sell_id)
            self.order_id = 0
            # self.action(symbol)
        except Exception as e:
            #print('bl: %s' % (e))
            self.logger.debug('Sell order error: %s' % (e))
            return None

    def cancel(self, symbol, orderId):
        # If order is not filled, cancel it.
        check_order = Orders.get_order(symbol, orderId)

        if not check_order:
            self.order_id = 0
            return True

        if check_order['status'] == 'NEW' or check_order['status'] != 'CANCELLED':
            Orders.cancel_order(symbol, orderId)
            self.order_id = 0
            return True

    def check_order(self):
        # If there is an open order, exit.
        if self.order_id > 0:
            print("check order error")
            exit(1)

    def action(self):
        #import ipdb; ipdb.set_trace()

        info = client.get_account()
        print(info)
        exit(1)
        print("action start_______________")
        if self.count == self.split_count:
            print("count filled finish")
            exit(1)
        
        # Order amount
        quantity = self.quantity

        # Order book prices
        lastBid, lastAsk = Orders.get_order_book(symbol)

        # Target buy price, add little increase #87
        buyPrice = lastBid * 0.999

        # Target sell price, decrease little 
        sellPrice = lastAsk * 1.001

        if self.direction == 'buy':
            # notional = self.quantity * buyPrice
            tradePrice = buyPrice
        else:
            # notional = self.quantity * sellPrice
            tradePrice = sellPrice
        
        print('Calculated Trade Price(0.999 or 1.001): %.8f' % tradePrice)
        if (tradePrice * 100000000) % (self.minPrice * 100000000) != 0:
            if self.direction == 'buy':
                tradePrice = int((tradePrice * 100000000)/(self.minPrice * 100000000))*self.minPrice
            else:
                tradePrice = (int((tradePrice * 100000000)/(self.minPrice * 100000000)) + 1)*self.minPrice

        print('Rounded Trade Price: %.8f' % tradePrice)
        # if notional < self.minNotional:
        #     self.logger.error('Invalid notional, minNotional: %.8f (u: %.8f)' % (self.minNotional, notional))
        #     exit(1)
        # if tradePrice < self.minPrice:
        #     self.logger.error('Invalid price, minPrice: %.8f (u: %.8f)' % (self.minPrice, tradePrice))
        #     exit(1)
        print("action start_______________3")
        # Screen log
        if self.direction == 'buy':
            self.buy(symbol, quantity, tradePrice)
        else:
            self.sell(symbol, quantity, tradePrice)
        print("action start_______________4")
    def filters(self):

        symbol = self.option.symbol

        # Get symbol exchange info
        symbol_info = Orders.get_info(symbol)

        if not symbol_info:
            #print('Invalid symbol, please try again...')
            self.logger.error('Invalid symbol, please try again...')
            exit(1)

        symbol_info['filters'] = {item['filterType']: item for item in symbol_info['filters']}

        return symbol_info

    def futureFilters(self):

        symbol = self.option.symbol

        # Get symbol exchange info
        symbol_info = Orders.get_future_info(symbol)

        if not symbol_info:
            #print('Invalid symbol, please try again...')
            self.logger.error('Invalid symbol, please try again...')
            exit(1)

        symbol_info['filters'] = {item['filterType']: item for item in symbol_info['filters']}

        return symbol_info

    def validate(self):

        # valid = True
        symbol = self.option.symbol
        filters = self.filters()['filters']
        futureFilters = self.futureFilters()['filters']

        minQty = float(filters['LOT_SIZE']['minQty'])
        self.minPrice = float(filters['PRICE_FILTER']['minPrice'])
        minNotional = float(filters['MIN_NOTIONAL']['minNotional'])
        
        minFutureQty = float(futureFilters['LOT_SIZE']['minQty'])
        minFutureNotional = float(futureFilters['MIN_NOTIONAL']['notional'])

        quantity = float(self.option.split_amount)
        amount = float(self.option.amount)
        
        lastBid, lastAsk = Orders.get_order_book(symbol)
        notional = lastBid * float(quantity)

        lastFutureBid, lastFutureAsk = Orders.get_future_order_book(symbol)
        futureNotional = lastFutureBid * float(quantity)

        self.amount = amount
        self.quantity = quantity

        if amount < quantity:
            self.logger.error('Invalid amount, splitAmount: %.8f, %.8f' % (amount, quantity))
            exit(1)
        if self.direction != "buy" and self.direction != "sell":
            self.logger.error('Invalid direction. Should be "buy" or "sell": %.s' % (self.direction))
            exit(1)
        # minQty = minimum order quantity
        if quantity < minQty:
            #print('Invalid quantity, minQty: %.8f (u: %.8f)' % (minQty, quantity))
            self.logger.error('Invalid quantity, minQty: %.8f (u: %.8f)' % (minQty, quantity))
            exit(1)

        if quantity < minFutureQty:
            #print('Invalid quantity, minQty: %.8f (u: %.8f)' % (minQty, quantity))
            self.logger.error('Invalid future quantity, minQty: %.8f (u: %.8f)' % (minFutureQty, quantity))
            exit(1)

        if notional < minNotional:
            #print('Invalid notional, minNotional: %.8f (u: %.8f)' % (minNotional, notional))
            self.logger.error('Invalid notional, minNotional: %.8f (u: %.8f)' % (minNotional, notional))
            exit(1)

        if futureNotional < minFutureNotional:
            #print('Invalid notional, minNotional: %.8f (u: %.8f)' % (minNotional, notional))
            self.logger.error('Invalid future notional, minNotional: %.8f (u: %.8f)' % (minFutureNotional, minNotional))
            exit(1)

    def run(self):

        cycle = 0
        actions = []

        symbol = self.option.symbol

        print('Auto Trading for Binance.com @vladyslav')
        print('\n')

        # Validate symbol
        self.validate()

        print('Started...')
        print('Trading Symbol: %s' % symbol)
        # print('Amount: %.3f' % self.quantity)
        # print('Split Amount: %.3f' % self.quantity)
        self.action()