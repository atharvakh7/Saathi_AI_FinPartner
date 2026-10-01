"""/admin/* endpoints (spec F19, §7.2, §7.4). Every route requires role 'admin' (403 otherwise).

Admins are made by logging in with ADMIN_PHONE_E164 (or the seed). No mobile screens in the MVP.
"""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import require_role
from app.modules.admin import service
from app.modules.admin.schemas import (
    FraudPatternIn,
    FraudPatternOut,
    GlossaryIn,
    GlossaryOut,
    GlossaryTranslationIn,
    LessonIn,
    LessonOut,
    SchemeAdminOut,
    SchemeIn,
    SchemeTranslationIn,
    TranslationOut,
    VideoIn,
    VideoUploadOut,
)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_role("admin"))])

TranslationLang = Literal["hi", "mr", "ta"]


# --- Schemes -----------------------------------------------------------------------

@router.post("/schemes", response_model=SchemeAdminOut, status_code=201)
async def create_scheme(body: SchemeIn, session: AsyncSession = Depends(get_db)):
    return await service.create_scheme(session, body)


@router.put("/schemes/{scheme_id}", response_model=SchemeAdminOut)
async def replace_scheme(scheme_id: uuid.UUID, body: SchemeIn, session: AsyncSession = Depends(get_db)):
    return await service.replace_scheme(session, scheme_id, body)


@router.delete("/schemes/{scheme_id}", status_code=204)
async def deactivate_scheme(scheme_id: uuid.UUID, session: AsyncSession = Depends(get_db)) -> Response:
    await service.deactivate_scheme(session, scheme_id)
    return Response(status_code=204)


@router.put("/schemes/{scheme_id}/translations/{lang}", response_model=TranslationOut)
async def set_scheme_translation(scheme_id: uuid.UUID, lang: TranslationLang, body: SchemeTranslationIn,
                                 session: AsyncSession = Depends(get_db)):
    return await service.set_scheme_translation(session, scheme_id, lang, body)


# --- Glossary ----------------------------------------------------------------------

@router.post("/glossary", response_model=GlossaryOut, status_code=201)
async def create_term(body: GlossaryIn, session: AsyncSession = Depends(get_db)):
    return await service.create_term(session, body)


@router.put("/glossary/{term_id}", response_model=GlossaryOut)
async def update_term(term_id: uuid.UUID, body: GlossaryIn, session: AsyncSession = Depends(get_db)):
    return await service.update_term(session, term_id, body)


@router.put("/glossary/{term_id}/translations/{lang}", response_model=TranslationOut)
async def set_term_translation(term_id: uuid.UUID, lang: TranslationLang, body: GlossaryTranslationIn,
                               session: AsyncSession = Depends(get_db)):
    return await service.set_term_translation(session, term_id, lang, body)


# --- Lessons & videos --------------------------------------------------------------

@router.post("/lessons", response_model=LessonOut, status_code=201)
async def create_lesson(body: LessonIn, session: AsyncSession = Depends(get_db)):
    return await service.create_lesson(session, body)


@router.put("/lessons/{lesson_id}", response_model=LessonOut)
async def update_lesson(lesson_id: uuid.UUID, body: LessonIn, session: AsyncSession = Depends(get_db)):
    return await service.update_lesson(session, lesson_id, body)


@router.post("/videos", response_model=VideoUploadOut, status_code=201)
async def register_video(body: VideoIn, session: AsyncSession = Depends(get_db)):
    return await service.register_video(session, body)


# --- Fraud patterns ----------------------------------------------------------------

@router.get("/fraud-patterns", response_model=list[FraudPatternOut])
async def list_patterns(session: AsyncSession = Depends(get_db)):
    return await service.list_patterns(session)


@router.post("/fraud-patterns", response_model=FraudPatternOut, status_code=201)
async def create_pattern(body: FraudPatternIn, session: AsyncSession = Depends(get_db)):
    return await service.create_pattern(session, body)


@router.put("/fraud-patterns/{pattern_id}", response_model=FraudPatternOut)
async def update_pattern(pattern_id: uuid.UUID, body: FraudPatternIn, session: AsyncSession = Depends(get_db)):
    return await service.update_pattern(session, pattern_id, body)
