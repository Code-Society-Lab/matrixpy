# Registry

`Registry` is the shared base class for both `Bot` and `Extension`. It owns all command/group registration logic and event handler wiring, keeping that surface consistent across both entry points.

You typically interact with `Registry` indirectly through the decorators it exposes (`@bot.command`, `@bot.on`, etc.).

::: matrix.registry.Registry
