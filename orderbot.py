import common_bot_interfaces as cbi

from telegram.ext import CommandHandler, ContextTypes
from telegram import Update
import sys

#%%
class OrderInterface:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _addInterfaceHandlers(self):
        super()._addInterfaceHandlers()
        print("Adding OrderInterface:start")
        self._app.add_handler(CommandHandler(
            "start",
            self.start
        ))
        print("Adding OrderInterface:order")
        self._app.add_handler(CommandHandler(
            "order",
            self.order
        ))
        print("Adding OrderInterface:stop")
        self._app.add_handler(CommandHandler(
            "stop",
            self.stop
        ))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass

    async def order(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass

    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass # TODO: complete


class OrderBot(cbi.ControlInterface, cbi.StatusInterface, cbi.BotContainer):
    pass


#%%
if __name__ == "__main__":
    print(sys.argv)
    bot = OrderBot.fromTokenString(sys.argv[1])
    bot.run()