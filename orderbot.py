"""
Insert these to the BotFather for good menu command descriptions.

help - Shows a tutorial of how to use the bot.
start - Starts a group order.
join - Joins a group order. E.g. /join 123456789.
order - Adds a drink to the group order.
cancel - Cancels one of your individual drinks.
close - Closes a group order.
current - Displays the current group order.
announce - Toggles announcements in the current group chat.
"""


import common_bot_interfaces as cbi

from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import sys
import pickle

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
    lastOrderSymbol = "^" # We use this symbol in the callback data to identify the last order menu

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Container for orders
        self.orders = dict() # Lookup for group->user->list of orders
        self.activeGroup = dict() # Lookup for user->current group
        self._chatids = dict() # Lookup for user->chatid

        # Try to load announcements
        try:
            self._loadAnnouncements()
            print(self._announcements)
        except Exception as e:
            print("Couldn't load announcements, defaulting to blank dict: %s" % str(e))
            self._announcements = dict() # Lookup for group/userleader->chatid

        # Try to load saved previous orders
        try:
            self._loadLastOrders()
            print(self._lastOrders)
        except Exception as e:
            print("Couldn't load orders, defaulting to blank dict: %s" % str(e))
            self._lastOrders = dict() # Lookup for user->last order string

        self._timeout = 1800 # Default timeout in seconds

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
            filters=self.ufilts & cbi.PrivateOnlyChatFilter()
        ))
        print("Adding OrderInterface:join")
        self._app.add_handler(CommandHandler(
            "join",
            self.join,
            filters=self.ufilts & cbi.PrivateOnlyChatFilter()
        ))
        print("Adding OrderInterface:order")
        self._app.add_handler(CommandHandler(
            "order",
            self.order,
            filters=self.ufilts & cbi.PrivateOnlyChatFilter()
        ))
        print("Adding OrderInterface:button")
        self._app.add_handler(CallbackQueryHandler(self.button))
        print("Adding OrderInterface:cancel")
        self._app.add_handler(CommandHandler(
            "cancel",
            self.cancel,
            filters=self.ufilts & cbi.PrivateOnlyChatFilter()
        ))
        print("Adding OrderInterface:close")
        self._app.add_handler(CommandHandler(
            "close",
            self.close,
            filters=self.ufilts & cbi.PrivateOnlyChatFilter()
        ))
        print("Adding OrderInterface:current")
        self._app.add_handler(CommandHandler(
            "current",
            self.current,
            filters=self.ufilts & cbi.PrivateOnlyChatFilter()
        ))
        print("Adding OrderInterface:announce")
        self._app.add_handler(CommandHandler(
            "announce",
            self.announce,
            filters=self.ufilts & cbi.GroupOnlyChatFilter()
        ))
        # Admin only handlers
        print("Adding OrderInterface:reset")
        self._app.add_handler(CommandHandler(
            "reset",
            self.reset,
            filters=self.ufilts & self._adminfilter # Note that this assumes AdminInterface
        ))
        print("Adding OrderInterface:setTimeout")
        self._app.add_handler(CommandHandler(
            "timeout",
            self.setTimeout,
            filters=self.ufilts & self._adminfilter # Note that this assumes AdminInterface
        ))
        

    ###########################################
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        helpstr = "Start a group order with /start. The person who starts the order will be the leader," \
            " and is responsible for closing the order with /close at the end.\n\n" \
            "Other members of the group can join with /join. " \
            "The leader will have an ID that they can share to the other group members, which should be placed after the /join command. Use '/join 24838501' for example. \n\n" \
            "Members can then add drinks to the order with /order. To cancel drinks, use /cancel.\n\n" \
            "When everyone is done with the order, the leader can /close the order to collate the drinks.\n\n" \
            "In your group chat, you can use /announce to post updates to the group when you start or close a new group order. If you'd like to toggle this off, simply /announce again."

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=helpstr
        )

    ###########################################
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Add to the order list if not already there
        if update.effective_user.id not in self.orders:
            # Create the group order
            self._createOrderGroup(update.effective_user.id)
            # Set a timeout job
            context.job_queue.run_once(self.timeoutGroupOrder, self._timeout, data=update.effective_user.id)
            # Also join it yourself
            await self._joinOrderGroup(update, context, update.effective_user.id, update.effective_user.id, alsoSendMessage=False)
            
            # DEBUG CHECK
            print(self.orders)

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Starting a new group order.. Tell your friends to '/join %d'! Add your own order with /order." % (update.effective_chat.id)
            )

            # Announce if it's been configured by this user
            if update.effective_user.id in self._announcements:
                await context.bot.send_message(
                    chat_id=self._announcements[update.effective_user.id],
                    text="%s just started a new group order; open a chat with me and '/join %d'!" % (update.effective_user.first_name, update.effective_chat.id)
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
        
        # Check if the user has a last order saved
        if update.effective_user.id in self._lastOrders:
            # Get the last order
            lastorder = self._lastOrders[update.effective_user.id]

            await update.message.reply_text(
                "Your last order was %s, do you want it again?" % (lastorder),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("Yes", callback_data=self.lastOrderSymbol+"Yes"),
                         InlineKeyboardButton("No", callback_data=self.lastOrderSymbol+"No")]
                    ]
                )
            )

        # Otherwise by default just present the menu
        else:
            reply_markup = self._generateKeyboard()

            await update.message.reply_text(
                "What would you like to order?",
                reply_markup=reply_markup
            )

    def _generateKeyboard(self, key: str=None, subkey: str=None):
        """
        Internal method to generate the keyboard for the order interface.

        1. If no key or subkey is supplied, generate from the top-level menu
        2. If a key is supplied, generate from the submenu
        3. If a key and subkey is supplied, generate from the configuration menu
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
    
    def _addToOrder(self, userid: int, order: str):
        activeGroup = self.activeGroup[userid]
        self.orders[activeGroup][userid].append(order)
        # Also update the last order
        self._updateLastOrder(userid, order)

    async def button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Parses the CallbackQuery and updates the message text."""
        query = update.callback_query

        # CallbackQueries need to be answered, even if no notification to the user is needed
        # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
        await query.answer()

        # Did we have a last order?
        if self.lastOrderSymbol in query.data:
            # If yes, retrieve the user's last order
            if "Yes" in query.data:
                lastorder = self._lastOrders[update.effective_user.id]
                # Add to the order directly
                self._addToOrder(update.effective_user.id, lastorder)
                print(self.orders)

                await query.edit_message_text(text=f"{lastorder} has been added!")

            # Otherwise we start the menu again
            else:
                reply_markup = self._generateKeyboard()

                await query.edit_message_text(text="What would you like to order?", reply_markup=reply_markup)
                

        # Are we at the joining groups menu?
        elif self.groupSymbol in query.data:
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
            self._addToOrder(update.effective_user.id, self._prettifyOrderString(query.data))
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

        # We send the closing message to every user in the group
        for member in members:
            # Generate user-specific collation
            usercollated, _ = self._collate(self.orders[update.effective_user.id], member)

            await context.bot.send_message(
                chat_id=self._chatids[member],
                text="Closing this group order...\n%s" % (
                    usercollated
                )
            )

        # Also send to the announcement group if it is set
        if update.effective_user.id in self._announcements:
            await context.bot.send_message(
                chat_id=self._announcements[update.effective_user.id],
                text="%s has closed the group order!\n%s" % (update.effective_user.first_name, collated)
            )

        # Then close the order
        self._closeOrderGroup(update.effective_user.id)

        print(self.orders)
        print(self.activeGroup)


    def _collate(self, orders: dict, user: int=None):
        """
        Counts the unique drinks in the group order and returns the string to send to the users.
        Also returns a list of the users who are in the group, to be used to reference their chat ids later.
        """
        counter = dict()
        usercounter = dict()
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

                # If a user is specified, add it to his/her counters
                if user is not None and member == user:
                    if drink not in usercounter:
                        usercounter[drink] = 1
                    else:
                        usercounter[drink] += 1

        # Now make a nice long string for every unique drink
        collated = ""
        for drink, count in counter.items():
            usercheck = ""
            if user is not None and drink in usercounter:
                # Attach the string from usercounter
                usercheck = " (You: x%d)" % (usercounter[drink])
            
            collated += "%3dx %s%s\n" % (count, drink, usercheck)
        
        return collated, members
    
    def _closeOrderGroup(self, groupid):
        # Check if groupid is still in the dict (this would get called by the job but may have been closed by the user already)
        if groupid in self.orders:
            # Pop the active group for each of the users in the group
            for userid in self.orders[groupid]:
                self.activeGroup.pop(userid, None)

            # Then pop the group itself from orders dict
            self.orders.pop(groupid, None)

    ###########################################
    async def current(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Display orders for the user's active group with a message
        userid = update.effective_user.id
        activeGroup = self.activeGroup[userid]
        grouporders = self.orders[activeGroup]
        collated, _ = self._collate(grouporders, userid)

        if len(collated) > 0:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=collated
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="There are no drink orders yet in this group."
            )

    ###########################################
    async def announce(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Turn off the announcements if the current group is currently set for announcements for this user
        if update.effective_user.id in self._announcements and self._announcements[update.effective_user.id] == update.effective_chat.id:
            self._announcements.pop(update.effective_user.id)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Okay %s, I've turned off your announcements in this group." % (update.effective_user.first_name)
            )

        # Otherwise if it's currently set to another group, or no group yet, then
        else:
            # Set the chat id to announce the group order to
            self._announcements[update.effective_user.id] = update.effective_chat.id

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Okay %s, I'll announce here if you start or close a group order." % (update.effective_user.first_name)
            )

        # Save the announcements
        self._saveAnnouncements()

    def _saveAnnouncements(self):
        with open('announcements.pkl', 'wb') as fp:
            pickle.dump(self._announcements, fp)

    def _loadAnnouncements(self):
        with open('announcements.pkl', 'rb') as fp:
            self._announcements = pickle.load(fp)

    ###########################################
    def _updateLastOrder(self, userid: int, order: str):
        self._lastOrders[userid] = order
        # Save it
        self._saveLastOrders()

    def _saveLastOrders(self):
        with open('lastorders.pkl', 'wb') as fp:
            pickle.dump(self._lastOrders, fp)

    def _loadLastOrders(self):
        with open('lastorders.pkl', 'rb') as fp:
            self._lastOrders = pickle.load(fp)

    ################## Admin commands ##################
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

    async def setTimeout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Command to either view current timeout or set a new timeout.
        """
        if len(context.args) == 0:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Timeout is currently set to %d seconds." % (self._timeout)
            )
            return

        # Set a new timeout
        self._timeout = int(context.args[0])

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Timeout set to {self._timeout} seconds."
        )

    async def timeoutGroupOrder(self, context: ContextTypes.DEFAULT_TYPE):
        """
        Job to timeout the active group order.
        """
        job = context.job
        self._closeOrderGroup(job.data)

        print("Timed out the active group order %d..." % (job.data))


# Note that OrderInterface must be the first inheritance
class OrderBot(OrderInterface, cbi.GitInterface, cbi.ControlInterface, cbi.StatusInterface, cbi.BotContainer):
    pass


#%%
if __name__ == "__main__":
    bot = OrderBot.fromTokenString(sys.argv[1])
    bot.setAdmin(int(sys.argv[2]))
    bot.run()