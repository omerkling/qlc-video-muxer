#!/usr/bin/python3

import argparse
import asyncio
import liblo
import websockets


   
        

class oscbridge(liblo.ServerThread):
    def __init__(self, websocket, universe, channel, port):
        super().__init__(port)
        
        self.loop = None

        print("Creating OSC Bridge")
            
        self.websocket = websocket
        self.add_method("/%i/dmx/%i"%(universe,channel), 'f', self.cb_index)
        self.add_method("/%i/dmx/%i"%(universe,channel+1), 'f', self.cb_next)
        self.add_method("/%i/dmx/%i"%(universe,channel+2), 'f', self.cb_prev)
        self.add_method("/%i/dmx/%i"%(universe,channel+3), 'f', self.cb_reset)

        self.add_method(None, None, self.osc_fallback)
        
    def __del__(self):
        print ("Destroying OSC Bridge")
   
    def __toclients(self, msg):
        if self.loop is None:
            self.loop = asyncio.new_event_loop()
        async def sendmsg():
            print("> {}".format(msg))
            try:
                await self.websocket.send(msg)
            except:
                print("Exception sending message")
        self.loop.run_until_complete(sendmsg())                
                
    def stop(self):
        super().stop()

    def cb_next(self, path, args):
        print("%s:%s %s" % (path, 'cb_next', args))
        if args[0] == 1:
            self.__toclients("goto:next")
            
    def cb_prev(self, path, args):
        print("%s:%s %s" % (path, 'cb_prev', args))
        if args[0] == 1:
            self.__toclients("goto:prev")
            
    def cb_index(self, path, args):
        print("%s:%s %s" % (path, 'cb_index', args))
        self.__toclients("goto:%d" % round(args[0] * 255))
        
    def cb_reset(self, path, args):
        print("%s:%s %s" % (path, 'cb_reset', args))
        if args[0] == 1:
            self.__toclients("goto:0")
        
    def osc_fallback(self, path, args):
        print ("oscbridge: received unknown message", path, args)

class Application():
    def __init__(self, args):
        self.args = args
        
        self.started = False
        self.oscbridge = None

    async def run(self):
        uni = self.args.universe-1
        port = self.args.port
        chan = self.args.channel-1
        server = self.args.server        
        async with websockets.connect(server) as websocket:
            print("Created websocket")
            self.oscbridge = oscbridge(websocket, uni, chan, port)            
            self.oscbridge.start()
            try:
                while True:
                    msg = await websocket.recv();
                    print("< {}".format(msg))                
            finally:
                print("Connection closed")
                self.oscbridge.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Bridge program for controlling mplayer via slave mode from QLCPlus via the OSC plug in")
    parser.add_argument('--universe', action="store", default=1, type=int)
    parser.add_argument('--port', action="store", default=9000, type=int)
    parser.add_argument('--channel', action="store", default=1, type=int)
    parser.add_argument('--server', action="store", default="ws://localhost:8765")

    args = parser.parse_args()  
    application = Application(args)
    asyncio.get_event_loop().run_until_complete(application.run())
