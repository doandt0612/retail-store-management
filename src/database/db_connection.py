import os
import pyodbc
from dotenv import load_dotenv

# Tự động nạp các biến từ file .env
load_dotenv()

class DatabaseManager:
    def __init__(self):
        # Đọc thông tin từ biến môi trường, nếu không có thì lấy giá trị mặc định
        self.server = os.getenv('DB_SERVER')
        self.database = os.getenv('DB_NAME')
        self.driver = os.getenv('DB_DRIVER', '{ODBC Driver 18 for SQL Server}')

    def get_connection(self):
        # Đọc thêm user và password từ .env
        user = os.getenv('DB_USER')
        password = os.getenv('DB_PASSWORD')
        
        if not self.server: return None
            
        conn_str = (
            f'DRIVER={self.driver};'
            f'SERVER={self.server};'
            f'DATABASE={self.database};'
            f'UID={user};'
            f'PWD={password};'
            f'TrustServerCertificate=yes;' # Bắt buộc cho Driver 18 trên WSL
        )
        try:
            return pyodbc.connect(conn_str, timeout=5) # Đặt timeout ngắn để test nhanh
        except Exception as e:
            print(f"Lỗi kết nối: {e}")
            return None
    
    def fetch_all(self, query, params=None):
        """Hàm dùng để lấy dữ liệu (SELECT)"""
        conn = self.get_connection()
        if not conn: return []
        
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
            
        conn.close()
        return results

    def execute_query(self, query, params=None):
        """Hàm dùng để Thêm/Sửa/Xóa (INSERT/UPDATE/DELETE)"""
        conn = self.get_connection()
        if not conn: return False
        
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return True
        except Exception as e:
            print(f"Lỗi thực thi Query: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()