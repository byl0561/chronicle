# Chronicle

**个人慢性病指标记录与趋势监控**

自托管、零依赖第三方服务的健康数据追踪工具。在界面里自由创建分类和指标，录入带日期的数值，自动生成趋势折线图，越界数据点高亮显示。

---

## 功能

- **自定义分类（Tab）**：按病种或身体系统组织指标，例如「慢性肾炎」「心血管」「肝功能」，支持颜色标识和排序
- **自定义指标**：在分类下创建任意指标，设置单位、默认参考范围、方向（区间内正常 / 越低越好 / 越高越好）
- **快速录入**：弹出式表单录入数值、测量日期、备注，三步完成
- **记录级参考区间**：同一指标在不同医院测量方法/正常区间可能不同，每条记录可单独填写本次化验单的参考上/下限（留空则继承指标默认），越界判定按记录自己的区间
- **检测来源**：每条记录可标注来源（医院/方法），录入时从历史来源自动补全
- **趋势图**：概览卡片用「按各自区间归一化」的走势（跨医院方法可比，校平换院造成的假跳变）；详情页折线图用实际值 + 每条记录各自区间画的**阶梯参考带**，越界点自动标红
- **仪表盘**：进入分类时以卡片形式展示所有指标的最新值与状态（正常 / 越界）
- **历史记录**：查看某指标的全部历史，支持编辑和删除单条
- **CSV 导入导出**：全量数据导出为 CSV，支持从同格式文件导入（幂等，重复跳过）
- **可选访问密码**：通过环境变量设置 HTTP Basic Auth，留空则不启用
- **响应式布局**：桌面端左侧导航栏，移动端顶部横向 Tab 滚动

---

## 快速启动

**前提**：已安装 Docker 和 Docker Compose。

```bash
# 1. 克隆项目
git clone <repo-url> chronicle
cd chronicle

# 2. 启动（默认不需要密码）
docker compose up -d

# 3. 打开浏览器
open http://localhost:8000
```

首次启动会自动创建数据库，无需额外初始化步骤。

### 启用访问密码

```bash
# 方式一：临时设置
APP_PASSWORD=your_secret docker compose up -d

# 方式二：在项目根目录创建 .env 文件（推荐）
cat > .env << 'EOF'
APP_USERNAME=admin
APP_PASSWORD=your_secret
EOF
docker compose up -d
```

设置密码后，浏览器访问时会弹出登录框。适合部署在内网并通过反向代理（如 Nginx、Caddy）对外暴露的场景。

---

## 配置

所有配置通过环境变量传入，可在 `.env` 文件中设置：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `APP_PASSWORD` | _(空)_ | 访问密码，**留空则完全不启用 Basic Auth** |
| `APP_USERNAME` | `chronicle` | Basic Auth 用户名（密码不为空时有效） |
| `GUNICORN_WORKERS` | `2` | gunicorn worker 进程数，低配 NAS 可改为 `1` |

---

## 数据持久化

数据库文件 `chronicle.db` 存放于 Docker 命名卷 `chronicle-data`，挂载到容器内 `/app/data/chronicle.db`。重建容器不丢失数据。

### 备份

```bash
# 直接从容器拷出数据库文件
docker cp chronicle:/app/data/chronicle.db ./chronicle_backup_$(date +%Y%m%d).db
```

或者找到卷的宿主机路径直接拷贝：

```bash
docker volume inspect chronicle-data --format '{{ .Mountpoint }}'
# 输出类似：/var/lib/docker/volumes/chronicle-data/_data
```

### 还原

```bash
# 停止容器，拷入备份文件，重启
docker compose stop
docker cp ./chronicle_backup.db chronicle:/app/data/chronicle.db
docker compose start
```

### 迁移到新服务器

1. 在旧服务器执行备份，得到 `chronicle_backup.db`
2. 在新服务器部署后，将备份文件拷入容器的 `/app/data/chronicle.db`
3. 重启容器即可

---

## CSV 格式

### 导出

在「设置 → 数据管理」中点击「导出 CSV」，文件包含所有分类、指标和历史记录。

### 导入

CSV 必须包含以下表头（顺序不限）：

| 列名 | 必填 | 说明 |
|---|---|---|
| `tab_name` | ✓ | 分类名称 |
| `tab_color` | | 分类颜色（十六进制，如 `#3B5BDB`） |
| `indicator_name` | ✓ | 指标名称 |
| `unit` | | 单位（如 `μmol/L`） |
| `ref_low` | | 参考范围下限（数字） |
| `ref_high` | | 参考范围上限（数字） |
| `direction` | | `range` / `lower` / `higher`，默认 `range` |
| `measured_at` | | 测量日期，格式 `YYYY-MM-DD` |
| `value` | | 数值（有 `measured_at` 时必填） |
| `note` | | 备注 |
| `record_ref_low` | | 本条记录的参考下限（留空继承指标 `ref_low`） |
| `record_ref_high` | | 本条记录的参考上限（留空继承指标 `ref_high`） |
| `source` | | 检测来源（医院/方法） |

> `ref_low` / `ref_high` 是**指标**的默认区间；`record_ref_low` / `record_ref_high` 是**单条记录**的区间，用于记录不同医院化验单印的不同参考范围，留空则回退到指标默认。

