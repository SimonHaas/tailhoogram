"""Application entry point."""

from pathlib import Path

from dotenv import load_dotenv

# Load .env file before importing settings (for local development)
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file)

from app import create_app  # noqa: E402

app = create_app()


def run() -> None:
    """Run the application."""
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
    )


if __name__ == "__main__":
    run()
