# -*- coding: utf-8 -*-
"""
Алгоритмы многокритериального анализа решений (MCDA - Multi-Criteria Decision Analysis):
1. Базовая аддитивная модель (без нормализации, монография ВГЛТУ).
2. Нормализованная взвешенная сумма (WSM - Weighted Sum Model).
3. Метод идеальной точки (TOPSIS - Technique for Order Preference by Similarity to Ideal Solution).
"""

from __future__ import annotations
import math
from typing import Sequence

from forest_optima.domain.constants import DEFAULT_WEIGHTS
from forest_optima.domain.exceptions import DatasetEmptyError
from forest_optima.domain.models import (
    CriterionWeights,
    DistrictEvaluation,
    ForestDistrict,
    NormalizedCriteria,
)
from forest_optima.services.normalization import min_max_scale


def calculate_raw_score(district: ForestDistrict, weights: CriterionWeights) -> float:
    """
    Традиционная аддитивная свертка без предварительной нормализации размерностей:
        EV_raw = x_1 * w_1 + x_2 * w_2 + x_3 * w_3
    """
    return round(
        district.timber_stock_k_m3 * weights.stock
        + district.allowed_area_ha * weights.area
        + district.road_length_km * weights.roads,
        2,
    )


def calculate_wsm_score(norm: NormalizedCriteria, weights: CriterionWeights) -> float:
    """
    Нормализованный интегральный индекс WSM (Weighted Sum Model) в интервале [0, 1]:
        WSM = x'_1 * w_1 + x'_2 * w_2 + x'_3 * w_3
    """
    norm_w = weights.normalized
    score = (
        norm.stock * norm_w.stock
        + norm.area * norm_w.area
        + norm.roads * norm_w.roads
    )
    return round(score, 4)


def calculate_topsis_score(norm: NormalizedCriteria, weights: CriterionWeights) -> float:
    """
    Многомерная векторная оценка близости к идеальной точке (TOPSIS):
        D+ = sqrt( sum( w_j * (1 - x'_j)^2 ) )
        D- = sqrt( sum( w_j * (x'_j - 0)^2 ) )
        C_i = D- / (D+ + D-)
    """
    norm_w = weights.normalized

    d_plus = math.sqrt(
        norm_w.stock * ((1.0 - norm.stock) ** 2)
        + norm_w.area * ((1.0 - norm.area) ** 2)
        + norm_w.roads * ((1.0 - norm.roads) ** 2)
    )

    d_minus = math.sqrt(
        norm_w.stock * (norm.stock ** 2)
        + norm_w.area * (norm.area ** 2)
        + norm_w.roads * (norm.roads ** 2)
    )

    total_dist = d_plus + d_minus
    if total_dist < 1e-12:
        return 0.0

    return round(d_minus / total_dist, 4)


def evaluate_districts(
    districts: Sequence[ForestDistrict],
    weights: CriterionWeights | None = None,
) -> list[DistrictEvaluation]:
    """
    Комплексная оценка и ранжирование совокупности лесничеств.

    Выполняет:
    1. Min-Max нормализацию физических критериев к шкале [0, 1].
    2. Расчет базовой аддитивной свертки (для сравнительного анализа с монографией).
    3. Расчет нормализованного индекса WSM и индекса TOPSIS.
    4. Определение рангов и расчет дельты смещения позиций.

    Returns:
        Список объектов DistrictEvaluation, отсортированный по WSM-индексу (убывание).
    """
    if not districts:
        raise DatasetEmptyError("Набор лесничеств для оценки не может быть пустым.")

    w = (weights or DEFAULT_WEIGHTS).normalized

    stocks = [d.timber_stock_k_m3 for d in districts]
    areas = [d.allowed_area_ha for d in districts]
    roads = [d.road_length_km for d in districts]

    norm_stocks = min_max_scale(stocks)
    norm_areas = min_max_scale(areas)
    norm_roads = min_max_scale(roads)

    # Временный промежуточный контейнер
    class _Interim:
        def __init__(self, district: ForestDistrict, norm: NormalizedCriteria):
            self.district = district
            self.norm = norm
            self.raw_score = calculate_raw_score(district, w)
            self.wsm_score = calculate_wsm_score(norm, w)
            self.topsis_score = calculate_topsis_score(norm, w)
            self.raw_rank = 0
            self.optimal_rank = 0

    interim_list = [
        _Interim(d, NormalizedCriteria(stock=ns, area=na, roads=nr))
        for d, ns, na, nr in zip(districts, norm_stocks, norm_areas, norm_roads)
    ]

    # Ранжирование по базовой ненормированной модели (монография)
    interim_list.sort(key=lambda item: item.raw_score, reverse=True)
    for rank_idx, item in enumerate(interim_list, start=1):
        item.raw_rank = rank_idx

    # Ранжирование по нормализованной модели Лес-Оптима (WSM)
    interim_list.sort(key=lambda item: item.wsm_score, reverse=True)
    for rank_idx, item in enumerate(interim_list, start=1):
        item.optimal_rank = rank_idx

    # Формирование итоговых доменных объектов
    results: list[DistrictEvaluation] = []
    for item in interim_list:
        rank_shift = item.raw_rank - item.optimal_rank
        results.append(
            DistrictEvaluation(
                district=item.district,
                normalized=item.norm,
                raw_score=item.raw_score,
                wsm_score=item.wsm_score,
                topsis_score=item.topsis_score,
                raw_rank=item.raw_rank,
                optimal_rank=item.optimal_rank,
                rank_shift=rank_shift,
            )
        )

    return results
