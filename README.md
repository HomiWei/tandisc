# tandisc

探盘单体仓库。

- `web/`：前端（Vite + React + TypeScript）。安装、开发、构建、预览、SPA 回退与 `data-testid` 见 [`web/README.md`](web/README.md)。
- 仓库根目录留给后端和部署文件。前端业务代码只放在 `web/`。

密钥不要写入仓库。前端公开变量只使用 `VITE_` 前缀。
