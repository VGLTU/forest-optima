# -*- coding: utf-8 -*-
"""Тестирование сервиса математической нормализации."""

import pytest
from forest_optima.domain.exceptions import DatasetEmptyError
from forest_optima.services.normalization import min_max_scale, z_score_scale


def test_min_max_scale_regular():
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    scaled = min_max_scale(values)
    assert scaled[0] == 0.0
    assert scaled[-1] == 1.0
    assert scaled[2] == 0.5


def test_min_max_scale_zero_variance():
    # Все значения одинаковы (дисперсия = 0)
    values = [42.0, 42.0, 42.0]
    scaled = min_max_scale(values, default_zero_variance=0.0)
    assert scaled == [0.0, 0.0, 0.0]


def test_min_max_scale_empty_raises():
    with pytest.raises(DatasetEmptyError):
        min_max_scale([])


def test_z_score_scale_regular():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    scaled = z_score_scale(values)
    mean = sum(scaled) / len(scaled)
    assert abs(mean) < 1e-6


def test_z_score_scale_zero_variance():
    values = [10.0, 10.0, 10.0]
    scaled = z_score_scale(values)
    assert scaled == [0.0, 0.0, 0.0]
