from typing_extensions import TypeAlias, override

from statomata.abc import Context
from statomata.sdk import create_unary_sm
from statomata.unary import UnaryState, UnaryStateMachine

AuthInput: TypeAlias = dict[str, object]
AuthMachine: TypeAlias = UnaryStateMachine[AuthInput, str]


class WaitingForUsername(UnaryState[AuthInput, str]):
    @override
    def handle(self, income: AuthInput, context: Context[UnaryState[AuthInput, str]]) -> str:
        if "username" not in income:
            context.defer()
            return "Username is missing."

        username = str(income["username"])
        # Switch state
        context.set_state(WaitingForPassword(username))
        # Recall deferred messages (maybe one had the password already)
        context.recall()

        if "password" in income:
            context.defer()

        return f"Username '{username}' accepted."


class WaitingForPassword(UnaryState[AuthInput, str]):
    def __init__(self, username: str) -> None:
        self.__username = username

    @override
    def handle(self, income: AuthInput, context: Context[UnaryState[AuthInput, str]]) -> str:
        if "password" not in income:
            context.defer()
            return "Password is missing."

        password = income["password"]
        if password == "secret":
            context.set_state(Authenticated(self.__username))
            context.recall()

            if "data" in income:
                context.defer()

            return f"User '{self.__username}' authenticated."

        else:
            return "Invalid password."


class Authenticated(UnaryState[AuthInput, str]):
    def __init__(self, username: str) -> None:
        self.__username = username

    @override
    def handle(self, income: AuthInput, context: Context[UnaryState[AuthInput, str]]) -> str:
        context.recall()
        data = income.get("data")
        return f"Welcome {self.__username}, processing data: {data}"


def create_auth_machine() -> AuthMachine:
    return create_unary_sm(WaitingForUsername())


def main() -> None:
    sm = create_auth_machine()
    values: list[dict[str, object]] = [{"password": "secret", "username": "John", "data": "ok"}]
    for income in values:
        print(sm.run(income))


if __name__ == "__main__":
    main()
