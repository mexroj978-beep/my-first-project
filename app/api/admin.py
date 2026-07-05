from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.device import Device
from app.models.parent import Parent, StudentParent
from app.models.school import School
from app.models.settings import AppSettings
from app.models.student import Student
from app.models.attendance import AttendanceEvent
from app.schemas import *
from app.services.subscription import SubscriptionService

router = APIRouter(prefix="/api", tags=["Admin"])


def admin(x: str = Header(..., alias="X-Admin-Key")):
    if x != settings.admin_api_key:
        raise HTTPException(401, "Noto'g'ri kalit")


# ---- MAKTAB ----
@router.get("/schools", response_model=list[SchoolOut], dependencies=[Depends(admin)])
async def schools(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(School).order_by(School.id))
    return list(r.scalars().all())


@router.post("/schools", response_model=SchoolOut, dependencies=[Depends(admin)])
async def create_school(d: SchoolCreate, db: AsyncSession = Depends(get_db)):
    s = School(**d.model_dump())
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


# ---- O'QUVCHI ----
@router.get("/students", response_model=list[StudentOut], dependencies=[Depends(admin)])
async def students(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Student).order_by(Student.id))
    return list(r.scalars().all())


@router.post("/students", response_model=StudentOut, dependencies=[Depends(admin)])
async def create_student(d: StudentCreate, db: AsyncSession = Depends(get_db)):
    if not await db.get(School, d.school_id):
        raise HTTPException(404, "Maktab topilmadi")
    ex = await db.execute(select(Student).where(Student.card_id == d.card_id))
    if ex.scalar_one_or_none():
        raise HTTPException(400, "Karta mavjud")
    s = Student(**d.model_dump())
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


@router.put("/students/{sid}", response_model=StudentOut, dependencies=[Depends(admin)])
async def update_student(sid: int, d: StudentUpdate, db: AsyncSession = Depends(get_db)):
    s = await db.get(Student, sid)
    if not s:
        raise HTTPException(404, "Topilmadi")
    for k, v in d.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    await db.commit()
    await db.refresh(s)
    return s


@router.delete("/students/{sid}", dependencies=[Depends(admin)])
async def delete_student(sid: int, db: AsyncSession = Depends(get_db)):
    s = await db.get(Student, sid)
    if not s:
        raise HTTPException(404, "Topilmadi")
    for l in (await db.execute(select(StudentParent).where(StudentParent.student_id == sid))).scalars():
        await db.delete(l)
    await db.delete(s)
    await db.commit()
    return {"ok": True}


# ---- OTA-ONA ----
@router.get("/parents", response_model=list[ParentOut], dependencies=[Depends(admin)])
async def parents(db: AsyncSession = Depends(get_db)):
    cfg = await SubscriptionService.get_settings(db)
    r = await db.execute(select(Parent).order_by(Parent.id))
    out = []
    for p in r.scalars().all():
        out.append(ParentOut(
            id=p.id, full_name=p.full_name, phone=p.phone,
            telegram_chat_id=p.telegram_chat_id, is_active=p.is_active,
            subscription_status=SubscriptionService.status(p, cfg)["label"],
        ))
    return out


@router.post("/parents", response_model=ParentOut, dependencies=[Depends(admin)])
async def create_parent(d: ParentCreate, db: AsyncSession = Depends(get_db)):
    p = Parent(full_name=d.full_name, phone=d.phone)
    db.add(p)
    await db.flush()
    for sid in d.student_ids:
        if await db.get(Student, sid):
            db.add(StudentParent(student_id=sid, parent_id=p.id))
    await db.commit()
    await db.refresh(p)
    cfg = await SubscriptionService.get_settings(db)
    return ParentOut(id=p.id, full_name=p.full_name, phone=p.phone,
                     telegram_chat_id=p.telegram_chat_id, is_active=p.is_active,
                     subscription_status=SubscriptionService.status(p, cfg)["label"])


@router.put("/parents/{pid}", response_model=ParentOut, dependencies=[Depends(admin)])
async def update_parent(pid: int, d: ParentUpdate, db: AsyncSession = Depends(get_db)):
    p = await db.get(Parent, pid)
    if not p:
        raise HTTPException(404, "Topilmadi")
    data = d.model_dump(exclude_unset=True)
    ids = data.pop("student_ids", None)
    for k, v in data.items():
        setattr(p, k, v)
    if ids is not None:
        for l in (await db.execute(select(StudentParent).where(StudentParent.parent_id == pid))).scalars():
            await db.delete(l)
        for sid in ids:
            if await db.get(Student, sid):
                db.add(StudentParent(student_id=sid, parent_id=pid))
    await db.commit()
    await db.refresh(p)
    cfg = await SubscriptionService.get_settings(db)
    return ParentOut(id=p.id, full_name=p.full_name, phone=p.phone,
                     telegram_chat_id=p.telegram_chat_id, is_active=p.is_active,
                     subscription_status=SubscriptionService.status(p, cfg)["label"])


@router.delete("/parents/{pid}", dependencies=[Depends(admin)])
async def delete_parent(pid: int, db: AsyncSession = Depends(get_db)):
    p = await db.get(Parent, pid)
    if not p:
        raise HTTPException(404, "Topilmadi")
    for l in (await db.execute(select(StudentParent).where(StudentParent.parent_id == pid))).scalars():
        await db.delete(l)
    await db.delete(p)
    await db.commit()
    return {"ok": True}


@router.post("/parents/{pid}/subscribe", dependencies=[Depends(admin)])
async def activate_sub(pid: int, d: ActivateSub, db: AsyncSession = Depends(get_db)):
    p = await db.get(Parent, pid)
    if not p:
        raise HTTPException(404, "Topilmadi")
    cfg = await SubscriptionService.get_settings(db)
    await SubscriptionService.activate(db, p, cfg, d.months)
    return {"ok": True, "status": SubscriptionService.status(p, cfg)["label"]}


# ---- TURNIKET ----
@router.get("/devices", response_model=list[DeviceOut], dependencies=[Depends(admin)])
async def devices(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Device).order_by(Device.id))
    return list(r.scalars().all())


@router.post("/devices", response_model=DeviceOut, dependencies=[Depends(admin)])
async def create_device(d: DeviceCreate, db: AsyncSession = Depends(get_db)):
    data = d.model_dump()
    data["direction"] = d.direction.value
    dev = Device(**data)
    db.add(dev)
    await db.commit()
    await db.refresh(dev)
    return dev


# ---- DAVOMAT ----
@router.get("/attendance", response_model=list[AttendanceOut], dependencies=[Depends(admin)])
async def attendance(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(AttendanceEvent).order_by(AttendanceEvent.event_time.desc()).limit(100))
    return list(r.scalars().all())


# ---- OBUNA SOZLAMALARI ----
@router.get("/settings", response_model=SettingsOut, dependencies=[Depends(admin)])
async def get_settings(db: AsyncSession = Depends(get_db)):
    return await SubscriptionService.get_settings(db)


@router.put("/settings", response_model=SettingsOut, dependencies=[Depends(admin)])
async def update_settings(d: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    s = await SubscriptionService.get_settings(db)
    for k, v in d.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    await db.commit()
    await db.refresh(s)
    return s
