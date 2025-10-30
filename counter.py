import os
import psycopg2
from flask import Flask, render_template,request,redirect,url_for,jsonify

app=Flask(__name__)


def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        conn = psycopg2.connect(database_url)
        
    else:
        conn = psycopg2.connect(
            host = "db",
            database = "counter_db",
            user = "user",
            password = "futaba0127"
        )
        
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cousor()
    
    try:
        with app.open_resource('schema.sql', mode="r") as f:
            cur.execute(f.read())
            
            conn.commit()
            print('テーブルが作成されました')
            
    except Exception as e:
        print(f'データベース作成時エラー：{e}')
        
        if conn:
            conn.rollback()
            
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            
with app.app_context():
    init_db()
    
    
@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug = True, host = '0.0.0.0', port = 8080)
