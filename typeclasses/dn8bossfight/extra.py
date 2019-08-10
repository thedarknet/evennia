import random
from evennia import CmdSet
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils import create, search
from commands.command import Command
from twisted.internet import reactor
from typeclasses.exits import Exit
from typeclasses.objects import Object
from typeclasses.rooms import Room

def debug(msg):
    search.objects("loki")[0].msg(msg)
def say_soon(location, msg):
    def say(location, msg):
        location.msg_contents(msg)
    reactor.callLater(0, say, location, msg)

class RememberLookedAt(Object):
    def at_desc(self, looker):
        super(RememberLookedAt, self).at_desc(looker)
        looker.attributes.add("looked_at_%d"%self.id, True)

class Safe(Object):
    def return_appearance(self, looker):
        if self.locks.check_lockstring(looker, "has_looked_at(%d)"%self.db.password.id):
            looker.attributes.add("looked_at_%d"%self.id, True)
            return """
            You enter "joker" into the keypad. The safe unlocks with a click.
            """.strip()
        else:
            return """
            You need a passphrase.
            """.strip()

class Crate(Object):
    def obj_used_upon(self, user, obj_used):
        debug("%s used on crate; expecting %s"%(obj_used,self.db.open_with))
        if obj_used == self.db.open_with:
            self.db.desc = "An open crate full of flashlights"
            flashlight = [x for x in self.location.contents if x.name == "flashlight"][0]
            flashlight.locks.add("view:all()")
            user.msg("You pry open one of the crates. It's full of flashlights.")
        else:
            user.msg("Nothing happens.")

class RetroComputer(Object):
    def obj_used_upon(self, user, obj_used):
        debug("%s used on retrocomputer; expecting %s"%(obj_used,self.db.open_with))
        if obj_used == self.db.open_with:
            self.location.db.desc = "This room’s walls are covered with retro computer screens. A four-handed keyboard (why??) sits on the desk, connected to a tower under the desk."
            self.db.desc = "FINGERPRINT MATCH FOUND: STANLEY JOBSON"
            user.msg("You attach the four-handed keyboard to the tower (why????). The computer screens light up.")
        else:
            user.msg("Nothing happens.")

class InfiniteFlashlight(Object):
    def at_before_get(self, destination):
        def delay_say(target, msg):
            def say(target, msg):
                target.msg(msg)
            reactor.callLater(0, say, target, msg)

        matches = [x for x in destination.contents if "dn8bossfight#flashlight" in x.aliases.all()]
        if len(matches) == 0:
            if random.random() < 0.75:
                obj = create.create_object(Object, "flashlight", destination, self.location, aliases=["dn8bossfight#flashlight"])
                obj.db.desc = "A flashlight. It lights things up and protects you from the darkness."
            else:
                obj = create.create_object(Object, "fleshlight", destination, self.location, aliases=["dn8bossfight#flashlight"])
                obj.db.desc = "A fleshlight."
            delay_say(destination, "You get a %s. The darkness cannot hurt you now."%obj.name)
        else:
            delay_say(destination, "Let's not be greedy. You've already got one.")

        return False

class CmdUse(MuxCommand):
    """
    use <object> on <target>
    """
    rhs_split = ["on"]
    def func(self):
        if self.rhs:
            target = self.caller.search(self.rhs)
            if target is None:
                self.caller.msg("%s not found"%self.rhs)
            else:
                target.obj_used_upon(self.caller, self.obj)
        else:
            self.caller.msg(self.key + " on what?")

class UsableObject(Object):
    def at_init(self):
        cmdset = CmdSet(key="%s CmdSet"%self.name, cmdsetobj=self)
        cmd = CmdUse(key="use %s"%self.name)
        cmdset.add(cmd)
        self.cmdset.add(cmdset)

class GrueHouse(Room):
    pass

class GrueHouseExit(Exit):
    def at_traverse(self, obj, target, **kwargs):
        debug("attempted exit %s -> %s"%(obj,target))
        matches = [x for x in obj.contents if "dn8bossfight#flashlight" in x.aliases.all()]
        if len(matches) > 0:
            if matches[0].name == "fleshlight":
                obj.msg("|gYou turn on your fleshlight and the room lights up. Huh, you weren't expecting that to work.\nYou make your way through the room. Guess there was no grue after all.")
            else:
                obj.msg("|gYou turn on your flashlight and make your way through the room. Huh, guess there was no grue after all.")
            super(GrueHouseExit, self).at_traverse(obj, target, **kwargs)
        else:
            obj.msg("|rYou have been eaten by a grue.")
            obj.move_to(search.objects("dn8bossfight#entrance", typeclass='typeclasses.dn8bossfight.rooms.Entrance')[0])