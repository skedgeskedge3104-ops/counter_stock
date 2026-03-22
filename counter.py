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

# ポイント景品は在庫 = 入庫×入り数 − 出庫（出庫は入り数を掛けない）
POINT_PRIZE_CATEGORY = "ポイント景品"

# お菓子・ドリンク: タブ式入力し、GROUP 名で両カテゴリ合算表示（一般棚卸一覧からは除外）
SNACK_DRINK_CATEGORIES = ("お菓子", "ドリンク")
SNACK_DRINK_CATEGORY_SET = frozenset(SNACK_DRINK_CATEGORIES)


def _format_ts_display(value):
    """入出庫一覧の日付表示。psycopg2 が datetime でも str でも受け付ける。"""
    if value is None:
        return ''
    if isinstance(value, str):
        s = value.strip().replace('T', ' ')
        if len(s) >= 10 and s[4] == '-' and s[7] == '-':
            y, m, d = s[:10].split('-')
            return f"{y[-2:]},{m},{d}"
        return s
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.strftime('%y,%m,%d')
    return str(value)


@app.template_filter('ts_display')
def ts_display_filter(value):
    return _format_ts_display(value)


def _today_jst_iso():
    return datetime.datetime.now(pytz.timezone("Asia/Tokyo")).date().isoformat()


def _parse_iso_date(s):
    if not s:
        return None
    try:
        return datetime.date.fromisoformat(str(s).strip())
    except (ValueError, TypeError, AttributeError):
        return None


