ampdup
======

A type-hinted async python mpd client library.


Summary
=======

`ampdup` is an async/await based MPD library.

It is fully type-hinted and MPD responses are typed as well, so it is able to
play nicely with `mypy` and autocompletion such as what is provided by `jedi`.

Examples
========

First a basic usage example. `make()` returns a connected client as a context
manager that handles disconnection automatically.

```python
async def main():
    async with MPDClient.make('localhost', 6600) as m:
        await m.play()
```

The IdleClient class provides the `idle()` function. Since `ampdup` is
`async`/`await`-based this loop can easily run concurrently with other
operations.

```
async def observe_state():
    async with IdleClient.make('localhost', 6600) as i:
        while True:
            changed = await i.idle()
            handle_changes(changed)
```

Todo
====

- [ ] Support command lists.
- [ ] Support connecting through Unix socket.
- [ ] Support the more obscure MPD features such as partitions.
