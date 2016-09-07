from mpf.core.rgb_color import RGBColor
from mpf.tests.MpfMachineTestCase import MpfMachineTestCase


class TestBnD(MpfMachineTestCase):

    def test_bnd(self):
        # make sure attract mode is running
        self.assertTrue(self.machine.modes['attract'].active)

        self.advance_time_and_run()

        # make sure the GI comes on
        self.assertEqual(RGBColor('66ff18'),
            self.machine.leds.l_gi_right_5.hw_driver.current_color)
