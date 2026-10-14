# -*- coding: utf-8 -*-
"""Тестирование модулей экспорта данных в CSV и Excel."""

from pathlib import Path
import pytest
from forest_optima.domain.models import ForestDistrict, ForestEnterprise
from forest_optima.services.euler_venn import evaluate_enterprises
from forest_optima.services.mcda import evaluate_districts
from forest_optima.storage.csv_exporter import export_to_csv
from forest_optima.storage.excel_exporter import OPENPYXL_AVAILABLE, export_to_excel


def test_csv_export(tmp_path: Path, sample_districts: list[ForestDistrict]):
    districts_res = evaluate_districts(sample_districts)
    enterprises = [
        ForestEnterprise("Предприятие 1", 5.0, 5.0, 5.0),
        ForestEnterprise("Предприятие 2", 2.0, 2.0, 1.0),
    ]
    enterprises_res = evaluate_enterprises(enterprises)

    csv_file = tmp_path / "test_report.csv"
    result_path = export_to_csv(districts_res, enterprises_res, csv_file)

    assert result_path.exists()
    content = result_path.read_text(encoding="utf-8-sig")
    assert "Лесничество А" in content
    assert "Предприятие 1" in content
    assert "WSM" in content


@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl не установлен")
def test_excel_export(tmp_path: Path, sample_districts: list[ForestDistrict]):
    districts_res = evaluate_districts(sample_districts)
    enterprises = [
        ForestEnterprise("Предприятие 1", 5.0, 5.0, 5.0),
    ]
    enterprises_res = evaluate_enterprises(enterprises)

    xlsx_file = tmp_path / "test_report.xlsx"
    result_path = export_to_excel(districts_res, enterprises_res, xlsx_file)

    assert result_path.exists()
    assert result_path.stat().st_size > 0
