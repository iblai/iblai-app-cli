"""Base generator class for all app templates."""

import os
import sys
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, Template


class BaseGenerator:
    """Base class for app generators."""

    def __init__(
        self,
        app_name: str,
        platform_key: str,
        output_dir: str,
        mentor_id: Optional[str] = None,
        use_ai: bool = False,
        ai_provider: Optional[str] = None,
        openai_key: Optional[str] = None,
        anthropic_key: Optional[str] = None,
        prompt: Optional[str] = None,
        ai_model: Optional[str] = None,
        ai_temperature: Optional[float] = None,
        ai_max_tokens: Optional[int] = None,
        builds: bool = False,
    ):
        """
        Initialize the generator.

        Args:
            app_name: Name of the app
            platform_key: Platform/tenant key
            output_dir: Output directory path
            mentor_id: Optional mentor/agent ID
            use_ai: Whether to use AI assistance
            ai_provider: AI provider ("openai" or "anthropic")
            openai_key: OpenAI API key
            anthropic_key: Anthropic API key
            prompt: Optional enhancement prompt for AI customization
            ai_model: Override the default AI model
            ai_temperature: Override the default AI temperature
            ai_max_tokens: Override the default AI max_tokens
        """
        self.app_name = app_name
        self.platform_key = platform_key
        self.mentor_id = mentor_id
        self.output_dir = Path(output_dir)
        # Support both source and PyInstaller frozen binary paths
        if getattr(sys, "_MEIPASS", None):
            self.template_dir = Path(sys._MEIPASS) / "iblai" / "templates"
        else:
            self.template_dir = Path(__file__).parent.parent / "templates"
        self.use_ai = use_ai
        self.ai_provider = ai_provider
        self.openai_key = openai_key
        self.anthropic_key = anthropic_key
        self.prompt = prompt
        self.ai_model = ai_model
        self.ai_temperature = ai_temperature
        self.ai_max_tokens = ai_max_tokens
        self.builds = builds

        # Initialize AI helper if AI is enabled
        self.ai_helper = None
        if self.use_ai and self.ai_provider:
            from iblai.ai_helper import AIHelper

            self.ai_helper = AIHelper(
                provider=self.ai_provider,
                anthropic_key=self.anthropic_key,
                openai_key=self.openai_key,
                model=self.ai_model,
                temperature=self.ai_temperature,
                max_tokens=self.ai_max_tokens,
            )

    def get_context(self) -> Dict[str, Any]:
        """
        Get the template context variables.

        Returns:
            Dictionary of context variables for template rendering
        """
        return {
            "app_name": self.app_name,
            "platform_key": self.platform_key,
            "mentor_id": self.mentor_id,
            "has_mentor_id": bool(self.mentor_id),
            "builds": self.builds,
        }

    def create_directory_structure(
        self, structure: Dict[str, Any], base_path: Optional[Path] = None
    ) -> None:
        """
        Create directory structure from a nested dictionary.

        Args:
            structure: Nested dictionary representing directory structure
            base_path: Base path to create structure in (defaults to output_dir)
        """
        if base_path is None:
            base_path = self.output_dir

        for name, content in structure.items():
            path = base_path / name
            if isinstance(content, dict):
                path.mkdir(parents=True, exist_ok=True)
                self.create_directory_structure(content, path)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)

    def render_template(self, template_path: str, **extra_context: Any) -> str:
        """
        Render a Jinja2 template.

        Args:
            template_path: Relative path to template file
            **extra_context: Additional context variables

        Returns:
            Rendered template string
        """
        env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        template = env.get_template(template_path)
        context = {**self.get_context(), **extra_context}
        return template.render(context)

    def write_file(self, file_path: Path, content: str) -> None:
        """
        Write content to a file.

        Args:
            file_path: Path to the file
            content: Content to write
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def copy_file(self, src: Path, dest: Path) -> None:
        """
        Copy a file from source to destination.

        Args:
            src: Source file path
            dest: Destination file path
        """
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    def _copy_static_file(self, template_relative_path: str, dest: Path) -> None:
        """
        Copy a static file from the template directory to destination.

        Args:
            template_relative_path: Relative path from template directory
            dest: Destination file path
        """
        src = self.template_dir / template_relative_path
        if not src.exists():
            raise FileNotFoundError(f"Static file not found: {src}")
        self.copy_file(src, dest)

    def generate(self) -> None:
        """Generate the app. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement generate()")
