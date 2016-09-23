
import logging
from mpf.core.scriptlet import Scriptlet


class Trough(Scriptlet):

    def on_load(self):

        self.log = logging.getLogger('Trough Scriptlet')

        self.log.info("Loading...")

        self.machine.events.add_handler(
            'balldevice_bd_trough_ball_eject_success', self._eject)
        self.machine.events.add_handler(
            'balldevice_bd_drain_ball_enter', self._eject)

        self.machine.clock.schedule_once(self._eject, 1)

    def _eject(self, *args, **kwargs):

        self.log.info("Eject callback. Drain balls: %s, Trough balls: %s",
                      self.machine.ball_devices.bd_trough.balls,
                      self.machine.ball_devices.bd_drain.balls)

        if (self.machine.ball_devices.bd_trough.balls < 3 and
                self.machine.ball_devices.bd_drain.balls):

            self.log.info("Ejecting ball from trough")
            self.machine.ball_devices.bd_drain.eject(
                target=self.machine.ball_devices.bd_trough)
