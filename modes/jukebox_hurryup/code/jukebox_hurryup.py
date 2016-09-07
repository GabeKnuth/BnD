from mpf.system.modes import Mode

class Jukebox_hurryup(Mode):

    def mode_init(self):
        #self.jukebox_score = 1000000
        self.add_mode_event_handler('timer_jukebox_timer_tick',
                                    self.score_change)
        self.add_mode_event_handler('reset_jukebox_hurryup',
                                    self.reset_jukebox_hurryup)
        self.add_mode_event_Handler('sw_jukebox', self.score_value)
        self.reset_jukebox_hurryup(count=0)

    def reset_jukebox_hurryup(self, count, **kwargs):
        # score need to decrease each second. I can do this a few ways, but I
        # think the way to go is to take the score when it's reset and divide
        # it by 15, then subtract that at each timer tick. This method resets
        # the score.

        if count <= 1:
            self.jukebox_score = 1000000
        elif count == 2:
            self.jukebox_score = 2000000
        elif count >= 3:
            self.jukebox_score = 3000000

        self.maths()

    def maths(self):
        self.hit_score = self.jukebox_score
        self.decrease = self.jukebox_score // 15

    def score_change(self):
        self.hit_score = self.hit_score - self.decrease

    def score_value(self):
        # This method will add the points that are being displayed to the
        # user's score
        player.score += self.hit_score
