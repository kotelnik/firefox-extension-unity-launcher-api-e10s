#!/usr/bin/env python3

import sys, json, struct, subprocess

application = 'firefox'

# debug logging - TODO remove!!!
import logging
from logging.handlers import RotatingFileHandler
#logging.basicConfig(filename='launcher_api_firefox_stdin.log', level=logging.DEBUG, format='%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('file_logger')
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler("launcher_api_firefox_stdin.log", maxBytes=1024*1024, backupCount=1)
formatter = logging.Formatter(fmt='%(asctime)s [%(levelname)s] {%(process)d} (%(threadName)s) %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)
# debug logging - TODO remove!!!

# try libunity
launcher = None
try:
    import gi
    gi.require_version('Unity', '7.0')
    from gi.repository import Unity, Gio, GObject, Dbusmenu
    loop = GObject.MainLoop()
    launcher = Unity.LauncherEntry.get_for_desktop_id("firefox.desktop")
    launcher.set_property('count', 0)
    launcher.set_property('count_visible', False)
    launcher.set_property('progress', 0.0)
    launcher.set_property('progress_visible', False)
    try:
        _thread.start_new_thread(loop.run, ())
    except:
        logger.debug('Error creating a thread')
except:
    logger.debug('libunity not found')

# read a message from stdin and decode it.
def readMessage():
    rawLength = sys.stdin.buffer.read(4)
    if len(rawLength) == 0:
        logger.debug('length is empty, exiting')
        sys.exit(0)
    messageLength = struct.unpack('@I', rawLength)[0]
    message = sys.stdin.read(messageLength)
    receivedMessage = json.loads(message)
    logger.debug('receivedMessage: ' + receivedMessage)
    return receivedMessage


def processMessage(receivedMessage):

    splitted = receivedMessage.split('|')
    countMessage = splitted[0]
    progressMessage = splitted[1]

    #
    # handle message with COUNT
    #
    try:
        count = int(countMessage[6:])
        if (count < 0 or count > 9999):
            logger.debug("Count has to be in range 0...9999.")
        else:
            if (count == 0):
                #
                # reset task manager entry (make count and progress invisible)
                #
                if launcher is not None:
                    launcher.set_property('count', 0)
                    launcher.set_property('count_visible', False)
                    launcher.set_property('progress', 0.0)
                    launcher.set_property('progress_visible', False)
                else:
                    subprocess.run(["gdbus", "emit", "--session", "--object-path", "/", "--signal", "com.canonical.Unity.LauncherEntry.Update", application, "{'progress-visible': <'false'>, 'count-visible': <'false'>, 'count': <'0'>, 'progress': <'0'>}"])
                return
            else:
                #
                # set task manager entry's 'count'
                #
                if launcher is not None:
                    launcher.set_property('count', count)
                    launcher.set_property('count_visible', True)
                else:
                    subprocess.run(["gdbus", "emit", "--session", "--object-path", "/", "--signal", "com.canonical.Unity.LauncherEntry.Update", application, "{'progress-visible': <'true'>, 'count-visible': <'true'>, 'count': <'%d'>}" % count])
    except:
        logger.debug("Error parsing count value.")

    #
    # handle message with PROGRESS
    #
    try:
        progress = float(progressMessage[9:])
        if (progress < 0 or progress > 1):
            logger.debug("Progress has to be in range 0...1.")
        else:
            #
            # set task manager entry's 'progress'
            #
            if launcher is not None:
                launcher.set_property('progress', progress)
                launcher.set_property('progress_visible', True)
            else:
                subprocess.run(["gdbus", "emit", "--session", "--object-path", "/", "--signal", "com.canonical.Unity.LauncherEntry.Update", application, "{'progress-visible': <'true'>, 'progress': <'%.4f'>}" % progress])
    except:
        logger.debug("Error parsing progress value.")


while True:
    receivedMessage = readMessage()
    processMessage(receivedMessage)
