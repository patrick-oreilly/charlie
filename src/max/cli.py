import typer
from ..tui.app import MaxApp

app = typer.Typer(help="Local AI for your codebase. Run in any project folder.")

@app.command()
def main(path: str = "."):
    """Launch Max in the given project directory."""
    import os
    project_path = os.path.abspath(path)

    if not os.path.isdir(project_path):
        typer.echo(f"Error: {project_path} is not a valid directory.")
        raise typer.Exit(1)

    typer.echo(f"Launching Max in: {project_path}")
    max_app = MaxApp(project_path)
    max_app.run()

if __name__ == "__main__":
    app()