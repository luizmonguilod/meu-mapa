# Meu Mapa — versão pronta para publicação

Esta versão mantém o app FastAPI/PWA original e acrescenta itens para uso em produção:

- `Dockerfile` para hospedagem em serviços compatíveis com Docker.
- `render.yaml` para publicação simplificada no Render.
- `/healthz` para verificação de disponibilidade.
- Service Worker no escopo raiz (`/sw.js`) para instalação correta como PWA.
- Ícones PWA 192x192 e 512x512.
- Cálculo de "hoje" usando explicitamente `America/Sao_Paulo`.
- Proteção opcional por usuário/senha via `APP_USER` e `APP_PASSWORD`.

## Testar no computador

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

Abra `http://localhost:8000`.

## Publicar no Render

1. Coloque esta pasta em um repositório GitHub privado.
2. No Render, crie um **Blueprint** a partir do repositório. O arquivo `render.yaml` configura o serviço.
3. Em **Environment**, adicione `APP_USER` e `APP_PASSWORD` se quiser proteger seus dados pessoais.
4. Faça o deploy. O Render fornecerá uma URL HTTPS.
5. Abra a URL no celular e use **Adicionar à tela inicial / Instalar app**.

> Observação de privacidade: o app contém nome completo, data, hora e local de nascimento. Para hospedagem na internet, recomenda-se ativar `APP_PASSWORD`.

## PWA

O PWA depende de HTTPS quando está hospedado na internet. Em `localhost`, os navegadores também permitem Service Worker para testes.
