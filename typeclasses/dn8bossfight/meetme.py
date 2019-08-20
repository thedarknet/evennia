import random
from commands.command import Command
from evennia import CmdSet
from evennia.utils import create, search
from twisted.internet import reactor
from typeclasses.characters import Character
from typeclasses.objects import Object
from typeclasses.rooms import Room, Zone
from typeclasses.scripts import Script

def debug(msg):
    search.objects("loki")[0].msg(msg)
    # pass
def say_soon(location, msg):
    def say(location, msg):
        location.msg_contents(msg)
    reactor.callLater(0, say, location, msg)

def getroom(x,y):
    zone = search.objects('ZoneDN8BossFight', typeclass=Zone)[0]

    # debug("searching for room (%d,%d)" % (x,y))
    for obj in zone.contents:
        try:
            if obj.is_typeclass(Room, exact=False) and obj.db.coordinates is not None and obj.db.coordinates[0] == x and obj.db.coordinates[1] == y:
                return obj
        except Exception as err:
            debug("error searching for room (%d,%d): %s" % (x,y,str(err)))
            return None
    debug("room with coordinates (%d,%d) not found"%(x,y))
    return None

class CmdDisconnectDataLink(Command):
    key = "disconnect"
    def func(self):
        link = self.caller.location.search(self.args)
        if link is not None and link.is_typeclass(DataLink):
            self.caller.msg("Disconnecting data link to %s"%self.args)
            if link == search.objects("dn8bossfight#march_hare_data_link")[0]:
                search.channels("Public")[0].msg("|rMarch Hare Data Link disconnected. Cyberez Control Environment terminating.")
                self.terminate_bossfight()
                search.objects("dn8bossfight#march_hare_data_link")[0].delete()
            elif link == search.objects("dn8bossfight#daemon_data_link")[0]:
                search.channels("Public")[0].msg("|rDaemon Data Link disconnected. March Hare-Daemon connection broken. Message Code: B3DD072FD962EAAF3090D66CC46AC708DD819D534AD7062213A9CFCD01FF1DCF")
                search.objects("dn8bossfight#daemon_data_link")[0].delete()
        else:
            self.caller.msg("%s not found"%self.args)

    def terminate_bossfight(self):
        zone = search.objects('ZoneDN8BossFight', typeclass=Zone)[0]
        limbo = search.objects('Limbo', typeclass=Room)[0]
        for obj in limbo.exits:
            if obj.destination.location == zone:
                debug("deleting exit to bossfightzone: "+str(obj))
                obj.delete()
        for room in zone.contents:
            for obj in room.contents:
                if obj.is_typeclass(Character, exact=False):
                    debug("moving character out of bossfightzone: "+str(obj))
                    obj.move_to(limbo)
        


class DataLinkCmdSet(CmdSet):
    def at_cmdset_creation(self):
        super(DataLinkCmdSet, self).at_cmdset_creation()
        self.add(CmdDisconnectDataLink)

class DataLink(Object):
    pass
    # def at_object_creation(self):
    #     self.cmdset.add(DataLinkCmdSet, permanent=True)