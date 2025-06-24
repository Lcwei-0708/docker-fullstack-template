from math import ceil
from sqlalchemy import or_, select, func
from models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from core.security import hash_password
from .schema import UserCreate, UserUpdate, UserSortField

async def get_user(db: AsyncSession, user_id: str):
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def get_users(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 10,
    keyword: str = None,
    sort_by: str = None,
    desc: bool = False
):
    stmt = select(User)
    if keyword:
        stmt = stmt.where(
            or_(
                User.first_name.ilike(f"%{keyword}%"),
                User.last_name.ilike(f"%{keyword}%")
            )
        )
    # Sorting
    SORT_FIELDS = set(e.value for e in UserSortField)
    if sort_by in SORT_FIELDS:
        sort_col = getattr(User, sort_by)
        if desc:
            sort_col = sort_col.desc()
        stmt = stmt.order_by(sort_col)
    # Total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()
    total_pages = ceil(total / per_page) if per_page else 1
    # Pagination
    skip = (page - 1) * per_page
    stmt = stmt.offset(skip).limit(per_page)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "users": users
    }

async def create_user(db: AsyncSession, user_in: UserCreate):
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar():
        raise ValueError("Email already exists")
    user = User(
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        email=user_in.email,
        phone=user_in.phone,
        password=hash_password(user_in.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def update_user(db: AsyncSession, user_id: str, user_in: UserUpdate):
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None
    update_data = user_in.model_dump(exclude_unset=True)
    if "email" in update_data and update_data["email"]:
        result = await db.execute(select(User).where(User.email == update_data["email"], User.id != user_id))
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError("Email already exists")
    if "password" in update_data and update_data["password"]:
        update_data["password"] = hash_password(update_data["password"])
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user

async def delete_user(db: AsyncSession, user_id: str):
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None
    await db.delete(user)
    await db.commit()
    return user