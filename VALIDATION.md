# 验证记录

- Python 3.13，Windows；9 项单元/HTTP 测试通过。
- 覆盖文档校验、分块、同名替换、来源、空库、缺密钥、HTTP 参数、模拟模型请求。
- 六道样例题在 lexical 词面演示后端上 evidence_hit_at_4=1.0。此结果仅验证小样例流程，不代表语义检索效果或真实回答准确率。
- 真实 Chroma + Sentence Transformers 链路仍需完成依赖和模型下载后验证。
- 真实 DeepSeek 调用未验证；聊天中出现过的密钥未写入项目，需撤销后在本地 .env 配置新密钥。
- Dockerfile 已提供，Docker 构建未验证。

