import random
from evennia.utils import create, search
from twisted.internet import reactor
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

results = search.objects('ZoneDN8BossFight', typeclass=Zone)
if len(results) > 0:
    zone = results[0]
else:
    zone = None

def getroom(x,y):
    for obj in zone.contents:
        if obj.is_typeclass(Room, exact=False) and obj.db.coordinates is not None and obj.db.coordinates[0] == x and obj.db.coordinates[1] == y:
            return obj
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
        (4,5), # cpu room
    ]

    # def at_object_arrive(self, obj, source_location):
    #     reactor.callLater(0.5, self.capture_target, obj)

    def move_callback(self):
        self.timeout = None
        # check to see if we are on the coordinate grid
        if self.location.db.coordinates is not None:
            self.move()

    def move(self):
        curindex = WhiteRabbit.PATH.index(self.location.db.coordinates)
        # If not found, results in returning to the start room
        nextroom = getroom(*WhiteRabbit.PATH[curindex + 1])
        debug("rabbit moving to "+str(nextroom)+" (%d,%d)"%nextroom.db.coordinates)
        self.move_to(nextroom)

    def at_after_move(self, source_location):
        if self.location.db.coordinates == WhiteRabbit.PATH[-1]:
            # done
            self.location.msg_contents("Payload delivered; rabbit self-destructing")
            self.delete()
        else:
            self.wait_to_move()

    def at_init(self):
        self.wait_to_move()

    def wait_to_move(self):
        if hasattr(self, 'timeout') and self.timeout is not None:
            self.timeout.cancel()
        delay = round(random.random()*2+3) # 3-5seconds
        self.timeout = reactor.callLater(delay, self.move_callback)

class WhiteRabbitFactory(Script):
    def at_script_creation(self):
        """
        Only called once, when the script is created. This is a default Evennia
        hook.
        """
        self.persistent = True
        self.interval = 5*60 # 5 minutes
        self.db.start_room = getroom(*WhiteRabbit.PATH[0])

    def at_repeat(self):
        rabbit = create.create_object(WhiteRabbit, key="rabbit", location=self.db.start_room, home=self.db.start_room)
        rabbit.aliases.add("dn8bossfight#whiterabbit")
        rabbit.locks.add("get:false()")
