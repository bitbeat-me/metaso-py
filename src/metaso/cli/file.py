from __future__ import annotations

from dataclasses import asdict

import click

from metaso.cli.helpers import async_command, get_client, output_json


@click.group("file")
def file_group():
    """Manage files in topics."""


@file_group.command("upload")
@click.argument("path", type=click.Path(exists=True))
@click.option("--dir-root-id", required=True, help="dirRootId from topic creation.")
@click.option("--json", "json_output", is_flag=True)
@click.pass_context
@async_command
async def file_upload(ctx, path, dir_root_id, json_output):
    """Upload a file to a topic (requires dirRootId)."""
    client = get_client(ctx)
    async with client:
        f = await client.files.upload(dir_root_id, path)
        if json_output:
            output_json(asdict(f))
        else:
            click.echo(f"Uploaded: {f.file_name} (id: {f.id})")


@file_group.command("progress")
@click.argument("file_id")
@click.pass_context
@async_command
async def file_progress(ctx, file_id):
    """Check file processing progress."""
    client = get_client(ctx)
    async with client:
        p = await client.files.progress(file_id)
        click.echo(f"Progress: {p}%")


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
