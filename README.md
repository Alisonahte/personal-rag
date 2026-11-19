# Personal RAG：个人资料问答

Python / FastAPI / LangChain Text Splitters / Sentence Transformers / Chroma / DeepSeek API。

上传 PDF、UTF-8 TXT 或 Markdown → 按页解析 → 600 字符分块、100 字符重叠 → 嵌入 → Chroma 持久化 → top-k 检索 → DeepSeek 依据片段回答并附来源。

## 本机运行（PowerShell）

```powershell
cd D:\cxdownload\agent-night-lab\personal-rag
$py = '..\.venv\Scripts\python.exe'
Copy-Item .env.example .env
# 用编辑器填写 .env 的 LLM_API_KEY；不要提交此文件。
& $py -m pip install -e '.[dev]'
& $py -m uvicorn rag.api:app --host 127.0.0.1 --port 8000
```

浏览器打开 http://127.0.0.1:8000/docs ：先 POST /documents 上传 samples/course.md，再 POST /ask。

```json
{"question":"期末项目占多少成绩？","k":4,"generate":true}
```

回答应以资料中的 40% 为依据，sources 给出文件名、页码、片段及检索分数。PDF 页码为物理页序号；TXT/MD page=1。

## 不用密钥的离线流程

```powershell
$env:RAG_BACKEND='lexical'
& $py -m pytest -q --basetemp ..\tmp\rag-tests-local
& $py -m rag.evaluate
& $py -m uvicorn rag.api:app --host 127.0.0.1 --port 8000
```

POST /ask 时 generate=false。lexical 是词面重叠演示，不是 Sentence Transformers，也不能用它证明语义检索效果。
要跑真实向量链路，设置 `$env:RAG_BACKEND='chroma'`，下载模型后重新导入资料。首次下载模型需要网络。

## 从空文件夹搭建的顺序

1. 创建虚拟环境及 pyproject.toml，安装依赖。
2. documents.py：先写 parse，验证页码；再写 chunks，验证长度、重叠与稳定 ID。
3. store.py：SentenceTransformer.encode 生成向量，PersistentClient 保存；查询也用同一个模型。
4. service.py：把检索片段编号后拼进提示词，调用模型；无密钥报错而非伪造回答。
5. api.py：上传限额、请求参数校验、把阻塞操作移到线程池。
6. tests：重复导入不重复、替换旧文档、来源可追溯、空库拒答、缺密钥报错。
7. evaluate.py：测标注证据是否进入 top-4，并记录检索耗时；生成答案需人工判断事实与引用。

## 明确的边界

- 单用户本机原型，无登录、租户隔离和外网部署配置；服务默认仅监听本机。
- PDF 未实现 OCR；扫描件需先 OCR。
- 使用 LangChain 的文本分割组件，没有使用 LangChain Agent。
- 同名文件视为更新；跨目录同名冲突尚未解决。Chroma 删除加写入不是一个原子事务。
- 模型提示词降低编造风险，不保证消除幻觉；分数不是答案正确概率。
- 当前只有空库/零命中拒答，没有经过标定的语义相似度拒答阈值。
- 六道样例题只能验证流程，不代表真实课程资料准确率。请补充至少 20–30 道真实题和无答案题。
- 改嵌入模型必须用新的数据目录重建索引。
- Dockerfile 已提供，是否实际构建请看验证报告；不能把写了 Dockerfile 等同于验证过容器隔离。

## Docker

```sh
docker build -t personal-rag .
docker run --rm -p 127.0.0.1:8000:8000 --env-file .env personal-rag
```

正式使用再配置数据持久化卷；不要将 .env 烘焙进镜像。

## 面试一句话

“我做了一个单用户资料问答原型，把文档分块后用 Sentence Transformers 编码，存入 Chroma；查询召回 top-k 片段，再交给 DeepSeek 生成带来源的答案。我补充了重复导入处理、基本输入校验和检索评测。尚未做 OCR、多用户权限和生产级部署。”
