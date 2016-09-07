"""Test scriptlet identify lights"""
from collections import deque
from mpf.system.scriptlet import Scriptlet
import thread

class LightTest(Scriptlet):
    def on_load(self):
        #self.config_name = None
        #led_config_file = open("leds.txt", "w") # to create a new file for writing
        self.led_list = deque(sorted(self.machine.leds, key=lambda x: x.config['number']))
        #self.led_list = deque(sorted(self.machine.leds, key=lambda x: int(x.config['number_str'].split('-')[1])))
        self.lednum = 0
        self.machine.events.add_handler('s_leftflipper_active', self.step_down)
        self.machine.events.add_handler('s_rightflipper_active', self.step_up)
        open("led_list.txt", 'w')

    def step_down(self):
        self.turn_off_led()
        self.led_list.rotate(1)
        self.light_led()

    def step_up(self):
        self.turn_off_led()
        self.led_list.rotate(-1)
        self.light_led()

    def turn_off_led(self):
        self.led_list[0].off()

    def light_led(self):
        self.led_list[0].on()
        thread.start_new_thread(self.collect_input, ())

    def collect_input(self):
        config_name = raw_input('Light name:')
        print("l_" + config_name)
        with open("led_list.txt", 'a+') as f:
            f.write("l_" + (config_name.lower()) + ":\n")
            f.write("    number: " + self.led_list[0].config['number_str'] + "\n")


