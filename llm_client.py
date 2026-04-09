"""LLM 客户端模块 - 通过 CC-switch 代理调用大模型"""
import os
from typing import Optional, Dict, Any, List
import anthropic


class LLMClient:
    """大模型客户端，通过 CC-switch 本地代理调用"""

    def __init__(self, proxy_url: str = "http://127.0.0.1:15721"):
        """
        初始化 LLM 客户端

        Args:
            proxy_url: CC-switch 本地代理地址
        """
        self.proxy_url = proxy_url
        # 设置代理环境变量
        os.environ["HTTP_PROXY"] = proxy_url
        os.environ["HTTPS_PROXY"] = proxy_url

        api_key = os.environ.get("ANTHROPIC_API_KEY", "dev")
        self.client = anthropic.Anthropic(
            base_url=proxy_url,
            api_key=api_key
        )

    def is_available(self) -> tuple[bool, str]:
        """检查 LLM 服务是否可用，返回 (是否可用, 错误信息)"""
        try:
            # 发送一个简单的请求来测试连接
            self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
            return True, ""
        except Exception as e:
            error_msg = str(e)
            # 提供更友好的错误提示
            if "Connection refused" in error_msg or "Cannot connect" in error_msg:
                error_msg = f"无法连接到代理 {self.proxy_url}，请确认 CC-switch 已启动"
            elif "timeout" in error_msg.lower():
                error_msg = f"连接代理 {self.proxy_url} 超时"
            return False, error_msg

    def polish_ocr_text(self, ocr_text: str, model: str = "claude-sonnet-4-20250514") -> str:
        """
        润色 OCR 识别结果，修正错误

        Args:
            ocr_text: OCR 识别的原始文本
            model: 使用的模型

        Returns:
            润色后的文本
        """
        if not ocr_text or not ocr_text.strip():
            return ocr_text

        prompt = f"""请修正以下 OCR 识别文本中的错误，保持原意不变。
只返回修正后的文本，不要添加任何解释或说明。

OCR 识别文本：
{ocr_text}

修正后的文本："""

        response = self.client.messages.create(
            model=model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()

    def summarize_knowledge(
        self,
        paper_title: str,
        keywords_data: Dict[str, List[str]],
        model: str = "claude-sonnet-4-20250514"
    ) -> str:
        """
        总结论文关键词知识点

        Args:
            paper_title: 论文标题
            keywords_data: 关键词及其对应的句子 {keyword: [sentences]}
            model: 使用的模型

        Returns:
            总结文本
        """
        # 构建输入内容
        content_parts = [f"论文标题：{paper_title}\n\n提取的关键词知识点：\n"]

        for keyword, sentences in keywords_data.items():
            content_parts.append(f"【{keyword}】")
            for i, sentence in enumerate(sentences[:5], 1):  # 限制每个关键词最多5个句子
                content_parts.append(f"  {i}. {sentence}")
            content_parts.append("")

        content = "\n".join(content_parts)

        prompt = f"""请总结以下论文中关键词相关的知识点，用中文简洁清晰地描述：

{content}

请按以下格式总结：
1. 对每个主要关键词，给出2-3句总结
2. 指出关键词之间的关系（如果有）
3. 用学术但易懂的语言描述"""

        response = self.client.messages.create(
            model=model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()

    def recommend_keywords(
        self,
        paper_text: str,
        paper_title: str = "",
        num_recommendations: int = 10,
        model: str = "claude-sonnet-4-20250514"
    ) -> List[str]:
        """
        根据论文内容推荐相关关键词

        Args:
            paper_text: 论文文本（前几页）
            paper_title: 论文标题
            num_recommendations: 推荐关键词数量
            model: 使用的模型

        Returns:
            推荐的关键词列表
        """
        title_hint = f"论文标题：{paper_title}\n\n" if paper_title else ""

        prompt = f"""{title_hint}请根据以下论文内容，推荐 {num_recommendations} 个相关的关键词（中英文均可）。

要求：
1. 选择最重要且有实际意义的关键词
2. 包括技术术语、方法和概念
3. 返回格式：每行一个关键词，不要编号，不要解释

论文内容（节选）：
{paper_text[:3000]}

推荐关键词："""

        response = self.client.messages.create(
            model=model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )

        # 解析返回的关键词
        lines = response.content[0].text.strip().split("\n")
        keywords = []
        for line in lines:
            keyword = line.strip().strip("•-*1234567890.、 ")
            if keyword and len(keyword) > 1:
                keywords.append(keyword)

        return keywords[:num_recommendations]
