# 探盘 (tandisc)

探盘的 monorepo。当前只有后端 P0 骨架，前端目录留给下一位同学。

## 目录

- `backend/` — FastAPI 服务（产品列表、详情、GitHub 月度榜、档案问答）
- `frontend/` — 预留给前端应用，本仓库还没有前端代码

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

更完整的环境变量、迁移和接口说明见 [backend/README.md](backend/README.md)。

## Docker

镜像监听 `8080`，健康检查是容器内的 `GET /health`。

```bash
docker build -t tandisc-backend backend
docker run --rm -p 8080:8080 tandisc-backend
```

需要 Postgres 或模型配置时，用环境变量传入，不要把填好的 `.env` 放进镜像或提交到仓库。变量名见 `backend/.env.example`。

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
