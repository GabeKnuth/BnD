from collections import namedtuple

from mpf.core.scriptlet import Scriptlet

Card = namedtuple('Card', ['asset', 'value_name', 'value', 'suit'])

class Cards(Scriptlet):

    def on_load(self):
        cards = list()

        value_map = dict(ace=14, king=13, queen=12, jack=11, ten=10, nine=9,
                         eight=8, seven=7, six=6, five=5, four=4, three=3,
                         two=2)

        for suit in ('clubs', 'hearts', 'diamonds', 'spades'):
            for value_name, value in value_map.items():
                cards.append(Card('{}_{}'.format(value_name, suit), value_name,
                             value, suit))

        self.machine.card_deck = cards
