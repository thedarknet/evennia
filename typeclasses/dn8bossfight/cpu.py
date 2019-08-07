from typeclasses.rooms import Room, Zone
from typeclasses.objects import Object
from twisted.internet import reactor

def debug(msg):
    # search.objects("loki")[0].msg(msg)
    pass
def say_soon(location, msg):
    def say(location, msg):
        location.msg_contents(msg)
    reactor.callLater(0, say, location, msg)

class Mainframe(Room):
    pass

class CPU(Object):
    pass