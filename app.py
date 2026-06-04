from flask import Flask, render_template, request, redirect, url_for, flash, g, send_file, send_from_directory
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
import sqlite3
import os
import sys
from datetime import datetime, timedelta
import uuid
import re

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    app = Flask(__name__, template_folder=template_folder)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    app = Flask(__name__)

app.secret_key = 'chave-secreta-estudio-tatuagem-segura' 
csrf = CSRFProtect(app) 
DATABASE = os.path.join(BASE_DIR, 'estudio.db')
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')

@app.template_filter('formatar_data')
def formatar_data(data_string):
    if not data_string: return ""
    try:
        data_obj = datetime.strptime(data_string, '%Y-%m-%dT%H:%M')
        return data_obj.strftime('%d/%m/%Y às %H:%M')
    except ValueError:
        return data_string

@app.template_filter('formatar_nascimento')
def formatar_nascimento(data_string):
    if not data_string: return ""
    try:
        data_obj = datetime.strptime(data_string, '%Y-%m-%d')
        return data_obj.strftime('%d/%m/%Y')
    except ValueError:
        return data_string

@app.template_filter('limpar_telefone')
def limpar_telefone(telefone_string):
    if not telefone_string: return ""
    return re.sub(r'\D', '', telefone_string)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db = get_db()
        db.execute('''CREATE TABLE IF NOT EXISTS estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_item TEXT NOT NULL,
            categoria TEXT NOT NULL,
            quantidade INTEGER NOT NULL
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_cliente TEXT NOT NULL,
            telefone TEXT,
            data_hora TEXT NOT NULL,
            data_hora_fim TEXT,
            descricao_tatuagem TEXT,
            status TEXT DEFAULT 'Pendente',
            valor REAL DEFAULT 0.0
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS agendamento_materiais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agendamento_id INTEGER,
            material_id INTEGER,
            quantidade INTEGER,
            FOREIGN KEY(agendamento_id) REFERENCES agendamentos(id),
            FOREIGN KEY(material_id) REFERENCES estoque(id)
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            data_nascimento TEXT,
            observacoes TEXT,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS despesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            data_despesa TEXT NOT NULL
        )''')
        
        try: db.execute("ALTER TABLE clientes ADD COLUMN alergias TEXT")
        except sqlite3.OperationalError: pass
        try: db.execute("ALTER TABLE clientes ADD COLUMN medicamentos TEXT")
        except sqlite3.OperationalError: pass
        try: db.execute("ALTER TABLE clientes ADD COLUMN condicoes_medicas TEXT")
        except sqlite3.OperationalError: pass
        try: db.execute("ALTER TABLE agendamentos ADD COLUMN imagem TEXT")
        except sqlite3.OperationalError: pass
        
        db.commit()

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def index():
    filtro_categoria = request.args.get('categoria')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    db = get_db()
    
    try:
        estoque_baixo = db.execute("SELECT COUNT(*) FROM estoque WHERE quantidade < 5 AND categoria != 'Tintas'").fetchone()[0]
        hoje = datetime.now().strftime('%Y-%m-%d')
        hoje_mes = f"{datetime.now().strftime('%Y-%m')}%"
        
        agendamentos_hoje = db.execute("SELECT COUNT(*) FROM agendamentos WHERE data_hora LIKE ?", (f"{hoje}%",)).fetchone()[0]
        faturamento = db.execute("SELECT SUM(valor) FROM agendamentos WHERE data_hora LIKE ? AND status = 'Concluído'", (hoje_mes,)).fetchone()[0] or 0.0
        despesas = db.execute("SELECT SUM(valor) FROM despesas WHERE data_despesa LIKE ?", (hoje_mes,)).fetchone()[0] or 0.0
        lucro_real = faturamento - despesas

        if filtro_categoria:
            total = db.execute('SELECT COUNT(*) FROM estoque WHERE categoria = ?', (filtro_categoria,)).fetchone()[0]
            itens = db.execute('SELECT * FROM estoque WHERE categoria = ? ORDER BY nome_item LIMIT ? OFFSET ?', (filtro_categoria, per_page, offset)).fetchall()
        else:
            total = db.execute('SELECT COUNT(*) FROM estoque').fetchone()[0]
            itens = db.execute('SELECT * FROM estoque ORDER BY categoria, nome_item LIMIT ? OFFSET ?', (per_page, offset)).fetchall()
            
        total_pages = max(1, (total + per_page - 1) // per_page)
            
        return render_template('index.html', estoque=itens, categoria_atual=filtro_categoria, 
                               estoque_baixo=estoque_baixo, agendamentos_hoje=agendamentos_hoje,
                               faturamento=faturamento, despesas=despesas, lucro_real=lucro_real, 
                               page=page, total_pages=total_pages)
    except sqlite3.Error:
        flash('Erro ao carregar os dados da base de dados.', 'danger')
        return render_template('index.html', estoque=[], page=1, total_pages=1, faturamento=0.0, despesas=0.0, lucro_real=0.0)

@app.route('/adicionar_material', methods=['POST'])
def adicionar_material():
    item = request.form['item']
    categoria = request.form['categoria']
    try:
        quantidade = int(request.form.get('quantidade', 0))
        if quantidade < 0: return redirect(url_for('index'))
    except ValueError: return redirect(url_for('index'))
        
    db = get_db()
    db.execute('INSERT INTO estoque (nome_item, categoria, quantidade) VALUES (?, ?, ?)', (item, categoria, quantidade))
    db.commit()
    return redirect(url_for('index'))

@app.route('/alterar_quantidade/<int:id>/<acao>', methods=['POST'])
def alterar_quantidade(id, acao):
    db = get_db()
    if acao == 'mais': db.execute('UPDATE estoque SET quantidade = quantidade + 1 WHERE id = ?', (id,))
    elif acao == 'menos': db.execute('UPDATE estoque SET quantidade = quantidade - 1 WHERE id = ? AND quantidade > 0', (id,))
    db.commit()
    return redirect(url_for('index'))

@app.route('/deletar_material/<int:id>', methods=['POST'])
def deletar_material(id):
    db = get_db()
    db.execute('DELETE FROM estoque WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('index'))

@app.route('/editar_material/<int:id>', methods=['POST'])
def editar_material(id):
    db = get_db()
    db.execute('UPDATE estoque SET nome_item = ?, categoria = ?, quantidade = ? WHERE id = ?', (request.form['item'], request.form['categoria'], request.form['quantidade'], id))
    db.commit()
    return redirect(url_for('index'))

@app.route('/agenda')
def agenda():
    db = get_db()
    page = request.args.get('page', 1, type=int)
    per_page = 8
    offset = (page - 1) * per_page
    
    try:
        todos = db.execute("SELECT id, nome_cliente, data_hora, data_hora_fim, status, descricao_tatuagem FROM agendamentos").fetchall()
        eventos_calendar = [{'id': str(a['id']), 'title': f"{a['nome_cliente']} - {a['descricao_tatuagem']}", 'start': a['data_hora'], 'end': a['data_hora_fim'] or a['data_hora'], 'color': '#198754' if a['status'] == 'Concluído' else '#212529'} for a in todos]
        
        total = db.execute('SELECT COUNT(*) FROM agendamentos').fetchone()[0]
        total_pages = max(1, (total + per_page - 1) // per_page)
        agendamentos = db.execute("SELECT * FROM agendamentos ORDER BY status DESC, data_hora ASC LIMIT ? OFFSET ?", (per_page, offset)).fetchall()
        
        estoque_disponivel = db.execute("SELECT id, nome_item, quantidade FROM estoque WHERE quantidade > 0 ORDER BY nome_item").fetchall()
        clientes_salvos = db.execute("SELECT nome, telefone FROM clientes ORDER BY nome").fetchall()

        return render_template('agenda.html', agendamentos=agendamentos, eventos_calendar=eventos_calendar, estoque_disponivel=estoque_disponivel, clientes_salvos=clientes_salvos, page=page, total_pages=total_pages)
    except sqlite3.Error:
        return render_template('agenda.html', agendamentos=[], eventos_calendar=[], estoque_disponivel=[], clientes_salvos=[], page=1, total_pages=1)

@app.route('/novo_agendamento', methods=['POST'])
def novo_agendamento():
    cliente = request.form['cliente']
    telefone = request.form['telefone']
    data_hora = request.form['data_hora']
    descricao = request.form['descricao']
    duracao = float(request.form.get('duracao', 1) or 1)
    valor = float(request.form.get('valor') or 0.0)
    data_hora_fim = (datetime.strptime(data_hora[:16], '%Y-%m-%dT%H:%M') + timedelta(hours=duracao)).strftime('%Y-%m-%dT%H:%M')
    
    imagem = request.files.get('imagem')
    nome_imagem = None
    if imagem and imagem.filename:
        ext = imagem.filename.rsplit('.', 1)[-1].lower()
        if ext in {'png', 'jpg', 'jpeg', 'webp'}:
            nome_imagem = f"{uuid.uuid4().hex}.{ext}"
            imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem))

    db = get_db()
    db.execute('INSERT INTO agendamentos (nome_cliente, telefone, data_hora, data_hora_fim, descricao_tatuagem, valor, imagem) VALUES (?, ?, ?, ?, ?, ?, ?)', 
               (cliente, telefone, data_hora, data_hora_fim, descricao, valor, nome_imagem))
    db.commit()
    flash('Sessão marcada com sucesso!', 'success')
    return redirect(url_for('agenda'))

@app.route('/concluir_agendamento/<int:id>', methods=['POST'])
def concluir_agendamento(id):
    db = get_db()
    material_ids = request.form.getlist('material_id[]')
    material_qtds = request.form.getlist('material_qtd[]')
    for m_id, qtd in zip(material_ids, material_qtds):
        if m_id and qtd:
            db.execute("UPDATE estoque SET quantidade = MAX(0, quantidade - ?) WHERE id = ?", (int(qtd), m_id))
            db.execute("INSERT INTO agendamento_materiais (agendamento_id, material_id, quantidade) VALUES (?, ?, ?)", (id, m_id, int(qtd)))
    db.execute("UPDATE agendamentos SET status = 'Concluído' WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for('agenda'))

@app.route('/mudar_status_agenda/<int:id>/<status>', methods=['POST'])
def mudar_status_agenda(id, status):
    db = get_db()
    if status == 'Pendente':
        usados = db.execute("SELECT material_id, quantidade FROM agendamento_materiais WHERE agendamento_id = ?", (id,)).fetchall()
        for m in usados:
            db.execute("UPDATE estoque SET quantidade = quantidade + ? WHERE id = ?", (m['quantidade'], m['material_id']))
        db.execute("DELETE FROM agendamento_materiais WHERE agendamento_id = ?", (id,))
    db.execute('UPDATE agendamentos SET status = ? WHERE id = ?', (status, id))
    db.commit()
    return redirect(url_for('agenda'))

@app.route('/deletar_agendamento/<int:id>', methods=['POST'])
def deletar_agendamento(id):
    db = get_db()
    db.execute('DELETE FROM agendamento_materiais WHERE agendamento_id = ?', (id,))
    db.execute('DELETE FROM agendamentos WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('agenda'))

@app.route('/editar_agendamento/<int:id>', methods=['POST'])
def editar_agendamento(id):
    db = get_db()
    db.execute('''UPDATE agendamentos SET nome_cliente=?, telefone=?, data_hora=?, data_hora_fim=?, descricao_tatuagem=?, valor=? WHERE id=?''', 
               (request.form['cliente'], request.form['telefone'], request.form['data_hora'][:16], request.form['data_hora_fim'][:16], request.form['descricao'], float(request.form.get('valor') or 0.0), id))
    db.commit()
    return redirect(url_for('agenda'))

@app.route('/clientes')
def clientes():
    db = get_db()
    lista_clientes = db.execute("SELECT * FROM clientes ORDER BY nome").fetchall()
    return render_template('clientes.html', clientes=lista_clientes)

@app.route('/novo_cliente', methods=['POST'])
def novo_cliente():
    db = get_db()
    db.execute('''INSERT INTO clientes (nome, telefone, data_nascimento, observacoes, alergias, medicamentos, condicoes_medicas) 
                  VALUES (?, ?, ?, ?, ?, ?, ?)''',
               (request.form['nome'], request.form['telefone'], request.form['data_nascimento'], request.form['observacoes'],
                request.form.get('alergias', ''), request.form.get('medicamentos', ''), request.form.get('condicoes', '')))
    db.commit()
    flash('Cliente registado com sucesso!', 'success')
    return redirect(url_for('clientes'))

@app.route('/deletar_cliente/<int:id>', methods=['POST'])
def deletar_cliente(id):
    db = get_db()
    db.execute('DELETE FROM clientes WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('clientes'))

@app.route('/financeiro')
def financeiro():
    db = get_db()
    hoje_mes = f"{datetime.now().strftime('%Y-%m')}%"
    despesas_lista = db.execute("SELECT * FROM despesas ORDER BY data_despesa DESC").fetchall()
    faturamento = db.execute("SELECT SUM(valor) FROM agendamentos WHERE data_hora LIKE ? AND status = 'Concluído'", (hoje_mes,)).fetchone()[0] or 0.0
    despesas_total = db.execute("SELECT SUM(valor) FROM despesas WHERE data_despesa LIKE ?", (hoje_mes,)).fetchone()[0] or 0.0
    lucro = faturamento - despesas_total
    return render_template('financeiro.html', despesas=despesas_lista, faturamento=faturamento, despesas_total=despesas_total, lucro=lucro)

@app.route('/nova_despesa', methods=['POST'])
def nova_despesa():
    db = get_db()
    db.execute("INSERT INTO despesas (descricao, valor, data_despesa) VALUES (?, ?, ?)", 
               (request.form['descricao'], float(request.form['valor']), request.form['data_despesa']))
    db.commit()
    flash('Despesa adicionada!', 'success')
    return redirect(url_for('financeiro'))

@app.route('/deletar_despesa/<int:id>', methods=['POST'])
def deletar_despesa(id):
    db = get_db()
    db.execute("DELETE FROM despesas WHERE id = ?", (id,))
    db.commit()
    flash('Despesa removida.', 'success')
    return redirect(url_for('financeiro'))

@app.route('/backup')
def fazer_backup():
    return send_file(os.path.abspath(DATABASE), as_attachment=True, download_name=f"backup_estudio_{datetime.now().strftime('%Y-%m-%d')}.db")
    
@app.route('/restaurar_backup', methods=['POST'])
def restaurar_backup():
    arquivo = request.files.get('arquivo_backup')
    if arquivo and arquivo.filename.endswith('.db'):
        temp_path = DATABASE + '.tmp'
        arquivo.save(temp_path) 
        try:
            conn = sqlite3.connect(temp_path)
            conn.execute('SELECT 1 FROM sqlite_master LIMIT 1')
            conn.close()
            os.replace(temp_path, DATABASE)
            flash('Backup restaurado com sucesso! Reinicie o sistema.', 'success')
        except sqlite3.Error:
            if os.path.exists(temp_path): os.remove(temp_path)
            flash('Erro: Arquivo corrompido.', 'danger')
    return redirect(url_for('index'))

@app.route('/desligar', methods=['POST'])
def desligar():
    os._exit(0)
    return "Desligando..."

if __name__ == '__main__':
    import webbrowser
    from threading import Timer
    PORTA = 5000
    def abrir_navegador(): webbrowser.open(f"http://127.0.0.1:{PORTA}")
    init_db()
    timer_navegador = Timer(1.5, abrir_navegador)
    try:
        timer_navegador.start()
        app.run(port=PORTA, debug=False)
    except OSError:
        timer_navegador.cancel()
        abrir_navegador()