class Card:
    """מחלקת קלף במשחק."""

    def __init__(self, action_type: str, value: int):
        """
        בנאי הקלף.
        :param action_type: סוג הפעולה (למשל: "PUSH", "GRAB", "DODGE")
        :param value: הערך המספרי של הקלף (למשל: 1 עד 5)
        """
        self._action_type = action_type
        self._value = value

    def get_action_type(self) -> str:
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
        """
        בודק אם סוג הקלף זהה לסוג הקלף האחר.
        :return: True אם הסוגים זהים, אחרת False.
        """
        return self._action_type == other_card.get_action_type()

    # --- ייצוג טקסטואלי ---
    def __repr__(self) -> str:
        return f"Card({self._action_type}, {self._value})"