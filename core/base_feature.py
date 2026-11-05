# ==============================================================================
# 🔒 SACRED FILE 1 OF 4: core/base_feature.py
# RULE 5: base_feature.py IS SACRED.
# The `execute(context: ExecutionContext) -> ExecutionContext` signature MUST NEVER BE MODIFIED.
# All 38 features and their sub-features derive from this class.
# ==============================================================================

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from core.context import ExecutionContext


class BaseFeature(ABC):
    """
    The Mother of all Features in CypherLabelGuard CORE EDITION v2.0.
    
    Every single feature across Categories A through F inherits from this class.
    Each feature is completely plug-and-play and loaded via its manifest.yaml.
    """

    def __init__(self, manifest: Dict[str, Any]):
        """
        Initialize the feature with its loaded manifest metadata.
        """
        self.manifest: Dict[str, Any] = manifest
        self.feature_id: str = manifest.get("id", "feat_unknown")
        self.name: str = manifest.get("name", "Unknown Feature")
        self.category: str = manifest.get("category", "UNCATEGORIZED")
        self.version: str = manifest.get("version", "2.0.0")
        self.description: str = manifest.get("description", "")
        self.dependencies: List[str] = manifest.get("dependencies", [])
        self.enabled: bool = manifest.get("enabled", True)
        self.sub_features: List[Dict[str, Any]] = manifest.get("sub_features", [])

    @abstractmethod
    async def execute(self, context: "ExecutionContext") -> "ExecutionContext":
        """
        The SACRED execution signature.
        Takes an immutable ExecutionContext, performs its operation,
        and returns an evolved ExecutionContext.
        
        Args:
            context (ExecutionContext): The current execution context snapshot.
            
        Returns:
            ExecutionContext: The new evolved context snapshot.
        """
        raise NotImplementedError(f"{type(self).__name__} must implement execute()")

    def get_manifest(self) -> Dict[str, Any]:
        """Return the feature manifest dictionary."""
        return self.manifest

    def is_enabled(self) -> bool:
        """Check if the feature is currently active."""
        return self.enabled

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id='{self.feature_id}' category='{self.category}' enabled={self.enabled}>"
