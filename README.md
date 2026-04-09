# 论文关键词知识点提取工具

一个基于 Tkinter GUI 的论文 PDF 关键词提取工具，支持在论文中搜索关键词并提取完整句子。

## 功能特性

- **PDF 解析**：自动提取 PDF 论文的文本内容和标题
- **关键词搜索**：支持多关键词搜索，自动匹配英文大小写
- **上下文提取**：提取包含关键词的完整句子，便于理解语义
- **批量处理**：支持单个文件或整个文件夹（递归搜索）
- **结果导出**：支持导出为 JSON 或 Markdown 格式
- **进度显示**：实时显示处理进度

## 安装依赖

```bash
pip install -r requirements.txt
```

## requirements.txt

```
PyMuPDF>=1.23.0
```

## 使用方法

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

## 项目结构

```
paper_knowledge_extractor/
├── main.py              # GUI 主程序
├── pdf_processor.py     # PDF 解析模块
├── keyword_search.py     # 关键词搜索模块
├── result_exporter.py    # 结果导出模块
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
- **语言**：Python 3.11+
