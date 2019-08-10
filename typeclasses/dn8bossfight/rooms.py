from typeclasses.rooms import Room
from twisted.internet import reactor
from evennia.utils import search
import time

def debug(msg):
    search.objects("loki")[0].msg(msg)
    # pass
def say_soon(location, msg):
    def say(location, msg):
        location.msg_contents(msg)
    reactor.callLater(0, say, location, msg)

class Entrance(Room):
    pass

class Jail(Room):
    JAIL_SENTENCES = [1,2,3,7,11,13,17]
    def at_object_creation(self):
        self.db.next_jail_sentence_index = 0

    def at_object_receive(self, obj, source_location):
        debug("new prisoner! %s from %s" % (obj, source_location))
        def welcome(obj):
            obj.msg("Welcome to quarantine! We hope you enjoy your stay.")
        reactor.callLater(0, welcome, obj)

        obj.db.imprisoned_time = time.time()
        obj.db.jail_sentence = Jail.JAIL_SENTENCES[self.db.next_jail_sentence_index] * 60
        search.channels("Public")[0].msg("|r%s was put in quarantine for %d minutes."%(obj.name, obj.db.jail_sentence/60))
        if self.db.next_jail_sentence_index + 1 < len(Jail.JAIL_SENTENCES):
            self.db.next_jail_sentence_index = self.db.next_jail_sentence_index + 1

        self.set_release_timer(obj)

    def set_release_timer(self, obj):
        if hasattr(obj.db, 'imprisoned_time') and hasattr(obj.db, 'jail_sentence'):
            self.cleanup_release_timer(obj)

            delay = obj.db.imprisoned_time + obj.db.jail_sentence - time.time()
            if delay <= 0:
                debug("scheduled release for %s has already passed" % (str(obj)))
                self.release(obj)
            else:
                debug("scheduling release of %s for %f seconds in the future" % (str(obj), delay))
                obj.ndb.jail_release_timer = reactor.callLater(delay, self.release, obj)

    def cleanup_release_timer(self, obj):
        if hasattr(obj.ndb, 'jail_release_timer'):
            if obj.ndb.jail_release_timer is not None and obj.ndb.jail_release_timer.active():
                obj.ndb.jail_release_timer.cancel()
            del obj.ndb.jail_release_timer
        

    def release(self, obj):
        debug("releasing %s from jail" % str(obj))
        # TODO sanity check: confirm in jail

        if hasattr(obj.db, 'imprisoned_time'):
            del obj.db.imprisoned_time
        if hasattr(obj.db, 'jail_sentence'):
            del obj.db.jail_sentence
        self.cleanup_release_timer(obj)

        entrance = self.search("dn8bossfight#entrance", global_search=True)
        obj.move_to(entrance)
        debug("%s released" % (str(obj)))

    def at_server_reload(self):
        debug("cancelling jail timers before reload")
        # Cancel all the timers so we don't attempt to release during a reload
        for obj in self.contents:
            self.cleanup_release_timer(obj)

    def at_init(self):
        # Defer modifying state to prevent strange race conditions caused by lazy loading
        def start_timers(self):
            debug("refreshing jail release timers")
            for obj in self.contents:
                self.set_release_timer(obj)
        reactor.callLater(0, start_timers, self)
        

    def return_appearance(self, looker):
        appearance = super(Jail, self).return_appearance(looker)

        obj = looker
        if hasattr(obj.db, 'imprisoned_time') and hasattr(obj.db, 'jail_sentence'):
            delay = (obj.db.imprisoned_time or 0) + (obj.db.jail_sentence or 0) - time.time()
            if delay <= 0:
                # Bug state
                remaining_sentence = "You are improperly quarantined. You should contact @mansel."
            else:
                remaining_sentence = "You have %.0f seconds remaining in your quarantine." % delay
        else:
            # Bug state
            remaining_sentence = "You are improperly quarantined. You should contact @mansel."

        appearance = appearance + "\n" + remaining_sentence
        return appearance
