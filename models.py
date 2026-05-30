import sqlite3
import json
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join('instance', 'smart_todo.db')

def init_db():
    """Initialize database with all tables"""
    os.makedirs('instance', exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Tasks table
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            time_config TEXT,
            next_due TIMESTAMP
        )
    ''')
    
    # Categories table
    c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            icon TEXT,
            color TEXT,
            is_custom BOOLEAN DEFAULT 0
        )
    ''')
    
    # Insert default categories
    default_cats = [
        ('Work', '💼', '#4CAF50', 0),
        ('Personal', '🏠', '#2196F3', 0),
        ('Health', '🏃', '#FF9800', 0),
        ('Learning', '📚', '#9C27B0', 0),
        ('Shopping', '🛒', '#F44336', 0)
    ]
    
    for cat in default_cats:
        c.execute('INSERT OR IGNORE INTO categories (name, icon, color, is_custom) VALUES (?, ?, ?, ?)', cat)
    
    conn.commit()
    conn.close()

def add_task(title, description, category, time_config):
    """Add a new task with smart scheduling"""
    from scheduler import calculate_next_due
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    next_due = calculate_next_due(time_config)
    
    c.execute('''
        INSERT INTO tasks (title, description, category, time_config, next_due)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, description, category, json.dumps(time_config), next_due))
    
    task_id = c.lastrowid
    conn.commit()
    conn.close()
    return task_id

def get_all_tasks():
    """Get all tasks ordered by next due date"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM tasks ORDER BY next_due ASC NULLS LAST')
    tasks = [dict(row) for row in c.fetchall()]
    
    for task in tasks:
        task['time_config'] = json.loads(task['time_config']) if task['time_config'] else {}
    
    conn.close()
    return tasks

def get_due_tasks():
    """Get tasks that are due now"""
    now = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM tasks WHERE next_due <= ? AND status = "pending"', (now,))
    tasks = [dict(row) for row in c.fetchall()]
    conn.close()
    return tasks

def update_task_status(task_id, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, task_id))
    conn.commit()
    conn.close()

def get_categories_from_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM categories ORDER BY is_custom, name')
    categories = [dict(row) for row in c.fetchall()]
    conn.close()
    return categories

def add_custom_category(name, icon, color):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO categories (name, icon, color, is_custom) VALUES (?, ?, ?, 1)',
              (name, icon, color))
    category_id = c.lastrowid
    conn.commit()
    conn.close()
    return category_id