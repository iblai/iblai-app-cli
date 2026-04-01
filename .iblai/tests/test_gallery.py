"""Tests for iblai.gallery — component gallery generation."""

import os
import tempfile

from iblai.gallery import (
    ExportEntry,
    categorize_exports,
    generate_gallery_markdown,
    is_react_component,
    parse_exports,
    replace_gallery_section,
    resolve_skill_path,
    CategoryDef,
    IMPORT_PREFIX,
    GITHUB_RAW_BASE,
    SCREENSHOT_PAGES,
    SKILL_RELATIVE_PATH,
    _DEMO_PAGES,
)


# ---------------------------------------------------------------------------
# parse_exports
# ---------------------------------------------------------------------------


class TestParseExports:
    def test_export_block(self):
        dts = "export { Profile, UserProfileDropdown, Account };"
        exports = parse_exports(dts, ".")
        names = {e.name for e in exports}
        assert names == {"Profile", "UserProfileDropdown", "Account"}
        assert len(exports) == 3

    def test_export_block_multiline(self):
        dts = """export {
  Profile,
  Account,
  Spinner
};"""
        exports = parse_exports(dts, ".")
        assert len(exports) == 3

    def test_export_declare_function(self):
        dts = "export declare function handleSsoCallback(data: any): void;"
        exports = parse_exports(dts, "./sso")
        assert len(exports) == 1
        assert exports[0].name == "handleSsoCallback"
        assert exports[0].kind == "function"
        assert exports[0].import_path == f"{IMPORT_PREFIX}/sso"

    def test_export_declare_const(self):
        dts = "export declare const DEFAULT_SSO_STORAGE_KEYS: SsoStorageKeys;"
        exports = parse_exports(dts, ".")
        assert exports[0].name == "DEFAULT_SSO_STORAGE_KEYS"
        assert exports[0].kind == "const"

    def test_export_declare_class(self):
        dts = "export declare class ProfileManager { }"
        exports = parse_exports(dts, ".")
        assert exports[0].kind == "component"

    def test_export_type(self):
        dts = "export type ProfileProps = { org: string; };"
        exports = parse_exports(dts, ".")
        assert exports[0].name == "ProfileProps"
        assert exports[0].kind == "type"

    def test_export_interface(self):
        dts = "export interface NotificationConfig { }"
        exports = parse_exports(dts, ".")
        assert exports[0].name == "NotificationConfig"
        assert exports[0].kind == "interface"

    def test_export_as_alias(self):
        dts = "export { InternalName as PublicName };"
        exports = parse_exports(dts, ".")
        assert exports[0].name == "PublicName"

    def test_deduplication(self):
        dts = """export { Profile };
export declare function Profile(): JSX.Element;"""
        exports = parse_exports(dts, ".")
        assert len(exports) == 1

    def test_root_import_path(self):
        dts = "export { Profile };"
        exports = parse_exports(dts, ".")
        assert exports[0].import_path == IMPORT_PREFIX

    def test_next_import_path(self):
        dts = "export { SsoLogin };"
        exports = parse_exports(dts, "./next")
        assert exports[0].import_path == f"{IMPORT_PREFIX}/next"

    def test_sso_import_path(self):
        dts = "export { parseSsoData };"
        exports = parse_exports(dts, "./sso")
        assert exports[0].import_path == f"{IMPORT_PREFIX}/sso"

    def test_empty_content(self):
        assert parse_exports("", ".") == []

    def test_hook_classified_as_function(self):
        dts = "export { useLocalStorage };"
        exports = parse_exports(dts, ".")
        assert exports[0].kind == "function"

    def test_mixed_exports(self):
        dts = """export { Profile, NotificationDropdown };
export declare function useOverview(): any;
export type GroupOption = { label: string; value: string; };
export interface AnalyticsConfig { }"""
        exports = parse_exports(dts, ".")
        names = {e.name for e in exports}
        assert names == {
            "Profile",
            "NotificationDropdown",
            "useOverview",
            "GroupOption",
            "AnalyticsConfig",
        }


# ---------------------------------------------------------------------------
# is_react_component
# ---------------------------------------------------------------------------


