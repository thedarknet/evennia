"""
Simple four-room puzzle inspired by the movie Hackers
Each room is an accounting database that commits transactions into the ledger as they appear
A worm is roaming around the rooms and will nibble a few cents off of each transaction that it sees
"""
from evennia import TICKER_HANDLER
from typeclasses.rooms import Room, Zone
from typeclasses.objects import Object
from typeclasses.characters import Character
from typeclasses.scripts import Script
from evennia.utils import create, search
import random
from twisted.internet import reactor

def debug(msg):
    # search.objects("loki")[0].msg(msg)
    pass
def say_soon(location, msg):
    def say(location, msg):
        location.msg_contents(msg)
    reactor.callLater(0, say, location, msg)

class Accounting(Room):
    """
    Watch for new transactions and commit them after COMMIT_TIME
    """
    COMMIT_TIME = 30

    def commit(self, transaction):
        ledger = next(x for x in self.contents if x.is_typeclass(AccountingLedger))
        if ledger is None:
            transaction.location.msg_contents("Error: unable to find a ledger to commit the transaction into...")
            return
        ledger.commit(transaction)

class AccountingLedger(Object):
    SIZE=2
    def transactions(self):
        if self.ndb.transactions is None:
            self.ndb.transactions = []
        return self.ndb.transactions

    def commit(self, transaction):
        self.transactions().append("#%d: %s"%(transaction.db.txid, transaction.db.txdetails))
        # only keep the last SIZE transactions
        if len(self.ndb.transactions) > AccountingLedger.SIZE:
            self.ndb.transactions = self.ndb.transactions[-1*AccountingLedger.SIZE:]
        transaction.location.msg_contents("Transaction #%d committed to the ledger"%(transaction.db.txid))
        transaction.delete()

    def return_appearance(self, looker):
        appearance = super(AccountingLedger, self).return_appearance(looker)
        txhistory = self.transactions()[::-1] #reversed; newest on top
        appearance = appearance + "\n\nLatest Transactions:\n"+"\n".join(txhistory)
        return appearance.strip()

class Transaction(Object):
    def wait_to_commit(self):
        if hasattr(self, 'timeout') and self.timeout is not None:
            self.timeout.cancel()
        if self.location.is_typeclass(Accounting):
            self.timeout = reactor.callLater(self.location.COMMIT_TIME, self.location.commit, self)

    def at_init(self):
        self.wait_to_commit()

    def at_after_move(self, source_location):
        self.wait_to_commit()

    def return_appearance(self, looker):
        appearance = super(Transaction, self).return_appearance(looker)
        appearance = appearance + "\n\nTransaction Data: " + self.db.txdetails
        return appearance.strip()

class TransactionFactory(Script):
    def at_script_creation(self):
        """
        Only called once, when the script is created. This is a default Evennia
        hook.
        """
        self.persistent = True
        self.interval = 15
        if self.db.rooms is None:
            self.db.rooms = []
        self.db.txid = 0

    def create_transaction(self, room):
        self.db.txid = self.db.txid+1
        amount = round(random.random()*100,2)
        sign = random.sample(["+","-"],1)[0]
        txdata = "%s$%0.2f" % (sign, amount)
        # debug("new transaction data "+txdata)
        tx = create.create_object(Transaction, key="transaction",
                         aliases=["transaction#%d"%(self.db.txid)],
                         attributes=[["txdetails", txdata], ["txid", self.db.txid]],
                         location=None, home=room,
                         )
        tx.move_to(room, quiet=True)
        room.msg_contents("A new transaction appeared (%d)"%(tx.db.txid))
        # debug("new tx "+tx.dbref)

    def at_repeat(self):
        room = random.sample(self.db.rooms, 1)[0]
        # debug("creating a new transaction in "+str(room)+" "+room.dbref+" (%d,%d)"%room.db.coordinates)
        if room:
            self.create_transaction(room)

