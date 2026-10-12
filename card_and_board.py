from enum import Enum


class ActionType(Enum):
    PUSH = "PUSH"      # דחיפה
    GRAB = "GRAB"      # תפיסה
    DODGE = "DODGE"    # התחמקות


class Card:
    """מחלקה המייצגת קלף יחיד במשחק."""

    def __init__(self, action_type: ActionType, value: int):
        self._action_type = action_type
        self._value = value

    def get_action_type(self) -> ActionType:
        return self._action_type

    def get_value(self) -> int:
        return self._value

    def compare_value(self, other_card: "Card") -> int:
        if self._value > other_card.get_value():
            return 1
        elif self._value < other_card.get_value():
            return -1
        return 0

    def is_same_type(self, other_card: "Card") -> bool:
        return self._action_type == other_card.get_action_type()

    @staticmethod
    def get_min_value(card1: "Card", card2: "Card") -> int:
        return min(card1.get_value(), card2.get_value())

    def __repr__(self) -> str:
        return f"Card({self._action_type.value}, {self._value})"


class BoardState:
    """מחלקה המנהלת את מצב הלוח, המדדים ואזורי הסכנה."""

    def __init__(self, danger_threshold: int = 3):
        self.danger_threshold = danger_threshold  # מרחק למשבצת אדומה/אזור סכנה
        # מיקום 3 המדדים: 0 = מרכז, חיובי = לטובת שחקן 1, שלילי = לטובת שחקן 2
        self.tracks = {
            ActionType.PUSH: 0,
            ActionType.GRAB: 0,
            ActionType.DODGE: 0
        }
        self.power_token_owner = 0  # 0: ניטרלי, 1: שחקן 1, 2: שחקן 2

    def is_in_danger_zone(self, action_type: ActionType) -> bool:
        """בודק אם המדד הספציפי שנבחר נמצא כרגע במשבצת הסכנה האדומה."""
        return abs(self.tracks[action_type]) >= self.danger_threshold

    def get_winner(self) -> int:
        """מחזיר 1 אם שחקן 1 ניצח, 2 אם שחקן 2 ניצח, או 0 אם המשחק נמשך."""
        for pos in self.tracks.values():
            if pos > self.danger_threshold:
                return 1
            elif pos < -self.danger_threshold:
                return 2
        return 0