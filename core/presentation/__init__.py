"""Stable, browser-facing views assembled from application contracts."""

from .assembler import build_character_editor_view, build_move_calculation_view
from .catalog import CharacterCatalogItem, supported_character_catalog
from .calculation import (
    CalculationView,
    DamageEventModeView,
    DamageEventView,
    MoveCalculationView,
)
from .character_editor import CharacterEditorView
from .requests import CharacterBuildInput, EnemyInput, MoveCalculationViewRequest

__all__ = [
    "CalculationView",
    "CharacterBuildInput",
    "CharacterCatalogItem",
    "CharacterEditorView",
    "DamageEventModeView",
    "DamageEventView",
    "EnemyInput",
    "MoveCalculationView",
    "MoveCalculationViewRequest",
    "build_character_editor_view",
    "build_move_calculation_view",
    "supported_character_catalog",
]
