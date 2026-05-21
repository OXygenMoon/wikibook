# Wikibook 服务器技术栈调整说明

本文档说明的是：

- 当前仓库已经具备的基础能力
- 后续真正部署到服务器时，仍然建议继续调整的技术栈
- 推荐的生产环境架构
- 各服务的职责、风险点和落地顺序

这份文档重点面向“正式上服务器后的下一阶段”，不是本地开发说明。

## 1. 当前状态

当前项目已经完成了第一轮基础升级：

- 主应用支持通过 `DATABASE_URL` 切换到 PostgreSQL
- 已接入 Redis + RQ 队列基础设施
- 已具备独立 Judge Worker 与 Docker Judge Runtime 骨架
- 已提供 `docker-compose.yml`、`Dockerfile`、`.env.example`
- 已提供显式初始化命令：

```bash
flask --app app wikibook init-platform --with-schema
```

也就是说，当前仓库已经不再是“只能跑 SQLite 单体 Flask”的状态，而是进入了“可演进为生产多服务架构”的阶段。

但是，真正部署到服务器时，仍然不建议直接把当前默认形态原样上线。

## 2. 生产环境的总体建议

推荐把服务器上的 Wikibook 技术栈调整为下面这套结构：

```text
用户
  |
  v
Nginx / Caddy
  |
  v
Wikibook Web (Gunicorn + Flask)
  |
  +--> PostgreSQL
  |
  +--> Redis
  |
  +--> Judge Worker (RQ Worker)
           |
           v
      Docker Judge Runtime
```

如果后期规模扩大，还可以继续扩展为：

- Web 多实例
- Worker 多实例
- PostgreSQL 独立主机或托管数据库
- Redis 独立主机或托管缓存
- 对象存储替代本地上传目录

## 3. 正式上服务器后，建议继续调整的部分

## 3.1 Web 层

当前可以使用：

- `gunicorn`
- `Flask`
- `Nginx`

这套组合适合第一阶段上线，但建议注意以下调整：

1. 不要再使用 `app.run()` 作为任何生产入口。
2. 统一使用 `gunicorn --config gunicorn.conf.py app:app`。
3. 如果后期并发上涨，建议把 `worker_class` 从默认 `sync` 评估为更适合你业务的模型。
4. 静态文件和上传文件不要全靠 Flask 提供，尽量由 Nginx 直接托管。

建议服务器上的职责拆分：

- Nginx：HTTPS、反向代理、静态文件、上传目录访问控制
- Gunicorn：只负责 Flask 应用进程

## 3.2 数据库层

当前仓库已经支持 PostgreSQL，但服务器上建议进一步规范：

1. 正式环境不要继续使用 SQLite。
2. 数据库账号不要使用默认弱密码。
3. 单独创建生产数据库、测试数据库、预发布数据库。
4. 开启 PostgreSQL 自动备份。
5. 监控连接数、慢查询、磁盘增长。

建议的生产形态：

- 小规模单机：Docker 内 PostgreSQL 也可以接受
- 中期稳定运行：迁移到独立 PostgreSQL 主机
- 更稳妥：直接使用云厂商托管 PostgreSQL

如果你后面用户量上来，推荐优先把数据库独立出去，因为它比 Web 容器更敏感。

## 3.3 Redis 层

当前 Redis 的用途主要是：

- RQ 任务队列
- JudgeTask 入队

服务器上建议继续调整：

1. Redis 不要暴露公网。
2. 为 Redis 设置访问密码或内网隔离。
3. 明确持久化策略。
4. 区分缓存用途和队列用途。

后续如果功能继续增加，建议考虑：

- `db 0` 给判题队列
- `db 1` 给未来缓存用途

或者直接使用不同实例，避免职责混杂。

## 3.4 Judge Worker 层

这是后续服务器环境里最需要重点调整的部分。

当前项目已经有：

- `judge_worker.py`
- `judge_tasks.py`
- `judge_runtime/run_submission.py`

但正式环境还建议补足下面这些策略：

1. Worker 和 Web 分离部署。
2. Worker 节点尽量不要和数据库放在同一主机。
3. Worker 机器要限制 CPU、内存、磁盘占用。
4. Worker 要有独立日志。
5. Worker 要有崩溃自动拉起机制。

生产建议：

- `systemd` 管理 worker 进程，或
- `docker compose` / `docker swarm` / `k8s` 管理 worker 容器

如果你后面要支持更高并发判题，建议扩成多 worker：

- `worker-1`
- `worker-2`
- `worker-3`

它们共同监听同一个 Redis 队列。

## 3.5 Docker Judge Runtime

当前 Judge Runtime 已经做了基础隔离，但上服务器后还需要继续加强。

建议你后续重点加强以下部分：

1. 运行用户不要用 root。
2. 继续收紧容器权限。
3. 禁止网络访问。
4. 加强只读文件系统限制。
5. 补充 stdout/stderr/超时/编译失败的详细审计日志。
6. 增加每次判题的临时目录清理策略。

当前已经配置的方向是对的，但如果正式上线，建议进一步考虑：

- `seccomp`
- `apparmor`
- `rootless docker`
- 更强隔离方案如 `nsjail` / `isolate`

如果平台后面会开放给大量陌生用户提交代码，仅靠普通 Docker 隔离并不算终点方案，最多算第一阶段方案。

## 3.6 文件存储层

当前项目仍然保留本地上传目录：

- `static/uploads`

这在单机阶段没问题，但正式服务器建议你尽快规划两种方向之一：

