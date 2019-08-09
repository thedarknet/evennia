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
        if obj.is_typeclass(Room, exact=False) and obj.db.coordinates is not None and obj.db.coordinates[0] == x and obj.db.coordinates[1] == y:
            return obj
    return None

def cleanup_everything():
    for scriptname in ["AccountingTransactionFactory", "WhiteRabbitFactory"]:
        for script in search.scripts(scriptname):
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

#CODE
cleanup_everything()

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
import random
COLORS = [
    "red",
    "black",
    "purple",
]

# Coordinates  vy  >x
SIZE=(10,11)
rooms = dict()
for x in range(SIZE[0]):
    for y in range(SIZE[1]):
        if DEBUG:
            suffix = " (%d,%d)"%(x,y)
        else:
            suffix = ""

        color = random.sample(COLORS, 1)[0]
        desc = """
        This room is empty. The walls are painted %s.
        """.strip() % color

        rooms["%s,%s"%(x,y)] = create.create_object(Room, "Somewhere inside Cyberez"+suffix, zone, home=zone, report_to=caller, attributes=[['coordinates',(x,y)],['desc',desc]])

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
room.aliases.add("dn8bossfight#entrance")
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
from typeclasses.dn8bossfight.accounting import Accounting, AccountingLedger, Transaction, Worm, TransactionFactory, Bird, AccountingTrap
rooms = [
    getroom(8,0),
    getroom(9,0),
    getroom(8,1),
    getroom(9,1),
]
for room in rooms:
    room.swap_typeclass(Accounting, clean_cmdsets=True, run_start_hooks='all')
    room.aliases.add("dn8bossfight#accounting")
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
                            location=getroom(8,0), home=getroom(8,0),
                            report_to=caller
                            )
worm.locks.add("get:false()")
worm.db.desc = "A hungry looking worm wearing a fancy tie. He's too small and quick for you to grab, but maybe a smaller animal could do it."

bird = create.create_object(Bird, key="bird", report_to=caller, location=getroom(3,8), home=getroom(3,8))

rooms = [
    (7,0),
    (7,1),
    (7,2),
    (8,2),
]
for coords in rooms:
    room = getroom(*coords)
    room.swap_typeclass(AccountingTrap, clean_cmdsets=True, run_start_hooks='all')
    room.aliases.add("dn8bossfight#accounting_trap")
    room.db.desc = "This room is painted corporate off-white. Writing is scribbled across the walls in chalk."

#CODE
# Mainframe
from typeclasses.dn8bossfight.cpu import Mainframe, CPU

room = getroom(4,5)
room.swap_typeclass(Mainframe, clean_cmdsets=True, run_start_hooks='all')
room.name = "Mainframe"

cpu = create.create_object(CPU, key="CPU", report_to=caller, location=room, home=room)
cpu.aliases.add("dn8bossfight#cpu")
cpu.locks.add("get:false()")

# god's home directory
room = getroom(6,9)
# TODO typeclass as a home directory
file = create.create_object(Object, key="garbage", report_to=caller, location=room, home=room)
file.db.desc = "An encrypted garbage file"
file.db.message = "rbt whte follow"

# plague's home directory
room = getroom(0,8)
# TODO typeclass as a home directory
file = create.create_object(Object, key="garbage", report_to=caller, location=room, home=room)
file.db.desc = "An encrypted garbage file"
file.db.message = "davinci"

# margo's home directory
room = getroom(3,2)
# TODO typeclass as a home directory
file = create.create_object(Object, key="garbage", report_to=caller, location=room, home=room)
file.db.desc = "An encrypted garbage file"
file.db.message = "4bit + cache - bird"

#CODE
# Cryptochip theft
from typeclasses.dn8bossfight.cryptochip import Playtronics, AntiVirus, AntiVirusControl
from typeclasses.dn8bossfight.rooms import Jail

room = getroom(1,1)
room.swap_typeclass(Playtronics, clean_cmdsets=True, run_start_hooks='all')
room.aliases.add("dn8bossfight#playtronics")
room.name = "Playtronics HQ"
room.db.desc = """
You stand outside an office with a metal grill and a seamed opening.
It looks like maybe a microphone and a drawer?
""".strip()

room = getroom(4,4)
room.swap_typeclass(AntiVirus, clean_cmdsets=True, run_start_hooks='all')
room.aliases.add("dn8bossfight#antivirus")
room.name = "AntiVirus"
room.db.desc = "You see several AntiBodies sitting behind a desk, wholly disinterested in you."

obj = create.create_object(AntiVirusControl, key="AntiVirus Control Console", location=room, home=zone, report_to=caller, aliases=["dn8bossfight#avcontrol"])
obj.locks.add("get:false()")

room = create.create_object(Jail, "Internet Jail", zone, home=zone, report_to=caller, aliases=["dn8bossfight#jail"])
room.db.desc = "You are in jail. There is no escape. Please serve your time quietly."

#CODE
# White Rabbit
from typeclasses.dn8bossfight.rabbit import WhiteRabbitFactory, WhiteRabbit
from typeclasses.dn8bossfight.meetme import DataLink, DataLinkCmdSet
create.create_script(WhiteRabbitFactory, key="WhiteRabbitFactory", report_to=caller)

# Secret meet-me room
room = create.create_object(Room, "Meet-Me Room", zone, home=zone, report_to=caller, aliases=["dn8bossfight#meetme"])
room.db.desc = "You are in the back corner of the Cyberez MeetMe room, where all connections come and go."
room.cmdset.add(DataLinkCmdSet, permanent=True)

white_rabbit_origin = getroom(*WhiteRabbit.PATH[0])
from_exit = create.create_object(exit_typeclass, "Exit", room,
                                   aliases=["exit", "quit", "leave"],
                                   destination=white_rabbit_origin,
                                   report_to=caller)

obj = create.create_object(DataLink, "March Hare Data Link", location=room, home=room, aliases=["dn8bossfight#march_hare_data_link"])
obj.locks.add("get:false()")
obj.db.desc = """
A Decker data link to the March Hare. You can disconnect it.
""".strip()

obj = create.create_object(DataLink, "Daemon Data Link", location=room, home=room, aliases=["dn8bossfight#daemon_data_link"])
obj.locks.add("get:false()")
obj.db.desc = """
A Decker data link to the Daemon. You can disconnect it.
""".strip()

#CODE
# Funhouse Rooms
from typeclasses.dn8bossfight.funhouse import Funhouse, FunhouseExit
rooms = [
    getroom(1,4),
    getroom(4,9),
    getroom(6,4),
]
for room in rooms:
    room.swap_typeclass(Funhouse, clean_cmdsets=True, run_start_hooks='all')
    room.aliases.add("dn8bossfight#funhouse")
    
    for exit in room.exits:
        exit.swap_typeclass(FunhouseExit, run_start_hooks=None)

#CODE
# Cleanup the Zone
if DEBUG:
    cleanup_everything()