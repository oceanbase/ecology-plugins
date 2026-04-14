from __future__ import annotations

import click


def root_context(ctx: click.Context) -> click.Context:
    while ctx.parent is not None:
        ctx = ctx.parent
    return ctx


def output_fmt(ctx: click.Context) -> str:
    r = root_context(ctx)
    r.ensure_object(dict)
    return str(r.obj.get("format") or "json")
