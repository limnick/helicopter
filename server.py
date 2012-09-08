import sys, random, json

from twisted.internet import reactor
from twisted.python import log

from autobahn.websocket import WebSocketServerFactory, \
                               WebSocketServerProtocol, \
                               listenWS


#TODO: save all positions and random values to reconstruct the map and player paths
#TODO: build tool to viz the full map and all player paths (possibly as a heatmap)

class BroadcastServerProtocol(WebSocketServerProtocol):

   def onOpen(self):
      self.factory.register(self)
      self.factory.broadcast()

   def onMessage(self, msg, binary):
      if not binary:
         loc,state = json.loads(msg)
         self.factory.updateloc(float(loc), self.peerstr)
         self.factory.updatestate(state, self.peerstr)
         #self.factory.serverstep()
         #self.factory.broadcast(msg, self.peerstr)
         #self.factory.broadcast()

   def connectionLost(self, reason):
      WebSocketServerProtocol.connectionLost(self, reason)
      try:
          del self.factory.posdict[self.peerstr]
      except KeyError:
          pass
      try:
          del self.factory.statedict[self.peerstr]
      except KeyError:
          pass
      self.factory.unregister(self)

class BroadcastPreparedServerFactory(WebSocketServerFactory):
   """
   Functionally same as above, but optimized broadcast using
   prepareMessage and sendPreparedMessage.
   """

   def __init__(self, url, debug = False, debugCodePaths = False):
      WebSocketServerFactory.__init__(self, url, debug = debug, debugCodePaths = debugCodePaths)
      self.clients = []
      self.posdict = {}
      self.statedict = {}
      self.randvals = []
      self.tickcount = 0
      self.allready = True
      self.tick()

   def tick(self):
      self.tickcount += 1
      self.randvals = [random.random() for i in range(10)]
      
      #when all clients are dead, set allready to True
      self.allready = not reduce(lambda x,y:x or y, self.statedict.values() or [0])
      
      #TODO: dead players should have camera locked on the remaining players
      #TODO: add countdown to new game start
      self.broadcast()
      
      reactor.callLater(0.1, self.tick)

   def register(self, client):
      if not client in self.clients:
         print "registered client " + client.peerstr
         self.clients.append(client)

   def unregister(self, client):
      if client in self.clients:
         print "unregistered client " + client.peerstr
         self.clients.remove(client)

   def updateloc(self, msg, peer):
      self.posdict[peer] = msg
      
      
   def updatestate(self, state, peer):
      self.statedict[peer] = state

   def broadcast(self):
      msg = json.dumps((self.tickcount, self.randvals, self.posdict.values(), self.allready))
      preparedMsg = self.prepareMessage(msg)
      for c in self.clients:
         c.sendPreparedMessage(preparedMsg)
         print "prepared message sent to " + c.peerstr


if __name__ == '__main__':

   if len(sys.argv) > 1 and sys.argv[1] == 'debug':
      log.startLogging(sys.stdout)
      debug = True
   else:
      debug = False

   factory = BroadcastPreparedServerFactory("ws://0.0.0.0:9000",
                           debug = debug,
                           debugCodePaths = debug)

   factory.protocol = BroadcastServerProtocol
   factory.setProtocolOptions(allowHixie76 = True)
   listenWS(factory)

   reactor.run()