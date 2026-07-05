from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models.attendance import AttendanceEvent
from app.models.device import Device
from app.models.parent import Parent, StudentParent
from app.models.school import School
from app.models.settings import AppSettings
from app.models.student import Student
from app.schemas import (
    ActivateSubscription,
    AttendanceResponse,
    DeviceCreate,
    DeviceResponse,
    LinkParentStudent,
    ParentCreate,
    ParentResponse,
    ParentUpdate,
    SchoolCreate,
    SchoolResponse,
    StudentCreate,
    StudentResponse,
    StudentUpdate,
    SubscriptionSettingsResponse,
    SubscriptionSettingsUpdate,
)
from app.services.subscription import SubscriptionService

router = APIRouter(prefix="/api", tags=["Admin"])


def verify_admin_key(x_admin_key: str = Header(..., alias="X-Admin-Key")) -> None:
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Noto'g'ri admin kaliti")


@router.post("/schools", response_model=SchoolResponse, dependencies=[Depends(verify_admin_key)])
async def create_school(payload: SchoolCreate, db: AsyncSession = Depends(get_db)) -> School:
    school = School(name=payload.name, address=payload.address)
    db.add(school)
    await db.commit()
    await db.refresh(school)
    return school


@router.get("/schools", response_model=list[SchoolResponse], dependencies=[Depends(verify_admin_key)])
async def list_schools(db: AsyncSession = Depends(get_db)) -> list[School]:
    result = await db.execute(select(School).order_by(School.id))
    return list(result.scalars().all())


