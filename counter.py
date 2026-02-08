import os
import psycopg2
from flask import Flask, render_template,request,redirect,url_for,jsonify,session
from io import TextIOWrapper
import csv
import datetime
import pytz


# -----------------------------
# 初期設定
# -----------------------------

app=Flask(__name__)
app.secret_key = "super-secret-key"


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

# -----------------------------
# 登録関係
# -----------------------------

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


# -----------------------------
# 入庫
# -----------------------------            

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
        
        cur.execute("SELECT p.group_name, SUM(i_in.received_quantity)*p.quantity_box AS 入庫合計 FROM inventory_in AS i_in LEFT JOIN products AS p ON p.product_name = i_in.product_name WHERE DATE(i_in.received_day)=DATE(TIMEZONE('Asia/Tokyo',Now())) GROUP BY i_in.received_quantity,p.group_name, p.quantity_box; ")
        total_in = cur.fetchall()
        
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
        
    return render_template('inventory_in.html', group_names = group_names, product_names = product_names, inventory_in = inventory_in , total_in=total_in)

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

# -----------------------------
# 出庫
# -----------------------------

@app.route('/inventory_out', methods=['GET','POST'])
def inventory_out():
    group_names = []
    
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT * FROM group_by_counts;')
        group_names = [row[1] for row in cur.fetchall()]
        
        cur.execute('SELECT product_name FROM products;')
        product_names = [row[0] for row in cur.fetchall()]
        
        cur.execute("SELECT * FROM inventory_out WHERE DATE(shipped_day)=DATE(timezone('Asia/Tokyo',now()));")
        inventory_out = cur.fetchall()

        
        if request.method == 'POST':
            group_name = request.form.get('group_name')
            product_name = request.form.get('product_name')
            shipped_quantity = request.form.get('shipped_quantity')
            
          
            cur.execute("INSERT INTO inventory_out (group_name,product_name,shipped_quantity,shipped_day) VALUES (%s,%s,%s,timezone('Asia/Tokyo', now()));", (group_name,product_name,shipped_quantity,))
            
            conn.commit()
            
            return redirect(url_for('inventory_out'))
            
        return render_template('inventory_out.html', group_names=group_names, product_names=product_names, inventory_out = inventory_out)
    
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
            

@app.route('/get_product_names/<group_name>')
def get_product_names(group_name):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT product_name FROM products WHERE group_name = %s;',(group_name,))
    product_names = [row[0] for row in cur.fetchall()]
    
    cur.close()
    conn.close()    
    
    return jsonify(product_names)


# -----------------------------
# 在庫確認画面
# -----------------------------   

@app.route('/counter_stock')
def counter_stock():
    return render_template('counter_stock.html')

@app.route('/api/get_stock/<category>')
def api_get_stock(category):
    items = []
    conn = None
    cur = None
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
    
        cur.execute('''
            SELECT 
                c.category_name, 
                g.group_name, 
                p.product_name,
                (COALESCE(in_sums.total_in, 0) - COALESCE(out_sums.total_out, 0)) AS stock_count
            FROM products AS p
            JOIN categories AS c ON p.category_name = c.category_name
            JOIN group_by_counts AS g ON p.group_name = g.group_name
            
            -- 入庫の合計
            LEFT JOIN (
                SELECT product_name, SUM(received_quantity) AS total_in
                FROM inventory_in
                GROUP BY product_name
            ) AS in_sums ON p.product_name = in_sums.product_name
            
            -- 出庫の合計
            LEFT JOIN (
                SELECT product_name, SUM(shipped_quantity) AS total_out
                FROM inventory_out
                GROUP BY product_name
            ) AS out_sums ON p.product_name = out_sums.product_name
            
            -- 指定されたカテゴリで絞り込み
            WHERE c.category_name = %s
            AND (COALESCE(in_sums.total_in, 0) - COALESCE(out_sums.total_out, 0)) != 0
            ORDER BY g.group_no;
        ''', (category,))
        
        rows = cur.fetchall()
        
        items = [
            {
                "category": r[0],
                "group": r[1],
                "name": r[2],
                "stock": float(r[3]) 
            } for r in rows
        ]
        
        return jsonify(items)

    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
        
    finally:
        if cur: cur.close()
        if conn: conn.close()

# -----------------------------
# 玉数別在庫確認画面
# -----------------------------   

@app.route('/group_by_counts_stock')
def group_by_counts():
    conn=get_db_connection()
    cur=conn.cursor()
    
    cur.execute("""
                SELECT g.group_name, COALESCE(SUM(i.total_in - COALESCE(o.total_out, 0)), 0) AS 合計 FROM group_by_counts AS g
                INNER JOIN 
                (
                    SELECT p.group_name, COALESCE(SUM(i_in.received_quantity * p.quantity_box), 0) AS total_in FROM inventory_in AS i_in
                    LEFT JOIN products AS p ON p.product_name = i_in.product_name WHERE p.category_name = 'お菓子'
                    GROUP BY p.group_name
                ) AS i ON g.group_name = i.group_name
                LEFT JOIN
                (
                   SELECT p.group_name,COALESCE(SUM(i_out.shipped_quantity * p.quantity_box),0) AS total_out FROM inventory_out AS i_out
                   LEFT JOIN products AS p ON p.product_name = i_out.product_name WHERE p.category_name = 'お菓子'
                   GROUP BY p.group_name 
                ) AS o ON g.group_name = o.group_name
                GROUP BY g.group_name ORDER BY g.group_no;  
                """)
    counts = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('group_by_counts_stock.html', counts=counts)


