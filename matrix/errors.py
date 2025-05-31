class MatrixError(Exception):
    pass


class CommandError(MatrixError):
    pass


class CommandNotFoundError(CommandError):
    def __init__(self, cmd):
        super().__init__(f"Command with name '{cmd}' not found")


class MissingArgumentError(CommandError):
    def __init__(self, param):
        super().__init__(f"Missing required argument: '{param.name}'")
