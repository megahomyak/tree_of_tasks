import functools
from configparser import ConfigParser
from typing import NoReturn, Tuple, List

from sqlalchemy.orm.exc import NoResultFound

import dataclasses_
import db_apis
import exceptions
import orm_classes
from default_fields_for_settings_file import DEFAULT_FIELDS_FOR_SETTINGS
from ini_worker import MyINIWorker
from types_converter import TypesConverter


class MainLogic:

    def __init__(
            self, tasks_manager: db_apis.TasksManager,
            ini_worker: MyINIWorker) -> None:
        self.tasks_manager = tasks_manager
        ini_worker.load()
        ini_worker.load_fields_if_not_exists(DEFAULT_FIELDS_FOR_SETTINGS)
        ini_worker.save()
        self.settings = ini_worker
        if self.settings.get_auto_showing_state():
            self.print_tasks()
        self.commands = (
            dataclasses_.Command(
                ("автопоказ", "autoshowing"),
                "включает/выключает показ дерева задач после каждого изменения",
                self.change_auto_showing,
                (
                    dataclasses_.Arg(
                        "состояние настройки",
                        dataclasses_.BoolArgType()
                    ),
                )
            ),
            dataclasses_.Command(
                ("помощь", "команды", "help", "commands"),
                "показывает список команд",
                self.show_help_message
            ),
            dataclasses_.Command(
                ("помощь", "команды", "help", "commands"),
                "показывает помощь по конкретным командам",
                self.show_help_message_for_specific_commands,
                (
                    dataclasses_.Arg(
                        "названия команд",
                        dataclasses_.SequenceArgType(
                            dataclasses_.StringArgType()
                        ),
                        (
                            "названия команд должны быть через запятую без "
                            "пробела; название только одной команды тоже можно "
                            "написать; в качестве имени команды можно "
                            "использовать еще и любой псевдоним этой команды"
                        )
                    ),
                )
            ),
            dataclasses_.Command(
                ("добавить", "add", "+"),
                (
                    "добавляет задачу с указанным "
                    "родителем (необязательно) и текстом"
                ),
                self.add_task,
                (
                    dataclasses_.Arg(
                        "ID родителя",
                        dataclasses_.OptionalIntArgType(),
                        "ID задачи, в которую будет вложена добавляемая задача"
                    ),
                    dataclasses_.Arg(
                        "текст новой задачи",
                        dataclasses_.StringArgType()
                    )
                )
            ),
            dataclasses_.Command(
                ("показать", "show", "дерево", "tree"),
                "выводит в консоль дерево задач",
                self.print_tasks
            ),
            dataclasses_.Command(
                ("удалить", "delete", "del", "-", "remove", "убрать", "rm"),
                "удаляет задачу с указанным ID",
                self.delete_tasks,
                (
                    dataclasses_.Arg(
                        "ID задач, которые нужно удалить",
                        dataclasses_.SequenceArgType(
                            dataclasses_.IntArgType()
                        ),
                        (
                            "ID задач должны быть через запятую без пробела; "
                            "ID только одной задачи тоже можно написать"
                        )
                    ),
                )
            ),
            dataclasses_.Command(
                (
                    "пометить", "чек", "отметить", "выполнить",
                    "check", "mark", "complete", "x", "х", "X", "Х"
                ),
                "помечает задачи как выполненные",
                functools.partial(self.change_checked_state, True),
                (
                    dataclasses_.Arg(
                        "ID задач, которые нужно пометить выполненными",
                        dataclasses_.SequenceArgType(
                            dataclasses_.IntArgType()
                        ),
                        (
                            "ID задач должны быть через запятую без пробела; "
                            "ID только одной задачи тоже можно написать"
                        )
                    ),
                )
            ),
            dataclasses_.Command(
                ("убрать метку", "снять метку", "uncheck"),
                "помечает задачи как невыполненные",
                functools.partial(self.change_checked_state, False),
                (
                    dataclasses_.Arg(
                        "ID задач, которые нужно пометить невыполненными",
                        dataclasses_.SequenceArgType(
                            dataclasses_.IntArgType()
                        ),
                        (
                            "ID задач должны быть через запятую без пробела; "
                            "ID только одной задачи тоже можно написать"
                        )
                    ),
                )
            ),
            dataclasses_.Command(
                ("свернуть", "collapse"),
                (
                    "сворачивает задачу, так что все дочерние задачи не будут "
                    "видны"
                ),
                functools.partial(self.change_collapsing_state, True),
                (
                    dataclasses_.Arg(
                        "ID задач, которые нужно свернуть",
                        dataclasses_.SequenceArgType(
                            dataclasses_.IntArgType()
                        ),
                        (
                            "ID задач должны быть через запятую без пробела; "
                            "ID только одной задачи тоже можно написать"
                        )
                    ),
                )
            ),
            dataclasses_.Command(
                ("развернуть", "expand"),
                (
                    "разворачивает задачу, так что все дочерние задачи будут "
                    "видны"
                ),
                functools.partial(self.change_collapsing_state, False),
                (
                    dataclasses_.Arg(
                        "ID задач, которые нужно свернуть",
                        dataclasses_.SequenceArgType(
                            dataclasses_.IntArgType()
                        ),
                        (
                            "ID задач должны быть через запятую без пробела; "
                            "ID только одной задачи тоже можно написать"
                        )
                    ),
                )
            ),
            dataclasses_.Command(
                (
                    "изменить", "отредактировать",
                    "change", "edit"
                ),
                "изменяет текст указанной задачи",
                self.edit_task,
                (
                    dataclasses_.Arg(
                        "ID задачи",
                        dataclasses_.IntArgType()
                    ),
                    dataclasses_.Arg(
                        "текст задачи",
                        dataclasses_.StringArgType()
                    )
                )
            )
        )

    def change_checked_state(self, state: bool, task_ids: Tuple[int]) -> None:
        at_least_one_task_is_changed = False
        for task_id in task_ids:
            try:
                self.tasks_manager.get_task_by_id(task_id).is_checked = state
            except NoResultFound:
                reason = (
                    "она не может быть помечена"
                    if state else
                    "с нее нельзя убрать метку"
                )
                print(f"Задачи с ID {task_id} нет, поэтому {reason}")
            else:
                self.tasks_manager.commit()
                at_least_one_task_is_changed = True
        if at_least_one_task_is_changed:
            if self.settings.get_auto_showing_state():
                self.print_tasks()

    def change_collapsing_state(
            self, state: bool, task_ids: Tuple[int]) -> None:
        at_least_one_task_is_changed = False
        for task_id in task_ids:
            try:
                self.tasks_manager.get_task_by_id(task_id).is_collapsed = state
            except NoResultFound:
                reason = (
                    "она не может быть свернута"
                    if state else
                    "она не может быть развернута"
                )
                print(f"Задачи с ID {task_id} нет, поэтому {reason}")
            else:
                self.tasks_manager.commit()
                at_least_one_task_is_changed = True
        if at_least_one_task_is_changed:
            if self.settings.get_auto_showing_state():
                self.print_tasks()

    def add_task(self, parent_id: int, text: str) -> None:
        if (
            parent_id is None
            or
            self.tasks_manager.check_existence(
                orm_classes.Task.id == parent_id
            )
        ):
            task = orm_classes.Task(text=text, parent_task_id=parent_id)
            self.tasks_manager.append(task)
            self.tasks_manager.commit()
            if self.settings.get_auto_showing_state():
                self.print_tasks()
        else:
            print(
                f"Задачи с ID {parent_id} нет, поэтому новая задача не может "
                f"быть создана"
            )

    def edit_task(self, task_id: int, text: str) -> None:
        try:
            task = self.tasks_manager.get_task_by_id(task_id)
        except NoResultFound:
            print(
                f"Задачи с ID {task_id} нет, поэтому она не может быть "
                f"изменена!"
            )
        else:
            task.text = text
            self.tasks_manager.commit()
            if self.settings.get_auto_showing_state():
                self.print_tasks()

    def delete_tasks(self, task_ids: Tuple[int]) -> None:
        at_least_one_task_is_deleted = False
        for task_id in task_ids:
            try:
                self.tasks_manager.delete(
                    self.tasks_manager.get_task_by_id(task_id)
                )
            except NoResultFound:
                print(
                    f"Задачи с ID {task_id} нет, поэтому она не может быть "
                    f"удалена"
                )
            else:
                self.tasks_manager.commit()
                at_least_one_task_is_deleted = True
        if at_least_one_task_is_deleted:
            if self.settings.get_auto_showing_state():
                self.print_tasks()

    def show_help_message(self) -> None:
        print("\n\n".join(
            [
                command.get_full_description(include_heading=True)
                for command in self.commands
            ]
        ))

    def show_help_message_for_specific_commands(
            self, command_names: Tuple[str]) -> None:
        commands_info = []
        for command_name in command_names:
            for command in self.commands:
                if command_name in command.names:
                    commands_info.append(
                        command.get_full_description(include_heading=True)
                    )
        print("\n\n".join(commands_info))

    def change_auto_showing(self, state: bool) -> None:
        print(
            "Автопоказ дерева задач после каждой команды теперь "
            f"{'включен' if state else 'выключен'}"
        )
        self.settings["auto_showing"] = str(state)
        self.settings.save()

    def print_tasks(self) -> None:
        root_tasks = self.tasks_manager.get_root_tasks()
        if root_tasks:
            print(
                self.get_all_tasks_as_string(
                    root_tasks
                )
            )
        else:
            print("<дерево пустое>")

    def listen_for_commands_infinitely(self) -> NoReturn:
        while True:
            entered_command = input(">>> ")
            for command in self.commands:
                try:
                    command.attached_function(
                        *command.convert_command_to_args(entered_command)
                    )
                except exceptions.ParsingError:
                    pass
                else:
                    break
            else:
                print("Что?")

    def get_all_tasks_as_string(
            self,
            root_tasks: List[orm_classes.Task],
            indentation_level: int = 0,
            indent_size: int = 4) -> str:
        for task in root_tasks:
            task_as_str = (
                f"{' ' * (indentation_level * indent_size)}"
                f"[{'+' if task.is_collapsed else '-'}]"
                f"[{'X' if task.is_checked else ' '}]"
                f"[ID: {task.id}]"
                f" {task.text}"
            )
            if not task.is_collapsed:
                next_tasks_as_str = self.get_all_tasks_as_string(
                    task.nested_tasks,
                    indentation_level + 1,
                    indent_size
                )
                if next_tasks_as_str:
                    return f"{task_as_str}\n{next_tasks_as_str}"
                return task_as_str
            return task_as_str


if __name__ == '__main__':
    main_logic = MainLogic(
        db_apis.TasksManager(
            db_apis.get_sqlalchemy_db_session("sqlite:///tree_of_tasks.db")
        ),
        MyINIWorker(
            ConfigParser(),
            "tree_of_tasks_config.ini",
            TypesConverter()
        )
    )
    main_logic.listen_for_commands_infinitely()
