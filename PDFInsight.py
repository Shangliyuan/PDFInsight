import requests
import re
import os
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract\tesseract.exe'  # 您的tesseract路径
poppler_path = 'D:\\poppler\\poppler-23.11.0\\Library\\bin'  # 您的poppler路径


#用来下载pdf文件
def download_pdfs_from_string(string):
    # 使用正则表达式提取PDF链接
    pdf_links = re.findall(r'https?://[^\s,]+\.pdf', string)

    # 创建一个文件夹来存储下载的PDF文件
    if not os.path.exists('downloaded_pdfs'):
        os.makedirs('downloaded_pdfs')

    # 设置User-Agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    
    file_paths = []
    # 下载每个PDF文件
    for link in pdf_links:
        try:
            # 从链接中提取文件名
            filename = link.split('/')[-1]
            # 发送HTTP GET请求下载PDF文件
            response = requests.get(link, headers=headers)

            # 检查是否成功下载文件
            if response.status_code == 200:
                # 保存PDF文件到本地
                with open(os.path.join('downloaded_pdfs', filename), 'wb') as file:
                    file.write(response.content)
                print(f"Downloaded {filename}")
                file_paths += [os.path.join('downloaded_pdfs', filename)]
            else:
                print(f"Failed to download {filename}. Response code: {response.status_code}")
        except Exception as e:
            print(f"An error occurred while downloading {filename}: {e}")
    return file_paths

#用来处理可直接阅读的pdf
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text

#用ocr处理不可直接阅读的pdf
def pdf_to_text_ocr(pdf_path, poppler_path):
    images = convert_from_path(pdf_path, poppler_path=poppler_path)
    text_output = []
    for image in images:
        text = pytesseract.image_to_string(image, lang='chi_sim')
        text_output.append(text)
    return "\n\n".join(text_output)


#把识别的pdf文本还原出原本的段落结构
def process_text(text):
    # 移除所有空格
    text = text.replace(' ', '')
    text = text.replace('\n\n\n', '\n')
    text = text.replace('\n\n', '\n')
    
    # 去除掉页脚 -1-
    pattern = r'-\d+-'
    text = re.sub(pattern, "", text)


    # 预定义中文标点符号和数字
    punctuation = '。！？；：.，,、》“)(][〔≤《〕（－'
    chinese_numbers = '一二三四五六七八九十'

    # 定义一个处理换行符的函数
    def is_valid_newline(index):
        # 检查索引是否越界
        if index == 0 or index >= len(text) - 1:
            return False

        # 如果换行符前后的字符都是中文且不是标点符号，则不是有效的换行符
        if is_chinese(text[index - 1]) and is_chinese(text[index + 1]):
            return False
        # 如果换行符前是逗号或顿号，则不是有效的换行符
        elif (text[index - 1] in '.，,、》“)(][〔≤《〕（－') or (text[index + 1] in '.，,、》“)(][〔≤《〕（－'):
            return False
        else:
            return True

    # 定义一个检查字符是否是中文的函数
    def is_chinese(char):
        return ('\u4e00' <= char <= '\u9fff') or char.isalpha() or char.isdigit()

    # 处理文本中的每个换行符
    new_text = ""
    i = 0
    while i < len(text):
        if text[i] == '\n':
            if is_valid_newline(i):
                new_text += '\n'
            i += 1
        else:
            new_text += text[i]
            i += 1

    return new_text

def par_pdf(string):
    file_paths = download_pdfs_from_string(string)
    text_output = ""
    for pdf_path in file_paths:
        # 尝试直接从PDF提取文本
        text = extract_text_from_pdf(pdf_path)
        if not text.strip():  # 检查提取的文本是否为空
            # 如果直接提取失败，使用OCR
            text =  pdf_to_text_ocr(pdf_path, poppler_path)
        text_output += text
        print('Your pdf file is recognized:')
    return print(process_text(text_output))
    
    