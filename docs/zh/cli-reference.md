# CLI 参考

`cast` 命令行工具完整参考手册。

## 目录

- [安装](#安装)
- [全局选项](#全局选项)
- [命令](#命令)
  - [cast init](#cast-init)
  - [cast version](#cast-version)
- [退出码](#退出码)

---

## 安装

```bash
pip install cast-cli
```

**要求：** Python 3.9 或更高版本。

安装完成后，`cast` 命令即可在 PATH 中使用：

```bash
cast --help
```

---

## 全局选项

```
Options:
  --help    显示帮助信息并退出。
```

不带参数运行 `cast` 会显示帮助信息。

---

## 命令

### cast init

在当前目录初始化 DevSecOps 流水线。

#### 语法

```
cast init [OPTIONS]
```

#### 说明

将生产就绪的工作流文件写入目标路径：
- **GitHub**：`.github/workflows/devsecops.yml`
- **GitLab**：`.gitlab-ci.yml`

执行流程：

1. 从标记文件检测项目类型（或使用 `--type` 指定）
2. 检测 CI 平台（或使用 `--platform` 指定）
3. 检查工作流文件是否已存在
4. 读取对应的嵌入式模板
5. 按需创建目录并写入工作流文件

#### 选项

| 选项 | 简写 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--force` | `-f` | 标志 | `false` | 强制覆盖已有工作流文件 |
| `--type` | `-t` | 字符串 | 自动检测 | 项目类型：`python` / `nodejs` / `go` |
| `--platform` | `-p` | 字符串 | 自动检测 | CI 平台：`github` / `gitlab` |
| `--help` | | | | 显示帮助并退出 |

#### 示例

**自动检测项目类型和平台：**

```bash
cd my-project
cast init
```

**指定项目类型：**

```bash
cast init --type nodejs
```

**生成 GitLab CI 配置：**

```bash
cast init --platform gitlab
```

**Go 项目 + GitLab：**

```bash
cast init --type go --platform gitlab
```

**覆盖已有工作流：**

```bash
cast init --force
# 简写
cast init -f
```

#### 自动检测逻辑

**项目类型**：扫描当前目录的标记文件：

| 项目类型 | 标记文件 |
|---------|---------|
| `python` | `pyproject.toml`、`requirements.txt`、`setup.py`、`setup.cfg` |
| `nodejs` | `package.json` |
| `go` | `go.mod` |

第一个匹配的类型生效。多种标记文件并存时优先级：python > nodejs > go。

**CI 平台**：检查以下标记：

| CI 平台 | 检测依据 |
|---------|---------|
| `gitlab` | `.gitlab-ci.yml` 文件存在 |
| `github` | `.github/` 目录存在（默认回退） |

#### 错误情况

| 错误信息 | 原因 | 解决方法 |
|---------|------|---------|
| `Could not detect project type.` | 未找到标记文件 | 使用 `--type` 指定 |
| `Workflow already exists` | 目标文件已存在 | 使用 `--force` 覆盖 |
| `Unsupported project type` | 类型不在支持列表 | 使用 `python`、`nodejs` 或 `go` |
| `Unsupported platform` | 平台不在支持列表 | 使用 `github` 或 `gitlab` |

---

### cast version

显示已安装的 `cast-cli` 版本。

#### 语法

```
cast version
```

#### 说明

从已安装的包元数据中读取版本号并打印。

#### 示例

```bash
cast version
# cast 0.1.0
```

---

## 退出码

| 退出码 | 含义 |
|--------|------|
| `0` | 成功 |
| `1` | 错误（检测失败、不支持的类型、文件已存在、模板加载失败） |
