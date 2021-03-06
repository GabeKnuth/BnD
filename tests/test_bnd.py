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
        self.assertEqual(self.machine.ball_controller.num_balls_known, 4)

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
            self.assertEqual(RGBColor('ff9027'),
                led.get_color())

        # make sure the attract mode shows are running

    def _start_single_player_game(self, secs_since_plunge):
        self.set_num_balls_known(4)
        self.machine.playfield.ball_search.disable()
        self.advance_time_and_run(10)
        self.hit_and_release_switch('s_start')

        # game should be running
        self.assertIsNotNone(self.machine.game)
        self.assertEqual(1, self.machine.game.player.ball)

        # advance enough time for the balls to eject and stuff
        self.advance_time_and_run(2)

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

    def test_mission_rotator(self):
        self._start_single_player_game(1)

        # no missions should be selected, all should be enabled

        selected = [x for x in
                    self.machine.achievement_groups.missions.config['achievements']
                    if x.state == 'selected']

        enabled = [x for x in
                   self.machine.achievement_groups.missions.config['achievements']
                   if x.state == 'enabled']

        self.assertEqual(len(selected), 0)
        self.assertEqual(len(enabled), 5)

        self.hit_and_release_switch('s_rightrampopto')

        # one of the missions should be selected

        selected = [x for x in
                    self.machine.achievement_groups.missions.config['achievements']
                    if x.state == 'selected']

        enabled = [x for x in
                   self.machine.achievement_groups.missions.config['achievements']
                   if x.state == 'enabled']

        self.assertEqual(len(selected), 1)  # should be 1 selected
        self.assertEqual(len(enabled), 4)  # and 4 enabled

        selected = selected[0]

        # selected one should be flashing between its default color and off
        self.assertLedColors(selected.config['show_tokens']['leds'], ['on', 'off'])

        # enabled ones should be off
        for x in enabled:
            self.assertLedColor(x.config['show_tokens']['leds'], 'off')

        # begin round should be off
        self.assertLedColor('l_begin_round', 'off')

        # light mission select should be running on ball start
        self.assertModeRunning('light_mission_select')

        # its light should be flashing
        self.assertLedColors('l_ramp_fire', ['on', 'off'])

        # hit the ramp
        self.hit_and_release_switch('s_rightrampopto')

        # ramp light should be off
        self.assertLedColor('l_ramp_fire', 'off')

        # begin round should be flashing
        self.assertLedColors('l_begin_round', ['on', 'off'])
        self.assertShotProfile('begin_round', 'begin_round')
        self.assertShotProfileState('begin_round', 'lit')

        # shoot the lower vuk to start the mode
        self.hit_switch_and_run('s_LowerVUKOpto', 1)
        self.assertEqual(selected.state, 'started')

        # begin round should be off
        self.assertLedColor('l_begin_round', 'off')

        # the rotator should be disabled
        self.assertFalse(self.machine.achievement_groups.missions.enabled)

        # wait for this mode to timeout:
        while selected.state == 'started':
            self.advance_time_and_run(5)

        # modes just go to 'enabled' if they fail, and one should be selected
        # again

        # the rotator should be enabled
        self.assertTrue(self.machine.achievement_groups.missions.enabled)

        selected = [x for x in
                    self.machine.achievement_groups.missions.config['achievements']
                    if x.state == 'selected']

        enabled = [x for x in
                  self.machine.achievement_groups.missions.config['achievements']
                  if x.state == 'enabled']

        self.assertEqual(len(selected), 1)  # should be 1 selected
        self.assertEqual(len(enabled), 4)  # and 4 enabled

        selected = selected[0]

        # let's get the selected one to world_tour:
        while self.machine.achievements.world_tour.state != 'selected':
            self.hit_and_release_switch('s_rightsling')

        self.assertEqual(self.machine.achievements.world_tour.state, 'selected')
        self.assertEqual(self.machine.achievements.money_bags.state, 'enabled')
        self.assertEqual(self.machine.achievements.music_awards.state, 'enabled')
        self.assertEqual(self.machine.achievements.jukebox.state, 'enabled')
        self.assertEqual(self.machine.achievements.play_poker.state, 'enabled')

        self.hit_and_release_switch('s_rightsling')
        self.assertEqual(self.machine.achievements.world_tour.state, 'enabled')
        self.assertEqual(self.machine.achievements.money_bags.state, 'selected')
        self.assertEqual(self.machine.achievements.music_awards.state, 'enabled')
        self.assertEqual(self.machine.achievements.jukebox.state, 'enabled')
        self.assertEqual(self.machine.achievements.play_poker.state, 'enabled')

        self.assertLedColor('l_world_tour', 'off')
        self.assertLedColors('l_money_bags', ['on', 'off'])
        self.assertLedColor('l_music_awards', 'off')
        self.assertLedColor('l_jukebox_insert', 'off')
        self.assertLedColor('l_play_poker', 'off')

    def test_world_tour(self):
        self.mock_event('world_tour_success')
        self.mock_event('world_tour_fail')
        self.mock_event('add_time')
        self.mock_event('wt_australia_complete')

        self._start_single_player_game(1)

        self.assertModeRunning('light_mission_select')

        # shoot the right ramp
        self.hit_and_release_switch('s_rightrampopto')
        self.assertShotProfile('begin_round', 'begin_round')
        self.assertShotProfileState('begin_round', 'lit')

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
        self.mock_event('begin_round_lit_hit')
        self.hit_switch_and_run('s_lowervukopto', 1)
        self.assertEventCalled('begin_round_lit_hit')

        self.assertEqual(self.machine.achievements.world_tour.state, 'started')
        self.assertFalse(self.machine.achievement_groups.missions.enabled)

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
        self.assertLedColors('l_ramp_fire', ['red', 'off'], 1)
        self.assertModeRunning('light_mission_select')

        # hit the ramp
        self.mock_event('enable_mission_selection')
        self.assertModeRunning('mission_rotator')
        self.hit_and_release_switch('s_rightrampopto')
        self.advance_time_and_run(1)
        self.assertEventCalled('enable_mission_selection')

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

        self.assertEqual(self.get_timer('wt_intro_timer').ticks_remaining, 2)
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

        self.assertEqual(self.get_timer('world_tour_timer').ticks_remaining, 17)
        self.advance_time_and_run(1.25)  # this is the tick interval
        self.assertEqual(self.get_timer('world_tour_timer').ticks_remaining, 16)

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
        self.assertEqual(self.get_timer('world_tour_timer').ticks_remaining, 12)

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
        self.assertLedColors('l_ramp_fire', ['red', 'off'], 1)

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

        # # hit the sling until jukebox is lit
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
        self.assertEqual(self.machine.achievements.jukebox.state, 'started')
        self.assertModeRunning('jukebox_mode')

        # intro show should be playing
        self.assertShowRunning('jukebox_intro')

        # advance enough time for the show to end
        self.advance_time_and_run(5)

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

    def test_play_poker_mode(self):
        self._start_single_player_game(1)

        self.assertEqual(self.machine.achievements.play_poker.state, 'enabled')

        # shoot the right ramp to light the rotator
        self.hit_and_release_switch('s_rightrampopto')

        # # hit the sling until play_poker is lit
        x = 0
        while self.machine.achievements.play_poker.state != 'selected':

            if x > 5:
                raise AssertionError("Mode failed to be selected")

            x += 1
            self.hit_and_release_switch('s_rightsling')
            self.advance_time_and_run()

        self.assertModeNotRunning('play_poker')

        # shoot the lower vuk to start the mode
        self.hit_switch_and_run('s_lowervukopto', .1)

        # make sure the mode started
        self.assertModeRunning('play_poker')

        # there should be a 5s show
        self.assertShowRunning('play_poker_intro')

        # meanwhile make sure the ball is still locked

        self.advance_time_and_run(3)
        self.assertEqual(self.machine.ball_devices.bd_lower_vuk.balls, 1)

        # advanced to when show should be over and ball is ejected
        self.advance_time_and_run(3)
        self.assertShowNotRunning('play_poker_intro')
        self.assertEqual(self.machine.ball_devices.bd_lower_vuk.balls, 0)

    def test_bonus(self):

        self.mock_event('bonus_start')
        self.mock_event('quarter_bonus')
        self.mock_event('wizard_bonus')
        self.mock_event('bonus_total')

        self._start_single_player_game(5)

        self.machine.game.player.quarters = 2
        self.machine.game.player.album_value = 250000
        self.machine.game.player.num_albums = 2

        self.hit_switch_and_run('s_drain', 1)
        self.assertModeRunning('bonus')

        self.assertEventCalled('bonus_start')
        self.assertEventNotCalled('quarter_bonus')
        self.assertEventNotCalled('wizard_bonus')
        self.assertEventNotCalled('bonus_total')

        self.advance_time_and_run(2)
        self.assertEventCalled('quarter_bonus')
        self.assertEventNotCalled('wizard_bonus')
        self.assertEventNotCalled('bonus_total')

        self.advance_time_and_run(2)
        self.assertEventCalled('wizard_bonus')
        self.assertEventNotCalled('bonus_total')

        self.advance_time_and_run(2)
        self.assertEventCalled('bonus_total')

        # (2 quarters * 250k album value) + (25k * 2 albums)
        self.assertEqual(self.machine.game.player.score, 550000)

        self.advance_time_and_run(2)
        self.assertModeNotRunning('bonus')

    def test_ball_search(self):
        self._start_single_player_game(5)

        self.advance_time_and_run(30)

    def test_money_bags(self):
        self._start_single_player_game(5)

        self.machine.events.post('start_money_bags_mode')
        self.advance_time_and_run(1)

        self.assertLedColors('l_left_longhorn', ['off'])
        self.assertLedColors('l_center_longhorn', ['off', 'on'])

        self.hit_and_release_switch('s_spinner')
        self.advance_time_and_run(1)
        self.hit_switch_and_run('s_toprightvuk', .1)
        self.assertLedColors('l_left_longhorn', ['off', 'on'])
        self.assertLedColors('l_center_longhorn', ['off'])

        self.hit_and_release_switch('s_bottomkickingtarget')
        self.advance_time_and_run(2)

        self.assertLedColors('l_left_longhorn', ['off'])
        self.assertLedColors('l_center_longhorn', ['off', 'on'])

        self.hit_and_release_switch('s_spinner')
        self.advance_time_and_run(1)
        self.hit_switch_and_run('s_toprightvuk', 2)

        self.assertLedColors('l_left_longhorn', ['off', 'on'])
        self.assertLedColors('l_center_longhorn', ['off'])
