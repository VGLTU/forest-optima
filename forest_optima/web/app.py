# -*- coding: utf-8 -*-
"""
Основное ASGI-приложение FastAPI для программного комплекса «Лес-Оптима».
Предоставляет REST API и веб-интерфейс с поддержкой изолированных рабочих пространств.
"""

from __future__ import annotations
import io
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse

from forest_optima.domain.models import (
    CriterionWeights,
    ForestDistrict,
    ForestEnterprise,
)
from forest_optima.services.euler_venn import evaluate_enterprises
from forest_optima.services.mcda import evaluate_districts
from forest_optima.storage.csv_exporter import export_to_csv
from forest_optima.storage.excel_exporter import export_to_excel
from forest_optima.web.database import (
    delete_workspace,
    get_workspace,
    init_db,
    list_workspaces,
    upsert_workspace,
)
from forest_optima.web.defaults import DEFAULT_WORKSPACE_DATA
from forest_optima.web.models import (
    CalculateRequest,
    WorkspaceResponse,
    WorkspaceSaveRequest,
    WorkspaceSummary,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
HTML_FILE_PATH = BASE_DIR / "Калькулятор_ЛесОптима.html"
DATA_DIR = Path(os.getenv("FOREST_OPTIMA_DATA_DIR", str(BASE_DIR / "data")))
DB_PATH = DATA_DIR / "forest_optima.db"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Инициализация БД
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    init_db(DB_PATH)
    yield
    # Shutdown


app = FastAPI(
    title="Лес-Оптима API",
    version="1.0.0",
    description="Научно-практический комплекс многокритериальной оценки лесного фонда (ВГЛТУ)",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Отдача основного одностраничного веб-интерфейса калькулятора."""
    if not HTML_FILE_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Файл веб-интерфейса Калькулятор_ЛесОптима.html не найден на сервере.",
        )
    return HTMLResponse(content=HTML_FILE_PATH.read_text(encoding="utf-8"))


@app.get("/api/health")
async def health_check():
    """Проверка доступности и работоспособности сервиса."""
    return {
        "status": "healthy",
        "service": "forest-optima",
        "version": "1.0.0",
        "database": str(DB_PATH),
    }


@app.get("/api/workspaces", response_model=list[WorkspaceSummary])
async def get_all_workspaces(limit: int = 50):
    """Список последних сохраненных рабочих пространств."""
    rows = list_workspaces(DB_PATH, limit=limit)
    return [WorkspaceSummary(**r) for r in rows]


@app.get("/api/workspace/{uid}", response_model=WorkspaceResponse)
async def get_single_workspace(uid: str):
    """
    Получение сохраненного состояния по ID рабочего пространства.
    Если запись не существует, возвращается шаблонное состояние по умолчанию.
    """
    cleaned_uid = uid.strip()
    if not cleaned_uid:
        raise HTTPException(status_code=400, detail="Идентификатор не может быть пустым.")

    record = get_workspace(DB_PATH, cleaned_uid)
    if record:
        return WorkspaceResponse(**record)

    # Авто-инициализация нового рабочего пространства дефолтными данными
    new_record = upsert_workspace(
        db_path=DB_PATH,
        uid=cleaned_uid,
        name=f"Расчет #{cleaned_uid[:8]}",
        data=DEFAULT_WORKSPACE_DATA,
    )
    return WorkspaceResponse(**new_record)


@app.post("/api/workspace/{uid}", response_model=WorkspaceResponse)
async def save_single_workspace(uid: str, payload: WorkspaceSaveRequest):
    """
    Сохранение / автосинхронизация состояния рабочего пространства пользователя.
    """
    cleaned_uid = uid.strip()
    if not cleaned_uid:
        raise HTTPException(status_code=400, detail="Идентификатор не может быть пустым.")

    name = payload.name.strip() if payload.name else f"Расчет #{cleaned_uid[:8]}"
    record = upsert_workspace(
        db_path=DB_PATH,
        uid=cleaned_uid,
        name=name,
        data=payload.data,
    )
    return WorkspaceResponse(**record)


@app.delete("/api/workspace/{uid}")
async def remove_workspace(uid: str):
    """Удаление рабочего пространства."""
    cleaned_uid = uid.strip()
    success = delete_workspace(DB_PATH, cleaned_uid)
    if not success:
        raise HTTPException(status_code=404, detail="Рабочее пространство не найдено.")
    return {"status": "deleted", "uid": cleaned_uid}


@app.post("/api/calculate")
async def calculate_scenario(req: CalculateRequest):
    """
    Серверная проверка и расчет на основе строгих математических моделей:
    1. MCDA нормализация (WSM + TOPSIS) лесничеств.
    2. Триединая модель Эйлера-Венна для предприятий.
    """
    try:
        weights = CriterionWeights(
            stock=req.weights.stock,
            area=req.weights.area,
            roads=req.weights.roads,
        )

        districts = [
            ForestDistrict(
                name=d.name,
                timber_stock_k_m3=d.stock,
                allowed_area_ha=d.area,
                road_length_km=d.roads,
            )
            for d in req.districts
        ]

        enterprises = [
            ForestEnterprise(
                name=e.name,
                economic_score=e.econ,
                ecological_score=e.ecol,
                social_score=e.soc,
            )
            for e in req.enterprises
        ]

        dist_eval = evaluate_districts(districts, weights) if districts else []
        ent_eval = evaluate_enterprises(enterprises) if enterprises else []

        return {
            "districts": [
                {
                    "name": item.district.name,
                    "wsm_score": round(item.wsm_score, 4),
                    "topsis_score": round(item.topsis_score, 4),
                    "raw_score": round(item.raw_score, 2),
                    "raw_rank": item.raw_rank,
                    "optimal_rank": item.optimal_rank,
                    "rank_shift": item.rank_shift,
                }
                for item in dist_eval
            ],
            "enterprises": [
                {
                    "name": item.enterprise.name,
                    "total_score": item.total_score,
                    "sustainability_level": item.sustainability_level,
                    "euler_venn_zone": item.euler_venn_zone,
                }
                for item in ent_eval
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/export/excel")
async def export_excel_report(req: CalculateRequest):
    """
    Серверная генерация форматированного аналитического отчета Excel (.xlsx).
    """
    try:
        weights = CriterionWeights(
            stock=req.weights.stock,
            area=req.weights.area,
            roads=req.weights.roads,
        )

        districts = [
            ForestDistrict(
                name=d.name,
                timber_stock_k_m3=d.stock,
                allowed_area_ha=d.area,
                road_length_km=d.roads,
            )
            for d in req.districts
        ]

        enterprises = [
            ForestEnterprise(
                name=e.name,
                economic_score=e.econ,
                ecological_score=e.ecol,
                social_score=e.soc,
            )
            for e in req.enterprises
        ]

        dist_eval = evaluate_districts(districts, weights)
        ent_eval = evaluate_enterprises(enterprises)

        tmp_file = DATA_DIR / f"temp_report_{os.getpid()}.xlsx"
        export_to_excel(dist_eval, ent_eval, tmp_file)

        content = tmp_file.read_bytes()
        tmp_file.unlink(missing_ok=True)

        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=Forest_Optima_Analysis.xlsx"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/export/csv")
async def export_csv_report(req: CalculateRequest):
    """
    Серверная генерация форматированного аналитического отчета CSV (UTF-8 с BOM).
    """
    try:
        weights = CriterionWeights(
            stock=req.weights.stock,
            area=req.weights.area,
            roads=req.weights.roads,
        )

        districts = [
            ForestDistrict(
                name=d.name,
                timber_stock_k_m3=d.stock,
                allowed_area_ha=d.area,
                road_length_km=d.roads,
            )
            for d in req.districts
        ]

        enterprises = [
            ForestEnterprise(
                name=e.name,
                economic_score=e.econ,
                ecological_score=e.ecol,
                social_score=e.soc,
            )
            for e in req.enterprises
        ]

        dist_eval = evaluate_districts(districts, weights)
        ent_eval = evaluate_enterprises(enterprises)

        tmp_file = DATA_DIR / f"temp_report_{os.getpid()}.csv"
        export_to_csv(dist_eval, ent_eval, tmp_file)

        content = tmp_file.read_bytes()
        tmp_file.unlink(missing_ok=True)

        return StreamingResponse(
            io.BytesIO(content),
            media_type="text/csv; charset=utf-8-sig",
            headers={
                "Content-Disposition": "attachment; filename=Forest_Optima_Analysis.csv"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

