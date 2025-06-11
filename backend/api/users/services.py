from math import ceil
from sqlalchemy import or_
from models.user import User
from sqlalchemy.orm import Session
from core.security import hash_password
from .schema import UserCreate, UserUpdate, UserSortField

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_users(
    db: Session,
    page: int = 1,
    per_page: int = 10,
    keyword: str = None,
    sort_by: str = None,
    desc: bool = False
):
    query = db.query(User)

    if keyword:
        query = query.filter(
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
        query = query.order_by(sort_col)

    # Total count
    total = query.count()
    total_pages = ceil(total / per_page) if per_page else 1

    # Pagination
    skip = (page - 1) * per_page
    users = query.offset(skip).limit(per_page).all()

    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "users": users
    }

def create_user(db: Session, user_in: UserCreate):
    if db.query(User).filter(User.email == user_in.email).first():
        raise ValueError("Email already exists")
    user = User(
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        email=user_in.email,
        phone=user_in.phone,
        password=hash_password(user_in.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user(db: Session, user_id: int, user_in: UserUpdate):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    update_data = user_in.model_dump(exclude_unset=True)
    if "email" in update_data and update_data["email"]:
        existing = db.query(User).filter(User.email == update_data["email"], User.id != user_id).first()
        if existing:
            raise ValueError("Email already exists")
    if "password" in update_data and update_data["password"]:
        update_data["password"] = hash_password(update_data["password"])
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    db.delete(user)
    db.commit()
    return user