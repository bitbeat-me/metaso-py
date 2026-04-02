from __future__ import annotations

from dataclasses import asdict

import click

from metaso.cli.helpers import async_command, get_client, output_json


@click.group("file")
def file_group():
    """Manage files in topics."""


@file_group.command("upload")
@click.argument("path", type=click.Path(exists=True))
@click.option("--topic", required=True, help="Topic ID.")
@click.option("--json", "json_output", is_flag=True)
@click.pass_context
@async_command
async def file_upload(ctx, path, topic, json_output):
    """Upload a file to a topic."""
    client = get_client(ctx)
    async with client:
        f = await client.files.upload(topic, path)
        if json_output:
            output_json(asdict(f))
        else:
            click.echo(f"Uploaded: {f.file_name} (id: {f.id})")


@file_group.command("list")
@click.option("--topic", required=True, help="Topic ID.")
@click.option("--json", "json_output", is_flag=True)
@click.pass_context
@async_command
async def file_list(ctx, topic, json_output):
    """List files in a topic."""
    client = get_client(ctx)
    async with client:
        files = await client.files.list(topic)
        if json_output:
            output_json({"files": [asdict(f) for f in files]})
        else:
            if not files:
                click.echo("No files found.")
            for f in files:
                click.echo(f"  {f.id}  {f.file_name}  progress={f.progress}%")


@file_group.command("delete")
@click.argument("file_id")
@click.pass_context
@async_command
async def file_delete(ctx, file_id):
    """Delete a file."""
    client = get_client(ctx)
    async with client:
        success = await client.files.delete(file_id)
        click.echo(f"Deleted: {file_id}" if success else f"Failed: {file_id}")
