from __future__ import annotations

from dataclasses import asdict

import click

from metaso.cli.helpers import async_command, get_client, output_json


@click.group("book")
def book_group():
    """Manage bookshelf."""


@book_group.command("add")
@click.argument("url")
@click.option("--json", "json_output", is_flag=True)
@click.pass_context
@async_command
async def book_add(ctx, url, json_output):
    """Add a book/PDF from URL."""
    client = get_client(ctx)
    async with client:
        book = await client.bookshelf.add(url)
        if json_output:
            output_json(asdict(book))
        else:
            click.echo(f"Added: {book.title} (id: {book.id})")
