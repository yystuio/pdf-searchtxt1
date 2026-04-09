# 论文关键词知识点提取工具

一个基于 Tkinter GUI 的论文 PDF 关键词提取工具，支持在论文中搜索关键词并提取完整句子。

## 功能特性

- **PDF 解析**：自动提取 PDF 论文的文本内容和标题
- **关键词搜索**：支持多关键词搜索，自动匹配英文大小写
- **上下文提取**：提取包含关键词的完整句子，便于理解语义
- **批量处理**：支持单个文件或整个文件夹（递归搜索）
- **结果导出**：支持导出为 JSON 或 Markdown 格式
- **进度显示**：实时显示处理进度

### OCR 图片文字识别（可选）

- **图片文字识别**：自动识别 PDF 中嵌入图片里的文字（截图、扫描件等）
- **OCR 润色**：使用 LLM 修正 OCR 识别错误

### LLM 增强功能（可选，需要 CC-switch）

- **AI 推荐关键词**：根据论文内容智能推荐相关关键词
- **AI 知识总结**：自动总结论文中关键词相关的知识点

## 安装依赖

```bash
pip install -r requirements.txt
```

## requirements.txt

```
PyMuPDF>=1.23.0
easyocr>=1.7.0
anthropic>=0.18.0
```

## 使用方法

### 基础提取

1. 运行程序：
   ```bash
   python main.py
   ```

2. **选择 PDF 文件**：
   - 点击「选择PDF文件」选择单个或多个 PDF
   - 点击「选择文件夹」递归处理文件夹内所有 PDF

3. **输入关键词**：
   - 在文本框中输入关键词，每行一个
   - 支持英文大小写自动匹配
   - 可点击「从文件导入关键词」批量导入

4. **开始提取**：点击「开始提取」按钮

5. **导出结果**：
   - 「导出JSON」保存为结构化 JSON
   - 「导出Markdown」保存为可读性好的 Markdown

### OCR 图片识别

1. 勾选「启用OCR（识别图片中的文字）」
2. 执行关键词提取
3. （可选）使用「润色OCR结果」用 LLM 修正识别错误

### LLM 增强功能

1. 确保 CC-switch 已启动并配置了 API Provider
2. 点击「检查LLM服务」验证连接
3. 使用以下功能：
   - **AI推荐关键词**：选择 PDF 后点击，获取推荐关键词，可导入使用
   - **AI总结知识**：提取关键词后点击，生成知识总结

## 项目结构

```
paper_knowledge_extractor/
├── main.py              # GUI 主程序
├── pdf_processor.py     # PDF 解析模块
├── keyword_search.py     # 关键词搜索模块
├── result_exporter.py    # 结果导出模块
├── llm_client.py        # LLM 客户端（通过 CC-switch）
├── llm_enhancer.py      # LLM 增强功能
└── requirements.txt      # 依赖列表
```

## 输出格式

### JSON 格式

```json
[
  {
    "paper": "论文标题",
    "path": "/path/to/paper.pdf",
    "keywords_found": {
      "关键词1": ["包含关键词的句子1", "包含关键词的句子2"],
      "关键词2": ["包含关键词的句子"]
    }
  }
]
```

### Markdown 格式

```markdown
# 论文关键词知识点提取结果

## 论文标题

**文件路径**: `/path/to/paper.pdf`

### 关键词: 关键词1

1. 包含关键词的句子1
2. 包含关键词的句子2

---
```

## 技术栈

- **GUI**：Tkinter (Python 标准库)
- **PDF 解析**：PyMuPDF (fitz)
- **OCR 识别**：EasyOCR
- **LLM 调用**：Anthropic SDK（通过 CC-switch 代理）
- **语言**：Python 3.11+

## CC-switch 集成

本工具通过 CC-switch 管理的大模型 API 进行 LLM 调用。使用前请确保：

1. CC-switch 已安装并运行
2. 已配置至少一个 API Provider
3. LLM 代理服务地址为 `http://localhost:8080`（默认）
