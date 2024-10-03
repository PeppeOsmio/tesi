from uuid import UUID


class UserNotFoundError(Exception):
    def __init__(self) -> None:
        super().__init__()


class UsernameExistsError(Exception):
    def __init__(self) -> None:
        super().__init__()


class EmailExistsError(Exception):
    def __init__(self) -> None:
        super().__init__()


class InvalidCursorError(Exception):
    pass
