from mpf.core.rgb_color import RGBColor
from mpf.tests.MpfMachineTestCase import MpfMachineTestCase
from mpfmc.tests.FullMpfMachineTestCase import FullMachineTestCase


class TestBnd(MpfMachineTestCase):

    def test_machine_boot(self):

        # game starts with drain and trough switches active
        # let's make sure the counts are right

        self.assertEqual(self.machine.ball_devices.bd_drain.balls, 1)
        self.assertEqual(self.machine.ball_devices.bd_trough.balls, 3)
        self.assertEqual(self.machine.ball_devices.bd_plunger.balls, 0)

        # advance 1 sec and make sure everything is still right
        # this checks for the trough kicking out a ball and the plunger
        # auto-plunging it?
        self.advance_time_and_run(1)

        self.assertEqual(self.machine.ball_devices.bd_drain.balls, 1)
        self.assertEqual(self.machine.ball_devices.bd_trough.balls, 3)
        self.assertEqual(self.machine.ball_devices.bd_plunger.balls, 0)

        self.advance_time_and_run(10)

        self.assertEqual(self.machine.ball_devices.bd_drain.balls, 1)
        self.assertEqual(self.machine.ball_devices.bd_trough.balls, 3)
        self.assertEqual(self.machine.ball_devices.bd_plunger.balls, 0)

    def test_attract_mode(self):
        # make sure attract mode is running
        self.assertTrue(self.machine.modes['attract'].active)

        # make sure the GI comes on
        for led in self.machine.leds.items_tagged('gi'):
            self.assertEqual(RGBColor('ff6618'),
                led.hw_driver.current_color)

        # make sure the attract mode shows are running

    def _dump_balls(self):
        print('-------------')
        print('drain:    ', self.machine.ball_devices.bd_drain.balls)
        print('trough:   ', self.machine.ball_devices.bd_trough.balls)
        print('plunger:  ', self.machine.ball_devices.bd_plunger.balls)
        print('playfield:', self.machine.ball_devices.playfield.balls)

    def _start_single_player_game(self, secs_since_plunge):
        self.hit_and_release_switch('s_start')

        # game should be running
        self.assertIsNotNone(self.machine.game)
        self.assertEqual(1, self.machine.game.player.ball)

        # advance enough time for the balls to eject and stuff
        self.advance_time_and_run()

        # ball should be sitting in the plunger lane
        self.assertEqual(self.machine.ball_devices.bd_drain.balls, 0)
        self.assertEqual(self.machine.ball_devices.bd_trough.balls, 3)
        self.assertEqual(self.machine.ball_devices.bd_plunger.balls, 1)

        # playfield expects a ball
        self.assertEqual(1, self.machine.playfield.available_balls)

        # but its not there yet
        self.assertEqual(0, self.machine.playfield.balls)

        # after 20s it's still not there
        self.advance_time_and_run(20)
        self.assertEqual(0, self.machine.playfield.balls)

        # player mechanically ejects
        self.machine.switch_controller.process_switch('s_plungerlane', 0, True)
        self.advance_time_and_run(secs_since_plunge)  # plunger timeout is 3s

    def test_single_player_game_start(self):
        self._start_single_player_game(4)

        # 4 secs since plunge means ball is on the pf
        self.assertEqual(1, self.machine.playfield.balls)
        self.assertEqual(self.machine.ball_devices.bd_drain.balls, 0)
        self.assertEqual(self.machine.ball_devices.bd_trough.balls, 3)
        self.assertEqual(self.machine.ball_devices.bd_plunger.balls, 0)

    def test_ball_fails_to_plunge(self):
        self._start_single_player_game(1)

        # ball lands back on the plunger
        self.hit_switch_and_run('s_plungerlane', 1)

        self.assertEqual(0, self.machine.playfield.balls)
        self.assertEqual(self.machine.ball_devices.bd_drain.balls, 0)
        self.assertEqual(self.machine.ball_devices.bd_trough.balls, 3)

        # ball is not added back to the plunger count. Need to figure out a
        # test for this.
        # self.assertEqual(self.machine.ball_devices.bd_plunger.balls, 1)

        # player tries to eject again and fails
        self.release_switch_and_run('s_plungerlane', 2)
        self.hit_switch_and_run('s_plungerlane', 1)
        self.assertEqual(0, self.machine.playfield.balls)

        # finally they get it
        self.release_switch_and_run('s_plungerlane', 3)
        self.assertEqual(1, self.machine.playfield.balls)

    def test_ball_launch_from_button(self):
        self.hit_and_release_switch('s_start')
        self.advance_time_and_run()
        self.assertEqual(self.machine.ball_devices.bd_plunger.balls, 1)

        self.hit_and_release_switch('s_launch')
        self.advance_time_and_run(4)  # plunger lane timeout is 3 secs

        self.assertFalse(self.machine.switch_controller.is_active(
            's_plungerlane'))

        self.assertEqual(self.machine.ball_devices.bd_plunger.balls, 0)
        self.assertEqual(1, self.machine.playfield.balls)

    def test_world_tour(self):
        self._start_single_player_game(1)

        # shot the right ramp
        self.hit_and_release_switch('s_rightrampopto')

        # hit the sling until world tour is lit
        while self.machine.leds.l_world_tour.hw_driver.current_color == [0, 0, 0]:
            self.hit_and_release_switch('s_rightsling')
            self.advance_time_and_run()

        self.assertFalse(self.machine.modes.world_tour.active)

        # shot the lower vuk to start the mode
        self.machine.switch_controller.process_switch('s_lowervukopto', logical=True)

        # advance enough time for it to kick the ball out
        self.advance_time_and_run(3)

        self.assertTrue(self.machine.modes.world_tour.active)

        # make sure the shots have the proper shows running
        self.assertEqual('flash',
            self.machine.shots.shot_north_america.profiles[0]['running_show'].name)
        self.assertIsNone(self.machine.shots.shot_europe.profiles[0]['running_show'])
        self.assertIsNone(self.machine.shots.shot_south_america.profiles[0]['running_show'])
        self.assertIsNone(self.machine.shots.shot_australia.profiles[0]['running_show'])

        # and the shots are enabled properly
        self.assertTrue(self.machine.shots.shot_north_america.enabled)
        self.assertFalse(self.machine.shots.shot_europe.enabled)
        self.assertFalse(self.machine.shots.shot_south_america.enabled)
        self.assertFalse(self.machine.shots.shot_australia.enabled)

        # hit north america
        self.hit_and_release_switch('s_leftorbit')

        self.assertIsNone(self.machine.shots.shot_north_america.profiles[0]['running_show'])
        self.assertEqual('flash',
            self.machine.shots.shot_europe.profiles[0]['running_show'].name)
        self.assertIsNone(self.machine.shots.shot_south_america.profiles[0]['running_show'])
        self.assertIsNone(self.machine.shots.shot_australia.profiles[0]['running_show'])

        self.assertFalse(self.machine.shots.shot_north_america.enabled)
        self.assertTrue(self.machine.shots.shot_europe.enabled)
        self.assertFalse(self.machine.shots.shot_south_america.enabled)
        self.assertFalse(self.machine.shots.shot_australia.enabled)

        # hit europe
        self.hit_and_release_switch('s_spinner')
        self.machine.switch_controller.process_switch('s_TopRightVUK', logical=True)
        self.advance_time_and_run(1)

        self.assertIsNone(self.machine.shots.shot_north_america.profiles[0]['running_show'])
        self.assertIsNone(self.machine.shots.shot_europe.profiles[0]['running_show'])
        self.assertEqual('flash',
            self.machine.shots.shot_south_america.profiles[0]['running_show'].name)
        self.assertIsNone(self.machine.shots.shot_australia.profiles[0]['running_show'])

        self.assertFalse(self.machine.shots.shot_north_america.enabled)
        self.assertFalse(self.machine.shots.shot_europe.enabled)
        self.assertTrue(self.machine.shots.shot_south_america.enabled)
        self.assertFalse(self.machine.shots.shot_australia.enabled)

        # hit south america
        self.hit_and_release_switch('s_rightrampopto')

        self.assertIsNone(self.machine.shots.shot_north_america.profiles[0]['running_show'])
        self.assertIsNone(self.machine.shots.shot_europe.profiles[0]['running_show'])
        self.assertIsNone(self.machine.shots.shot_south_america.profiles[0]['running_show'])
        self.assertEqual('flash',
            self.machine.shots.shot_australia.profiles[0]['running_show'].name)

        self.assertFalse(self.machine.shots.shot_north_america.enabled)
        self.assertFalse(self.machine.shots.shot_europe.enabled)
        self.assertFalse(self.machine.shots.shot_south_america.enabled)
        self.assertTrue(self.machine.shots.shot_australia.enabled)

        # hit autralia
        self.hit_switch_and_run('s_rightrampopto', 1)

        # todo now what?

# class TestBndFull(FullMachineTestCase):
#
#     def test_integrated_attract_mode(self):
#         pass
