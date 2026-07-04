#!/usr/bin/env python3
"""Namuna ma'lumotlar yuklash skripti."""

import asyncio

from app.database import async_session, init_db
from app.models.device import Device
from app.models.parent import Parent, StudentParent
from app.models.school import School
from app.models.student import Student


async def seed() -> None:
    await init_db()

    async with async_session() as session:
        school = School(name="15-sonli maktab", address="Toshkent sh.")
        session.add(school)
        await session.flush()

        students = [
            Student(
                school_id=school.id,
                first_name="Ali",
                last_name="Karimov",
                class_name="5-A",
                card_id="CARD001",
            ),
            Student(
                school_id=school.id,
                first_name="Dilnoza",
                last_name="Rahimova",
                class_name="7-B",
                card_id="CARD002",
            ),
        ]
        session.add_all(students)
        await session.flush()

        parents = [
            Parent(full_name="Karim Karimov", phone="+998901234567"),
            Parent(full_name="Malika Rahimova", phone="+998907654321"),
        ]
        session.add_all(parents)
        await session.flush()

        session.add_all(
            [
                StudentParent(student_id=students[0].id, parent_id=parents[0].id, relation="ota"),
                StudentParent(student_id=students[1].id, parent_id=parents[1].id, relation="ona"),
            ]
        )

        session.add_all(
            [
                Device(
                    school_id=school.id,
                    device_code="GATE_IN_01",
                    name="Asosiy kirish turniketi",
                    location="1-qavat, asosiy eshik",
                    direction="in",
                ),
                Device(
                    school_id=school.id,
                    device_code="GATE_OUT_01",
                    name="Asosiy chiqish turniketi",
                    location="1-qavat, asosiy eshik",
                    direction="out",
                ),
            ]
        )

        await session.commit()

    print("✅ Namuna ma'lumotlar yuklandi!")
    print("   Maktab: 15-sonli maktab")
    print("   O'quvchilar: CARD001 (Ali), CARD002 (Dilnoza)")
    print("   Ota-onalar: ID=1 (Karim), ID=2 (Malika)")
    print("   Turniketlar: GATE_IN_01, GATE_OUT_01")


if __name__ == "__main__":
    asyncio.run(seed())
