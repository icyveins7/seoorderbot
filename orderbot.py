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
    submenuSymbol = "~" # We use this symbol in the callback data to identify the submenu.
    configureDrink = ["Iced", "No Ice", "Hot"] # Generic configurations of drinks which apply to everything, last step of the order
    configureSymbol = "!" # We use this symbol in the callback data to identify the configure menu, which is the end of the order

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Container for orders
        self.orders = dict() # Lookup for group->user->list of orders
        self.activeGroup = dict() # Lookup for user->current group

    def _createOrderGroup(self, groupid):
        self.orders[groupid] = dict()

    def _joinOrderGroup(self, groupid, userid):
        self.orders[groupid][userid] = list()
        self.activeGroup[userid] = groupid

    def _addInterfaceHandlers(self):
        super()._addInterfaceHandlers()
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
        print("Adding OrderInterface:close")
        self._app.add_handler(CommandHandler(
            "close",
            self.close,
            filters=self.ufilts
        ))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Add to the order list if not already there
        if update.effective_user.id not in self.orders:
            # Create the group order
            self._createOrderGroup(update.effective_user.id)
            # Also join it yourself
            self._joinOrderGroup(update.effective_user.id, update.effective_user.id)
            
            # DEBUG CHECK
            print(self.orders)

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Starting a new group order.. Tell your friends to /join %d! Add your own order with /order." % (update.effective_chat.id)
            )
        
        # Otherwise tell them the order already exists
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="You already have an active order! Tell your friends to /join %d! Add your own order with /order." % (update.effective_chat.id)
            )

    async def join(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Join the group based on the argument supplied
        groupid = int(context.args[0])
        if groupid in self.orders:
            # If not yet in the group then join it
            if update.effective_user.id not in self.orders[groupid]:
                self._joinOrderGroup(groupid, update.effective_user.id)

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="You have joined group %d. Add your order with /order." % (groupid)
                )
            # Otherwise tell them they are already in the group
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="You are already in group %d!" % (groupid)
                )

        # Error if the group doesn't exist
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Group %d does not exist!" % (groupid)
            )

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

        # Are we at the configure menu?
        if self.configureSymbol in query.data:
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

    async def close(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Collate the orders
        collated = self._collate(self.orders[update.effective_user.id])

        # Then pop the order
        self.orders.pop(update.effective_user.id, None)

        print(self.orders)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Closing this group order...\n%s" % (
                collated
            )
        )

    def _collate(self, orders: dict):
        return "EMPTY"
    
    def _closeOrderGroup(self, groupid):
        # Pop the active group for each of the users in the group
        for userid in self.orders[groupid]:
            self.activeGroup.pop(userid, None)

        # Then pop the group itself from orders dictd
        self.orders.pop(groupid, None)


class OrderBot(OrderInterface, cbi.ControlInterface, cbi.StatusInterface, cbi.BotContainer):
    pass


#%%
if __name__ == "__main__":
    bot = OrderBot.fromTokenString(sys.argv[1])
    bot.run()