class TestIsReactComponent:
    def test_pascal_case_component(self):
        e = ExportEntry("Profile", ".", IMPORT_PREFIX, "component")
        assert is_react_component(e) is True

    def test_declared_class(self):
        e = ExportEntry("ProfileManager", ".", IMPORT_PREFIX, "component")
        assert is_react_component(e) is True

    def test_hook_is_not_component(self):
        e = ExportEntry("useOverview", ".", IMPORT_PREFIX, "function")
        assert is_react_component(e) is False

    def test_declared_function_not_component(self):
        e = ExportEntry("handleSsoCallback", ".", IMPORT_PREFIX, "function")
        assert is_react_component(e) is False

    def test_const_not_component(self):
        e = ExportEntry("DEFAULT_SSO_STORAGE_KEYS", ".", IMPORT_PREFIX, "const")
        assert is_react_component(e) is False

    def test_type_not_component(self):
        e = ExportEntry("ProfileProps", ".", IMPORT_PREFIX, "type")
        assert is_react_component(e) is False

    def test_interface_not_component(self):
        e = ExportEntry("NotificationConfig", ".", IMPORT_PREFIX, "interface")
        assert is_react_component(e) is False

    def test_enum_not_component(self):
        e = ExportEntry("Theme", ".", IMPORT_PREFIX, "enum")
        assert is_react_component(e) is False

    def test_lowercase_unknown_not_component(self):
        e = ExportEntry("sanitizeCss", ".", IMPORT_PREFIX, "unknown")
        assert is_react_component(e) is False

    def test_pascal_case_unknown_is_component(self):
        e = ExportEntry("NewWidget", ".", IMPORT_PREFIX, "unknown")
        assert is_react_component(e) is True


# ---------------------------------------------------------------------------
# categorize_exports
# ---------------------------------------------------------------------------


class TestCategorizeExports:
    def test_known_components_categorized(self):
        entries = [
            ExportEntry("Profile", ".", IMPORT_PREFIX, "component"),
            ExportEntry("AnalyticsOverview", ".", IMPORT_PREFIX, "component"),
        ]
        cats = categorize_exports(entries)
        assert "profile" in cats
        assert "analytics" in cats
        assert any(e.name == "Profile" for e in cats["profile"].entries)
        assert any(
            e.name == "AnalyticsOverview" for e in cats["analytics"].entries
        )

    def test_hooks_auto_categorized(self):
        entries = [
            ExportEntry("useCustomHook", ".", IMPORT_PREFIX, "function"),
        ]
        cats = categorize_exports(entries)
        assert "hooks" in cats

    def test_types_auto_categorized(self):
        entries = [
            ExportEntry("ProfileProps", ".", IMPORT_PREFIX, "interface"),
        ]
        cats = categorize_exports(entries)
        assert "types" in cats

    def test_unknown_goes_to_other(self):
        entries = [
            ExportEntry("SomethingNew", ".", IMPORT_PREFIX, "component"),
        ]
        cats = categorize_exports(entries)
        assert "other" in cats

    def test_empty_categories_excluded(self):
        entries = [
            ExportEntry("Profile", ".", IMPORT_PREFIX, "component"),
        ]
        cats = categorize_exports(entries)
        assert "notifications" not in cats
        assert "analytics" not in cats

    def test_ui_primitives_excluded(self):
        entries = [
            ExportEntry("Button", ".", IMPORT_PREFIX, "component"),
            ExportEntry("Profile", ".", IMPORT_PREFIX, "component"),
        ]
        cats = categorize_exports(entries)
        # Button should not appear in any category
        all_names = set()
        for cat in cats.values():
            for e in cat.entries:
                all_names.add(e.name)
        assert "Button" not in all_names
        assert "Profile" in all_names

    def test_components_only_excludes_hooks(self):
        entries = [
            ExportEntry("Profile", ".", IMPORT_PREFIX, "component"),
            ExportEntry("useOverview", ".", IMPORT_PREFIX, "function"),
        ]
        cats = categorize_exports(entries, components_only=True)
        all_names = set()
        for cat in cats.values():
            for e in cat.entries:
                all_names.add(e.name)
        assert "Profile" in all_names
        assert "useOverview" not in all_names

    def test_components_only_excludes_consts(self):
        entries = [
            ExportEntry("Profile", ".", IMPORT_PREFIX, "component"),
            ExportEntry("DEFAULT_SSO_STORAGE_KEYS", ".", IMPORT_PREFIX, "const"),
        ]
        cats = categorize_exports(entries, components_only=True)
        all_names = set()
        for cat in cats.values():
            for e in cat.entries:
                all_names.add(e.name)
        assert "DEFAULT_SSO_STORAGE_KEYS" not in all_names

    def test_components_only_excludes_types(self):
        entries = [
            ExportEntry("Profile", ".", IMPORT_PREFIX, "component"),
            ExportEntry("ProfileProps", ".", IMPORT_PREFIX, "type"),
            ExportEntry("NotificationConfig", ".", IMPORT_PREFIX, "interface"),
        ]
        cats = categorize_exports(entries, components_only=True)
        assert "types" not in cats

    def test_components_only_keeps_pascal_case_components(self):
        entries = [
            ExportEntry("Profile", ".", IMPORT_PREFIX, "component"),
            ExportEntry("Account", ".", IMPORT_PREFIX, "component"),
            ExportEntry("handleSsoCallback", ".", IMPORT_PREFIX, "function"),
            ExportEntry("sanitizeCss", ".", IMPORT_PREFIX, "unknown"),
        ]
        cats = categorize_exports(entries, components_only=True)
        all_names = set()
        for cat in cats.values():
            for e in cat.entries:
                all_names.add(e.name)
        assert all_names == {"Profile", "Account"}


