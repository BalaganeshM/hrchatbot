"""Seed the database with sample data for development."""
import asyncio
import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory, engine, Base
from app.models.user import User, UserRole
from app.models.department import Department
from app.core.security import hash_password


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        existing = await db.execute(select(User).limit(1))
        if existing.scalar_one_or_none():
            print("Database already has data, skipping seed.")
            return

        # Departments
        eng = Department(id=uuid.uuid4(), name="Engineering", description="Software engineering")
        hr = Department(id=uuid.uuid4(), name="Human Resources", description="HR department")
        sales = Department(id=uuid.uuid4(), name="Sales", description="Sales and marketing")
        finance = Department(id=uuid.uuid4(), name="Finance", description="Finance and accounting")
        design = Department(id=uuid.uuid4(), name="Design", description="UI/UX design")
        operations = Department(id=uuid.uuid4(), name="Operations", description="Operations and logistics")

        db.add_all([eng, hr, sales, finance, design, operations])
        await db.flush()

        # Admin / CEO
        admin = User(
            id=uuid.uuid4(),
            email="admin@scb.com",
            password_hash=hash_password("admin123"),
            first_name="System",
            last_name="Admin",
            role=UserRole.admin,
            position="Chief Technology Officer",
            department_id=eng.id,
            phone="+1-555-0100",
            hire_date=date(2020, 1, 15),
            salary=150000,
        )

        # CEO / Top-level
        ceo = User(
            id=uuid.uuid4(),
            email="john@scb.com",
            password_hash=hash_password("john123"),
            first_name="John",
            last_name="Doe",
            role=UserRole.admin,
            position="Chief Executive Officer",
            department_id=operations.id,
            phone="+1-555-0099",
            hire_date=date(2019, 6, 1),
            salary=200000,
        )

        # Managers (report to CEO)
        vp_eng = User(
            id=uuid.uuid4(),
            email="alice@scb.com",
            password_hash=hash_password("alice123"),
            first_name="Alice",
            last_name="Johnson",
            role=UserRole.manager,
            position="VP of Engineering",
            department_id=eng.id,
            manager_id=ceo.id,
            phone="+1-555-0101",
            hire_date=date(2020, 3, 10),
            salary=130000,
        )
        vp_hr = User(
            id=uuid.uuid4(),
            email="bob@scb.com",
            password_hash=hash_password("bob123"),
            first_name="Bob",
            last_name="Smith",
            role=UserRole.manager,
            position="VP of Human Resources",
            department_id=hr.id,
            manager_id=ceo.id,
            phone="+1-555-0102",
            hire_date=date(2020, 6, 20),
            salary=125000,
        )
        vp_sales = User(
            id=uuid.uuid4(),
            email="sarah@scb.com",
            password_hash=hash_password("sarah123"),
            first_name="Sarah",
            last_name="Connor",
            role=UserRole.manager,
            position="VP of Sales",
            department_id=sales.id,
            manager_id=ceo.id,
            phone="+1-555-0107",
            hire_date=date(2020, 9, 5),
            salary=128000,
        )
        vp_finance = User(
            id=uuid.uuid4(),
            email="michael@scb.com",
            password_hash=hash_password("michael123"),
            first_name="Michael",
            last_name="Scott",
            role=UserRole.manager,
            position="VP of Finance",
            department_id=finance.id,
            manager_id=ceo.id,
            phone="+1-555-0108",
            hire_date=date(2021, 1, 15),
            salary=127000,
        )

        # Engineering team (under Alice)
        emp1 = User(
            id=uuid.uuid4(),
            email="charlie@scb.com",
            password_hash=hash_password("charlie123"),
            first_name="Charlie",
            last_name="Brown",
            role=UserRole.employee,
            position="Senior Software Engineer",
            department_id=eng.id,
            manager_id=vp_eng.id,
            phone="+1-555-0103",
            hire_date=date(2022, 2, 1),
            salary=95000,
        )
        emp2 = User(
            id=uuid.uuid4(),
            email="diana@scb.com",
            password_hash=hash_password("diana123"),
            first_name="Diana",
            last_name="Prince",
            role=UserRole.employee,
            position="Frontend Developer",
            department_id=eng.id,
            manager_id=vp_eng.id,
            phone="+1-555-0104",
            hire_date=date(2022, 5, 15),
            salary=85000,
        )
        emp_eng3 = User(
            id=uuid.uuid4(),
            email="tony@scb.com",
            password_hash=hash_password("tony123"),
            first_name="Tony",
            last_name="Stark",
            role=UserRole.employee,
            position="DevOps Engineer",
            department_id=eng.id,
            manager_id=vp_eng.id,
            phone="+1-555-0110",
            hire_date=date(2022, 8, 20),
            salary=92000,
        )
        emp_eng4 = User(
            id=uuid.uuid4(),
            email="bruce@scb.com",
            password_hash=hash_password("bruce123"),
            first_name="Bruce",
            last_name="Wayne",
            role=UserRole.employee,
            position="Backend Developer",
            department_id=eng.id,
            manager_id=vp_eng.id,
            phone="+1-555-0111",
            hire_date=date(2023, 3, 10),
            salary=88000,
        )

        # HR team (under Bob)
        emp3 = User(
            id=uuid.uuid4(),
            email="eve@scb.com",
            password_hash=hash_password("eve123"),
            first_name="Eve",
            last_name="Adams",
            role=UserRole.employee,
            position="HR Coordinator",
            department_id=hr.id,
            manager_id=vp_hr.id,
            phone="+1-555-0105",
            hire_date=date(2023, 1, 10),
            salary=65000,
        )
        emp_hr2 = User(
            id=uuid.uuid4(),
            email="natasha@scb.com",
            password_hash=hash_password("natasha123"),
            first_name="Natasha",
            last_name="Romanoff",
            role=UserRole.employee,
            position="Talent Acquisition Specialist",
            department_id=hr.id,
            manager_id=vp_hr.id,
            phone="+1-555-0112",
            hire_date=date(2023, 6, 1),
            salary=70000,
        )
        emp_hr3 = User(
            id=uuid.uuid4(),
            email="clark@scb.com",
            password_hash=hash_password("clark123"),
            first_name="Clark",
            last_name="Kent",
            role=UserRole.employee,
            position="Benefits Administrator",
            department_id=hr.id,
            manager_id=vp_hr.id,
            phone="+1-555-0113",
            hire_date=date(2024, 2, 15),
            salary=62000,
        )

        # Sales team (under Sarah)
        emp4 = User(
            id=uuid.uuid4(),
            email="frank@scb.com",
            password_hash=hash_password("frank123"),
            first_name="Frank",
            last_name="Miller",
            role=UserRole.employee,
            position="Senior Sales Executive",
            department_id=sales.id,
            manager_id=vp_sales.id,
            phone="+1-555-0106",
            hire_date=date(2023, 4, 1),
            salary=82000,
        )
        emp_sales2 = User(
            id=uuid.uuid4(),
            email="lara@scb.com",
            password_hash=hash_password("lara123"),
            first_name="Lara",
            last_name="Croft",
            role=UserRole.employee,
            position="Sales Executive",
            department_id=sales.id,
            manager_id=vp_sales.id,
            phone="+1-555-0114",
            hire_date=date(2023, 9, 1),
            salary=75000,
        )
        emp_sales3 = User(
            id=uuid.uuid4(),
            email="peter@scb.com",
            password_hash=hash_password("peter123"),
            first_name="Peter",
            last_name="Parker",
            role=UserRole.employee,
            position="Sales Associate",
            department_id=sales.id,
            manager_id=vp_sales.id,
            phone="+1-555-0115",
            hire_date=date(2024, 1, 10),
            salary=55000,
        )

        # Finance team (under Michael)
        emp_fin1 = User(
            id=uuid.uuid4(),
            email="sam@scb.com",
            password_hash=hash_password("sam123"),
            first_name="Sam",
            last_name="Wilson",
            role=UserRole.employee,
            position="Financial Analyst",
            department_id=finance.id,
            manager_id=vp_finance.id,
            phone="+1-555-0116",
            hire_date=date(2022, 11, 1),
            salary=78000,
        )
        emp_fin2 = User(
            id=uuid.uuid4(),
            email="wanda@scb.com",
            password_hash=hash_password("wanda123"),
            first_name="Wanda",
            last_name="Maximoff",
            role=UserRole.employee,
            position="Accountant",
            department_id=finance.id,
            manager_id=vp_finance.id,
            phone="+1-555-0117",
            hire_date=date(2023, 8, 15),
            salary=72000,
        )

        # Second Engineering team (Platform team under Alice)
        plat_manager = User(
            id=uuid.uuid4(),
            email="steve@scb.com",
            password_hash=hash_password("steve123"),
            first_name="Steve",
            last_name="Rogers",
            role=UserRole.manager,
            position="Platform Engineering Manager",
            department_id=eng.id,
            manager_id=vp_eng.id,
            phone="+1-555-0118",
            hire_date=date(2021, 7, 1),
            salary=115000,
        )
        emp_plat1 = User(
            id=uuid.uuid4(),
            email="carol@scb.com",
            password_hash=hash_password("carol123"),
            first_name="Carol",
            last_name="Danvers",
            role=UserRole.employee,
            position="Senior Software Engineer",
            department_id=eng.id,
            manager_id=plat_manager.id,
            phone="+1-555-0119",
            hire_date=date(2022, 4, 10),
            salary=98000,
        )
        emp_plat_junior = User(
            id=uuid.uuid4(),
            email="hope@scb.com",
            password_hash=hash_password("hope123"),
            first_name="Hope",
            last_name="van Dyne",
            role=UserRole.employee,
            position="Junior Software Engineer",
            department_id=eng.id,
            manager_id=plat_manager.id,
            phone="+1-555-0123",
            hire_date=date(2024, 6, 15),
            salary=65000,
        )
        emp_plat2 = User(
            id=uuid.uuid4(),
            email="thor@scb.com",
            password_hash=hash_password("thor123"),
            first_name="Thor",
            last_name="Odinson",
            role=UserRole.employee,
            position="Software Engineer",
            department_id=eng.id,
            manager_id=plat_manager.id,
            phone="+1-555-0120",
            hire_date=date(2022, 10, 5),
            salary=82000,
        )
        emp_plat3 = User(
            id=uuid.uuid4(),
            email="scott@scb.com",
            password_hash=hash_password("scott123"),
            first_name="Scott",
            last_name="Lang",
            role=UserRole.employee,
            position="QA Engineer",
            department_id=eng.id,
            manager_id=plat_manager.id,
            phone="+1-555-0121",
            hire_date=date(2023, 5, 20),
            salary=78000,
        )
        emp_plat4 = User(
            id=uuid.uuid4(),
            email="shuri@scb.com",
            password_hash=hash_password("shuri123"),
            first_name="Shuri",
            last_name="Udaku",
            role=UserRole.employee,
            position="Data Engineer",
            department_id=eng.id,
            manager_id=plat_manager.id,
            phone="+1-555-0122",
            hire_date=date(2023, 11, 1),
            salary=90000,
        )

        db.add_all([
            admin, ceo,
            vp_eng, vp_hr, vp_sales, vp_finance,
            emp1, emp2, emp_eng3, emp_eng4,
            emp3, emp_hr2, emp_hr3,
            emp4, emp_sales2, emp_sales3,
            emp_fin1, emp_fin2,
            plat_manager,
            emp_plat1, emp_plat_junior, emp_plat2, emp_plat3, emp_plat4,
        ])
        await db.commit()

        print("Database seeded successfully!")
        print()
        print("Login credentials:")
        print("  CEO:     john@scb.com / john123")
        print("  Admin:   admin@scb.com / admin123")
        print("  Manager: alice@scb.com / alice123 (VP Engineering)")
        print("  Manager: bob@scb.com / bob123 (VP HR)")
        print("  Manager: sarah@scb.com / sarah123 (VP Sales)")
        print("  Manager: michael@scb.com / michael123 (VP Finance)")
        print("  Employee: charlie@scb.com / charlie123")
        print("  Employee: diana@scb.com / diana123")
        print("  Employee: tony@scb.com / tony123")
        print("  Employee: bruce@scb.com / bruce123")
        print("  Employee: eve@scb.com / eve123")
        print("  Employee: natasha@scb.com / natasha123")
        print("  Employee: clark@scb.com / clark123")
        print("  Employee: frank@scb.com / frank123")
        print("  Employee: lara@scb.com / lara123")
        print("  Employee: peter@scb.com / peter123")
        print("  Employee: sam@scb.com / sam123")
        print("  Employee: wanda@scb.com / wanda123")
        print()
        print("--- New Platform Engineering Team ---")
        print("  Manager:  steve@scb.com / steve123 (Platform Engineering Manager, reports to Alice)")
        print("  Employee: carol@scb.com / carol123")
        print("  Employee: thor@scb.com / thor123")
        print("  Employee: scott@scb.com / scott123")
        print("  Employee: shuri@scb.com / shuri123")
        print("  Employee: hope@scb.com / hope123")


if __name__ == "__main__":
    asyncio.run(seed())
