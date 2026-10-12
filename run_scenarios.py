import random
import pandas as pd
from card_and_board import Card, ActionType, BoardState
from game_engine import RulesEngine, Player


# ==========================================
# 1. הגדרת אסטרטגיות השחקנים (Agents)
# ==========================================

class HighestCardPlayer(Player):
    """אסטרטגיה 1: תמיד בוחר את הקלף בעל הערך הגבוה ביותר ביד."""

    def choose_card(self, board: BoardState) -> Card:
        # מיון הקלפים מהגבוה לנמוך ובחירת הראשון
        best_card = max(self.hand, key=lambda c: c.get_value())
        return best_card


class FocusTrackPlayer(Player):
    """אסטרטגיה 2: מתמקד תמיד באותה שורה/מדד (למשל: רק PUSH)."""

    def __init__(self, player_id: int, target_action: ActionType = ActionType.PUSH):
        super().__init__(player_id)
        self.target_action = target_action

    def choose_card(self, board: BoardState) -> Card:
        # סינון קלפים מהפעולה שנבחרה
        matching_cards = [c for c in self.hand if c.get_action_type() == self.target_action]
        if matching_cards:
            # אם יש, בוחר את הקלף הגבוה ביותר מביניהם
            return max(matching_cards, key=lambda c: c.get_value())
        # אם אין קלף מפעולה זו ביד, בוחר אקראית
        return random.choice(self.hand)


class AlternatingPlayer(Player):
    """אסטרטגיה 3: מחליף כל הזמן את הלחץ בין עמודות/מדדים שונים."""

    def __init__(self, player_id: int):
        super().__init__(player_id)
        self.actions_cycle = [ActionType.PUSH, ActionType.GRAB, ActionType.DODGE]
        self.current_idx = 0

    def choose_card(self, board: BoardState) -> Card:
        # נקבע את הפעולה לפי התור במחזוריות
        target_action = self.actions_cycle[self.current_idx % 3]
        self.current_idx += 1

        matching_cards = [c for c in self.hand if c.get_action_type() == target_action]
        if matching_cards:
            return max(matching_cards, key=lambda c: c.get_value())
        return random.choice(self.hand)


# ==========================================
# 2. מחלקת הסימולציה והרצת ניסויים
# ==========================================

class ScenarioRunner:
    def __init__(self, danger_threshold: int = 3):
        self.danger_threshold = danger_threshold

    def _build_deck(self) -> list:
        deck = []
        for act in ActionType:
            for val in range(1, 6):
                deck.append(Card(act, val))
        random.shuffle(deck)
        return deck

    def run_single_game(self, p1: Player, p2: Player, hand_size: int, max_turns: int = 100) -> tuple:
        board = BoardState(danger_threshold=self.danger_threshold)
        deck1 = self._build_deck()
        deck2 = self._build_deck()

        p1.hand = [deck1.pop() for _ in range(min(hand_size, len(deck1)))]
        p2.hand = [deck2.pop() for _ in range(min(hand_size, len(deck2)))]

        turn_count = 0
        while board.get_winner() == 0 and turn_count < max_turns:
            c1 = p1.choose_card(board)
            c2 = p2.choose_card(board)

            target_action = c1.get_action_type()
            is_danger = board.is_in_danger_zone(target_action)

            winner = RulesEngine.resolve_encounter(c1, c2, is_danger)

            if winner != 0:
                damage = Card.get_min_value(c1, c2)
                if winner == board.power_token_owner:
                    damage += 1
                direction = 1 if winner == 1 else -1
                board.tracks[target_action] += direction * damage

            # עדכון סמן עוצמה
            comp_val = c1.compare_value(c2)
            if comp_val == 1:
                board.power_token_owner = 1
            elif comp_val == -1:
                board.power_token_owner = 2

            # שליפה
            p1.hand.remove(c1)
            p2.hand.remove(c2)
            if deck1: p1.hand.append(deck1.pop())
            if deck2: p2.hand.append(deck2.pop())

            turn_count += 1

        return board.get_winner(), turn_count

    def run_experiment_matrix(self, num_simulations: int = 2000, hand_sizes: list = [3, 4, 5]) -> pd.DataFrame:
        # הגדרת פונקציות ליצירת שחקנים מחדש בכל משחק
        strategies = {
            "HighestCard": lambda pid: HighestCardPlayer(pid),
            "FocusTrack": lambda pid: FocusTrackPlayer(pid, ActionType.PUSH),
            "Alternating": lambda pid: AlternatingPlayer(pid)
        }

        results = []

        for h_size in hand_sizes:
            for strat1_name, create_p1 in strategies.items():
                for strat2_name, create_p2 in strategies.items():

                    p1_wins = 0
                    p2_wins = 0
                    draws = 0
                    total_turns = 0

                    for _ in range(num_simulations):
                        p1 = create_p1(1)
                        p2 = create_p2(2)

                        winner, turns = self.run_single_game(p1, p2, hand_size=h_size)

                        if winner == 1:
                            p1_wins += 1
                        elif winner == 2:
                            p2_wins += 1
                        else:
                            draws += 1

                        total_turns += turns

                    # שמירת התוצאות
                    results.append({
                        "Hand_Size": h_size,
                        "P1_Strategy": strat1_name,
                        "P2_Strategy": strat2_name,
                        "Is_Same_Strategy": (strat1_name == strat2_name),
                        "P1_Wins": p1_wins,
                        "P2_Wins": p2_wins,
                        "Draws": draws,
                        "P1_Win_Rate (%)": round((p1_wins / num_simulations) * 100, 2),
                        "P2_Win_Rate (%)": round((p2_wins / num_simulations) * 100, 2),
                        "Avg_Turns": round(total_turns / num_simulations, 2)
                    })

        df = pd.DataFrame(results)
        return df


# ==========================================
# 3. הרצה והדפסת הסיכום
# ==========================================

if __name__ == "__main__":
    runner = ScenarioRunner(danger_threshold=3)

    print("מריץ סימולציות (2000 חזרות לכל שילוב אסטרטגיות וגודל יד)...")
    df_results = runner.run_experiment_matrix(num_simulations=2000, hand_sizes=[3, 4, 5])

    # הגדרות תצוגה מלאות ל-pandas
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)

    print("\n=== תוצאות מסוכמות ב-DataFrame ===")
    print(df_results)

    # שמירה לקובץ CSV
    df_results.to_csv("simulation_results.csv", index=False)
    print("\nהתוצאות שנשמרו בהצלחה לקובץ 'simulation_results.csv'!")