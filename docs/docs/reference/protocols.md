# Protocols

The `protocols` module defines structural interfaces (PEPs 544) used internally to decouple components. `BotLike` is the protocol that `Extension` and other subsystems accept instead of a concrete `Bot`, making them easier to test in isolation.

::: matrix.protocols.BotLike
