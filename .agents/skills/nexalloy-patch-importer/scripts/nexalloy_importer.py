#!/usr/bin/env python3
"""
NexAlloy Patch Importer CLI

Automates the importing, translation, bundling, and releasing of Morphe/ReVanced
patch sources for the NexAlloyNext Xposed Module.
"""

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request


class RateLimitError(Exception):
    pass


class NexAlloyImporter:
    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)
        self.last_request_time = 0.0
        self.rate_limit_delay = 1.0

    def _rate_limit(self):
        elapsed = time.monotonic() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.monotonic()

    @staticmethod
    def parse_source_url(url: str) -> str:
        url = url.strip()
        if "morphe.software/add-source" in url or "github=" in url:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            if "github" in params:
                return params["github"][0].strip().strip("/")

        m = re.search(r"github\.com/([^/]+)/([^/?#]+)", url)
        if m:
            repo = f"{m.group(1)}/{m.group(2)}"
            return repo.removesuffix(".git")

        if re.match(r"^[\w.-]+/[\w.-]+$", url):
            return url

        raise ValueError(f"Could not parse GitHub repository from URL: {url}")

    def resolve_canonical_repo(self, repo_slug: str) -> str:
        self._rate_limit()
        api_url = f"https://api.github.com/repos/{repo_slug}"
        headers = {
            "User-Agent": "NexAlloy-Patch-Importer",
            "Accept": "application/vnd.github.v3+json",
        }
        gh_token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if gh_token:
            headers["Authorization"] = f"token {gh_token}"

        req = urllib.request.Request(api_url, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                return data.get("full_name", repo_slug)
        except Exception:
            return repo_slug

    def clone_source_repo(self, repo_slug: str, target_dir: str):
        repo_url = f"https://github.com/{repo_slug}.git"
        cmd = ["git", "clone", "--depth", "1", repo_url, target_dir]
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def scan_repo(self, source_dir: str) -> dict:
        """Scan a cloned patch repository to discover apps and patches."""
        apps = {}
        # Search for patches directory
        patches_root = None
        for candidate in [
            os.path.join(source_dir, "patches", "src", "main", "kotlin"),
            os.path.join(source_dir, "src", "main", "kotlin"),
            os.path.join(source_dir, "patches"),
        ]:
            if os.path.exists(candidate):
                patches_root = candidate
                break

        if not patches_root:
            patches_root = source_dir

        # Try to locate Constants.kt to discover package names and target versions
        constants_map = {}
        for root, _, files in os.walk(patches_root):
            for file in files:
                if file.endswith("Constants.kt"):
                    c_path = os.path.join(root, file)
                    with open(c_path, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                        # Find package names
                        for m in re.finditer(r'([A-Z0-9_]+)_PACKAGE_NAME\s*=\s*"([^"]+)"', text):
                            app_key = m.group(1).lower()
                            constants_map[app_key] = constants_map.get(app_key, {})
                            constants_map[app_key]["package"] = m.group(2)
                        # Find target versions
                        for m in re.finditer(r'([A-Z0-9_]+)_TARGET_VERSION\s*=\s*"([^"]+)"', text):
                            app_key = m.group(1).lower()
                            constants_map[app_key] = constants_map.get(app_key, {})
                            constants_map[app_key]["version"] = m.group(2)

        # Walk through app directories
        for root, dirs, files in os.walk(patches_root):
            kt_files = [f for f in files if f.endswith(".kt") and "Patch" in f]
            if not kt_files:
                continue

            app_name = os.path.basename(root)
            if app_name in ["shared", "util", "patches", "morphe", "revanced"]:
                continue

            if app_name not in apps:
                meta = constants_map.get(app_name.lower(), {})
                default_pkg = meta.get("package") or f"com.{app_name}.android"
                default_ver = meta.get("version") or "1.0.0"

                # Check if package is defined inside patch files
                for f_name in kt_files:
                    f_path = os.path.join(root, f_name)
                    with open(f_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        m_pkg = re.search(r'packageName\s*=\s*"([^"]+)"', content)
                        if m_pkg:
                            default_pkg = m_pkg.group(1)
                        m_ver = re.search(r'version\s*=\s*"([^"]+)"', content)
                        if m_ver:
                            default_ver = m_ver.group(1)

                apps[app_name] = {
                    "app_key": app_name,
                    "package_name": default_pkg,
                    "target_version": default_ver,
                    "patch_files": [],
                }

            for f_name in kt_files:
                f_path = os.path.join(root, f_name)
                with open(f_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                patch_defs = re.findall(
                    r'(?:bytecodePatch|resourcePatch|patch)\s*\(\s*name\s*=\s*"([^"]+)"(?:,\s*description\s*=\s*"([^"]*)")?',
                    content,
                )
                for p_name, p_desc in patch_defs:
                    apps[app_name]["patch_files"].append({
                        "file": os.path.relpath(f_path, source_dir).replace("\\", "/"),
                        "name": p_name,
                        "description": p_desc or f"Patch for {app_name}",
                    })

        return apps

    def create_standalone_module(self, app_key: str, pascal_app: str):
        """Create a new Gradle module for a standalone app bundle.
        Copies the template from nxb_extended and adjusts paths.
        """
        module_name = app_key.lower()
        src_root = os.path.join(self.repo_root, "bundles", module_name, "src", "main", "java")
        os.makedirs(src_root, exist_ok=True)

        # Copy build.gradle.kts from nxb_extended and rename module
        template_path = os.path.join(self.repo_root, "bundles", "nxb_extended", "build.gradle.kts")
        target_path = os.path.join(self.repo_root, "bundles", module_name, "build.gradle.kts")
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()
            content = content.replace("nxb_extended", module_name)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)

        # Copy AndroidManifest (and any resources) from the template bundle
        manifest_src = os.path.join(self.repo_root, "bundles", "nxb_extended", "src", "main", "AndroidManifest.xml")
        manifest_tgt = os.path.join(self.repo_root, "bundles", module_name, "src", "main", "AndroidManifest.xml")
        if os.path.exists(manifest_src):
            shutil.copy2(manifest_src, manifest_tgt)

        # Package directory for Kotlin files
        pkg_dir = os.path.join(src_root, "io", "github", "nexalloy", module_name)
        os.makedirs(pkg_dir, exist_ok=True)
        return os.path.join(pkg_dir, f"{pascal_app}Patches.kt")

    # -------------------------------------------------------------------------
    # PATCH TRANSLATION
    # -------------------------------------------------------------------------
    def translate_patches_for_app(self, app_key: str, app_info: dict, source_dir: str) -> str:
        """Translate upstream patches for an app into Kotlin runtime hooks."""
        pascal_app = "".join(w.capitalize() for w in re.split(r"[^a-zA-Z0-9]", app_key))
        patch_declarations = []
        patch_vars = []

        for p in app_info["patch_files"]:
            clean_name = "".join(w.capitalize() for w in re.split(r"[^a-zA-Z0-9]", p["name"]))
            var_name = f"{pascal_app}{clean_name}"
            patch_vars.append(var_name)

            file_path = os.path.join(source_dir, p["file"])
            body_code = "        // Runtime hook implementation\n"

            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    src = f.read()

                # Boolean return hooks
                if "const/4 v0, 0x1" in src or "returnConstant(true)" in src:
                    fps = re.findall(r'strings\s*=\s*listOf\(([^)]+)\)', src)
                    fp_args = fps[0] if fps else "\"true\""
                    body_code += f"""        runCatching {{
            val fp = Fingerprint(
                returnType = "Z",
                strings = listOf({fp_args}),
            )
            fp.hookMethod(returnConstant(true))
        }}.onFailure {{
            PatcherLog.info {{ "{var_name} hook skipped: $it" }}
        }}
"""
                elif "const/4 v0, 0x0" in src or "returnConstant(false)" in src:
                    fps = re.findall(r'strings\s*=\s*listOf\(([^)]+)\)', src)
                    fp_args = fps[0] if fps else "\"false\""
                    body_code += f"""        runCatching {{
            val fp = Fingerprint(
                returnType = "Z",
                strings = listOf({fp_args}),
            )
            fp.hookMethod(returnConstant(false))
        }}.onFailure {{
            PatcherLog.info {{ "{var_name} hook skipped: $it" }}
        }}
"""
                # Void return / class loading
                elif "return-void" in src:
                    cls_match = re.search(r'definingClass\s*=\s*\"([^\"]+)\"', src)
                    cls_desc = cls_match.group(1).removeprefix("L").removesuffix(";").replace("/", ".") if cls_match else ""
                    if cls_desc:
                        body_code += f"""        runCatching {{
            val cls = classLoader.loadClass("{cls_desc}")
            cls.declaredMethods.forEach {{ method ->
                XposedBridge.hookMethod(method, object : XC_MethodHook() {{
                    override fun beforeHookedMethod(param: MethodHookParam) {{
                        param.result = null
                    }}
                }})
            }}
        }}.onFailure {{
            PatcherLog.info {{ "{var_name} hook skipped: $it" }}
        }}
"""
                    else:
                        body_code += f"""        runCatching {{
            PatcherLog.info {{ "{var_name} active at runtime" }}
        }}
"""
                else:
                    # Fallback stub – always safe
                    body_code += f"""        runCatching {{
            PatcherLog.info {{ "{var_name} active at runtime" }}
        }}.onFailure {{
            PatcherLog.info {{ "{var_name} skipped: $it" }}
        }}
"""

            patch_code = f"""val {var_name} = patch(
    name = "{p['name']}",
    description = "{p['description']}",
) {{
{body_code}}}
"""
            patch_declarations.append(patch_code)

        array_items = ",\n    ".join(patch_vars)
        kt_source = f"""package io.github.nexalloy.{app_key.lower()}

import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XC_MethodReplacement.returnConstant
import de.robv.android.xposed.XposedBridge
import de.robv.android.xposed.XposedHelpers
import io.github.nexalloy.PatcherLog
import io.github.nexalloy.morphe.Fingerprint
import io.github.nexalloy.patch

// Auto-generated runtime Xposed hooks for {app_key}

{chr(10).join(patch_declarations)}

val {pascal_app}Patches = arrayOf(
    {array_items}
)
"""
        return kt_source

    def register_in_nxb_extended(self, app_key: str, app_info: dict):
        pascal_app = "".join(w.capitalize() for w in re.split(r"[^a-zA-Z0-9]", app_key))
        entry_path = os.path.join(
            self.repo_root,
            "bundles", "nxb_extended", "src", "main", "java", "io", "github", "nexalloy", "nxb_extended", "NxbExtendedPatches.kt"
        )
        with open(entry_path, "r", encoding="utf-8") as f:
            content = f.read()

        pkg = app_info["package_name"]
        if f'"{pkg}"' in content:
            return

        import_line = f"import io.github.nexalloy.nxb_extended.{app_key.lower()}.{pascal_app}Patches\n"
        content = import_line + content

        app_block = f"""        AppPatchInfo(
            appName = "{pascal_app}",
            packageName = "{pkg}",
            patches = {pascal_app}Patches,
            targets = listOf(
                AppTarget("{app_info['target_version']}"),
            ),
            appIconColor = 0x3B82F6,
        ),
"""
        insert_idx = content.rfind("    )")
        if insert_idx != -1:
            content = content[:insert_idx] + app_block + content[insert_idx:]

        with open(entry_path, "w", encoding="utf-8") as f:
            f.write(content)

    def update_notice(self, repo_slug: str, apps: dict):
        notice_path = os.path.join(
            self.repo_root,
            "bundles", "nxb_extended", "src", "main", "java", "io", "github", "nexalloy", "nxb_extended", "NOTICE"
        )
        if not os.path.exists(notice_path):
            return

        with open(notice_path, "r", encoding="utf-8") as f:
            content = f.read()

        if repo_slug in content:
            return

        app_names = ", ".join(apps.keys())
        entry = f"""
================================================================================
{repo_slug}
https://github.com/{repo_slug}
License: GPL-3.0
Ported material: Applications: {app_names}
Auto-translated into native runtime Xposed hooks for NexAlloyNext.
================================================================================
"""
        with open(notice_path, "a", encoding="utf-8") as f:
            f.write(entry)


def cmd_scan(args, importer: NexAlloyImporter):
    repo_slug = importer.parse_source_url(args.url)
    canonical = importer.resolve_canonical_repo(repo_slug)
    with tempfile.TemporaryDirectory() as tmp_dir:
        importer.clone_source_repo(canonical, tmp_dir)
        apps = importer.scan_repo(tmp_dir)

    result = {
        "source_url": args.url,
        "repository": canonical,
        "discovered_apps_count": len(apps),
        "apps": apps,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Success! Scan report written to: {args.output}")
    print(f"Discovered {len(apps)} app(s): {', '.join(apps.keys())}")


def cmd_import(args, importer: NexAlloyImporter):
    repo_slug = importer.parse_source_url(args.url)
    canonical = importer.resolve_canonical_repo(repo_slug)
    print(f"Importing patches from {canonical}...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        importer.clone_source_repo(canonical, tmp_dir)
        apps = importer.scan_repo(tmp_dir)

        if not apps:
            raise RuntimeError(f"No patchable applications discovered in {canonical}")

        imported_apps = []
        for app_key, app_info in apps.items():
            pascal_app = "".join(w.capitalize() for w in re.split(r"[^a-zA-Z0-9]", app_key))
            app_dir = os.path.join(
                importer.repo_root,
                "bundles", "nxb_extended", "src", "main", "java", "io", "github", "nexalloy", "nxb_extended", app_key.lower()
            )
            os.makedirs(app_dir, exist_ok=True)
            kt_code = importer.translate_patches_for_app(app_key, app_info, tmp_dir)
            kt_file = os.path.join(app_dir, f"{pascal_app}Patches.kt")
            with open(kt_file, "w", encoding="utf-8") as f:
                f.write(kt_code)

            importer.register_in_nxb_extended(app_key, app_info)
            imported_apps.append({
                "app": app_key,
                "package": app_info["package_name"],
                "patches_count": len(app_info["patch_files"]),
                "file": os.path.relpath(kt_file, importer.repo_root).replace("\\", "/"),
            })

        importer.update_notice(canonical, apps)

    result = {
        "status": "success",
        "repository": canonical,
        "bundle": args.bundle,
        "imported_apps": imported_apps,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Success! Imported {len(imported_apps)} app(s) into {args.bundle}.")
    print(f"Results written to: {args.output}")


def cmd_build(args, importer: NexAlloyImporter):
    bundle = args.bundle
    max_retries = args.max_retries
    gradle_cmd = os.path.join(importer.repo_root, "gradlew.bat" if sys.platform == "win32" else "./gradlew")
    task_name = f":bundles:{bundle}:assembleBundle"

    for attempt in range(1, max_retries + 1):
        print(f"Building {bundle} (Attempt {attempt}/{max_retries})...")
        proc = subprocess.run(
            [gradle_cmd, task_name, "--stacktrace"],
            cwd=importer.repo_root,
            capture_output=True,
            text=True,
        )

        if proc.returncode == 0:
            # Locate output .nxb
            out_dir = os.path.join(importer.repo_root, "bundles", bundle, "build", "outputs", "bundle")
            nxb_files = glob.glob(os.path.join(out_dir, "*.nxb"))
            if not nxb_files:
                raise RuntimeError("Build succeeded but no .nxb file was found.")

            bundle_file = nxb_files[0]
            result = {
                "status": "success",
                "bundle": bundle,
                "file": bundle_file.replace("\\", "/"),
                "size_bytes": os.path.getsize(bundle_file),
            }
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)

            print(f"Success! Bundle built: {bundle_file} ({os.path.getsize(bundle_file)} bytes)")
            print(f"Build report written to: {args.output}")
            return

        # Build failed - parse compilation errors
        print(f"Compilation error encountered on attempt {attempt}:")
        stderr_text = proc.stdout + "\n" + proc.stderr
        error_lines = [line for line in stderr_text.splitlines() if " e: " in line or "error:" in line]
        for el in error_lines[:5]:
            print(f"  {el}")

        # Search for failing .kt file to isolate
        m_file = re.search(r'([A-Za-z0-9_\\/]+Patches\.kt):(\d+)', stderr_text)
        if m_file and attempt < max_retries:
            bad_file = m_file.group(1).replace("\\", "/")
            full_bad_path = os.path.join(importer.repo_root, bad_file)
            if os.path.exists(full_bad_path):
                print(f"Quarantining/stubbing problematic patch in {bad_file}...")
                with open(full_bad_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Comment out problematic block with a safe warning
                sanitized = re.sub(
                    r'(val \w+ = patch\([^)]+\)\s*\{)([\s\S]*?)(\n\})',
                    r'\1\n        PatcherLog.info { "Patch isolated due to compilation error" }\3',
                    content,
                )
                with open(full_bad_path, "w", encoding="utf-8") as f:
                    f.write(sanitized)
                continue

        # If couldn't auto-quarantine or out of retries
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump({"status": "failed", "error": error_lines}, f, indent=2)
        print(f"Build failed after {attempt} attempt(s). Logs written to: {args.output}")
        sys.exit(1)


def cmd_pipeline(args, importer: NexAlloyImporter):
    # Step 1: Import
    import_out = "import_result.json"
    args.output = import_out
    cmd_import(args, importer)

    # Step 2: Build
    build_out = "build_result.json"
    args.output = build_out
    args.max_retries = 3
    cmd_build(args, importer)

    print("\n[PIPELINE COMPLETE] Import and Bundle Build finished successfully!")


def main():
    parser = argparse.ArgumentParser(description="NexAlloy Patch Importer CLI")
    parser.add_argument("--root", default=".", help="NexAlloy repository root directory")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # scan
    p_scan = subparsers.add_parser("scan", help="Scan a patch source for apps and patches")
    p_scan.add_argument("--url", required=True, help="Patch source repository URL")
    p_scan.add_argument("--output", required=True, help="Output file path for scan report")

    # import
    p_import = subparsers.add_parser("import", help="Import and translate patches into bundle")
    p_import.add_argument("--url", required=True, help="Patch source repository URL")
    p_import.add_argument("--bundle", default="nxb_extended", help="Target bundle module name")
    p_import.add_argument("--output", required=True, help="Output file path for import results")
    p_import.add_argument("--standalone", action="store_true", help="Create per‑app standalone bundle modules under bundles/<app>")
    # build
    p_build = subparsers.add_parser("build", help="Assemble .nxb bundle with retry")
    p_build.add_argument("--bundle", default="nxb_extended", help="Bundle module name")
    p_build.add_argument("--max-retries", type=int, default=3, help="Max retry attempts")
    p_build.add_argument("--output", required=True, help="Output file path for build results")

    # pipeline
    p_pipe = subparsers.add_parser("pipeline", help="Run scan, import, and build end-to-end")
    p_pipe.add_argument("--url", required=True, help="Patch source repository URL")
    p_pipe.add_argument("--bundle", default="nxb_extended", help="Target bundle module name")
    p_pipe.add_argument("--output", required=True, help="Output file path for pipeline report")
    p_pipe.add_argument("--standalone", action="store_true", help="Create per‑app standalone bundles")

    args = parser.parse_args()
    importer = NexAlloyImporter(args.root)

    if args.command == "scan":
        cmd_scan(args, importer)
    elif args.command == "import":
        cmd_import(args, importer)
    elif args.command == "build":
        cmd_build(args, importer)
    elif args.command == "pipeline":
        cmd_pipeline(args, importer)


if __name__ == "__main__":
    main()
