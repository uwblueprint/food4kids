from datetime import datetime
from typing import Any, TypedDict

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text

from app.models import get_session


class TableErrorInfo(TypedDict):
    error: str


class TableDataInfo(TypedDict):
    total_rows: int
    columns: list[str]
    data: list[dict[str, Any]]


TableInfo = TableErrorInfo | TableDataInfo

router = APIRouter(tags=["database"])


@router.get("/table")
async def get_all_tables(
    session: AsyncSession = Depends(get_session),
) -> Response:
    """
    Get ALL tables and their data - show everything in the database
    """
    try:
        # Get all table names
        tables_result = await session.execute(
            text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        )
        table_names = [row[0] for row in tables_result.fetchall()]

        all_data: dict[str, TableInfo] = {}

        for table_name in table_names:
            try:
                # Get all data from this table
                result = await session.execute(text(f"SELECT * FROM {table_name}"))
                rows = result.fetchall()

                # Get column names
                columns: list[str] = (
                    list(result.keys()) if hasattr(result, "keys") else []
                )

                # Convert rows to dictionaries
                table_data: list[dict[str, Any]] = []
                for row in rows:
                    row_dict: dict[str, Any] = {}
                    for i, value in enumerate(row):
                        if i < len(columns):
                            # Convert datetime/date objects to strings
                            if hasattr(value, "isoformat"):
                                row_dict[columns[i]] = value.isoformat()
                            else:
                                row_dict[columns[i]] = (
                                    str(value) if value is not None else None
                                )
                    table_data.append(row_dict)

                all_data[table_name] = TableDataInfo(
                    total_rows=len(table_data),
                    columns=columns,
                    data=table_data,
                )

            except Exception as e:
                all_data[table_name] = TableErrorInfo(
                    error=f"Could not read table: {e!s}",
                )

        # Generate HTML output
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Database Tables</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 20px; background: #fafafa; }}
                .header {{ background: #2563eb; color: white; padding: 16px; border-radius: 6px; margin-bottom: 20px; }}
                .header h1 {{ margin: 0; font-size: 20px; }}
                .header p {{ margin: 4px 0 0 0; opacity: 0.9; }}
                .table-container {{ background: white; margin: 16px 0; border-radius: 6px; border: 1px solid #e5e7eb; }}
                .table-header {{ background: #f3f4f6; padding: 12px 16px; border-bottom: 1px solid #e5e7eb; font-weight: 600; font-size: 14px; }}
                .empty-header {{ background: #fef3c7; color: #92400e; }}
                .error-header {{ background: #fecaca; color: #991b1b; }}
                .columns {{ padding: 8px 16px; border-bottom: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; font-family: monospace; }}
                .data-container {{ max-height: 300px; overflow-y: auto; }}
                .row {{ padding: 8px 16px; border-bottom: 1px solid #f3f4f6; font-size: 12px; font-family: monospace; }}
                .row:hover {{ background: #f9fafb; }}
                .key {{ color: #dc2626; }}
                .value {{ color: #059669; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Database Tables</h1>
                <p>{len(table_names)} tables • {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>
        """

        # Generate HTML for each table
        for table_name, table_info in all_data.items():
            if "error" in table_info:
                error_info: TableErrorInfo = table_info  # type: ignore[assignment]
                html_content += f"""
                <div class="table-container">
                    <div class="table-header error-header">
                        {table_name}
                    </div>
                    <div class="columns">Error: {error_info["error"]}</div>
                </div>
                """
            else:
                data_info: TableDataInfo = table_info
                if data_info["total_rows"] == 0:
                    html_content += f"""
                    <div class="table-container">
                        <div class="table-header empty-header">
                            {table_name} (empty)
                        </div>
                        <div class="columns">Columns: {", ".join(data_info["columns"])}</div>
                    </div>
                    """
                else:
                    html_content += f"""
                    <div class="table-container">
                        <div class="table-header">
                            {table_name} ({data_info["total_rows"]} rows)
                        </div>
                        <div class="columns">Columns: {", ".join(data_info["columns"])}</div>
                        <div class="data-container">
                    """

                    for row_data in data_info["data"]:
                        row_html = '<div class="row">'
                        for key, value in row_data.items():
                            row_html += f'<span class="key">{key}</span>=<span class="value">{value}</span> '
                        row_html += "</div>"
                        html_content += row_html

                    html_content += """
                        </div>
                    </div>
                    """

        html_content += """
        </body>
        </html>
        """

        return Response(
            content=html_content,
            media_type="text/html",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching database data: {e!s}",
        ) from e
