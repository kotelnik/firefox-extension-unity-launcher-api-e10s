#!/usr/bin/env python3

import sys, json, struct, subprocess, os, os.path, socket, _thread, signal

import logging
from logging.handlers import RotatingFileHandler
#logging.basicConfig(filename='launcher_api_firefox_stdin.log', level=logging.DEBUG, format='%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('file_logger')
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler("launcher_api_firefox_stdin.log", maxBytes=1024*1024, backupCount=1)
formatter = logging.Formatter(fmt='%(asctime)s [%(levelname)s] {%(process)d} (%(threadName)s) %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.debug('running script')

application = "firefox"
pid_file = "/tmp/firefox_launcher_api.pid"
socket_file = "/tmp/firefox_launcher_api.sock"

# message handler
def handleMessage(msg, launcher=None, loop=None):
    #
    # handle message with COUNT
    #
    if (msg.startswith("count=")):
        try:
            count = int(msg[6:])
            if (count < 0 or count > 9999):
                logger.debug("Count has to be in range 0...9999.")
            else:
                if (count == 0):
                    #
                    # reset task manager entry (make count and progress invisible)
                    #
                    subprocess.run(["gdbus", "emit", "--session", "--object-path", "/", "--signal", "com.canonical.Unity.LauncherEntry.Update", application, "{'progress-visible': <'false'>, 'count-visible': <'false'>, 'count': <'0'>, 'progress': <'0'>}"])
                    if launcher is not None:
                        launcher.set_property("count", 0)
                        launcher.set_property("count_visible", False)
                        launcher.set_property("progress", 0.0)
                        launcher.set_property("progress_visible", False)
                        if loop is not None:
                            loop.quit()
                else:
                    #
                    # set task manager entry's 'count'
                    #
                    subprocess.run(["gdbus", "emit", "--session", "--object-path", "/", "--signal", "com.canonical.Unity.LauncherEntry.Update", application, "{'progress-visible': <'true'>, 'count-visible': <'true'>, 'count': <'%d'>}" % count])
                    if launcher is not None:
                        launcher.set_property("count", count)
                        launcher.set_property("count_visible", True)
                        launcher.set_property("progress_visible", True)
        except:
            logger.debug("Error parsing count value.")

    #
    # handle message with PROGRESS
    #
    elif (msg.startswith("progress=")):
        try:
            progress = float(msg[9:])
            if (progress < 0 or progress > 1):
                logger.debug("Progress has to be in range 0...1.")
            else:
                #
                # set task manager entry's 'progress'
                #
                subprocess.run(["gdbus", "emit", "--session", "--object-path", "/", "--signal", "com.canonical.Unity.LauncherEntry.Update", application, "{'progress-visible': <'true'>, 'progress': <'%.4f'>}" % progress])
                if launcher is not None:
                    launcher.set_property("progress", progress)
                    launcher.set_property("progress_visible", True)
        except:
            logger.debug("Error parsing progress value.")

start_server = len(sys.argv) > 1 and sys.argv[1] == 'server'

if start_server:
    logger.debug('starting server')
    first_message = sys.argv[2]
    logger.debug('first message: ' + first_message)
    # set default progress and count
    import gi
    gi.require_version('Unity', '7.0')
    from gi.repository import Unity, Gio, GObject, Dbusmenu
    loop = GObject.MainLoop()
    launcher = Unity.LauncherEntry.get_for_desktop_id("firefox.desktop")
    launcher.set_property("count", 0)
    launcher.set_property("count_visible", False)
    launcher.set_property("progress", 0.0)
    launcher.set_property("progress_visible", False)

    handleMessage(first_message, launcher)

    logger.debug('creating pid and socket file...')

    def run_listener():
        # create listener and perform message
        existing_pid = None
        with open(pid_file, 'r') as f: existing_pid = f.readline()
        if existing_pid is not None:
            try:
                os.kill(int(existing_pid), signal.SIGTERM)
            except OSError: pass
        with open(pid_file, 'w') as f: f.write(str(os.getpid()))
        try:
            os.remove(socket_file)
        except OSError: pass
        sckt = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sckt.bind(socket_file)
        sckt.listen()
        while True:
            (clientSocket, addr) = sckt.accept()
            data = clientSocket.recv(1024)
            if not data: break
            incommingMessage = data.decode()
            logger.debug('Received ' + incommingMessage)
            handleMessage(incommingMessage, launcher, loop)

    try:
        _thread.start_new_thread(run_listener, ())
    except:
        logger.debug('Error creating a thread')

    logger.debug('server started')
    loop.run()
    logger.debug('loop ended, exiting')
    sys.exit(0)

logger.debug('NOT starting server')

#
# read a message from stdin and decode it
#
rawLength = sys.stdin.buffer.read(4)
if len(rawLength) == 0:
    sys.exit(0)
messageLength = struct.unpack('@I', rawLength)[0]
message = sys.stdin.read(messageLength)
receivedMessage = json.loads(message)
logger.debug('receivedMessage: ' + receivedMessage)


if os.getenv('XDG_SESSION_DESKTOP') != 'ubuntu':
    handleMessage(receivedMessage)
    sys.exit(0)

logger.debug('Ubuntu desktop recognized')

def processExists(pid):
    try:
        os.kill(int(pid), 0)
    except OSError:
        return False
    else:
        return True

listener_running = False
if os.path.isfile(pid_file):
    logger.debug('pid file exists')
    existing_pid = ''
    with open(pid_file, 'r') as f: existing_pid = f.readline()
    logger.debug('pid from pid file: ' + existing_pid)
    pid_exists = processExists(existing_pid)
    listener_running = len(existing_pid) > 0 and pid_exists #os.path.isfile('/proc/' + existing_pid)
logger.debug('listener_running=' + str(listener_running))



def sendMessage():
    sckt = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sckt.connect(socket_file)
    sckt.send(str.encode(receivedMessage))
    sckt.close()

if listener_running:
    # send message
    sendMessage()

else:
    subprocess.Popen(args=['python3', 'launcher_api_firefox_stdin.py', 'server', receivedMessage], stdout=sys.stdout)
    logger.debug('server subprocess ended')

