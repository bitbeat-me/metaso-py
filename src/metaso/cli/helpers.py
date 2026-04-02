"""Shared CLI utilities."""

from __future__ import annotations

import asyncio
import functools
import json
from dataclasses import asdict
from typing import Any

import click

from metaso.client import MetasoClient


def async_command(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def get_client(ctx: click.Context) -> MetasoClient:
    profile = ctx.obj.get("profile") if ctx.obj else None
    return MetasoClient.auto(profile=profile)


def output_json(data: Any) -> None:
    if hasattr(data, "__dataclass_fields__"):
        data = asdict(data)
    click.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))
