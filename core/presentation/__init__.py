"""Stable, browser-facing views assembled from application contracts."""

from .assembler import (
    build_character_editor_view,
    build_move_calculation_view,
    build_wengine_editor_view,
)
from .catalog import (
    CharacterCatalogItem,
    WEngineCatalogItem,
    supported_character_catalog,
    supported_wengine_catalog,
)
from .character_editor import (
    CharacterEditorView,
    CompileConfigFieldView,
    WEngineEditorView,
)
from .calculation import (
    CalculationView,
    DamageEventModeView,
    DamageEventView,
    MoveCalculationView,
)
from .requests import CharacterBuildInput, EnemyInput, MoveCalculationViewRequest
from .registry import (
    CharacterPresentationRegistration,
    build_registered_editor_view,
    build_registered_wengine_editor_view,
    compile_registered_definition,
    config_fields_for,
    registration_for,
    supported_character_registrations,
)

__all__ = [
    "CalculationView",
    "CharacterBuildInput",
    "CharacterCatalogItem",
    "WEngineCatalogItem",
    "CharacterEditorView",
    "CompileConfigFieldView",
    "WEngineEditorView",
    "DamageEventModeView",
    "DamageEventView",
    "EnemyInput",
    "MoveCalculationView",
    "MoveCalculationViewRequest",
    "build_character_editor_view",
    "build_move_calculation_view",
    "build_wengine_editor_view",
    "CharacterPresentationRegistration",
    "build_registered_editor_view",
    "build_registered_wengine_editor_view",
    "compile_registered_definition",
    "config_fields_for",
    "registration_for",
    "supported_character_registrations",
    "supported_character_catalog",
    "supported_wengine_catalog",
]
