"""
Feature registration module.

This module registers all features with the feature registry.
Import this module to ensure all features are registered.
"""
from features import feature_registry
from common_resource_feature import common_resource_feature
from armagedon_anomalies_feature import armagedon_anomalies_feature

# Register all features
feature_registry.register(common_resource_feature)
feature_registry.register(armagedon_anomalies_feature)

print("✅ All features registered")
