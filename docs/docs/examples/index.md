# Examples

Ready-to-run bots demonstrating common patterns. Each example is a complete, working bot you can copy and adapt.

All examples expect a `config.yaml` file in the same directory:

```yaml
USERNAME: "@yourbot:matrix.org"
PASSWORD: "your_password"
```

| Example | What it shows |
|---------|--------------|
| [Ping Bot](ping.md) | Minimal bot with a single command |
| [Reactions](reaction.md) | Listening to events and reacting to messages |
| [Checks](checks.md) | Restricting commands to specific users |
| [Cooldowns](cooldown.md) | Rate-limiting commands per user |
| [Error Handling](error-handling.md) | Per-command and global error handlers |
| [Extension](extension.md) | Splitting a bot into modules with command groups |
| [Scheduler](scheduler.md) | Running tasks on a cron schedule |
