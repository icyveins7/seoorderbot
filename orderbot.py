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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Container for orders
        self.orders = dict()

    def _createOrderGroup(self, groupid):
        self.orders[groupid] = dict()

    def _joinOrderGroup(self, groupid, userid):
        self.orders[groupid][userid] = None

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
                text="Starting a new group order.. Tell your friends to join %d!" % (update.effective_chat.id)
            )
        
        # Otherwise tell them the order already exists
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="You already have an active order! Tell your friends to join %d!" % (update.effective_chat.id)
            )

    async def join(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Join the group based on the argument supplied
        groupid = int(context.args[0])
        if groupid in self.orders:
            # If not yet in the group then join it
            if update.effective_chat.id not in self.orders[groupid]:
                self.orders[groupid][update.effective_chat.id] = None

                # DEBUG CHECK
                print(self.orders)

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
        keyboard = [
            [
                InlineKeyboardButton("Option 1", callback_data="1"),
                InlineKeyboardButton("Option 2", callback_data="2"),
            ],
            [InlineKeyboardButton("Option 3", callback_data="3")],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)


        await update.message.reply_text(
            "What would you like to order?",
            reply_markup=reply_markup
        )

    async def button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Parses the CallbackQuery and updates the message text."""
        query = update.callback_query

        # CallbackQueries need to be answered, even if no notification to the user is needed
        # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
        await query.answer()

        await query.edit_message_text(text=f"Selected option: {query.data}")

        # await update.message.edit_reply_markup(reply_markup=self.menu[query.data])
        # Maybe this is how you edit the keyboard?

    async def close(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.orders.pop(update.effective_chat.id, None)

        print(self.orders)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Closing this group order..."
        )


class OrderBot(OrderInterface, cbi.ControlInterface, cbi.StatusInterface, cbi.BotContainer):
    pass


#%%
if __name__ == "__main__":
    bot = OrderBot.fromTokenString(sys.argv[1])
    bot.run()