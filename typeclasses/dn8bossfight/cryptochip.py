import random
from evennia.utils import create, search
from typeclasses.rooms import Room, Zone
from typeclasses.exits import Exit
from typeclasses.objects import Object
from twisted.internet import reactor


def debug(msg):
    search.objects("loki")[0].msg(msg)
    # pass
def say_soon(location, msg):
    def say(location, msg):
        location.msg_contents(msg)
    reactor.callLater(0, say, location, msg)

PASSPHRASE = "my voice is my passport"

class Cryptochip(Object):
    """
    Manages all movement of the cryptochip and notifies relevant downstream parties when the state changes
    """
    STATE_STORED = 1
    STATE_STOLEN = 2
    STATE_RECOVERED = 3
    STATE_INSTALLED = 4

    def at_object_creation(self):
        super(Cryptochip, self).at_object_creation()
        self.db.state = Cryptochip.STATE_STORED

    def at_get(self, getter):
        if self.db.state is Cryptochip.STATE_STORED:
            self.db.state = Cryptochip.STATE_STOLEN
            debug("activating antivirus")
            # activate antivirus
            self.search("dn8bossfight#antivirus", global_search=True).recover_cryptochip(self)

    def at_drop(self, dropper):
        if self.db.state in (Cryptochip.STATE_STOLEN, Cryptochip.STATE_RECOVERED) and dropper.location == self.home:
            self.db.state = Cryptochip.STATE_STORED
            self.home.return_cryptochip()
            debug("deactivating antivirus")
            # deactivate antivirus
            self.search("dn8bossfight#antivirus", global_search=True).return_home()
        else:
            if self.db.state is Cryptochip.STATE_STOLEN and dropper.location == self.search("CPU", global_search=True):
                debug("installing cryptochip")
                # TODO do better

    def at_object_delete(self):
        self.home.return_cryptochip(delete=False)
        return True

class Playtronics(Room):
    """
    Manages the cryptochip object and keeps track of whether it is here or elsewhere
    """
    def at_object_creation(self):
        super(Playtronics, self).at_object_creation()
        self.db.has_cryptochip = True
        self.db.cryptochip = None

    def return_cryptochip(self, delete=True):
        if self.db.has_cryptochip:
            debug("BUG cryptochip returning when we still have it")
        if delete:
            # TODO confirm cryptochip is in the room
            if self.db.cryptochip:
                self.db.cryptochip.delete()
            else:
                debug("BUG cryptochip returning when it doesn't exist")
        self.db.has_cryptochip = True

    def unlock_cryptochip(self):
        if self.db.has_cryptochip:
            debug("releasing the cryptochip!")
            self.db.has_cryptochip = False
            self.db.cryptochip = create.create_object(Cryptochip, "cryptochip", self, home=self, report_to=None)
            self.msg_contents("The drawer opens and reveals a small computer chip.")
        else:
            debug("cryptochip already released")
            self.msg_contents("The drawer opens, but it is empty.")

    def listen(self, speaker, speech):
        if speaker.location == self and speech == PASSPHRASE:
            self.unlock_cryptochip()

    # HACK: Listen for the magic words by intercepting the broadcast mechanism
    def msg_contents(self, text=None, exclude=None, from_obj=None, mapping=None, **kwargs):
        super(Playtronics, self).msg_contents(text, exclude, from_obj, mapping, **kwargs)

        if from_obj is not None and 'speech' in mapping:
            # debug("{speaker} says {speech}".format(speaker=str(from_obj), speech=str(mapping['speech'])))
            self.listen(from_obj, mapping['speech'])

class AntiVirus(Room):
    def at_object_creation(self):
        super(AntiVirus, self).at_object_creation()
        self.db.antibodies = []

    def recover_cryptochip(self, cryptochip):
        for _ in range(3):
            antibody = create.create_object(AntiBody, "antibody", self, home=self, report_to=None)
            antibody.db.antivirus = self
            antibody.set_target(cryptochip)
            self.db.antibodies.append(antibody)

    def return_home(self):
        for antibody in self.db.antibodies:
            if antibody is not None:
                antibody.delete()

class AntiBody(Object):
    STATE_PASSIVE = 0
    STATE_HUNTING = 1
    STATE_GOHOME = 2

    def set_target(self, target):
        self.db.target = target
        self.db.state = AntiBody.STATE_HUNTING
        debug("antibody hunting %s" % (target))

    def capture_target(self, obj):
        if obj == self.db.target or self.db.target in obj.contents:
            debug("target located!")
            if self.db.target in obj.contents:
                debug("imprisoning target holder")
                jail = self.search("dn8bossfight#jail", global_search=True)
                obj.move_to(jail)
            self.db.target.delete()
            debug("target destroyed; returning home")
            self.db.antivirus.return_home()

    def at_object_arrive(self, obj, source_location):
        reactor.callLater(0.5, self.capture_target, obj)

    def move_randomly(self):
        self.timeout = None
        randomized_exits = random.sample(self.location.exits, len(self.location.exits))
        exit = next(exit for exit in randomized_exits)
        if exit:
            debug("antibody moving to "+exit.destination.dbref+" (%d,%d)"%exit.destination.db.coordinates)
            self.move_to(exit)
        else:
            debug("nowhere to go? "+str(randomized_exits))

    def at_after_move(self, source_location):
        self.wait_to_move()
        for obj in self.location.contents:
            if obj == self:
                continue
            if obj.is_typeclass(Exit):
                continue
            debug("antibody examining objects on arrival: "+str(obj))
            self.capture_target(obj)

    def at_init(self):
        self.wait_to_move()

    def wait_to_move(self):
        if hasattr(self, 'timeout') and self.timeout is not None:
            self.timeout.cancel()
        delay = round(random.random()*1+3) # 1-4seconds
        self.timeout = reactor.callLater(delay, self.move_randomly)