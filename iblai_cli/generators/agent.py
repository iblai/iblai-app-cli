"""Agent app generator."""

import shutil
from pathlib import Path
from typing import Dict, Any, List

from iblai_cli.generators.base import BaseGenerator


# Files that can be customized by AI enhancement prompts.
ENHANCEABLE_FILES: List[str] = [
    "app/globals.css",
    "app/layout.tsx",
]


class AgentAppGenerator(BaseGenerator):
    """Generator for agent chat applications."""

    def generate(self) -> None:
        """Generate a complete agent app with navbar, sidebar, and chat interface."""
        # Create base directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Generate all files
        self._generate_package_json()
        self._generate_tsconfig()
        self._generate_next_config()
        self._generate_tailwind_config()
        self._generate_postcss_config()
        self._generate_env_files()
        self._generate_gitignore()
        self._generate_eslintrc()
        self._generate_mcp_config()

        # Generate app structure (route groups: (auth) for SSO, (app) for authenticated)
        self._generate_app_layout()
        self._generate_authenticated_layout()
        self._generate_app_page()
        self._generate_sso_login_complete()
        self._generate_platform_layout()
        self._generate_platform_page()
        self._generate_agent_layout()
        self._generate_agent_page()

        # Generate components
        self._generate_app_shell()
        self._generate_iblai_components()
        self._generate_ui_components()

        # Generate hooks
        self._generate_hooks()

        # Generate lib files
        self._generate_lib_files()

        # Generate providers
        self._generate_providers()

        # Generate store
        self._generate_store()

        # Generate public assets
        self._generate_public_assets()

    def _generate_package_json(self) -> None:
        """Generate package.json."""
        content = self.render_template("agent/package.json.j2")
        self.write_file(self.output_dir / "package.json", content)

    def _generate_tsconfig(self) -> None:
        """Generate tsconfig.json."""
        content = self.render_template("agent/tsconfig.json.j2")
        self.write_file(self.output_dir / "tsconfig.json", content)

    def _generate_next_config(self) -> None:
        """Generate next.config.mjs."""
        content = self.render_template("agent/next.config.js.j2")
        self.write_file(self.output_dir / "next.config.mjs", content)

    def _generate_tailwind_config(self) -> None:
        """Generate tailwind.config.ts."""
        content = self.render_template("agent/tailwind.config.ts.j2")
        self.write_file(self.output_dir / "tailwind.config.ts", content)

    def _generate_postcss_config(self) -> None:
        """Generate postcss.config.mjs."""
        content = self.render_template("agent/postcss.config.mjs.j2")
        self.write_file(self.output_dir / "postcss.config.mjs", content)

    def _generate_env_files(self) -> None:
        """Generate environment files."""
        env_example = self.render_template("agent/.env.example.j2")
        self.write_file(self.output_dir / ".env.example", env_example)

        env_js = self.render_template("agent/public/env.js.j2")
        self.write_file(self.output_dir / "public" / "env.js", env_js)

    def _generate_gitignore(self) -> None:
        """Generate .gitignore."""
        content = self.render_template("agent/.gitignore.j2")
        self.write_file(self.output_dir / ".gitignore", content)

    def _generate_eslintrc(self) -> None:
        """Generate .eslintrc.json."""
        content = self.render_template("agent/.eslintrc.json.j2")
        self.write_file(self.output_dir / ".eslintrc.json", content)

    def _generate_mcp_config(self) -> None:
        """Generate .mcp.json for MCP server integration."""
        content = self.render_template("agent/.mcp.json.j2")
        self.write_file(self.output_dir / ".mcp.json", content)

    def _generate_app_layout(self) -> None:
        """Generate app/layout.tsx and globals.css."""
        content = self.render_template("agent/app/layout.tsx.j2")
        self.write_file(self.output_dir / "app" / "layout.tsx", content)

        # Copy globals.css (static file, not a template)
        self._copy_static_file(
            "agent/app/globals.css", self.output_dir / "app" / "globals.css"
        )

    def _generate_authenticated_layout(self) -> None:
        """Generate app/(app)/layout.tsx — wraps authenticated routes with AppShell."""
        content = self.render_template("agent/app/(app)/layout.tsx.j2")
        self.write_file(self.output_dir / "app" / "(app)" / "layout.tsx", content)

    def _generate_app_page(self) -> None:
        """Generate app/(app)/page.tsx — redirect to platform page."""
        content = self.render_template("agent/app/(app)/page.tsx.j2")
        self.write_file(self.output_dir / "app" / "(app)" / "page.tsx", content)

    def _generate_sso_login_complete(self) -> None:
        """Generate app/(auth)/sso-login-complete/page.tsx — SSO callback, NO auth providers."""
        content = self.render_template(
            "agent/app/(auth)/sso-login-complete/page.tsx.j2"
        )
        self.write_file(
            self.output_dir / "app" / "(auth)" / "sso-login-complete" / "page.tsx",
            content,
        )

    def _generate_platform_layout(self) -> None:
        """Generate app/(app)/platform/[tenantKey]/layout.tsx."""
        content = self.render_template(
            "agent/app/(app)/platform/[tenantKey]/layout.tsx.j2"
        )
        self.write_file(
            self.output_dir
            / "app"
            / "(app)"
            / "platform"
            / "[tenantKey]"
            / "layout.tsx",
            content,
        )

    def _generate_platform_page(self) -> None:
        """Generate app/(app)/platform/[tenantKey]/page.tsx."""
        content = self.render_template(
            "agent/app/(app)/platform/[tenantKey]/page.tsx.j2"
        )
        self.write_file(
            self.output_dir / "app" / "(app)" / "platform" / "[tenantKey]" / "page.tsx",
            content,
        )

    def _generate_agent_layout(self) -> None:
        """Generate app/(app)/platform/[tenantKey]/[agentId]/layout.tsx."""
        content = self.render_template(
            "agent/app/(app)/platform/[tenantKey]/[agentId]/layout.tsx.j2"
        )
        self.write_file(
            self.output_dir
            / "app"
            / "(app)"
            / "platform"
            / "[tenantKey]"
            / "[agentId]"
            / "layout.tsx",
            content,
        )

    def _generate_agent_page(self) -> None:
        """Generate app/(app)/platform/[tenantKey]/[agentId]/page.tsx."""
        content = self.render_template(
            "agent/app/(app)/platform/[tenantKey]/[agentId]/page.tsx.j2"
        )
        self.write_file(
            self.output_dir
            / "app"
            / "(app)"
            / "platform"
            / "[tenantKey]"
            / "[agentId]"
            / "page.tsx",
            content,
        )

    def _generate_app_shell(self) -> None:
        """Generate app shell component for client-only provider loading."""
        content = self.render_template("agent/components/app-shell.tsx.j2")
        self.write_file(self.output_dir / "components" / "app-shell.tsx", content)

    def _generate_iblai_components(self) -> None:
        """Generate IBL.ai integration components (chat-widget, profile, notifications)."""
        # ChatWidget — wraps <mentor-ai> Web Component
        # Rendered from the shared `add/chat/` template (same source as iblai add chat)
        from jinja2 import Environment, FileSystemLoader

        add_env = Environment(
            loader=FileSystemLoader(str(self.template_dir / "add")),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        widget_content = add_env.get_template("chat/chat-widget.tsx.j2").render(
            self.get_context()
        )
        self.write_file(
            self.output_dir / "components" / "iblai" / "chat-widget.tsx",
            widget_content,
        )

        # Profile dropdown
        profile_content = add_env.get_template(
            "profile/profile-dropdown.tsx.j2"
        ).render(self.get_context())
        self.write_file(
            self.output_dir / "components" / "iblai" / "profile-dropdown.tsx",
            profile_content,
        )

        # Notification bell
        notif_content = add_env.get_template(
            "notifications/notification-bell.tsx.j2"
        ).render(self.get_context())
        self.write_file(
            self.output_dir / "components" / "iblai" / "notification-bell.tsx",
            notif_content,
        )

    def _generate_ui_components(self) -> None:
        """Generate UI components from web-containers."""
        ui_components = [
            "button",
            "sidebar",
            "dropdown-menu",
            "avatar",
            "tooltip",
            "dialog",
            "input",
            "textarea",
            "skeleton",
            "sheet",
            "separator",
            "sonner",
        ]

        for component in ui_components:
            content = self.render_template(f"agent/components/ui/{component}.tsx.j2")
            self.write_file(
                self.output_dir / "components" / "ui" / f"{component}.tsx", content
            )

    def _generate_hooks(self) -> None:
        """Generate React hooks."""
        content = self.render_template("agent/hooks/use-mobile.ts.j2")
        self.write_file(self.output_dir / "hooks" / "use-mobile.ts", content)

        content = self.render_template("agent/hooks/use-user.ts.j2")
        self.write_file(self.output_dir / "hooks" / "use-user.ts", content)

        # use-copy-to-clipboard removed — ChatWidget handles copying internally

    def _generate_lib_files(self) -> None:
        """Generate lib utility files."""
        # utils.ts
        content = self.render_template("agent/lib/utils.ts.j2")
        self.write_file(self.output_dir / "lib" / "utils.ts", content)

        # config.ts
        content = self.render_template("agent/lib/config.ts.j2")
        self.write_file(self.output_dir / "lib" / "config.ts", content)

        # hooks.ts
        content = self.render_template("agent/lib/hooks.ts.j2")
        self.write_file(self.output_dir / "lib" / "hooks.ts", content)

    def _generate_providers(self) -> None:
        """Generate provider components."""
        # Main providers
        content = self.render_template("agent/providers/index.tsx.j2")
        self.write_file(self.output_dir / "providers" / "index.tsx", content)

        # Store provider
        content = self.render_template("agent/providers/store-provider.tsx.j2")
        self.write_file(self.output_dir / "providers" / "store-provider.tsx", content)

    def _generate_store(self) -> None:
        """Generate Redux store configuration."""
        content = self.render_template("agent/store/index.ts.j2")
        self.write_file(self.output_dir / "store" / "index.ts", content)

    def _generate_public_assets(self) -> None:
        """Generate public assets."""
        # Generate a minimal README in public
        content = self.render_template("agent/public/README.md.j2")
        self.write_file(self.output_dir / "public" / "README.md", content)

    def enhance_with_prompt(self) -> None:
        """Post-process generated files using the AI helper and user prompt."""
        if not self.prompt or not self.ai_helper:
            return

        # Read enhanceable files from disk
        files: Dict[str, str] = {}
        for rel_path in ENHANCEABLE_FILES:
            full_path = self.output_dir / rel_path
            if full_path.exists():
                with open(full_path, "r", encoding="utf-8") as f:
                    files[rel_path] = f.read()

        if not files:
            return

        # Send to LLM for enhancement
        enhanced = self.ai_helper.enhance_app(files, self.prompt, self.get_context())

        # Write enhanced files back
        for rel_path, content in enhanced.items():
            if rel_path in files:  # Only write back files we originally sent
                full_path = self.output_dir / rel_path
                self.write_file(full_path, content)
