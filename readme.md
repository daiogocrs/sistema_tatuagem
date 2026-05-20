# Sistema de Gestão para Estúdio de Tatuagem

Um sistema web leve, rápido e de execução local, desenvolvido especialmente para tatuadores. Ele permite a gestão prática da agenda de clientes e o controle de estoque de materiais, sem a necessidade de configurações complexas ou mensalidades de servidores.

O sistema funciona localmente no computador, garantindo que os dados dos clientes e do estúdio permaneçam 100% privados e seguros na própria máquina.

---

## Tecnologias Utilizadas

- **Back-end:** Python 3 + Flask
- **Banco de Dados:** SQLite
- **Front-end:** HTML5 + Jinja2 + Bootstrap 5

---

## Como Instalar e Executar

### Pré-requisitos

É necessário ter o Python 3.6 ou superior instalado no computador.

- :contentReference[oaicite:0]{index=0}

---

## Passo a passo

### 1. Clone este repositório

Abra o terminal (ou Prompt de Comando) e execute:

```bash
git clone https://github.com/daiogocrs/sistema_tatuagem.git
cd sistema_tatuagem
```

### 2. Crie um ambiente virtual (Recomendado)

Isso isola as bibliotecas do projeto do restante do sistema.

```bash
python -m venv venv
```

Ative o ambiente virtual:
* No **Windows**: `venv\Scripts\activate`
* No **Linux/Mac**: `source venv/bin/activate`

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Execute o sistema
```bash
python app.py
```

### 5. Acesse o sistema
Abra o navegador e acesse: `http://127.0.0.1:5000`

> **Nota sobre o Banco de Dados:** Você não precisa configurar nenhum banco de dados. Na primeira vez que você rodar o `python app.py`, o sistema criará automaticamente um arquivo chamado `estudio.db` na pasta do projeto com todas as tabelas necessárias.

## Estrutura do Projeto

```text
/
├── app.py
├── requirements.txt
├── .gitignore
└── templates/
    ├── base.html
    ├── index.html
    ├── agenda.html
    ├── editar_material.html
    └── editar_agendamento.html
```

Este projeto é de código aberto e livre para uso pessoal ou comercial.