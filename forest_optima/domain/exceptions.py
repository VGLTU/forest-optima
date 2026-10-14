# -*- coding: utf-8 -*-
"""Иерархия доменных исключений программного комплекса Лес-Оптима."""

from typing import Optional


class ForestOptimaError(Exception):
    """Базовое исключение доменной области комплекса."""
    pass


class ValidationError(ForestOptimaError):
    """Ошибка валидации входных данных или параметров моделирования."""
    pass


class NormalizationError(ForestOptimaError):
    """Ошибка при математической нормализации векторов данных."""
    pass


class DatasetEmptyError(ValidationError):
    """Исключение при передаче пустого набора лесничеств или предприятий."""
    pass