1. 继续本地磁盘，但做定时备份
2. 改为对象存储

如果你预计未来会有：

- 用户头像
- 题目附件
- 公告附件
- 代码样例文件

那么更推荐切到对象存储，例如：

- MinIO
- 阿里云 OSS
- 腾讯云 COS
- AWS S3

这样可以避免：

- 容器重建后文件丢失
- 多实例 Web 之间文件不同步

## 3.7 配置管理

当前项目已经使用 `.env` 风格配置，但部署到服务器后建议再往前走一步：

1. 区分开发、测试、生产环境变量。
2. 密钥不要写入仓库。
3. 生产环境变量交给 `systemd EnvironmentFile`、容器 secrets 或 CI/CD 管理。
4. 定义清晰的变量命名规范。

推荐至少区分：

- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `JUDGE_RUNTIME_IMAGE`
- `GUNICORN_*`
- 邮件/短信/第三方登录密钥

## 3.8 迁移与初始化策略

当前项目已经去掉了“首个请求自动改表”的模式，这是正确方向。

后续服务器上建议坚持下面的发布流程：

1. 拉取新版本代码
2. 安装依赖或构建镜像
3. 执行数据库迁移或平台初始化命令
4. 启动 Web
5. 启动 Worker
6. 检查健康状态

不要再回到这种模式：

- 启动 Web 时自动改库
- 第一个用户请求进来时自动建表

生产环境必须保持“初始化”和“对外服务”解耦。

## 3.9 日志与监控

服务器正式运行后，建议尽快补下面这套观测能力：

1. Nginx 访问日志
2. Gunicorn 错误日志
3. Flask 应用日志
4. Worker 日志
5. Judge Runtime 异常日志
6. PostgreSQL 慢查询或连接监控
7. Redis 队列长度监控

建议优先观察的指标：

- Web 响应时间
- 5xx 比例
- Redis 队列积压长度
- 单次判题平均耗时
- Worker 存活数量
- 数据库连接数
- 磁盘空间

如果后续持续运营，推荐接入：

- Prometheus + Grafana
- Loki / ELK
- Sentry

## 3.10 备份与容灾

这一项很容易被忽略，但服务器正式上线后必须提前规划。

至少要备份：

1. PostgreSQL 数据库
2. 上传文件目录
3. `.env` 和部署配置
4. Nginx / systemd / compose 配置

建议的最低标准：

- 数据库每日自动备份
- 上传目录每日增量备份
- 每周一次恢复演练

如果没有恢复演练，备份就不算真正可靠。

## 4. 推荐的服务器分阶段演进路线

## 第一阶段：单机可上线

适合：

- 早期内部使用
- 学校课程内使用
- 用户量不大

建议结构：

- 1 台服务器
- Nginx
- Web 容器
- PostgreSQL 容器
- Redis 容器
- Worker 容器
- Docker Judge Runtime

优点：

- 部署简单
- 成本低

缺点：

- 单点故障明显
- 判题高峰可能影响主站

## 第二阶段：服务拆分

适合：

- 用户开始增多
- 判题任务变重
- 需要更稳的可用性

建议结构：

- 1 台 Web 服务器
- 1 台数据库服务器
- 1 台 Worker 服务器
- Redis 独立部署

优点：

- Web 和判题互不抢资源
- 数据库更稳定

## 第三阶段：准生产化

适合：

- 长期运营
- 多课程、多班级、多教师
- 题库和判题量都增长

建议结构：

- 托管 PostgreSQL
- 托管 Redis
- Web 多实例
- Worker 多实例
- 对象存储
- 统一日志与监控

## 5. 对当前仓库建议继续补的代码层改造

当前基础设施已经有了，但后续为了更适合服务器运行，建议继续做这些代码改造：

1. 把现有 `Assignment / Submission` 正式接入 `JudgeTask`
2. 增加判题状态查询 API
3. 增加重判接口
4. 增加队列积压查看页或管理页
5. 增加健康检查接口，例如 `/healthz`
6. 增加生产日志格式化
7. 拆出更明确的配置类
8. 逐步把 `app.py` 里的大单文件拆模块

尤其是最后一点。

当前 `app.py` 仍然是超大单文件，功能继续增长后，服务器环境下排障、协作和发布成本都会越来越高。建议中期拆成：

- `models/`
- `routes/`
- `services/`
- `workers/`
- `config/`

## 6. 推荐的生产环境落地顺序

建议按这个顺序推进，不要一次性全改：

1. 先用 PostgreSQL 替换 SQLite
2. 确保 Redis 队列在服务器可稳定运行
3. 单独跑通 Judge Worker
4. 补全 Nginx + HTTPS
5. 增加备份
6. 增加监控
7. 再考虑对象存储与多实例扩容

这个顺序的好处是：

- 每一步都可验证
- 出问题时更容易定位
- 不会把数据库迁移、判题隔离、反向代理、备份监控混成一个大故障面

## 7. 一句话结论

当前仓库已经完成了“从单体 SQLite Flask 应用，走向可生产化多服务架构”的第一步。

真正部署到服务器后，最需要继续加强的不是 Flask 本身，而是：

- PostgreSQL 的独立与备份
- Redis 的安全与职责边界
- Judge Worker 的资源隔离
- Docker Judge Runtime 的安全收口
- 上传文件的持久化方案
- 监控、日志、恢复能力

如果后续按这个文档推进，Wikibook 会从“能跑”逐步进入“适合长期稳定运行”的状态。
