from telegram.ext import Updater, CommandHandler, MessageHandler, MessageFilter, Filters, CallbackQueryHandler, CallbackContext
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
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
                     'Milo': {'Normal','Gau','Gah Dai','Dinosaur'},
                     'Homemade Lemon Tea': {'Normal'},
                     'Bandung': {'Normal'},
                     'Can/Packet': {'Coke', 'Pepsi', 'Soya Bean Milk', 'Almond Milk', 'Lemon Tea', 'Chrysanthemum Tea'}}
                     
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
        
        

        
        # dict of unique sessions tied to unique chats
        self.sessions = {}
        
    
        
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
        if update.message.chat_id not in self.sessions: self.sessions[update.message.chat_id] = Session(update.message.chat_id) 
        if self.sessions[update.message.chat_id].nowOrdering is False:
            self.sessions[update.message.chat_id].nowOrdering = True
            
            # kb = [[InlineKeyboardButton(i, callback_data=i)] for i in list(self.menu.keys())]
            
            # kb_markup = InlineKeyboardMarkup(kb)
            
            # context.bot.send_message(chat_id=update.message.chat_id, text='Please begin orders by typing "O".',
            #                          reply_markup=kb_markup)
            context.bot.send_message(chat_id=update.message.chat_id, text='Please begin orders by typing "Order".',
                                    reply_markup=ReplyKeyboardRemove())
            
        else:
            context.bot.send_message(chat_id=update.message.chat_id, text='Ongoing order; type "Order" to order.')
    
    def addToOrder(self, update, context):
        if update.message.chat_id in self.sessions and self.sessions[update.message.chat_id].nowOrdering is True: # we can do this since 'and' is a short-circuit operator
            kb = [[KeyboardButton(i)] for i in list(self.menu.keys())]
            name = update.message.from_user.first_name
            context.bot.send_message(chat_id=update.message.chat_id, text=name + ' is adding an item..', 
                                     reply_to_message_id=update.message.message_id,
                                     reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, selective=True))
    
    def editOrder(self, update, context):
        if update.message.chat_id in self.sessions and self.sessions[update.message.chat_id].nowOrdering is True:
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
                # print("%s finished order: %s" % (update.message.from_user.first_name, update.message.text))
                uid = update.message.chat_id
                item = update.message.text
                name = update.message.from_user.first_name
                self.sessions[uid].orders.append(item)
                self.sessions[uid].owner[item]=[name] if item not in self.sessions[uid].owner else self.sessions[uid].owner[item]+[name]
                context.bot.send_message(chat_id=uid, 
                                     text=name + " ordered " + item, 
                                     reply_markup=ReplyKeyboardRemove(selective=True))
                
    
    def closeOrder(self, update, context):
        if update.message.chat_id in self.sessions and self.sessions[update.message.chat_id].nowOrdering is True:
            self.sessions[update.message.chat_id].nowOrdering = False
            context.bot.send_message(chat_id=update.message.chat_id, text='Orders closed.')
            # deliver the order list
            orders = self.sessions[update.message.chat_id].orders
            owner = self.sessions[update.message.chat_id].owner
            ordertext = '<i><b>Orders Simplified</b></i> ☕️🥤\n' + ''.join(['%s x%d\n'%(item,orders.count(item)) for item in set(orders)])
            context.bot.send_message(chat_id=update.message.chat_id, text=ordertext, parse_mode='HTML')
            ownertext = '<i><b>Orders with Names</b></i> ☕️🥤\n'+ ''.join([item + ': ' +', '.join(str(n) for n in owner[item])+'\n' for item in owner])
            context.bot.send_message(chat_id=update.message.chat_id, text=ownertext, parse_mode='HTML')
            # reset orders
            self.sessions[update.message.chat_id].orders = []
            self.sessions[update.message.chat_id].owner = {}

class Session:
    def __init__(self,chat_id):
        self.orders = [] # Orders
        self.owner = {} # Owners
        self.chat_id = chat_id # Unique chat id
        self.nowOrdering = False # ordering status
        print('Session created for chat ',chat_id)

if __name__ == '__main__':
    try:
        with open("token.txt") as f:
            TOKEN = f.read()
        bot = OrderBot(TOKEN)
    except:
        bot = OrderBot()
    bot.run()