from typing import Any, TypeVar

from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import JSONB, array_agg
from sqlalchemy.engine import CursorResult, Row
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import Select, func
from sqlalchemy.sql._typing import _ColumnsClauseArgument


def sql_jsonb_agg(table: Table) -> _ColumnsClauseArgument[JSONB]:
    """Equivalent to `func.JSONB_AGG` but removes empty elements from the output"""
    return func.to_jsonb(
        func.array_remove(array_agg(table.table_valued().distinct()), None)
    ).label(table.name)


T = TypeVar("T", bound=tuple[Any, ...])


async def fetch_one(conn: AsyncConnection, stmt: Select[T]) -> Row[T] | None:
    res: CursorResult[T] = await conn.execute(stmt.limit(1))
    return res.first()
