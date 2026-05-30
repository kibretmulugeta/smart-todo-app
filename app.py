from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import sqlite3
import json
import os
from dotenv import load_dotenv
from models import init_db, add_task, get_all_tasks, get_due_tasks, update_task_status, get_categories_from_db, add_custom_category
from scheduler import calculate_next_due, generate_recurring_dates

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

# Initialize database
init_db()

@app.route('/')
def index():
    return render_template('index.html')

# Get all tasks
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    tasks = get_all_tasks()
    return jsonify(tasks)

# Get tasks due now
@app.route('/api/tasks/due', methods=['GET'])
def get_due():
    tasks = get_due_tasks()
    return jsonify(tasks)

# Create new smart task
@app.route('/api/tasks', methods=['POST'])
def create_task():
    try:
        data = request.get_json()
        
        required = ['title', 'category', 'time_type']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Build time configuration
        time_config = {
            'type': data['time_type']
        }
        
        if data['time_type'] == 'once':
            time_config['scheduled_datetime'] = data.get('scheduled_datetime')
        
        elif data['time_type'] == 'duration':
            time_config.update({
                'duration_value': data.get('duration_value'),
                'duration_unit': data.get('duration_unit'),
                'start_now': data.get('start_now', True),
                'start_datetime': datetime.now().isoformat() if data.get('start_now') else data.get('start_datetime')
            })
        
        elif data['time_type'] == 'recurring':
            time_config.update({
                'pattern': data.get('pattern'),
                'interval': data.get('interval', 1),
                'unit': data.get('unit', 'days'),
                'start_datetime': data.get('start_datetime'),
                'end_datetime': data.get('end_datetime'),
                'max_occurrences': data.get('max_occurrences')
            })
        
        # Add time bounds if provided
        if 'time_bound' in data:
            time_config['bound'] = {
                'start': data['time_bound'].get('start'),
                'end': data['time_bound'].get('end')
            }
        
        task_id = add_task(
            title=data['title'],
            description=data.get('description', ''),
            category=data['category'],
            time_config=time_config
        )
        
        return jsonify({'id': task_id, 'message': 'Task created successfully'}), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Complete a task
@app.route('/api/tasks/<int:task_id>/complete', methods=['PUT'])
def complete_task(task_id):
    update_task_status(task_id, 'completed')
    return jsonify({'success': True})

# Delete a task
@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    conn = sqlite3.connect('instance/smart_todo.db')
    c = conn.cursor()
    c.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# Get categories
@app.route('/api/categories', methods=['GET'])
def get_categories():
    categories = get_categories_from_db()
    return jsonify(categories)

# Add custom category
@app.route('/api/categories', methods=['POST'])
def add_category():
    data = request.get_json()
    category_id = add_custom_category(data['name'], data.get('icon', '📌'), data.get('color', '#808080'))
    return jsonify({'id': category_id, 'message': 'Category added'}), 201

if __name__ == '__main__':
    app.run(debug=True, port=5000)