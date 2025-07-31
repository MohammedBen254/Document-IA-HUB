import sqlite3
import os
from datetime import datetime

class DocumentDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initialise la structure de la base de données"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.executescript('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    type TEXT,
                    summary TEXT,
                    file_path TEXT,
                    upload_date TEXT,
                    class_folder TEXT
                );

                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER,
                    entity_type TEXT,
                    value TEXT,
                    FOREIGN KEY (document_id) REFERENCES documents(id)
                );

                CREATE TABLE IF NOT EXISTS search_index (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER,
                    content TEXT,
                    FOREIGN KEY (document_id) REFERENCES documents(id)
                );
            ''')
            conn.commit()

    def add_document(self, title, doc_type, summary, file_path, entities):
        """Ajoute un document à la base de données"""
        upload_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        class_folder = os.path.join('class_folders', doc_type)

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO documents (title, type, summary, file_path, upload_date, class_folder)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (title, doc_type, summary, file_path, upload_date, class_folder))
            doc_id = cursor.lastrowid

            # Enregistre les entités
            for entity_type, values in entities.items():
                if entity_type in ['PER', 'ORG', 'DATE']:
                    for value in values[:5]:  # max 5 par type
                        cursor.execute('''
                            INSERT INTO entities (document_id, entity_type, value)
                            VALUES (?, ?, ?)
                        ''', (doc_id, entity_type, value))

            # Ajoute à l'index de recherche
            cursor.execute('''
                INSERT INTO search_index (document_id, content)
                VALUES (?, ?)
            ''', (doc_id, summary))

            conn.commit()
        return doc_id

    def get_documents_by_type(self, doc_type):
        """Récupère les documents par type"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, upload_date, summary 
                FROM documents 
                WHERE type = ?
                ORDER BY upload_date DESC
            ''', (doc_type,))
            return cursor.fetchall()

    def get_document_stats(self):
        """Retourne le nombre de documents par type"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT type, COUNT(*) FROM documents GROUP BY type
            ''')
            return cursor.fetchall()

    def get_document_details(self, document_id):
        """Retourne les détails d'un document et ses entités"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM documents WHERE id = ?', (document_id,))
            document = cursor.fetchone()
            if not document:
                return None

            cursor.execute('SELECT entity_type, value FROM entities WHERE document_id = ?', (document_id,))
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
        """Recherche dans les titres, résumés et entités"""
        with self._connect() as conn:
            cursor = conn.cursor()
            like_query = f"%{query}%"
            cursor.execute('''
                SELECT id, title, summary, upload_date FROM documents
                WHERE title LIKE ? OR summary LIKE ? OR id IN (
                    SELECT document_id FROM entities WHERE value LIKE ?
                )
                ORDER BY upload_date DESC
            ''', (like_query, like_query, like_query))
            return cursor.fetchall()

    def delete_document(self, document_id):
        """Supprime un document et ses entités associées"""
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
