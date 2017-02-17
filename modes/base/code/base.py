from mpf.core.mode import Mode

class Base(Mode):
    def mode_init(self):
        self.add_mode_event_handler('jukebox_hit', self.jukebox_manager)

    def jukebox_manager(self, count, **kwargs):
        if count == 3:
            self.machine.events.post('light_lock_1')
        elif count == 8:
            self.machine.events.post('light_hilo')
        elif count == 16:
            self.machine.events.post('light_lock_2')
        elif count == 2: #24:
            self.machine.events.post('light_jukebox_hurryup')
        elif count == 36:
            self.machine.events.post('light_lock_3')
        elif count == 48:
            self.machine.events.post('light_hilo')
        elif count == 64:
            self.machine.events.post('light_jukebox_hurryup')
        elif count == 99:
            self.machine.events.post('jukebox_double_score_mode')
        else:
            pass

