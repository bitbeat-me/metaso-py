"""Chat command."""

from __future__ import annotations

from dataclasses import asdict

import click

from metaso.cli.helpers import async_command, get_client, output_json


@click.command("chat")
@click.argument("message")
@click.option("--model", default="fast", help="Model to use.")
@click.option("--json", "json_output", is_flag=True, help="JSON output.")
@click.pass_context
@async_command
async def chat_cmd(ctx, message, model, json_output):
    """Ask a question (RAG intelligent Q&A)."""
    client = get_client(ctx)
    async with client:
        result = await client.chat.ask(message, model=model)
        if json_output:
            output_json(asdict(result))
        else:
            click.echo(result.answer)
