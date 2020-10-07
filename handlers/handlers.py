from typing import Tuple, Optional, List

from sqlalchemy.orm.exc import NoResultFound

import dataclasses_
from handlers import handler_helpers
from orm import orm_classes
from orm.db_apis import TasksManager
from scripts_for_settings.ini_worker import MyINIWorker


def change_auto_showing(settings: MyINIWorker, new_state: bool) -> str:
    settings["auto_showing"] = str(new_state)
    settings.save()
    return (
        "Автопоказ дерева задач после каждой команды теперь "
        f"{'включен' if new_state else 'выключен'}"
    )


def get_help_message(commands: Tuple[dataclasses_.Command]) -> str:
    return "\n\n".join(
        [
            command.get_full_description(include_heading=True)
            for command in commands
        ]
    )


def get_help_message_for_specific_commands(
        commands: Tuple[dataclasses_.Command],
        command_names: Tuple[str]) -> str:
    help_messages = []
    for command_name in command_names:
        for command in commands:
            if command_name in command.names:
                help_messages.append(
                    command.get_full_description(include_heading=True)
                )
    return (
        "\n\n".join(help_messages)
        if help_messages else
        "Ни одна указанная команда не найдена!"
    )


def add_task(
        tasks_manager: TasksManager, parent_id: int,
        text: str) -> Optional[str]:
    if (
        parent_id is None
        or
        tasks_manager.check_existence(
            orm_classes.Task.id == parent_id
        )
    ):
        task = orm_classes.Task(text=text, parent_id=parent_id)
        tasks_manager.append(task)
        tasks_manager.commit()
    else:
        return (
            f"Задачи с ID {parent_id} нет, поэтому новая задача не может "
            f"быть создана"
        )


def get_tasks_as_string(
        root_tasks: List[orm_classes.Task],
        indent_size: int = 4,
        indentation_symbol: str = " ") -> str:
    if root_tasks:
        return "\n".join(
            handler_helpers.get_tasks_as_strings(
                root_tasks,
                indent_size=indent_size,
                indentation_symbol=indentation_symbol
            )
        )
    else:
        return "<дерево пустое>"


def delete_tasks(
        tasks_manager: TasksManager, task_ids: Tuple[int]) -> Optional[str]:
    errors = []
    for task_id in task_ids:
        try:
            tasks_manager.delete(
                tasks_manager.get_task_by_id(task_id)
            )
        except NoResultFound:
            errors.append(
                f"Задачи с ID {task_id} нет, поэтому она не может быть "
                f"удалена"
            )
        else:
            tasks_manager.commit()
    return "\n".join(errors) if errors else None


def change_checked_state(
        tasks_manager: TasksManager, state: bool,
        task_ids: Tuple[int]) -> Optional[str]:
    errors = []
    for task_id in task_ids:
        try:
            tasks_manager.get_task_by_id(task_id).is_checked = state
        except NoResultFound:
            reason = (
                "она не может быть помечена"
                if state else
                "с нее нельзя убрать метку"
            )
            errors.append(f"Задачи с ID {task_id} нет, поэтому {reason}")
        else:
            tasks_manager.commit()
    return "\n".join(errors) if errors else None


def change_collapsing_state(
        tasks_manager: TasksManager, state: bool,
        task_ids: Tuple[int]) -> Optional[str]:
    errors = []
    for task_id in task_ids:
        try:
            tasks_manager.get_task_by_id(task_id).is_collapsed = state
        except NoResultFound:
            reason = (
                "она не может быть свернута"
                if state else
                "она не может быть развернута"
            )
            errors.append(f"Задачи с ID {task_id} нет, поэтому {reason}")
        else:
            tasks_manager.commit()
    return "\n".join(errors) if errors else None


def edit_task(
        tasks_manager: TasksManager, task_id: int, text: str) -> Optional[str]:
    try:
        task = tasks_manager.get_task_by_id(task_id)
    except NoResultFound:
        return (
            f"Задачи с ID {task_id} нет, поэтому она не может быть "
            f"изменена!"
        )
    else:
        task.text = text
        tasks_manager.commit()


def change_parent_of_task(
        tasks_manager: TasksManager,
        task_id: int, parent_id: int) -> Optional[str]:
    try:
        task = tasks_manager.get_task_by_id(task_id)
    except NoResultFound:
        return (
            f"Задачи с ID {task_id} нет, поэтому она не может быть "
            f"изменена!"
        )
    else:
        if task_id == parent_id:
            return (
                f"Задача не может быть родителем самой себя! "
                f"({task_id} == {parent_id})"
            )
        else:
            if (
                parent_id is None
                or
                tasks_manager.check_existence(
                    orm_classes.Task.id == parent_id
                )
            ):
                task.parent_id = parent_id
                tasks_manager.commit()
            else:
                return f"Задачи с ID {parent_id} нет!"


def show_date(tasks_manager: TasksManager, task_id: int) -> str:
    try:
        task = tasks_manager.get_task_by_id(task_id)
    except NoResultFound:
        return (
            f"Задачи с ID {task_id} нет, поэтому невозможно узнать дату ее "
            f"создания!"
        )
    else:
        return f"Дата создания задачи с ID {task_id}: {task.creation_date}"