# -----------------------------
# 棚卸入力画面
# -----------------------------

@app.route('/tobacco_check')
def tobacco_check():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""SELECT 
    p.product_name, 
    p.group_name,
    (COALESCE(i.total_in, 0) - COALESCE(o.total_out, 0)) * p.quantity_box AS db_stock
FROM products p
LEFT JOIN (
    -- 先に入庫だけを合計する
    SELECT product_name, group_name, SUM(received_quantity) as total_in 
    FROM inventory_in GROUP BY product_name, group_name
) i ON p.product_name = i.product_name AND p.group_name = i.group_name
LEFT JOIN (
    -- 先に出庫だけを合計する
    SELECT product_name, group_name, SUM(shipped_quantity) as total_out 
    FROM inventory_out GROUP BY product_name, group_name
) o ON p.product_name = o.product_name AND p.group_name = o.group_name
WHERE p.category_name = 'たばこ'
ORDER BY p.product_no; """)
    db_products = cur.fetchall()
    cur.close()
    conn.close()

    temp_data = session.get('tobacco_temp', [])
    
    temp_dict = {item['product_name']: item for item in temp_data}

    products_with_values = []
    for p in db_products:
        name = p[0]
        
        in_shelf = temp_dict.get(name, {}).get('in_shelf_count', 0)
        unit_count = temp_dict.get(name, {}).get('unit_count', 0)
        
        products_with_values.append({
            'product_name': p[0],
            'group_name': p[1],
            'db_stock': p[2],
            'in_shelf_count': in_shelf,
            'unit_count': unit_count
        })

    return render_template('tobacco_check.html', products=products_with_values)

@app.route('/tobacco_check/confirm', methods=['POST'])
def tobacco_check_confirm():
    data = request.json
    if not data:
        return jsonify({"status": "error"}), 400
    session['tobacco_temp'] = data 
    return jsonify({"status": "ok"})


@app.route('/tobacco_result')
def tobacco_result():
    temp_data = session.get('tobacco_temp', [])
    

    summary_dict = {} 
    
    for item in temp_data:
        g_name = item['group_name']

        actual_val = (
            int(item.get('in_shelf_count', 0)) + 
            int(item.get('unit_count', 0)) + 
            int(item.get('db_stock', 0))
        )
        
        if g_name not in summary_dict:
            summary_dict[g_name] = 0
        summary_dict[g_name] += actual_val

    results = [[group, total] for group, total in summary_dict.items()]

    return render_template('tobacco_result.html', results=results)

@app.route('/tobacco_check/final_save', methods=['POST'])
def tobacco_final_save():
    temp_data = session.get('tobacco_temp', [])
    pos_dict = request.json
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        for row in temp_data:
            g_name = row['group_name']
            group_pos = pos_dict.get(g_name, 0)
            
            cur.execute("""
                INSERT INTO tobacco_inventory_check (
                    product_name, group_name, in_shelf_count, 
                    unit_count, pos_stock, check_date
                ) VALUES (%s, %s, %s, %s, %s, CURRENT_DATE)
            """, (
                row['product_name'], row['group_name'], 
                row['in_shelf_count'], row['unit_count'], group_pos
            ))
        
        conn.commit()
        session.pop('tobacco_temp', None) 
        
        return jsonify({"status": "ok"})
        
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cur.close()
        conn.close()

# -----------------------------
# 原価率計算と表示
# -----------------------------


@app.route('/analysis')
def analysis():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''SELECT
        SUM(i.received_quantity * p.unit_price * p.quantity_box) / SUM(i.received_quantity * g.values * p.quantity_box) AS 原価率
        FROM inventory_in i
        INNER JOIN products p
        ON p.product_name = i.product_name
        INNER JOIN group_by_counts g
        ON g.group_name = p.group_name
        WHERE p.category_name != 'たばこ';
        ''')
    
    cost_percentage = cur.fetchone()
    
    cur.execute('''SELECT p.product_name,  round(
        COALESCE((p.unit_price / g.values), 0)::NUMERIC,2) AS 原価率 FROM products as p
        INNER JOIN group_by_counts  AS g ON p.group_name = g.group_name
        WHERE p.category_name != 'たばこ'
        GROUP BY p.product_name,g.values,g.group_name
        ORDER BY 原価率 DESC;
        ''')
    
    costs = cur.fetchall()
    
    cur.close()
    conn.close()
    
    
    return render_template('analysis.html',cost_percentage=cost_percentage, costs=costs)


# -----------------------------
# 窪田主任用ページ
# -----------------------------

@app.route('/kubota')
def kubota():
    conn=get_db_connection()
    cur = conn.corsor()
    
    cur.execute('''
                select p.shop_name,p.group_name,p.product_name,p.quantity_box,p.unit_price,(coalesce(i.total_in,0)-coalesce(o.total_out,0))*coalesce(p.quantity_box) as total_counts
                from products as p 
                inner join 
                (select product_name ,sum(coalesce(received_quantity,0)) as total_in from inventory_in group by product_name) as i
                on p.product_name = i.product_name
                inner join
                (select product_name, sum(coalesce(shipped_quantity,0))as total_out from inventory_out group by product_name) as o
                on p.product_name = o.product_name
                where p.category_name!= 'たばこ'
                order by p.shop_name;
                ''')
    
    kubotas = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('kubota.html',kubotas=kubotas)


if __name__ == '__main__':
    app.run(debug = True, host = '0.0.0.0', port = 8081)
