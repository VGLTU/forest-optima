# -*- coding: utf-8 -*-
"""
Программный комплекс "Лес-Оптима" (Forest-Optima v1.0).
Фасадный модуль обратной совместимости.
Делегирует исполнение архитектурно чистому пакету forest_optima.
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Any

# Добавляем родительскую директорию в sys.path для надежного импорта при прямом запуске
_CURRENT_DIR = Path(__file__).resolve().parent
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))

from forest_optima.domain.constants import (
    DEFAULT_ENTERPRISES_DATA,
    DEFAULT_FORESTRY_DATA,
    DEFAULT_WEIGHTS,
)
from forest_optima.domain.models import (
    CriterionWeights,
    ForestDistrict as ForestryDistrict,
    ForestEnterprise,
)
from forest_optima.services.euler_venn import evaluate_enterprises
from forest_optima.services.mcda import evaluate_districts
from forest_optima.storage.csv_exporter import export_to_csv
from forest_optima.storage.excel_exporter import OPENPYXL_AVAILABLE, export_to_excel
from forest_optima.cli import main

# Алиасы для полной обратной совместимости
FORESTRY_DATA = DEFAULT_FORESTRY_DATA
ENTERPRISES_DATA = DEFAULT_ENTERPRISES_DATA
WEIGHT_STOCK = DEFAULT_WEIGHTS.stock
WEIGHT_AREA = DEFAULT_WEIGHTS.area
WEIGHT_ROADS = DEFAULT_WEIGHTS.roads
HAS_OPENPYXL = OPENPYXL_AVAILABLE


def calculate_models(districts: list[ForestryDistrict] | None = None) -> list[dict[str, Any]]:
    """
    Адаптер обратной совместимости: возвращает словарное представление
    результатов многокритериальной оценки.
    """
    items = districts or DEFAULT_FORESTRY_DATA
    evaluated = evaluate_districts(items)

    records: list[dict[str, Any]] = []
    for item in evaluated:
        d = item.district
        delta_str = f"+{item.rank_shift}" if item.rank_shift > 0 else str(item.rank_shift)
        records.append({
            "Лесничество": d.name,
            "Запас_тыс_м3": d.timber_stock_k_m3,
            "Площадь_га": d.allowed_area_ha,
            "Дороги_км": d.road_length_km,
            "EV_монография": item.raw_score,
            "Ранг_монография": item.raw_rank,
            "Индекс_ЛесОптима": item.wsm_score,
            "Индекс_TOPSIS": item.topsis_score,
            "Ранг_ЛесОптима": item.optimal_rank,
            "Дельта_рангов": delta_str,
        })
    return records


def classify_enterprises(enterprises: list[ForestEnterprise] | None = None) -> list[dict[str, Any]]:
    """
    Адаптер обратной совместимости: возвращает словарное представление
    классификации предприятий по матрице Эйлера-Венна.
    """
    items = enterprises or DEFAULT_ENTERPRISES_DATA
    evaluated = evaluate_enterprises(items)

    records: list[dict[str, Any]] = []
    for item in evaluated:
        e = item.enterprise
        records.append({
            "Предприятие": e.name,
            "У_экон": e.economic_score,
            "У_экол": e.ecological_score,
            "У_соц": e.social_score,
            "Интеграл (0-15)": item.total_score,
            "Уровень": item.sustainability_level,
            "Зона_Эйлера_Венна": item.euler_venn_zone,
        })
    return records


def export_all(forestry_res: list[Any] | None = None, enterprise_res: list[Any] | None = None) -> None:
    """Экспорт результатов в Excel и CSV."""
    f_res = evaluate_districts(DEFAULT_FORESTRY_DATA)
    e_res = evaluate_enterprises(DEFAULT_ENTERPRISES_DATA)

    xlsx_path = _CURRENT_DIR / "Результаты_Оценки_ЛесОптима.xlsx"
    csv_path = _CURRENT_DIR / "Результаты_Оценки_ЛесОптима.csv"

    if OPENPYXL_AVAILABLE:
        export_to_excel(f_res, e_res, xlsx_path)
    export_to_csv(f_res, e_res, csv_path)


if __name__ == "__main__":
    sys.exit(main())
