/**
 * Frontend Application for Keywords Checker
 * Handles UI interactions and API calls
 */

const API_BASE_URL = 'http://localhost:5001/api';

// DOM Elements
let skillSelect, productInfo, checkButton, singleResult, singleLoading, singleError;
let excelFile, batchCheckButton, batchLoading, batchError, batchSkillSelect;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    initializeEventListeners();
    loadSkills();
});

/**
 * Initialize DOM element references
 */
function initializeElements() {
    // Single check elements
    skillSelect = document.getElementById('skill-select');
    productInfo = document.getElementById('product-info');
    checkButton = document.getElementById('check-button');
    singleResult = document.getElementById('single-result');
    singleLoading = document.getElementById('single-loading');
    singleError = document.getElementById('single-error');
    
    // Batch check elements
    excelFile = document.getElementById('excel-file');
    batchCheckButton = document.getElementById('batch-check-button');
    batchLoading = document.getElementById('batch-loading');
    batchError = document.getElementById('batch-error');
    batchSkillSelect = document.getElementById('batch-skill-select');
}

/**
 * Initialize event listeners
 */
function initializeEventListeners() {
    // Tab switching
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => switchTab(button.dataset.tab));
    });
    
    // Single check
    checkButton.addEventListener('click', checkProduct);
    
    // Batch check
    excelFile.addEventListener('change', handleFileSelect);
    batchCheckButton.addEventListener('click', checkExcel);
}

/**
 * Switch between tabs
 */
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.toggle('active', button.dataset.tab === tabName);
    });
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}-tab`);
    });
}

/**
 * Load available skills from backend
 */
async function loadSkills() {
    try {
        const response = await fetch(`${API_BASE_URL}/skills`);
        const data = await response.json();
        
        if (data.skills && data.skills.length > 0) {
            // Update both skill select dropdowns
            [skillSelect, batchSkillSelect].forEach(select => {
                select.innerHTML = '';
                data.skills.forEach(skill => {
                    const option = document.createElement('option');
                    option.value = skill.name;
                    option.textContent = `${skill.name} - ${skill.description}`;
                    select.appendChild(option);
                });
            });
        }
    } catch (error) {
        console.error('Failed to load skills:', error);
    }
}

/**
 * Check a single product
 */
async function checkProduct() {
    const productInfoText = productInfo.value.trim();
    
    if (!productInfoText) {
        showError(singleError, '商品情報を入力してください');
        return;
    }
    
    // Show loading
    singleLoading.style.display = 'block';
    singleResult.style.display = 'none';
    singleError.style.display = 'none';
    checkButton.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}/check`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                skill_name: skillSelect.value,
                product_info: productInfoText
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displaySingleResult(data);
        
    } catch (error) {
        showError(singleError, `エラーが発生しました: ${error.message}`);
    } finally {
        singleLoading.style.display = 'none';
        checkButton.disabled = false;
    }
}

/**
 * Display single check result
 */
function displaySingleResult(data) {
    singleResult.style.display = 'block';
    
    // Display conclusion
    const conclusionDiv = document.getElementById('single-conclusion');
    const conclusion = data.conclusion || 'UNKNOWN';
    conclusionDiv.innerHTML = `
        <div class="conclusion-badge ${conclusion.toLowerCase()}">
            ${conclusion === 'OK' ? '✅ OK' : conclusion === 'NG' ? '❌ NG' : '⚠️ 判定不明'}
        </div>
    `;
    
    // Display details
    const detailsDiv = document.getElementById('single-details');
    detailsDiv.innerHTML = `<pre>${escapeHtml(data.result)}</pre>`;
    
    // Display usage
    if (data.usage) {
        const usageDiv = document.getElementById('single-usage');
        usageDiv.innerHTML = `
            <small>
                入力トークン: ${data.usage.input_tokens.toLocaleString()} | 
                出力トークン: ${data.usage.output_tokens.toLocaleString()}
            </small>
        `;
    }
}

/**
 * Handle file selection for batch check
 */
function handleFileSelect(event) {
    const file = event.target.files[0];
    batchCheckButton.disabled = !file;
    batchError.style.display = 'none';
}

/**
 * Check Excel file (batch processing)
 */
async function checkExcel() {
    const file = excelFile.files[0];
    
    if (!file) {
        showError(batchError, 'Excelファイルを選択してください');
        return;
    }
    
    // Show loading
    batchLoading.style.display = 'block';
    batchError.style.display = 'none';
    batchCheckButton.disabled = true;
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('skill_name', batchSkillSelect.value);
        
        const response = await fetch(`${API_BASE_URL}/check-excel`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        // Download the result file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `check_result_${new Date().getTime()}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        // Show success message
        showSuccess(batchError, '✅ チェック完了！結果ファイルがダウンロードされました。');
        
    } catch (error) {
        showError(batchError, `エラーが発生しました: ${error.message}`);
    } finally {
        batchLoading.style.display = 'none';
        batchCheckButton.disabled = false;
    }
}

/**
 * Show error message
 */
function showError(element, message) {
    element.style.display = 'block';
    element.className = 'error-message';
    element.textContent = message;
}

/**
 * Show success message
 */
function showSuccess(element, message) {
    element.style.display = 'block';
    element.className = 'success-message';
    element.textContent = message;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