def _add_calendar_months(d, delta):
    """d は月の1日想定。delta ヶ月シフトした月の1日を返す。"""
    mi = d.year * 12 + d.month - 1 + delta
    return datetime.date(mi // 12, mi % 12 + 1, 1)


def _jst_current_month_start():
    now = datetime.datetime.now(pytz.timezone("Asia/Tokyo")).date()
    return datetime.date(now.year, now.month, 1)


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


@app.route('/inventory_in/history')
def inventory_in_history():
    raw = request.args.get("date") or _today_jst_iso()
    view_date = _parse_iso_date(raw) or _parse_iso_date(_today_jst_iso())
    date_str = view_date.isoformat()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT in_id, product_name, group_name, received_quantity, received_day
        FROM inventory_in
        WHERE DATE(timezone('Asia/Tokyo', received_day)) = %s
        ORDER BY received_day DESC, in_id;
        """,
        (view_date,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template(
        "inventory_in_history.html",
        rows=rows,
        selected_date=date_str,
    )


@app.route('/inventory_in/<int:in_id>/edit', methods=["GET", "POST"])
def edit_in(in_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM inventory_in WHERE in_id = %s", (in_id,))
    item = cur.fetchone()
    if not item:
        cur.close()
        conn.close()
        return redirect(url_for("inventory_in"))
    history_date = request.args.get("history_date") or request.form.get("history_date")

    if request.method == "POST":
        received_quantity = request.form.get("received_quantity")
        cur.execute(
            "UPDATE inventory_in SET received_quantity = %s WHERE in_id = %s;",
            (received_quantity, in_id),
        )
        conn.commit()
        cur.close()
        conn.close()
        if history_date and _parse_iso_date(history_date):
            return redirect(url_for("inventory_in_history", date=history_date))
        return redirect(url_for("inventory_in"))

    cur.close()
    conn.close()
    return render_template("edit_in.html", item=item, history_date=history_date)


@app.route("/inventory_in/<int:in_id>/delete", methods=["POST"])
def delete_in(in_id):
    history_date = request.form.get("history_date")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM inventory_in WHERE in_id = %s", (in_id,))
    conn.commit()
    cur.close()
    conn.close()
    if history_date and _parse_iso_date(history_date):
        return redirect(url_for("inventory_in_history", date=history_date))
    return redirect(url_for("inventory_in"))


@app.route('/inventory_in', methods = ('GET','POST'))
def inventory_in():
    category_names = []
    inventory_in = []
    total_in = []
    conn = None
    cur = None

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT category_name FROM categories ORDER BY category_name;')
        category_names = [row[0] for row in cur.fetchall()]

        cur.execute("SELECT * FROM inventory_in WHERE DATE(received_day) = DATE(timezone('Asia/Tokyo',now())); ")
        inventory_in = cur.fetchall()
        
        cur.execute("SELECT p.group_name, SUM(i_in.received_quantity)*p.quantity_box AS 入庫合計 FROM inventory_in AS i_in LEFT JOIN products AS p ON p.product_name = i_in.product_name WHERE DATE(i_in.received_day)=DATE(TIMEZONE('Asia/Tokyo',Now())) GROUP BY i_in.received_quantity,p.group_name, p.quantity_box; ")
        total_in = cur.fetchall()

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
            if conn:
                conn.rollback()
            print(f'error:{e}')
            return f'error:{e}'
        
    
        return redirect(url_for('inventory_in'))
        
    return render_template(
        'inventory_in.html',
        category_names=category_names,
        inventory_in=inventory_in,
        total_in=total_in
    )

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
            if conn:
                conn.rollback()
            return f'error:{e}'

    return render_template('import.html')

# -----------------------------
# 出庫
# -----------------------------


@app.route("/inventory_out/history")
def inventory_out_history():
    raw = request.args.get("date") or _today_jst_iso()
    view_date = _parse_iso_date(raw) or _parse_iso_date(_today_jst_iso())
    date_str = view_date.isoformat()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT out_id, product_name, group_name, shipped_quantity, shipped_day
        FROM inventory_out
        WHERE DATE(timezone('Asia/Tokyo', shipped_day)) = %s
        ORDER BY shipped_day DESC, out_id;
        """,
        (view_date,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template(
        "inventory_out_history.html",
        rows=rows,
        selected_date=date_str,
    )


@app.route('/inventory_out', methods=['GET','POST'])
def inventory_out():
    category_names = []
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT category_name FROM categories ORDER BY category_name;')
        category_names = [row[0] for row in cur.fetchall()]

        cur.execute("SELECT * FROM inventory_out WHERE DATE(shipped_day)=DATE(timezone('Asia/Tokyo',now()));")
        inventory_out = cur.fetchall()

        
        if request.method == 'POST':
            group_name = request.form.get('group_name')
            product_name = request.form.get('product_name')
            shipped_quantity = request.form.get('shipped_quantity')
            
          
            cur.execute("INSERT INTO inventory_out (group_name,product_name,shipped_quantity,shipped_day) VALUES (%s,%s,%s,timezone('Asia/Tokyo', now()));", (group_name,product_name,shipped_quantity,))
            
            conn.commit()
            
            return redirect(url_for('inventory_out'))
            
        return render_template(
            'inventory_out.html',
            category_names=category_names,
            inventory_out=inventory_out
        )
    
    except Exception as e:
        if conn:
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
    if not item:
        cur.close()
        conn.close()
        return redirect(url_for('inventory_out'))

    history_date = request.args.get('history_date') or request.form.get('history_date')

    if request.method =='POST':
        shipped_quantity = request.form.get('shipped_quantity')
        cur.execute('UPDATE inventory_out SET shipped_quantity = %s WHERE out_id=%s;',(shipped_quantity,out_id,))
        conn.commit()
        cur.close()
        conn.close()
        if history_date and _parse_iso_date(history_date):
            return redirect(url_for('inventory_out_history', date=history_date))
        return redirect(url_for('inventory_out'))
        
    cur.close()
    conn.close()
    
    return render_template('edit_out.html', item=item, history_date=history_date)
    
@app.route('/<int:out_id>/delete',methods=['POST'])
def delete_out(out_id):
    history_date = request.form.get('history_date')
    conn=get_db_connection()
    cur=conn.cursor()
    cur.execute('DELETE FROM inventory_out WHERE out_id = %s',(out_id,))
    conn.commit()
    
    cur.close()
    conn.close()
    
    if history_date and _parse_iso_date(history_date):
        return redirect(url_for('inventory_out_history', date=history_date))
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


@app.route('/api/group_names_by_category/<path:category>')
def api_group_names_by_category(category):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT p.group_name
        FROM products p
        INNER JOIN group_by_counts g ON p.group_name = g.group_name
        WHERE p.category_name = %s
        GROUP BY p.group_name, g.group_no
        ORDER BY g.group_no, p.group_name;
        """,
        (category,),
    )
    names = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(names)


@app.route('/get_product_names_for')
def get_product_names_for():
    category = (request.args.get('category') or '').strip()
    group_name = (request.args.get('group_name') or '').strip()
    if not category or not group_name:
        return jsonify([])

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT product_name FROM products
        WHERE category_name = %s AND group_name = %s
        ORDER BY product_no, product_name;
        """,
        (category, group_name),
    )
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
                g.values,
                p.product_name,
                CASE WHEN c.category_name = %s THEN
                    COALESCE(in_sums.total_in, 0) * COALESCE(p.quantity_box, 1)
                    - COALESCE(out_sums.total_out, 0)
                ELSE
                    (COALESCE(in_sums.total_in, 0) - COALESCE(out_sums.total_out, 0))
                END AS stock_count
            FROM products AS p
            JOIN categories AS c ON p.category_name = c.category_name
            JOIN group_by_counts AS g ON p.group_name = g.group_name

            LEFT JOIN (
                SELECT product_name, SUM(received_quantity) AS total_in
                FROM inventory_in
                GROUP BY product_name
            ) AS in_sums ON p.product_name = in_sums.product_name

            LEFT JOIN (
                SELECT product_name, SUM(shipped_quantity) AS total_out
                FROM inventory_out
                GROUP BY product_name
            ) AS out_sums ON p.product_name = out_sums.product_name

            WHERE c.category_name = %s
            AND (
                CASE WHEN c.category_name = %s THEN
                    COALESCE(in_sums.total_in, 0) * COALESCE(p.quantity_box, 1)
                    - COALESCE(out_sums.total_out, 0)
                ELSE
                    (COALESCE(in_sums.total_in, 0) - COALESCE(out_sums.total_out, 0))
                END
            ) != 0
            ORDER BY g.group_no;
        ''', (POINT_PRIZE_CATEGORY, category, POINT_PRIZE_CATEGORY))
        
        rows = cur.fetchall()
        
        items = [
            {
                "category": r[0],
                "group": r[1],
                "point_value": float(r[2]) if r[2] is not None else None,
                "name": r[3],
                "stock": float(r[4])
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
# 棚卸入力画面（カテゴリ別）
# -----------------------------

_INVENTORY_CHECK_PRODUCTS_SQL = """
SELECT
    p.product_name,
    p.group_name,
    (COALESCE(i.total_in, 0) - COALESCE(o.total_out, 0)) * p.quantity_box AS db_stock
FROM products p
LEFT JOIN (
    SELECT product_name, group_name, SUM(received_quantity) AS total_in
    FROM inventory_in GROUP BY product_name, group_name
) i ON p.product_name = i.product_name AND p.group_name = i.group_name
LEFT JOIN (
    SELECT product_name, group_name, SUM(shipped_quantity) AS total_out
    FROM inventory_out GROUP BY product_name, group_name
) o ON p.product_name = o.product_name AND p.group_name = o.group_name
WHERE p.category_name = %s
ORDER BY p.product_no;
"""

# ポイント景品: 商品別在庫 = 入庫×入り数 − 出庫（出庫は入り数を掛けない）をグループで合計
_POINTS_STOCK_BY_GROUP_SQL = """
SELECT
    g.group_name,
    SUM(
        COALESCE(i.total_in, 0) * COALESCE(p.quantity_box, 1) - COALESCE(o.total_out, 0)
    ) AS stock_total
FROM products p
INNER JOIN group_by_counts g ON p.group_name = g.group_name
LEFT JOIN (
    SELECT product_name, group_name, SUM(received_quantity) AS total_in
    FROM inventory_in GROUP BY product_name, group_name
) i ON p.product_name = i.product_name AND p.group_name = i.group_name
LEFT JOIN (
    SELECT product_name, group_name, SUM(shipped_quantity) AS total_out
    FROM inventory_out GROUP BY product_name, group_name
) o ON p.product_name = o.product_name AND p.group_name = o.group_name
WHERE p.category_name = %s
GROUP BY g.group_name, g.group_no
ORDER BY g.group_no;
"""

_DB_STOCK_BY_GROUP_CATEGORY_SQL = """
SELECT
    g.group_name,
    SUM((COALESCE(i.total_in, 0) - COALESCE(o.total_out, 0)) * p.quantity_box) AS db_stock
FROM products p
INNER JOIN group_by_counts g ON p.group_name = g.group_name
LEFT JOIN (
    SELECT product_name, group_name, SUM(received_quantity) AS total_in
    FROM inventory_in GROUP BY product_name, group_name
) i ON p.product_name = i.product_name AND p.group_name = i.group_name
LEFT JOIN (
    SELECT product_name, group_name, SUM(shipped_quantity) AS total_out
    FROM inventory_out GROUP BY product_name, group_name
) o ON p.product_name = o.product_name AND p.group_name = o.group_name
WHERE p.category_name = %s
GROUP BY g.group_name, g.group_no
ORDER BY g.group_no;
"""

_USED_IN_OUT_PRODUCTS_SQL = """
SELECT p.product_name, COALESCE(p.quantity_box, 1) AS quantity_box
FROM products p
WHERE p.category_name = %s AND p.group_name = %s
AND (
    EXISTS (
        SELECT 1 FROM inventory_in i
        WHERE i.product_name = p.product_name AND i.group_name = p.group_name
    )
    OR EXISTS (
        SELECT 1 FROM inventory_out o
        WHERE o.product_name = p.product_name AND o.group_name = p.group_name
    )
)
ORDER BY p.product_no NULLS LAST, p.product_name;
"""


def _build_snack_drink_bootstrap():
    conn = get_db_connection()
    cur = conn.cursor()
    bootstrap = {}
    try:
        for cat in SNACK_DRINK_CATEGORIES:
            cur.execute(_DB_STOCK_BY_GROUP_CATEGORY_SQL, (cat,))
            rows = cur.fetchall()
            groups = []
            for row in rows:
                gn = row[0]
                db_s = row[1]
                cur.execute(_USED_IN_OUT_PRODUCTS_SQL, (cat, gn))
                products = [
                    {
                        "product_name": r[0],
                        "quantity_box": int(r[1]) if r[1] is not None else 1,
                    }
                    for r in cur.fetchall()
                ]
                groups.append({
                    "group_name": gn,
                    "db_stock": float(db_s) if db_s is not None else 0.0,
                    "products": products,
                })
            bootstrap[cat] = groups
    finally:
        cur.close()
        conn.close()
    return bootstrap


def _tab_total_from_entry(entry):
    if not entry:
        return 0.0
    db = float(entry.get("db_stock") or 0)
    adj = 0.0
    for line in entry.get("lines") or []:
        mode = line.get("mode")
        if mode == "product":
            q = int(line.get("quantity") or 0)
            box = int(line.get("quantity_box") or 1)
            adj += q * box
        elif mode == "mul":
            adj += int(line.get("a") or 0) * int(line.get("b") or 0)
        elif mode == "add":
            adj += int(line.get("quantity") or 0)
        elif line.get("product_name") and line.get("op") is not None:
            # 旧形式（互換）
            q = int(line.get("quantity") or 0)
            if line.get("op") == "mul":
                adj += 5 * q
            else:
                adj += q
    return db + adj


def _snack_drink_combined_rows(stored):
    all_groups = set()
    for cat in SNACK_DRINK_CATEGORIES:
        cat_data = stored.get(cat) or {}
        all_groups.update(cat_data.keys())

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT group_name FROM group_by_counts ORDER BY group_no;")
    order = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()

    ordered = [g for g in order if g in all_groups]
    for g in all_groups:
        if g not in ordered:
            ordered.append(g)

    rows = []
    c0, c1 = SNACK_DRINK_CATEGORIES
    for g in ordered:
        e0 = (stored.get(c0) or {}).get(g)
        e1 = (stored.get(c1) or {}).get(g)
        t0 = _tab_total_from_entry(e0)
        t1 = _tab_total_from_entry(e1)
        rows.append({
            "group_name": g,
            "snack_total": t0,
            "drink_total": t1,
            "combined": t0 + t1,
        })
    return rows


@app.route('/inventory_check')
def inventory_check_menu():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT category_name FROM categories ORDER BY category_name;')
    categories = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    menu_categories = [c for c in categories if c not in SNACK_DRINK_CATEGORY_SET]
    return render_template(
        'inventory_check_select.html',
        categories=menu_categories,
        show_snack_drink_link=True,
    )


@app.route('/inventory_check/confirm', methods=['POST'])
def inventory_check_confirm():
    data = request.json
    if not data or 'items' not in data or 'category_name' not in data:
        return jsonify({"status": "error"}), 400
    if data['category_name'] == POINT_PRIZE_CATEGORY:
        return jsonify({"status": "error", "message": "ポイント景品は棚卸の保存対象外です"}), 400
    if data['category_name'] in SNACK_DRINK_CATEGORY_SET:
        return jsonify({
            "status": "error",
            "message": "お菓子・ドリンクは専用の棚卸画面から入力してください",
        }), 400
    session['inventory_check_temp'] = data['items']
    session['inventory_check_category'] = data['category_name']
    return jsonify({"status": "ok"})


@app.route('/inventory_check/result')
def inventory_check_result():
    temp_data = session.get('inventory_check_temp', [])
    category_name = session.get('inventory_check_category', '')
    if not temp_data:
        return redirect(url_for('inventory_check_menu'))

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

    return render_template(
        'inventory_result.html',
        category_name=category_name,
        results=results
    )


@app.route('/inventory_check/final_save', methods=['POST'])
def inventory_check_final_save():
    temp_data = session.get('inventory_check_temp', [])
    category_name = session.get('inventory_check_category', '')
    pos_dict = request.json or {}

    if not temp_data or not category_name:
        return jsonify({"status": "error", "message": "セッションが無効です"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        for row in temp_data:
            g_name = row['group_name']
            group_pos = pos_dict.get(g_name, 0)
            cur.execute("""
                INSERT INTO inventory_check (
                    category_name, product_name, group_name, in_shelf_count,
                    unit_count, pos_stock, check_date
                ) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE)
            """, (
                category_name,
                row['product_name'], row['group_name'],
                row['in_shelf_count'], row['unit_count'], group_pos
            ))

        conn.commit()
        session.pop('inventory_check_temp', None)
        session.pop('inventory_check_category', None)

        return jsonify({"status": "ok"})

    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route('/inventory_check/snack_drink')
def inventory_check_snack_drink():
    bootstrap = _build_snack_drink_bootstrap()
    return render_template(
        'inventory_check_snack_drink.html',
        bootstrap=bootstrap,
        snack_drink_categories=list(SNACK_DRINK_CATEGORIES),
        snack_label=SNACK_DRINK_CATEGORIES[0],
        drink_label=SNACK_DRINK_CATEGORIES[1],
    )


@app.route('/inventory_check/snack_drink/confirm', methods=['POST'])
def inventory_check_snack_drink_confirm():
    data = request.json
    if not data or not isinstance(data, dict):
        return jsonify({"status": "error"}), 400
    cleaned = {}
    for cat in SNACK_DRINK_CATEGORIES:
        cat_in = data.get(cat)
        if not isinstance(cat_in, dict):
            cleaned[cat] = {}
            continue
        cleaned[cat] = {}
        for gname, entry in cat_in.items():
            if not isinstance(entry, dict):
                continue
            lines = []
            for line in entry.get("lines") or []:
                if not isinstance(line, dict):
                    continue
                mode = line.get("mode")
                if mode == "product":
                    pn = line.get("product_name")
                    if not pn:
                        continue
                    lines.append({
                        "mode": "product",
                        "product_name": pn,
                        "quantity": int(line.get("quantity") or 0),
                        "quantity_box": max(1, int(line.get("quantity_box") or 1)),
                    })
                elif mode == "mul":
                    lines.append({
                        "mode": "mul",
                        "a": int(line.get("a") or 0),
                        "b": int(line.get("b") or 0),
                    })
                elif mode == "add":
                    lines.append({
                        "mode": "add",
                        "quantity": int(line.get("quantity") or 0),
                    })
            cleaned[cat][gname] = {
                "db_stock": float(entry.get("db_stock") or 0),
                "lines": lines,
            }
    session['snack_drink_inventory'] = cleaned
    return jsonify({"status": "ok"})


@app.route('/inventory_check/snack_drink/result')
def inventory_check_snack_drink_result():
    stored = session.get('snack_drink_inventory')
    if not stored:
        return redirect(url_for('inventory_check_snack_drink'))
    rows = _snack_drink_combined_rows(stored)
    return render_template(
        'inventory_check_snack_drink_result.html',
        rows=rows,
        snack_label=SNACK_DRINK_CATEGORIES[0],
        drink_label=SNACK_DRINK_CATEGORIES[1],
    )


@app.route("/inventory_check/history")
def inventory_check_history():
    raw = request.args.get("date") or _today_jst_iso()
    view_date = _parse_iso_date(raw) or _parse_iso_date(_today_jst_iso())
    date_str = view_date.isoformat()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT category_name, product_name, group_name,
               in_shelf_count, unit_count, pos_stock, check_date
        FROM inventory_check
        WHERE check_date = %s
        ORDER BY category_name, group_name, product_name;
        """,
        (view_date,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template(
        "inventory_check_history.html",
        rows=rows,
        selected_date=date_str,
    )


@app.route('/inventory_check/<category>')
def inventory_check(category):
    if category in SNACK_DRINK_CATEGORY_SET:
        return redirect(url_for('inventory_check_snack_drink'))

    conn = get_db_connection()
    cur = conn.cursor()

    if category == POINT_PRIZE_CATEGORY:
        cur.execute(_POINTS_STOCK_BY_GROUP_SQL, (category,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        point_groups = [
            {'group_name': r[0], 'stock_total': r[1]}
            for r in rows
        ]
        return render_template(
            'inventory_check_points.html',
            category_name=category,
            point_groups=point_groups
        )

    cur.execute(_INVENTORY_CHECK_PRODUCTS_SQL, (category,))
    db_products = cur.fetchall()
    cur.close()
    conn.close()

    temp_category = session.get('inventory_check_category')
    if temp_category != category:
        session.pop('inventory_check_temp', None)
        session.pop('inventory_check_category', None)
        temp_data = []
    else:
        temp_data = session.get('inventory_check_temp', [])
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

    return render_template(
        'inventory_check.html',
        category_name=category,
        products=products_with_values
    )


@app.route('/tobacco_check')
def tobacco_check():
    return redirect(url_for('inventory_check', category='たばこ'))


@app.route('/tobacco_check/confirm', methods=['POST'])
def tobacco_check_confirm():
    data = request.json
    if not data:
        return jsonify({"status": "error"}), 400
    if isinstance(data, list):
        session['inventory_check_temp'] = data
        session['inventory_check_category'] = 'たばこ'
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 400


@app.route('/tobacco_result')
def tobacco_result():
    return redirect(url_for('inventory_check_result'))


@app.route('/tobacco_check/final_save', methods=['POST'])
def tobacco_final_save():
    return inventory_check_final_save()

# -----------------------------
# 分析（ハブ・原価率・出庫予測）
# -----------------------------


@app.route("/analysis")
def analysis_index():
    return render_template("analysis_index.html")


@app.route("/analysis/cost_ratio")
def analysis_cost_ratio():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """SELECT
        SUM(i.received_quantity * p.unit_price * p.quantity_box)
            / NULLIF(SUM(i.received_quantity * g.values * p.quantity_box), 0) AS 原価率
        FROM inventory_in i
        INNER JOIN products p ON p.product_name = i.product_name
        INNER JOIN group_by_counts g ON g.group_name = p.group_name
        WHERE p.category_name IN %s;
        """,
        (tuple(SNACK_DRINK_CATEGORIES),),
    )
    cost_percentage = cur.fetchone()

    cur.execute(
        """SELECT p.category_name, p.product_name, round(
        COALESCE((p.unit_price / g.values), 0)::NUMERIC, 2) AS 原価率
        FROM products AS p
        INNER JOIN group_by_counts AS g ON p.group_name = g.group_name
        WHERE p.category_name IN %s
        GROUP BY p.category_name, p.product_name, g.values, g.group_name
        ORDER BY CASE p.category_name WHEN %s THEN 0 WHEN %s THEN 1 ELSE 2 END,
            p.product_name;
        """,
        (
            tuple(SNACK_DRINK_CATEGORIES),
            SNACK_DRINK_CATEGORIES[0],
            SNACK_DRINK_CATEGORIES[1],
        ),
    )
    costs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template(
        "analysis_cost_ratio.html",
        cost_percentage=cost_percentage,
        costs=costs,
    )


_OUTBOUND_BY_PRODUCT_SQL = """
SELECT
    p.category_name,
    p.product_name,
    (date_trunc('month', timezone('Asia/Tokyo', o.shipped_day)))::date AS ym,
    SUM(
        CASE WHEN p.category_name = %s
        THEN o.shipped_quantity::numeric
        ELSE (o.shipped_quantity * COALESCE(p.quantity_box, 1))::numeric
        END
    ) AS qty
FROM inventory_out o
INNER JOIN products p
    ON p.product_name = o.product_name AND p.group_name = o.group_name
WHERE p.category_name IN ('たばこ', 'ポイント景品')
  AND date_trunc('month', timezone('Asia/Tokyo', o.shipped_day))
      >= date_trunc('month', timezone('Asia/Tokyo', now())) - interval '36 months'
GROUP BY p.category_name, p.product_name, ym
ORDER BY p.category_name, p.product_name, ym;
"""

_OUTBOUND_SNACK_DRINK_BY_GROUP_SQL = """
SELECT
    p.group_name,
    (date_trunc('month', timezone('Asia/Tokyo', o.shipped_day)))::date AS ym,
    SUM((o.shipped_quantity * COALESCE(p.quantity_box, 1))::numeric) AS qty
FROM inventory_out o
INNER JOIN products p
    ON p.product_name = o.product_name AND p.group_name = o.group_name
WHERE p.category_name IN ('お菓子', 'ドリンク')
  AND date_trunc('month', timezone('Asia/Tokyo', o.shipped_day))
      >= date_trunc('month', timezone('Asia/Tokyo', now())) - interval '36 months'
GROUP BY p.group_name, ym
ORDER BY p.group_name, ym;
"""


def _month_label(d):
    return f"{d.year}年{d.month}月"


@app.route("/analysis/outbound_forecast")
def analysis_outbound_forecast():
    cur_m = _jst_current_month_start()
    display_months = [_add_calendar_months(cur_m, -11 + i) for i in range(12)]
    prev_year_month = _add_calendar_months(cur_m, -12)
    prev_block_months = [_add_calendar_months(cur_m, -23 + i) for i in range(12)]
    month_labels = [_month_label(m) for m in display_months]

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(_OUTBOUND_BY_PRODUCT_SQL, (POINT_PRIZE_CATEGORY,))
    prod_rows = cur.fetchall()
    cur.execute(_OUTBOUND_SNACK_DRINK_BY_GROUP_SQL)
    group_rows = cur.fetchall()
    cur.close()
    conn.close()

    def norm_ym(v):
        if v is None:
            return None
        if isinstance(v, datetime.datetime):
            return datetime.date(v.year, v.month, 1)
        if isinstance(v, datetime.date):
            return datetime.date(v.year, v.month, 1)
        return v

    # たばこ / ポイント景品: (category, product) -> {ym: qty}
    prod_map = {}
    for cat, pname, ym, qty in prod_rows:
        key = (cat, pname)
        prod_map.setdefault(key, {})
        prod_map[key][norm_ym(ym)] = float(qty or 0)

    tobacco_rows = []
    point_rows = []
    for key in sorted(prod_map.keys()):
        cat, pname = key
        mq = prod_map[key]
        vals = [mq.get(m, 0.0) for m in display_months]
        if cat == "たばこ":
            tobacco_rows.append({"product_name": pname, "months": vals})
        else:
            point_rows.append({"product_name": pname, "months": vals})

    # お菓子+ドリンク: group -> {ym: qty}
    grp_map = {}
    for gname, ym, qty in group_rows:
        grp_map.setdefault(gname, {})
        grp_map[gname][norm_ym(ym)] = float(qty or 0)

    snack_group_rows = []
    for gname in sorted(grp_map.keys()):
        mqty = grp_map[gname]
        vals_12 = [mqty.get(m, 0.0) for m in display_months]
        sum_12 = sum(vals_12)
        avg_12 = sum_12 / 12.0 if display_months else 0.0
        prev_y_val = mqty.get(prev_year_month, 0.0)
        curr_val = vals_12[-1] if vals_12 else 0.0
        if prev_y_val > 0:
            yoy_pct = (curr_val / prev_y_val - 1.0) * 100.0
        else:
            yoy_pct = None
        sum_prev = sum(mqty.get(m, 0.0) for m in prev_block_months)
        if sum_prev > 0:
            trend = sum_12 / sum_prev
            pred = prev_y_val * trend
        else:
            trend = None
            pred = avg_12 if avg_12 else None

        snack_group_rows.append({
            "group_name": gname,
            "months": vals_12,
            "avg_12": round(avg_12, 2),
            "prev_year_same": round(prev_y_val, 2),
            "yoy_pct": round(yoy_pct, 2) if yoy_pct is not None else None,
            "prediction": round(pred, 2) if pred is not None else None,
        })

    return render_template(
        "analysis_outbound_forecast.html",
        month_labels=month_labels,
        display_months=display_months,
        tobacco_rows=tobacco_rows,
        point_rows=point_rows,
        snack_group_rows=snack_group_rows,
        as_of_month=_month_label(cur_m),
    )


# -----------------------------
# 窪田主任用ページ
# -----------------------------

@app.route('/kubota')
def kubota():
    conn=get_db_connection()
    cur = conn.cursor()
    
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
