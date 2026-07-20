# HubStudio App - Nova versão

Sistema Flask redesenhado com as abas Dashboard, Produtos, Prospecções, Propostas, Clientes e Produção.

## Banco
A nova versão mantém a tabela `usuarios` e cria tabelas independentes:
- `produtos`
- `produto_etapas`
- `contatos`
- `producoes`
- `producao_produtos`

As tabelas antigas permanecem no Supabase e não são apagadas.

## Atualização
1. Faça backup do Supabase.
2. Substitua o código do repositório pelos arquivos desta versão.
3. Preserve as variáveis de ambiente da Vercel.
4. Localmente, configure `.env` com a mesma `DATABASE_URL`.
5. Execute `python scripts/init_db.py` uma vez para criar as novas tabelas.
6. Envie ao GitHub e aguarde o redeploy da Vercel.

## Regras principais
- Produto: nome, descrição, tags e checklist livre.
- Prospecção: contato editável com observações; ao enviar, sai da lista.
- Propostas: kanban Reunião > Análise > Proposta > Negociação > Cliente.
- Ao chegar em Cliente, o card sai do kanban e aparece na lista de clientes.
- Produção: kanban Alinhamento > Materiais > Produção > Ajustes > Entrega.
- Cada produção vincula um cliente a um ou mais produtos.
- Cada produto vinculado recebe preço próprio e periodicidade Pontual ou Mensal.

## Atualização de julho de 2026

Após publicar esta versão, execute uma vez, localmente, apontando o `.env` para o mesmo Supabase:

```powershell
py scripts/init_db.py
```

O comando adiciona os campos de data da produção, cria a tabela `producao_checklist` e gera o checklist inicial das produções já existentes. Nenhum cliente, produto ou serviço é apagado.

A logo deve permanecer em `public/logo.png`. O Flask publica essa pasta pelo endereço `/static/logo.png` tanto localmente quanto na Vercel.
