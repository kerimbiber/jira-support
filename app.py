from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import pandas as pd
import re
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename
import io
import base64
import requests as http_requests

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}
app.config['NOTES_PER_PAGE'] = 10

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'notes.db')

# Upload klasörünü oluştur
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'Genel',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL DEFAULT 'Genel',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sql_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            purpose TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            sql_code TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS jira_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jira_url TEXT NOT NULL,
            email TEXT NOT NULL,
            api_token TEXT NOT NULL,
            project_key TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def convert_time_format(time_str):
    """Time string'i yeni formata çevirir"""
    time_str = str(time_str).strip()
    
    if pd.isna(time_str) or time_str == 'nan':
        return None
    
    is_negative = time_str.startswith('-')
    if is_negative:
        time_str = time_str.replace('-', '').strip()
    
    hours = 0
    minutes = 0
    
    hour_match = re.search(r'(\d+)\s*sa\.', time_str)
    minute_match = re.search(r'(\d+)\s*dk\.', time_str)
    
    if hour_match:
        hours = int(hour_match.group(1))
    if minute_match:
        minutes = int(minute_match.group(1))
    
    if is_negative:
        return f'-{hours}.{minutes:02d}'
    else:
        return f'{hours}.{minutes:02d}'

def format_to_minutes(time_str):
    """Saat.dakika formatını toplam dakikaya çevirir"""
    if pd.isna(time_str) or time_str == '':
        return None
    time_str = str(time_str).strip()
    is_negative = time_str.startswith('-')
    if is_negative:
        time_str = time_str.replace('-', '').strip()
    
    parts = time_str.split('.')
    hours = int(parts[0]) if parts[0] else 0
    minutes = int(parts[1]) if len(parts) > 1 else 0
    
    total_minutes = hours * 60 + minutes
    return -total_minutes if is_negative else total_minutes

