from mpf.core.mode import Mode
from random import choice

class Base(Mode):

    def mode_start(self, **kwargs):
        del kwargs
        self.check_for_hold_multiplier()

    def mode_stop(self, **kwargs):
        del kwargs
        self.clean_up_album_number()

    def check_for_hold_multiplier(self, **kwargs):
        """
        Checks for a hold multiplier in the player object and updates the player's multiplier accordingly.
        """
        if self.player.hold_multiplier == 1:
            self.player.multiplier = self.player.temp_multiplier
            self.player.album_value = self.player.temp_album_value
            self.player.album_name = self.player.temp_album_name
        else:
            self.player.multiplier = 1
            self.player.album_value = None
            self.player.album_name = None
            self.machine.events.post('reset_album_lights')       
        # Clean-up
        self.player.temp_multiplier = 1
        self.player.temp_album_value = None
        self.player.temp_album_name = "INDY"
        self.player.hold_multiplier = 0

    def clean_up_album_number(self, **kwargs): # This is here because the number has to be cleaned up before bonus mode starts again
        if self.player.hold_multiplier != 1:
            self.player.temp_num_albums = 0
        
        