# ---------------------------------------------------------------------------
# generate_gallery_markdown
# ---------------------------------------------------------------------------


class TestGenerateGalleryMarkdown:
    def test_contains_version(self):
        cats = {
            "profile": CategoryDef(
                title="Profile & Account",
                entries=[
                    ExportEntry("Profile", ".", IMPORT_PREFIX, "component")
                ],
            )
        }
        md = generate_gallery_markdown(cats, "1.2.0")
        assert "1.2.0" in md
        assert "## Component Gallery" in md

    def test_table_format(self):
        cats = {
            "profile": CategoryDef(
                title="Profile & Account",
                entries=[
                    ExportEntry("Profile", ".", IMPORT_PREFIX, "component")
                ],
            )
        }
        md = generate_gallery_markdown(cats, "1.0.0")
        assert "| `Profile` |" in md
        assert "| Export | Import | Description |" in md

    def test_import_example(self):
        cats = {
            "profile": CategoryDef(
                title="Profile & Account",
                entries=[
                    ExportEntry("Profile", ".", IMPORT_PREFIX, "component")
                ],
            )
        }
        md = generate_gallery_markdown(cats, "1.0.0")
        assert f'import {{ Profile }} from "{IMPORT_PREFIX}";' in md

    def test_ui_primitives_section(self):
        cats = {}
        md = generate_gallery_markdown(cats, "1.0.0", ["Button", "Input"])
        assert "### UI Primitives" in md
        assert "`Button`" in md
        assert "`Input`" in md

    def test_auto_discovered_description(self):
        cats = {
            "other": CategoryDef(
                title="Other",
                entries=[
                    ExportEntry("NewThing", ".", IMPORT_PREFIX, "component")
                ],
            )
        }
        md = generate_gallery_markdown(cats, "1.0.0")
        assert "auto-discovered" in md

    def test_regeneration_note(self):
        cats = {}
        md = generate_gallery_markdown(cats, "1.0.0")
        assert "iblai update-gallery" in md


# ---------------------------------------------------------------------------
# replace_gallery_section
# ---------------------------------------------------------------------------


class TestReplaceGallerySection:
    def test_replace_between_markers(self):
        content = (
            "# Title\n\n"
            "## Component Gallery\n\nold content\n\n"
            "## Component Priority\n\nrest"
        )
        gallery = "## Component Gallery\n\nnew content"
        result = replace_gallery_section(content, gallery)
        assert "new content" in result
        assert "old content" not in result
        assert "## Component Priority" in result
        assert "rest" in result

    def test_no_markers_appends(self):
        content = "# Title\n\nSome content"
        gallery = "## Component Gallery\n\nnew content"
        result = replace_gallery_section(content, gallery)
        assert "## Component Gallery" in result
        assert "new content" in result
        assert "# Title" in result

    def test_start_only_replaces_to_end(self):
        content = "# Title\n\n## Component Gallery\n\nold"
        gallery = "## Component Gallery\n\nnew"
        result = replace_gallery_section(content, gallery)
        assert "new" in result
        assert "old" not in result

    def test_preserves_content_before_gallery(self):
        content = (
            "---\nname: test\n---\n\n# Title\n\nbefore\n\n"
            "## Component Gallery\n\nold\n\n"
            "## Component Priority\n\nafter"
        )
        gallery = "## Component Gallery\n\nupdated"
        result = replace_gallery_section(content, gallery)
        assert "---\nname: test\n---" in result
        assert "before" in result
        assert "updated" in result
        assert "after" in result
        assert "old" not in result


