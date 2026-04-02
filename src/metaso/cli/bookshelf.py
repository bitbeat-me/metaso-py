from __future__ import annotations

from dataclasses import asdict

import click

from metaso.cli.helpers import async_command, get_client, output_json


@click.group("book")
def book_group():
    """Manage bookshelf."""


@book_group.command("add")
@click.argument("url")
@click.option("--topic", required=True, help="Topic ID.")
@click.option("--json", "json_output", is_flag=True)
@click.pass_context
@async_command
async def book_add(ctx, url, topic, json_output):
    """Add a book/PDF from URL."""
    client = get_client(ctx)
    async with client:
        book = await client.bookshelf.add(topic, url)
        if json_output:
            output_json(asdict(book))
        else:
            click.echo(f"Added: {book.title} (id: {book.id})")


@book_group.command("list")
@click.option("--topic", required=True, help="Topic ID.")
@click.option("--json", "json_output", is_flag=True)
@click.pass_context
@async_command
async def book_list(ctx, topic, json_output):
    """List books in a topic."""
    client = get_client(ctx)
    async with client:
        books = await client.bookshelf.list(topic)
        if json_output:
            output_json({"books": [asdict(b) for b in books]})
        else:
            if not books:
                click.echo("No books found.")
            for b in books:
                click.echo(f"  {b.id}  {b.title}  progress={b.progress}%")
