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
from typeclasses.dn8bossfight.cpu import Mainframe, CPU, HomeDirectory

room = getroom(4,5)
room.swap_typeclass(Mainframe, clean_cmdsets=True, run_start_hooks='all')
room.name = "Mainframe"

cpu = create.create_object(CPU, key="CPU", report_to=caller, location=room, home=room)
cpu.aliases.add("dn8bossfight#cpu")
cpu.locks.add("get:false()")

# god's home directory
room = getroom(6,9)
room.swap_typeclass(HomeDirectory, clean_cmdsets=True)
room.db.desc = "god's home directory"
file = create.create_object(Object, key=".GARBAGE", report_to=caller, location=room, home=room)
file.db.desc = "An encrypted garbage file"
file.db.message = "rbt whte follow"
file.locks.add("view:false()")

# plague's home directory
room = getroom(0,8)
room.swap_typeclass(HomeDirectory, clean_cmdsets=True)
room.db.desc = "plague's home directory"
file = create.create_object(Object, key=".GARBAGE", report_to=caller, location=room, home=room)
file.db.desc = "An encrypted garbage file"
file.db.message = "davinci"
file.locks.add("view:false()")

# margo's home directory
room = getroom(3,2)
room.swap_typeclass(HomeDirectory, clean_cmdsets=True)
room.db.desc = "margo's home directory"
file = create.create_object(Object, key=".GARBAGE", report_to=caller, location=room, home=room)
file.db.desc = "An encrypted garbage file"
file.db.message = "4bit + cache - bird"
file.locks.add("view:false()")

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

room = create.create_object(Jail, "Quarantine", zone, home=zone, report_to=caller, aliases=["dn8bossfight#jail"])
room.db.desc = "You are in quarantine. There is no escape. Please serve your time quietly."

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
# Red Herring Rooms

from typeclasses.dn8bossfight.extra import Crate, GrueHouse, GrueHouseExit, InfiniteFlashlight, RememberLookedAt, RetroComputer, Safe, UsableObject

# UR1
room = getroom(9,6)
room.db.desc = """
This room is covered with playing cards, scattered across the floor and taped to the walls.
""".strip()

obj = create.create_object(Object, "cards", room)
obj.db.desc = """
There are at least a dozen different decks, all with varying face and back designs.
""".strip()
obj.locks.add("get:false()")

#####

# UR2
room = getroom(7,1)
room.db.desc = """
This room is empty. The walls are smeared with red ink in the shape of violent blood spatters.
""".strip()

obj = create.create_object(Object, "ink", room)
obj.db.desc = """
It’s tacky. It’s just paint… right?
""".strip()
obj.locks.add("get:false()")

#####

# UR5
room = getroom(9,7)
room.db.desc = """
This room is empty. The walls are painted black. A Cheshire Cat smile is painted in the corner.
""".strip()

smile = create.create_object(RememberLookedAt, "smile", room)
smile.db.desc = """
The rest of the cat is painted in a different shade of black on the wall. In one paw it holds a joker playing card.
""".strip()
smile.locks.add("get:false()")

#####

# UR6
room = getroom(0,3)
room.db.desc = """
This room is painted purple. A framed painting of the Mad Hatter from Disney’s “Alice in Wonderland” hangs on one wall.
""".strip()

painting = create.create_object(RememberLookedAt, "painting", room)
painting.db.desc = """
There’s a hidden wall safe behind the painting. A screen glows softly above a keypad.
""".strip()
painting.locks.add("get:false()")

safe = create.create_object(Safe, "safe", room)
safe.db.desc = """
A hidden wall safe
""".strip()
safe.locks.add("get:false();view:has_looked_at(%d)"%painting.id)
safe.db.password = smile

cards = create.create_object(Object, "deck of playing cards", room)
cards.db.desc = """
A deck of playing cards
""".strip()
cards.locks.add("view:has_looked_at(%d)"%safe.id)

boards = create.create_object(Object, "broken circuit board", room)
boards.db.desc = """
A broken circuit board
""".strip()
boards.locks.add("view:has_looked_at(%d)"%safe.id)

crowbar = create.create_object(UsableObject, "crowbar", room)
crowbar.db.desc = """
A metal crowbar. It looks good for pulling nails.
""".strip()
crowbar.locks.add("view:has_looked_at(%d)"%safe.id)

#####

# UR3
room = getroom(1,10)
room.db.desc = """
This room is piled high with boxes and crates of varying sizes.
""".strip()

crate = create.create_object(Crate, "crate", room)
crate.db.desc = """
It's nailed shut.
""".strip()
crate.locks.add("get:false()")
crate.db.open_with = crowbar

flashlight = create.create_object(InfiniteFlashlight, "flashlight", room)
flashlight.db.desc = """
A flashlight. It makes darkness brighter.
""".strip()
flashlight.locks.add("view:false()")

#####