def minutes_to_format(total_minutes):
    """Toplam dakikayı saat.dakika formatına çevirir"""
    if pd.isna(total_minutes):
        return None
    total_minutes = float(total_minutes)
    is_negative = total_minutes < 0
    abs_minutes = abs(total_minutes)
    hours = int(abs_minutes // 60)
    minutes = int(abs_minutes % 60)
    
    if is_negative:
        return f'-{hours}.{minutes:02d}'
    else:
        return f'{hours}.{minutes:02d}'

def process_excel(file_path):
    """Excel dosyasını işle"""
    try:
        # Excel dosyasını oku
        df = pd.read_excel(file_path, sheet_name='Your Jira Issues')
        
        # Time to resolution dönüştür
        df['Time to resolution (New Format)'] = df['Time to resolution'].apply(convert_time_format)
        
        # Müdahale SLA dönüştür
        mudahale_sla_col = df.columns[5]
        df['Müdahale SLA (New Format)'] = df[mudahale_sla_col].apply(convert_time_format)
        
        # Hesaplamalar
        # Müdahale SLA hesaplama
        target_mudahale = 30
        df['Müdahale SLA (Hesaplama)'] = df['Müdahale SLA (New Format)'].apply(
            lambda x: minutes_to_format(target_mudahale - format_to_minutes(x)) if pd.notna(x) else None
        )
        
        # Time to resolution hesaplama
        target_resolution = 8 * 60
        df['Time to resolution (Hesaplama)'] = df['Time to resolution (New Format)'].apply(
            lambda x: minutes_to_format(target_resolution - format_to_minutes(x)) if pd.notna(x) else None
        )
        
        # Sonuç hesaplama
        def add_calculations(row):
            mudahale = format_to_minutes(row['Müdahale SLA (Hesaplama)'])
            resolution = format_to_minutes(row['Time to resolution (Hesaplama)'])
            if pd.isna(mudahale) or pd.isna(resolution):
                return None
            total_minutes = mudahale + resolution
            return minutes_to_format(total_minutes)
        
        df['Sonuç'] = df.apply(add_calculations, axis=1)
        
        # About sayfasını oku
        try:
            about_df = pd.read_excel(file_path, sheet_name='About')
        except:
            about_df = pd.DataFrame()
        
        # Yeni dosya oluştur
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Your Jira Issues', index=False)
            if not about_df.empty:
                about_df.to_excel(writer, sheet_name='About', index=False)
        
        output.seek(0)
        return output, len(df)
        
    except Exception as e:
        raise Exception(f"İşlem hatası: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('Dosya seçilmedi!', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('Dosya seçilmedi!', 'error')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            output, record_count = process_excel(filepath)
            
            # Geçici dosyayı sil
            os.remove(filepath)
            
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'processed_{filename}'
            )
        except Exception as e:
            # Hata durumunda dosyayı sil
            if os.path.exists(filepath):
                os.remove(filepath)
            flash(f'Hata: {str(e)}', 'error')
            return redirect(url_for('index'))
    else:
        flash('Geçersiz dosya formatı! Sadece .xlsx ve .xls dosyaları kabul edilir.', 'error')
        return redirect(url_for('index'))

CATEGORIES = ['Genel', 'Prosedür', 'Hata/Bug', 'Döküman', 'İpucu']


@app.route('/notes')
def notes_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    per_page = app.config['NOTES_PER_PAGE']

    conn = get_db()
    params = []
    where = "WHERE 1=1"
    if search:
        where += " AND (title LIKE ? OR content LIKE ?)"
        params += [f'%{search}%', f'%{search}%']
    if category:
        where += " AND category = ?"
        params.append(category)

    total = conn.execute(f"SELECT COUNT(*) FROM notes {where}", params).fetchone()[0]
    notes = conn.execute(
        f"SELECT * FROM notes {where} ORDER BY updated_at DESC LIMIT ? OFFSET ?",
        params + [per_page, (page - 1) * per_page]
    ).fetchall()
    conn.close()

    total_pages = max(1, (total + per_page - 1) // per_page)
    return render_template(
        'notes.html',
        notes=notes,
        page=page,
        total_pages=total_pages,
        search=search,
        category=category,
        categories=CATEGORIES,
        total=total,
    )


@app.route('/notes/new', methods=['GET', 'POST'])
def note_new():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', 'Genel').strip()
        if not title or not content:
            flash('Başlık ve içerik zorunludur.', 'error')
            return render_template('note_form.html', categories=CATEGORIES,
                                   note=None, title=title, content=content, category=category)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = get_db()
        conn.execute(
            "INSERT INTO notes (title, content, category, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (title, content, category, now, now)
        )
        conn.commit()
        conn.close()
        flash('Not başarıyla oluşturuldu.', 'success')
        return redirect(url_for('notes_list'))
    return render_template('note_form.html', categories=CATEGORIES, note=None,
                           title='', content='', category='Genel')


@app.route('/notes/<int:note_id>')
def note_detail(note_id):
    conn = get_db()
    note = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    conn.close()
    if note is None:
        flash('Not bulunamadı.', 'error')
        return redirect(url_for('notes_list'))
    return render_template('note_detail.html', note=note)


@app.route('/notes/<int:note_id>/edit', methods=['GET', 'POST'])
def note_edit(note_id):
    conn = get_db()
    note = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    conn.close()
    if note is None:
        flash('Not bulunamadı.', 'error')
        return redirect(url_for('notes_list'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', 'Genel').strip()
        if not title or not content:
            flash('Başlık ve içerik zorunludur.', 'error')
            return render_template('note_form.html', categories=CATEGORIES,
                                   note=note, title=title, content=content, category=category)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = get_db()
        conn.execute(
            "UPDATE notes SET title=?, content=?, category=?, updated_at=? WHERE id=?",
            (title, content, category, now, note_id)
        )
        conn.commit()
        conn.close()
        flash('Not başarıyla güncellendi.', 'success')
        return redirect(url_for('note_detail', note_id=note_id))

    return render_template('note_form.html', categories=CATEGORIES, note=note,
                           title=note['title'], content=note['content'], category=note['category'])


@app.route('/notes/<int:note_id>/delete', methods=['POST'])
def note_delete(note_id):
    conn = get_db()
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    flash('Not silindi.', 'success')
    return redirect(url_for('notes_list'))


LINK_CATEGORIES = ['Genel', 'Swagger', 'Panel', 'Dashboard', 'API', 'Araç', 'Döküman', 'Diğer']


@app.route('/links')
def links_list():
    search = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    conn = get_db()
    params = []
    where = "WHERE 1=1"
    if search:
        where += " AND (title LIKE ? OR description LIKE ? OR url LIKE ?)"
        params += [f'%{search}%', f'%{search}%', f'%{search}%']
    if category:
        where += " AND category = ?"
        params.append(category)

    total = conn.execute(f"SELECT COUNT(*) FROM links {where}", params).fetchone()[0]
    links = conn.execute(
        f"SELECT * FROM links {where} ORDER BY category ASC, title ASC",
        params
    ).fetchall()
    conn.close()

    return render_template(
        'links.html',
        links=links,
        search=search,
        category=category,
        categories=LINK_CATEGORIES,
        total=total,
    )


@app.route('/links/new', methods=['GET', 'POST'])
def link_new():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        url = request.form.get('url', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'Genel').strip()
        if not title or not url:
            flash('Başlık ve URL zorunludur.', 'error')
            return render_template('link_form.html', categories=LINK_CATEGORIES,
                                   link=None, title=title, url=url,
                                   description=description, category=category)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = get_db()
        conn.execute(
            "INSERT INTO links (title, url, description, category, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (title, url, description, category, now, now)
        )
        conn.commit()
        conn.close()
        flash('Link başarıyla eklendi.', 'success')
        return redirect(url_for('links_list'))
    return render_template('link_form.html', categories=LINK_CATEGORIES, link=None,
                           title='', url='', description='', category='Genel')


@app.route('/links/<int:link_id>/edit', methods=['GET', 'POST'])
def link_edit(link_id):
    conn = get_db()
    link = conn.execute("SELECT * FROM links WHERE id = ?", (link_id,)).fetchone()
    conn.close()
    if link is None:
        flash('Link bulunamadı.', 'error')
        return redirect(url_for('links_list'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        url = request.form.get('url', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'Genel').strip()
        if not title or not url:
            flash('Başlık ve URL zorunludur.', 'error')
            return render_template('link_form.html', categories=LINK_CATEGORIES,
                                   link=link, title=title, url=url,
                                   description=description, category=category)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = get_db()
        conn.execute(
            "UPDATE links SET title=?, url=?, description=?, category=?, updated_at=? WHERE id=?",
            (title, url, description, category, now, link_id)
        )
        conn.commit()
        conn.close()
        flash('Link başarıyla güncellendi.', 'success')
        return redirect(url_for('links_list'))

    return render_template('link_form.html', categories=LINK_CATEGORIES, link=link,
                           title=link['title'], url=link['url'],
                           description=link['description'], category=link['category'])


@app.route('/links/<int:link_id>/delete', methods=['POST'])
def link_delete(link_id):
    conn = get_db()
    conn.execute("DELETE FROM links WHERE id = ?", (link_id,))
    conn.commit()
    conn.close()
    flash('Link silindi.', 'success')
    return redirect(url_for('links_list'))


@app.route('/sql-queries')
def sql_queries_list():
    search = request.args.get('q', '').strip()

    conn = get_db()
    params = []
    where = "WHERE 1=1"
    if search:
        where += " AND (title LIKE ? OR purpose LIKE ? OR notes LIKE ? OR sql_code LIKE ?)"
        params += [f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%']

    total = conn.execute(f"SELECT COUNT(*) FROM sql_queries {where}", params).fetchone()[0]
    queries = conn.execute(
        f"SELECT * FROM sql_queries {where} ORDER BY updated_at DESC",
        params
    ).fetchall()
    conn.close()

    return render_template('sql_queries.html', queries=queries, search=search, total=total)


@app.route('/sql-queries/new', methods=['GET', 'POST'])
def sql_query_new():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        purpose = request.form.get('purpose', '').strip()
        notes = request.form.get('notes', '').strip()
        sql_code = request.form.get('sql_code', '').strip()
        if not title or not sql_code:
            flash('Başlık ve SQL kodu zorunludur.', 'error')
            return render_template('sql_query_form.html', query=None,
                                   title=title, purpose=purpose, notes=notes, sql_code=sql_code)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = get_db()
        conn.execute(
            "INSERT INTO sql_queries (title, purpose, notes, sql_code, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (title, purpose, notes, sql_code, now, now)
        )
        conn.commit()
        conn.close()
        flash('SQL sorgusu başarıyla oluşturuldu.', 'success')
        return redirect(url_for('sql_queries_list'))
    return render_template('sql_query_form.html', query=None,
                           title='', purpose='', notes='', sql_code='')


@app.route('/sql-queries/<int:query_id>')
def sql_query_detail(query_id):
    conn = get_db()
    query = conn.execute("SELECT * FROM sql_queries WHERE id = ?", (query_id,)).fetchone()
    conn.close()
    if query is None:
        flash('SQL sorgusu bulunamadı.', 'error')
        return redirect(url_for('sql_queries_list'))
    return render_template('sql_query_detail.html', query=query)


@app.route('/sql-queries/<int:query_id>/edit', methods=['GET', 'POST'])
def sql_query_edit(query_id):
    conn = get_db()
    query = conn.execute("SELECT * FROM sql_queries WHERE id = ?", (query_id,)).fetchone()
    conn.close()
    if query is None:
        flash('SQL sorgusu bulunamadı.', 'error')
        return redirect(url_for('sql_queries_list'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        purpose = request.form.get('purpose', '').strip()
        notes = request.form.get('notes', '').strip()
        sql_code = request.form.get('sql_code', '').strip()
        if not title or not sql_code:
            flash('Başlık ve SQL kodu zorunludur.', 'error')
            return render_template('sql_query_form.html', query=query,
                                   title=title, purpose=purpose, notes=notes, sql_code=sql_code)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = get_db()
        conn.execute(
            "UPDATE sql_queries SET title=?, purpose=?, notes=?, sql_code=?, updated_at=? WHERE id=?",
            (title, purpose, notes, sql_code, now, query_id)
        )
        conn.commit()
        conn.close()
        flash('SQL sorgusu başarıyla güncellendi.', 'success')
        return redirect(url_for('sql_query_detail', query_id=query_id))

    return render_template('sql_query_form.html', query=query,
                           title=query['title'], purpose=query['purpose'],
                           notes=query['notes'], sql_code=query['sql_code'])


@app.route('/sql-queries/<int:query_id>/delete', methods=['POST'])
def sql_query_delete(query_id):
    conn = get_db()
    conn.execute("DELETE FROM sql_queries WHERE id = ?", (query_id,))
    conn.commit()
    conn.close()
    flash('SQL sorgusu silindi.', 'success')
    return redirect(url_for('sql_queries_list'))


def get_jira_settings():
    conn = get_db()
    settings = conn.execute("SELECT * FROM jira_settings LIMIT 1").fetchone()
    conn.close()
    return settings


def jira_auth_header(settings):
    token = base64.b64encode(f"{settings['email']}:{settings['api_token']}".encode()).decode()
    return {'Authorization': f'Basic {token}', 'Accept': 'application/json'}


@app.route('/jira/ayarlar', methods=['GET', 'POST'])
def jira_settings_view():
    settings = get_jira_settings()

    if request.method == 'POST':
        jira_url = request.form.get('jira_url', '').strip().rstrip('/')
        email = request.form.get('email', '').strip()
        api_token = request.form.get('api_token', '').strip()
        project_key = request.form.get('project_key', '').strip().upper()

        # When updating, an empty api_token means keep the existing one
        if settings and not api_token:
            api_token = settings['api_token']

        if not all([jira_url, email, api_token, project_key]):
            flash('Tüm alanlar zorunludur.', 'error')
            return render_template('jira_settings.html', settings=settings)

        # Test connection using the helper
        try:
            test_headers = jira_auth_header({'email': email, 'api_token': api_token})
            resp = http_requests.get(
                f"{jira_url}/rest/api/3/myself",
                headers=test_headers,
                timeout=10
            )
            if resp.status_code == 401:
                flash('Kimlik doğrulama hatası. E-posta veya API token hatalı.', 'error')
                return render_template('jira_settings.html', settings=settings)
            if resp.status_code != 200:
                flash(f'Jira bağlantısı başarısız (HTTP {resp.status_code}). URL\'yi kontrol edin.', 'error')
                return render_template('jira_settings.html', settings=settings)
        except http_requests.RequestException as e:
            flash(f'Bağlantı hatası: {str(e)}', 'error')
            return render_template('jira_settings.html', settings=settings)

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = get_db()
        if settings:
            conn.execute(
                "UPDATE jira_settings SET jira_url=?, email=?, api_token=?, project_key=?, updated_at=? WHERE id=?",
                (jira_url, email, api_token, project_key, now, settings['id'])
            )
        else:
            conn.execute(
                "INSERT INTO jira_settings (jira_url, email, api_token, project_key, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (jira_url, email, api_token, project_key, now, now)
            )
        conn.commit()
        conn.close()
        flash('Jira bağlantısı başarıyla kaydedildi.', 'success')
        return redirect(url_for('jira_kayitlar'))

    return render_template('jira_settings.html', settings=settings)


@app.route('/jira/kayitlar')
def jira_kayitlar():
    settings = get_jira_settings()
    if not settings:
        flash('Önce Jira bağlantısını yapılandırın.', 'warning')
        return redirect(url_for('jira_settings_view'))

    search = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    jql = f"project = \"{settings['project_key']}\""
    if search:
        jql += f" AND text ~ \"{search}\""
    if status_filter:
        jql += f" AND status = \"{status_filter}\""
    jql += " ORDER BY updated DESC"

    issues = []
    total = 0
    total_pages = 1
    error = None

    try:
        resp = http_requests.get(
            f"{settings['jira_url']}/rest/api/3/search",
            headers=jira_auth_header(settings),
            params={
                'jql': jql,
                'maxResults': per_page,
                'startAt': (page - 1) * per_page,
                'fields': 'summary,status,priority,assignee,reporter,created,updated,issuetype'
            },
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            issues = data.get('issues', [])
            total = data.get('total', 0)
            total_pages = max(1, (total + per_page - 1) // per_page)
        else:
            error = f'Jira API hatası (HTTP {resp.status_code}): {resp.text[:200]}'
    except http_requests.RequestException as e:
        error = f'Bağlantı hatası: {str(e)}'

    return render_template(
        'jira_kayitlar.html',
        settings=settings,
        issues=issues,
        total=total,
        page=page,
        total_pages=total_pages,
        search=search,
        status_filter=status_filter,
        error=error,
    )


@app.route('/jira/kurulum-rehberi')
def jira_kurulum():
    return render_template('jira_kurulum.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

