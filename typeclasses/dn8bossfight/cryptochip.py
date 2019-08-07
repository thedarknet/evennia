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
        antibodyclasses = [
            AntiBody,
            XFirstAntiBody,
            YFirstAntiBody,
            WeightedRandomAntiBody,
        ]
        for typeclass in antibodyclasses:
            antibody = create.create_object(typeclass, "antibody", self, home=self, report_to=None)
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

    def move_callback(self):
        self.timeout = None
        self.move()

    def move(self):
        # Base behavior is to just pick a random exit
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
        self.timeout = reactor.callLater(delay, self.move_callback)

    def target_coordinates(self):
        # target -> room
        if self.db.target.location.db.coordinates is not None:
            return self.db.target.location.db.coordinates
        # target -> character -> room
        if self.db.target.location.location is not None and self.db.target.location.location.db.coordinates is not None:
            return self.db.target.location.location.db.coordinates
        return None

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

class XFirstAntiBody(AntiBody):
    def move(self):
        # debug("antibody moving")
        target_coordinates = self.target_coordinates()
        if target_coordinates is None:
            debug("bad coordinates")
        target_y, target_x = target_coordinates
        my_y, my_x = self.location.db.coordinates
        # debug("target located at (%d,%d)"%(target_y, target_x))

        if target_y < my_y:
            # debug("go west")
            new_y = my_y - 1
            new_x = my_x
        elif target_y > my_y:
            # debug("go east")
            new_y = my_y + 1
            new_x = my_x
        elif target_y == my_y:
            new_y = my_y
            if target_x < my_x:
                # debug("go north")
                new_x = my_x - 1
            elif target_x > my_x:
                # debug("go south")
                new_x = my_x + 1
            elif target_x == my_x:
                debug("target found; why aren't we firing?")
                return

        new_room = getroom(new_y, new_x)
        debug("antibody moving to "+str(new_room)+" (%d,%d)"%(new_y,new_x))
        self.move_to(new_room)

class YFirstAntiBody(AntiBody):
    def move(self):
        target_coordinates = self.target_coordinates()
        if target_coordinates is None:
            debug("bad coordinates")
        target_x, target_y = target_coordinates
        my_x, my_y = self.location.db.coordinates

        if target_y < my_y:
            new_y = my_y - 1
            new_x = my_x
        elif target_y > my_y:
            new_y = my_y + 1
            new_x = my_x
        elif target_y == my_y:
            new_y = my_y
            if target_x < my_x:
                new_x = my_x - 1
            elif target_x > my_x:
                new_x = my_x + 1
            elif target_x == my_x:
                debug("target found; why aren't we firing?")
                return

        new_room = getroom(new_x, new_y)
        debug("antibody moving to "+str(new_room)+" (%d,%d)"%(new_x,new_y))
        self.move_to(new_room)

class WeightedRandomAntiBody(AntiBody):
    def move(self):
        target_coordinates = self.target_coordinates()
        if target_coordinates is None:
            debug("bad coordinates")
        target_x, target_y = target_coordinates
        my_x, my_y = self.location.db.coordinates

        # [0.000, 0.250): towards x
        # [0.250, 0.500): towards y
        # [0.500, 0.750): towards x and y
        # [0.750, 0.875): away x
        # [0.875, 1.000): away y

        value = random.random()
        # debug("antibody moving %.3f"% value)
        if 0.000 <= value and value < 0.250:
            # move towards x
            new_y = my_y
            if target_x < my_x:
                new_x = my_x - 1
            elif target_x > my_x:
                new_x = my_x + 1
            else:
                new_x = my_x # results in no movement
        elif 0.250 <= value and value < 0.500:
            # move towards y
            new_x = my_x
            if target_y < my_y:
                new_y = my_y - 1
            elif target_y > my_y:
                new_y = my_y + 1
            else:
                new_y = my_y # results in no movement
        elif 0.500 <= value and value < 0.750:
            # move towards x and y
            if target_x < my_x:
                new_x = my_x - 1
            elif target_x > my_x:
                new_x = my_x + 1
            else:
                new_x = my_x # results in no movement

            if target_y < my_y:
                new_y = my_y - 1
            elif target_y > my_y:
                new_y = my_y + 1
            else:
                new_y = my_y # results in no movement
        elif 0.750 <= value and value < 0.875:
            # move away x
            new_y = my_y
            if target_x < my_x:
                new_x = my_x + 1
            elif target_x > my_x:
                new_x = my_x - 1
            else:
                if random.random() > 0.5:
                    new_x = my_x + 1
                else:
                    new_x = my_x - 1
            if new_x < 0:
                new_x = 0
            if new_x > 9:
                new_x = 9
        elif 0.875 <= value and value < 1.000:
            # move towards y
            new_x = my_x
            if target_y < my_y:
                new_y = my_y - 1
            elif target_y > my_y:
                new_y = my_y + 1
            else:
                if random.random() > 0.5:
                    new_y = my_y + 1
                else:
                    new_y = my_y - 1
            if new_y < 0:
                new_y = 0
            if new_y > 10:
                new_y = 10

        new_room = getroom(new_x, new_y)
        debug("antibody moving to "+str(new_room)+" (%d,%d)"%(new_x,new_y))
        self.move_to(new_room)