class Worm(Object):
    def at_object_creation(self):
        self.db.balance = 0.0

    def nibble_transaction(self, obj):
        if obj.is_typeclass(Transaction) and "nibbled" not in obj.tags.all() and obj.location == self.location:
            # self.location.msg_contents("%s preparing to nibble a little bit off of %s (%s)" % (self.name, obj.name, obj.dbref))
            txdata = obj.db.txdetails
            if txdata is None:
                # Bad transaction
                self.location.msg_contents("destroying bad transaction %s" % (obj.dbref))
                search.objects("loki")[0].msg("destroying bad transaction %s" % (obj.dbref))
                # obj.delete()
                obj.move_to(search.objects("loki")[0])
                return
            oldval = float(txdata.split("$")[1])
            nibble_amount = round(random.random()/4, 2) # max $0.25
            if nibble_amount < oldval/10: # keep it quiet
                # make outgoing (negative) transactions larger (and keep the leftover)
                # make incoming (positive) transactions smaller (and keep the leftover)
                newval = oldval - nibble_amount

                # Commit the transfer
                obj.db.txdetails = txdata[0]+"$%0.2f"%(newval)
                self.db.balance = self.db.balance + nibble_amount
                obj.tags.add("nibbled")

                say_soon(self.location, "%s nibbled a little bit off of %s" % (self.name, obj.name))

    def at_object_arrive(self, obj, source_location):
        reactor.callLater(1, self.nibble_transaction, obj)

    def move_randomly(self):
        self.timeout = None
        randomized_exits = random.sample(self.location.exits, len(self.location.exits))
        exit = next(exit for exit in randomized_exits if exit.destination.is_typeclass(Accounting))
        if exit:
            debug("worm moving to "+exit.destination.dbref+" (%d,%d)"%exit.destination.db.coordinates)
            self.move_to(exit)
        else:
            debug("nowhere to go? "+str(randomized_exits))

    def at_after_move(self, source_location):
        self.wait_to_move()
        for obj in self.location.contents:
            # debug("worm examining objects on arrival: "+str(obj))
            self.nibble_transaction(obj)

    def at_init(self):
        self.wait_to_move()

    def wait_to_move(self):
        if hasattr(self, 'timeout') and self.timeout is not None:
            self.timeout.cancel()
        delay = round(random.random()*15+15) # 15-30seconds
        self.timeout = reactor.callLater(delay, self.move_randomly)

class Bird(Object):
    def at_object_creation(self):
        self.db.balance = 0

    def eat_worm(self, worm):
        debug("eat the worm")
        # eat the worm
        say_soon(worm.location, "%s gobbles up %s"%(self.name, worm.name))
        worm.move_to(self)
        self.db.balance = self.db.balance + worm.db.balance
        worm.db.balance = 0

    def at_desc(self, looker):
        if looker.is_typeclass(Character, exact=False):
            create.create_object(Object, key="money", attributes=[["desc","$%0.2f"%self.db.balance]], location=self.location, report_to=looker)
            say_soon(self.location, "%s drops money and flies away, never to be seen again"%(self.name))
            worm = next(obj for obj in self.contents if obj.is_typeclass(Worm))
            if worm is not None:
                worm.delete()
            self.delete()

    def at_object_arrive(self, obj, source_location):
        if self.location.is_typeclass(Room, exact=False) and obj.is_typeclass(Worm):
            self.eat_worm(obj)

    def at_after_move(self, source_location):
        if self.location.is_typeclass(Accounting, exact=False):
            # Look for the worm
            worm = next((obj for obj in self.location.contents if obj.is_typeclass(Worm)), None)
            if worm is not None:
                self.eat_worm(worm)
            else:
                # wait 5 seconds before hopping away
                debug("no worm; waiting 5s")
                self.timeout = reactor.callLater(5, self.hop_away)
        else:
            if hasattr(self, 'timeout') and self.timeout is not None:
                self.timeout.cancel()
                self.timeout = None

    def hop_away(self):
        # TODO fix the hardcoding
        def getroom(x,y):
            zone = search.objects('ZoneDN8BossFight', typeclass=Zone)[0]
            for obj in zone.contents:
                if obj.is_typeclass(Room, exact=False) and hasattr(obj.db, 'coordinates') and obj.db.coordinates[0] == x and obj.db.coordinates[1] == y:
                    return obj
            return None
        SIZE=(5,5)
        x = int(round(random.random()*SIZE[0]))
        y = int(round(random.random()*SIZE[1]))
        newroom = getroom(x,y)
        say_soon(self.location, "%s hops away to a new room"%(self.name))
        debug("bird moved to (%d,%d)"%(x,y))
        self.move_to(newroom, quiet=True)