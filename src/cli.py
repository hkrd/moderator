import logging
import platform
import click
import subprocess
from pathlib import Path
from src.scripts import file_converter
from src.scripts import content_moderator
import src.scripts.test_client as test_client

# Define paths to key files
PROJECT_ROOT = Path(__file__).parent


@click.group()
def cli():
    """Central CLI for interacting with the project."""
    pass


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path())
def parse(input_file: str, output_file: str) -> None:
    """Parse the input file."""
    click.echo(f"Parsing file {input_file}.")
    # Assuming you have a parse function in one of your scripts
    file_converter.convert_to_json(input_file, output_file)


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path())
@click.option("--categories", type=str, required=True)
@click.option(
    "--num-threads",
    type=int,
    default=15,
    show_default=True,
    help="Number of concurrent processing threads.",
)
@click.option(
    "--api-key-file",
    type=click.Path(exists=True),
    default="openai_key.txt",
    help="File containing the OpenAI API key.",
)
@click.option("--debug", is_flag=True, help="Enable DEBUG mode for logging")
@click.option("--verbose", is_flag=True, help="Enable INFO mode for logging")
def moderate(
    input_file: str,
    output_file: str,
    categories: str,
    num_threads: int,
    api_key_file: str,
    debug: bool,
    verbose: bool,
) -> None:
    """Moderate a file using the specified moderation categories."""

    # Set logging level based on flags
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    elif verbose:
        logging.basicConfig(level=logging.INFO)

    click.echo(
        f"Moderating file {input_file} with categories {categories} using {num_threads} threads."
    )
    content_moderator.moderate_conversations(
        input_file, output_file, categories, num_threads, api_key_file
    )


@click.command()
@click.option("--host", default="127.0.0.1", help="Host for server")
@click.option("--port", default=8000, help="Port for FastAPI server")
@click.option("--reload", is_flag=True, help="Enable auto-reload for FastAPI server")
@click.option("--daemon", is_flag=True, help="Run the server as a daemon.")
def start_server(host: str, port: int, reload: bool, daemon: bool) -> None:
    """Start the FastAPI moderation server."""
    command = ["uvicorn", "src.app:app", f"--host={host}", f"--port={port}"]
    if reload:
        command.append("--reload")
    if daemon:
        # Run the command as a daemon
        with open("server.log", "w") as log_file:
            subprocess.Popen(command, stdout=log_file, stderr=log_file)
        click.echo(
            f"Server started in daemon mode on {host}:{port}. Logs are being written to server.log"
        )
    else:
        subprocess.run(command)


@click.command()
@click.option("--port", default=8000, help="Port for FastAPI server")
def stop_server(port: int) -> None:
    """Start or stop the FastAPI server."""
    system = platform.system()

    if system == "Windows":
        # Windows command to kill the process using a specific port
        click.echo(f"Stopping server on port {port} using taskkill")
        subprocess.run(["netstat", "-ano", "|", "findstr", f":{port}"], shell=True)
        output = subprocess.check_output(["netstat", "-ano"], shell=True).decode()
        for line in output.splitlines():
            if f":{port}" in line:
                pid = int(line.strip().split()[-1])
                subprocess.run(["taskkill", "/PID", str(pid), "/F"])
                click.echo(f"Killed process with PID {pid} on port {port}")
                return
        click.echo(f"No process found running on port {port}")

    else:
        # Unix-based systems command to kill the process using a specific port
        click.echo(f"Stopping server on port {port} using fuser")
        subprocess.run(["fuser", "-k", f"{port}/tcp"])


@click.command()
@click.argument("file_results", type=click.Path(exists=True, dir_okay=False))
@click.argument("api_key", type=str)
@click.option("--api_url", default="http://localhost:8000/moderate", type=str)
@click.option("--categories", type=str)
@click.option(
    "--num-threads", default=15, help="Number of threads to use for parallel requests"
)
def test_moderation(
    file_results: str, api_key: str, api_url: str, categories: str, num_threads: int
) -> None:
    """Test moderation API by comparing with file."""
    click.echo(f"Testing moderation using file {file_results} against API {api_url}.")
    test_client.main(file_results, api_url, api_key, categories, num_threads)


# Add commands to the CLI group
cli.add_command(parse)
cli.add_command(moderate)
cli.add_command(start_server)
cli.add_command(stop_server)
cli.add_command(test_moderation)
