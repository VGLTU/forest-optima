# -*- coding: utf-8 -*-
"""
Консольный интерфейс (CLI) и точка входа в аналитический комплекс Лес-Оптима.
Предоставляет параметры конфигурации весов, форматированный табличный вывод и экспорт.
"""

from __future__ import annotations
import argparse
import logging
import sys
from pathlib import Path
from typing import Sequence

from forest_optima.domain.constants import (
    DEFAULT_ENTERPRISES_DATA,
    DEFAULT_FORESTRY_DATA,
    DEFAULT_WEIGHTS,
)
from forest_optima.domain.exceptions import ForestOptimaError
from forest_optima.domain.models import (
    CriterionWeights,
    DistrictEvaluation,
    EnterpriseEvaluation,
)
from forest_optima.services.euler_venn import evaluate_enterprises
from forest_optima.services.mcda import evaluate_districts
from forest_optima.storage.csv_exporter import export_to_csv
from forest_optima.storage.excel_exporter import OPENPYXL_AVAILABLE, export_to_excel

logger = logging.getLogger("forest_optima")


def setup_logging(verbose: bool = False) -> None:
    """Настройка структурированного логирования приложения."""
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="[%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.setLevel(level)
    logger.handlers.clear()
    logger.addHandler(handler)


def format_districts_table(evaluations: Sequence[DistrictEvaluation], limit: int = 12) -> str:
    """Форматирует сводную таблицу лесничеств для вывода в консоль."""
    lines = [
        "",
        "=" * 105,
        f"{'Лесничество':<18} | {'Запас (тыс.м³)':<14} | {'Площадь (га)':<12} | "
        f"{'Базовая (EV)':<12} | {'Ранг баз.':<10} | {'Лес-Оптима':<11} | {'Ранг':<5} | {'Смещение':<8}",
        "=" * 105,
    ]

    for item in evaluations[:limit]:
        d = item.district
        shift_str = f"+{item.rank_shift}" if item.rank_shift > 0 else str(item.rank_shift)
        lines.append(
            f"{d.name:<18} | {d.timber_stock_k_m3:<14.1f} | {d.allowed_area_ha:<12.1f} | "
            f"{item.raw_score:<12.2f} | {item.raw_rank:<10} | {item.wsm_score:<11.4f} | "
            f"{item.optimal_rank:<5} | {shift_str:<8}"
        )

    if len(evaluations) > limit:
        lines.append(f"... и еще {len(evaluations) - limit} лесничеств (полный список сохранен в отчете)")
    lines.append("=" * 105)
    return "\n".join(lines)


def format_enterprises_table(evaluations: Sequence[EnterpriseEvaluation]) -> str:
    """Форматирует таблицу оценки арендаторов по диаграмме Эйлера-Венна."""
    lines = [
        "",
        "[ОЦЕНКА УСТОЙЧИВОСТИ АРЕНДАТОРОВ ПО ДИАГРАММЕ ЭЙЛЕРА-ВЕННА]:",
        "-" * 105,
        f"{'Предприятие':<32} | {'Балл (0-15)':<11} | {'Качественный уровень':<35} | {'Зона матрицы'}",
        "-" * 105,
    ]

    for item in evaluations:
        lines.append(
            f"{item.enterprise.name:<32} | {item.total_score:<11.1f} | "
            f"{item.sustainability_level:<35} | {item.euler_venn_zone}"
        )

    lines.append("-" * 105)
    return "\n".join(lines)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Разбор аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog="forest-optima",
        description="Программный комплекс многокритериальной оценки лесного фонда (ВГЛТУ, 2026)",
    )
    parser.add_argument(
        "--stock-weight",
        type=float,
        default=DEFAULT_WEIGHTS.stock,
        help="Весовой коэффициент запаса древесины (по умолч.: 0.5)",
    )
    parser.add_argument(
        "--area-weight",
        type=float,
        default=DEFAULT_WEIGHTS.area,
        help="Весовой коэффициент разрешенной площади (по умолч.: 0.2)",
    )
    parser.add_argument(
        "--roads-weight",
        type=float,
        default=DEFAULT_WEIGHTS.roads,
        help="Весовой коэффициент лесных дорог (по умолч.: 0.3)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Каталог сохранения итоговых аналитических файлов",
    )
    parser.add_argument(
        "--format",
        choices=["all", "xlsx", "csv", "none"],
        default="all",
        help="Формат выгрузки отчетов (по умолч.: all)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Включить подробный вывод отладочной информации",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Основной сценарий выполнения консольного приложения."""
    args = parse_args(argv)
    setup_logging(verbose=args.verbose)

    logger.info("=" * 65)
    logger.info(" ИНФОРМАЦИОННО-АНАЛИТИЧЕСКИЙ КОМПЛЕКС 'ЛЕС-ОПТИМА' v1.0")
    logger.info("  Научно-прикладная разработка ФГБОУ ВО «ВГЛТУ имени Г.Ф. Морозова»")
    logger.info("=" * 65)

    try:
        weights = CriterionWeights(
            stock=args.stock_weight,
            area=args.area_weight,
            roads=args.roads_weight,
        ).normalized

        logger.info(
            "Параметры весов: древесина=%.2f, площадь=%.2f, дороги=%.2f (сумма: %.2f)",
            weights.stock,
            weights.area,
            weights.roads,
            weights.stock + weights.area + weights.roads,
        )

        districts_res = evaluate_districts(DEFAULT_FORESTRY_DATA, weights=weights)
        enterprises_res = evaluate_enterprises(DEFAULT_ENTERPRISES_DATA)

        print(format_districts_table(districts_res))
        print(format_enterprises_table(enterprises_res))

        out_dir = Path(args.output_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        if args.format in ["all", "xlsx"]:
            if OPENPYXL_AVAILABLE:
                xlsx_path = out_dir / "Результаты_Оценки_ЛесОптима.xlsx"
                export_to_excel(districts_res, enterprises_res, xlsx_path)
                logger.info("Сформирован премиальный Excel-отчет: %s", xlsx_path.name)
            else:
                logger.warning("openpyxl недоступен; экспорт в XLSX пропущен.")

        if args.format in ["all", "csv"]:
            csv_path = out_dir / "Результаты_Оценки_ЛесОптима.csv"
            export_to_csv(districts_res, enterprises_res, csv_path)
            logger.info("Сформирован резервный CSV-отчет: %s", csv_path.name)

        logger.info("Расчет многокритериальной модели успешно завершен.")
        return 0

    except ForestOptimaError as err:
        logger.error("Доменная ошибка моделирования: %s", err)
        return 2
    except Exception as exc:
        logger.exception("Непредвиденная системная ошибка: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
