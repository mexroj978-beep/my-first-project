"""Namuna ma'lumotlar."""
import asyncio
from app.database import SessionLocal, init_db
from app.models.device import Device
from app.models.parent import Parent, StudentParent
from app.models.school import School
from app.models.student import Student


async def main():
    await init_db()
    async with SessionLocal() as db:
        school = School(name="15-sonli maktab", address="Toshkent")
        db.add(school)
        await db.flush()
        s1 = Student(school_id=school.id, first_name="Ali", last_name="Karimov", class_name="5-A", card_id="001")
        s2 = Student(school_id=school.id, first_name="Dilnoza", last_name="Rahimova", class_name="7-B", card_id="002")
        db.add_all([s1, s2])
        await db.flush()
        p1 = Parent(full_name="Karim Karimov", phone="+998901234567")
        db.add(p1)
        await db.flush()
        db.add(StudentParent(student_id=s1.id, parent_id=p1.id))
        db.add_all([
            Device(school_id=school.id, device_code="GATE_IN_01", name="Kirish", location="1-qavat", direction="in"),
            Device(school_id=school.id, device_code="GATE_OUT_01", name="Chiqish", location="1-qavat", direction="out"),
        ])
        await db.commit()
    print("✅ Namuna ma'lumotlar yuklandi!")
    print("   O'quvchi: Ali (karta 001), Parent ID=1")
    print("   Bot: /register 1")


if __name__ == "__main__":
    asyncio.run(main())
