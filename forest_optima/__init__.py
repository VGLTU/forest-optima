# -*- coding: utf-8 -*-
"""
Программный комплекс "Лес-Оптима" (Forest-Optima v1.0).
Научно-прикладная разработка для регистрации РИД в Роспатенте (Программа для ЭВМ)
и публикации в научных журналах ВАК / RSCI.

Авторы: Зиновьева И.С., Бурмистров А.М., Лесных И.
ФГБОУ ВО «Воронежский государственный лесотехнический университет имени Г.Ф. Морозова» (ВГЛТУ)
"""

__version__ = "1.0.0"
__author__ = "Иван Лесных, И.С. Зиновьева, А.М. Бурмистров"

from forest_optima.domain.constants import (
    DEFAULT_ENTERPRISES_DATA,
    DEFAULT_FORESTRY_DATA,
    DEFAULT_WEIGHTS,
)
from forest_optima.domain.exceptions import (
    DatasetEmptyError,
    ForestOptimaError,
    NormalizationError,
    ValidationError,
)
from forest_optima.domain.models import (
    CriterionWeights,
    DistrictEvaluation,
    EnterpriseEvaluation,
    ForestDistrict,
    ForestEnterprise,
    NormalizedCriteria,
)
from forest_optima.services.euler_venn import evaluate_enterprises
from forest_optima.services.mcda import (
    calculate_raw_score,
    calculate_topsis_score,
    calculate_wsm_score,
    evaluate_districts,
)
from forest_optima.services.normalization import min_max_scale, z_score_scale
from forest_optima.storage.csv_exporter import export_to_csv
from forest_optima.storage.excel_exporter import export_to_excel

__all__ = [
    "__version__",
    "__author__",
    # Domain
    "CriterionWeights",
    "ForestDistrict",
    "ForestEnterprise",
    "NormalizedCriteria",
    "DistrictEvaluation",
    "EnterpriseEvaluation",
    "DEFAULT_WEIGHTS",
    "DEFAULT_FORESTRY_DATA",
    "DEFAULT_ENTERPRISES_DATA",
    "ForestOptimaError",
    "ValidationError",
    "NormalizationError",
    "DatasetEmptyError",
    # Services
    "min_max_scale",
    "z_score_scale",
    "calculate_raw_score",
    "calculate_wsm_score",
    "calculate_topsis_score",
    "evaluate_districts",
    "evaluate_enterprises",
    # Storage
    "export_to_csv",
    "export_to_excel",
]
