#!/usr/bin/python3

import argparse
import subprocess
import time
import liblo
import fcntl
import os
import select
import shlex
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkX11

class oscbridge(liblo.ServerThread):
    def __init__(self, windowId, window, universe, channel, port, fifo, folder, extraArgs):
        super().__init__(port)

        self.__fifoname = fifo
        self.window = window
        
        os.mkfifo(self.__fifoname)
        cmd = [
            'mplayer',
            '-ao', 'pulse,alsa,',
            '-fixed-vo',
            '-idle',
            '-slave',
            '-input', 'file=%s' % (self.__fifoname),
            '-volume', '0',
            '-wid', '%s' % windowId,
        ]
        if extraArgs is not None:
            cmd += extraArgs
        print("Opening mplayer")
        #self.__proc = subprocess.Popen(shlex.split("mplayer -idle -slave -input file=%s -volume 0 -wid %s" % (self.__fifoname, windowId)))
        self.__proc = subprocess.Popen(cmd)
        print(self.__proc.args)
        self.__fifo = open(self.__fifoname, 'w')
        self.__fifo.flush()
     
        self.add_method("/%i/dmx/%i"%(universe,channel), 'f', self.cb_index)
        self.add_method("/%i/dmx/%i"%(universe,channel+1), 'f', self.cb_play)
        self.add_method("/%i/dmx/%i"%(universe,channel+2), 'f', self.cb_next)
        self.add_method("/%i/dmx/%i"%(universe,channel+3), 'f', self.cb_prev)
        self.add_method("/%i/dmx/%i"%(universe,channel+4), 'f', self.cb_volume)
        self.add_method("/%i/dmx/%i"%(universe,channel+5), 'f', self.cb_fullscreen)
        #self.add_method("/%i/dmx/%i"%(universe,channel+6), 'f', self.cb_brightness)
        #self.add_method("/%i/dmx/%i"%(universe,channel+7), 'f', self.cb_contrast)
        #self.add_method("/%i/dmx/%i"%(universe,channel+8), 'f', self.cb_gamma)
        #self.add_method("/%i/dmx/%i"%(universe,channel+9), 'f', self.cb_hue)
        #self.add_method("/%i/dmx/%i"%(universe,channel+10), 'f', self.cb_saturation)

        self.add_method(None, None, self.osc_fallback)
        
        self.files = list()
        self.set_playback_folder(folder)

        self.playing = False
        self.brightness = 0
        self.contrast = 0
        self.gamma = 0
        self.volume = 0
        self.hue = 0
        self.saturation = 0
        self.osd = 0
        self.index = 0

        
    def __del__(self):
        os.remove(self.__fifoname)

    def set_playback_folder(self, folder):
        print("Loading folder: %s" % folder)
        if (folder):
            for i in os.listdir(folder):
                if os.path.isfile(os.path.join(folder,i)):
                    self.files.append(os.path.join(folder,i))
        self.files = sorted(self.files)
        
        print(self.files)

    def __loadfile(self, index):
        print("request loading file: %s" % index)
        self.index = max(min(index, len(self.files)-1), 0)
        if len(self.files) is 0:
            print ("no files loaded")
            return

        print("loading file: %s / %s" % (self.index, len(self.files) - 1))
        self.__tomplayer('pausing_keep loadfile "%s"' % (self.files[self.index]))

    def __tomplayer(self, msg):
        m = '%s\n' % (msg)
        print(m)
        self.__fifo.write(m)
        self.__fifo.flush()    
        
    def stop(self):
        super().stop()

    def quit(self):
        self.__tomplayer('quit\n')
        self.__fifo.close()
        self.__fife = None
        self.__proc.terminate()
        self.__proc = None

    def cb_play(self, path, args):
        print("%s:%s %s" % (path, 'cb_play', args))
        if args[0] == 1.0:            
            self.__tomplayer("pausing_toggle set_property pause 0")
        else:                 
            self.__tomplayer("pausing_keep_force set_property pause 1")

    def cb_next(self, path, args):
        print("%s:%s %s" % (path, 'cb_next', args))
        self.__loadfile(self.index+1)
            
    def cb_prev(self, path, args):
        print("%s:%s %s" % (path, 'cb_prev', args))
        self.__loadfile(self.index-1)
            
    def cb_index(self, path, args):
        print("%s:%s %s" % (path, 'cb_index', args))
        self.__loadfile(round(args[0] * 255))
        
    def cb_brightness(self, path, args):
        print("%s:%s %s" % (path, 'cb_brightness', args))
        self.brightness = int(round(args[0]*200)-100)
        self.__tomplayer('set_property brightness %d'%(self.brightness))

    def cb_contrast(self, path, args):
        print("%s:%s %s" % (path, 'cb_contrast', args))
        self.contrast = int(round(args[0]*200)-100)
        self.__tomplayer('set_property contrast %d'%(self.contrast))

    def cb_gamma(self, path, args):
        print("%s:%s %s" % (path, 'cb_gamma', args))
        self.gamma = int(round(args[0]*200)-100)
        self.__tomplayer('set_property gamma %d'%(self.gamma))

    def cb_hue(self, path, args):
        print("%s:%s %s" % (path, 'cb_hue', args))
        self.hue = int(round(args[0]*200)-100)
        self.__tomplayer('set_property hue %d'%(self.hue))

    def cb_saturation(self, path, args):
        print("%s:%s %s" % (path, 'cb_saturation', args))
        self.saturation = int(round(args[0]*200)-100)
        self.__tomplayer('set_property saturation %d'%(self.saturation))

    def cb_volume(self, path, args):
        print("%s:%s %s" % (path, 'cb_volume', args))
        self.volume = int(round(args[0]*100))
        self.__tomplayer('set_property volume %d'%(self.volume))
     
         
    def cb_fullscreen(self, path, args):
        print("%s:%s %s" % (path, 'cb_fullscreen', args))
        if args[0] > 0.5:
            self.window.fullscreen()
        else:
            self.window.unfullscreen()

    def osc_fallback(self, path, args):
        print ("oscbridge: received unknown message", path, args)

