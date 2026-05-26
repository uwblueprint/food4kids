from sqlalchemy import Result, Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.pagination import PaginationParams


async def paginate_query(
    session: AsyncSession,
    statement: Select,
    params: PaginationParams,
) -> tuple[Result, int]:
    """
    Apply pagination to a SQLAlchemy select statement.

    Runs a count query on the statement, then applies offset/limit.
    Returns the raw Result and total count so callers can extract items
    however they need (.scalars().all() for single-table, .all() for joins).
    """
    count_statement = select(func.count()).select_from(statement.subquery())
    count_result = await session.execute(count_statement)
    total = count_result.scalar_one()

    paginated_statement = statement.offset(params.offset).limit(params.limit)
    result = await session.execute(paginated_statement)

    return result, total
