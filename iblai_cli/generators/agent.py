"""Agent app generator — extends the base template with a full-screen ChatWidget."""

from jinja2 import Environment, FileSystemLoader

from iblai_cli.generators.base_app import BaseAppGenerator


class AgentAppGenerator(BaseAppGenerator):
    """
    Generate a Next.js app with IBL.ai authentication and a full-screen
    ChatWidget on the home page.

    The agent template extends the base template, overriding only:
      - ``app/(app)/page.tsx`` — full-screen ChatWidget using mentor ID from config
      - ``lib/config.ts``      — adds ``defaultAgentId()`` and ``agentUrl()``
      - ``.env.example``       — adds ``NEXT_PUBLIC_DEFAULT_AGENT_ID``
      - ``package.json``       — same as base (ensures app_name is rendered)
    """

    # Files that the AI ``--prompt`` enhancement may modify.
    ENHANCEABLE_FILES = [
        "app/globals.css",
        "app/(app)/page.tsx",
    ]

    def get_context(self):
        ctx = super().get_context()
        ctx["mentor_id"] = self.mentor_id
        ctx["has_mentor_id"] = bool(self.mentor_id)
        return ctx

    def generate(self) -> None:
        """Generate the complete base app, then overlay agent-specific files."""
        # 1. Generate the full base app (auth, providers, store, components, skills…)
        super().generate()

        # 2. Set up a Jinja2 loader that searches agent/ first, then falls back
        #    to base/ and shared/ so we can reference any shared template.
        agent_env = Environment(
            loader=FileSystemLoader(
                [
                    str(self.template_dir / "agent"),
                    str(self.template_dir / "base"),
                    str(self.template_dir / "shared"),
                    str(self.template_dir / "add"),
                ]
            ),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        ctx = self.get_context()

        def _render(path: str) -> str:
            return agent_env.get_template(path).render(ctx)

        # 3. Overwrite files with agent-specific versions
        self._write("app/(app)/page.tsx", _render("app/(app)/page.tsx.j2"))
        self._write("lib/config.ts", _render("lib/config.ts.j2"))
        self._write(".env.example", _render(".env.example.j2"))
        self._write("package.json", _render("package.json.j2"))