# ---------------------------------------------------------------------------
# resolve_skill_path
# ---------------------------------------------------------------------------


class TestResolveSkillPath:
    def test_directory_with_skill_md(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = os.path.join(tmpdir, "iblai-components")
            os.makedirs(skill_dir)
            skill_file = os.path.join(skill_dir, "SKILL.md")
            with open(skill_file, "w") as f:
                f.write("# Test")
            result = resolve_skill_path(tmpdir)
            assert str(result) == skill_file

    def test_direct_file_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_file = os.path.join(tmpdir, "SKILL.md")
            with open(skill_file, "w") as f:
                f.write("# Test")
            result = resolve_skill_path(skill_file)
            assert str(result) == skill_file

    def test_missing_skill_md_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                resolve_skill_path(tmpdir)
                assert False, "Expected FileNotFoundError"
            except FileNotFoundError as e:
                assert "iblai-components/SKILL.md" in str(e)


# ---------------------------------------------------------------------------
# screenshots integration with generate_gallery_markdown
# ---------------------------------------------------------------------------


class TestScreenshotIntegration:
    def test_no_screenshots_no_images(self):
        cats = {
            "profile": CategoryDef(
                title="Profile & Account",
                entries=[
                    ExportEntry("Profile", ".", IMPORT_PREFIX, "component")
                ],
            )
        }
        md = generate_gallery_markdown(cats, "1.0.0")
        assert "![" not in md

    def test_screenshots_inserts_image(self):
        cats = {
            "profile": CategoryDef(
                title="Profile & Account",
                entries=[
                    ExportEntry("Profile", ".", IMPORT_PREFIX, "component")
                ],
            )
        }
        screenshots = {"profile": "gallery-profile.png"}
        md = generate_gallery_markdown(cats, "1.0.0", screenshots=screenshots)
        expected_url = f"{GITHUB_RAW_BASE}/gallery-profile.png"
        assert f"![Profile & Account]({expected_url})" in md

    def test_screenshot_before_table(self):
        cats = {
            "analytics": CategoryDef(
                title="Analytics",
                entries=[
                    ExportEntry(
                        "AnalyticsOverview", ".", IMPORT_PREFIX, "component"
                    )
                ],
            )
        }
        screenshots = {"analytics": "gallery-analytics.png"}
        md = generate_gallery_markdown(cats, "1.0.0", screenshots=screenshots)
        img_idx = md.index("![Analytics]")
        table_idx = md.index("| Export |")
        assert img_idx < table_idx

    def test_unmatched_screenshot_ignored(self):
        cats = {
            "profile": CategoryDef(
                title="Profile & Account",
                entries=[
                    ExportEntry("Profile", ".", IMPORT_PREFIX, "component")
                ],
            )
        }
        screenshots = {"nonexistent": "gallery-none.png"}
        md = generate_gallery_markdown(cats, "1.0.0", screenshots=screenshots)
        assert "gallery-none.png" not in md

    def test_multiple_screenshots(self):
        cats = {
            "auth": CategoryDef(
                title="Authentication & SSO",
                entries=[
                    ExportEntry("SsoLogin", "./next", f"{IMPORT_PREFIX}/next", "component")
                ],
            ),
            "profile": CategoryDef(
                title="Profile & Account",
                entries=[
                    ExportEntry("Profile", ".", IMPORT_PREFIX, "component")
                ],
            ),
        }
        screenshots = {
            "auth": "gallery-auth.png",
            "profile": "gallery-profile.png",
        }
        md = generate_gallery_markdown(cats, "1.0.0", screenshots=screenshots)
        assert "gallery-auth.png" in md
        assert "gallery-profile.png" in md

    def test_screenshot_url_format(self):
        """All screenshot filenames should produce valid GitHub raw URLs."""
        for _cat_key, _route, filename in SCREENSHOT_PAGES:
            url = f"{GITHUB_RAW_BASE}/{filename}"
            assert url.startswith("https://raw.githubusercontent.com/")
            assert filename.endswith(".png")

    def test_demo_pages_are_valid_jsx(self):
        """Demo page content should be non-empty and contain JSX."""
        for rel_path, (_route, content) in _DEMO_PAGES.items():
            assert rel_path.endswith(".tsx"), f"{rel_path} must be .tsx"
            assert "export default function" in content
            assert len(content) > 50
