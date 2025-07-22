// 基本功能腳本
// 主要邏輯已經在 index.html 中的 <script> 標籤內

console.log('Market Analysis System - Frontend Scripts Loaded');

// 全域錯誤處理
window.addEventListener('error', (e) => {
    console.error('JavaScript 錯誤:', e.error);
});

// 全域未處理的 Promise 拒絕
window.addEventListener('unhandledrejection', (e) => {
    console.error('未處理的 Promise 拒絕:', e.reason);
});

// 確保頁面加載完成後執行
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ DOM 已加載完成');
});