import re
import openai
import fitz
import os

def GPT_turbo(prompt):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", 
        messages=[{
            "role": "user", 
            "content":prompt,
            }]
        )
    return completion.choices[0].message.content.strip()

def extract_text(page_num: int, doc) -> str:    
    page = doc[page_num]
    text = page.get_text()
    return text

def clean_html(html: str) -> str:
    simplified_html = re.sub(r'(line-height|font-family|font-size|color):[^>^<]+', '', html)
    simplified_html = re.sub(r'style="+', '', simplified_html)
    simplified_html = re.sub(r'(line-height|font-family|font-size|color):[^>^<]+', '', html)
    simplified_html = re.sub(r'style="+', '', simplified_html)
    simplified_html = re.sub(r'<img.*?src="data:image/[^>]*>', '', simplified_html)
    simplified_html = re.sub(r'<img.*?src="data:image/png;base64,[^>]*>', '', simplified_html)
    simplified_html = re.sub(r'<img.*?src="data:image/jpeg;base64,[^>]*>', '', simplified_html)
    simplified_html = re.sub(r'<img.*?src="data:image/gif;base64,[^>]*>', '', simplified_html)
    simplified_html = re.sub(r'<img.*?src="data:image/webp;base64,[^>]*>', '', simplified_html)
    simplified_html = re.sub(r'<img.*?src="data:image/svg+xml;base64,[^>]*>', '', simplified_html)
    simplified_html = re.sub(r'\.[\d]pt', '', simplified_html)
    simplified_html = re.sub(r'<span >', '', simplified_html)
    simplified_html = re.sub(r'</span>', '', simplified_html)
    simplified_html = re.sub(r'<p top:(\d+);left:(\d+);>', r'<p \1/\2>', simplified_html)

    return simplified_html

def convert_to_html(page_num: int, doc) -> str:
    page = doc[page_num]
    html = page.get_text("html")
    return clean_html(html)

def convert_to_markdown(save_content: str, html: str) -> str:
    prompt = f'''
Please convert the following HTML-like text to Markdown format:
[
{html}
]

Notes:
1. <p number/number> represents the position of the paragraph, which might be helpful.
2. You can reference the same content section on the previous and next pages, where there may be some useful information.
3. The previous and next pages have the same following text: {save_content}
4. If there is a table, please provide it in the form of a Markdown table.
5. If there is a formula, please provide it in the form of a Markdown formula.
6. Please only return the converted Markdown text.

Let's think step by step!
'''

    markdown = GPT_turbo(prompt)
    return markdown

def get_same_content(page_number1, page_number2, doc):
    prev_text = extract_text(page_number1 - 1, doc) if page_number1 > 0 else ""
    num_pages = len(doc)
    next_text = extract_text(page_number2 + 1, doc) if page_number2 < num_pages - 1 else ""
    same_content = set(prev_text.split()) & set(next_text.split())
    return same_content

def main(pdf_path: str, output_path: str):
    with fitz.open(pdf_path) as doc:
        num_pages = len(doc)
        markdown_output = ""

        for page_num in range(3):
            print(f"Processing page {page_num + 1} of {num_pages}")
            same_content = get_same_content(page_num-1, page_num+1, doc)
            html = convert_to_html(page_num, doc)
            print(same_content)
            markdown = convert_to_markdown(same_content, html)
            # markdown = ""
            markdown_output += markdown + "\n\n"

        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(markdown_output)

if __name__ == "__main__":
    openai.api_key = os.environ.get("OPENAI_API_KEY")

    pdf_path = "test_pdf/test.pdf"
    output_path = "test_pdf/test.md"
    main(pdf_path, output_path)
