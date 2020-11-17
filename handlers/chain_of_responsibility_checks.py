from typing import Optional

from orm import models
from orm.db_apis import TasksManager


class ValidationError(Exception):
    pass


def parent_id_is_equal_to_the_current_task_id(
        task: models.Task, parent_id: int) -> None:
    if task.id == parent_id:
        raise ValidationError(
            f"Задача не может быть родителем самой себя! "
            f"({task.id} == {parent_id})"
        )


def parent_id_exists(
        tasks_manager: TasksManager, parent_id: Optional[int],
        task: models.Task) -> None:
    if (
        parent_id is not None
        and
        tasks_manager.check_existence(
            task.id == parent_id
        )
    ):
        raise ValidationError(f"Задачи с ID {parent_id} нет!")


def check_for_subtask(task: models.Task, parent_id: Optional[int]) -> None:
    if parent_id and task.check_for_subtask(parent_id):
        raise ValidationError(
            f"Задача {parent_id} не может быть родителем задачи {task.id}, "
            f"так как задача {task.id} содержит задачу {parent_id} как дочернюю"
        )
