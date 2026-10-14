# -*- coding: utf-8 -*-
"""Тестирование алгоритмов многокритериального анализа решений (MCDA)."""

import pytest
from forest_optima.domain.exceptions import DatasetEmptyError
from forest_optima.domain.models import CriterionWeights, ForestDistrict
from forest_optima.services.mcda import (
    calculate_raw_score,
    calculate_topsis_score,
    calculate_wsm_score,
    evaluate_districts,
)


def test_mcda_evaluation_on_full_dataset(full_districts_dataset: list[ForestDistrict]):
    results = evaluate_districts(full_districts_dataset)
    assert len(results) == len(full_districts_dataset)

    # 1. Лидер нормализованной модели - Теллермановское
    top_district = results[0]
    assert top_district.district.name == "Теллермановское"
    assert top_district.optimal_rank == 1
    assert top_district.wsm_score > 0.90

    # 2. Проверка Павловского (в ненормированной модели было #1 из-за масштаба площади)
    pavlovskoe = next(r for r in results if r.district.name == "Павловское")
    assert pavlovskoe.raw_rank == 1  # Было первым в базовой модели
    assert pavlovskoe.optimal_rank == 4  # Закономерно опустилось на 4 место в WSM
    assert pavlovskoe.rank_shift == -3  # Смещение на 3 позиции вниз

    # 3. Все индексы WSM и TOPSIS в интервале [0, 1]
    for r in results:
        assert 0.0 <= r.wsm_score <= 1.0
        assert 0.0 <= r.topsis_score <= 1.0
        assert r.optimal_rank >= 1
        assert r.raw_rank >= 1


def test_mcda_custom_weights(sample_districts: list[ForestDistrict]):
    # Вес только на древесину
    weights = CriterionWeights(stock=1.0, area=0.0, roads=0.0)
    results = evaluate_districts(sample_districts, weights=weights)

    # Лесничество В имеет максимальный запас (3000), должно быть первым
    assert results[0].district.name == "Лесничество В"
    assert results[0].wsm_score == 1.0


def test_mcda_empty_dataset_raises():
    with pytest.raises(DatasetEmptyError):
        evaluate_districts([])
