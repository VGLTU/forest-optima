# -*- coding: utf-8 -*-
"""
Константы доменной области и базовые эмпирические наборы данных.
Соответствуют материалам монографии ВГЛТУ (Воронеж, 2025).
"""

from typing import Final
from forest_optima.domain.models import ForestDistrict, ForestEnterprise, CriterionWeights

# Экспертные веса по умолчанию (Монография, стр. 130, табл. 3.3)
DEFAULT_WEIGHTS: Final[CriterionWeights] = CriterionWeights(
    stock=0.50,
    area=0.20,
    roads=0.30,
)

# Пороговые значения интегральной устойчивости арендаторов (шкала 0..15)
HIGH_SUSTAINABILITY_THRESHOLD: Final[float] = 11.0
MEDIUM_SUSTAINABILITY_THRESHOLD: Final[float] = 6.0
HARMONY_ZONE_THRESHOLD: Final[float] = 14.0

# 23 лесничества Воронежской области (Монография ВГЛТУ, Табл. 3.1 и 3.4)
DEFAULT_FORESTRY_DATA: Final[list[ForestDistrict]] = [
    ForestDistrict("Теллермановское", 6546.2, 40549.7, 415.7),
    ForestDistrict("Воронежское", 5124.1, 27165.0, 142.8),
    ForestDistrict("Бутурлиновское", 4965.4, 24146.0, 40.1),
    ForestDistrict("Острогожское", 4673.6, 26463.0, 24.5),
    ForestDistrict("Бобровское", 3946.9, 26113.0, 62.2),
    ForestDistrict("Воронцовское", 3805.2, 15913.0, 15.9),
    ForestDistrict("Калачеевское", 3276.8, 27213.6, 70.1),
    ForestDistrict("Аннинское", 3253.6, 20235.0, 65.6),
    ForestDistrict("Савальское", 2543.4, 18499.0, 14.7),
    ForestDistrict("Павловское", 2417.4, 74675.0, 113.5),
    ForestDistrict("Давыдовское", 1850.0, 31776.0, 35.2),
    ForestDistrict("Новоусманское", 1620.0, 22799.0, 8.4),
    ForestDistrict("Семилукское", 1450.0, 18302.0, 81.4),
    ForestDistrict("Новохоперское", 1380.0, 17041.0, 2.5),
    ForestDistrict("Песковское", 1290.0, 16419.0, 24.3),
    ForestDistrict("Хреновское", 1150.0, 14184.0, 77.5),
    ForestDistrict("Пригородное", 980.0, 12239.0, 12.0),
    ForestDistrict("Россошанское", 840.0, 10485.0, 2.9),
    ForestDistrict("Сомовское", 750.0, 9316.2, 11.6),
    ForestDistrict("Богучарское", 620.0, 7332.0, 10.1),
    ForestDistrict("Кантемировское", 510.0, 6332.0, 1.1),
    ForestDistrict("Эртильское", 420.0, 3216.0, 16.0),
    ForestDistrict("Донское", 310.0, 2717.0, 1.0),
]

# 7 арендаторов лесного фонда Воронежской области (Монография ВГЛТУ, Приложение А и Табл. 3.6)
DEFAULT_ENTERPRISES_DATA: Final[list[ForestEnterprise]] = [
    ForestEnterprise("ООО Фирма «Шипов лес»", 5.0, 5.0, 5.0),
    ForestEnterprise("ООО «Бобровский лес»", 5.0, 5.0, 4.0),
    ForestEnterprise("ООО «Бутурлиновский лесхоз»", 4.0, 4.0, 3.0),
    ForestEnterprise("ООО «ВоронежПромСтройЛес»", 4.0, 3.0, 2.5),
    ForestEnterprise("ООО «Орион»", 3.0, 3.0, 2.0),
    ForestEnterprise("ООО «Гранд-Галант»", 3.0, 2.0, 2.0),
    ForestEnterprise("ООО Предприятие «Эко-Интекс»", 2.0, 2.0, 1.0),
]
