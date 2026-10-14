# -*- coding: utf-8 -*-
"""
Математические алгоритмы нормализации многомерных векторов данных.
Реализует приведение разноразмерных физических величин к безразмерной шкале [0, 1].
"""

from __future__ import annotations
import math
from typing import Sequence

from forest_optima.domain.exceptions import DatasetEmptyError, NormalizationError


def min_max_scale(values: Sequence[float], default_zero_variance: float = 0.0) -> list[float]:
    """
    Линейная Min-Max нормализация вектора значений к интервалу [0, 1].

    Формула:
        x'_i = (x_i - min(X)) / (max(X) - min(X))

    Защита от нулевой дисперсии:
        Если все значения в выборке равны (max == min), возвращается вектор,
        заполненный default_zero_variance (по умолчанию 0.0).

    Raises:
        DatasetEmptyError: Если последовательность пуста.
    """
    if not values:
        raise DatasetEmptyError("Невозможно нормализовать пустую последовательность значений.")

    min_val = min(values)
    max_val = max(values)
    span = max_val - min_val

    if abs(span) < 1e-12:
        return [default_zero_variance for _ in values]

    return [(x - min_val) / span for x in values]


def z_score_scale(values: Sequence[float]) -> list[float]:
    """
    Стандартизация вектора значений методом Z-Score (среднее 0, дисперсия 1).

    Формула:
        z_i = (x_i - mu) / sigma

    Защита:
        Если стандартное отклонение равно 0, возвращается вектор нулей.

    Raises:
        DatasetEmptyError: Если последовательность пуста.
    """
    if not values:
        raise DatasetEmptyError("Невозможно стандартизировать пустую последовательность значений.")

    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    std = math.sqrt(variance)

    if abs(std) < 1e-12:
        return [0.0 for _ in values]

    return [(x - mean) / std for x in values]
