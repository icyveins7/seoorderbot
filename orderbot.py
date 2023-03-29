"""
Insert these to the BotFather for good menu command descriptions.

help - Shows a tutorial of how to use the bot.
start - Starts a group order.
join - Joins a group order. E.g. /join 123456789.
order - Adds a drink to the group order.
cancel - Cancels one of your individual drinks.
close - Closes a group order.
"""


import common_bot_interfaces as cbi

from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import sys

#%%
class OrderInterface:
    menu = {
        'Kopi': {'Normal', 'Siew Dai', 'Gau', 'Gah Dai', 'Po'},
        'Kopi-O': {'Normal', 'Siew Dai', 'Gau', 'Kosong', 'Po', 'Kosong Di Lo'},
        'Kopi-C': {'Normal', 'Siew Dai', 'Gau', 'Gah Dai', 'Po'},
        'Teh': {'Normal', 'Siew Dai', 'Gau', 'Gah Dai', 'Po'}, 
        'Teh-O': {'Normal', 'Siew Dai', 'Gau', 'Kosong', 'Po', 'Kosong Di Lo'},
        'Teh-C': {'Normal', 'Siew Dai', 'Gau', 'Gah Dai', 'Po'},
        'Milo': {'Normal','Gau','Gah Dai','Dinosaur'},
        'Homemade Lemon Tea': {'Normal'},
        'Bandung': {'Normal'},
        'Can/Packet': {'Coke', 'Pepsi', 'Sprite', 'Soya Bean Milk', 'Almond Milk', 'Lemon Tea', 'Chrysanthemum Tea'}
    }
    groupSymbol = "#" # Use this symbol to denote the keyboard for joining groups.
    submenuSymbol = "~" # We use this symbol in the callback data to identify the submenu.
    configureDrink = ["Iced", "No Ice", "Hot"] # Generic configurations of drinks which apply to everything, last step of the order
    configureSymbol = "!" # We use this symbol in the callback data to identify the configure menu, which is the end of the order
    cancelSymbol = "@" # We use this symbol in the callback data to identify the cancel menu

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Container for orders
        self.orders = dict() # Lookup for group->user->list of orders
        self.activeGroup = dict() # Lookup for user->current group
        self._chatids = dict() # Lookup for user->chatid

    def _addInterfaceHandlers(self):
        super()._addInterfaceHandlers()
        print("Adding OrderInterface:help")
        self._app.add_handler(CommandHandler(
            "help",
            self.help,
            filters=self.ufilts
        ))
        print("Adding OrderInterface:start")
        self._app.add_handler(CommandHandler(
            "start",
            self.start,
            filters=self.ufilts
        ))
        print("Adding OrderInterface:join")
        self._app.add_handler(CommandHandler(
            "join",
            self.join,
            filters=self.ufilts
        ))
        print("Adding OrderInterface:order")
        self._app.add_handler(CommandHandler(
            "order",
            self.order,
            filters=self.ufilts
        ))
        print("Adding OrderInterface:button")
        self._app.add_handler(CallbackQueryHandler(self.button))
        print("Adding OrderInterface:cancel")
        self._app.add_handler(CommandHandler(
            "cancel",
            self.cancel,
            filters=self.ufilts
        ))
        print("Adding OrderInterface:close")
        self._app.add_handler(CommandHandler(
            "close",
            self.close,
            filters=self.ufilts
        ))
        # Admin only handlers
        print("Adding OrderInterface:reset")
        self._app.add_handler(CommandHandler(
            "reset",
            self.reset,
            filters=self.ufilts & self._adminfilter # Note that this assumes AdminInterface
        ))

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        helpstr = "Start a group order with /start. The person who starts the order will be the leader," \
            " and is responsible for closing the order with /close at the end.\n\n" \
            "Other members of the group can join with /join. " \
            "The leader will have an ID that they can share to the other group members, which should be placed after the /join command. Use '/join 24838501' for example. \n\n" \
            "Members can then add drinks to the order with /order. To cancel drinks, use /cancel.\n\n" \
            "When everyone is done with the order, the leader can /close the order to collate the drinks."

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=helpstr
        )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Add to the order list if not already there
        if update.effective_user.id not in self.orders:
            # Create the group order
            self._createOrderGroup(update.effective_user.id)
            # Also join it yourself
            await self._joinOrderGroup(update, context, update.effective_user.id, update.effective_user.id, alsoSendMessage=False)
            
            # DEBUG CHECK
            print(self.orders)

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Starting a new group order.. Tell your friends to '/join %d'! Add your own order with /order." % (update.effective_chat.id)
            )
        
        # Otherwise tell them the order already exists
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="You already have an active order! Tell your friends to '/join %d'! Add your own order with /order." % (update.effective_chat.id)
            )

    def _createOrderGroup(self, groupid):
        self.orders[groupid] = dict()

    ###########################################
    async def join(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # If no group id is supplied, show available groups as an inline keyboard
        if len(context.args) == 0:
            keyboard = [
                [InlineKeyboardButton(group, callback_data=self.groupSymbol + str(group))]
                for group in self.orders
            ]
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Available groups:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            return

        # Join the group based on the argument supplied
        groupid = int(context.args[0])
        if groupid in self.orders:
            # If not yet in the group then join it
            if update.effective_user.id not in self.orders[groupid]:
                await self._joinOrderGroup(update, context, groupid, update.effective_user.id)

            # Otherwise tell them they are already in the group
            else:
                await self._alreadyInOrderGroup(update, context, groupid)

        # Error if the group doesn't exist
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Group %d does not exist!" % (groupid)
            )

    async def _joinOrderGroup(self, update, context, groupid, userid, alsoSendMessage=True):
        # We use this to store chat ids, not in the outer join() since group creators don't invoke that
        self._chatids[update.effective_user.id] = update.effective_chat.id

        self.orders[groupid][userid] = list()
        self.activeGroup[userid] = groupid

        if alsoSendMessage:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="You have joined group %d. Add your order with /order." % (groupid)
            )

    async def _alreadyInOrderGroup(self, update, context, groupid):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You are already in group %d!" % (groupid)
        )

    ###########################################
    async def order(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Check if the user is in a group first
        if update.effective_user.id not in self.activeGroup:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="You are not in a group! Join a group first with /join or start a group with /start."
            )
            return

        reply_markup = self._generateKeyboard()

        await update.message.reply_text(
            "What would you like to order?",
            reply_markup=reply_markup
        )

    def _generateKeyboard(self, key: str=None, subkey: str=None):
        """
        Internal method to generate the keyboard for the order interface.
        """
        keyboard = []

        # If no key supplied then generate from the top-level menu
        if key is None:
            row = []
            for key in self.menu:
                row.append(InlineKeyboardButton(key, callback_data=key))
                if len(row) == 3:
                    keyboard.append(row)
                    row = []

            if len(row) > 0:
                keyboard.append(row)

        # Otherwise we generate from the submenu
        elif subkey is None:
            row = []
            for subkey in self.menu[key]:
                row.append(InlineKeyboardButton(subkey, callback_data=key+self.submenuSymbol+subkey))
                if len(row) == 3:
                    keyboard.append(row)
                    row = []

            if len(row) > 0:
                keyboard.append(row)

        # Otherwise generate the final configuration menu
        else:
            row = []
            for config in self.configureDrink:
                row.append(
                    InlineKeyboardButton(
                        config,
                        callback_data=key+self.submenuSymbol+subkey+self.configureSymbol+config
                    )
                )
            keyboard.append(row)
            
        return InlineKeyboardMarkup(keyboard)
    
    def _prettifyOrderString(self, querydata: str):
        return querydata.replace(self.submenuSymbol, " ").replace(self.configureSymbol, ", ")

    async def button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Parses the CallbackQuery and updates the message text."""
        query = update.callback_query

        # CallbackQueries need to be answered, even if no notification to the user is needed
        # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
        await query.answer()

        # Are we at the joining groups menu?
        if self.groupSymbol in query.data:
            groupid = int(query.data[1:])
            userid = update.effective_user.id
            if userid not in self.orders[groupid]:
                # Join the group
                await self._joinOrderGroup(update, context, groupid, userid)
            else:
                # Tell them they are already in the group
                await self._alreadyInOrderGroup(update, context, groupid)

            return
        
        # Are we at the cancel menu?
        elif self.cancelSymbol in query.data:
            # Get the drink to be cancelled
            drink = query.data[1:]
            userid = update.effective_user.id
            groupid = self.activeGroup[userid]
            self.orders[groupid][userid].remove(drink)

            await query.edit_message_text(text="Drink %s has been removed." % (drink))

        # Are we at the configure menu?
        elif self.configureSymbol in query.data:
            # Complete the order
            activeGroup = self.activeGroup[update.effective_user.id]
            self.orders[activeGroup][update.effective_user.id].append(
                self._prettifyOrderString(query.data)
            )
            print(self.orders)

            await query.edit_message_text(text=f"{self._prettifyOrderString(query.data)} has been added!")

        # Are we in a submenu?
        elif self.submenuSymbol in query.data:
            # Get the key and subkey
            key, subkey = query.data.split(self.submenuSymbol)

            # Generate a configure keyboard
            reply_markup = self._generateKeyboard(key=key, subkey=subkey)

            await update.callback_query.edit_message_reply_markup(reply_markup=reply_markup)
            
        # Is this the top menu?
        else:
            # Generate the submenu keyboard
            reply_markup = self._generateKeyboard(key=query.data)

            await update.callback_query.edit_message_reply_markup(reply_markup=reply_markup)

    ###########################################
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Display all orders for the user's active group with an inline keyboard
        userid = update.effective_user.id
        activeGroup = self.activeGroup[userid]
        keyboard = [
            [InlineKeyboardButton(drink, callback_data=self.cancelSymbol + drink)]
            for drink in self.orders[activeGroup][userid]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "What would you like to cancel?",
            reply_markup=reply_markup
        )

    ###########################################
    async def close(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Check if user is in a group
        if update.effective_user.id not in self.orders:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="You don't seem to be leading any group orders."
            )
            return

        # Collate the orders
        collated, members = self._collate(self.orders[update.effective_user.id])

        # Then close the order
        self._closeOrderGroup(update.effective_user.id)

        print(self.orders)
        print(self.activeGroup)

        # We send the closing message to every user in the group
        for member in members:
            await context.bot.send_message(
                chat_id=self._chatids[member],
                text="Closing this group order...\n%s" % (
                    collated
                )
            )


    def _collate(self, orders: dict):
        """
        Counts the unique drinks in the group order and returns the string to send to the users.
        Also returns a list of the users who are in the group, to be used to reference their chat ids later.
        """
        counter = dict()
        members = []
        # Iterate over every member
        for member, drinks in orders.items():
            members.append(member)
            # Iterate over every drink
            for drink in drinks:
                # Add drink to the counter if not there
                if drink not in counter:
                    counter[drink] = 1
                # Otherwise increment the counter
                else: 
                    counter[drink] += 1

        # Now make a nice long string for every unique drink
        collated = ""
        for drink, count in counter.items():
            collated += "%3dx %s\n" % (count, drink)
        
        return collated, members
    
    def _closeOrderGroup(self, groupid):
        # Pop the active group for each of the users in the group
        for userid in self.orders[groupid]:
            self.activeGroup.pop(userid, None)

        # Then pop the group itself from orders dictd
        self.orders.pop(groupid, None)

    #%% Admin commands
    def _reset(self):
        """
        Clears the orders dictionary and the active group dictionary.
        """
        self.activeGroup.clear()
        self.orders.clear()

    async def reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._reset()

        print(self.activeGroup)
        print(self.orders)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="All orders and active groups have been reset."
        )


# Note that OrderInterface must be the first inheritance
class OrderBot(OrderInterface, cbi.AdminInterface, cbi.StatusInterface, cbi.BotContainer):
    pass


#%%
if __name__ == "__main__":
    bot = OrderBot.fromTokenString(sys.argv[1])
    bot.setAdmin(int(sys.argv[2]))
    bot.run()