# UR4
room = getroom(3,10)
room.db.desc = """
This room contains an elegant sitting area. Sleek leather chairs surround a carved teak coffee table.
""".strip()

obj = create.create_object(Object, "art book", room)
obj.db.desc = """
It contains concept art for a dinosaur movie.
""".strip()
obj.locks.add("get:false()")

#####

# UR7
room = getroom(6,6)
room.db.desc = """
This room is painted blue. A framed photo of a young Angelina Jolie hangs on the wall.
""".strip()

obj = create.create_object(Object, "photo", room)
obj.db.desc = """
This image looks familiar somehow...
""".strip()
obj.locks.add("get:false()")

#####

# UR8
room = getroom(7,6)
room.db.desc = """
This room is empty. The wallpaper is an elegant diamonds pattern.
""".strip()

obj = create.create_object(Object, "", room)
obj.db.desc = """
""".strip()
obj.locks.add("get:false()")

#####

# UR9
room = getroom(8,10)
room.db.desc = """
This room is empty. The walls are painted black, with clubs drawn on them in white chalk.
""".strip()

#####

# UR10
room = getroom(4,3)
room.db.desc = """
This room is empty. A giant fractal heart is painted on one wall, made up of smaller hearts, which are made up of smaller hearts.
""".strip()

#####

# UR11
room = getroom(6,3)
room.db.desc = """
This room is empty. The walls are painted black. Two-foot-tall letters in neon green courier font are painted on the walls. They spell out, "Do you want to play a game?"
""".strip()

#####

# UR12
room = getroom(2,1)
room.db.desc = """
This room is covered with white wallpaper. The wallpaper is peeling on one wall. A framed photo of a young Robert Redford hangs under the peeling paper.
""".strip()

obj = create.create_object(Object, "photo", room)
obj.db.desc = """
This image looks familiar somehow...
""".strip()
obj.locks.add("get:false()")

#####

# UR13
room = getroom(8,4)
room.db.desc = """
This room is empty. The walls are painted purple. The words “We’re all mad here” are scrawled across the walls in green chalk.
""".strip()

#####

# UR14
room = getroom(3,6)
room.db.desc = """
This room is painted blue. A framed photo of Sandra Bullock hangs on one wall.
""".strip()

obj = create.create_object(Object, "photo", room)
obj.db.desc = """
This image looks familiar somehow...
""".strip()
obj.locks.add("get:false()")

#####

# UR16
room = getroom(4,8)
room.db.desc = """
The floor of this room is covered with soil. Water trickles down the walls, nourishing a flowering trumpet vine growing on a heart-shaped trellis. A shovel sits in one corner.
""".strip()

#####

# UR17
room = getroom(2,9)
room.db.desc = """
This room is full of hat stands, each holding several top hats in various styles and colors.
""".strip()

obj = create.create_object(Object, "hats", room)
obj.db.desc = """
Each hat has a card tucked into the band which reads “10 / 6”
""".strip()
obj.locks.add("get:false()")

#####

# UR18
room = getroom(5,5)
room.db.desc = """
This room’s walls are covered with retro computer screens. A single desk sits in the middle of the room. A four-handed keyboard (why??) sits on the desk, connected to a tower under the desk.
""".strip()
# TODO modify room description when keyboard is picked up

obj = create.create_object(Object, "screens", room)
obj.db.desc = """
CHECKFSYS
DAEMON
ADM
UUCP
BIN
SYS
123
ADDUSER
ADMIN
ANON
ANONUUCP
ANONYMOUS
ASG
AUDIT
AUTH
BACKAPPL
BACKUP
BATCH
BBH
BLAST
BUPSCHED
CBM
CBMTEST
ROOT
""".strip()
obj.locks.add("get:false()")

keyboard = create.create_object(UsableObject, "keyboard", room)
keyboard.db.desc = """
A four-handed keyboard. Why???
"""

#####

# UR19
room = getroom(0,0)
room.db.desc = """
This room’s walls are covered with retro computer screens. A single desk sits in the middle of the room. A tower sits under the desk. It has no keyboard attached.
""".strip()

obj = create.create_object(RetroComputer, "screen", room)
obj.aliases.add("desk")
obj.aliases.add("computer")
obj.db.desc = """
The screens are all black.
""".strip()
obj.locks.add("get:false()")
obj.db.open_with = keyboard

#####

# UR20
room = getroom(4,7)
room.swap_typeclass(GrueHouse, clean_cmdsets=True, run_start_hooks='all')
room.aliases.add("dn8bossfight#gruehouse")
room.db.desc = """
This room is dark. You are likely to be eaten by a grue.
""".strip()

for exit in room.exits:
    exit.swap_typeclass(GrueHouseExit, run_start_hooks=None)

#####

# UR21
room = getroom(0,6)
room.db.desc = """
This room is empty. The walls are painted black, with gleaming black steel spades stamped in the corners.
""".strip()

#CODE
# Cleanup the Zone
if DEBUG:
    cleanup_everything()