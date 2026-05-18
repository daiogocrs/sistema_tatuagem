from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

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

if __name__ == '__main__':
    init_db()
    app.run(debug=True)