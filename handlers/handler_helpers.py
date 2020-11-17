from typing import List

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
