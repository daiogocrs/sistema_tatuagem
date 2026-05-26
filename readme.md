# Sistema de Gestão para Estúdio de Tatuagem

Um sistema web leve, rápido e de execução local, desenvolvido especialmente para tatuadores. Ele permite a gestão prática da agenda de clientes e o controle de estoque de materiais, sem a necessidade de configurações complexas ou mensalidades de servidores.

O sistema funciona localmente no computador, garantindo que os dados dos clientes e do estúdio permaneçam 100% privados e seguros na própria máquina.

---

## Tecnologias Utilizadas

- **Back-end:** Python 3 + Flask
- **Banco de Dados:** SQLite
- **Front-end:** HTML5 + Jinja2 + Bootstrap 5

---

## Como Usar

1. Acesse a aba **[Releases]** (ou Lançamentos) aqui no lado direito do GitHub.
2. Baixe o arquivo **`Tattoo.exe`**.
3. Salve em uma pasta no seu computador e dê dois cliques.
4. Uma tela preta vai abrir (não a feche) e o sistema abrirá automaticamente no seu navegador!

> **Nota sobre o Banco de Dados:** Seus dados ficam salvos em um arquivo chamado `estudio.db` que será criado na mesma pasta do programa. Faça backup dele regularmente!*

## Estrutura do Projeto

```text
/
├── app.py
├── requirements.txt
├── .gitignore
└── templates/
    ├── agenda.html
    ├── base.html
    └── index.html
```

Este projeto é de código aberto e livre para uso pessoal ou comercial.