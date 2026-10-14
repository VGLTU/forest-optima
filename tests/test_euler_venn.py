# -*- coding: utf-8 -*-
"""Тестирование сервиса матрицы Эйлера-Венна."""

import pytest
from forest_optima.domain.exceptions import DatasetEmptyError
from forest_optima.domain.models import ForestEnterprise
from forest_optima.services.euler_venn import (
    classify_sustainability_level,
    determine_euler_venn_zone,
    evaluate_enterprises,
)


def test_euler_venn_full_dataset(full_enterprises_dataset: list[ForestEnterprise]):
    results = evaluate_enterprises(full_enterprises_dataset)
    assert len(results) == len(full_enterprises_dataset)

    # Лидер устойчивости - Шипов Лес (максимальные баллы 5/5/5)
    shipov = results[0]
    assert shipov.enterprise.name == "ООО Фирма «Шипов лес»"
    assert shipov.total_score == 15.0
    assert "Абсолютная гармония" in shipov.euler_venn_zone
    assert "Высокий" in shipov.sustainability_level


def test_euler_venn_boundary_levels():
    assert "Высокий" in classify_sustainability_level(11.0)
    assert "Средний" in classify_sustainability_level(10.9)
    assert "Средний" in classify_sustainability_level(6.0)
    assert "Низкий" in classify_sustainability_level(5.9)


def test_euler_venn_bi_criteria_zone():
    ent = ForestEnterprise("Тестовое предприятие", 4.0, 4.0, 1.0)
    zone = determine_euler_venn_zone(ent, total_score=9.0)
    assert "Би-критериальная зона (Экономика-Экология)" in zone


def test_euler_venn_empty_dataset_raises():
    with pytest.raises(DatasetEmptyError):
        evaluate_enterprises([])
