from mpf.core.rgb_color import RGBColor
from mpf.tests.MpfMachineTestCase import MpfMachineTestCase
from mpfmc.tests.FullMpfMachineTestCase import FullMachineTestCase


class TestBnd(MpfMachineTestCase):

    def get_platform(self):
        return 'smart_virtual'

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
        self.mock_event('world_tour_success')
        self.mock_event('world_tour_fail')
        self.mock_event('add_time')
        self.mock_event('wt_australia_complete')

        self._start_single_player_game(1)
        self.assertEqual(self.machine.achievements.world_tour.state, 'enabled')

        self.assertModeRunning('light_mission_select')

        # shoot the right ramp
        self.hit_and_release_switch('s_rightrampopto')
        self.assertModeRunning('mission_rotator')

        # # hit the sling until world tour is lit
        x = 0
        while self.machine.achievements.world_tour.state != 'selected':

            if x > 5:
                raise AssertionError("Mode failed to be selected")

            x += 1
            self.hit_and_release_switch('s_rightsling')
            self.advance_time_and_run()

        self.assertModeNotRunning('world_tour')

        # shoot the lower vuk to start the mode
        self.mock_event('shot_lower_vuk_from_playfield_hit')
        self.hit_switch_and_run('s_lowervukopto', 1)
        self.assertEventCalled('shot_lower_vuk_from_playfield_hit')

        self.assertEqual(self.machine.achievements.world_tour.state, 'started')

        # advance enough time for it to kick the ball out
        self.advance_time_and_run(3)

        self.assertModeRunning('world_tour')

        self.assertLedColors('l_north_america', ['red', 'off'], 1)

        self.assertEqual(self.get_timer('world_tour_timer').ticks_remaining, 19)

        self.hit_and_release_switch('s_leftorbit')

        self.assertLedColors('l_north_america', ['off'], 1)
        self.assertLedColors('l_europe', ['red', 'off'], 1)

        # make sure it added more time
        self.assertEventCalled('add_time')

        self.mock_event('light_mission_select')

        # drain ball and start again
        self.hit_switch_and_run('s_drain', 3)
        self.assertEqual(self.machine.game.player.ball, 2)

        self.assertModeRunning('base')
        self.assertEventCalled('light_mission_select')

        # launch ball
        self.release_switch_and_run('s_plungerlane', 3)

        self.assertModeNotRunning('world_tour')
        self.assertEventNotCalled('world_tour_success')

        # check the ramp light is flashing
        self.assertLedColors('l_ramp_fire', ['white', 'off'], 1)
        self.assertModeRunning('light_mission_select')

        # hit the ramp
        self.mock_event('enable_mission_selection')
        self.assertModeRunning('mission_rotator')
        self.hit_and_release_switch('s_rightrampopto')
        self.advance_time_and_run(1)
        self.assertEventCalled('enable_mission_selection')
        self.assertModeNotRunning('light_mission_select')

        print(self.machine.achievements.world_tour.state)
        self.assertNotEqual(self.machine.achievements.world_tour.state, 'completed')

        # # hit the sling until world tour is lit
        x = 0
        while self.machine.achievements.world_tour.state != 'selected':

            if x > 5:
                raise AssertionError("Mode failed to be selected")

            x += 1
            self.hit_and_release_switch('s_rightsling')
            self.advance_time_and_run()

        # make sure the LED is flashing
        self.assertLedColors('l_world_tour', ['red', 'off'], 1)

        # shoot the lower vuk to start the mode
        self.hit_switch_and_run('s_lowervukopto', 1)

        # make sure the mode is running
        self.assertModeRunning('world_tour')
        self.assertEqual(self.machine.achievements.world_tour.state, 'started')

        # and the light is still flashing
        self.assertLedColors('l_world_tour', ['red', 'off'], 1)

        # ramp light should be off
        self.assertLedColor('l_ramp_fire', 'off')

        self.assertEqual(self.get_timer('wt_intro_timer').ticks_remaining, 1)
        self.assertEqual(self.get_timer('world_tour_timer').ticks_remaining, 0)

        # make sure we picked up where we left off
        self.assertLedColor('l_north_america', 'red')
        self.assertLedColors('l_europe', ['red', 'off'], 1)
        self.assertLedColor('l_south_america', 'off')
        self.assertLedColor('l_australia', 'off')

        # advance past the intro and into the countdown
        self.advance_time_and_run(5)

        # ball should be ejected
        self.assertEqual(self.machine.ball_devices.bd_lower_vuk.balls, 0)

        self.assertEqual(self.get_timer('world_tour_timer').ticks_remaining, 16)
        self.advance_time_and_run(1.25)  # this is the tick interval
        self.assertEqual(self.get_timer('world_tour_timer').ticks_remaining, 15)

        # hit complete shot and it should not change anything
        self.hit_and_release_switch('s_leftorbit')
        self.advance_time_and_run(1.25)
        self.assertLedColor('l_north_america', 'red')
        self.assertLedColors('l_europe', ['red', 'off'], 1)
        self.assertLedColor('l_south_america', 'off')
        self.assertLedColor('l_australia', 'off')
        self.assertEqual(self.get_timer('world_tour_timer').ticks_remaining, 14)

        # hit unlit shot and nothing should change
        self.hit_and_release_switch('s_rightrampopto')
        self.advance_time_and_run(1.25)
        self.assertLedColor('l_north_america', 'red')
        self.assertLedColors('l_europe', ['red', 'off'], 1)
        self.assertLedColor('l_south_america', 'off')
        self.assertLedColor('l_australia', 'off')
        self.assertEqual(self.get_timer('world_tour_timer').ticks_remaining, 12)

        # hit europe
        self.hit_and_release_switch('s_spinner')
        self.advance_time_and_run(1)
        self.hit_switch_and_run('s_TopRightVUK', 2)  # have to wait for show to end
        self.assertLedColor('l_north_america', 'red')
        self.assertLedColor('l_europe', 'red')
        self.assertLedColors('l_south_america', ['red', 'off'], 1)
        self.assertLedColor('l_australia', 'off')
        self.assertEqual(self.get_timer('world_tour_timer').ticks_remaining, 12)

        # ball should be ejected
        self.assertEqual(self.machine.ball_devices.bd_top_right_vuk.balls, 0)

        # hit south america
        self.mock_event('wt_south_america_complete')
        self.hit_and_release_switch('s_rightrampopto')
        self.advance_time_and_run(3)  # give it time for the show to run

        self.assertEventCalled('wt_south_america_complete')

        self.assertLedColor('l_north_america', 'red')
        self.assertLedColor('l_europe', 'red')
        self.assertLedColor('l_south_america', 'red')
        self.assertLedColors('l_australia', ['red', 'off'], 1)
        self.assertEqual(self.get_timer('world_tour_timer').ticks_remaining, 11)

        self.assertEqual(self.machine.ball_devices.bd_top_right_vuk.balls, 0)

        # hit australia
        self.hit_switch_and_run('s_TopRightVUK', 2) # have to wait for show to end
        self.assertEventCalled('wt_australia_complete')
        self.assertLedColor('l_north_america', 'red')
        self.assertLedColor('l_europe', 'red')
        self.assertLedColor('l_south_america', 'red')
        self.assertLedColor('l_australia', 'red')

        # should eject ball and end mode
        self.advance_time_and_run(6)
        self.assertEqual(self.machine.ball_devices.bd_top_right_vuk.balls, 0)
        self.assertModeNotRunning('world_tour')
        self.assertLedColor('l_world_tour', 'red')

        # light next mission should be flashing
        self.assertLedColors('l_ramp_fire', ['white', 'off'], 1)

        # rotating should keep world tour complete

        for x in range(5):
            self.hit_and_release_switch('s_rightsling')
            self.assertLedColors('l_world_tour', ['red'], 1)
            self.assertEqual(self.machine.achievements.world_tour.state, 'completed')

    def test_jukebox_mode(self):
        self._start_single_player_game(1)
        self.assertEqual(self.machine.achievements.jukebox.state, 'enabled')

        # shoot the right ramp
        self.hit_and_release_switch('s_rightrampopto')

        # # hit the sling until world tour is lit
        x = 0
        while self.machine.achievements.jukebox.state != 'selected':

            if x > 5:
                raise AssertionError("Mode failed to be selected")

            x += 1
            self.hit_and_release_switch('s_rightsling')
            self.advance_time_and_run()

        self.assertModeNotRunning('jukebox_mode')

        # shoot the lower vuk to start the mode
        self.hit_switch_and_run('s_lowervukopto', 1)

        # make sure the timer is running
        self.assertEqual(self.machine.achievements.jukebox.state, 'started')
        self.assertEqual(self.get_timer('jb_intro_timer').ticks_remaining, 2)
        self.advance_time_and_run(1)
        self.assertEqual(self.get_timer('jb_intro_timer').ticks_remaining, 1)

        # advance enough time for it to kick the ball out
        self.advance_time_and_run(2)

        self.assertModeRunning('jukebox_mode')

        # make sure the timer is running
        self.assertEqual(self.get_timer('jukebox_mode_timer').ticks_remaining, 10)
        self.advance_time_and_run(1.25)
        self.assertEqual(self.get_timer('jukebox_mode_timer').ticks_remaining, 9)
        self.advance_time_and_run(1.25)
        self.assertEqual(self.get_timer('jukebox_mode_timer').ticks_remaining, 8)

        # shoot the lower vuk and make sure it ejects the ball
        self.hit_switch_and_run('s_lowervukopto', 2)
        self.assertEqual(self.machine.ball_devices.bd_lower_vuk.balls, 0)

        self.assertEqual(self.get_timer('jukebox_mode_timer').ticks_remaining, 6)

        # shoot the jukebox
        self.hit_and_release_switch('s_jukeboxopto')
        self.assertEqual(self.get_timer('jukebox_mode_timer').ticks_remaining, 9)
