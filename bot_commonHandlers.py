# -*- coding: utf-8 -*-
"""
Created on Thu Nov 26 11:28:16 2020

@author: Seo
"""


from telegram.ext import Updater, Filters
import os
import ntpath
import pytz
import datetime as dt
import subprocess
import zipfile

#%%
fileDir = ntpath.split(os.path.realpath(__file__))[0]

#%%
sgtz = pytz.timezone('Singapore')

time_bot_started = dt.datetime.now()
time_bot_started = sgtz.localize(time_bot_started) # this is the correct way

#%%
def getLocalizedTimeNow():
    return sgtz.localize(dt.datetime.now())

def checkCommandIsOld(message):
    print('Datetime message was received was '+str(message.date))
    print('Bot started at ' + str(time_bot_started))
    print('%20s : %s' % ('Message time', str(message.date.timestamp())))
    print('%20s : %s' % ('Bot start time', str(time_bot_started.timestamp())))

    if message.date.timestamp() <= time_bot_started.timestamp():
        print('old msg')
        return True
    else:
        print('new msg')
        return False

#%%
def status(update, context):
    if not checkCommandIsOld(update.message):
        timeNow = getLocalizedTimeNow()
        context.bot.send_message(chat_id=update.message.chat_id,
                         text='This bot was started at '+str(time_bot_started)+' and has been alive for '+str(timeNow-time_bot_started))

#%%
def stopBot(update, context):
    if not checkCommandIsOld(update.message):
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text='Ending this bot.')
        print("Ending the bot.")
        # os.kill(os.getpid(), signal.SIGINT)
        # threading.Thread(target=botShutdown).start()
        botShutdown()
        
        
def botShutdown():
    os._exit(0) # hardcore? but always works 
    # updater.stop()
    # updater.is_idle = False

#%%
def restartBot(command, timeout=10):
    command = "start python botRestart.py seopibot_main.py"
    print(command)
    os.system(command) # we start the restart protocol
    botShutdown() # then shutdown
    
#%%
def runScriptToFile(script, file):
    with open(file,"w+") as fid:
        subprocess.call(["python", script], stdout=fid)
    
def runScriptAndSendFile(update, context):
    if not checkCommandIsOld(update.message):
        context.bot.send_message(chat_id=update.message.chat_id,
                         text='Please wait while we run the script..')
        
        script = context.args[0]
        file = context.args[1]
        runScriptToFile(script,file)
        
        context.bot.sendDocument(chat_id=update.message.chat_id, document=open(file, 'rb'))
        
        # clear the file
        os.remove(file)

#%% file management
def zipFiles(filepaths, zipfilepath, cl=9):
    '''Compression levels 0 (no compression) to 9 (max compression)'''
    z = zipfile.ZipFile(zipfilepath,'w', compression=zipfile.ZIP_DEFLATED, compresslevel=cl)
    
    for fp in filepaths:
        z.write(fp)
    
    z.close()
    
    
#%%
def downloader(update, context):
    origName = update.message.document.file_name
    
    path2save = os.path.join(ntpath.split(os.path.realpath(__file__))[0], origName)
    with open(path2save, 'wb') as f:
        context.bot.get_file(update.message.document).download(out=f)
        
    print('Saved to ' + path2save)
    context.bot.send_message(chat_id=update.message.chat_id,
                         text='Downloaded file ' + origName)



