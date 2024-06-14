from mpf.core.mode import Mode
from random import choice

class HiLo(Mode):

    def mode_start(self, **kwargs):
        del kwargs

        self.deck = self.machine.card_deck.copy()
        self.current_card = None
        self.next_card = None
        self.current_round = 0
        self.max_rounds = 3
        self.state = 'intro'
        self.lose = 0
        self.score_values = [(125000, '125K'),
                             (250000, '250K'),
                             (500000, '500K'),
                             (1000000, '1M')]

        self.machine.events.post('hilo_intro')
        self.delay.add(3000, self.show_card, 'hilo')

        self.add_mode_event_handler('sw_left_flipper', self.left_flipper)
        self.add_mode_event_handler('sw_right_flipper', self.right_flipper)
        self.add_mode_event_handler('flipper_cancel', self.both_flippers)
        self.add_mode_event_handler('timer_time_out_complete', self.gamble_lose)

    def both_flippers(self, **kwargs):
        if self.state == 'intro':
            self.delay.run_now('hilo')

    def left_flipper(self, **kwargs):
        if self.state == 'show':
            self.cash_out()
            self.machine.events.post('play_hilo_cash_out_sound')
            self.machine.events.post('reset_timer')
        elif self.state == 'gamble':
            self.guess_lower()
            self.machine.events.post('play_hilo_guess_lower_sound')
            self.machine.events.post('reset_timer')

    def right_flipper(self, **kwargs):
        if self.state == 'show':
            self.gamble()
            self.machine.events.post('play_hilo_gamble_sound')
            self.machine.events.post('reset_timer')
        elif self.state == 'gamble':
            self.guess_higher()
            self.machine.events.post('play_hilo_guess_higher_sound')
            self.machine.events.post('reset_timer')

    def show_card(self, **kwargs):
        self.state = 'show'
        self.machine.events.post('reset_timer')

        if self.next_card:
            self.current_card = self.next_card
        else:
            self.current_card = self.get_card()
        self.machine.events.post('hilo_clear_cards')
        self.machine.events.post(
            'hilo_show_card',
            cash_out=self.score_values[self.current_round][1],
            next_bet=self.score_values[self.current_round+1][1])
        self.machine.events.post('show_player_card',
                                 image=self.current_card.asset)

    def gamble(self, **kwargs):
        self.state = 'gamble'
        self.machine.events.post('reset_timer')
        self.machine.events.post('hilo_gamble')
        self.delay.add(2000, self.show_gamble_slide, 'hilo')

    def show_gamble_slide(self, **kwargs):
        self.machine.events.post('reset_timer')
        self.machine.events.post('hilo_show_gamble_slide')
        self.machine.events.post('play_hilo_higher_lower_sound')
        self.machine.events.post('show_player_card',
                                 image=self.current_card.asset)
        

    def cash_out(self, **kwargs):
        points = self.score_values[self.current_round][0]
        self.machine.events.post('hilo_cash_out', points=points)
        self.end()

    def guess_higher(self, **kwargs):
        self.machine.events.post('hilo_guess_higher')
        self.delay.add(2000, self.show_next_card, bet='higher')

    def guess_lower(self, **kwargs):
        self.machine.events.post('hilo_guess_lower')
        self.delay.add(2000, self.show_next_card, bet='lower')

    def show_next_card(self, bet, **kwargs):
        self.next_card = self.get_card()
        self.machine.events.post('reset_timer')
        # make sure the next card is not a tie, just to keep things simple
        while self.next_card.value == self.current_card.value:
            self.next_card = self.get_card()
        self.machine.events.post('hilo_clear_cards')
        self.machine.events.post('hilo_show_next_card')
        self.machine.events.post('show_player_card',
                                 image=self.current_card.asset)
        self.machine.events.post('show_dealer_card',
                                 image=self.next_card.asset)
        self.delay.add(2000, self.gamble_result, bet=bet)

    def gamble_result(self, bet, **kwargs):
        self.machine.events.post('reset_timer')
        if ((bet == 'higher' and
                self.next_card.value > self.current_card.value) or
                (bet == 'lower' and
                self.next_card.value < self.current_card.value)):
            self.machine.events.post('play_hilo_win_sound')
            self.gamble_win()
        else:
            self.machine.events.post('play_hilo_lose_sound')
            self.gamble_lose()

    def gamble_win(self):
        self.current_round += 1
        self.machine.events.post('reset_timer')
        if self.current_round < self.max_rounds:
            self.machine.events.post('hilo_win',
                points=self.score_values[self.current_round][0])

            self.delay.add(2000, self.show_card)
        else:
            self.machine.events.post('hilo_game_win',
                points=self.score_values[self.current_round][0])
            self.delay.add(2000, self.end)

    def gamble_lose(self, **kwargs):
        self.machine.events.post('hilo_lose')
        
        self.lose = 1 # needed a way to decide if win/lose for scoring
        self.delay.add(2000, self.end)

    def end(self, **kwargs):
        points = self.score_values[self.current_round][0]
        if self.lose == 1:
            points = 0
        self.machine.events.post('hilo_total', score=points)
        self.player.score += points
        self.machine.events.post('hilo_done')

    def get_card(self):
        card = choice(self.deck)
        self.deck.remove(card)
        return card
