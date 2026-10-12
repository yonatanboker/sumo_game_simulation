import random
import pandas as pd
import numpy as np
from card_and_board import Card, ActionType, BoardState
from game_engine import RulesEngine, Player


# ==========================================
# 1. הגדרת אסטרטגיות השחקנים (Agents)
# ==========================================

class HighestCardPlayer(Player):
    """אסטרטגיה 1: תמיד בוחר את הקלף בעל הערך הגבוה ביותר ביד."""

    def choose_card(self, board: BoardState) -> Card:
        if not self.hand:
            return None
        return max(self.hand, key=lambda c: c.get_value())


class FocusTrackPlayer(Player):
    """אסטרטגיה 2: מתמקד תמיד באותה שורה/מדד (למשל: רק PUSH)."""

    def __init__(self, player_id: int, target_action: ActionType = ActionType.PUSH):
        super().__init__(player_id)
        self.target_action = target_action

    def choose_card(self, board: BoardState) -> Card:
        if not self.hand:
            return None
        matching_cards = [c for c in self.hand if c.get_action_type() == self.target_action]
        if matching_cards:
            return max(matching_cards, key=lambda c: c.get_value())
        return random.choice(self.hand)


class AlternatingPlayer(Player):
    """אסטרטגיה 3: מחליף כל הזמן את הלחץ בין עמודות/מדדים שונים ברוטציה קבועה."""

    def __init__(self, player_id: int):
        super().__init__(player_id)
        self.actions_cycle = [ActionType.PUSH, ActionType.GRAB, ActionType.DODGE]
        self.current_idx = 0

    def choose_card(self, board: BoardState) -> Card:
        if not self.hand:
            return None
        target_action = self.actions_cycle[self.current_idx % 3]
        self.current_idx += 1

        matching_cards = [c for c in self.hand if c.get_action_type() == target_action]
        if matching_cards:
            return max(matching_cards, key=lambda c: c.get_value())
        return random.choice(self.hand)


class AvoidLastPlayedTypePlayer(Player):
    """אסטרטגיה מתוחכמת 1: משחק סוג קלף שלא שוחק בתור הקודם."""

    def __init__(self, player_id: int):
        super().__init__(player_id)
        self.last_played_types = set()

    def choose_card(self, board: BoardState) -> Card:
        if not self.hand:
            return None

        available_types = [act for act in ActionType if act not in self.last_played_types]
        matching_cards = [c for c in self.hand if c.get_action_type() in available_types]

        if matching_cards:
            return max(matching_cards, key=lambda c: c.get_value())

        return max(self.hand, key=lambda c: c.get_value())


class CopyOpponentTypePlayer(Player):
    """אסטרטגיה מתוחכמת 2: משחק את סוג הקלף שהיריב שיחק בתור הקודם."""

    def __init__(self, player_id: int):
        super().__init__(player_id)
        self.last_opponent_type = None

    def choose_card(self, board: BoardState) -> Card:
        if not self.hand:
            return None

        if self.last_opponent_type is not None:
            matching_cards = [c for c in self.hand if c.get_action_type() == self.last_opponent_type]
            if matching_cards:
                return max(matching_cards, key=lambda c: c.get_value())

        return max(self.hand, key=lambda c: c.get_value())


# ==========================================
# 2. מחלקת הסימולציה והרצת ניסויים
# ==========================================

