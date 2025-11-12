import os
import psycopg2
from flask import Flask, render_template,request,redirect,url_for,jsonify
from io import TextIOWrapper
import csv

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
    cur = conn.cursor()
    
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
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register_group',methods = ('POST','GET'))
def register_group():
    if request.method == 'POST':
        group_name = request.form.get('group_name')
        values = request.form.get('values')
        
        # if not group_name:
        #     error = '玉数名を入力してください'
        # if error:
        #     return render_template('register.html', error=error)
        
        conn = None
        cur = None
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute('INSERT INTO group_by_counts(group_name, values) VALUES(%s,%s);',(group_name, values,))
            
            conn.commit()
            
        except Exception as e:
            if conn:
                conn.rollback()
                print(f'error:{e}')
                
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
                
        return redirect(url_for('index'))
    
    return render_template('register_group.html')

@app.route('/register_shop', methods=['GET','POST'])
def register_shop():
    if request.method == 'POST':
        shop_name = request.form.get('shop_name')
        
        cur = None
        conn = None
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute('INSERT INTO shops(shop_name) VALUES(%s);',(shop_name,))
            
            conn.commit()
            
        except Exception as e:
            if conn:
                conn.rollback()
                print(f'error:{e}')
                
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
                
        return redirect(url_for('index'))

    return render_template('register_shop.html')

@app.route('/register_category', methods=['GET','POST'])
def register_category():
    if request.method == 'POST':
        category_name = request.form.get('category_name')
        
        cur = None
        conn = None
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('INSERT INTO categories(category_name) VALUES(%s);', (category_name,))
            
            conn.commit()
            
        except Exception as e:
            if conn:
                conn.rollback()
                print(f'error:{e}')
                
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
        return redirect(url_for('index'))
    
    return render_template('register_category.html')


@app.route('/register_product', methods=['GET','POST'])
def register_product():
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        maker = request.form.get('maker')
        category_name = request.form.get('category_name')
        shop_name = request.form.get('shop_name')
        group_name = request.form.get('group_name')
        product_name = request.form.get('product_name')
        provisional_name = request.form.get('provisional_name')
        quantity_box = request.form.get('quantity_box')
        unit_price = request.form.get('unit_price')
        
        cur = None
        conn = None 
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute('INSERT INTO products(product_id, maker, category_name, shop_name, group_name, product_name, provisional_name, quantity_box, unit_price) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);', (product_id, maker, category_name, shop_name, group_name, product_name, provisional_name, quantity_box, unit_price, ) )
            
            conn.commit()
            
            if cur:
                cur.close()
            if conn:
                conn.close()
            
            return redirect(url_for('register_product'))
        
        except Exception as e:
            conn.rollback()
            return f'error:{e}'
        
    return render_template('register_product.html')
            

@app.route('/inventory_in', methods = ('GET','POST'))
def inventory_in():
    if request.method == 'post':
        group_name = request.form.get('group_name')
        product_name = request.form.get('product_name')
        received_quantity = request.form.get('received_quantity')
        
        conn = None
        cur = None
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute('INSERT INTO inventory_in(group_name, product_name,received_quantity) VALUES (%s, %s, %s);', (group_name, product_name,received_quantity,))
            
            conn.commit()
            
            if cur:
                cur.close()
            if conn:
                conn.close()
                
        except Exception as e:
            conn.rollback()
            return f'error:{e}'
        
    
        return redirect(url_for('inventory_in'))
        
    return render_template('inventory_in.html')

@app.route('/import', methods=['GET','POST'])
def import_csv():
    if request.method == 'POST':
        if 'file' not in  request.files:
            return 'ファイルがアップロードされていません',400
        
        file = request.files['file']
        
        cur = None
        conn = None
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            csv_file = TextIOWrapper(file,'utf-8')
            reader = csv.reader(csv_file, quotechar='"')
            
            next(reader)
            
            for row in reader:
                group_name = row[0]
                product_name = row[1]
                received_quantity = row[2]
                
                cur.execute(
                    "INSERT INTO inventory_in(group_name,procduct_name,receiived_quantity) VALUES (%s,%s,%s,NOW());", (group_name,product_name,received_quantity,)
                )
        
            conn.commit()
            
            if cur:
                cur.close()
                
            if conn:
                conn.close()
            
            return redirect(url_for('index'))
            
        except Exception as e:
            conn.rollback()
            return f'error:{e}' 
        
    
    return render_template('import.html')



@app.route('/inventory_out', methods=['GET','POST'])
def inventory_out():
    if request.method == 'POST':
        group_name = request.form.get('group_name')
        provisional_name = request.form.get('provisional_name')
        shipped_quantity = request.form.get('shipped_quantity')
        
        conn = None
        cur = None
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('INSERT INTO inventory_out (group_name,provisioinal_name,shipped_quantity) VALUES (%s,%s,%s);', (group_name,provisional_name,shipped_quantity,))
            
            conn.commit()
            
            if cur:
                cur.close()
            if conn:
                conn.close()
            return redirect(url_for('index'))
        
        except Exception as e:
            conn.rollback()
            return f'error:{e}'
        
    return render_template('inventory_out.html')

@app.route('/provisional_table', methods=['GET','POST'])
def provisional_table():
    if request.method == 'POST':
        group_name = request.form.get('group_name')
        provisional_name = request.form.get('provisional_name')
        
        conn = None
        cur = None
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('INSERT INTO provisional_table(group_name,provisional_name) VALUES(%s,%s);', (group_name, provisional_name,))
            
            conn.commit()
            
            if cur:
                cur.close()
            if conn:
                conn.close()
            return redirect(url_for('index'))
                
        except Exception as e:
            conn.rollback()
            return f'error:{e}'
        
    return render_template('provisional_table.html')

@app.route('/counter_stock')
def counter_stock():
    return render_template('counter_stock.html')

@app.route('/analysis')
def analysis():
    return render_template('analysis.html')


if __name__ == '__main__':
    app.run(debug = True, host = '0.0.0.0', port = 8080)
