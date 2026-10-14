# -*- coding: utf-8 -*-
"""Тестирование доменных моделей и валидации."""

import pytest
from forest_optima.domain.exceptions import ValidationError
from forest_optima.domain.models import CriterionWeights, ForestDistrict, ForestEnterprise


def test_criterion_weights_valid():
    w = CriterionWeights(stock=0.5, area=0.2, roads=0.3)
    assert w.stock == 0.5
    assert w.area == 0.2
    assert w.roads == 0.3
    assert abs(w.normalized.stock - 0.5) < 1e-6


def test_criterion_weights_auto_normalization():
    w = CriterionWeights(stock=50, area=20, roads=30)
    norm = w.normalized
    assert abs(norm.stock - 0.5) < 1e-6
    assert abs(norm.area - 0.2) < 1e-6
    assert abs(norm.roads - 0.3) < 1e-6
    assert abs((norm.stock + norm.area + norm.roads) - 1.0) < 1e-6


def test_criterion_weights_negative_rejected():
    with pytest.raises(ValidationError):
        CriterionWeights(stock=-0.1, area=0.2, roads=0.3)


def test_criterion_weights_zero_sum_rejected():
    with pytest.raises(ValidationError):
        CriterionWeights(stock=0.0, area=0.0, roads=0.0)


def test_forest_district_validation():
    d = ForestDistrict("Теллермановское", 6546.2, 40549.7, 415.7)
    assert d.name == "Теллермановское"

    with pytest.raises(ValidationError):
        ForestDistrict("", 100, 100, 100)

    with pytest.raises(ValidationError):
        ForestDistrict("Тест", -5.0, 100, 100)


def test_forest_enterprise_validation():
    e = ForestEnterprise("ООО Тест", 4.5, 3.0, 5.0)
    assert e.name == "ООО Тест"

    with pytest.raises(ValidationError):
        ForestEnterprise("ООО Ошибка", 6.0, 3.0, 2.0)  # > 5.0

    with pytest.raises(ValidationError):
        ForestEnterprise("ООО Ошибка", -1.0, 3.0, 2.0)  # < 0.0
