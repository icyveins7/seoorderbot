from telegram.ext import Updater, CommandHandler, MessageHandler, MessageFilter, Filters, CallbackQueryHandler, CallbackContext
from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import datetime as dt
import re
import os
import time
# import ntpath
import numpy as np
from bot_commonHandlers import *

# class MenuFilter(MessageFilter):
#     def __
    
#     def filter(message):
        

class OrderBot:
    def __init__(self, API_TOKEN=None):
        if API_TOKEN is None:
            self.API_TOKEN = os.environ['ORDERBOTTOKEN']
        else:
            self.API_TOKEN = API_TOKEN
            
        self.updater = Updater(token=self.API_TOKEN, use_context=True)
        self.dispatcher = self.updater.dispatcher
        
        # define menu (2-layer should cover everything?)
        self.menu = {'Kopi': {'Normal', 'Siew Dai', 'Gau', 'Gah Dai', 'Po'},
                     'Kopi-O': {'Normal', 'Siew Dai', 'Gau', 'Kosong', 'Po', 'Kosong Di Lo'},
                     'Kopi-C': {'Normal', 'Siew Dai', 'Gau', 'Gah Dai', 'Po'},
                     'Teh': {'Normal', 'Siew Dai', 'Gau', 'Gah Dai', 'Po'}, 
                     'Teh-O': {'Normal', 'Siew Dai', 'Gau', 'Kosong', 'Po', 'Kosong Di Lo'},
                     'Teh-C': {'Normal', 'Siew Dai', 'Gau', 'Gah Dai', 'Po'},
                     'Canned': {'Coke', 'Pepsi'}}
        self.unpackedMenu = []
        for i in self.menu.keys():
            for j in self.menu[i]:
                self.unpackedMenu.append(i + ' ' + j)
        print(self.unpackedMenu)
                
        # build the filters for later
        MenuCoarse = list(self.menu.keys())
        self.filtMenuCoarse = Filters.regex(MenuCoarse[0])
        for i in range(1,len(MenuCoarse)):
            self.filtMenuCoarse = self.filtMenuCoarse | Filters.regex(MenuCoarse[i])
        
        # self.filtMenuFine = Filters.regex(self.unpackedMenu[0])
        # for i in range(1,len(self.unpackedMenu)):
        #     self.filtMenuFine = self.filtMenuFine | Filters.regex(self.unpackedMenu[i])
        # print(self.filtMenuFine)
        
        
        
        # define states
        self.nowOrdering = False
        
        # containers
        self.orders = []
        
    
        
    def run(self):
        self.dispatcher.add_handler(CommandHandler('status', self.check))
        self.dispatcher.add_handler(MessageHandler(Filters.regex(r'Drinks?'), self.openOrder))
        self.dispatcher.add_handler(MessageHandler(Filters.regex(r'Order'), self.addToOrder))
        self.dispatcher.add_handler(MessageHandler(Filters.regex(r'Done'), self.closeOrder))
        self.dispatcher.add_handler(MessageHandler(self.filtMenuCoarse, self.editOrder))
        # self.dispatcher.add_handler(MessageHandler(self.filtMenuFine, self.addIceToOrder))
        
        print("Bot initialization complete.")
        self.updater.start_polling()
        self.updater.idle()

    def check(self, update, context):
        status(update, context)

    def openOrder(self, update, context):
        if self.nowOrdering is False:
            self.nowOrdering = True
            
            # kb = [[InlineKeyboardButton(i, callback_data=i)] for i in list(self.menu.keys())]
            
            # kb_markup = InlineKeyboardMarkup(kb)
            
            # context.bot.send_message(chat_id=update.message.chat_id, text='Please begin orders by typing "O".',
            #                          reply_markup=kb_markup)
            context.bot.send_message(chat_id=update.message.chat_id, text='Please begin orders by typing "Order".')
            
        else:
            context.bot.send_message(chat_id=update.message.chat_id, text='Ongoing order; type "Order" to order.')
    
    def addToOrder(self, update, context):
        if self.nowOrdering is True:
            kb = [[KeyboardButton(i)] for i in list(self.menu.keys())]
            name = update.message.from_user.first_name
            context.bot.send_message(chat_id=update.message.chat_id, text=name + ' is adding an item..', 
                                     reply_to_message_id=update.message.message_id,
                                     reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, selective=True))
    
    def editOrder(self, update, context):
        if self.nowOrdering is True:
            # coarse -> fine stage
            if update.message.text in self.menu.keys():
                item = update.message.text
                name = update.message.from_user.first_name
                # spawn a keyboard with the customised text
                kb = [[KeyboardButton(item+' '+i)] for i in list(self.menu[item])]
                context.bot.send_message(chat_id=update.message.chat_id, text=name + ' is customising an item..', 
                                     reply_to_message_id=update.message.message_id,
                                     reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, selective=True))
            # add ice stage
            elif update.message.text in self.unpackedMenu:
                item = update.message.text
                name = update.message.from_user.first_name
                # spawn a keyboard with the customised text 
                kb = [[KeyboardButton(item+' +Ice')],[KeyboardButton(item+' +No Ice')]]
                context.bot.send_message(chat_id=update.message.chat_id, text=name + ' is finishing an item..', 
                                     reply_to_message_id=update.message.message_id,
                                     reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, selective=True))
            
            # completion stage
            elif re.search('[+]', update.message.text):
                print("%s finished order: %s" % (update.message.from_user.first_name, update.message.text))
                self.orders.append(update.message.text)
    
    def closeOrder(self, update, context):
        if self.nowOrdering is True:
            self.nowOrdering = False
            context.bot.send_message(chat_id=update.message.chat_id, text='Orders closed.')
            # deliver the order list
            uniqueItems = np.unique(self.orders)
            ordertext = ''
            for i in np.arange(uniqueItems.size):
                cnt = self.orders.count(uniqueItems[i])
                s = '%s   x%d' % (uniqueItems[i], cnt)
                ordertext = ordertext + s + '\n'
            context.bot.send_message(chat_id=update.message.chat_id, text=ordertext)
            
            # reset orders
            self.orders = []

        
if __name__ == '__main__':
    bot = OrderBot()
    bot.run()