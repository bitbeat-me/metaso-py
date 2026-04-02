from __future__ import annotations

from dataclasses import asdict

import click

from metaso.cli.helpers import async_command, get_client, output_json


@click.group("topic")
def topic_group():
    """Manage knowledge base topics."""


@topic_group.command("create")
@click.argument("name")
@click.option("--json", "json_output", is_flag=True)
@click.pass_context
@async_command
async def topic_create(ctx, name, json_output):
    """Create a new topic."""
    client = get_client(ctx)
    async with client:
        topic = await client.topics.create(name)
        if json_output:
            output_json(asdict(topic))
        else:
            click.echo(f"Created topic: {topic.name}")
            click.echo(f"  id: {topic.id}")
            click.echo(f"  dirRootId: {topic.dir_root_id}")


@topic_group.command("delete")
@click.argument("topic_id")
@click.pass_context
@async_command
async def topic_delete(ctx, topic_id):
    """Delete a topic."""
    client = get_client(ctx)
    async with client:
        success = await client.topics.delete(topic_id)
        click.echo(f"Deleted topic: {topic_id}" if success else f"Failed to delete: {topic_id}")
