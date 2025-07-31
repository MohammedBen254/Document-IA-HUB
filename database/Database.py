import sqlite3
import json
from datetime import datetime
import os

class DocumentDatabase:
    def __init__(self, db_path='documents1.db'):
        self.db_path = db_path
        self._create_tables()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    doc_type TEXT,
                    summary TEXT,
                    file_path TEXT,
                    created_at TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER,
                    entity_type TEXT,
                    value TEXT,
                    FOREIGN KEY(document_id) REFERENCES documents(id)
                )
            ''')
            conn.commit()

    def add_document(self, title, doc_type, summary, file_path, entities):
        with self._connect() as conn:
            cursor = conn.cursor()
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO documents (title, doc_type, summary, file_path, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, doc_type, summary, file_path, created_at))
            document_id = cursor.lastrowid
            for entity_type, value in entities:
                cursor.execute('''
                    INSERT INTO entities (document_id, entity_type, value)
                    VALUES (?, ?, ?)
                ''', (document_id, entity_type, value))
            conn.commit()
            return document_id

    def get_document_stats(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT doc_type, COUNT(*) FROM documents GROUP BY doc_type
            ''')
            return cursor.fetchall()

    def get_documents_by_type(self, doc_type):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, summary, created_at FROM documents WHERE doc_type = ? ORDER BY created_at DESC
            ''', (doc_type,))
            return cursor.fetchall()

    def get_document_details(self, document_id):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT * FROM documents WHERE id = ?''', (document_id,))
            document = cursor.fetchone()
            if not document:
                return None
            cursor.execute('''SELECT entity_type, value FROM entities WHERE document_id = ?''', (document_id,))
            entities = cursor.fetchall()
            return {
                'document': {
                    'id': document[0],
                    'title': document[1],
                    'doc_type': document[2],
                    'summary': document[3],
                    'file_path': document[4],
                    'created_at': document[5]
                },
                'entities': entities
            }

    def search_documents(self, query):
        with self._connect() as conn:
            cursor = conn.cursor()
            like_query = f"%{query}%"
            cursor.execute('''
                SELECT id, title, summary, created_at FROM documents
                WHERE title LIKE ? OR summary LIKE ? OR id IN (
                    SELECT document_id FROM entities WHERE value LIKE ?
                ) ORDER BY created_at DESC
            ''', (like_query, like_query, like_query))
            return cursor.fetchall()

    def delete_document(self, document_id):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT file_path FROM documents WHERE id = ?', (document_id,))
            row = cursor.fetchone()
            if row:
                file_path = row[0]
                if os.path.exists(file_path):
                    os.remove(file_path)
            cursor.execute('DELETE FROM entities WHERE document_id = ?', (document_id,))
            cursor.execute('DELETE FROM documents WHERE id = ?', (document_id,))
            conn.commit()
            return True
        return False