**导入规则：**
- 按 `tab_name` 查找或创建分类
- 按 `(tab_name, indicator_name)` 查找或创建指标
- 按 `(indicator_id, measured_at)` 判断重复，重复则跳过（幂等导入）
- 没有 `value` 的行仅创建指标，不创建记录

**示例：**

```csv
tab_name,tab_color,indicator_name,unit,ref_low,ref_high,direction,measured_at,value,note,record_ref_low,record_ref_high,source
慢性肾炎,#3B5BDB,肌酐,μmol/L,44,133,range,2025-01-15,98.5,复查,,,A医院
慢性肾炎,#3B5BDB,肌酐,μmol/L,44,133,range,2025-04-20,103.2,,80,133,B医院·酶法
慢性肾炎,#3B5BDB,尿蛋白,g/L,0,0.15,range,2025-01-15,0.12,,,,
```

---

## 本地开发

**后端**（Python 3.12+）：

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload   # 监听 http://127.0.0.1:8000
```

**前端**（Node.js 18+）：

```bash
cd frontend
npm install
npm run dev    # 监听 http://localhost:5173，/api/* 代理到 :8000
```

前端 dev server 已配置代理，前后端分别启动后直接访问 `http://localhost:5173` 即可。

---

## 项目结构

```
chronicle/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI 入口 + 生命周期（自动建表 + 轻量列迁移）
│   │   ├── deps.py           # DB session 依赖注入
│   │   ├── core/config.py    # 环境变量配置（CHRONICLE_ 前缀）
│   │   ├── db/base.py        # SQLAlchemy engine（WAL + 外键）
│   │   ├── models/models.py  # Tab / Indicator / Record ORM 模型
│   │   ├── schemas/schemas.py # Pydantic 请求/响应 Schema
│   │   └── api/
│   │       ├── router.py     # 路由汇总
│   │       ├── tabs.py       # Tab CRUD + 重排序
│   │       ├── indicators.py # Indicator CRUD + 重排序
│   │       ├── records.py    # Record CRUD
│   │       └── data.py       # CSV 导出 / 导入
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.vue           # 布局外壳（侧边栏 + Tab 导航 + Toast）
│       ├── style.css         # 设计系统（CSS 变量、组件样式）
│       ├── api.js            # Axios 封装
│       ├── store.js          # 全局状态 + 状态计算/归一化工具函数
│       ├── components/
│       │   ├── Icon.vue          # SVG 图标集
│       │   ├── Sheet.vue         # 抽屉弹窗
│       │   ├── ConfirmDialog.vue # 危险操作确认框
│       │   ├── CustomSelect.vue  # 自定义下拉选择
│       │   ├── DateInput.vue     # 自定义日历选择器
│       │   ├── SourceInput.vue   # 检测来源输入（自由文本 + 历史补全）
│       │   └── IndicatorChart.vue # Chart.js 趋势图（实际值 + 逐记录阶梯参考带）
│       └── views/
│           ├── Dashboard.vue      # Tab 仪表盘（指标卡片网格）
│           ├── IndicatorDetail.vue # 趋势图 + 历史记录列表
│           └── Settings.vue       # 分类/指标管理 + CSV 导入导出
├── nginx/nginx.conf          # 静态文件 + /api/ 反向代理
├── Dockerfile                # 两阶段构建：node → python-slim + nginx
├── docker-compose.yml
└── docker-entrypoint.sh      # 启动脚本（生成 htpasswd → nginx → gunicorn）
```

---

## 技术栈

| 层 | 技术 |
|---|---|
| 后端框架 | FastAPI 0.115 + Uvicorn/Gunicorn |
| 数据库 | SQLite（WAL 模式，`python-multipart` 支持文件上传） |
| ORM | SQLAlchemy 2.0（声明式映射） |
| 前端框架 | Vue 3 + Vite + Vue Router |
| 图表 | Chart.js 4 + chartjs-adapter-date-fns |
| HTTP 客户端 | Axios |
| 反向代理 | nginx |
| 容器 | Docker（两阶段构建，单容器运行） |

---

## API 路由速览

```
GET    /api/tabs
POST   /api/tabs
PATCH  /api/tabs/{id}
DELETE /api/tabs/{id}
POST   /api/tabs/reorder

GET    /api/tabs/{tab_id}/indicators
POST   /api/tabs/{tab_id}/indicators
PATCH  /api/indicators/{id}
DELETE /api/indicators/{id}
POST   /api/indicators/reorder

GET    /api/indicators/{indicator_id}/records
POST   /api/indicators/{indicator_id}/records
PATCH  /api/records/{id}
DELETE /api/records/{id}
GET    /api/sources                        # 历史检测来源（按频次，供录入补全）

GET    /api/data/export
POST   /api/data/import

GET    /api/health
```

完整的自动生成文档（Swagger UI）在开发模式下访问 `http://127.0.0.1:8000/docs`。

---

## 免责声明

本工具仅供个人记录与可视化，不构成医疗建议，不能替代医生的诊断与随访。所有数据仅存储在您自己的服务器上，不会上传至任何第三方服务。

---

## License

[MIT](LICENSE)