class Application():

    def __init__(self, args):
        self.args = args
        
        win = Gtk.Window()
        win.resize(400, 400)
        win.connect('delete-event', self.on_quit)

        da = Gtk.DrawingArea()
        win.add(da)

        self.window = win
        self.drawingArea = da
        self.started = False
        self.oscbridge = None

    def run(self):
        self.window.show_all()
        #self.window.fullscreen()
        self.start_mplayer()
        Gtk.main()
                
    def start_mplayer(self):
        try:
            uni = self.args.universe-1
            port = self.args.port
            chan = self.args.channel-1
            mplfifo = self.args.fifo
            ext = self.args.extraArgs
            windowId = self.drawingArea.get_property('window').get_xid()
            print("windowId:%s" % windowId)
            self.oscbridge = oscbridge(windowId, self.window, uni, chan, port, mplfifo, args.folder, ext)
            self.oscbridge.start()
            print("embedmplayer: connected") 
        except liblo.ServerError as err:
            print("embedmplayer: ServerError: {0}".format(err))
        except OSError as err:
            print("embedmplayer: OSERROR: {0}".format(err))
        
    def on_quit(self, widget, data=None):
        if (self.oscbridge):
            self.oscbridge.quit()
            self.oscbridge.stop()                
        Gtk.main_quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Bridge program for controlling mplayer via slave mode from QLCPlus via the OSC plug in")
    parser.add_argument('--universe', action="store", default=1, type=int)
    parser.add_argument('--port', action="store", default=9000, type=int)
    parser.add_argument('--channel', action="store", default=1, type=int)
    parser.add_argument('--fifo', action="store", default="/tmp/mplayer.fifo")
    parser.add_argument('--extraArgs', action="store", nargs=argparse.REMAINDER)
    parser.add_argument('--folder', action="store")

    args = parser.parse_args()  
    application = Application(args)
    application.run()
