from typing import Any

from lexer.lexer_classes import BaseMetadata, ConstantContext


class CommandsMetadata(BaseMetadata):

    @staticmethod
    def get_data_from_context(context: ConstantContext) -> Any:
        return context.commands
