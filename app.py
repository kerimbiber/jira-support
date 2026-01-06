from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import pandas as pd
import re
import os
import time
from pathlib import Path
from werkzeug.utils import secure_filename
import io

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}

# Upload klasörünü oluştur
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

