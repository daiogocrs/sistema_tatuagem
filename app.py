from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
DATABASE = 'estudio.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_item TEXT NOT NULL,
            categoria TEXT NOT NULL,
            quantidade INTEGER NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_cliente TEXT NOT NULL,
            telefone TEXT,
            data_hora TEXT NOT NULL,
            descricao_tatuagem TEXT,
            status TEXT DEFAULT 'Pendente'
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    filtro_categoria = request.args.get('categoria')
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    
    if filtro_categoria:
        itens = conn.execute('SELECT * FROM estoque WHERE categoria = ? ORDER BY nome_item', (filtro_categoria,)).fetchall()
    else:
        itens = conn.execute('SELECT * FROM estoque ORDER BY categoria, nome_item').fetchall()
        
    conn.close()
    
    return render_template('index.html', estoque=itens, categoria_atual=filtro_categoria)

@app.route('/adicionar_material', methods=['POST'])
def adicionar_material():
    item = request.form['item']
    categoria = request.form['categoria']
    quantidade = request.form['quantidade']
    
    conn = sqlite3.connect(DATABASE)
    conn.execute('INSERT INTO estoque (nome_item, categoria, quantidade) VALUES (?, ?, ?)', (item, categoria, quantidade))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/alterar_quantidade/<int:id>/<acao>')
def alterar_quantidade(id, acao):
    conn = sqlite3.connect(DATABASE)
    if acao == 'mais':
        conn.execute('UPDATE estoque SET quantidade = quantidade + 1 WHERE id = ?', (id,))
    elif acao == 'menos':
        conn.execute('UPDATE estoque SET quantidade = quantidade - 1 WHERE id = ? AND quantidade > 0', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/deletar_material/<int:id>')
def deletar_material(id):
    conn = sqlite3.connect(DATABASE)
    conn.execute('DELETE FROM estoque WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/agenda')
def agenda():
    conn = sqlite3.connect(DATABASE)
    
    agora = datetime.now().strftime('%Y-%m-%dT%H:%M')
    
    conn.execute("UPDATE agendamentos SET status = 'Concluído' WHERE data_hora < ? AND status = 'Pendente'", (agora,))
    conn.commit()

    conn.row_factory = sqlite3.Row
    agendamentos = conn.execute("SELECT * FROM agendamentos ORDER BY status DESC, data_hora ASC").fetchall()
    conn.close()
    
    return render_template('agenda.html', agendamentos=agendamentos)

@app.route('/novo_agendamento', methods=['POST'])
def novo_agendamento():
    cliente = request.form['cliente']
    telefone = request.form['telefone']
    data_hora = request.form['data_hora']
    descricao = request.form['descricao']
    
    conn = sqlite3.connect(DATABASE)
    conn.execute('INSERT INTO agendamentos (nome_cliente, telefone, data_hora, descricao_tatuagem) VALUES (?, ?, ?, ?)', 
                 (cliente, telefone, data_hora, descricao))
    conn.commit()
    conn.close()
    
    return redirect(url_for('agenda'))

@app.route('/mudar_status_agenda/<int:id>/<status>')
def mudar_status_agenda(id, status):
    conn = sqlite3.connect(DATABASE)
    conn.execute('UPDATE agendamentos SET status = ? WHERE id = ?', (status, id))
    conn.commit()
    conn.close()
    return redirect(url_for('agenda'))

@app.route('/deletar_agendamento/<int:id>')
def deletar_agendamento(id):
    conn = sqlite3.connect(DATABASE)
    conn.execute('DELETE FROM agendamentos WHERE id = ?', (id))
    conn.commit()
    conn.close()
    return redirect(url_for('agenda'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)