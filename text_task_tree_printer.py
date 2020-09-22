from typing import List

import orm_classes


class TextTaskTreePrinter:

    def print_tasks(
            self,
            root_tasks: List[orm_classes.Task],
            indentation_level: int = 0,
            indent_size: int = 4
    ):
        for task in root_tasks:
            print(
                f"{' ' * (indentation_level * indent_size)}"
                f"[{'-' if task.nested_tasks_is_shown else '+'}]"
                f"[{'X' if task.is_checked else ' '}]"
                f"[ID: {task.id}]"
                f" {task.text}"
            )
            if task.nested_tasks_is_shown:
                self.print_tasks(
                    task.nested_tasks,
                    indentation_level + 1,
                    indent_size
                )
