from statomata.declarative.builder import State
from statomata.declarative.state_machine import DeclarativeStateMachine


class Transitions(DeclarativeStateMachine):
    a, b, c, d, e, f = State(initial=True), State(), State(), State(), State(), State(final=True)

    @a.to(b)
    @c.to(d)
    @e.to(f)
    def from_ace_to_bdf(self) -> None:
        pass

    @b.to(c)
    def from_b_to_c(self) -> None:
        pass
