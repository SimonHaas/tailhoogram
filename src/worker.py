"""Cloudflare Workers entrypoint for FastAPI."""

from workers import WorkerEntrypoint

from app import create_app  # noqa: E402


class Default(WorkerEntrypoint):
    """Workers entrypoint that bridges to the FastAPI app."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = None

    def _get_app(self):
        if self._app is None:
            # Create env_getter that reads from Workers environment bindings
            def env_getter(key: str) -> str | None:
                """Get environment variable from Workers runtime."""
                return getattr(self.env, key, None)

            self._app = create_app(env_getter=env_getter)
        return self._app

    async def fetch(self, request):
        import asgi

        app = self._get_app()
        return await asgi.fetch(app, request.js_object, self.env)
