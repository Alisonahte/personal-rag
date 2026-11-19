"""Small labelled retrieval evaluation; not a claim about production accuracy."""
import argparse
import json
from pathlib import Path
from statistics import mean
from .service import from_env

CASES = [
    ("项目截止日期是什么时候？", "course.md", "12 月 20 日"),
    ("期末项目占多少成绩？", "course.md", "40%"),
    ("实验使用哪种数据库？", "course.md", "PostgreSQL"),
    ("每个小组可以有几个人？", "course.md", "三人"),
    ("ReAct 循环是什么？", "agent.md", "工具执行"),
    ("权限门禁能代替沙箱吗？", "agent.md", "不能"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate", action="store_true", help="Call paid API and record answers for manual evaluation")
    args = parser.parse_args()
    service = from_env()
    for path in Path("samples").iterdir():
        service.ingest(path.name, path.read_bytes())
    rows = []
    for question, source, expected in CASES:
        result = service.ask(question, generate=args.generate)
        hit = any(r["source"] == source and expected in r["text"] for r in result["sources"])
        rows.append({"question": question, "expected_evidence": expected, "hit_at_4": hit, **result})
    report = {"cases": len(rows), "evidence_hit_at_4": mean(r["hit_at_4"] for r in rows), "mean_retrieval_ms": mean(r["retrieval_ms"] for r in rows), "note": "6 toy cases; no general accuracy claim. Manually grade generated answers for factual support and citations.", "results": rows}
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