@router.post("/students", response_model=StudentResponse, dependencies=[Depends(verify_admin_key)])
async def create_student(payload: StudentCreate, db: AsyncSession = Depends(get_db)) -> Student:
    school = await db.get(School, payload.school_id)
    if not school:
        raise HTTPException(status_code=404, detail="Maktab topilmadi")

    existing = await db.execute(select(Student).where(Student.card_id == payload.card_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu karta allaqachon ro'yxatdan o'tgan")

    student = Student(**payload.model_dump())
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student


@router.get("/students", response_model=list[StudentResponse], dependencies=[Depends(verify_admin_key)])
async def list_students(db: AsyncSession = Depends(get_db)) -> list[Student]:
    result = await db.execute(select(Student).order_by(Student.id))
    return list(result.scalars().all())


@router.put("/students/{student_id}", response_model=StudentResponse, dependencies=[Depends(verify_admin_key)])
async def update_student(
    student_id: int, payload: StudentUpdate, db: AsyncSession = Depends(get_db)
) -> Student:
    student = await db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")

    data = payload.model_dump(exclude_unset=True)
    if "card_id" in data and data["card_id"] != student.card_id:
        existing = await db.execute(select(Student).where(Student.card_id == data["card_id"]))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Bu karta allaqachon mavjud")

    for key, value in data.items():
        setattr(student, key, value)
    await db.commit()
    await db.refresh(student)
    return student


@router.delete("/students/{student_id}", dependencies=[Depends(verify_admin_key)])
async def delete_student(student_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    student = await db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")

    links = await db.execute(select(StudentParent).where(StudentParent.student_id == student_id))
    for link in links.scalars().all():
        await db.delete(link)
    await db.delete(student)
    await db.commit()
    return {"success": True, "message": "O'quvchi o'chirildi"}


@router.post("/parents", response_model=ParentResponse, dependencies=[Depends(verify_admin_key)])
async def create_parent(payload: ParentCreate, db: AsyncSession = Depends(get_db)) -> Parent:
    parent = Parent(full_name=payload.full_name, phone=payload.phone)
    db.add(parent)
    await db.flush()

    for student_id in payload.student_ids:
        student = await db.get(Student, student_id)
        if student:
            db.add(StudentParent(student_id=student_id, parent_id=parent.id))

    await db.commit()
    await db.refresh(parent)
    return parent


@router.get("/parents", response_model=list[ParentResponse], dependencies=[Depends(verify_admin_key)])
async def list_parents(db: AsyncSession = Depends(get_db)) -> list[dict]:
    result = await db.execute(select(Parent).order_by(Parent.id))
    parents = list(result.scalars().all())
    settings = await SubscriptionService.get_settings(db)

    response = []
    for p in parents:
        status = SubscriptionService.get_status(p, settings)
        response.append(
            ParentResponse(
                id=p.id,
                full_name=p.full_name,
                phone=p.phone,
                telegram_chat_id=p.telegram_chat_id,
                is_active=p.is_active,
                bot_registered_at=p.bot_registered_at,
                subscription_until=p.subscription_until,
                subscription_status=status["label"],
            )
        )
    return response


@router.put("/parents/{parent_id}", response_model=ParentResponse, dependencies=[Depends(verify_admin_key)])
async def update_parent(
    parent_id: int, payload: ParentUpdate, db: AsyncSession = Depends(get_db)
) -> ParentResponse:
    parent = await db.get(Parent, parent_id)
    if not parent:
        raise HTTPException(status_code=404, detail="Ota-ona topilmadi")

    data = payload.model_dump(exclude_unset=True)
    student_ids = data.pop("student_ids", None)

    for key, value in data.items():
        setattr(parent, key, value)

    if student_ids is not None:
        existing = await db.execute(select(StudentParent).where(StudentParent.parent_id == parent_id))
        for link in existing.scalars().all():
            await db.delete(link)
        for sid in student_ids:
            if await db.get(Student, sid):
                db.add(StudentParent(student_id=sid, parent_id=parent_id))

    await db.commit()
    await db.refresh(parent)
    settings = await SubscriptionService.get_settings(db)
    status = SubscriptionService.get_status(parent, settings)
    return ParentResponse(
        id=parent.id,
        full_name=parent.full_name,
        phone=parent.phone,
        telegram_chat_id=parent.telegram_chat_id,
        is_active=parent.is_active,
        bot_registered_at=parent.bot_registered_at,
        subscription_until=parent.subscription_until,
        subscription_status=status["label"],
    )


@router.delete("/parents/{parent_id}", dependencies=[Depends(verify_admin_key)])
async def delete_parent(parent_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    parent = await db.get(Parent, parent_id)
    if not parent:
        raise HTTPException(status_code=404, detail="Ota-ona topilmadi")

    links = await db.execute(select(StudentParent).where(StudentParent.parent_id == parent_id))
    for link in links.scalars().all():
        await db.delete(link)
    await db.delete(parent)
    await db.commit()
    return {"success": True, "message": "Ota-ona o'chirildi"}


@router.post("/parents/{parent_id}/subscribe", dependencies=[Depends(verify_admin_key)])
async def activate_parent_subscription(
    parent_id: int,
    payload: ActivateSubscription,
    db: AsyncSession = Depends(get_db),
) -> dict:
    parent = await db.get(Parent, parent_id)
    if not parent:
        raise HTTPException(status_code=404, detail="Ota-ona topilmadi")

    settings = await SubscriptionService.get_settings(db)
    await SubscriptionService.activate_subscription(db, parent, settings, payload.months)
    status = SubscriptionService.get_status(parent, settings)
    return {"success": True, "message": f"Obuna faollashtirildi: {status['label']}"}


@router.get("/settings/subscription", response_model=SubscriptionSettingsResponse, dependencies=[Depends(verify_admin_key)])
async def get_subscription_settings(db: AsyncSession = Depends(get_db)) -> AppSettings:
    return await SubscriptionService.get_settings(db)


@router.put("/settings/subscription", response_model=SubscriptionSettingsResponse, dependencies=[Depends(verify_admin_key)])
async def update_subscription_settings(
    payload: SubscriptionSettingsUpdate, db: AsyncSession = Depends(get_db)
) -> AppSettings:
    settings = await SubscriptionService.get_settings(db)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, key, value)
    await db.commit()
    await db.refresh(settings)
    return settings


@router.post("/parents/link", dependencies=[Depends(verify_admin_key)])
async def link_parent_student(payload: LinkParentStudent, db: AsyncSession = Depends(get_db)) -> dict:
    parent = await db.get(Parent, payload.parent_id)
    student = await db.get(Student, payload.student_id)
    if not parent or not student:
        raise HTTPException(status_code=404, detail="Ota-ona yoki o'quvchi topilmadi")

    existing = await db.execute(
        select(StudentParent).where(
            StudentParent.parent_id == payload.parent_id,
            StudentParent.student_id == payload.student_id,
        )
    )
    if existing.scalar_one_or_none():
        return {"success": True, "message": "Allaqachon bog'langan"}

    db.add(
        StudentParent(
            parent_id=payload.parent_id,
            student_id=payload.student_id,
            relation=payload.relation,
        )
    )
    await db.commit()
    return {"success": True, "message": "Muvaffaqiyatli bog'landi"}


@router.post("/devices", response_model=DeviceResponse, dependencies=[Depends(verify_admin_key)])
async def create_device(payload: DeviceCreate, db: AsyncSession = Depends(get_db)) -> Device:
    school = await db.get(School, payload.school_id)
    if not school:
        raise HTTPException(status_code=404, detail="Maktab topilmadi")

    device = Device(
        school_id=payload.school_id,
        device_code=payload.device_code,
        name=payload.name,
        location=payload.location,
        direction=payload.direction.value,
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


@router.get("/devices", response_model=list[DeviceResponse], dependencies=[Depends(verify_admin_key)])
async def list_devices(db: AsyncSession = Depends(get_db)) -> list[Device]:
    result = await db.execute(select(Device).order_by(Device.id))
    return list(result.scalars().all())


@router.get("/attendance", response_model=list[AttendanceResponse], dependencies=[Depends(verify_admin_key)])
async def list_attendance(db: AsyncSession = Depends(get_db)) -> list[AttendanceEvent]:
    result = await db.execute(select(AttendanceEvent).order_by(AttendanceEvent.event_time.desc()).limit(100))
    return list(result.scalars().all())


@router.get("/attendance/student/{student_id}", response_model=list[AttendanceResponse])
async def student_attendance(student_id: int, db: AsyncSession = Depends(get_db)) -> list[AttendanceEvent]:
    result = await db.execute(
        select(AttendanceEvent)
        .where(AttendanceEvent.student_id == student_id)
        .order_by(AttendanceEvent.event_time.desc())
        .limit(50)
    )
    return list(result.scalars().all())
