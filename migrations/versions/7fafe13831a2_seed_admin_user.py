"""Seed admin user for integration tests

Revision ID: 7fafe13831a2
Revises: "a93240b89c29"
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from passlib.context import CryptContext
import uuid


# revision identifiers, used by Alembic.
revision = "7fafe13831a2"
down_revision = "a93240b89c29"
branch_labels = None
depends_on = None


def _cols(insp, table_name):
    return {c["name"] for c in insp.get_columns(table_name, schema="public")}


def _pk(insp, table_name):
    pk = insp.get_pk_constraint(table_name, schema="public") or {}
    cols = pk.get("constrained_columns") or []
    return cols[0] if cols else "id"


def _gen_pk(bind, table, pk_col, pk_type, table_name):
    t = str(pk_type).lower()
    if "uuid" in t:
        return str(uuid.uuid4())
    if "int" in t:
        nxt = bind.execute(sa.text(f"SELECT COALESCE(MAX({pk_col}), 0) + 1 FROM public.{table_name}")).scalar()
        return int(nxt)
    return str(uuid.uuid4())


def _find_users_table(insp):
    for tname in insp.get_table_names(schema="public"):
        cols = _cols(insp, tname)
        if "login" in cols and ({"password_hash", "hashed_password", "password"} & cols):
            return tname
    return None


def _find_roles_table(insp):
    for tname in insp.get_table_names(schema="public"):
        cols = _cols(insp, tname)
        if "name" in cols and "role" in tname.lower():
            return tname
    return None


def _find_link_table(insp):
    for tname in insp.get_table_names(schema="public"):
        cols = _cols(insp, tname)
        if "user_id" in cols and "role_id" in cols:
            return tname
    return None


def upgrade():
    bind = op.get_bind()
    insp = inspect(bind)

    users_name = _find_users_table(insp)
    roles_name = _find_roles_table(insp)
    link_name = _find_link_table(insp)

    if not users_name:
        return

    meta = sa.MetaData()
    users = sa.Table(users_name, meta, autoload_with=bind, schema="public")
    roles = sa.Table(roles_name, meta, autoload_with=bind, schema="public") if roles_name else None
    link = sa.Table(link_name, meta, autoload_with=bind, schema="public") if link_name else None

    users_pk = _pk(insp, users_name)

    # hash exactly by context that accepts bcrypt_sha256 + bcrypt
    pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")
    pwd_hash = pwd_context.hash("Admin_123!")

    # 1) ensure role admin (explicit id if needed)
    role_id = None
    if roles is not None:
        roles_pk = _pk(insp, roles_name)

        role_id = bind.execute(sa.select(roles.c[roles_pk]).where(roles.c.name == "admin")).scalar()
        if role_id is None:
            ins = {"name": "admin"}
            if roles_pk in roles.c and roles_pk != "name":
                ins[roles_pk] = _gen_pk(bind, roles, roles_pk, roles.c[roles_pk].type, roles_name)
            bind.execute(sa.insert(roles).values(**ins))
            role_id = bind.execute(sa.select(roles.c[roles_pk]).where(roles.c.name == "admin")).scalar()

    # 2) upsert admin user (explicit id if needed) + put hash into existing password column
    pwd_col = None
    for cand in ("password_hash", "hashed_password", "password"):
        if cand in users.c:
            pwd_col = cand
            break

    admin_id = bind.execute(sa.select(users.c[users_pk]).where(users.c.login == "admin")).scalar()
    if admin_id is None:
        values = {"login": "admin"}

        if users_pk in users.c and users_pk != "login":
            values[users_pk] = _gen_pk(bind, users, users_pk, users.c[users_pk].type, users_name)

        if "email" in users.c:
            values["email"] = "admin@test.local"

        if pwd_col:
            values[pwd_col] = pwd_hash

        for col in ("is_active", "is_superuser", "is_admin"):
            if col in users.c:
                values[col] = True

        res = bind.execute(sa.insert(users).values(**values))
        try:
            admin_id = res.inserted_primary_key[0]
        except Exception:
            admin_id = bind.execute(sa.select(users.c[users_pk]).where(users.c.login == "admin")).scalar()
    else:
        upd = {}
        if "email" in users.c:
            upd["email"] = "admin@test.local"
        if pwd_col:
            upd[pwd_col] = pwd_hash
        for col in ("is_active", "is_superuser", "is_admin"):
            if col in users.c:
                upd[col] = True
        if upd:
            bind.execute(sa.update(users).where(users.c.login == "admin").values(**upd))

    # 3) link admin -> admin role (explicit id if link table has PK)
    if link is not None and admin_id is not None and role_id is not None:
        exists = bind.execute(
            sa.select(sa.literal(1)).select_from(link).where(sa.and_(link.c.user_id == admin_id, link.c.role_id == role_id))
        ).scalar()
        if exists is None:
            ins = {"user_id": admin_id, "role_id": role_id}
            link_pk = _pk(insp, link_name)
            if link_pk in link.c and link_pk not in ("user_id", "role_id"):
                ins[link_pk] = _gen_pk(bind, link, link_pk, link.c[link_pk].type, link_name)
            bind.execute(sa.insert(link).values(**ins))


def downgrade():
    pass