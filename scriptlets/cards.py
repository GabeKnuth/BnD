from collections import namedtuple

from mpf.core.scriptlet import Scriptlet

Card = namedtuple('Card', ['asset', 'value_name', 'value', 'suit'])

class Cards(Scriptlet):

    def on_load(self):
        cards = list()

        value_map = dict(ACE=14, KING=13, QUEEN=12, JACK=11, TEN=10, NINE=9,
                         EIGHT=8, SEVEN=7, SIX=6, FIVE=5, FOUR=4, THREE=3,
                         TWO=2)

        for suit in ('clubs', 'hearts', 'diamonds', 'spades'):
            for value_name, value in value_map.items():
                cards.append(Card('{}_{}'.format(value_name, suit), value_name,
                             value, suit))

        self.machine.card_deck = cards
