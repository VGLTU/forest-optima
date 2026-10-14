import sys
from pathlib import Path

# Обеспечиваем доступность пакета forest_optima при запуске из любого рабочего каталога
_PKG_ROOT = Path(__file__).resolve().parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

import pytest
from forest_optima.domain.constants import (
    DEFAULT_ENTERPRISES_DATA,
    DEFAULT_FORESTRY_DATA,
    DEFAULT_WEIGHTS,
)
from forest_optima.domain.models import CriterionWeights, ForestDistrict, ForestEnterprise


@pytest.fixture
def default_weights() -> CriterionWeights:
    return DEFAULT_WEIGHTS


@pytest.fixture
def sample_districts() -> list[ForestDistrict]:
    return [
        ForestDistrict("Лесничество А", 1000.0, 10000.0, 50.0),
        ForestDistrict("Лесничество Б", 2000.0, 5000.0, 100.0),
        ForestDistrict("Лесничество В", 3000.0, 2000.0, 150.0),
    ]


@pytest.fixture
def full_districts_dataset() -> list[ForestDistrict]:
    return DEFAULT_FORESTRY_DATA


@pytest.fixture
def full_enterprises_dataset() -> list[ForestEnterprise]:
    return DEFAULT_ENTERPRISES_DATA
