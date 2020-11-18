from typing import Tuple, Dict, List, Callable

from sqlalchemy.orm.exc import NoResultFound

from handlers import handler_helpers
from handlers.handler_helpers import HandlingResult
from ini_worker import MyINIWorker
from lexer import lexer_classes
from orm import models
from orm.db_apis import TasksManager


class Handlers:

    def __init__(self, ini_worker: MyINIWorker, tasks_manager: TasksManager):
        self.ini_worker = ini_worker
        self.tasks_manager = tasks_manager

    def change_auto_showing(self, new_state: bool) -> HandlingResult:
        new_state_str = str(new_state)
        if self.ini_worker["auto_showing"] != new_state_str:
            self.ini_worker["auto_showing"] = new_state_str
            self.ini_worker.save()
            return HandlingResult(
                (
                    "Автопоказ дерева задач после каждой команды теперь "
                    f"{'включен' if new_state else 'выключен'}"
                ), whether_to_print_a_tree=False
            )
        return HandlingResult(
            "Ничего не изменилось", whether_to_print_a_tree=False
        )

    # noinspection PyMethodMayBeStatic
    # Because maybe in the future I will use self
    def get_help_message(
            self, commands: Tuple[lexer_classes.Command]) -> HandlingResult:
        return HandlingResult(
            "\n\n".join([
                command.get_full_description(include_heading=True)
                for command in commands
            ]), whether_to_print_a_tree=False
        )

    # noinspection PyMethodMayBeStatic
    # Because maybe in the future I will use self
    def get_help_message_for_specific_commands(
            self, command_descriptions: Dict[str, List[Callable]],
            command_names: Tuple[str, ...]) -> HandlingResult:
        command_descriptions_as_strings = []
        quoted_not_found_commands: List[str] = []
        for command_name in command_names:
            try:
                command_descriptions_as_strings.extend(
                    (
                        # Here desc_func is a Command.get_full_description,
                        # if I set Command.get_full_description as a type -
                        # I wouldn't get any IDE hints anyway
                        desc_func(include_heading=True)
                        for desc_func in command_descriptions[command_name]
                    )
                )
            except KeyError:
                quoted_not_found_commands.append(f"\"{command_name}\"")
        return HandlingResult(
            "\n\n".join(
                (
                    (
                        f"Команда с названием "
                        f"{quoted_not_found_commands[0]} не найдена!"
                        if len(quoted_not_found_commands) == 1 else
                        f"Команды с названиями "
                        f"{', '.join(quoted_not_found_commands)} не найдены!"
                    ), *command_descriptions_as_strings
                ) if quoted_not_found_commands else
                command_descriptions_as_strings
            ), whether_to_print_a_tree=False
        )

    def add_task(self, parent_id: int, text: str) -> HandlingResult:
        if (
            parent_id is None
            or self.tasks_manager.check_existence(models.Task.id == parent_id)
        ):
            task = models.Task(text=text, parent_id=parent_id)
            self.tasks_manager.add(task)
            self.tasks_manager.commit()
            return HandlingResult(
                "Задача создана!", whether_to_print_a_tree=True
            )
        else:
            return HandlingResult(
                (
                    f"Задачи с ID {parent_id} нет, поэтому новая задача не "
                    f"может быть создана"
                ), whether_to_print_a_tree=False
            )

    def get_tasks_as_string(
            self, indent_size: int = 4,
            indentation_symbol: str = " ") -> HandlingResult:
        root_tasks = self.tasks_manager.get_root_tasks()
        if root_tasks:
            return HandlingResult(
                "\n".join(handler_helpers.get_tasks_as_strings(
                    root_tasks,
                    indent_size=indent_size,
                    indentation_symbol=indentation_symbol
                )), whether_to_print_a_tree=False
            )
        else:
            return HandlingResult(
                "<дерево пустое>", whether_to_print_a_tree=False
            )

    def delete_tasks(self, task_ids: Tuple[int]) -> HandlingResult:
        ids_of_non_existing_tasks = []
        ids_of_successful_tasks = []
        for task_id in task_ids:
            try:
                self.tasks_manager.delete(
                    self.tasks_manager.get_task_by_id(task_id)
                )
            except NoResultFound:
                ids_of_non_existing_tasks.append(task_id)
            else:
                self.tasks_manager.commit()
                ids_of_successful_tasks.append(task_id)
        return HandlingResult(
            handler_helpers.make_optional_string_from_optional_strings(
                [
                    handler_helpers.make_strings_with_enumeration(
                        ids_of_non_existing_tasks, (
                            "Задачи с ID {} нет, поэтому она не может быть "
                            "удалена!"
                        ),
                        "Задач с ID {} нет, поэтому они не могут быть удалены!"
                    ),
                    handler_helpers.make_strings_with_enumeration(
                        ids_of_successful_tasks,
                        "Задача с ID {} успешно удалена!",
                        "Задачи с ID {} успешно удалены!"
                    )
                ]
            ), whether_to_print_a_tree=bool(ids_of_successful_tasks)
        )

    def change_bool_field_state(
            self, field: handler_helpers.BooleanTaskFields, state: bool,
            task_ids: Tuple[int]) -> HandlingResult:
        ids_of_non_existing_tasks = []
        ids_of_tasks_where_nothing_changed = []
        ids_of_successful_tasks = []
        for task_id in task_ids:
            try:
                task = self.tasks_manager.get_task_by_id(
                    task_id
                )
            except NoResultFound:
                ids_of_non_existing_tasks.append(task_id)
            else:
                if field is handler_helpers.BooleanTaskFields.IS_CHECKED:
                    something_changed = task.change_state_recursively(
                        is_checked=state
                    )
                elif field is handler_helpers.BooleanTaskFields.IS_COLLAPSED:
                    if task.is_collapsed == state:
                        something_changed = False
                    else:
                        something_changed = True
                        task.is_collapsed = state
                else:
                    raise NotImplementedError(f"Unknown field \"{field}\"!")
                if something_changed:
                    ids_of_successful_tasks.append(task_id)
                else:
                    ids_of_tasks_where_nothing_changed.append(task_id)
        if ids_of_successful_tasks:
            self.tasks_manager.commit()
        return HandlingResult(
            handler_helpers.make_optional_string_from_optional_strings(
                [
                    handler_helpers.make_strings_with_enumeration(
                        ids_of_non_existing_tasks, (
                            "Задачи с ID {} нет, поэтому ей нельзя сменить "
                            "состояние!"
                        ), (
                            "Задач с ID {} нет, поэтому им нельзя сменить "
                            "состояние!"
                        )
                    ),
                    handler_helpers.make_strings_with_enumeration(
                        ids_of_tasks_where_nothing_changed,
                        "У задачи с ID {} ничего не изменилось!",
                        "У задач с ID {} ничего не изменилось!"
                    ),
                    handler_helpers.make_strings_with_enumeration(
                        ids_of_successful_tasks,
                        "Состояние задачи с ID {} успешно изменено!",
                        "Состояние задач с ID {} успешно изменено!"
                    )
                ]
            ), whether_to_print_a_tree=bool(ids_of_successful_tasks)
        )

    def edit_task(self, task_id: int, text: str) -> HandlingResult:
        try:
            task = self.tasks_manager.get_task_by_id(task_id)
        except NoResultFound:
            return HandlingResult(
                (
                    f"Задачи с ID {task_id} нет, поэтому она не может быть "
                    f"изменена!"
                ), whether_to_print_a_tree=False
            )
        else:
            task.text = text
            self.tasks_manager.commit()
            return HandlingResult(
                "Задача изменена!", whether_to_print_a_tree=True
            )

    def change_parent_of_task(
            self, parent_id: int, task_ids: Tuple[int]) -> HandlingResult:
        ids_of_tasks_with_first_error = []
        ids_of_tasks_with_second_error = []
        ids_of_tasks_with_third_error = []
        ids_of_tasks_with_fourth_error = []
        ids_of_tasks_with_fifth_error = []
        ids_of_successful_tasks = []
        for task_id in task_ids:
            try:
                task = self.tasks_manager.get_task_by_id(task_id)
            except NoResultFound:
                ids_of_tasks_with_first_error.append(task_id)
            else:
                if task_id == parent_id:
                    ids_of_tasks_with_second_error.append(task_id)
                elif task.parent_id == parent_id:
                    ids_of_tasks_with_third_error.append(task_id)
                elif (
                    parent_id is not None
                    and self.tasks_manager.check_existence(task.id == parent_id)
                ):
                    ids_of_tasks_with_fourth_error.append(task_id)
                elif parent_id and task.check_for_subtask(parent_id):
                    ids_of_tasks_with_fifth_error.append(task_id)
                else:
                    ids_of_successful_tasks.append(task_id)
                    task.parent_id = parent_id
        self.tasks_manager.commit()
        return HandlingResult(
            handler_helpers.make_optional_string_from_optional_strings(
                [
                    handler_helpers.make_strings_with_enumeration(
                        ids_of_tasks_with_first_error, (
                            "Задачи с ID {} нет, поэтому она не может быть "
                            "изменена!"
                        ),
                        "Задач с ID {} нет, поэтому они не могут быть изменены!"
                    ),
                    handler_helpers.make_strings_with_enumeration(
                        ids_of_tasks_with_second_error,
                        "Задача с ID {} не может быть родителем самой себя!",
                        "Задачи с ID {} не могут быть родителями самих себя!"
                    ),
                    handler_helpers.make_strings_with_enumeration(
                        ids_of_tasks_with_third_error, (
                            "Задача с ID {} уже содержит в качестве родителя "
                            "задачу с указанным ID родителя!"
                        ), (
                            "Задачи с ID {} уже содержат в качестве родителя "
                            "задачу с указанным ID родителя!"
                        ), ending=(
                            " (Пример: указанный ID родительской задачи - 1, "
                            "Задача 2 уже имеет родителя, и это - Задача 1)"
                        )
                    ),
                    handler_helpers.make_strings_with_enumeration(
                        ids_of_tasks_with_fourth_error, (
                            "Задачи с ID {} нет, поэтому ее нельзя назначить "
                            "родителем!"
                        ), (
                            "Задач с ID {} нет, поэтому их нельзя назначить "
                            "родителями!"
                        )
                    ),
                    handler_helpers.make_strings_with_enumeration(
                        ids_of_tasks_with_fifth_error, (
                            "Задача с ID {} в одной из своих подзадач содержит "
                            "указанного родителя, поэтому ее нельзя сделать "
                            "дочерней задачей этого родителя!"
                        ), (
                            "Задачи с ID {} в одной из своих подзадач содержат "
                            "указанного родителя, поэтому их нельзя сделать "
                            "дочерней задачей этого родителя!"
                        ), ending=(
                            " (Пример: Задача 1 содержит Задачу 2. "
                            "Задачу 1 нельзя сделать дочерней для Задачи 2.)"
                        )
                    ),
                    handler_helpers.make_strings_with_enumeration(
                        ids_of_successful_tasks,
                        "У задачи с ID {} была изменена родительская задача!",
                        "У задач с ID {} была изменена родительская задача!"
                    )
                ]
            ), whether_to_print_a_tree=bool(ids_of_successful_tasks)
        )

    def show_date(self, task_id: int) -> HandlingResult:
        try:
            task = self.tasks_manager.get_task_by_id(task_id)
        except NoResultFound:
            return HandlingResult(
                (
                    f"Задачи с ID {task_id} нет, поэтому невозможно узнать "
                    f"дату ее создания!"
                ), whether_to_print_a_tree=False
            )
        else:
            return HandlingResult(
                f"Дата создания задачи с ID {task_id}: {task.creation_date}",
                whether_to_print_a_tree=False
            )
