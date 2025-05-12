# Statomata

[![Latest Version](https://img.shields.io/pypi/v/statomata.svg)](https://pypi.python.org/pypi/statomata)
[![Python Supported versions](https://img.shields.io/pypi/pyversions/statomata.svg)](https://pypi.python.org/pypi/statomata)
[![MyPy Strict](https://img.shields.io/badge/mypy-strict-blue)](https://mypy.readthedocs.io/en/stable/getting_started.html#strict-mode-and-configuration)
[![Test Coverage](https://codecov.io/gh/zerlok/statomata/branch/main/graph/badge.svg)](https://codecov.io/gh/zerlok/statomata)
[![Downloads](https://img.shields.io/pypi/dm/statomata.svg)](https://pypistats.org/packages/statomata)
[![GitHub stars](https://img.shields.io/github/stars/zerlok/statomata)](https://github.com/zerlok/statomata/stargazers)

**Statomata** is a strictly typed, flexible library for building and running finite state machines (FSMs) and automata in Python. It provides core automata implementations out of the box and lets you define custom states and state management logic.

## Features

- 🧠 **State Interface & Context:** Follow the state machine pattern with clear, isolated state definitions.
- ⚡ **Built-in Automata:** Unary, async unary, unary iterable, and async iterable automata.
- 🏗 **Custom Automata Support:** Build your own automata with custom state management logic.
- ✅ **Strict Typing:** Designed for type safety and clarity with full type hints.

## Installation

```bash
pip install statomata
```

## Quick Start

Define your states:

```python
from statomata.abc import State, Context


class OpenState(State[str, str]):
    def handle(self, income: str, context: Context[State[str, str]]) -> str:
        if income == "close":
            context.set_state(ClosedState())
            return "Closed"

        return "Still open"


class ClosedState(State[str, str]):
    def handle(self, income: str, context: Context[State[str, str]]) -> str:
        if income == "open":
            context.set_state(OpenState())
            return "Opened"

        return "Still closed"
```

Run the state machine with a built-in automaton:

```python
from statomata.sdk import create_unary_sm

sm = create_unary_sm(OpenState())

print(sm.run("close"))  # Output: Closed
print(sm.run("open"))  # Output: Opened
```
