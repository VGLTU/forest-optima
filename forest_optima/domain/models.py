# -*- coding: utf-8 -*-
"""
Доменные сущности и структуры данных программного комплекса Лес-Оптима.
Реализованы в виде строго типизированных неизменяемых классов данных (dataclasses).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import NamedTuple

from forest_optima.domain.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class CriterionWeights:
    """
    Весовые коэффициенты многокритериальной оценки.
    По умолчанию соответствуют экспертным весам из монографии ВГЛТУ (п. 3.1):
    - stock (запас древесины): 0.50
    - area (разрешенная площадь): 0.20
    - roads (лесные дороги): 0.30
    """
    stock: float = 0.50
    area: float = 0.20
    roads: float = 0.30

    def __post_init__(self) -> None:
        if self.stock < 0 or self.area < 0 or self.roads < 0:
            raise ValidationError("Весовые коэффициенты не могут быть отрицательными.")
        total = self.stock + self.area + self.roads
        if total <= 0:
            raise ValidationError("Сумма весовых коэффициентов должна быть строго больше нуля.")

    @property
    def normalized(self) -> CriterionWeights:
        """Возвращает нормализованные веса с суммой, строго равной 1.0."""
        total = self.stock + self.area + self.roads
        if abs(total - 1.0) < 1e-6:
            return self
        return CriterionWeights(
            stock=self.stock / total,
            area=self.area / total,
            roads=self.roads / total,
        )


@dataclass(frozen=True, slots=True)
class ForestDistrict:
    """
    Характеристика лесничества (объекта лесного фонда).
    """
    name: str
    timber_stock_k_m3: float  # Общий запас древесины, тыс. м3
    allowed_area_ha: float    # Разрешенная площадь заготовки, га
    road_length_km: float     # Протяженность лесных дорог, км

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValidationError("Наименование лесничества не может быть пустым.")
        if self.timber_stock_k_m3 < 0:
            raise ValidationError(f"Запас древесины не может быть отрицательным: {self.name}")
        if self.allowed_area_ha < 0:
            raise ValidationError(f"Площадь не может быть отрицательной: {self.name}")
        if self.road_length_km < 0:
            raise ValidationError(f"Протяженность дорог не может быть отрицательной: {self.name}")


@dataclass(frozen=True, slots=True)
class ForestEnterprise:
    """
    Предприятие-лесопользователь (арендатор лесного фонда).
    Оценки экспертной комиссии по шкале [0, 5].
    """
    name: str
    economic_score: float  # Экономическая устойчивость
    ecological_score: float  # Экологическая ответственность
    social_score: float  # Социальная эффективность

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValidationError("Наименование предприятия не может быть пустым.")
        for score_name, val in [
            ("экономической", self.economic_score),
            ("экологической", self.ecological_score),
            ("социальной", self.social_score),
        ]:
            if not (0.0 <= val <= 5.0):
                raise ValidationError(
                    f"Балл {score_name} оценки предприятия '{self.name}' "
                    f"должен находиться в интервале [0, 5], получено: {val}"
                )


@dataclass(frozen=True, slots=True)
class NormalizedCriteria:
    """Нормализованные критерии лесничества в шкале [0, 1]."""
    stock: float
    area: float
    roads: float


@dataclass(frozen=True, slots=True)
class DistrictEvaluation:
    """
    Результат многокритериальной оценки лесничества.
    Объединяет базовую аддитивную модель и современный нормализованный анализ (WSM + TOPSIS).
    """
    district: ForestDistrict
    normalized: NormalizedCriteria
    raw_score: float           # Традиционная аддитивная модель без нормализации (EV_raw)
    wsm_score: float           # Нормализованный интегральный индекс WSM [0, 1]
    topsis_score: float        # Векторный индекс близости к идеальной точке TOPSIS [0, 1]
    raw_rank: int              # Ранг в базовой ненормированной модели
    optimal_rank: int          # Ранг в нормализованной модели Лес-Оптима
    rank_shift: int            # Смещение позиции (raw_rank - optimal_rank)


@dataclass(frozen=True, slots=True)
class EnterpriseEvaluation:
    """
    Результат социо-эколого-экономической оценки предприятия-лесопользователя.
    """
    enterprise: ForestEnterprise
    total_score: float         # Интегральный балл (сумма трех факторов 0..15)
    sustainability_level: str  # Качественный уровень (Высокий / Средний / Низкий)
    euler_venn_zone: str       # Сегмент диаграммы Эйлера-Венна
