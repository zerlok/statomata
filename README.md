from statomata.exception import InvalidStateErrorfrom contextlib import suppressfrom statomata.exception import InvalidStateErrorfrom contextlib import suppress

# Statomata

[![Latest Version](https://img.shields.io/pypi/v/statomata.svg)](https://pypi.python.org/pypi/statomata)
[![Python Supported versions](https://img.shields.io/pypi/pyversions/statomata.svg)](https://pypi.python.org/pypi/statomata)
[![MyPy Strict](https://img.shields.io/badge/mypy-strict-blue)](https://mypy.readthedocs.io/en/stable/getting_started.html#strict-mode-and-configuration)
[![Test Coverage](https://codecov.io/gh/zerlok/statomata/branch/main/graph/badge.svg)](https://codecov.io/gh/zerlok/statomata)
[![Downloads](https://img.shields.io/pypi/dm/statomata.svg)](https://pypistats.org/packages/statomata)
[![GitHub stars](https://img.shields.io/github/stars/zerlok/statomata)](https://github.com/zerlok/statomata/stargazers)

**Statomata** is a strictly typed, flexible library for building and running finite state machines (FSMs) and automata
in Python. It provides core automata implementations out of the box and lets you define custom states and state
management logic.

## Features

- 🧠 **State Interface & Context:** Follow the state machine OOP pattern with clear, isolated state definitions.
- ⚡ **Built-in Automata:** feel free to use one of the predefined automata classes from SDK.
- 🏗 **Custom Automata Support:** Build your own automata with custom state management logic. You can choose declarative
  style or built custom automata using provided interfaces.
- ✅ **Strict Typing:** Designed for type safety and clarity with full type hints.

## Installation

```bash
pip install statomata
```

## Quick Start

Use high-level declarative style:

```python
from statomata.declarative import DeclarativeStateMachine, State


class OpenCloseExample(DeclarativeStateMachine):
    closed = State(initial=True)
    opened = State()
    
    @closed.to(opened)
    def open(self) -> str:
        return "Opened"
    
    @opened.to(closed)
    def close(self) -> str:
        return "Closed"
```

Run the state machine with a built-in automaton:

```python
from contextlib import suppress
from statomata.exception import InvalidStateError

sm = OpenCloseExample()

print(sm.open())  # Output: Opened
print(sm.close())  # Output: Closed

with suppress(InvalidStateError):
    sm.close()
```

Or you can use low-level style:

```python
from statomata.abc import State, Context
from statomata.exception import InvalidStateError


class OpenState(State[str, str]):
    def handle(self, income: str, context: Context[State[str, str]]) -> str:
        if income != "close":
            raise InvalidStateError(self, message="already opened")
        
        context.set_state(ClosedState())
        return "Closed"


class ClosedState(State[str, str]):
    def handle(self, income: str, context: Context[State[str, str]]) -> str:
        if income != "open":
            raise InvalidStateError(self,message="already closed")

        context.set_state(OpenState())
        return "Opened"
```

Run the state machine with a built-in automaton:

```python
from contextlib import suppress

from statomata.exception import InvalidStateError
from statomata.sdk import create_unary_sm

sm = create_unary_sm(ClosedState())

print(sm.run("open"))  # Output: Opened
print(sm.run("close"))  # Output: Closed

with suppress(InvalidStateError):
    sm.run("close")
```
