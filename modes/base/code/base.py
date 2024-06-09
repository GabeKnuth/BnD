from mpf.core.mode import Mode
from random import choice

class Base(Mode):

    def mode_start(self, **kwargs):
        del kwargs
        self.check_for_hold_multiplier()

    def check_for_hold_multiplier(self, **kwargs):
        """
        Checks for a hold multiplier in the player object and updates the player's multiplier accordingly.
        """
        if self.player.hold_multiplier == 1:
            self.player.multiplier = self.player.temp_multiplier
        else:
            self.player.multiplier = 1
            self.machine.events.post('reset_album_lights')
        self.player.temp_multiplier = 1
        self.player.hold_multiplier = 0
        

