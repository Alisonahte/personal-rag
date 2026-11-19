# 真实向量验证的下载诊断

已成功安装 Chroma 和 Sentence Transformers；Python 导入正常。官方 config.json 请求 HTTP 200。
禁用 Xet 后尝试 HTTP 权重下载，服务端在收到 200591518 / 470641600 字节时提前关闭连接。
因此尚未得到真实向量检索评测结果，不能用离线词面检索成绩替代。

网络稳定后，在 PowerShell 中运行：

```powershell
cd D:\cxdownload\agent-night-lab\personal-rag
$env:HF_HOME='D:\cxdownload\agent-night-lab\model-cache'
$env:HF_HUB_DISABLE_XET='1'
$env:RAG_BACKEND='chroma'
$env:RAG_DATA_DIR='D:\cxdownload\agent-night-lab\tmp\rag-vector-eval'
& '..\.venv\Scripts\python.exe' -m rag.evaluate
```

这个命令不调用付费大模型。成功后，填写本地 .env 的新 LLM_API_KEY，再加 --generate 验证真实回答。
不要分享密钥，不要把 .env 提交到 GitHub。

