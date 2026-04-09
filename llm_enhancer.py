"""LLM 增强功能模块 - 提供 OCR 润色、知识总结、关键词推荐"""
import os
import threading
from typing import List, Dict, Any, Optional, Callable

from llm_client import LLMClient


class LLMEnhancer:
    """LLM 增强功能封装"""

    def __init__(self, proxy_url: str = None):
        # 默认使用与 llm_client.py 相同的端口
        if proxy_url is None:
            proxy_url = os.environ.get("LLM_PROXY_URL", "http://127.0.0.1:15721")
        self.proxy_url = proxy_url
        self._client: Optional[LLMClient] = None

    @property
    def client(self) -> LLMClient:
        """延迟初始化 LLM 客户端"""
        if self._client is None:
            self._client = LLMClient(self.proxy_url)
        return self._client

    def is_available(self) -> tuple[bool, str]:
        """检查 LLM 服务是否可用，返回 (是否可用, 错误信息)"""
        try:
            return self.client.is_available()
        except Exception as e:
            return False, str(e)

    def polish_ocr_worker(
        self,
        results: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        润色所有论文的 OCR 结果

        Args:
            results: 原始搜索结果
            progress_callback: 进度回调

        Returns:
            润色后的结果
        """
        total = len(results)

        for i, result in enumerate(results):
            if progress_callback:
                progress_callback(i, total, f"润色 OCR: {result.get('paper', 'unknown')}")

            ocr_text = result.get("ocr_text", "")
            if ocr_text:
                try:
                    polished = self.client.polish_ocr_text(ocr_text)
                    result["ocr_text_polished"] = polished
                except Exception as e:
                    result["ocr_text_polished"] = ocr_text
                    result["ocr_error"] = str(e)

        if progress_callback:
            progress_callback(total, total, "OCR 润色完成")

        return results

    def summarize_knowledge_worker(
        self,
        results: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        总结所有论文的关键词知识点

        Args:
            results: 搜索结果
            progress_callback: 进度回调

        Returns:
            包含总结的结果
        """
        total = len(results)

        for i, result in enumerate(results):
            if progress_callback:
                progress_callback(i, total, f"总结知识: {result.get('paper', 'unknown')}")

            paper_title = result.get("paper", "")
            keywords_found = result.get("keywords_found", {})

            if keywords_found:
                try:
                    summary = self.client.summarize_knowledge(paper_title, keywords_found)
                    result["knowledge_summary"] = summary
                except Exception as e:
                    result["knowledge_summary"] = ""
                    result["summary_error"] = str(e)

        if progress_callback:
            progress_callback(total, total, "知识总结完成")

        return results

    def recommend_keywords_worker(
        self,
        pdf_files: List[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        num_recommendations: int = 10
    ) -> List[Dict[str, Any]]:
        """
        为多篇论文推荐关键词

        Args:
            pdf_files: PDF 文件路径列表
            progress_callback: 进度回调
            num_recommendations: 每篇论文推荐关键词数量

        Returns:
            每篇论文的推荐关键词
        """
        from pdf_processor import extract_text_from_pdf

        recommendations = []
        total = len(pdf_files)

        for i, pdf_path in enumerate(pdf_files):
            if progress_callback:
                filename = pdf_path.split('/')[-1].split('\\')[-1]
                progress_callback(i, total, f"推荐关键词: {filename}")

            try:
                title, text = extract_text_from_pdf(pdf_path)
                keywords = self.client.recommend_keywords(
                    text[:5000],  # 限制文本长度
                    title,
                    num_recommendations
                )
                recommendations.append({
                    "paper": title,
                    "path": pdf_path,
                    "recommended_keywords": keywords
                })
            except Exception as e:
                recommendations.append({
                    "paper": pdf_path.split('/')[-1].split('\\')[-1],
                    "path": pdf_path,
                    "recommended_keywords": [],
                    "error": str(e)
                })

        if progress_callback:
            progress_callback(total, total, "关键词推荐完成")

        return recommendations


def polish_ocr_in_background(
    results: List[Dict[str, Any]],
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> List[Dict[str, Any]]:
    """在后台线程中润色 OCR 结果"""
    enhancer = LLMEnhancer()
    return enhancer.polish_ocr_worker(results, progress_callback)


def summarize_knowledge_in_background(
    results: List[Dict[str, Any]],
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> List[Dict[str, Any]]:
    """在后台线程中总结知识"""
    enhancer = LLMEnhancer()
    return enhancer.summarize_knowledge_worker(results, progress_callback)


def recommend_keywords_in_background(
    pdf_files: List[str],
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    num_recommendations: int = 10
) -> List[Dict[str, Any]]:
    """在后台线程中推荐关键词"""
    enhancer = LLMEnhancer()
    return enhancer.recommend_keywords_worker(pdf_files, progress_callback, num_recommendations)
