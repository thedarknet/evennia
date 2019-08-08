import random
from evennia.utils import search
from typeclasses.characters import Character
from typeclasses.rooms import Room
from typeclasses.exits import Exit

def debug(msg):
    search.objects("loki")[0].msg(msg)

class Funhouse(Room):
    COLORS = [
        "red",
        "black",
        "purple",
    ]
    def at_object_receive(self, obj, source_location):
        obj.db.funhouse_source = source_location

    def rotate(self, triggering_obj):
        color = random.sample(Funhouse.COLORS, 1)[0]
        self.db.desc = """
        This room is empty. The walls are painted %s.
        """.strip() % color
        # Notify everyone _except_ the one that moved
        for obj in self.contents:
            if obj == triggering_obj:
                continue
            if obj.is_typeclass(Character, exact=False):
                obj.msg("The room is now %s." % (color))

class FunhouseExit(Exit):
    def at_traverse(self, obj, target, **kwargs):
        debug("attempted exit %s -> %s"%(obj,target))
        if target == obj.db.funhouse_source:
            del obj.db.funhouse_source
            super(FunhouseExit, self).at_traverse(obj, target, **kwargs)
        else:
            debug("masking exit and modifying room")
            self.location.rotate(obj)
            obj.msg(self.location.return_appearance(obj))