# -*- coding: utf-8 -*-
"""
Сервис классификации предприятий-лесопользователей на основе матрицы Эйлера-Венна.
Реализует триединую модель устойчивого развития:
1. Экономическая эффективность (У_экон).
2. Экологическая ответственность (У_экол).
3. Социальная отдача (У_соц).
"""

from __future__ import annotations
from typing import Sequence

from forest_optima.domain.constants import (
    HARMONY_ZONE_THRESHOLD,
    HIGH_SUSTAINABILITY_THRESHOLD,
    MEDIUM_SUSTAINABILITY_THRESHOLD,
)
from forest_optima.domain.exceptions import DatasetEmptyError
from forest_optima.domain.models import EnterpriseEvaluation, ForestEnterprise


def classify_sustainability_level(total_score: float) -> str:
    """Определение качественного уровня устойчивости лесопользования."""
    if total_score >= HIGH_SUSTAINABILITY_THRESHOLD:
        return "Высокий (рациональное лесопользование)"
    if total_score >= MEDIUM_SUSTAINABILITY_THRESHOLD:
        return "Средний (допустимое развитие)"
    return "Низкий (кризисное состояние)"


def determine_euler_venn_zone(
    enterprise: ForestEnterprise,
    total_score: float,
) -> str:
    """
    Определение топологической зоны в трехлепестковой диаграмме Эйлера-Венна.
    """
    if total_score >= HARMONY_ZONE_THRESHOLD:
        return "Абсолютная гармония (Социо-Эколого-Экономическая)"

    factors = [
        ("Экономика", enterprise.economic_score),
        ("Экология", enterprise.ecological_score),
        ("Социум", enterprise.social_score),
    ]
    # Сортировка по невозрастанию баллов
    factors.sort(key=lambda item: item[1], reverse=True)

    top1_name, top1_val = factors[0]
    top2_name, top2_val = factors[1]

    # Если два ведущих фактора равны — би-критериальное пересечение
    if abs(top1_val - top2_val) < 1e-6 and top1_val > 0:
        return f"Би-критериальная зона ({top1_name}-{top2_name})"

    return f"Моно-доминанта: {top1_name}"


def evaluate_enterprises(
    enterprises: Sequence[ForestEnterprise],
) -> list[EnterpriseEvaluation]:
    """
    Комплексная оценка устойчивости совокупности предприятий-арендаторов.

    Returns:
        Список объектов EnterpriseEvaluation, отсортированный по интегральному баллу (убывание).
    """
    if not enterprises:
        raise DatasetEmptyError("Набор предприятий для оценки не может быть пустым.")

    results: list[EnterpriseEvaluation] = []
    for ent in enterprises:
        total = round(ent.economic_score + ent.ecological_score + ent.social_score, 1)
        level = classify_sustainability_level(total)
        zone = determine_euler_venn_zone(ent, total)

        results.append(
            EnterpriseEvaluation(
                enterprise=ent,
                total_score=total,
                sustainability_level=level,
                euler_venn_zone=zone,
            )
        )

    results.sort(key=lambda r: r.total_score, reverse=True)
    return results
