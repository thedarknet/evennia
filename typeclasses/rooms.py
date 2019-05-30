"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia import DefaultRoom
from evennia.utils import create, search

class Room(DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See examples/object.py for a list of
    properties and methods available on all Objects.
    """
    def basetype_setup(self):
        # Override location removal in DefaultRoom setup and replace with first Zone
        location = self.location
        super(Room, self).basetype_setup()
        # keep going up locations until you find one that is a Zone
        while True:
            if location.__class__ == Zone:
                self.location = location
                break
            if hasattr(location, 'location'):
                if location.location is None:
                    break
                else:
                    location = location.location
                    continue
            break

class Zone(Room):
    def at_object_delete(self):
        ret = super(Zone, self).at_object_delete()
        if ret:
            for o in self.contents:
                if isinstance(o, Room):
                    o.delete()
            return True
        else:
            return False