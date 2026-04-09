"""论文关键词知识点提取工具 - GUI主程序"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from pathlib import Path
from typing import List

from pdf_processor import extract_text_from_pdf, get_sentences_with_context
from keyword_search import search_papers_for_keywords
from result_exporter import export_to_json, export_to_markdown, export_to_xls
from llm_enhancer import (
    polish_ocr_in_background,
    summarize_knowledge_in_background,
    recommend_keywords_in_background
)
from llm_client import LLMClient


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("论文关键词知识点提取工具")
        self.root.geometry("900x700")

        self.pdf_files: List[str] = []
        self.results = []
        self.use_ocr = False
        self.llm_client = LLMClient()
        self.llm_available = False
        self.recommended_keywords = []  # LLM 推荐的关键词

        self.setup_ui()

    def setup_ui(self):
        """设置UI布局"""
        # 顶部标题
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(title_frame, text="论文PDF关键词知识点提取工具",
                  font=('Microsoft YaHei', 16, 'bold')).pack()

        # PDF文件选择区域
        pdf_frame = ttk.LabelFrame(self.root, text="PDF文件选择")
        pdf_frame.pack(fill=tk.X, padx=10, pady=5)

        pdf_btn_frame = ttk.Frame(pdf_frame)
        pdf_btn_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(pdf_btn_frame, text="选择PDF文件", command=self.select_pdf_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(pdf_btn_frame, text="选择文件夹", command=self.select_folder).pack(side=tk.LEFT, padx=5)
        ttk.Label(pdf_btn_frame, textvariable=tk.StringVar(value="已选择 0 个PDF文件")).pack(side=tk.LEFT, padx=20)

        # 关键词输入区域
        keyword_frame = ttk.LabelFrame(self.root, text="关键词（每行一个，支持英文大小写匹配）")
        keyword_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.keyword_text = scrolledtext.ScrolledText(keyword_frame, height=8, font=('Consolas', 10))
        self.keyword_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        keyword_btn_frame = ttk.Frame(keyword_frame)
        keyword_btn_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(keyword_btn_frame, text="从文件导入关键词", command=self.import_keywords).pack(side=tk.LEFT, padx=5)
        ttk.Button(keyword_btn_frame, text="清空关键词", command=self.clear_keywords).pack(side=tk.LEFT, padx=5)

        # 操作按钮
        action_frame = ttk.Frame(self.root)
        action_frame.pack(fill=tk.X, padx=10, pady=5)

        self.extract_btn = ttk.Button(action_frame, text="开始提取", command=self.start_extraction)
        self.extract_btn.pack(side=tk.LEFT, padx=5)

        # OCR 选项
        self.ocr_var = tk.BooleanVar(value=False)
        self.ocr_check = ttk.Checkbutton(
            action_frame,
            text="启用OCR（识别图片中的文字）",
            variable=self.ocr_var,
            command=self.on_ocr_toggle
        )
        self.ocr_check.pack(side=tk.LEFT, padx=20)

        self.export_json_btn = ttk.Button(action_frame, text="导出JSON", command=self.export_json, state=tk.DISABLED)
        self.export_json_btn.pack(side=tk.LEFT, padx=5)

        self.export_md_btn = ttk.Button(action_frame, text="导出Markdown", command=self.export_markdown, state=tk.DISABLED)
        self.export_md_btn.pack(side=tk.LEFT, padx=5)

        self.export_xls_btn = ttk.Button(action_frame, text="整理导出XLS", command=self.export_xls, state=tk.DISABLED)
        self.export_xls_btn.pack(side=tk.LEFT, padx=5)

        # LLM 功能区域
        llm_frame = ttk.LabelFrame(self.root, text="LLM 增强功能")
        llm_frame.pack(fill=tk.X, padx=10, pady=5)

        llm_btn_frame = ttk.Frame(llm_frame)
        llm_btn_frame.pack(fill=tk.X, padx=5, pady=5)

        self.check_llm_btn = ttk.Button(
            llm_btn_frame,
            text="检查LLM服务",
            command=self.check_llm_service
        )
        self.check_llm_btn.pack(side=tk.LEFT, padx=5)

        self.llm_status_label = ttk.Label(llm_btn_frame, text="LLM服务: 未检测")
        self.llm_status_label.pack(side=tk.LEFT, padx=10)

        self.recommend_keywords_btn = ttk.Button(
            llm_btn_frame,
            text="AI推荐关键词",
            command=self.start_keyword_recommendation,
            state=tk.DISABLED
        )
        self.recommend_keywords_btn.pack(side=tk.LEFT, padx=5)

        self.polish_ocr_btn = ttk.Button(
            llm_btn_frame,
            text="润色OCR结果",
            command=self.start_ocr_polish,
            state=tk.DISABLED
        )
        self.polish_ocr_btn.pack(side=tk.LEFT, padx=5)

        self.summarize_btn = ttk.Button(
            llm_btn_frame,
            text="AI总结知识",
            command=self.start_knowledge_summary,
            state=tk.DISABLED
        )
        self.summarize_btn.pack(side=tk.LEFT, padx=5)

        # 状态显示
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(action_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=20)

        # 进度条
        self.progress = ttk.Progressbar(self.root, mode='determinate')
        self.progress.pack(fill=tk.X, padx=10, pady=2)

        # 结果显示区域
        result_frame = ttk.LabelFrame(self.root, text="提取结果预览")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.result_text = scrolledtext.ScrolledText(result_frame, font=('Consolas', 9))
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def select_pdf_files(self):
        """选择PDF文件"""
        files = filedialog.askopenfilenames(
            title="选择PDF文件",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        if files:
            self.pdf_files = list(files)
            self.update_pdf_count()

    def select_folder(self):
        """选择文件夹（包含子目录）"""
        folder = filedialog.askdirectory(title="选择包含PDF的文件夹")
        if folder:
            # rglob 递归搜索所有子目录下的PDF
            self.pdf_files = [str(p) for p in Path(folder).rglob("*.pdf")]
            self.update_pdf_count()

    def update_pdf_count(self):
        """更新PDF计数显示"""
        count = len(self.pdf_files)
        # 找到那个Label并更新
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.LabelFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Frame):
                        for c in child.winfo_children():
                            if isinstance(c, ttk.Label) and "已选择" in str(c.cget("text")):
                                c.config(text=f"已选择 {count} 个PDF文件")

    def import_keywords(self):
        """从文件导入关键词"""
        file = filedialog.askopenfilename(
            title="导入关键词文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file:
            with open(file, 'r', encoding='utf-8') as f:
                keywords = f.read()
            self.keyword_text.delete('1.0', tk.END)
            self.keyword_text.insert('1.0', keywords)

    def clear_keywords(self):
        """清空关键词"""
        self.keyword_text.delete('1.0', tk.END)

    def get_keywords(self) -> List[str]:
        """获取关键词列表"""
        content = self.keyword_text.get('1.0', tk.END)
        keywords = [k.strip() for k in content.split('\n') if k.strip()]
        return keywords

    def on_ocr_toggle(self):
        """OCR复选框切换事件"""
        self.use_ocr = self.ocr_var.get()

    def start_extraction(self):
        """开始提取"""
        if not self.pdf_files:
            messagebox.showwarning("警告", "请先选择PDF文件！")
            return

        keywords = self.get_keywords()
        if not keywords:
            messagebox.showwarning("警告", "请输入关键词！")
            return

        self.extract_btn.config(state=tk.DISABLED)
        self.status_var.set("正在提取...")

        # 在后台线程执行
        thread = threading.Thread(target=self.extract_worker, args=(keywords,))
        thread.start()

    def extract_worker(self, keywords: List[str]):
        """提取工作线程"""
        try:
            self.results = search_papers_for_keywords(
                self.pdf_files, keywords, self.update_progress, self.use_ocr
            )
            self.root.after(0, self.extraction_complete)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", str(e)))
            self.root.after(0, self.extraction_complete)

    def update_progress(self, current: int, total: int, message: str = ""):
        """更新进度"""
        progress = (current / total) * 100 if total > 0 else 0
        self.root.after(0, lambda: self.progress.config(value=progress))
        status = f"处理中: {current}/{total} {message}"
        self.root.after(0, lambda: self.status_var.set(status))

    def extraction_complete(self):
        """提取完成"""
        self.extract_btn.config(state=tk.NORMAL)
        self.export_json_btn.config(state=tk.NORMAL)
        self.export_md_btn.config(state=tk.NORMAL)
        self.export_xls_btn.config(state=tk.NORMAL)
        self.progress.config(value=100)
        self.status_var.set(f"提取完成，共处理 {len(self.results)} 篇论文")

        # 预览结果
        self.preview_results()

    def preview_results(self):
        """预览结果"""
        self.result_text.delete('1.0', tk.END)

        for result in self.results:
            self.result_text.insert(tk.END, f"📄 {result['paper']}\n")
            self.result_text.insert(tk.END, f"   路径: {result['path']}\n")

            keywords_found = result.get('keywords_found', {})
            if keywords_found:
                for keyword, sentences in keywords_found.items():
                    self.result_text.insert(tk.END, f"   🔑 {keyword}: 找到 {len(sentences)} 处\n")
            else:
                self.result_text.insert(tk.END, "   (未找到关键词)\n")
            self.result_text.insert(tk.END, "\n")

    def export_json(self):
        """导出JSON"""
        if not self.results:
            return

        file = filedialog.asksaveasfilename(
            title="保存JSON文件",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json")]
        )
        if file:
            try:
                export_to_json(self.results, file)
                messagebox.showinfo("成功", f"已导出到:\n{file}")
            except Exception as e:
                messagebox.showerror("错误", str(e))

    def export_markdown(self):
        """导出Markdown"""
        if not self.results:
            return

        file = filedialog.asksaveasfilename(
            title="保存Markdown文件",
            defaultextension=".md",
            filetypes=[("Markdown文件", "*.md")]
        )
        if file:
            try:
                export_to_markdown(self.results, file)
                messagebox.showinfo("成功", f"已导出到:\n{file}")
            except Exception as e:
                messagebox.showerror("错误", str(e))

    def export_xls(self):
        """导出整理后的XLS"""
        if not self.results:
            return

        # 检查是否有 LLM 可用
        use_llm = self.llm_available
        if use_llm:
            available, _ = self.llm_client.is_available()
            use_llm = available

        file = filedialog.asksaveasfilename(
            title="保存XLS文件",
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx")]
        )
        if file:
            self.export_xls_btn.config(state=tk.DISABLED)
            self.status_var.set("正在整理导出...")

            # 在后台线程执行（LLM 整理较慢）
            thread = threading.Thread(
                target=self._export_xls_worker,
                args=(file, self.llm_client if use_llm else None)
            )
            thread.start()

    def _export_xls_worker(self, file: str, llm_client):
        """XLS 导出工作线程"""
        try:
            export_to_xls(
                self.results,
                file,
                llm_client=llm_client,
                progress_callback=self.update_progress
            )
            self.root.after(0, lambda: self._export_xls_complete(file))
        except ImportError as e:
            self.root.after(0, lambda: messagebox.showerror("错误", str(e)))
            self.root.after(0, self._export_xls_complete_error)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", str(e)))
            self.root.after(0, self._export_xls_complete_error)

    def _export_xls_complete(self, file: str):
        """XLS 导出完成"""
        self.export_xls_btn.config(state=tk.NORMAL)
        self.status_var.set("导出完成")
        messagebox.showinfo("成功", f"已导出到:\n{file}")

    def _export_xls_complete_error(self):
        """XLS 导出失败"""
        self.export_xls_btn.config(state=tk.NORMAL)
        self.status_var.set("导出失败")

    def check_llm_service(self):
        """检查 LLM 服务是否可用"""
        self.check_llm_btn.config(state=tk.DISABLED)
        self.status_var.set("正在检测 LLM 服务...")

        def worker():
            try:
                available, error = self.llm_client.is_available()
                self.root.after(0, lambda: self._update_llm_status(available, error))
            except Exception as e:
                self.root.after(0, lambda: self._update_llm_status(False, str(e)))

        thread = threading.Thread(target=worker)
        thread.start()

    def _update_llm_status(self, available: bool, error: str = ""):
        """更新 LLM 状态显示"""
        self.check_llm_btn.config(state=tk.NORMAL)
        self.llm_available = available

        if available:
            self.llm_status_label.config(text="LLM服务: 已连接", foreground="green")
            self.recommend_keywords_btn.config(state=tk.NORMAL)
            self.polish_ocr_btn.config(state=tk.NORMAL)
            self.summarize_btn.config(state=tk.NORMAL)
            messagebox.showinfo("成功", "LLM 服务已连接！")
        else:
            self.llm_status_label.config(text=f"LLM服务: 不可用", foreground="red")
            messagebox.showwarning("警告", f"无法连接 LLM 服务\n\n请确保 CC-switch 已启动并配置了 API Provider。\n\n错误: {error or '未知错误'}")

        self.status_var.set("就绪")

    def start_keyword_recommendation(self):
        """开始 AI 关键词推荐"""
        if not self.pdf_files:
            messagebox.showwarning("警告", "请先选择PDF文件！")
            return

        self.recommend_keywords_btn.config(state=tk.DISABLED)
        self.status_var.set("正在推荐关键词...")

        thread = threading.Thread(target=self.keyword_recommendation_worker)
        thread.start()

    def keyword_recommendation_worker(self):
        """关键词推荐工作线程"""
        try:
            self.recommended_keywords = recommend_keywords_in_background(
                self.pdf_files, self.update_progress
            )
            self.root.after(0, self.keyword_recommendation_complete)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"关键词推荐失败: {e}"))
            self.root.after(0, lambda: self._enable_llm_buttons())

    def keyword_recommendation_complete(self):
        """关键词推荐完成"""
        self.recommend_keywords_btn.config(state=tk.NORMAL)
        self.status_var.set("关键词推荐完成")

        # 显示推荐的关键词
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert(tk.END, "📋 AI 推荐的关键词\n\n")

        for rec in self.recommended_keywords:
            self.result_text.insert(tk.END, f"📄 {rec['paper']}\n")
            keywords = rec.get('recommended_keywords', [])
            if keywords:
                self.result_text.insert(tk.END, f"   推荐关键词: {', '.join(keywords)}\n")
            else:
                error = rec.get('error', '无')
                self.result_text.insert(tk.END, f"   错误: {error}\n")
            self.result_text.insert(tk.END, "\n")

        # 可以选择导入推荐关键词
        if any(rec.get('recommended_keywords') for rec in self.recommended_keywords):
            self._offer_to_import_keywords()

    def _offer_to_import_keywords(self):
        """询问用户是否导入推荐的关键词"""
        if messagebox.askyesno("导入关键词", "是否将推荐的关键词导入到关键词输入框？"):
            self._import_recommended_keywords()

    def _import_recommended_keywords(self):
        """导入推荐的关键词到输入框"""
        all_keywords = []
        for rec in self.recommended_keywords:
            all_keywords.extend(rec.get('recommended_keywords', []))

        if all_keywords:
            unique_keywords = list(set(all_keywords))
            self.keyword_text.delete('1.0', tk.END)
            self.keyword_text.insert('1.0', '\n'.join(unique_keywords))

    def start_ocr_polish(self):
        """开始润色 OCR 结果"""
        if not self.results:
            messagebox.showwarning("警告", "请先执行关键词提取！")
            return

        self.polish_ocr_btn.config(state=tk.DISABLED)
        self.status_var.set("正在润色 OCR 结果...")

        thread = threading.Thread(target=self.ocr_polish_worker)
        thread.start()

    def ocr_polish_worker(self):
        """OCR 润色工作线程"""
        try:
            polished_results = polish_ocr_in_background(self.results, self.update_progress)
            self.results = polished_results
            self.root.after(0, self.ocr_polish_complete)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"OCR 润色失败: {e}"))
            self.root.after(0, lambda: self._enable_llm_buttons())

    def ocr_polish_complete(self):
        """OCR 润色完成"""
        self.polish_ocr_btn.config(state=tk.NORMAL)
        self.status_var.set("OCR 润色完成")
        self.preview_results()

    def start_knowledge_summary(self):
        """开始 AI 知识总结"""
        if not self.results:
            messagebox.showwarning("警告", "请先执行关键词提取！")
            return

        self.summarize_btn.config(state=tk.DISABLED)
        self.status_var.set("正在总结知识...")

        thread = threading.Thread(target=self.knowledge_summary_worker)
        thread.start()

    def knowledge_summary_worker(self):
        """知识总结工作线程"""
        try:
            summarized_results = summarize_knowledge_in_background(self.results, self.update_progress)
            self.results = summarized_results
            self.root.after(0, self.knowledge_summary_complete)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"知识总结失败: {e}"))
            self.root.after(0, lambda: self._enable_llm_buttons())

    def knowledge_summary_complete(self):
        """知识总结完成"""
        self.summarize_btn.config(state=tk.NORMAL)
        self.status_var.set("知识总结完成")
        self.preview_results()

    def _enable_llm_buttons(self):
        """启用 LLM 按钮"""
        if self.llm_available:
            self.polish_ocr_btn.config(state=tk.NORMAL)
            self.summarize_btn.config(state=tk.NORMAL)


def main():
    root = tk.Tk()
    root.style = ttk.Style()
    # 设置主题
    try:
        root.style.theme_use('clam')
    except:
        pass

    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
