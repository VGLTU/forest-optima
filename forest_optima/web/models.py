# -*- coding: utf-8 -*-
"""
Pydantic-схемы валидации данных веб-интерфейса и API программного комплекса «Лес-Оптима».
Поддерживает стандарт Pydantic v2.
"""

from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field, field_validator


class DistrictInputItem(BaseModel):
    id: int | str = Field(..., description="Уникальный идентификатор лесничества в таблице")
    name: str = Field(..., min_length=1, max_length=200, description="Наименование лесничества")
    stock: float = Field(..., ge=0.0, description="Общий запас древесины, тыс. м3")
    area: float = Field(..., ge=0.0, description="Разрешенная площадь заготовки, га")
    roads: float = Field(..., ge=0.0, description="Протяженность лесных дорог, км")


class EnterpriseInputItem(BaseModel):
    id: int | str = Field(..., description="Уникальный идентификатор предприятия в таблице")
    name: str = Field(..., min_length=1, max_length=200, description="Наименование предприятия-арендатора")
    econ: float = Field(..., ge=0.0, le=5.0, description="Экономическая устойчивость (0-5)")
    ecol: float = Field(..., ge=0.0, le=5.0, description="Экологическая ответственность (0-5)")
    soc: float = Field(..., ge=0.0, le=5.0, description="Социальная отдача (0-5)")


class WeightsInput(BaseModel):
    stock: float = Field(default=0.50, ge=0.0, description="Вес запаса древесины")
    area: float = Field(default=0.20, ge=0.0, description="Вес площади заготовки")
    roads: float = Field(default=0.30, ge=0.0, description="Вес лесных дорог")

    @field_validator("roads")
    @classmethod
    def validate_sum_positive(cls, v: float, values: Any) -> float:
        data = values.data if hasattr(values, "data") else values
        stock = data.get("stock", 0.5)
        area = data.get("area", 0.2)
        if (stock + area + v) <= 0:
            raise ValueError("Сумма весовых коэффициентов должна быть строго больше нуля.")
        return v


class WorkspaceData(BaseModel):
    districts: list[DistrictInputItem] = Field(default_factory=list)
    enterprises: list[EnterpriseInputItem] = Field(default_factory=list)
    weights: WeightsInput = Field(default_factory=WeightsInput)


class WorkspaceSaveRequest(BaseModel):
    name: str = Field(default="Сценарий моделирования", max_length=255)
    data: dict[str, Any] = Field(..., description="Полный слепок состояния калькулятора")
    owner_id: str = Field(default="", description="Идентификатор пользователя-владельца")


class WorkspaceSummary(BaseModel):
    uid: str
    name: str
    created_at: str
    updated_at: str


class WorkspaceResponse(BaseModel):
    uid: str
    name: str
    data: dict[str, Any]
    owner_id: str = ""
    created_at: str
    updated_at: str


class CalculateRequest(BaseModel):
    districts: list[DistrictInputItem]
    enterprises: list[EnterpriseInputItem]
    weights: WeightsInput = Field(default_factory=WeightsInput)
