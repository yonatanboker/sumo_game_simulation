import random
from card_and_board import Card, ActionType, BoardState
from game_engine import RulesEngine, RandomPlayer


class GameSimulation:
    """מנהל הרצת משחק בודד בין שני שחקנים."""

    def __init__(self, player1, player2, hand_size: int = 3, danger_threshold: int = 3):
        self.board = BoardState(danger_threshold=danger_threshold)
        self.p1 = player1
        self.p2 = player2
        self.hand_size = hand_size
        self.deck1 = self._build_deck()
        self.deck2 = self._build_deck()

    def _build_deck(self) -> list:
        """בניית חבילה תקנית של 15 קלפים (1-5 מכל פעולה)."""
        deck = []
        for act in ActionType:
            for val in range(1, 6):
                deck.append(Card(act, val))
        random.shuffle(deck)
        return deck

    def _setup_hands(self):
        self.p1.hand = [self.deck1.pop() for _ in range(min(self.hand_size, len(self.deck1)))]
        self.p2.hand = [self.deck2.pop() for _ in range(min(self.hand_size, len(self.deck2)))]

    def play_turn(self):
        # 1. בחירת קלפים
        c1 = self.p1.choose_card(self.board)
        c2 = self.p2.choose_card(self.board)

        # 2. זיהוי אם המדד המושפע נמצא באזור סכנה
        target_action = c1.get_action_type()  # במפגש משפיעים על המדד של הקלף ששוחק
        is_danger = self.board.is_in_danger_zone(target_action)

        # 3. הכרעת מנצח במפגש
        winner = RulesEngine.resolve_encounter(c1, c2, is_danger)

        if winner != 0:
            # נזק בסיסי = הערך הנמוך מביניהם
            damage = Card.get_min_value(c1, c2)

            # בונוס סמן עוצמה
            if winner == self.board.power_token_owner:
                damage += 1

            # הזזת המדד בלוח
            direction = 1 if winner == 1 else -1
            self.board.tracks[target_action] += direction * damage

        # 4. עדכון סמן העוצמה (הקלף הגבוה מקבל אותו)
        comp_val = c1.compare_value(c2)
        if comp_val == 1:
            self.board.power_token_owner = 1
        elif comp_val == -1:
            self.board.power_token_owner = 2

        # 5. רענון קלפים ביד (שליפה מהחבילה)
        self.p1.hand.remove(c1)
        self.p2.hand.remove(c2)
        if self.deck1:
            self.p1.hand.append(self.deck1.pop())
        if self.deck2:
            self.p2.hand.append(self.deck2.pop())

    def run_game(self, max_turns: int = 100) -> tuple:
        self._setup_hands()
        turn_count = 0

        while self.board.get_winner() == 0 and turn_count < max_turns:
            self.play_turn()
            turn_count += 1

        return self.board.get_winner(), turn_count


# --- הרצה מהירה לבדיקה ---
if __name__ == "__main__":
    p1 = RandomPlayer(1)
    p2 = RandomPlayer(2)
    sim = GameSimulation(p1, p2, hand_size=3)
    winner, turns = sim.run_game()
    print(f"Game finished in {turns} turns. Winner: Player {winner}")