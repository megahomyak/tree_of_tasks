from enum import Enum, auto
from typing import List, Optional

from orm import models


def get_tasks_as_strings(
        root_tasks: List[models.Task],
        indentation_level: int = 0,
        indent_size: int = 4,
        indentation_symbol: str = " ") -> List[str]:
    tasks_as_strings = []
    for task in root_tasks:
        tasks_as_strings.append(
            f"{indentation_symbol * (indentation_level * indent_size)}"
            f"[{'+' if task.is_collapsed else '-'}]"
            f"[{'X' if task.is_checked else ' '}]"
            f"[ID: {task.id}]"
            f" {task.text}"
        )
        if not task.is_collapsed and task.nested_tasks:
            tasks_as_strings.extend(get_tasks_as_strings(
                task.nested_tasks,
                indentation_level + 1,
                indent_size,
                indentation_symbol
            ))
    return tasks_as_strings


def get_strings_enumeration(strings: List[str]) -> str:
    return " и ".join([i for i in (", ".join(strings[:-1]), strings[-1]) if i])


def make_strings_with_enumeration(
        error_ids: List[int], single_id_text: str,
        multiple_ids_text: str,
        ending: str = "") -> str:
    if len(error_ids) == 1:
        return single_id_text.format(error_ids[0]) + ending
    else:
        return (multiple_ids_text.format(get_strings_enumeration(
            list(map(str, error_ids))
        )) + ending) if error_ids else None


def make_optional_string_from_optional_strings(
        strings: List[Optional[str]], separator: str = "\n") -> str:
    errors = list(filter(None, strings))
    return separator.join(errors) if errors else None


class BooleanTaskFields(Enum):
    IS_CHECKED = auto()
    IS_COLLAPSED = auto()
