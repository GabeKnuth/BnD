from mpf.core.mode import Mode
from random import choice

class PlayPoker(Mode):

    def mode_start(self, **kwargs):
        del kwargs

        # store the deck in a player var since it needs to persist from ball to
        # ball
        if not self.player.poker_deck:
            self.reset_poker()

        self.add_mode_event_handler('s_spinner_active', self.pick_new_card)
        self.add_mode_event_handler('shot_lower_vuk_from_playfield_hit',
                                    self.lock_card)

        self.add_mode_event_handler('slide_card_background_active',
                                    self.populate_player_cards)

    def populate_player_cards(self, **kwargs):
        for i, x in enumerate(self.player.poker_cards):
            self.machine.events.post('poker_card_{}_solid'.format(i+1),
                                     image=x.asset)

        self.pick_new_card()

        self.machine.events.remove_handler(self.populate_player_cards)

    def reset_poker(self, **kwargs):
        self.player.poker_deck = self.machine.card_deck.copy()
        self.player.poker_cards = list()
        self.player.poker_current_card = None

    def pick_new_card(self, **kwargs):
        del kwargs

        # save the old card and pick a new one from the deck
        old_card = self.player.poker_current_card
        new_card = choice(self.player.poker_deck)
        self.player.poker_current_card = new_card

        # take the new one out of the deck and put the old one back in
        self.player.poker_deck.remove(new_card)
        if old_card:
            self.player.poker_deck.append(old_card)

        self.machine.events.post(
            'poker_remove_card_{}'.format(len(self.player.poker_cards) + 1))

        self.machine.events.post(
            'poker_card_{}_flash'.format(len(self.player.poker_cards) + 1),
            image=new_card.asset)
        # self.machine.events.post(
        #     'poker_flash_card_{}'.format(len(self.player.poker_cards) + 1))

    def lock_card(self, **kwargs):
        del kwargs

        self.player.poker_cards.append(self.player.poker_current_card)

        self.machine.events.post('poker_card_locked')

        self.machine.events.post(
            'poker_card_{}_solid'.format(len(self.player.poker_cards)),
            image=self.player.poker_current_card.asset)

        self.player.poker_current_card = None

        if len(self.player.poker_cards) == 5:
            self.deck_complete()
        else:
            self.pick_new_card()

    def deck_complete(self):

        # evaluate from most valuable to least with elifs so that only the
        # highest hand is awarded

        self.machine.events.post('poker_deck_complete')

        if self._is_flush() and self._is_straight():
            if self._get_highest_card() == 14:
                self.machine.events.post('poker_royal_flush')
            else:
                self.machine.events.post('poker_straight_flush')

        elif self._get_multiples()[0]:
            self.machine.events.post('poker_four_of_a_kind')

        elif self._get_multiples()[1] and self._get_multiples()[2]:
            self.machine.events.post('poker_full_house')

        elif self._is_flush():
            self.machine.events.post('poker_flush')

        elif self._is_straight():
            self.machine.events.post('poker_straight')

        elif self._get_multiples()[1]:
            self.machine.events.post('poker_three_of_a_kind')

        elif self._get_multiples()[2] == 2:
            self.machine.events.post('poker_two_pairs')

        elif self._get_multiples()[2]:
            self.machine.events.post('poker_one_pair')

        else:
            card = sorted(self.player.poker_cards, key=lambda x: x.value)[4]

            self.machine.events.post('poker_high_card', value=card.value,
                                     value_name=card.value_name)

        self.reset_poker()

    def _is_flush(self):
        suits = [x.suit for x in self.player.poker_cards]
        if len(suits) == 1:
            return True
        else:
            return False

    def _is_straight(self):
        vals = [x.value for x in self.player.poker_cards]
        vals.sort()

        for i, v in enumerate(vals):
            if v != vals[0] + i:
                return False

        return True

    def _get_highest_card(self):
        vals = [x.value for x in self.player.poker_cards]
        vals.sort()
        return vals[4]

    def _get_multiples(self):
        # returns a three item tuple of the number of four of a kind, three of
        # a kind, and pairs

        vals = [x.value for x in self.player.poker_cards]
        unique_vals = set(vals)

        fours = 0
        threes = 0
        pairs = 0

        for val in unique_vals:
            num = vals.count(val)

            if num == 4:
                fours += 1
            elif num == 3:
                threes += 1
            elif num == 2:
                pairs += 1

        return (fours, threes, pairs)
