from flask import Flask, render_template_string, request, redirect, session
import sqlite3

app = Flask(_name_)
app.secret_key = 'yopis_secret_key'
DB_NAME = 'yopis.db'

# -------------------- قاعدة البيانات --------------------
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        # إضافة عمود is_streaming لتحديد حالة البث
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT DEFAULT '',
            bio TEXT DEFAULT '',
            avatar TEXT DEFAULT 'https://via.placeholder.com/100',
            is_streaming INTEGER DEFAULT 0
        )''')

init_db()

# -------------------- القالب العام --------------------
layout = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>YOPIS - منصة البث</title>
    <style>
        body {{ font-family: Arial; background: #0e0e0e; color: #eee; margin: 0; padding: 0; }}
        nav {{ background: #111; padding: 1em; display: flex; justify-content: space-between; }}
        nav a {{ color: #0af; margin: 0 1em; text-decoration: none; }}
        .container {{ padding: 2em; max-width: 800px; margin: auto; }}
        input, textarea {{ width: 100%; padding: 0.5em; margin: 0.5em 0; border-radius: 5px; border: none; }}
        button {{ padding: 0.5em 1.5em; background: #0af; border: none; color: white; cursor: pointer; border-radius: 5px; }}
        .card {{ background: #1e1e1e; padding: 1em; border-radius: 8px; margin-bottom: 1em; }}
        .stream-list {{ display: flex; flex-wrap: wrap; gap: 1em; }}
        .streamer-card {{ background: #222; padding: 1em; border-radius: 10px; width: 200px; text-align: center; }}
        .streamer-card img {{ border-radius: 50%; width: 100px; height: 100px; object-fit: cover; }}
    </style>
</head>
<body>
    <nav>
        <div><a href="/">🎮 YOPIS</a></div>
        <div>
            <a href="/live">البث المباشر</a>
            {% if 'user' in session %}
                <a href="/profile">ملفي</a>
                <a href="/stream">البث</a>
                <a href="/settings">الإعدادات</a>
                <a href="/logout">خروج</a>
            {% else %}
                <a href="/login">دخول</a>
                <a href="/register">تسجيل</a>
            {% endif %}
        </div>
    </nav>
    <div class="container">
        {{ content }}
    </div>
</body>
</html>
"""

def render(content): return render_template_string(layout, content=content)

# -------------------- الصفحات --------------------

@app.route('/')
def home():
    return render(f"<h1>مرحبًا بك في YOPIS</h1><p>منصة البث الشبيهة بـ Kick</p>")

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ""
    if request.method == 'POST':
        u, p = request.form['username'], request.form['password']
        with sqlite3.connect(DB_NAME) as conn:
            try:
                conn.execute("INSERT INTO users (username, password) VALUES (?,?)", (u, p))
                conn.commit()
                return redirect('/login')
            except:
                msg = "⚠ اسم المستخدم موجود مسبقًا."
    return render(f'''
        <h2>تسجيل حساب جديد</h2>
        <form method="post">
            <input name="username" placeholder="اسم المستخدم" required>
            <input name="password" type="password" placeholder="كلمة المرور" required>
            <button type="submit">تسجيل</button>
        </form><p>{msg}</p>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ""
    if request.method == 'POST':
        u, p = request.form['username'], request.form['password']
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
            user = cur.fetchone()
            if user:
                session['user'] = u
                return redirect('/')
            else:
                msg = "❌ بيانات خاطئة"
    return render(f'''
        <h2>تسجيل الدخول</h2>
        <form method="post">
            <input name="username" placeholder="اسم المستخدم" required>
            <input name="password" type="password" placeholder="كلمة المرور" required>
            <button type="submit">دخول</button>
        </form><p>{msg}</p>
    ''')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/profile')
def profile():
    if 'user' not in session: return redirect('/login')
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT email, bio, avatar FROM users WHERE username=?", (session['user'],))
        email, bio, avatar = cur.fetchone()
    return render(f'''
        <h2>ملفي الشخصي</h2>
        <div class="card">
            <img src="{avatar}" width="100"><br>
            <strong>الاسم:</strong> {session['user']}<br>
            <strong>البريد:</strong> {email}<br>
            <strong>نبذة:</strong> {bio}<br>
        </div>
    ''')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user' not in session: return redirect('/login')
    msg = ""
    if request.method == 'POST':
        email = request.form['email']
        bio = request.form['bio']
        avatar = request.form['avatar']
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute("UPDATE users SET email=?, bio=?, avatar=? WHERE username=?", (email, bio, avatar, session['user']))
            conn.commit()
            msg = "✅ تم التحديث"
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT email, bio, avatar FROM users WHERE username=?", (session['user'],))
        email, bio, avatar = cur.fetchone()
    return render(f'''
        <h2>الإعدادات</h2>
        <form method="post">
            <input name="email" value="{email}" placeholder="البريد الإلكتروني">
            <input name="avatar" value="{avatar}" placeholder="رابط صورة البروفايل">
            <textarea name="bio" placeholder="نبذة عنك...">{bio}</textarea>
            <button type="submit">حفظ</button>
        </form><p>{msg}</p>
    ''')

@app.route('/stream', methods=['GET', 'POST'])
def stream():
    if 'user' not in session: return redirect('/login')
    msg = ""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT is_streaming FROM users WHERE username=?", (session['user'],))
        is_streaming = cur.fetchone()[0]

    if request.method == 'POST':
        # التبديل بين بدء وإيقاف البث
        new_status = 0 if is_streaming == 1 else 1
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute("UPDATE users SET is_streaming=? WHERE username=?", (new_status, session['user']))
            conn.commit()
        return redirect('/stream')

    button_text = "إيقاف البث" if is_streaming == 1 else "بدء البث"
    return render(f'''
        <h2>🎥 بث مباشر</h2>
        <div class="card">
            <p>مرحبًا <b>{session['user']}</b>! يمكنك ربط OBS ببثك هنا لاحقًا.</p>
            <form method="post">
                <button type="submit">{button_text}</button>
            </form>
            <p>حالة البث: <b>{ "يعمل" if is_streaming == 1 else "متوقف" }</b></p>
            <div style="background:#000;height:300px;text-align:center;line-height:300px;color:#777;">[نافذة البث المباشر]</div>
        </div>
    ''')

@app.route('/live')
def live():
    # عرض كل المستخدمين الذين يبثون حاليا (is_streaming=1)
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT username, bio, avatar FROM users WHERE is_streaming=1")
        streamers = cur.fetchall()

    if not streamers:
        content = "<h2>لا يوجد بث مباشر الآن.</h2>"
    else:
        cards = ""
        for u, bio, avatar in streamers:
            cards += f'''
                <div class="streamer-card">
                    <img src="{avatar}" alt="{u}">
                    <h3>{u}</h3>
                    <p>{bio[:50]}...</p>
                    <a href="/stream?user={u}"><button>مشاهدة البث</button></a>
                </div>
            '''
        content = f"<h2>البث المباشر الآن</h2><div class='stream-list'>{cards}</div>"

    return render(content)

if _name_ == '_main_':
    app.run(debug=True)
