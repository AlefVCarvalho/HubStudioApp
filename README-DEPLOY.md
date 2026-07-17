# HubStudio App - Vercel + Supabase

## Preparação local

1. Copie `.env.example` para `.env`.
2. Preencha `DATABASE_URL`, `SECRET_KEY` e os dados do administrador.
3. Instale as dependências: `pip install -r requirements.txt`.
4. Inicialize as tabelas e o administrador uma única vez: `python scripts/init_db.py`.
5. Teste localmente: `python app.py`.

## Produção

Cadastre na Vercel as variáveis `DATABASE_URL`, `SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_NOME` e `SESSION_COOKIE_SECURE=true`.
