from statomata.declarative.builder import State
from statomata.declarative.state_machine import DeclarativeStateMachine


class TransitionCases(DeclarativeStateMachine):
    a, b, c, d, e, f = State(initial=True), State(), State(), State(), State(), State(final=True)

    def __init__(self, *, allow_d_to_e: bool) -> None:
        super().__init__()
        self.allow_d_to_e = allow_d_to_e

    @property
    def is_d_to_e_allowed(self) -> bool:
        return self.allow_d_to_e

    @a.to(b)
    @c.to(d)
    @e.to(f)
    def from_ace_to_bdf(self) -> None:
        pass

    @b.to(c)
    def from_b_to_c(self) -> None:
        pass

    @d.to(e).when(is_d_to_e_allowed)
    def from_d_to_e(self) -> None:
        pass
