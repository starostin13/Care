#!/usr/bin/env python3
"""
Simple SQLite Web Interface for CareBot Database
"""

from flask import Flask, render_template_string, request, jsonify
import sqlite3
import os
import json
from datetime import datetime

app = Flask(__name__)

DATABASE_PATH = os.environ.get('DATABASE_PATH', '/app/data/game_database.db')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>CareBot Database - SQLite Web Interface</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { border-bottom: 2px solid #007bff; padding-bottom: 10px; margin-bottom: 20px; }
        .header h1 { color: #007bff; margin: 0; }
        .query-form { margin-bottom: 30px; padding: 20px; background: #f8f9fa; border-radius: 4px; }
        .query-form textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace; }
        .btn { background: #007bff; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; }
        .btn:hover { background: #0056b3; }
        .btn-secondary { background: #6c757d; }
        .btn-secondary:hover { background: #545b62; }
        .table-container { overflow-x: auto; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #007bff; color: white; position: sticky; top: 0; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .info { background: #d1ecf1; padding: 10px; border-radius: 4px; margin-bottom: 20px; color: #0c5460; }
        .error { background: #f8d7da; padding: 10px; border-radius: 4px; margin-bottom: 20px; color: #721c24; }
        .tables-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-bottom: 20px; }
        .table-card { background: #e9ecef; padding: 10px; border-radius: 4px; cursor: pointer; transition: background 0.3s; }
        .table-card:hover { background: #dee2e6; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 20px; }
        .stat-card { background: #007bff; color: white; padding: 15px; border-radius: 4px; text-align: center; }
        .stat-value { font-size: 24px; font-weight: bold; }
        .stat-label { font-size: 12px; opacity: 0.8; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 CareBot Database</h1>
            <p>SQLite Web Interface - Last updated: {{ timestamp }}</p>
        </div>

        <div class="stats" id="stats">
            <!-- Stats will be loaded here -->
        </div>

        <div class="info">
            <strong>Available Tables:</strong>
            <div class="tables-list" id="tables-list">
                <!-- Tables will be loaded here -->
            </div>
        </div>

        <div class="query-form">
            <h3>Execute SQL Query</h3>
            <textarea id="query" rows="5" placeholder="SELECT * FROM warmasters LIMIT 10;">SELECT * FROM warmasters LIMIT 10;</textarea>
            <br><br>
            <button class="btn" onclick="executeQuery()">Execute Query</button>
            <button class="btn btn-secondary" onclick="loadTables()">Refresh Tables</button>
        </div>

        <div id="results"></div>
    </div>

    <script>
        function loadTables() {
            fetch('/api/tables')
                .then(response => response.json())
                .then(data => {
                    const tablesContainer = document.getElementById('tables-list');
                    tablesContainer.innerHTML = data.tables.map(table => 
                        `<div class="table-card" onclick="selectTable('${table}')">${table}</div>`
                    ).join('');
                    
                    const statsContainer = document.getElementById('stats');
                    statsContainer.innerHTML = data.stats.map(stat => 
                        `<div class="stat-card">
                            <div class="stat-value">${stat.count}</div>
                            <div class="stat-label">${stat.table}</div>
                        </div>`
                    ).join('');
                });
        }

        function selectTable(tableName) {
            document.getElementById('query').value = `SELECT * FROM ${tableName} LIMIT 50;`;
        }

        function executeQuery() {
            const query = document.getElementById('query').value;
            const resultsDiv = document.getElementById('results');
            
            resultsDiv.innerHTML = '<div class="info">Executing query...</div>';
            
            fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    resultsDiv.innerHTML = `<div class="error"><strong>Error:</strong> ${data.error}</div>`;
                } else {
                    let html = `<div class="info"><strong>Query executed successfully.</strong> ${data.rows.length} row(s) returned.</div>`;
                    
                    if (data.rows.length > 0) {
                        html += '<div class="table-container"><table>';
                        html += '<thead><tr>' + data.columns.map(col => `<th>${col}</th>`).join('') + '</tr></thead>';
                        html += '<tbody>' + data.rows.map(row => 
                            '<tr>' + row.map(cell => `<td>${cell !== null ? cell : '<em>NULL</em>'}</td>`).join('') + '</tr>'
                        ).join('') + '</tbody>';
                        html += '</table></div>';
                    }
                    
                    resultsDiv.innerHTML = html;
                }
            })
            .catch(error => {
                resultsDiv.innerHTML = `<div class="error"><strong>Error:</strong> ${error.message}</div>`;
            });
        }

        // Load tables on page load
        loadTables();
    </script>
</body>
</html>
"""

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DATABASE_PATH)

@app.route('/')
def index():
    """Main page"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template_string(HTML_TEMPLATE, timestamp=timestamp)

@app.route('/api/tables')
def get_tables():
    """Get list of tables and basic stats"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Get row counts for each table
        stats = []
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats.append({'table': table, 'count': count})
            except:
                stats.append({'table': table, 'count': 'Error'})
        
        conn.close()
        return jsonify({'tables': tables, 'stats': stats})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/query', methods=['POST'])
def execute_query():
    """Execute SQL query"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query cannot be empty'})
        
        # Basic safety check
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
        query_upper = query.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return jsonify({'error': f'Dangerous operation "{keyword}" not allowed'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Get column names
        columns = [description[0] for description in cursor.description] if cursor.description else []
        
        conn.close()
        
        return jsonify({
            'rows': rows,
            'columns': columns,
            'count': len(rows)
        })
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print(f"Starting SQLite Web Interface for database: {DATABASE_PATH}")
    app.run(host='0.0.0.0', port=8080, debug=False)