#HEADER
# This will be included in all other #CODE blocks
from evennia.utils import create, search
from typeclasses.objects import Object
from typeclasses.rooms import Room, Zone
from typeclasses.exits import Exit
from django.conf import settings
exit_typeclass = settings.BASE_EXIT_TYPECLASS
# Make the syntax checker happy everywhere else
caller=caller

limbo = search.objects('Limbo', typeclass=Room)[0]
results = search.objects('ZoneDN8BossFight', typeclass=Zone)
if len(results) > 0:
    zone = results[0]
else:
    zone = None

def getroom(x,y):
    for obj in zone.contents:
        if obj.is_typeclass(Room, exact=False) and hasattr(obj.db, 'coordinates') and obj.db.coordinates[0] == x and obj.db.coordinates[1] == y:
            return obj
    return None

#CODE
# Setup the Zone
if not zone:
    zone = create.create_object(Zone, "ZoneDN8BossFight", None, home=None, report_to=caller)
    caller.msg("zone created")
else:
    caller.msg("zone already exists")

# clean up deferred until the end of the file

#CODE
# Create all the rooms
# Coordinates  vy  >x
SIZE=(10,11)
rooms = dict()
for x in range(SIZE[0]):
    for y in range(SIZE[1]):
        if DEBUG:
            suffix = " (%d,%d)"%(x,y)
        else:
            suffix = ""
        rooms["%s,%s"%(x,y)] = create.create_object(Room, "Somewhere inside Cyberez"+suffix, zone, home=zone, report_to=caller, attributes=[['coordinates',(x,y)]])

mapping = {
    "-1,-1": "nw",
    "-1,0": "w",
    "-1,1": "sw",
    "0,-1": "n",
    "0,1": "s",
    "1,-1": "ne",
    "1,0": "e",
    "1,1": "se",
}
for x in range(SIZE[0]):
    for y in range(SIZE[1]):
        room = rooms["%d,%d"%(x,y)]
        room.db.links = dict()
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                if dx == 0 and dy == 0:
                    continue
                if x+dx < 0 or x+dx >= SIZE[0]:
                    continue
                if y+dy < 0 or y+dy >= SIZE[1]:
                    continue
                cardinal = mapping["%d,%d"%(dx,dy)]
                position = "%d,%d"%(x+dx,y+dy)
                room.db.links[cardinal] = rooms[position]
                to_exit = create.create_object(exit_typeclass, cardinal, room,
                                               destination=rooms[position],
                                               report_to=caller)
        caller.msg("%d,%d"%room.db.coordinates + " " + str(room.db.links))

if DEBUG:
    for room in rooms.values():
        caller.msg("created "+room.name+" "+",".join(["%d"%x for x in room.db.coordinates])+" "+room.location.name)

#CODE
# Set up the Entrance room and link to Limbo
from typeclasses.dn8bossfight.rooms import Entrance
room = getroom(1,7)
room.swap_typeclass(Entrance, clean_cmdsets=True, run_start_hooks='all')
room.name = "The Grand Entrance Hall"
room.db.desc = """
You stand in the grand entrance hall for all of Cyberez.

You see a solid wall on some sides and pathways on others.
""".strip()

to_exit = create.create_object(exit_typeclass, "zone:cyberez", limbo,
                                aliases=["bossfight","cyberez"],
                                destination=room,
                                report_to=caller)
from_exit = create.create_object(exit_typeclass, "Limbo", room,
                                   aliases=["exit", "quit", "leave"],
                                   destination=limbo,
                                   report_to=caller)

if DEBUG:
    pass

#CODE
# Accounting Worm Puzzle
from typeclasses.dn8bossfight.accounting import Accounting, AccountingLedger, Transaction, Worm, TransactionFactory, Bird
rooms = [
    getroom(8,0),
    getroom(9,0),
    getroom(8,1),
    getroom(9,1),
]
for room in rooms:
    room.swap_typeclass(Accounting, clean_cmdsets=True, run_start_hooks='all')
    room.name = "Accounting"
    room.db.desc = "One of the accounting databases"
    ledger = create.create_object(AccountingLedger, key="ledger",
                                  aliases=["ledger"],
                                  attributes=[["desc","An accounting ledger"]],
                                  location=room, home=room,
                                  report_to=caller,
                                  )
    # Ledger must stay here
    ledger.locks.add("get:false()")

# for i in range(10):
#     create.create_object(Transaction, key="transaction",
#                          aliases=["transaction#%d"%(i)],
#                          attributes=[["txdetails", "+$10.%02d"%(i)]],
#                          location=getroom(0,0), home=getroom(0,0),
#                          report_to=caller
#                          )

create.create_script(TransactionFactory, key="AccountingTransactionFactory", report_to=caller, attributes=[["rooms",rooms]])

worm = create.create_object(Worm, key="worm",
                            location=getroom(3,0), home=getroom(3,0),
                            report_to=caller
                            )
worm.locks.add("get:false()")

bird = create.create_object(Bird, key="bird", report_to=caller, location=getroom(0,0), home=getroom(0,0))


#CODE
# Cleanup the Zone
if DEBUG:
    for script in search.scripts("AccountingTransactionFactory"):
        script.stop()
    if zone:
        for room in zone.contents:
            for item in room.contents:
                if item.is_typeclass(Room, exact=False) or item.is_typeclass(Exit, exact=False):
                    continue
                if item.is_typeclass(Object, exact=False):
                    item.delete()
                else:
                    caller.msg("Leaving behind object: %s (%s)"%(str(item),item.typeclass_path))
        zone.delete() # also deletes all the rooms
        caller.msg("zone deleted")