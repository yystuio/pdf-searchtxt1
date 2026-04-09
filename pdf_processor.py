"""PDF解析模块 - 解析PDF并分句"""
import re
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Tuple, Optional
from io import BytesIO


def extract_text_from_pdf(pdf_path: str, use_ocr: bool = False) -> Tuple[str, str]:
    """
    从PDF提取文本和标题（按阅读顺序）

    Args:
        pdf_path: PDF文件路径
        use_ocr: 是否启用OCR识别图片中的文字

    Returns: (标题, 完整文本)
    """
    doc = fitz.open(pdf_path)
    full_text = []

    for page in doc:
        # 使用dict模式获取结构化文本块
        blocks = page.get_text("dict")["blocks"]
        page_text = extract_blocks_as_text(blocks)
        if page_text:
            full_text.append(page_text)

    doc.close()

    combined_text = "\n".join(full_text)

    # 如果启用OCR，提取图片中的文字
    if use_ocr:
        try:
            ocr_text = extract_ocr_text_from_pdf(pdf_path)
            if ocr_text:
                combined_text += "\n[OCR识别内容]\n" + ocr_text
        except Exception as e:
            # OCR失败时记录错误但不中断流程
            print(f"OCR处理警告: {e}")

    # 尝试从第一页提取标题（通常是最大的文字）
    title = extract_title_from_text(combined_text) or Path(pdf_path).stem

    return title, combined_text


def extract_blocks_as_text(blocks: list) -> str:
    """
    从PDF块提取文本，按阅读顺序合并
    过滤掉纯数字、表格标题等噪音
    """
    text_lines = []

    for block in blocks:
        if block.get("type") == 0:  # 文本块
            block_text = extract_text_block(block)
            if block_text and is_valid_text_line(block_text):
                text_lines.append(block_text)

    # 合并所有行为一个大文本
    return "\n".join(text_lines)


def extract_text_block(block: dict) -> str:
    """从单个文本块提取内容"""
    lines = []
    for line in block.get("lines", []):
        line_text = ""
        for span in line.get("spans", []):
            line_text += span.get("text", "")
        if line_text.strip():
            lines.append(line_text)

    # 检查是否包含"图片"标注，过滤图表描述
    full_text = " ".join(lines)
    if any(char in full_text for char in ['图', 'Figure', 'fig.', 'Tab.', '表']):
        # 可能是图表标题，保留但不单独作为句子
        pass

    return " ".join(lines)


def is_valid_text_line(text: str) -> bool:
    """判断是否是有效的文本行（过滤噪音）"""
    if not text or len(text.strip()) < 3:
        return False

    # 过滤纯数字或主要是数字的行
    stripped = text.strip()
    digit_ratio = sum(c.isdigit() for c in stripped) / len(stripped) if stripped else 0
    if digit_ratio > 0.5:
        return False

    # 过滤页码
    if re.match(r'^\d+$', stripped):
        return False

    # 过滤DOI、URL
    if re.match(r'^(doi:|http)', stripped.lower()):
        return False

    return True


def extract_title_from_text(text: str) -> str:
    """从文本中提取标题"""
    lines = text.split('\n')
    for line in lines[:5]:
        line = line.strip()
        # 跳过太短或太长的行
        if 5 < len(line) < 200 and not line.startswith(('.', '*', '-', '1.', '2.', '3.')):
            return line
    return ""


def split_into_sentences(text: str) -> List[str]:
    """
    将文本分割成句子
    支持中英文标点，并合并PDF中分散的短句
    """
    # 中英文句子结束标点
    sentence_endings = re.compile(r'[。！？.!?]+')

    sentences = []
    current_pos = 0

    for match in sentence_endings.finditer(text):
        end_pos = match.end()
        sentence = text[current_pos:end_pos].strip()
        if sentence:
            sentences.append(sentence)
        current_pos = end_pos

    # 处理最后一部分
    remaining = text[current_pos:].strip()
    if remaining:
        sentences.append(remaining)

    # 合并过短的句子（PDF文本块分散问题）
    sentences = merge_short_sentences(sentences)

    return sentences


def merge_short_sentences(sentences: List[str], min_length: int = 15) -> List[str]:
    """
    合并过短的句子（通常是PDF文本块分割的结果）
    原理：短句后面如果不以结束符结尾，应该与下一句合并
    """
    if not sentences:
        return sentences

    merged = []
    current = sentences[0] if sentences else ""

    for i in range(1, len(sentences)):
        next_sent = sentences[i]
        # 如果当前句太短且不以结束标点结尾，合并
        if len(current) < min_length and not re.search(r'[。！？.!?]$', current):
            current = current + " " + next_sent
        else:
            if current:
                merged.append(current)
            current = next_sent

    if current:
        merged.append(current)

    return merged


def get_sentences_with_context(text: str, keyword: str, context_chars: int = 50) -> List[str]:
    """
    获取包含关键词的完整句子
    在句子前后添加上下文
    """
    sentences = split_into_sentences(text)
    matching_sentences = []

    for sentence in sentences:
        if keyword.lower() in sentence.lower():
            matching_sentences.append(sentence)

    return matching_sentences


def extract_images_from_pdf(pdf_path: str) -> List[bytes]:
    """
    从PDF中提取所有图片的字节数据

    Args:
        pdf_path: PDF文件路径

    Returns:
        图片字节数据列表
    """
    images = []
    doc = fitz.open(pdf_path)

    for page_num, page in enumerate(doc):
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            images.append(image_bytes)

    doc.close()
    return images


def extract_ocr_text_from_pdf(pdf_path: str, lang: List[str] = None) -> str:
    """
    从PDF中的图片提取文字（OCR）

    Args:
        pdf_path: PDF文件路径
        lang: OCR语言列表，默认['en', 'ch_sim']

    Returns:
        识别出的文本
    """
    if lang is None:
        lang = ['en', 'ch_sim']

    import easyocr

    images = extract_images_from_pdf(pdf_path)
    if not images:
        return ""

    all_text = []
    # 复用同一个 reader 实例以提高效率
    reader = easyocr.Reader(lang, gpu=False, verbose=False)

    for img_bytes in images:
        try:
            image = fitz.open(stream=img_bytes, filetype="png")
            page = image[0]
            mat = fitz.Matrix(2, 2)  # 2x放大以提高识别精度
            clip = page.rect
            pix = page.get_pixmap(matrix=mat, clip=clip)
            img_data = pix.tobytes("png")
            image.close()

            # 使用EasyOCR识别
            results = reader.readtext(img_data)
            for detection in results:
                text = detection[1].strip()
                if text:
                    all_text.append(text)
        except Exception as e:
            continue

    return " ".join(all_text)
