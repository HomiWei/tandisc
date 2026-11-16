# tandisc

探盘单体仓库。

- `web/`：前端（Vite + React + TypeScript）。安装、开发、构建、预览、SPA 回退与 `data-testid` 见 [`web/README.md`](web/README.md)。
- `backend/`：FastAPI 服务。本地运行、健康检查、Docker 与测试见下文；环境变量、迁移和接口见 [`backend/README.md`](backend/README.md)。
- 仓库根目录留给后端和部署文件。前端业务代码只放在 `web/`。

密钥不要写入仓库。前端公开变量只使用 `VITE_` 前缀。后端密钥只放在环境变量或未提交的 `.env` 里，变量名见 [`backend/.env.example`](backend/.env.example)。

## 本地启动后端

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

不设置 `DATABASE_URL` 时使用 SQLite 文件 `backend/data/tandisc.db`。进程启动时建表，并在产品表为空时写入至少 30 条自建目录。

健康检查：`GET http://127.0.0.1:8080/health`，返回 `{"status":"ok"}`。

## Docker

镜像监听 `8080`，健康检查是容器内的 `GET /health`。

```bash
docker build -t tandisc-backend backend
docker run --rm -p 8080:8080 tandisc-backend
```

需要 Postgres 或模型配置时，用环境变量传入，不要把填好的 `.env` 放进镜像或提交到仓库。

```bash
docker run --rm -p 8080:8080 \
  -e DATABASE_URL='postgresql://USER:PASSWORD@HOST:5432/tandisc' \
  tandisc-backend
```

## 测试

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```
