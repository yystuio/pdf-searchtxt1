"""结果导出模块 - 导出JSON或Markdown格式"""
import json
from pathlib import Path
from typing import List, Dict, Any


def export_to_json(results: List[Dict[str, Any]], output_path: str) -> None:
    """导出结果为JSON格式"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def export_to_markdown(results: List[Dict[str, Any]], output_path: str) -> None:
    """导出结果为Markdown格式"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 论文关键词知识点提取结果\n\n")

        for paper_result in results:
            f.write(f"## {paper_result['paper']}\n\n")
            f.write(f"**文件路径**: `{paper_result['path']}`\n\n")

            keywords_found = paper_result.get('keywords_found', {})
            if not keywords_found:
                f.write("*未找到关键词*\n\n")
                continue

            for keyword, sentences in keywords_found.items():
                f.write(f"### 关键词: {keyword}\n\n")
                for i, sentence in enumerate(sentences, 1):
                    f.write(f"{i}. {sentence}\n")
                f.write("\n")

            f.write("---\n\n")
