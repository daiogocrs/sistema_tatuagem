from flask import Flask, render_template, request, redirect, url_for, flash, g, send_file
import sqlite3
import os
from datetime import datetime
import re

app = Flask(__name__)

app.secret_key = os.urandom(24) 
DATABASE = 'estudio.db'

@app.template_filter('formatar_data')
def formatar_data(data_string):
    """Transforma 'YYYY-MM-DDTHH:MM' em 'DD/MM/YYYY às HH:MM'"""
    try:
        data_obj = datetime.strptime(data_string, '%Y-%m-%dT%H:%M')
        return data_obj.strftime('%d/%m/%Y às %H:%M')
    except ValueError:
        return data_string

@app.template_filter('limpar_telefone')
def limpar_telefone(telefone_string):
    """Remove parênteses, traços e espaços para o link do WhatsApp"""
    if not telefone_string:
        return ""
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
            descricao_tatuagem TEXT,
            status TEXT DEFAULT 'Pendente',
            valor REAL DEFAULT 0.0
        )''')
        db.commit()

def atualizar_status_passado():
    db = get_db()
    agora = datetime.now().strftime('%Y-%m-%dT%H:%M')
    try:
        db.execute("UPDATE agendamentos SET status = 'Concluído' WHERE data_hora < ? AND status = 'Pendente'", (agora,))
        db.commit()
    except sqlite3.Error as e:
        print(f"Erro ao atualizar status automático: {e}")

@app.route('/')
def index():
    filtro_categoria = request.args.get('categoria')
    db = get_db()
    
    try:
        estoque_baixo = db.execute("SELECT COUNT(*) FROM estoque WHERE quantidade < 5 AND categoria != 'Tintas'").fetchone()[0]
        
        hoje = datetime.now().strftime('%Y-%m-%d')
        agendamentos_hoje = db.execute("SELECT COUNT(*) FROM agendamentos WHERE data_hora LIKE ?", (f"{hoje}%",)).fetchone()[0]

        mes_atual = datetime.now().strftime('%Y-%m')
        faturamento = db.execute("SELECT SUM(valor) FROM agendamentos WHERE data_hora LIKE ? AND status = 'Concluído'", (f"{mes_atual}%",)).fetchone()[0]
        faturamento_mes = faturamento if faturamento else 0.0

        if filtro_categoria:
            itens = db.execute('SELECT * FROM estoque WHERE categoria = ? ORDER BY nome_item', (filtro_categoria,)).fetchall()
        else:
            itens = db.execute('SELECT * FROM estoque ORDER BY categoria, nome_item').fetchall()
            
        return render_template('index.html', estoque=itens, categoria_atual=filtro_categoria, 
                               estoque_baixo=estoque_baixo, agendamentos_hoje=agendamentos_hoje,
                               faturamento_mes=faturamento_mes)
    except sqlite3.Error as e:
        flash(f'Erro ao carregar os dados: {e}', 'danger')
        return render_template('index.html', estoque=[], categoria_atual=filtro_categoria, estoque_baixo=0, agendamentos_hoje=0, faturamento_mes=0.0)

@app.route('/adicionar_material', methods=['POST'])
def adicionar_material():
    item = request.form['item']
    categoria = request.form['categoria']
    quantidade = request.form['quantidade']
    
    if int(quantidade) < 0:
        flash('Erro: A quantidade não pode ser negativa!', 'danger')
        return redirect(url_for('index'))
    
    db = get_db()
    try:
        db.execute('INSERT INTO estoque (nome_item, categoria, quantidade) VALUES (?, ?, ?)', (item, categoria, quantidade))
        db.commit()
        flash(f'Material "{item}" adicionado com sucesso!', 'success')
    except sqlite3.Error as e:
        flash(f'Erro ao adicionar material: {e}', 'danger')
        
    return redirect(url_for('index'))

@app.route('/alterar_quantidade/<int:id>/<acao>')
def alterar_quantidade(id, acao):
    db = get_db()
    try:
        if acao == 'mais':
            db.execute('UPDATE estoque SET quantidade = quantidade + 1 WHERE id = ?', (id,))
        elif acao == 'menos':
            db.execute('UPDATE estoque SET quantidade = quantidade - 1 WHERE id = ? AND quantidade > 0', (id,))
        db.commit()
    except sqlite3.Error as e:
        flash('Erro ao alterar quantidade.', 'danger')
    return redirect(url_for('index'))

@app.route('/deletar_material/<int:id>')
def deletar_material(id):
    db = get_db()
    try:
        db.execute('DELETE FROM estoque WHERE id = ?', (id,))
        db.commit()
        flash('Material excluído com sucesso!', 'success')
    except sqlite3.Error:
        flash('Erro ao excluir o material.', 'danger')
    return redirect(url_for('index'))

@app.route('/editar_material/<int:id>', methods=['GET', 'POST'])
def editar_material(id):
    db = get_db()
    
    if request.method == 'POST':
        item = request.form['item']
        categoria = request.form['categoria']
        quantidade = request.form['quantidade']
        
        if int(quantidade) < 0:
            flash('Erro: A quantidade não pode ser negativa!', 'danger')
            return redirect(url_for('index'))
            
        try:
            db.execute('UPDATE estoque SET nome_item = ?, categoria = ?, quantidade = ? WHERE id = ?', (item, categoria, quantidade, id))
            db.commit()
            flash('Material atualizado!', 'success')
            return redirect(url_for('index'))
        except sqlite3.Error:
            flash('Erro ao atualizar material.', 'danger')
            return redirect(url_for('index'))
            
    item = db.execute('SELECT * FROM estoque WHERE id = ?', (id,)).fetchone()
    return render_template('editar_material.html', item=item)

@app.route('/agenda')
def agenda():
    atualizar_status_passado()
    db = get_db()
    try:
        agendamentos = db.execute("SELECT * FROM agendamentos ORDER BY status DESC, data_hora ASC").fetchall()
        return render_template('agenda.html', agendamentos=agendamentos)
    except sqlite3.Error as e:
        flash('Erro ao carregar agenda.', 'danger')
        return render_template('agenda.html', agendamentos=[])

@app.route('/novo_agendamento', methods=['POST'])
def novo_agendamento():
    cliente = request.form['cliente']
    telefone = request.form['telefone']
    data_hora = request.form['data_hora']
    descricao = request.form['descricao']
    valor = request.form['valor'] or 0.0
    
    if float(valor) < 0:
        flash('Erro: O valor cobrado não pode ser negativo!', 'danger')
        return redirect(url_for('agenda'))
    
    db = get_db()
    try:
        db.execute('INSERT INTO agendamentos (nome_cliente, telefone, data_hora, descricao_tatuagem, valor) VALUES (?, ?, ?, ?, ?)', 
                     (cliente, telefone, data_hora, descricao, float(valor)))
        db.commit()
        flash('Sessão agendada com sucesso!', 'success')
    except sqlite3.Error:
        flash('Erro ao agendar sessão.', 'danger')
        
    return redirect(url_for('agenda'))

@app.route('/mudar_status_agenda/<int:id>/<status>')
def mudar_status_agenda(id, status):
    db = get_db()
    try:
        db.execute('UPDATE agendamentos SET status = ? WHERE id = ?', (status, id))
        db.commit()
    except sqlite3.Error:
        flash('Erro ao alterar status.', 'danger')
    return redirect(url_for('agenda'))

@app.route('/deletar_agendamento/<int:id>')
def deletar_agendamento(id):
    db = get_db()
    try:
        db.execute('DELETE FROM agendamentos WHERE id = ?', (id,))
        db.commit()
        flash('Agendamento excluído.', 'success')
    except sqlite3.Error:
        flash('Erro ao excluir agendamento.', 'danger')
    return redirect(url_for('agenda'))

@app.route('/editar_agendamento/<int:id>', methods=['GET', 'POST'])
def editar_agendamento(id):
    db = get_db()
    
    if request.method == 'POST':
        cliente = request.form['cliente']
        telefone = request.form['telefone']
        data_hora = request.form['data_hora']
        status = request.form['status']
        descricao = request.form['descricao']
        valor = request.form['valor'] or 0.0
        
        if float(valor) < 0:
            flash('Erro: O valor cobrado não pode ser negativo!', 'danger')
            return redirect(url_for('agenda'))
        
        try:
            db.execute('''
                UPDATE agendamentos 
                SET nome_cliente = ?, telefone = ?, data_hora = ?, status = ?, descricao_tatuagem = ?, valor = ?
                WHERE id = ?
            ''', (cliente, telefone, data_hora, status, descricao, float(valor), id))
            db.commit()
            flash('Agendamento atualizado com sucesso!', 'success')
            return redirect(url_for('agenda'))
        except sqlite3.Error:
            flash('Erro ao atualizar agendamento.', 'danger')
            return redirect(url_for('agenda'))
            
    agendamento = db.execute('SELECT * FROM agendamentos WHERE id = ?', (id,)).fetchone()
    return render_template('editar_agendamento.html', agendamento=agendamento)

@app.route('/backup')
def fazer_backup():
    try:
        data_hoje = datetime.now().strftime('%Y-%m-%d')
        nome_arquivo = f"backup_estudio_{data_hoje}.db"
        
        return send_file(DATABASE, as_attachment=True, download_name=nome_arquivo)
    except Exception as e:
        flash(f'Erro ao gerar o backup: {e}', 'danger')
        return redirect(url_for('index'))
    
@app.route('/restaurar_backup', methods=['POST'])
def restaurar_backup():
    if 'arquivo_backup' not in request.files:
        flash('Nenhum ficheiro enviado.', 'danger')
        return redirect(url_for('index'))
        
    arquivo = request.files['arquivo_backup']
    
    if arquivo.filename == '':
        flash('Nenhum ficheiro selecionado.', 'danger')
        return redirect(url_for('index'))
        
    if arquivo and arquivo.filename.endswith('.db'):
        try:
            arquivo.save(DATABASE)
            flash('Backup restaurado com sucesso! Os dados foram atualizados.', 'success')
        except Exception as e:
            flash(f'Erro ao restaurar o backup: {e}', 'danger')
    else:
        flash('Formato inválido. Por favor, envie apenas o ficheiro .db do seu backup.', 'danger')
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)