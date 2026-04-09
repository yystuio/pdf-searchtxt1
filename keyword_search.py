"""关键词搜索模块 - 在论文中搜索关键词并提取完整句子"""
from typing import List, Dict, Any, Callable, Optional

from pdf_processor import extract_text_from_pdf, get_sentences_with_context


def search_papers_for_keywords(
    pdf_files: List[str],
    keywords: List[str],
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> List[Dict[str, Any]]:
    """
    在多个PDF论文中搜索关键词并提取完整句子

    Args:
        pdf_files: PDF文件路径列表
        keywords: 关键词列表
        progress_callback: 进度回调函数 (current, total, message)

    Returns:
        结果列表，每项包含 paper, path, keywords_found
    """
    results = []
    total = len(pdf_files)

    for i, pdf_path in enumerate(pdf_files):
        if progress_callback:
            filename = pdf_path.split('/')[-1].split('\\')[-1]
            progress_callback(i, total, filename)

        result = search_single_paper(pdf_path, keywords)
        results.append(result)

    if progress_callback:
        progress_callback(total, total, "完成")

    return results


def search_single_paper(pdf_path: str, keywords: List[str]) -> Dict[str, Any]:
    """搜索单篇论文"""
    try:
        title, text = extract_text_from_pdf(pdf_path)
    except Exception as e:
        return {
            "paper": pdf_path.split('/')[-1].split('\\')[-1],
            "path": pdf_path,
            "error": str(e),
            "keywords_found": {}
        }

    keywords_found: Dict[str, List[str]] = {}

    for keyword in keywords:
        sentences = get_sentences_with_context(text, keyword)
        if sentences:
            keywords_found[keyword] = sentences

    return {
        "paper": title,
        "path": pdf_path,
        "keywords_found": keywords_found
    }
