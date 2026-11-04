# ==============================================================================
# RULE 4 ENGINE: sandbox/verifier.py
# "First test in sandbox, then register into active pipeline."
# Verifies that every plugin adheres strictly to the Sacred Core contracts.
# ==============================================================================

import asyncio
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

# Ensure workspace root is in sys.path
workspace_root = str(Path(__file__).resolve().parent.parent)
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

import yaml

from core.base_feature import BaseFeature
from core.context import ExecutionContext


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CYPHER_LABEL_GUARD.SandboxVerifier")


class SandboxVerifier:
    """
    Automated sandbox test harness for validating feature plugins before registration.
    """

    REQUIRED_MANIFEST_FIELDS = ["id", "name", "category", "version", "entrypoint"]

    @classmethod
    async def verify_plugin(cls, feature_dir: Path) -> Tuple[bool, str, Dict[str, Any]]:
        manifest_file = feature_dir / "manifest.yaml"
        if not manifest_file.exists():
            return False, f"Missing manifest.yaml in {feature_dir}", {}

        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = yaml.safe_load(f)
        except Exception as e:
            return False, f"Failed to parse manifest.yaml: {e}", {}

        for field in cls.REQUIRED_MANIFEST_FIELDS:
            if field not in manifest:
                return False, f"Manifest missing required field '{field}'", manifest

        entrypoint_file = feature_dir / manifest["entrypoint"]
        if not entrypoint_file.exists():
            return False, f"Specified entrypoint {entrypoint_file} not found", manifest

        # Dynamically import in sandbox
        try:
            mod_name = f"sandbox_test_{manifest['id']}"
            spec = importlib.util.spec_from_file_location(mod_name, entrypoint_file)
            if not spec or not spec.loader:
                return False, "Failed to create module spec for sandbox execution", manifest

            module = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)

            found_class = None
            for attr in dir(module):
                obj = getattr(module, attr)
                if isinstance(obj, type) and issubclass(obj, BaseFeature) and obj is not BaseFeature:
                    found_class = obj
                    break

            if not found_class:
                return False, "Module does not contain a class inheriting from core.base_feature.BaseFeature", manifest

            # Instantiate and test execution
            instance = found_class(manifest)
            test_context = ExecutionContext(
                input_payload={"test_text": "Sandbox probe payload", "type": "TEST"}
            )

            evolved = await instance.execute(test_context)
            if not isinstance(evolved, ExecutionContext):
                return False, "Feature execute() did not return an ExecutionContext instance", manifest

            return True, f"Feature {manifest['id']} PASSED all sandbox validation checks.", manifest

        except Exception as e:
            return False, f"Execution failed in sandbox with error: {e}", manifest


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
        success, message, _ = asyncio.run(SandboxVerifier.verify_plugin(target))
        print(f"Sandbox Result: {'PASSED' if success else 'FAILED'} -> {message}")
        sys.exit(0 if success else 1)
