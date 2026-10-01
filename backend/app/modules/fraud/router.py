"""/fraud/* endpoints (spec §4.7 S28–S31, §7.4)."""

import uuid

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.rate_limit import rate_limit
from app.core.security import get_current_user
from app.modules.fraud import service
from app.modules.fraud.schemas import AnalyzeTextIn, FraudCheckOut, FraudCheckPage, Language, ReportOut, SourceApp
from app.modules.users.models import User

router = APIRouter(prefix="/fraud", tags=["fraud"])


@router.post(
    "/analyze/text", response_model=FraudCheckOut, status_code=201,
    dependencies=[Depends(rate_limit("fraud_text", 20, 3600))],
)
async def analyze_text(body: AnalyzeTextIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await service.analyze_text(
        session, user, body.text, source_app=body.source_app, input_type=body.input_type, language=body.language
    )


@router.post(
    "/analyze/image", response_model=FraudCheckOut, status_code=201,
    dependencies=[Depends(rate_limit("fraud_image", 10, 3600))],
)
async def analyze_image(
    image: UploadFile = File(...),
    source_app: SourceApp = Form("whatsapp"),
    language: Language | None = Form(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    data = await image.read(service.IMAGE_MAX_BYTES + 1)
    await image.close()
    return await service.analyze_image(session, user, data, image.content_type, source_app=source_app,
                                       language=language)


@router.get("/checks", response_model=FraudCheckPage)
async def list_checks(
    limit: int = Query(default=30, ge=1, le=100), cursor: str | None = None,
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db),
):
    return await service.list_checks(session, user, limit, cursor)


@router.get("/checks/{check_id}", response_model=FraudCheckOut)
async def get_check(check_id: uuid.UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await service.get_check(session, user, check_id)


@router.delete("/checks/{check_id}", status_code=204)
async def delete_check(
    check_id: uuid.UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> Response:
    await service.delete_check(session, user, check_id)
    return Response(status_code=204)


@router.post("/checks/{check_id}/report", response_model=ReportOut)
async def report_check(check_id: uuid.UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return ReportOut(reported=await service.report_check(session, user, check_id))
