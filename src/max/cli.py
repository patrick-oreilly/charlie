import typer
from .app import CharlieApp

app = typer.Typer(help="Local AI for your codebase. Run in any project folder.")

@app.command()
def main(path: str = "."):
    """Launch Charlie in the given project directory."""
    import os
    project_path = os.path.abspath(path)

    if not os.path.isdir(project_path):
        typer.echo(f"Error: {project_path} is not a valid directory.")
        raise typer.Exit(1)

    typer.echo(f"Launching Charlie in: {project_path}")
    charlie_app = CharlieApp(project_path)
    charlie_app.run()

if __name__ == "__main__":
    app()