class ScenarioRunner:
    def __init__(self, danger_threshold: int = 3, mistake_rate: float = 0.10):
        self.danger_threshold = danger_threshold
        self.mistake_rate = mistake_rate

    def _build_deck(self) -> list:
        deck = []
        for act in ActionType:
            for val in range(1, 6):
                deck.append(Card(act, val))
        random.shuffle(deck)
        return deck

    def _get_agent_decision(self, player: Player, board: BoardState) -> Card:
        if not player.hand:
            return None

        if random.random() < self.mistake_rate:
            return random.choice(player.hand)

        return player.choose_card(board)

    def run_single_game(self, p1: Player, p2: Player, hand_size: int, max_turns: int = 100) -> tuple:
        board = BoardState(danger_threshold=self.danger_threshold)
        deck1 = self._build_deck()
        deck2 = self._build_deck()

        p1.hand = [deck1.pop() for _ in range(min(hand_size, len(deck1)))]
        p2.hand = [deck2.pop() for _ in range(min(hand_size, len(deck2)))]

        turn_count = 0
        while board.get_winner() == 0 and turn_count < max_turns:
            c1 = self._get_agent_decision(p1, board)
            c2 = self._get_agent_decision(p2, board)

            if c1 is None or c2 is None:
                break

            if isinstance(p1, AvoidLastPlayedTypePlayer):
                p1.last_played_types = {c1.get_action_type(), c2.get_action_type()}
            if isinstance(p2, AvoidLastPlayedTypePlayer):
                p2.last_played_types = {c1.get_action_type(), c2.get_action_type()}

            if isinstance(p1, CopyOpponentTypePlayer):
                p1.last_opponent_type = c2.get_action_type()
            if isinstance(p2, CopyOpponentTypePlayer):
                p2.last_opponent_type = c1.get_action_type()

            target_action = c1.get_action_type()
            is_danger = board.is_in_danger_zone(target_action)

            winner = RulesEngine.resolve_encounter(c1, c2, is_danger)

            if winner != 0:
                damage = Card.get_min_value(c1, c2)
                if winner == board.power_token_owner:
                    damage += 1
                direction = 1 if winner == 1 else -1
                board.tracks[target_action] += direction * damage

            comp_val = c1.compare_value(c2)
            if comp_val == 1:
                board.power_token_owner = 1
            elif comp_val == -1:
                board.power_token_owner = 2

            p1.hand.remove(c1)
            p2.hand.remove(c2)

            if not deck1:
                deck1 = self._build_deck()
            p1.hand.append(deck1.pop())

            if not deck2:
                deck2 = self._build_deck()
            p2.hand.append(deck2.pop())

            turn_count += 1

        return board.get_winner(), turn_count

    def run_experiment_matrix(self, num_simulations: int = 3000, hand_sizes: list = list(range(3, 11))) -> pd.DataFrame:
        strategies = {
            "HighestCard": lambda pid: HighestCardPlayer(pid),
            "FocusTrack": lambda pid: FocusTrackPlayer(pid, ActionType.PUSH),
            "Alternating": lambda pid: AlternatingPlayer(pid),
            "AvoidLastPlayed": lambda pid: AvoidLastPlayedTypePlayer(pid),
            "CopyOpponent": lambda pid: CopyOpponentTypePlayer(pid)
        }

        results = []

        total_scenarios = len(hand_sizes) * len(strategies) * len(strategies)
        current_scenario = 0

        for h_size in hand_sizes:
            for strat1_name, create_p1 in strategies.items():
                for strat2_name, create_p2 in strategies.items():
                    current_scenario += 1
                    print(
                        f"מריץ תרחיש {current_scenario}/{total_scenarios}: Hand Size={h_size}, {strat1_name} vs {strat2_name}...")

                    p1_wins = 0
                    p2_wins = 0
                    draws = 0
                    turns_list = []

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

                        turns_list.append(turns)

                    # חישוב רבעונים וחציון
                    q1_turns = np.percentile(turns_list, 25)
                    median_turns = np.percentile(turns_list, 50)
                    q3_turns = np.percentile(turns_list, 75)
                    avg_turns = np.mean(turns_list)

                    results.append({
                        "Hand_Size": h_size,
                        "P1_First_Player_Strategy": strat1_name,
                        "P2_Second_Player_Strategy": strat2_name,
                        "Is_Same_Strategy": (strat1_name == strat2_name),
                        "First_Player_Wins (P1)": p1_wins,
                        "Second_Player_Wins (P2)": p2_wins,
                        "Draws": draws,
                        "First_Player_Win_Rate (%)": round((p1_wins / num_simulations) * 100, 2),
                        "Second_Player_Win_Rate (%)": round((p2_wins / num_simulations) * 100, 2),
                        "Avg_Turns": round(avg_turns, 2),
                        "Q1_Turns (25%)": round(q1_turns, 1),
                        "Median_Turns (50%)": round(median_turns, 1),
                        "Q3_Turns (75%)": round(q3_turns, 1),
                        "IQR_Turns (Q3-Q1)": round(q3_turns - q1_turns, 1)  # הטווח הבין-רבעוני (מדד הפיזור)
                    })

        df = pd.DataFrame(results)
        return df


# ==========================================
# 3. הרצה והדפסת הסיכום
# ==========================================

if __name__ == "__main__":
    runner = ScenarioRunner(danger_threshold=3, mistake_rate=0.10)

    print("מריץ 3,000 סימולציות לכל תרחיש עם ניתוח רבעונים (Q1, Median, Q3)...")
    df_results = runner.run_experiment_matrix(num_simulations=3000, hand_sizes=list(range(3, 11)))

    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)

    print("\n=== תוצאות מסוכמות ב-DataFrame ===")
    print(df_results.head(15))

    df_results.to_csv("simulation_results_quartiles.csv", index=False)
    print("\nהתוצאות שנשמרו בהצלחה לקובץ 'simulation_results_quartiles.csv'!")