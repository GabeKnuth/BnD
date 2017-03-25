from mpf.core.mode import Mode
from random import choice

class Base(Mode):

    def mode_start(self, **kwargs):
        del kwargs
        self.add_mode_event_handler('hit_jukebox', self.evaluate)

    def evaluate(self, count, **kwargs):
        if count%8==0:
            self.machine.events.post('start_light_lock')

            # This keeps going forever, and we don't have to have lots of lines
            # in config to keep it going. That way the jukebox hit counter is
            # always building towards something, even if we stopped doing HiLo
            # and the HurryUp a long time ago. I kind of like this for all of
            # those events, but this is good for now.

