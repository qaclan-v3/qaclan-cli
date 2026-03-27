import click

from cli.db import init_db
from cli.commands.project import project
from cli.commands.env import env_group
from cli.commands.status import status
from cli.commands.runs import runs_group
from cli.commands.web import web
from cli.commands.api import api


@click.group()
def qaclan():
    """QAClan — QA test management and execution CLI."""
    init_db()


qaclan.add_command(project, "project")
qaclan.add_command(env_group, "env")
qaclan.add_command(status, "status")
qaclan.add_command(runs_group, "runs")
qaclan.add_command(web, "web")
qaclan.add_command(api, "api")


# Also register `run show` at top level as `qaclan run show`
@qaclan.group("run", invoke_without_command=True)
@click.pass_context
def run_group(ctx):
    """View individual run details."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


from cli.commands.runs import run_show
run_group.add_command(run_show, "show")


@qaclan.command()
@click.option('--port', default=7823, help='Port to run on')
@click.option('--host', default='127.0.0.1', help='Host to bind to (use 0.0.0.0 for Docker)')
@click.option('--no-browser', is_flag=True, help='Do not open browser automatically')
def serve(port, host, no_browser):
    """Start the QAClan web UI."""
    import webbrowser
    import threading
    from rich.console import Console
    from web.server import create_app

    console = Console()
    app = create_app()
    url = f'http://localhost:{port}'
    console.print(f'[green]QAClan UI running at {url}[/green] — Press Ctrl+C to stop')
    if not no_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    qaclan()
