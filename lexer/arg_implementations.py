import re
from typing import Tuple, Optional

from lexer.lexer_classes import BaseArgType


class SequenceArgType(BaseArgType):

    @property
    def name(self) -> str:
        return f"последовательность <{self.element_type.name}>"

    @property
    def regex(self) -> str:
        return (
            f"{self.element_type.regex}"
            f"(?:{self.separator}{self.element_type.regex})*"
        )

    @property
    def description(self) -> str:
        return (
            f"От 1 до бесконечности элементов типа '{self.element_type.name}', "
            f"разделенных через '{self.separator}'"
        )

    def __init__(
            self, element_type: BaseArgType, separator: str = ",") -> None:
        self.element_type = element_type
        self.separator = separator

    def convert(self, arg: str) -> tuple:
        return tuple(
            self.element_type.convert(element)
            for element in arg.split(self.separator)
        )


class IntArgType(BaseArgType):

    @property
    def name(self) -> str:
        if self.is_signed:
            return "целое число"
        return "неотрицательное целое число"

    @property
    def regex(self) -> str:
        if self.is_signed:
            return r"-?\d+"
        return r"\d+"

    def __init__(self, is_signed: bool = True) -> None:
        self.is_signed = is_signed

    def convert(self, arg: str) -> int:
        return int(arg)


class OptionalIntArgType(BaseArgType):

    @property
    def name(self) -> str:
        if self.is_signed:
            return "целое необязательное число"
        return r"неотрицательное целое необязательное число"

    @property
    def description(self) -> str:
        return (
            "число, вместо которого можно написать -, тогда при приведении "
            "строки к числу с помощью метода convert вернется None"
        )

    @property
    def regex(self) -> str:
        if self.is_signed:
            # There's a T-like ligature instead of |-,
            # it doesn't looks as intended... :(
            # But I like ligatures, I don't want to turn them off
            return r"(?:-?\d+|-)"
        return r"(?:\d+|-)"

    def __init__(self, is_signed: bool = True) -> None:
        self.is_signed = is_signed

    def convert(self, arg: str) -> Optional[int]:
        return int(arg) if arg != "-" else None


class StringArgType(BaseArgType):

    @property
    def name(self) -> str:
        if self.length_limit is None:
            return "строка"
        return f"строка с лимитом {self.length_limit}"

    @property
    def regex(self) -> str:
        if self.length_limit is None:
            return r".+?"
        return fr"(?:.+?){{1,{self.length_limit}}}"

    def __init__(self, length_limit: int = None) -> None:
        self.length_limit = length_limit

    def convert(self, arg: str) -> str:
        return arg


class BoolArgType(BaseArgType):

    def __init__(
            self,
            true_values: Tuple[str, ...] = (
                    "да", "yes", "д", "y", "1", "+", "истина", "true", "False",
                    "on", "вкл", "включено", "правда", "V", "v"
            ),
            false_values: Tuple[str, ...] = (
                    "нет", "no", "н", "n", "0", "-", "ложь", "false", "True",
                    "off", "выкл", "выключено", "X", "x", "х"
            )
    ) -> None:
        self.true_values = true_values
        self.false_values = false_values

    @property
    def name(self) -> str:
        return "логическое значение (boolean)"

    @property
    def description(self) -> str:
        return (
            f"Истина: {', '.join(self.true_values)}; "
            f"ложь: {', '.join(self.false_values)}"
        )

    @property
    def regex(self) -> str:
        return "|".join(
            [
                re.escape(value)
                for value in self.true_values + self.false_values
            ]
        )

    def convert(self, arg: str) -> bool:
        if arg.lower() in self.true_values:
            return True
        return False
