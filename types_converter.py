class TypesConverter:

    @staticmethod
    def str_to_bool(string: str) -> bool:
        """
        Converts empty string or "False" to False, any other string to True
        """
        return False if string in ("False", "") else True
