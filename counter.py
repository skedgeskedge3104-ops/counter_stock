import os
import psycopg2
from flask import Flask, render_template,request,redirect,url_for,jsonify
from io import TextIOWrapper
import csv
import datetime
import pytz

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
    conn = None
    cur = None
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM group_by_counts;')
    group_by_counts = cur.fetchall()
    cur.close()
    conn.close()
    
    if request.method == 'POST':
        group_name = request.form.get('group_name')
        values = request.form.get('values')

        
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
                
        return redirect(url_for('register_group'))
    
    return render_template('register_group.html',group_by_counts = group_by_counts)

@app.route('/register_shop', methods=['GET','POST'])
def register_shop():
    conn = None
    cur = None
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM shops;')
    shops = cur.fetchall()
    
    cur.close()
    conn.close()

    
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
                
        return redirect(url_for('register_shop'))

    return render_template('register_shop.html', shops = shops)

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
    if request.method =='GET':
        group_names = []
        category_names = []
        shop_names = []
        provisional_names = []
        conn = None
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute('SELECT group_name FROM group_by_counts;')
            group_names = [row[0] for row in cur.fetchall()]
            
            cur.execute('SELECT category_name FROM categories;')
            category_names = [row[0] for row in cur.fetchall()]
            
            cur.execute('SELECT shop_name FROM shops;')
            shop_names = [row[0] for row in cur.fetchall()]
            
            cur.close()
            
        except Exception as e:
            print(f'error:{e}')
            
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
        return render_template('register_product.html', group_names=group_names, category_names = category_names,shop_names = shop_names)
    
    elif request.method == 'POST':
        product_id = request.form.get('product_id')
        maker = request.form.get('maker')
        category_name = request.form.get('category_name')
        shop_name = request.form.get('shop_name')
        group_name = request.form.get('group_name')
        product_name = request.form.get('product_name')
        quantity_box = request.form.get('quantity_box')
        unit_price = request.form.get('unit_price')
        
        cur = None
        conn = None 
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute("INSERT INTO products(product_id, maker, category_name, shop_name, group_name, product_name, quantity_box, unit_price,expiry_date) VALUES (%s, %s, %s,  %s, %s, %s, %s, %s, timezone('Asia/Tokyo',now()));", (product_id, maker, category_name, shop_name, group_name, product_name, quantity_box, unit_price,))
            
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
    group_names =  []
    product_names = []
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT * FROM group_by_counts;')
        group_names = [row[1] for row in cur.fetchall()]
        
        cur.execute('SELECT product_name FROM products;')
        product_names = [row[0] for row in cur.fetchall()]
        
        cur.execute("SELECT * FROM inventory_in WHERE DATE(received_day) = DATE(timezone('Asia/Tokyo',now())); ")
        
        inventory_in = cur.fetchall()
        
        cur.close()
        
    except Exception as e:
        print(f'error:{e}')
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            
    if request.method == 'POST':
        group_name = request.form.get('group_name')
        product_name = request.form.get('product_name')
        received_quantity = request.form.get('received_quantity')
        
        conn = None
        cur = None
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute("INSERT INTO inventory_in(group_name, product_name,received_quantity,received_day) VALUES (%s, %s, %s, timezone('Asia/Tokyo',now()));", (group_name, product_name,received_quantity,))
            
            conn.commit()
            
            if cur:
                cur.close()
            if conn:
                conn.close()
                
        except Exception as e:
            conn.rollback()
            print(f'error:{e}')
            return f'error:{e}'
        
    
        return redirect(url_for('inventory_in'))
        
    return render_template('inventory_in.html', group_names = group_names, product_names = product_names, inventory_in = inventory_in)

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
    group_names = []
    provisional_names = []
    
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT * FROM group_by_counts;')
        group_names = [row[1] for row in cur.fetchall()]
        
        cur.execute('SELECT provisional_name FROM provisional_table;')
        provisional_names = [row[0] for row in cur.fetchall()]
        
        cur.execute("SELECT * FROM inventory_out WHERE DATE(shipped_day)=DATE(timezone('Asia/Tokyo',now()));")
        inventory_out = cur.fetchall()

        
        if request.method == 'POST':
            group_name = request.form.get('group_name')
            provisional_name = request.form.get('provisional_name')
            shipped_quantity = request.form.get('shipped_quantity')
            
          
            cur.execute("INSERT INTO inventory_out (group_name,provisional_name,shipped_quantity,shipped_day) VALUES (%s,%s,%s,timezone('Asia/Tokyo', now()));", (group_name,provisional_name,shipped_quantity,))
            
            conn.commit()
            
            return redirect(url_for('inventory_out'))
            
        return render_template('inventory_out.html', group_names=group_names, provisional_names=provisional_names, inventory_out = inventory_out)
    
    except Exception as e:
                conn.rollback()
                return f'error:{e}'
            
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()     
            
@app.route('/<int:out_id>/edit_out',methods=['GET','POST'])            
def edit_out(out_id):
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM inventory_out WHERE out_id = %s',(out_id,))
    item = cur.fetchone()
    
    if request.method =='POST':
        shipped_quantity = request.form.get('shipped_quantity')
        cur.execute('UPDATE inventory_out SET shipped_quantity = %s WHERE out_id=%s;',(shipped_quantity,out_id,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('inventory_out'))
        
    cur.close()
    conn.close()
    
    return render_template('edit_out.html', item=item)
    
@app.route('/<int:out_id>/delete',methods=['POST'])
def delete_out(out_id):
    
    conn=get_db_connection()
    cur=conn.cursor()
    cur.execute('DELETE FROM inventory_out WHERE out_id = %s',(out_id,))
    conn.commit()
    
    cur.close()
    conn.close()
    
    return redirect(url_for('inventory_out'))
            

               
@app.route('/get_provisional_names/<group_name>')
def get_provisional_names(group_name):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 選択されたgroup_nameに紐づく商品名だけを取得
    cur.execute('SELECT provisional_name FROM provisional_table WHERE group_name = %s;', (group_name,))
    provisional_names = [row[0] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    # PythonのリストをJSON形式（JavaScriptが読める形式）で返す
    return jsonify(provisional_names)

@app.route('/get_product_names/<group_name>')
def get_product_names(group_name):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT product_name FROM products WHERE group_name = %s;',(group_name,))
    product_names = [row[0] for row in cur.fetchall()]
    
    cur.close()
    conn.close()    
    
    return jsonify(product_names)
    

@app.route('/provisional_table', methods=['GET','POST'])
def provisional_table():
    group_names = []
    
    conn = None
    cur = None
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT * FROM group_by_counts;')
    group_names = [row[1] for row in cur.fetchall()]
    
    cur.execute('SELECT * FROM provisional_table ORDER BY group_name;')
    provisional = cur.fetchall()
    
    cur.close()
    conn.close()
    
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
            return redirect(url_for('provisional_table'))
                
        except Exception as e:
            conn.rollback()
            return f'error:{e}'
        
    return render_template('provisional_table.html', provisional = provisional,  group_names = group_names)


@app.route('/counter_stock')
def counter_stock():
    conn = None
    cur = None
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM products;')
        
        items = cur.fetchall()
        
    except Exception as e:
        print(f'error:{e}')
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            
    return render_template('counter_stock.html', items = items)

@app.route('/analysis')
def analysis():
    return render_template('analysis.html')


if __name__ == '__main__':
    app.run(debug = True, host = '0.0.0.0', port = 8081)
