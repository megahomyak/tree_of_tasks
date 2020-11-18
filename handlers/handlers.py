from typing import Tuple, Optional

from sqlalchemy.orm.exc import NoResultFound

import dataclasses_
from handlers import handler_helpers
from ini_worker import MyINIWorker
from orm import models
from orm.db_apis import TasksManager


class Handlers:

    def __init__(self, ini_worker: MyINIWorker, tasks_manager: TasksManager):
        self.ini_worker = ini_worker
        self.tasks_manager = tasks_manager

    def change_auto_showing(self, new_state: bool) -> str:
        new_state_str = str(new_state)
        if self.ini_worker["auto_showing"] == new_state_str:
            self.ini_worker["auto_showing"] = new_state_str
            self.ini_worker.save()
            return (
                "Автопоказ дерева задач после каждой команды теперь "
                f"{'включен' if new_state else 'выключен'}"
            )
        return "Ничего не изменилось"

    # noinspection PyMethodMayBeStatic
    # Because maybe in the future I will use self
    def get_help_message(self, commands: Tuple[dataclasses_.Command]) -> str:
        return "\n\n".join(
            [
                command.get_full_description(include_heading=True)
                for command in commands
            ]
        )

    # noinspection PyMethodMayBeStatic
    # Because maybe in the future I will use self
    def get_help_message_for_specific_commands(
            self, commands: Tuple[dataclasses_.Command],
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

    def add_task(self, parent_id: int, text: str) -> Optional[str]:
        if (
            parent_id is None
            or
            self.tasks_manager.check_existence(
                models.Task.id == parent_id
            )
        ):
            task = models.Task(text=text, parent_id=parent_id)
            self.tasks_manager.append(task)
            self.tasks_manager.commit()
        else:
            return (
                f"Задачи с ID {parent_id} нет, поэтому новая задача не может "
                f"быть создана"
            )

    def get_tasks_as_string(
            self, indent_size: int = 4, indentation_symbol: str = " ") -> str:
        root_tasks = self.tasks_manager.get_root_tasks()
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

    def delete_tasks(self, task_ids: Tuple[int]) -> Optional[str]:
        errors = []
        for task_id in task_ids:
            try:
                self.tasks_manager.delete(
                    self.tasks_manager.get_task_by_id(task_id)
                )
            except NoResultFound:
                errors.append(
                    f"Задачи с ID {task_id} нет, поэтому она не может быть "
                    f"удалена"
                )
            else:
                self.tasks_manager.commit()
        return "\n".join(errors) if errors else None

    def change_checked_state(
            self, state: bool, task_ids: Tuple[int]) -> Optional[str]:
        errors = []
        for task_id in task_ids:
            try:
                self.tasks_manager.get_task_by_id(
                    task_id
                ).change_state_recursively(is_checked=state)
            except NoResultFound:
                reason = (
                    "она не может быть помечена"
                    if state else
                    "с нее нельзя убрать метку"
                )
                errors.append(f"Задачи с ID {task_id} нет, поэтому {reason}")
            else:
                self.tasks_manager.commit()
        return "\n".join(errors) if errors else None

    def change_collapsing_state(
            self, state: bool, task_ids: Tuple[int]) -> Optional[str]:
        errors = []
        for task_id in task_ids:
            try:
                self.tasks_manager.get_task_by_id(task_id).is_collapsed = state
            except NoResultFound:
                reason = (
                    "она не может быть свернута"
                    if state else
                    "она не может быть развернута"
                )
                errors.append(f"Задачи с ID {task_id} нет, поэтому {reason}")
            else:
                self.tasks_manager.commit()
        return "\n".join(errors) if errors else None

    def edit_task(self, task_id: int, text: str) -> Optional[str]:
        try:
            task = self.tasks_manager.get_task_by_id(task_id)
        except NoResultFound:
            return (
                f"Задачи с ID {task_id} нет, поэтому она не может быть "
                f"изменена!"
            )
        else:
            task.text = text
            self.tasks_manager.commit()

    def change_parent_of_task(
            self, parent_id: int, task_ids: Tuple[int]) -> Optional[str]:
        ids_of_tasks_with_first_error = []
        ids_of_tasks_with_second_error = []
        ids_of_tasks_with_third_error = []
        ids_of_tasks_with_fourth_error = []
        ids_of_successful_tasks = []
        for task_id in task_ids:
            try:
                task = self.tasks_manager.get_task_by_id(task_id)
            except NoResultFound:
                ids_of_tasks_with_first_error.append(task_id)
            else:
                if task_id == parent_id:
                    ids_of_tasks_with_second_error.append(task_id)
                elif (
                    parent_id is not None
                    and self.tasks_manager.check_existence(task.id == parent_id)
                ):
                    ids_of_tasks_with_third_error.append(task_id)
                elif parent_id and task.check_for_subtask(parent_id):
                    ids_of_tasks_with_fourth_error.append(task_id)
                else:
                    ids_of_successful_tasks.append(task_id)
                    task.parent_id = parent_id
        self.tasks_manager.commit()
        first_error_msg = handler_helpers.make_message_with_enumeration(
            ids_of_tasks_with_first_error,
            "Задачи с ID {} нет, поэтому она не может быть изменена!",
            "Задач с ID {} нет, поэтому они не могут быть изменены!"
        )
        second_error_msg = handler_helpers.make_message_with_enumeration(
            ids_of_tasks_with_second_error,
            "Задача с ID {} не может быть родителем самой себя!",
            "Задачи с ID {} не могут быть родителями самих себя!"
        )
        third_error_msg = handler_helpers.make_message_with_enumeration(
            ids_of_tasks_with_third_error,
            "Задачи с ID {} нет, поэтому ее нельзя назначить родителем!",
            "Задач с ID {} нет, поэтому их нельзя назначить родителями!"
        )
        fourth_error_msg = handler_helpers.make_message_with_enumeration(
            ids_of_tasks_with_fourth_error,
            (
                "Задача с ID {} в одной из своих подзадач содержит указанного "
                "родителя, поэтому ее нельзя сделать дочерней задачей этого "
                "родителя!"
            ),
            (
                "Задачи с ID {} в одной из своих подзадач содержат указанного "
                "родителя, поэтому их нельзя сделать дочерней задачей этого "
                "родителя!"
            ),
            ending=(
                " (Пример: Задача 1 содержит Задачу 2. "
                "Задачу 1 нельзя сделать дочерней для Задачи 2.)"
            )
        )
        success_msg = handler_helpers.make_message_with_enumeration(
            ids_of_successful_tasks,
            "У задачи с ID {} была изменена родительская задача!",
            "У задач с ID {} была изменена родительская задача!"
        )
        errors = list(filter(
            None, [
                first_error_msg, second_error_msg, third_error_msg,
                fourth_error_msg, success_msg
            ]
        ))
        return "\n".join(errors) if errors else None

    def show_date(self, task_id: int) -> str:
        try:
            task = self.tasks_manager.get_task_by_id(task_id)
        except NoResultFound:
            return (
                f"Задачи с ID {task_id} нет, поэтому невозможно узнать дату ее "
                f"создания!"
            )
        else:
            return f"Дата создания задачи с ID {task_id}: {task.creation_date}"
