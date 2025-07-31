from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import os
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64
from database.Database import DocumentDatabase
from Agents.AgentOCR import AgentOCR
from Agents.AgentGemini import AgentGemini

app = Flask(__name__)
app.secret_key = "12345678"
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['CLASS_FOLDERS'] = 'class_folders'
app.config['DATABASE'] = 'documents.db'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

ocr_agent = AgentOCR()
gemini_agent = AgentGemini()
db = DocumentDatabase(app.config['DATABASE'])

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CLASS_FOLDERS'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def process_uploaded_file(file):
    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        text = ocr_agent.extract_text_from_pdf(file_path)
        doc_type = ocr_agent.classify_document(text)
        summary = gemini_agent.generate_summary(text)
        extracted_info = gemini_agent.extract_information(text)

        doc_id = db.add_document(
            title=filename,
            doc_type=doc_type,
            summary=summary,
            file_path=file_path,
            entities=extracted_info
        )

        class_folder = os.path.join(app.config['CLASS_FOLDERS'], doc_type)
        os.makedirs(class_folder, exist_ok=True)
        new_path = os.path.join(class_folder, filename)
        os.rename(file_path, new_path)

        with sqlite3.connect(app.config['DATABASE']) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE documents SET file_path = ? WHERE id = ?', (new_path, doc_id))
            conn.commit()

        return {
            'success': True,
            'doc_id': doc_id,
            'type': doc_type,
            'summary': summary,
            'entities': extracted_info
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def generate_stats_chart():
    stats = db.get_document_stats()
    types = [stat[0] for stat in stats]
    counts = [stat[1] for stat in stats]
    plt.figure(figsize=(8, 6))
    plt.bar(types, counts, color='skyblue')
    plt.title('Document Types Distribution')
    plt.xlabel('Document Type')
    plt.ylabel('Count')
    plt.xticks(rotation=45)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return base64.b64encode(buf.read()).decode('utf-8')

@app.route('/')
def index():
    stats = db.get_document_stats()
    chart = generate_stats_chart()
    return render_template('index.html', stats=stats, chart=chart)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or request.files['file'].filename == '':
        flash('No file uploaded', 'error')
        return redirect(url_for('index'))

    file = request.files['file']
    if file and allowed_file(file.filename):
        result = process_uploaded_file(file)
        if result['success']:
            session['last_upload'] = result
            flash('Document processed successfully!', 'success')
            return redirect(url_for('show_upload_result'))
        else:
            flash(f'Error processing document: {result["error"]}', 'error')
            return redirect(url_for('index'))
    flash('Invalid file format. Only PDF files are allowed.', 'error')
    return redirect(url_for('index'))

@app.route('/upload-result')
def show_upload_result():
    if 'last_upload' not in session:
        flash('No recent upload to display', 'error')
        return redirect(url_for('index'))
    return render_template('upload_result.html', **session['last_upload'])

@app.route('/documents/<doc_type>')
def documents_by_type(doc_type):
    documents = db.get_documents_by_type(doc_type)
    return render_template('documents_list.html', doc_type=doc_type, documents=documents)

@app.route('/document/<int:doc_id>')
def document_detail(doc_id):
    doc_data = db.get_document_details(doc_id)
    if not doc_data:
        flash('Document not found', 'error')
        return redirect(url_for('index'))
    entities = {'PER': [], 'ORG': [], 'DATE': []}
    for entity_type, value in doc_data['entities']:
        if entity_type in entities:
            entities[entity_type].append(value)
    return render_template('document_detail.html', document=doc_data['document'], entities=entities)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        flash('Please enter a search term', 'error')
        return redirect(url_for('index'))
    results = db.search_documents(query)
    return render_template('search_results.html', query=query, results=results)

if __name__ == "__main__":
    app.run(debug=True)
