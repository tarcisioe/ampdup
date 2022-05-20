"""Tasks for summon."""
import typer
from summon.exec import execute
from summon.tasks import task


@task
def install_dev_tools(
    ci: bool = typer.Option(  # noqa: B008
        default=False, help='Avoid installing tools that are unneeded for CI jobs.'
    )
) -> None:
    """Install development tools."""
    extra_deps = ['pre-commit'] if not ci else []

    execute(
        [
            'poetry',
            'run',
            'pip',
            'install',
            'black',
            'flake8',
            'flake8-bugbear',
            'isort>=5.0.0',
            'mypy',
            'pylint',
            'pylint-quotes',
            *extra_deps,
        ],
    )

    if not ci:
        execute('pre-commit install')
