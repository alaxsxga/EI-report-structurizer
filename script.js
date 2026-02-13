// 全域變數儲存當前資料
let currentData = null;

// 處理檔案選擇
function handleFileSelect(event) {
    const file = event.target.files[0];
    const fileNameEl = document.getElementById('file-name');
    const parseBtn = document.getElementById('parse-btn');

    if (file) {
        fileNameEl.textContent = file.name;
        parseBtn.disabled = false;
    } else {
        fileNameEl.textContent = '未選擇檔案';
        parseBtn.disabled = true;
    }
}

// 顯示狀態訊息
function showStatus(message, type) {
    const statusEl = document.getElementById('status-message');
    statusEl.textContent = message;
    statusEl.className = `status-message ${type}`;
}

// 隱藏狀態訊息
function hideStatus() {
    const statusEl = document.getElementById('status-message');
    statusEl.className = 'status-message';
}

// 解析檔案
async function parseFile() {
    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];

    if (!file) {
        showStatus('請先選擇檔案', 'error');
        return;
    }

    const parseBtn = document.getElementById('parse-btn');
    const btnText = parseBtn.querySelector('.btn-text');
    const btnLoader = parseBtn.querySelector('.btn-loader');

    // 顯示載入狀態
    parseBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    showStatus('正在解析檔案...', 'loading');

    try {
        // 建立 FormData
        const formData = new FormData();
        formData.append('file', file);

        // 呼叫 API
        const response = await fetch('/api/parse', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || '解析失敗');
        }

        const result = await response.json();
        currentData = result.structure;

        // 渲染區塊 (左側用 structure，右側用原始文字)
        renderBlocks(result.structure, result.original_text);
        showStatus('✓ 解析成功！', 'success');

        // 3秒後隱藏成功訊息
        setTimeout(hideStatus, 3000);

    } catch (error) {
        console.error('解析錯誤:', error);
        showStatus(`解析失敗: ${error.message}`, 'error');
    } finally {
        // 恢復按鈕狀態
        parseBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
}

// 複製到剪貼簿
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showCopyToast();
    } catch (error) {
        console.error('複製失敗:', error);
        // 備用方案
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showCopyToast();
    }
}

// 顯示複製成功提示
function showCopyToast() {
    const toast = document.getElementById('copy-toast');
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 2000);
}

// 建立區塊
function createBlock(title, content) {
    const block = document.createElement('div');
    block.className = 'block';

    const header = document.createElement('div');
    header.className = 'block-header';

    const titleEl = document.createElement('div');
    titleEl.className = 'block-title';
    titleEl.textContent = title;

    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    copyBtn.textContent = '📋 複製';
    copyBtn.onclick = (e) => {
        e.stopPropagation();
        copyToClipboard(content);
    };

    header.appendChild(titleEl);
    header.appendChild(copyBtn);

    const contentEl = document.createElement('div');
    contentEl.className = 'block-content';
    contentEl.textContent = content;

    block.appendChild(header);
    block.appendChild(contentEl);

    // 點擊區塊也可以複製
    block.onclick = () => {
        copyToClipboard(content);
    };

    return block;
}

// 渲染所有區塊
function renderBlocks(data, originalText) {
    const container = document.getElementById('blocks-container');
    container.innerHTML = '';

    // ... (保留原本卡片渲染邏輯)

    // 區塊1: 綜合評估
    // ... (保留原本複雜的綜合評估邏輯)
    const comprehensiveContent = `家屬主訴與期待
${data.家屬主訴與期待}

問題分析
${data.問題分析.map((item, index) => `${index + 1}. ${item}`).join('\n')}

總結與建議
精細動作部分
${data.總結與建議.精細動作部分.map(item => `- ${item}`).join('\n')}

認知發展
${data.總結與建議.認知發展.map(item => `- ${item}`).join('\n')}

感覺統合部分
${data.總結與建議.感覺統合部分.map(item => `- ${item}`).join('\n')}

人際互動部分
${data.總結與建議.人際互動部分.map(item => `- ${item}`).join('\n')}`;

    container.appendChild(createBlock('職能治療評估', comprehensiveContent));

    // 區塊2: 精細動作評估結果
    const fineMotorResults = data.職能評估.精細動作.評估結果.join('\n');
    container.appendChild(createBlock('精細動作 - 評估工具', fineMotorResults));

    // 區塊3: 精細動作行為觀察及綜合結果
    const fineMotorObservation = data.職能評估.精細動作.行為觀察及綜合結果.join('\n');
    container.appendChild(createBlock('精細動作 - 行為觀察及綜合結果', fineMotorObservation));

    // 區塊4: 精細動作的建議
    const fineMotorSuggestions = data.總結與建議.精細動作部分.map(item => `- ${item}`).join('\n');
    container.appendChild(createBlock('精細動作訓練 - 具體建議', fineMotorSuggestions));

    // 區塊5: 感覺統合行為觀察及綜合結果
    const sensoryObservation = data.職能評估.感覺統合.行為觀察及綜合結果.join('\n');
    container.appendChild(createBlock('感覺統合 - 行為觀察及綜合結果', sensoryObservation));

    // 區塊6: 感覺統合的建議
    const sensorySuggestions = data.總結與建議.感覺統合部分.map(item => `- ${item}`).join('\n');
    container.appendChild(createBlock('感覺統合訓練 - 具體建議', sensorySuggestions));

    // 區塊7-11: 日常生活自理各項目
    const dailyActivities = [
        { key: '飲食', title: '日常生活自理 - 飲食' },
        { key: '穿脫衣', title: '日常生活自理 - 穿脫衣' },
        { key: '盥洗衛生', title: '日常生活自理 - 盥洗衛生' },
        { key: '遊戲活動', title: '日常生活自理 - 遊戲活動' },
        { key: '生活作息及參與', title: '日常生活自理 - 生活作息及參與' }
    ];

    dailyActivities.forEach(activity => {
        const content = data.職能評估.日常生活自理[activity.key].行為觀察及綜合結果;
        container.appendChild(createBlock(activity.title, content));
    });

    // 更新右側原始文件（顯示真正的原始文字順序與表格）
    const originalEl = document.getElementById('original-document');
    originalEl.textContent = originalText;
}


// 初始化
function init() {
    // 添加事件監聽器
    const fileInput = document.getElementById('file-input');
    const parseBtn = document.getElementById('parse-btn');

    fileInput.addEventListener('change', handleFileSelect);
    parseBtn.addEventListener('click', parseFile);

    // 顯示預設提示
    document.getElementById('blocks-container').innerHTML = `
        <div style="text-align: center; padding: 3rem; color: #94a3b8;">
            <p style="font-size: 1.2rem; margin-bottom: 0.5rem;">👋 歡迎使用</p>
            <p>請從上方上傳 DOCX 評估報告檔案開始解析</p>
        </div>`;

    document.getElementById('original-document').innerHTML = `
        <div style="text-align: center; padding: 3rem; color: #94a3b8;">
            <p>解析後的原始 JSON 資料將在此顯示</p>
        </div>`;
}

// 頁面載入完成後初始化
document.addEventListener('DOMContentLoaded', init);
