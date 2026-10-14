# -*- coding: utf-8 -*-
"""
Модуль экспорта результатов моделирования в формат CSV.
Использует кодировку UTF-8 с BOM (utf-8-sig) для бесшовного открытия в Microsoft Excel на macOS и Windows.
"""

from __future__ import annotations
import csv
from pathlib import Path
from typing import Sequence

from forest_optima.domain.models import DistrictEvaluation, EnterpriseEvaluation


def export_to_csv(
    districts_res: Sequence[DistrictEvaluation],
    enterprises_res: Sequence[EnterpriseEvaluation],
    output_path: str | Path,
) -> Path:
    """
    Экспортирует результаты оценки лесничеств и предприятий в единый структурированный CSV-файл.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")

        # Раздел 1: Лесничества
        writer.writerow(["=== МНОГОКРИТЕРИАЛЬНАЯ ОЦЕНКА ЛЕСНИЧЕСТВ (ЛЕС-ОПТИМА) ==="])
        writer.writerow([
            "Лесничество",
            "Запас древесины (тыс. м3)",
            "Разрешенная площадь (га)",
            "Протяженность дорог (км)",
            "Базовая линейная модель (EV_raw)",
            "Ранг в базовой модели",
            "Индекс Лес-Оптима (WSM)",
            "Индекс TOPSIS",
            "Скорректированный ранг",
            "Смещение ранга",
        ])

        for r in districts_res:
            delta_str = f"+{r.rank_shift}" if r.rank_shift > 0 else str(r.rank_shift)
            writer.writerow([
                r.district.name,
                f"{r.district.timber_stock_k_m3:.1f}",
                f"{r.district.allowed_area_ha:.1f}",
                f"{r.district.road_length_km:.1f}",
                f"{r.raw_score:.2f}",
                r.raw_rank,
                f"{r.wsm_score:.4f}",
                f"{r.topsis_score:.4f}",
                r.optimal_rank,
                delta_str,
            ])

        writer.writerow([])
        # Раздел 2: Предприятия
        writer.writerow(["=== ОЦЕНКА АРЕНДАТОРОВ (МАТРИЦА ЭЙЛЕРА-ВЕННА) ==="])
        writer.writerow([
            "Предприятие",
            "Экономика (У_экон)",
            "Экология (У_экол)",
            "Социум (У_соц)",
            "Интеграл (0-15)",
            "Качественный уровень",
            "Зона матрицы Эйлера-Венна",
        ])

        for e in enterprises_res:
            writer.writerow([
                e.enterprise.name,
                f"{e.enterprise.economic_score:.1f}",
                f"{e.enterprise.ecological_score:.1f}",
                f"{e.enterprise.social_score:.1f}",
                f"{e.total_score:.1f}",
                e.sustainability_level,
                e.euler_venn_zone,
            ])

    return path
