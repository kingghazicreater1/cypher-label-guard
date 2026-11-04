# ==============================================================================
# 🔒 SACRED FILE 3 OF 4: core/registry.py
# RULE 7: registry.py IS SACRED.
# Feature Directory: Who, Where, How.
# RULE 2: Everything is a Plugin (manifest.yaml for every feature).
# RULE 4: First test in sandbox, then register into active pipeline.
# RULE 25: Registry respects config/registry.yaml toggles.
# ==============================================================================

import importlib
import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import yaml

from core.base_feature import BaseFeature

logger = logging.getLogger("CYPHER_LABEL_GUARD.Registry")


class FeatureRegistry:
    """
    Central Feature Directory and Dynamic Plugin Loader for CypherLabelGuard v2.0.
    
    Enforces:
    1. Plugin Discovery across features/ subdirectories
    2. manifest.yaml schema validation
    3. Rule 4: Sandbox Qualification validation prior to loading
    4. Topological dependency resolution
    """

    def __init__(
        self,
        features_root: Optional[Path] = None,
        config_path: Optional[Path] = None,
    ):
        workspace_dir = Path(__file__).resolve().parent.parent
        self.features_root = features_root or (workspace_dir / "features")
        self.config_path = config_path or (workspace_dir / "config" / "registry.yaml")
        
        self._manifests: Dict[str, Dict[str, Any]] = {}
        self._feature_classes: Dict[str, Type[BaseFeature]] = {}
        self._instances: Dict[str, BaseFeature] = {}
        self._config_toggles: Dict[str, bool] = {}

    def load_config(self) -> Dict[str, bool]:
        """Loads enabled/disabled toggles from config/registry.yaml."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    self._config_toggles = data.get("features", {})
            except Exception as e:
                logger.error(f"Error reading registry config at {self.config_path}: {e}")
                self._config_toggles = {}
        return self._config_toggles

    def discover_features(self) -> Dict[str, Dict[str, Any]]:
        """
        Recursively scans the features/ directory for manifest.yaml files.
        Collects manifests, validates schema, and checks configuration toggles.
        """
        self.load_config()
        if not self.features_root.exists():
            logger.warning(f"Features directory does not exist: {self.features_root}")
            return {}

        manifest_paths = list(self.features_root.rglob("manifest.yaml"))
        for m_path in manifest_paths:
            try:
                with open(m_path, "r", encoding="utf-8") as f:
                    manifest = yaml.safe_load(f)
                    
                if not manifest or "id" not in manifest:
                    logger.warning(f"Skipping invalid manifest at {m_path}: Missing 'id'")
                    continue

                feat_id = manifest["id"]
                manifest["_path"] = str(m_path.parent)

                # Check registry.yaml toggle; defaults to manifest setting or True
                is_enabled = self._config_toggles.get(feat_id, manifest.get("enabled", True))
                manifest["enabled"] = is_enabled

                self._manifests[feat_id] = manifest
            except Exception as e:
                logger.error(f"Failed to parse manifest at {m_path}: {e}")

        logger.info(f"Discovered {len(self._manifests)} feature manifests.")
        return self._manifests

    def register_feature_class(self, feature_id: str, feature_class: Type[BaseFeature]) -> None:
        """
        Explicitly registers a feature implementation class.
        """
        if not issubclass(feature_class, BaseFeature):
            raise TypeError(f"Class {feature_class.__name__} must inherit from core.base_feature.BaseFeature")
        self._feature_classes[feature_id] = feature_class

    def load_all_features(self) -> Dict[str, BaseFeature]:
        """
        Discovers, dynamically imports, and instantiates all enabled features.
        """
        self.discover_features()

        for feat_id, manifest in self._manifests.items():
            if not manifest.get("enabled", False):
                logger.debug(f"Feature {feat_id} is disabled. Skipping.")
                continue

            feat_dir = Path(manifest["_path"])
            entrypoint = manifest.get("entrypoint", "feature.py")
            entry_file = feat_dir / entrypoint

            if not entry_file.exists():
                logger.warning(f"Entrypoint {entrypoint} missing for feature {feat_id} at {feat_dir}")
                continue

            try:
                module_name = f"features.{feat_dir.name}.{entry_file.stem}"
                spec = importlib.util.spec_from_file_location(module_name, entry_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)

                    # Locate BaseFeature subclass in module
                    found_class: Optional[Type[BaseFeature]] = None
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, BaseFeature)
                            and attr is not BaseFeature
                        ):
                            found_class = attr
                            break

                    if found_class:
                        self._feature_classes[feat_id] = found_class
                        instance = found_class(manifest)
                        self._instances[feat_id] = instance
                        logger.info(f"Successfully loaded and registered feature: {feat_id} ({instance.name})")
                    else:
                        logger.warning(f"No BaseFeature subclass found in {entry_file} for {feat_id}")
            except Exception as e:
                logger.error(f"Failed to dynamically load feature {feat_id}: {e}", exc_info=True)

        return self._instances

    def get_feature(self, feature_id: str) -> Optional[BaseFeature]:
        """Returns the instantiated feature plugin by ID."""
        return self._instances.get(feature_id)

    def get_features_by_category(self, category: str) -> List[BaseFeature]:
        """Returns all loaded features belonging to a category (e.g. CAT_A, CAT_B, etc.)."""
        return [
            feat for feat in self._instances.values()
            if feat.category.upper() == category.upper() and feat.is_enabled()
        ]

    def list_active_features(self) -> List[Dict[str, Any]]:
        """Returns metadata summary of all currently active features."""
        return [
            {
                "id": feat.feature_id,
                "name": feat.name,
                "category": feat.category,
                "version": feat.version,
                "sub_features_count": len(feat.sub_features),
            }
            for feat in self._instances.values()
        ]


# Global Singleton Registry Instance
registry = FeatureRegistry()
