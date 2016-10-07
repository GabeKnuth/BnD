from mpf.core.mode import Mode

class Jukebox_Mode(Mode):
    def mode_init(self):
        self.videos = [jb_9_to_5, jb_achy_breaky, jb_convoy,
                       jb_every_little_thing, jb_feel_like_a_woman,
                       jb_hello_darlin, jb_louisiana_woman,
                       jb_rhinestone_cowboy, jb_stand_by_your_man]

        self.add_mode_event_handler('jukebox_mode_hit_counter_hit', self.event_poster)

    def event_poster(self, count, **kwargs):
        if count >= 2:
            self.machine.events.post('play_scratch')
        else:
            pass

