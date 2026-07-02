#!/usr/bin/env python3
"""O'quvchilarni qo'shish uchun oddiy CLI skript."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal, init_db
from app.models import Student
from app.services.attendance import generate_registration_code


def add_student(full_name: str, class_name: str, card_id: str, code: str | None = None) -> None:
    init_db()
    db = SessionLocal()
    try:
        if db.query(Student).filter(Student.card_id == card_id).first():
            print(f"Xato: karta {card_id} allaqachon mavjud")
            sys.exit(1)

        reg_code = (code or generate_registration_code()).upper()
        student = Student(
            full_name=full_name,
            class_name=class_name,
            card_id=card_id,
            registration_code=reg_code,
        )
        db.add(student)
        db.commit()
        print(f"✅ Qo'shildi: {full_name} ({class_name})")
        print(f"   Karta ID: {card_id}")
        print(f"   Ro'yxatdan o'tish kodi: {reg_code}")
    finally:
        db.close()


def list_students() -> None:
    init_db()
    db = SessionLocal()
    try:
        students = db.query(Student).order_by(Student.class_name, Student.full_name).all()
        if not students:
            print("O'quvchilar yo'q.")
            return
        print(f"{'ID':<5} {'Ism':<25} {'Sinf':<8} {'Karta':<15} {'Kod':<10}")
        print("-" * 65)
        for s in students:
            print(f"{s.id:<5} {s.full_name:<25} {s.class_name:<8} {s.card_id:<15} {s.registration_code:<10}")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="O'quvchilarni boshqarish")
    sub = parser.add_subparsers(dest="command")

    add_cmd = sub.add_parser("add", help="O'quvchi qo'shish")
    add_cmd.add_argument("full_name")
    add_cmd.add_argument("class_name")
    add_cmd.add_argument("card_id")
    add_cmd.add_argument("--code", default=None)

    sub.add_parser("list", help="O'quvchilar ro'yxati")

    args = parser.parse_args()
    if args.command == "add":
        add_student(args.full_name, args.class_name, args.card_id, args.code)
    elif args.command == "list":
        list_students()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
