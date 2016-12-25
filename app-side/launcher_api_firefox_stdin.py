#!/usr/bin/env python3

import sys, json, struct, subprocess

application = "firefox"

# read a message from stdin and decode it.
def getMessage():
    rawLength = sys.stdin.buffer.read(4)
    if len(rawLength) == 0:
        sys.exit(0)
    messageLength = struct.unpack('@I', rawLength)[0]
    message = sys.stdin.read(messageLength)
    return json.loads(message)

# listen to messages from browser indefinitely
while True:

    # get message
    receivedMessage = getMessage()

    #
    # handle message with COUNT
    #
    if (receivedMessage.startswith("count=")):
        try:
            count = int(receivedMessage[6:])
            if (count < 0 or count > 9999):
                print("Count has to be in range 0...9999.")
            else:
                if (count == 0):
                    #
                    # reset task manager entry (make count and progress invisible)
                    #
                    subprocess.run(["gdbus", "emit", "--session", "--object-path", "/", "--signal", "com.canonical.Unity.LauncherEntry.Update", application, "{'progress-visible': <'false'>, 'count-visible': <'false'>, 'count': <'0'>, 'progress': <'0'>}"])
                else:
                    #
                    # set task manager entry's 'count'
                    #
                    subprocess.run(["gdbus", "emit", "--session", "--object-path", "/", "--signal", "com.canonical.Unity.LauncherEntry.Update", application, "{'progress-visible': <'true'>, 'count-visible': <'true'>, 'count': <'%d'>}" % count])
        except:
            print("Error parsing count value.")

    #
    # handle message with PROGRESS
    #
    elif (receivedMessage.startswith("progress=")):
        try:
            progress = float(receivedMessage[9:])
            if (progress < 0 or progress > 1):
                print("Progress has to be in range 0...1.")
            else:
                #
                # set task manager entry's 'progress'
                #
                subprocess.run(["gdbus", "emit", "--session", "--object-path", "/", "--signal", "com.canonical.Unity.LauncherEntry.Update", application, "{'progress-visible': <'true'>, 'progress': <'%.4f'>}" % progress])
        except:
            print("Error parsing progress value.")

    else:
        print("Cannot handle message: ", receivedMessage)
