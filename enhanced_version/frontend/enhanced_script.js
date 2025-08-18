// 增強型RAG問答系統前端腳本

class EnhancedRAGApp {
    constructor() {
        this.token = localStorage.getItem('token');
        this.isSystemInitialized = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkAuthStatus();
    }

    bindEvents() {
        // 登入/註冊事件
        document.getElementById('loginSubmit').addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('registerSubmit').addEventListener('submit', (e) => this.handleRegister(e));
        
        // 主頁面事件
        document.getElementById('initBtn').addEventListener('click', () => this.initializeSystem());
        document.getElementById('sendBtn').addEventListener('click', () => this.sendQuestion());
        document.getElementById('questionInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendQuestion();
            }
        });
        
        // 導航事件
        document.getElementById('statsBtn').addEventListener('click', () => this.showStatsPage());
        document.getElementById('chartsBtn').addEventListener('click', () => this.showChartsPage());
        document.getElementById('logoutBtn').addEventListener('click', () => this.logout());
        document.getElementById('backFromStatsBtn').addEventListener('click', () => this.showMainPage());
        document.getElementById('backFromChartsBtn').addEventListener('click', () => this.showMainPage());
    }

    checkAuthStatus() {
        if (this.token) {
            this.showMainPage();
            this.updateSystemStatus();
        } else {
            this.showLoginPage();
        }
    }

    // 頁面切換
    showPage(pageId) {
        document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
        document.getElementById(pageId).classList.add('active');
    }

    showLoginPage() {
        this.showPage('loginPage');
    }

    showMainPage() {
        this.showPage('mainPage');
    }

    showStatsPage() {
        this.showPage('statsPage');
        this.loadStatistics();
    }

    showChartsPage() {
        this.showPage('chartsPage');
        this.loadCharts();
    }

    // 表單切換
    showLogin() {
        document.getElementById('loginForm').classList.add('active');
        document.getElementById('registerForm').classList.remove('active');
    }

    showRegister() {
        document.getElementById('loginForm').classList.remove('active');
        document.getElementById('registerForm').classList.add('active');
    }

    // API 請求
    async apiRequest(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        if (this.token) {
            defaultOptions.headers.Authorization = `Bearer ${this.token}`;
        }

        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (response.status === 401) {
            this.logout();
            throw new Error('認證失敗，請重新登入');
        }

        return response;
    }

    // 載入指示器
    showLoading() {
        document.getElementById('loadingOverlay').classList.add('active');
    }

    hideLoading() {
        document.getElementById('loadingOverlay').classList.remove('active');
    }

    // 錯誤處理
    showError(message) {
        alert(`錯誤: ${message}`);
    }

    showSuccess(message) {
        alert(`成功: ${message}`);
    }

    // 登入處理
    async handleLogin(e) {
        e.preventDefault();
        
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;

        try {
            this.showLoading();
            
            const response = await this.apiRequest('/login', {
                method: 'POST',
                body: JSON.stringify({ username, password }),
            });

            if (response.ok) {
                const data = await response.json();
                this.token = data.access_token;
                localStorage.setItem('token', this.token);
                this.showMainPage();
                this.updateSystemStatus();
            } else {
                const error = await response.json();
                this.showError(error.detail || '登入失敗');
            }
        } catch (error) {
            this.showError(error.message);
        } finally {
            this.hideLoading();
        }
    }

    // 註冊處理
    async handleRegister(e) {
        e.preventDefault();
        
        const username = document.getElementById('registerUsername').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;

        try {
            this.showLoading();
            
            const response = await this.apiRequest('/register', {
                method: 'POST',
                body: JSON.stringify({ username, email, password }),
            });

            if (response.ok) {
                this.showSuccess('註冊成功，請登入');
                this.showLogin();
                document.getElementById('registerSubmit').reset();
            } else {
                const error = await response.json();
                this.showError(error.detail || '註冊失敗');
            }
        } catch (error) {
            this.showError(error.message);
        } finally {
            this.hideLoading();
        }
    }

    // 登出
    logout() {
        localStorage.removeItem('token');
        this.token = null;
        this.isSystemInitialized = false;
        this.showLoginPage();
    }

    // 更新系統狀態
    async updateSystemStatus() {
        try {
            const response = await this.apiRequest('/health');
            if (response.ok) {
                const data = await response.json();
                document.getElementById('systemStatusText').textContent = 
                    data.rag_initialized ? '已初始化' : '未初始化';
                this.isSystemInitialized = data.rag_initialized;
                
                if (this.isSystemInitialized) {
                    this.enableChat();
                    this.loadBasicStats();
                }
            }
        } catch (error) {
            console.error('無法獲取系統狀態:', error);
        }
    }

    // 載入基本統計
    async loadBasicStats() {
        try {
            const response = await this.apiRequest('/statistics');
            if (response.ok) {
                const data = await response.json();
                document.getElementById('chartsCount').textContent = 
                    data.rag_statistics.total_charts || 0;
                document.getElementById('llmProvider').textContent = 
                    data.rag_statistics.llm_provider || 'Unknown';
            }
        } catch (error) {
            console.error('無法載入統計資料:', error);
        }
    }

    // 初始化系統
    async initializeSystem() {
        try {
            this.showLoading();
            
            const response = await this.apiRequest('/init-rag');
            if (response.ok) {
                const data = await response.json();
                this.showSuccess('系統初始化完成');
                this.isSystemInitialized = true;
                this.enableChat();
                this.updateSystemStatus();
            } else {
                const error = await response.json();
                this.showError(error.detail || '系統初始化失敗');
            }
        } catch (error) {
            this.showError(error.message);
        } finally {
            this.hideLoading();
        }
    }

    // 啟用聊天功能
    enableChat() {
        document.getElementById('questionInput').disabled = false;
        document.getElementById('sendBtn').disabled = false;
        document.getElementById('questionInput').placeholder = '請輸入您的問題...';
    }

    // 發送問題
    async sendQuestion() {
        const questionInput = document.getElementById('questionInput');
        const question = questionInput.value.trim();

        if (!question) return;
        if (!this.isSystemInitialized) {
            this.showError('請先初始化系統');
            return;
        }

        try {
            // 顯示使用者訊息
            this.addMessage('user', question);
            questionInput.value = '';
            
            this.showLoading();
            
            const response = await this.apiRequest('/ask', {
                method: 'POST',
                body: JSON.stringify({ question }),
            });

            if (response.ok) {
                const data = await response.json();
                this.addAssistantMessage(data);
            } else {
                const error = await response.json();
                this.showError(error.detail || '問答處理失敗');
            }
        } catch (error) {
            this.showError(error.message);
        } finally {
            this.hideLoading();
        }
    }

    // 添加訊息到聊天記錄
    addMessage(sender, content) {
        const chatHistory = document.getElementById('chatHistory');
        
        // 移除歡迎訊息
        const welcomeMessage = chatHistory.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const metaDiv = document.createElement('div');
        metaDiv.className = 'message-meta';
        metaDiv.textContent = new Date().toLocaleTimeString();
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(metaDiv);
        messageDiv.appendChild(contentDiv);
        
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    // 添加助手回應（包含圖表）
    addAssistantMessage(data) {
        const chatHistory = document.getElementById('chatHistory');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        
        const metaDiv = document.createElement('div');
        metaDiv.className = 'message-meta';
        metaDiv.innerHTML = `
            回應時間: ${data.response_time.toFixed(2)}s | 
            來源: ${data.sources_count} | 
            圖表: ${data.charts_count}
        `;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = data.answer;
        
        messageDiv.appendChild(metaDiv);
        messageDiv.appendChild(contentDiv);
        
        // 添加圖表部分
        if (data.charts && data.charts.length > 0) {
            const chartsSection = document.createElement('div');
            chartsSection.className = 'charts-section';
            chartsSection.innerHTML = `<h4>📊 相關圖表 (${data.charts.length})</h4>`;
            
            data.charts.forEach(chart => {
                const chartDiv = document.createElement('div');
                chartDiv.className = 'chart-item';
                chartDiv.innerHTML = `
                    <div class="chart-header">
                        ${chart.chart_type} ${chart.chart_number}: ${chart.original_caption}
                    </div>
                    <div class="chart-description">
                        ${chart.generated_description}
                    </div>
                    <div class="chart-meta">
                        <span>頁碼: ${chart.page_number}</span>
                        <span>信心度: ${(chart.confidence_score * 100).toFixed(1)}%</span>
                        <span>來源: ${chart.source_file}</span>
                    </div>
                `;
                chartsSection.appendChild(chartDiv);
            });
            
            messageDiv.appendChild(chartsSection);
        }
        
        // 添加來源部分
        if (data.sources && data.sources.length > 0) {
            const sourcesSection = document.createElement('div');
            sourcesSection.className = 'sources-section';
            sourcesSection.innerHTML = `<h4>📚 參考來源 (${data.sources.length})</h4>`;
            
            data.sources.forEach((source, index) => {
                const sourceDiv = document.createElement('div');
                sourceDiv.className = 'source-item';
                sourceDiv.textContent = `${index + 1}. ${source.content}`;
                sourcesSection.appendChild(sourceDiv);
            });
            
            messageDiv.appendChild(sourcesSection);
        }
        
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    // 載入統計資料
    async loadStatistics() {
        try {
            this.showLoading();
            
            const response = await this.apiRequest('/statistics');
            if (response.ok) {
                const data = await response.json();
                this.displayStatistics(data);
            } else {
                this.showError('無法載入統計資料');
            }
        } catch (error) {
            this.showError(error.message);
        } finally {
            this.hideLoading();
        }
    }

    // 顯示統計資料
    displayStatistics(data) {
        const statsContent = document.getElementById('statsContent');
        
        const ragStats = data.rag_statistics;
        const usageStats = data.usage_statistics;
        
        statsContent.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">${ragStats.total_charts}</div>
                    <div class="stat-label">圖表總數</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${usageStats.total_questions}</div>
                    <div class="stat-label">問答總數</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${usageStats.average_response_time}s</div>
                    <div class="stat-label">平均回應時間</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${usageStats.total_chart_references}</div>
                    <div class="stat-label">圖表引用次數</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${ragStats.llm_provider}</div>
                    <div class="stat-label">LLM提供者</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${ragStats.vectorstore_available ? '✅' : '❌'}</div>
                    <div class="stat-label">向量資料庫</div>
                </div>
            </div>
            
            <h3>📊 圖表類型分布</h3>
            <div class="stats-grid">
                ${Object.entries(ragStats.chart_types).map(([type, count]) => `
                    <div class="stat-card">
                        <div class="stat-value">${count}</div>
                        <div class="stat-label">${type}</div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // 載入圖表庫
    async loadCharts() {
        try {
            this.showLoading();
            
            const response = await this.apiRequest('/charts');
            if (response.ok) {
                const data = await response.json();
                this.displayCharts(data.charts);
            } else {
                this.showError('無法載入圖表庫');
            }
        } catch (error) {
            this.showError(error.message);
        } finally {
            this.hideLoading();
        }
    }

    // 顯示圖表庫
    displayCharts(charts) {
        const chartsContent = document.getElementById('chartsContent');
        
        if (charts.length === 0) {
            chartsContent.innerHTML = '<p>尚無圖表資料</p>';
            return;
        }
        
        chartsContent.innerHTML = `
            <h3>📈 圖表庫 (共 ${charts.length} 個圖表)</h3>
            <div class="charts-grid">
                ${charts.map(chart => `
                    <div class="chart-card">
                        <div class="chart-card-header">
                            <span>${chart.chart_type} ${chart.chart_number}</span>
                            <span>${(chart.confidence_score * 100).toFixed(1)}%</span>
                        </div>
                        <div class="chart-card-description">
                            <strong>原始標題:</strong> ${chart.original_caption}<br><br>
                            <strong>AI描述:</strong> ${chart.generated_description}
                        </div>
                        <div class="chart-card-meta">
                            <span>頁碼: ${chart.page_number}</span>
                            <span>來源: ${chart.source_file}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
}

// 全域函數（HTML 中的 onclick 需要）
function showLogin() {
    app.showLogin();
}

function showRegister() {
    app.showRegister();
}

// 初始化應用程式
const app = new EnhancedRAGApp();