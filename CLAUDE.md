# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Testing:**
- `.venv/bin/pytest` - Run all tests
- `.venv/bin/pytest tests/integration/test_state_machine.py` - Run specific test file
- `.venv/bin/pytest tests/integration/test_state_machine.py::test_function_name` - Run specific test

**Code Quality:**
- `.venv/bin/mypy` - Type checking (strict mode enabled)
- `.venv/bin/ruff check` - Linting
- `.venv/bin/ruff format` - Code formatting
- `.venv/bin/pytest --cov=src --cov-report=term-missing` - Test coverage

**Build:**
- `poetry build` - Build package for distribution
- `poetry install` - Install dependencies and package in development mode

## Architecture Overview

**Statomata** is a strictly typed Python library for building finite state machines (FSMs) and automata. The architecture follows a layered approach:

### Core Abstractions (`src/statomata/abc.py`)
- `State[U_contra, V_co]` - Base state interface that handles income and produces outcome
- `Context[S_contra]` - Allows states to control state machine (set_state, abort)
- `StateMachine[S_co]` - Base state machine interface with current_state property
- `StateMachineSubscriber` - Observer pattern for state machine events

### Implementation Layers
1. **Low-level implementations**: `unary.py`, `iterable.py`, `executor.py` - Core state machine engines
2. **High-level SDK**: `sdk.py` - Factory functions for creating different types of state machines
3. **Declarative DSL**: `declarative/` - Class-based state machine definitions with decorators

### State Machine Types
- **Unary**: Processes single input and returns single output
- **Iterable**: Processes multiple inputs and yields multiple outputs  
- **Async variants**: Async versions of above with anyio integration

### Declarative Style
The `DeclarativeStateMachine` class allows defining state machines using:
- `State` class attributes for states (with `initial=True`, `final=True` options)
- Method decorators like `@state.to(other_state)` for transitions
- Idempotent states with `.idempotent().returns(func)`
- Conditional transitions with `.when(condition)`

### Examples Location
The `examples/state_machines/` directory contains comprehensive examples showing both low-level and declarative approaches for common patterns like order control, traffic lights, and positive number validation.