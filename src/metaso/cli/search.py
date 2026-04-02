"""Search command."""

from __future__ import annotations

from dataclasses import asdict

import click

from metaso.cli.helpers import async_command, get_client, output_json


@click.command("search")
@click.argument("query")
@click.option(
    "--scope",
    "-s",
    default="webpage",
    type=click.Choice(["webpage", "document", "paper", "image", "video", "podcast"]),
)
@click.option(
    "--mode",
    "-m",
    default=None,
    type=click.Choice(["concise", "detail", "research"]),
    help="Search mode (concise/detail/research).",
)
@click.option("--include-summary", is_flag=True, help="Include AI summary.")
@click.option("--size", default=10, type=int, help="Number of results.")
@click.option("--json", "json_output", is_flag=True, help="JSON output.")
@click.option("--stream", is_flag=True, help="Stream results.")
@click.pass_context
@async_command
async def search_cmd(ctx, query, scope, mode, include_summary, size, json_output, stream):
    """Search Metaso AI."""
    client = get_client(ctx)
    async with client:
        extra = {}
        if mode:
            extra["mode"] = mode
        if stream:
            async for chunk in await client.search.query(
                query, scope=scope, stream=True, include_summary=include_summary, size=size,
                **extra,
            ):
                if json_output:
                    output_json(chunk)
                else:
                    text = chunk.get("text", chunk.get("data", ""))
                    if text:
                        click.echo(text, nl=False)
            click.echo()
        else:
            result = await client.search.query(
                query, scope=scope, include_summary=include_summary, size=size,
                **extra,
            )
            if json_output:
                output_json(asdict(result))
            else:
                if result.summary:
                    click.echo(f"\n{result.summary}\n")
                click.echo(f"Found {len(result.results)} results:\n")
                for i, r in enumerate(result.results, 1):
                    click.echo(f"  {i}. {r.title}")
                    click.echo(f"     {r.url}")
                    click.echo(f"     {r.snippet[:100]}")
                    click.echo()
