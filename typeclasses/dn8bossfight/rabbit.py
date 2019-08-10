import random
from commands.command import Command
from evennia import CmdSet
from evennia.utils import create, search
from twisted.internet import reactor
from typeclasses.objects import Object
from typeclasses.rooms import Room, Zone
from typeclasses.scripts import Script

def debug(msg):
    search.objects("loki")[0].msg(msg)
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

class WhiteRabbit(Object):
    PATH = [
        (9,2), # start room
        (9,3),
        (9,4),
        (8,4),
        (7,4),
        (6,4), # dig loop
        (6,5),
        (6,6),
        (6,7),
        (5,7),
        (4,7),
        (4,6),
        (4,5), # mainframe room
    ]

    def at_object_creation(self):
        super(WhiteRabbit, self).at_object_creation()
        self.cmdset.add(WhiteRabbitCmdSet, permanent=True)
        self.db.frozen = False

    def move_callback(self):
        self.timeout = None
        if self.db.frozen:
            debug("rabbit is frozen")
            return
        self.move()

    def move(self):
        try:
            curindex = WhiteRabbit.PATH.index(self.location.db.coordinates)
        except Exception as err:
            debug("rabbit had an error; resetting to beginning; "+str(err))
            # If not found, results in returning to the start room
            curindex = -1
        debug("rabbit index: "+str(curindex))
        nextroom = getroom(*WhiteRabbit.PATH[curindex + 1])
        debug("rabbit moving to "+str(nextroom)+" (%d,%d)"%nextroom.db.coordinates)
        self.move_to(nextroom)

    def at_after_move(self, source_location):
        if self.location.db.coordinates == WhiteRabbit.PATH[-1]:
            # done
            debug("rabbit path complete")
            self.location.msg_contents("Payload delivered; rabbit self-destructing")
            self.delete()
            debug("rabbit deleted")
        else:
            self.wait_to_move()

    def at_init(self):
        self.wait_to_move()

    def wait_to_move(self):
        if hasattr(self, 'timeout') and self.timeout is not None and self.timeout.active():
            self.timeout.cancel()
        delay = round(random.random()*2+3) # 3-5seconds
        self.timeout = reactor.callLater(delay, self.move_callback)

    def freeze(self):
        if hasattr(self, 'timeout') and self.timeout is not None and self.timeout.active():
            self.timeout.cancel()
        self.db.frozen = True

class WhiteRabbitFactory(Script):
    def at_script_creation(self):
        """
        Only called once, when the script is created. This is a default Evennia
        hook.
        """
        self.persistent = True
        self.interval = 5*60 # 5 minutes

    def at_repeat(self):
        room = getroom(*WhiteRabbit.PATH[0])
        if room is None:
            debug("unable to locate rabbit start room; relying on recovery logic instead")
        rabbit = create.create_object(WhiteRabbit, key="rabbit", location=room, home=room)
        rabbit.aliases.add("dn8bossfight#whiterabbit")
        rabbit.locks.add("get:false()")
        rabbit.wait_to_move()
        debug("rabbit released")

        # testing
        # rabbit.freeze()
        # self.pause()

class WhiteRabbitCmdSet(CmdSet):
    def at_cmdset_creation(self):
        super(WhiteRabbitCmdSet, self).at_cmdset_creation()
        self.add(CmdRabbitExit)

class CmdRabbitExit(Command):
    key = "fini.obj"
    auto_help = False

    def func(self):
        if self.caller.location.db.coordinates == WhiteRabbit.PATH[0]:
            if self.obj.is_typeclass(WhiteRabbit):
                self.obj.freeze()
            else:
                debug("unexpected typeclass in fini.obj "+str(self.obj))
            for script in search.scripts("WhiteRabbitFactory"):
                script.pause()
            results = search.objects("dn8bossfight#meetme", typeclass=Room)
            if len(results) > 0:
                secret_room = results[0]
                self.caller.move_to(secret_room)
            else:
                self.caller.msg("BUG! Contact @mansel")
                debug("unable to locate secret room")
        else:
            self.caller.msg("ERROR unable to terminate once execution has begun")