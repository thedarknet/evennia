from commands.command import Command
from typeclasses.rooms import Room, Zone
from typeclasses.objects import Object
from typeclasses.dn8bossfight.cryptochip import Cryptochip
from evennia.commands.default.muxcommand import MuxCommand
from evennia import CmdSet
from twisted.internet import reactor
from evennia.utils import search

def debug(msg):
    # search.objects("loki")[0].msg(msg)
    pass
def say_soon(location, msg):
    def say(location, msg):
        location.msg_contents(msg)
    reactor.callLater(0, say, location, msg)

class Mainframe(Room):
    def at_object_receive(self, obj, source_location):
        if obj.is_typeclass(Cryptochip, exact=False):
            cpu = self.search("CPU")
            obj.move_to(cpu)
            cpu.db.cryptochip_installed = True
            debug("cryptochip installed")
            search.channels("Public")[0].msg("|rCryptochip installed in CPU")

class CmdDecrypt(MuxCommand):
    """
    Decrypt a file

    Usage:
      decrypt <file>
    """

    key = "decrypt"

    def func(self):
        if not self.args:
            self.caller.msg("Please provide a file to decrypt")
        else:
            cpu = self.caller.search("dn8bossfight#cpu")
            matches = [x for x in self.caller.location.contents if x.name.lower() == self.args.lower()]
            if len(matches) > 0:
                if not cpu.db.cryptochip_installed:
                    self.caller.msg("Cryptography routines not found")
                    return
                if cpu.db.ddos_mitigated:
                    file = matches[0]
                    self.caller.msg("Decrypting %s"%file)
                    cpu.db.garbage_file_decoded = file.db.message
                    self.caller.msg("Message: "+file.db.message)
                else:
                    def overloaded(self):
                        self.caller.msg("Unable to complete request. CPU overloaded.")
                    reactor.callLater(5, overloaded, self)
                    self.caller.msg("Processing...")
            else:
                self.caller.msg("File not found")
                

class CPUCmdSet(CmdSet):
    def at_cmdset_creation(self):
        super(CPUCmdSet, self).at_cmdset_creation()
        self.add(CmdDecrypt)

class CPU(Object):
    def at_object_creation(self):
        self.db.cryptochip_installed = False
        self.db.ddos_mitigated = True
        self.db.garbage_file_decoded = ""

        self.cmdset.add(CPUCmdSet, permanent=True)

    def obj_used_upon(self, user, obj_used):
        if obj_used == search.objects("dn8bossfight#cryptochip", typeclass=Cryptochip)[0]:
            cpu = self.search("CPU")
            obj_used.move_to(cpu)
            cpu.db.cryptochip_installed = True
            debug("cryptochip installed")
            search.channels("Public")[0].msg("|rCryptochip installed in CPU")
        else:
            user.msg("Nothing happens")

    def return_appearance(self, looker):
        appearance = super(CPU, self).return_appearance(looker)

        if self.db.cryptochip_installed:
            appearance = appearance + "\n\nThe cryptochip is installed in the CPU."
        else:
            appearance = appearance + "\n\nThere is an empty socket for an additional logic chip."

        if self.db.ddos_mitigated:
            appearance = appearance + "\n\nThe CPU load and temperature are within normal operating parameters."
        else:
            appearance = appearance + "\n\nThe CPU is under heavy load and is approaching critical shutdown temperature."

        if self.db.garbage_file_decoded:
            appearance = appearance + "\n\nLast decrypted message: " + self.db.garbage_file_decoded
        else:
            pass

        return appearance

class CmdListFiles(Command):
    """
    ls [-a]
    """
    FILES = """
WRHSE. EXPEND
GARBAGE
ANNUAL BUDGET
COMP. OPERATIONS
KINEMATICS
SEA-BOARD LAWS
TPGC. EXPEND
WRHSE. LOCATION
COMPANY STATUS
COMPOSITE PLANTS
EXPLOR. DVLT
EXPLOR. RESEARCH
GEOLOGIC RESEARCH
""".strip()
    def func(self):
        files = CmdListFiles.FILES
        if self.args.strip() == "-a":
            self.obj.search(".garbage").locks.add("view:all()")
            files = ".GARBAGE\n" + files
        self.caller.msg("/root/.workspace/\n"+files)

import evennia.commands.default.general
class CmdLook(evennia.commands.default.general.CmdLook):
    aliases = []

class HomeDirectory(Room):
    def at_init(self):
        cmdset = CmdSet(key="%s CmdSet"%self.name, cmdsetobj=self)
        cmdset.duplicates = None
        cmdset.priority = 10
        cmd = CmdListFiles(key="ls")
        cmdset.add(cmd)
        cmdset.add(CmdLook)
        self.cmdset.add(cmdset)

    def at_object_leave(self, obj, destination):
        if obj.name == ".GARBAGE":
            obj.locks.add("view:all()")