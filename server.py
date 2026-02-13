#!/usr/bin/env python3
"""
Flask API 伺服器 - 提供 docx 檔案上傳與解析功能
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import tempfile
import zipfile
from xml.etree import ElementTree as ET

app = Flask(__name__, static_folder='.')
CORS(app)

# 從 app.py 複製解析函數
def parse_docx_structure(docx_path):
    """解析 docx 文件並提取結構化內容"""
    
    if not os.path.exists(docx_path):
        return None
    
    # 讀取 docx
    with zipfile.ZipFile(docx_path, 'r') as docx:
        xml_content = docx.read('word/document.xml')
    
    # 解析 XML
    root = ET.fromstring(xml_content)
    
    # 定義命名空間
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    
    def get_text(element):
        """提取元素中的文字"""
        texts = []
        for t in element.findall('.//w:t', ns):
            if t.text:
                texts.append(t.text)
        return ''.join(texts)
    
    # 儲存所有段落（包含表格內容）以供原始顯示
    all_raw_elements = []
    for child in root.find('.//w:body', ns):
        if child.tag.endswith('p'):
            all_raw_elements.append(get_text(child))
        elif child.tag.endswith('tbl'):
            # 提取表格文字
            for tr in child.findall('.//w:tr', ns):
                row_data = [get_text(tc) for tc in tr.findall('.//w:tc', ns)]
                all_raw_elements.append(" | ".join(row_data))
    
    # 結構化解析 (保留原本邏輯，用於左側卡片)
    paragraphs = [p for p in all_raw_elements if p.strip()]
    
    structure = {
        "基本資訊": {},
        "家屬主訴與期待": "",
        "職能評估": {
            "精細動作": {
                "評估工具": "",
                "評估結果": [],
                "行為觀察及綜合結果": []
            },
            "感覺統合": {
                "評估工具": [],
                "行為觀察及綜合結果": []
            },
            "日常生活自理": {
                "飲食": { "行為觀察及綜合結果": "" },
                "穿脫衣": { "行為觀察及綜合結果": "" },
                "盥洗衛生": { "行為觀察及綜合結果": "" },
                "遊戲活動": { "行為觀察及綜合結果": "" },
                "生活作息及參與": { "行為觀察及綜合結果": "" }
            },
            "其他": ""
        },
        "問題分析": [],
        "總結與建議": {
            "精細動作部分": [],
            "認知發展": [],
            "感覺統合部分": [],
            "人際互動部分": []
        }
    }
    
    # 解析基本資訊
    if len(paragraphs) > 1:
        basic_info = paragraphs[1]
        structure["基本資訊"]["原始內容"] = basic_info
    
    # 解析家屬主訴與期待
    for i, para in enumerate(paragraphs):
        if "家屬主訴與期待" in para:
            if i + 1 < len(paragraphs):
                structure["家屬主訴與期待"] = paragraphs[i + 1]
            break
    
    # 解析精細動作
    in_fine_motor = False
    fine_motor_content = []
    evaluation_results = []
    for i, para in enumerate(paragraphs):
        if "精細動作" in para and ("無異常" in para or "發展遲緩" in para):
            in_fine_motor = True
            continue
        if in_fine_motor:
            if "評估工具：" in para:
                structure["職能評估"]["精細動作"]["評估工具"] = para.replace("評估工具：", "").strip()
                # 抓取評估工具後的評估結果
                j = i + 1
                while j < len(paragraphs) and "行為觀察及綜合結果：" not in paragraphs[j]:
                    if paragraphs[j].strip() and not any(keyword in paragraphs[j] for keyword in ["感覺統合", "日常生活自理"]):
                        evaluation_results.append(paragraphs[j])
                    j += 1
                structure["職能評估"]["精細動作"]["評估結果"] = evaluation_results
            elif "行為觀察及綜合結果：" in para:
                j = i + 1
                while j < len(paragraphs) and not any(keyword in paragraphs[j] for keyword in ["感覺統合", "日常生活自理", "問題分析"]):
                    fine_motor_content.append(paragraphs[j])
                    j += 1
                structure["職能評估"]["精細動作"]["行為觀察及綜合結果"] = fine_motor_content
                in_fine_motor = False
                break
    
    # 解析感覺統合
    in_sensory = False
    sensory_tools = []
    sensory_content = []
    for i, para in enumerate(paragraphs):
        if "感覺統合" in para and ("無異常" in para or "發展遲緩" in para):
            in_sensory = True
            continue
        if in_sensory:
            if "■" in para and ("量表" in para or "觀察" in para or "晤談" in para):
                sensory_tools.append(para.strip())
            elif "行為觀察及綜合結果：" in para:
                j = i + 1
                while j < len(paragraphs) and not any(keyword in paragraphs[j] for keyword in ["日常生活自理", "問題分析"]):
                    sensory_content.append(paragraphs[j])
                    j += 1
                structure["職能評估"]["感覺統合"]["評估工具"] = sensory_tools
                structure["職能評估"]["感覺統合"]["行為觀察及綜合結果"] = sensory_content
                in_sensory = False
                break
    
    # 解析日常生活自理各項目
    daily_activities = ["飲食", "穿脫衣", "盥洗衛生", "遊戲活動", "生活作息及參與"]
    
    for activity in daily_activities:
        for i, para in enumerate(paragraphs):
            if activity in para and ("無異常" in para or "發展遲緩" in para):
                if i + 1 < len(paragraphs) and "行為觀察及綜合結果：" in paragraphs[i + 1]:
                    if i + 2 < len(paragraphs):
                        structure["職能評估"]["日常生活自理"][activity]["行為觀察及綜合結果"] = paragraphs[i + 2]
                elif i + 2 < len(paragraphs) and "行為觀察及綜合結果：" in paragraphs[i + 2]:
                    if i + 3 < len(paragraphs):
                        structure["職能評估"]["日常生活自理"][activity]["行為觀察及綜合結果"] = paragraphs[i + 3]
                break
    
    # 解析其他（認知發展）
    for i, para in enumerate(paragraphs):
        if para.strip() == "其他：":
            if i + 1 < len(paragraphs):
                structure["職能評估"]["其他"] = paragraphs[i + 1]
            break
    
    # 解析問題分析
    in_analysis = False
    for i, para in enumerate(paragraphs):
        if "問題分析" in para:
            in_analysis = True
            continue
        if in_analysis:
            if "總結與建議" in para or "四、總結與建議" in para:
                break
            if para.strip() and not para.startswith("綜合以上"):
                structure["問題分析"].append(para)
    
    # 解析總結與建議
    in_conclusion = False
    current_section = None
    for i, para in enumerate(paragraphs):
        if "總結與建議" in para:
            in_conclusion = True
            continue
        if in_conclusion:
            if "精細動作部分" in para:
                current_section = "精細動作部分"
            elif "認知發展：" in para:
                current_section = "認知發展"
            elif "感覺統合部分：" in para:
                current_section = "感覺統合部分"
            elif "人際互動部分：" in para:
                current_section = "人際互動部分"
            elif current_section and para.strip() and not any(keyword in para for keyword in ["職能治療師", "綜合以上"]):
                structure["總結與建議"][current_section].append(para)

    return {
        "structure": structure,
        "original_text": "\n".join(all_raw_elements)
    }

@app.route('/')
def index():
    """提供首頁"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    """提供靜態檔案"""
    return send_from_directory('.', path)

@app.route('/api/parse', methods=['POST'])
def parse_file():
    """處理檔案上傳並解析"""
    try:
        # 檢查是否有檔案
        if 'file' not in request.files:
            return jsonify({'error': '未選擇檔案'}), 400
        
        file = request.files['file']
        
        # 檢查檔案名稱
        if file.filename == '':
            return jsonify({'error': '未選擇檔案'}), 400
        
        # 檢查檔案類型
        if not file.filename.endswith('.docx'):
            return jsonify({'error': '請上傳 .docx 檔案'}), 400
        
        # 儲存到臨時檔案
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
            file.save(tmp_file.name)
            tmp_path = tmp_file.name
        
        try:
            # 解析檔案
            result = parse_docx_structure(tmp_path)
            
            if result is None:
                return jsonify({'error': '檔案解析失敗'}), 500
            
            return jsonify(result)
        
        finally:
            # 刪除臨時檔案
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        return jsonify({'error': f'解析錯誤: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
