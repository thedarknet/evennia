"""
Simple four-room puzzle inspired by the movie Hackers
Each room is an accounting database that commits transactions into the ledger as they appear
A worm is roaming around the rooms and will nibble a few cents off of each transaction that it sees
"""
from evennia import TICKER_HANDLER
from typeclasses.rooms import Room
from typeclasses.objects import Object
from typeclasses.scripts import Script
from evennia.utils import create, search
import random

def debug(msg):
    search.objects("loki")[0].msg(msg)

class Accounting(Room):
    """
    Watch for new transactions and commit them after COMMIT_TIME
    """
    COMMIT_TIME = 30
    def ticker_idstring(self, transaction):
        return "commit-tx-"+transaction.dbref

    def commit(self, transaction):
        TICKER_HANDLER.remove(interval=Accounting.COMMIT_TIME, callback=self.commit, idstring=self.ticker_idstring(transaction))
        ledger = next(x for x in self.contents if x.is_typeclass(AccountingLedger))
        if ledger is None:
            transaction.location.msg_contents("Error: unable to find a ledger to commit the transaction into...")
            return
        ledger.commit(transaction)

    def at_object_receive(self, obj, source_location):
        super(Accounting, self).at_object_receive(obj, source_location)
        if obj.is_typeclass(Transaction):
            TICKER_HANDLER.add(interval=Accounting.COMMIT_TIME, callback=self.commit, idstring=self.ticker_idstring(obj), transaction=obj)

    def at_object_leave(self, obj, target_location):
        super(Accounting, self).at_object_leave(obj, target_location)
        TICKER_HANDLER.remove(interval=Accounting.COMMIT_TIME, callback=self.commit, idstring=self.ticker_idstring(obj))

class AccountingLedger(Object):
    SIZE=2
    def transactions(self):
        if self.ndb.transactions is None:
            self.ndb.transactions = []
        return self.ndb.transactions

    def commit(self, transaction):
        self.transactions().append(transaction.db.txdetails)
        # only keep the last SIZE transactions
        if len(self.ndb.transactions) > AccountingLedger.SIZE:
            self.ndb.transactions = self.ndb.transactions[-1*AccountingLedger.SIZE:]
        transaction.location.msg_contents("Transaction committed to the ledger")
        transaction.delete()

    def return_appearance(self, looker):
        appearance = super(AccountingLedger, self).return_appearance(looker)
        txhistory = self.transactions()[::-1] #reversed; newest on top
        appearance = appearance + "\n\nLatest Transactions:\n"+"\n".join(txhistory)
        return appearance.strip()

class Transaction(Object):
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
                         attributes=[["txdetails", txdata]],
                         location=room, home=room,
                         )
        debug("new tx "+tx.dbref)

    def at_repeat(self):
        room = random.sample(self.db.rooms, 1)[0]
        debug("creating a new transaction in "+str(room)+" "+room.dbref+" (%d,%d)"%room.db.coordinates)
        if room:
            self.create_transaction(room)

class Worm(Object):
    def at_object_creation(self):
        self.db.balance = 0.0

    def nibble_transaction(self, obj):
        if obj.is_typeclass(Transaction) and "nibbled" not in obj.tags.all():
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

                self.location.msg_contents("%s nibbled a little bit off of %s" % (self.name, obj.name))

    def at_object_arrive(self, obj, source_location):
        # debug("worm saw something arrive: "+str(obj))
        # self.nibble_transaction(obj)
        pass

    def move_randomly(self, delay):
        # TICKER_HANDLER.remove(interval=delay, callback=self.move_randomly)
        randomized_exits = random.sample(self.location.exits, len(self.location.exits))
        exit = next(exit for exit in randomized_exits if exit.destination.is_typeclass(Accounting))
        if exit:
            debug("worm moving to "+exit.destination.dbref+" (%d,%d)"%exit.destination.db.coordinates)
            self.move_to(exit)
        else:
            debug("nowhere to go? "+str(randomized_exits))

    def at_after_move(self, source_location):
        # delay = round(random.random()*15+15) # 15-30seconds
        delay = 5
        TICKER_HANDLER.add(interval=delay, callback=self.move_randomly, delay=delay)
        for obj in self.location.contents:
            # debug("worm examining objects on arrival: "+str(obj))
            self.nibble_transaction(obj)

