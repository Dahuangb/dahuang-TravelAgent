# tools/export_pdf.py
def export_pdf(md_text):
    import markdown
    import tempfile
    import os
    from datetime import datetime

    # Markdown → HTML
    html = markdown.markdown(md_text, extensions=['extra'])
    html_full = f"""
    <html><head><meta charset="utf-8"/><title>行程单</title></head>
    <body style="font-family:SimHei; margin:40px;">
    <h1>全程旅行行程单</h1><hr>{html}<hr>
    <p style="text-align:right; color:gray;">生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </body></html>
    """

    # 纯 Python → 直接写 PDF（无 wkhtmltopdf）
    from weasyprint import HTML
    pdf_bytes = HTML(string=html_full).write_pdf()
    return pdf_bytes