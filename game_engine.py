import random
from card_and_board import Card, ActionType, BoardState


class RulesEngine:
    """מנוע החוקים שמכריע מפגשים לפי מיקום המדד על הלוח."""

    @staticmethod
    def resolve_encounter(card1: Card, card2: Card, is_danger: bool) -> int:
        """
        מחזיר 1 אם שחקן 1 ניצח במפגש, 2 אם שחקן 2 ניצח, ו-0 בתיקו.
        """
        act1 = card1.get_action_type()
        act2 = card2.get_action_type()

        if act1 == act2:
            return 0

        # יחסים רגילים: PUSH > GRAB > DODGE > PUSH
        normal_wins = {
            (ActionType.PUSH, ActionType.GRAB),
            (ActionType.GRAB, ActionType.DODGE),
            (ActionType.DODGE, ActionType.PUSH)
        }

        # יחסי אזור סכנה (הפוך): PUSH > DODGE > GRAB > PUSH
        inverted_wins = {
            (ActionType.PUSH, ActionType.DODGE),
            (ActionType.DODGE, ActionType.GRAB),
            (ActionType.GRAB, ActionType.PUSH)
        }

        winning_pairs = inverted_wins if is_danger else normal_wins
        return 1 if (act1, act2) in winning_pairs else 2


class Player:
    """מחלקת בסיס לשחקן."""

    def __init__(self, player_id: int):
        self.player_id = player_id
        self.hand = []

    def choose_card(self, board: BoardState) -> Card:
        """בחירת קלף - מיושמת במחלקות היורשות."""
        raise NotImplementedError


class RandomPlayer(Player):
    """שחקן שמקבל החלטות אקראיות מתוך היד."""

    def choose_card(self, board: BoardState) -> Card:
        return random.choice(self.hand)