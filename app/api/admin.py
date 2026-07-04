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
from app.models.student import Student
from app.schemas import (
    AttendanceResponse,
    DeviceCreate,
    DeviceResponse,
    LinkParentStudent,
    ParentCreate,
    ParentResponse,
    SchoolCreate,
    SchoolResponse,
    StudentCreate,
    StudentResponse,
)

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
async def list_parents(db: AsyncSession = Depends(get_db)) -> list[Parent]:
    result = await db.execute(select(Parent).order_by(Parent.id))
    return list(result.scalars().all())


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
