# poetlens · 把 NAS 相册变成诗意网页

poetlens 是一个面向 NAS / 本地相册的自托管照片网页项目。

它的核心价值很简单：

- 直接读取 NAS 里的照片目录
- 用本地 AI 理解照片内容
- 为照片生成带一点诗意的中文配文
- 把这些照片整理成适合浏览的网页画廊和详情页

它不是简单的相册文件列表，也不是只按时间顺序堆照片，而是尝试把“存着很多年、很少再打开”的照片，重新变成一个愿意逛、愿意回看的网页。

---

## 核心能力

### 1. 面向 NAS 的照片网页
你可以把 NAS、SMB 挂载目录或本地相册目录直接交给 poetlens。服务端会基于这些真实路径读取照片，并在网页里完成浏览、筛选和详情展示。

### 2. 本地 AI 分析，不上传照片
poetlens 支持接入本地视觉模型，例如通过 [LM Studio](https://lmstudio.ai/) 暴露的 OpenAI 兼容接口。照片分析、评分和配文都可以在你自己的机器或局域网设备上完成，更适合处理私人相册。

### 3. 诗意配文，而不只是标签
除了基础描述、分类和评分，poetlens 还会为每张照片写一句适合网页展示的中文短句。目标不是“解释照片里有什么”，而是让网页里的每张图都有一点情绪和余味。

### 4. 适合回看和策展的浏览体验
项目自带网页画廊、详情页和 review 流程。你可以先批量分析，再在网页里检查高分照片、看 AI 配文、确认展示效果，逐步把自己的相册整理成更有叙事感的页面。

---

## 项目结构

poetlens 当前主要由三部分组成：

1. **照片分析**
   扫描照片目录，提取 EXIF，调用本地视觉模型，生成描述、分类、评分和短句文案，并写入数据库。

2. **数据与服务层**
   使用 MySQL 或兼容的本地 SQLite 数据库存储分析结果，并通过 Flask 提供网页、图片访问和 review 能力。

3. **网页展示**
   通过画廊页、详情页和 review 页，把 NAS 照片以更适合阅读和回看的方式呈现出来。

---

## 快速开始

### 1. 安装依赖
推荐 Python 3.9+：

```bash
python3 -m venv venv
# Windows: venv\Scripts\activate
# Linux / macOS: source venv/bin/activate
pip install -r requirements.txt
```

### 2. 准备配置

```bash
cp config-example.py config.py
# Windows PowerShell:
# Copy-Item config-example.py config.py
```

至少确认这些字段：

1. `SQLALCHEMY_DATABASE_URI`
   推荐指向 MySQL，当前网页服务和分析流程默认围绕 `image_analysis` 表工作。

2. `IMAGE_DIR` / `PHOTOS_BASE_DIR`
   填你的 NAS 挂载目录或本地照片根目录，例如 `Z:/我的相册` 或 `/app/static/photos`。

3. `DOWNLOAD_KEY`
   用于受保护的静态资源访问。即使现在重点是网页展示，也建议设置成随机字符串。

4. `ENABLE_REVIEW_WEBUI`
   控制是否启用 review 页面。

### 3. 安装 exiftool
可选但推荐，用于更稳定地读取 EXIF 与 GPS 信息。

- Windows：下载后重命名为 `exiftool.exe`，加入环境变量
- macOS：`brew install exiftool`
- Debian / Ubuntu：`apt-get install -y libimage-exiftool-perl`

---

## 分析你的照片

先启动本地模型服务，例如 LM Studio 的本地 OpenAI 兼容接口：

- 默认地址：`http://127.0.0.1:1234/v1`

然后执行：

```bash
python analyze_local_qwen.py "你的照片目录"
```

这个过程会：

- 扫描照片
- 读取 EXIF / GPS
- 调用本地视觉模型
- 生成 `caption`、`type`、`memory_score`、`beauty_score`
- 生成适合网页展示的 `one_sentence_copy`
- 写入数据库

---

## 启动网页

```bash
python server.py
```

浏览器访问：

```text
http://[你的服务器IP]:8765/
```

当前网页侧重点包括：

- 照片画廊浏览
- 单张照片详情页
- review 页面检查 AI 配文和评分结果
- 面向本地 / NAS 路径的图片访问

---

## 部署到 NAS

如果你希望把 poetlens 长期放在 NAS 上跑，可以直接使用仓库里的 `Dockerfile`。

部署时建议：

1. 把真实相册目录挂载到容器内
2. 把数据库连接配置进 `config.py`
3. 暴露 `8765` 端口
4. 让分析任务和网页服务分开执行，便于长期维护

---

## 隐私说明

- `config.py`、数据库、日志、`output/` 默认不应提交到公开仓库
- `models/` 目录里的大模型文件建议只保留在本地或通过 Git LFS 管理
- poetlens 的推荐使用方式，是把照片保留在自己的 NAS / 局域网环境内

---

## 鸣谢

- 这个项目的最初灵感参考了 [dai-hongtao/InkTime](https://github.com/dai-hongtao/InkTime)。我在它的基础上把重点进一步转向了“把 NAS 照片放到网页上，并用诗意语言配文”的网页体验。
- 中文离线经纬度查城市名数据库基于 [GeoNames](https://www.geonames.org/)

---

## License

MIT
