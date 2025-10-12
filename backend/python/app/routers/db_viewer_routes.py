from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.models import get_session

router = APIRouter(prefix="/db", tags=["database"])


@router.get("/view", response_class=HTMLResponse)
async def view_database(session: AsyncSession = Depends(get_session)):
    """View all database tables and their contents"""

    html_parts = [
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Database Viewer</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }
                h1 {
                    color: #333;
                }
                .table-container {
                    background: white;
                    padding: 20px;
                    margin-bottom: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                h2 {
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                }
                th {
                    background-color: #3498db;
                    color: white;
                    padding: 12px;
                    text-align: left;
                }
                td {
                    padding: 10px;
                    border-bottom: 1px solid #ddd;
                }
                tr:hover {
                    background-color: #f5f5f5;
                }
                .count {
                    color: #7f8c8d;
                    font-style: italic;
                }
            </style>
        </head>
        <body>
            <h1>Database Viewer</h1>
        """
    ]

    tables_query = text(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
        """
    )

    result = await session.execute(tables_query)
    tables = [row[0] for row in result.fetchall()]

    for table_name in tables:
        count_query = text(f"SELECT COUNT(*) FROM {table_name}")
        count_result = await session.execute(count_query)
        count = count_result.scalar()

        html_parts.append(f'<div class="table-container">')
        html_parts.append(
            f'<h2>{table_name} <span class="count">({count} rows)</span></h2>'
        )

        data_query = text(f"SELECT * FROM {table_name} LIMIT 100")
        data_result = await session.execute(data_query)
        rows = data_result.fetchall()
        columns = data_result.keys()

        if rows:
            html_parts.append("<table>")
            html_parts.append("<tr>")
            for col in columns:
                html_parts.append(f"<th>{col}</th>")
            html_parts.append("</tr>")

            for row in rows:
                html_parts.append("<tr>")
                for value in row:
                    html_parts.append(f"<td>{value}</td>")
                html_parts.append("</tr>")

            html_parts.append("</table>")
        else:
            html_parts.append("<p>No data in this table.</p>")

        html_parts.append("</div>")

    html_parts.append("</body></html>")

    return "".join(html_parts)
