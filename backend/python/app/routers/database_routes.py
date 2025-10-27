from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text
from datetime import datetime

from app.models import get_session

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
        tables_result = await session.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        table_names = [row[0] for row in tables_result.fetchall()]

        all_data = {}

        for table_name in table_names:
            try:
                # Get all data from this table
                result = await session.execute(text(f"SELECT * FROM {table_name}"))
                rows = result.fetchall()

                # Get column names
                columns = list(result.keys()) if hasattr(result, 'keys') else []

                # Convert rows to dictionaries
                table_data = []
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        if i < len(columns):
                            # Convert datetime/date objects to strings
                            if hasattr(value, 'isoformat'):
                                row_dict[columns[i]] = value.isoformat()
                            else:
                                row_dict[columns[i]] = str(value) if value is not None else None
                    table_data.append(row_dict)

                all_data[table_name] = {
                    "total_rows": len(table_data),
                    "columns": columns,
                    "data": table_data
                }

            except Exception as e:
                all_data[table_name] = {
                    "error": f"Could not read table: {str(e)}"
                }

        # Generate HTML output
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Database Tables</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; }}
                .summary {{ background: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .table-container {{ background: white; margin: 20px 0; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
                .table-header {{ background: #4CAF50; color: white; padding: 15px; font-weight: bold; font-size: 18px; }}
                .empty-header {{ background: #FF9800; }}
                .error-header {{ background: #f44336; }}
                .columns {{ background: #f8f9fa; padding: 10px 15px; border-bottom: 1px solid #dee2e6; font-family: monospace; color: #6c757d; }}
                .data-container {{ max-height: 400px; overflow-y: auto; }}
                .row {{ padding: 10px 15px; border-bottom: 1px solid #eee; font-family: monospace; font-size: 12px; }}
                .row:hover {{ background-color: #f8f9fa; }}
                .row-number {{ color: #6c757d; margin-right: 10px; font-weight: bold; }}
                .key {{ color: #d63384; font-weight: bold; }}
                .value {{ color: #0d6efd; }}
                .emoji {{ font-size: 1.2em; margin-right: 8px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🗃️ Database Tables Inspector</h1>
                <p>Complete view of all database tables and their data</p>
            </div>

            <div class="summary">
                <h3>📊 Summary</h3>
                <p><strong>Total Tables:</strong> {len(table_names)}</p>
                <p><strong>Database:</strong> PostgreSQL</p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """

        # Generate HTML for each table
        for table_name, table_info in all_data.items():
            if "error" in table_info:
                html_content += f"""
                <div class="table-container">
                    <div class="table-header error-header">
                        <span class="emoji">❌</span>{table_name}
                    </div>
                    <div class="columns">Error: {table_info['error']}</div>
                </div>
                """
            elif table_info["total_rows"] == 0:
                html_content += f"""
                <div class="table-container">
                    <div class="table-header empty-header">
                        <span class="emoji">🗃️</span>{table_name} (empty)
                    </div>
                    <div class="columns">Columns: {', '.join(table_info['columns'])}</div>
                </div>
                """
            else:
                html_content += f"""
                <div class="table-container">
                    <div class="table-header">
                        <span class="emoji">📊</span>{table_name} ({table_info['total_rows']} rows)
                    </div>
                    <div class="columns">Columns: {', '.join(table_info['columns'])}</div>
                    <div class="data-container">
                """

                for i, row in enumerate(table_info["data"]):
                    row_html = f'<div class="row"><span class="row-number">#{i+1}</span>'
                    for key, value in row.items():
                        row_html += f'<span class="key">{key}=</span><span class="value">{value}</span>  '
                    row_html += '</div>'
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
            media_type="text/html"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching database data: {str(e)}"
        )