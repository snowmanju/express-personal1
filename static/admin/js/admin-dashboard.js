/**
 * 管理后台仪表板 JavaScript
 * Admin Dashboard JavaScript
 */

class AdminDashboard {
    constructor() {
        this.currentUser = null;
        this.currentSection = 'dashboard';
        this.manifests = [];
        this.currentPage = 1;
        this.totalPages = 1;
        
        this.init();
    }
    
    async init() {
        console.log('[AdminDashboard] 初始化开始');
        console.log('[AdminDashboard] 当前URL:', window.location.href);
        console.log('[AdminDashboard] localStorage Token:', localStorage.getItem('admin_token') ? '存在' : '不存在');
        console.log('[AdminDashboard] sessionStorage Token:', sessionStorage.getItem('admin_token') ? '存在' : '不存在');
        
        // 等待一小段时间，确保Token已经保存（如果是从登录页跳转过来的）
        await new Promise(resolve => setTimeout(resolve, 200));
        
        // 检查认证状态
        await this.checkAuth();
        
        // 如果认证成功（没有被跳转走），继续初始化
        if (this.currentUser) {
            console.log('[AdminDashboard] 认证成功，继续初始化');
            
            // 初始化事件监听器
            this.initEventListeners();
            
            // 加载仪表板数据
            await this.loadDashboard();
            
            console.log('[AdminDashboard] 初始化完成');
        } else {
            console.log('[AdminDashboard] 认证失败或正在跳转');
        }
    }
    
    async checkAuth(retryCount = 0) {
        console.log(`[checkAuth] 开始认证检查 (尝试 ${retryCount + 1}/3)`);
        
        const token = localStorage.getItem('admin_token') || sessionStorage.getItem('admin_token');
        if (!token) {
            console.log('[checkAuth] 未找到Token，跳转到登录页');
            // 延迟跳转，避免与登录页的跳转冲突
            setTimeout(() => {
                window.location.href = '/admin/login.html';
            }, 100);
            return;
        }
        
        console.log(`[checkAuth] 找到Token: ${token.substring(0, 30)}...`);
        
        try {
            console.log('[checkAuth] 发送验证请求到 /api/v1/admin/me');
            const response = await fetch('/api/v1/admin/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            console.log(`[checkAuth] 响应状态: ${response.status}`);
            
            if (response.ok) {
                this.currentUser = await response.json();
                console.log(`[checkAuth] 认证成功，用户: ${this.currentUser.username}`);
                const usernameElement = document.getElementById('currentUsername');
                if (usernameElement) {
                    usernameElement.textContent = this.currentUser.username;
                }
            } else {
                console.error(`[checkAuth] 认证失败，状态码: ${response.status}`);
                
                // 如果是401且还有重试次数，等待后重试
                if (response.status === 401 && retryCount < 2) {
                    console.log(`[checkAuth] 401错误，${500 * (retryCount + 1)}ms后重试...`);
                    await new Promise(resolve => setTimeout(resolve, 500 * (retryCount + 1)));
                    return this.checkAuth(retryCount + 1);
                }
                
                // 重试失败或其他错误，清除Token并跳转
                console.log('[checkAuth] 清除Token并跳转到登录页');
                localStorage.removeItem('admin_token');
                sessionStorage.removeItem('admin_token');
                localStorage.removeItem('admin_user');
                setTimeout(() => {
                    window.location.href = '/admin/login.html';
                }, 100);
            }
        } catch (error) {
            console.error('[checkAuth] 请求异常:', error);
            
            // 如果还有重试次数，等待后重试
            if (retryCount < 2) {
                console.log(`[checkAuth] 网络错误，${500 * (retryCount + 1)}ms后重试...`);
                await new Promise(resolve => setTimeout(resolve, 500 * (retryCount + 1)));
                return this.checkAuth(retryCount + 1);
            }
            
            // 重试失败，清除Token并跳转
            console.log('[checkAuth] 重试失败，清除Token并跳转到登录页');
            localStorage.removeItem('admin_token');
            sessionStorage.removeItem('admin_token');
            localStorage.removeItem('admin_user');
            setTimeout(() => {
                window.location.href = '/admin/login.html';
            }, 100);
        }
    }
    
    initEventListeners() {
        // 导航菜单点击
        document.querySelectorAll('[data-section]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.target.closest('[data-section]').dataset.section;
                this.showSection(section);
            });
        });
        
        // 退出登录
        document.getElementById('logoutBtn').addEventListener('click', (e) => {
            e.preventDefault();
            this.logout();
        });
        
        // 文件上传表单
        document.getElementById('uploadForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleFileUpload();
        });
        
        // 清除上传表单
        document.getElementById('clearUploadBtn').addEventListener('click', () => {
            this.clearUploadForm();
        });
        
        // 搜索表单
        document.getElementById('searchForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.searchManifests();
        });
        
        // 全选复选框
        document.getElementById('selectAll').addEventListener('change', (e) => {
            this.toggleSelectAll(e.target.checked);
        });
        
        // 批量删除按钮
        document.getElementById('batchDeleteBtn').addEventListener('click', () => {
            this.batchDeleteManifests();
        });
        
        // 编辑理货单表单
        document.getElementById('editManifestForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveManifest();
        });
        
        // 保存理货单按钮
        document.getElementById('saveManifestBtn').addEventListener('click', () => {
            this.saveManifest();
        });
    }
    
    showSection(sectionName) {
        // 隐藏所有内容区域
        document.querySelectorAll('.content-section').forEach(section => {
            section.style.display = 'none';
        });
        
        // 显示目标区域
        const targetSection = document.getElementById(sectionName + 'Section');
        if (targetSection) {
            targetSection.style.display = 'block';
        }
        
        // 更新导航状态
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');
        
        this.currentSection = sectionName;
        
        // 根据区域加载相应数据
        switch (sectionName) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'manifests':
                this.loadManifests();
                break;
            case 'upload':
                // 上传区域不需要额外加载
                break;
        }
    }
    
    async loadDashboard() {
        try {
            this.showLoading();
            
            const response = await this.apiRequest('/api/v1/admin/manifest/statistics');
            
            if (response.success) {
                this.updateStatistics(response.data);
            } else {
                this.showError('加载统计信息失败');
            }
        } catch (error) {
            console.error('Load dashboard failed:', error);
            this.showError('加载仪表板失败');
        } finally {
            this.hideLoading();
        }
    }
    
    updateStatistics(stats) {
        document.getElementById('totalManifests').textContent = stats.total_count || 0;
        document.getElementById('todayUploads').textContent = stats.recent_count || 0;
        document.getElementById('uniqueCustomers').textContent = stats.unique_customers || 0;
        document.getElementById('uniqueTransports').textContent = stats.unique_transports || 0;
    }
    
    async handleFileUpload() {
        const fileInput = document.getElementById('manifestFile');
        const previewOnly = document.getElementById('previewOnly').checked;
        const uploadBtn = document.getElementById('uploadBtn');
        
        if (!fileInput.files.length) {
            this.showAlert('请选择要上传的文件', 'danger');
            return;
        }
        
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);
        formData.append('preview_only', previewOnly);
        
        try {
            this.setUploadButtonLoading(true);
            
            const response = await fetch('/api/v1/admin/manifest/upload', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
                },
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showUploadResults(result);
                if (!previewOnly) {
                    this.showAlert('文件上传成功！', 'success');
                    this.clearUploadForm();
                } else {
                    this.showAlert('文件预览成功！', 'info');
                }
            } else {
                this.showAlert(`上传失败: ${result.errors ? result.errors.join(', ') : '未知错误'}`, 'danger');
            }
        } catch (error) {
            console.error('Upload failed:', error);
            this.showAlert('上传失败，请稍后重试', 'danger');
        } finally {
            this.setUploadButtonLoading(false);
        }
    }
    
    showUploadResults(result) {
        const resultsDiv = document.getElementById('uploadResults');
        const statisticsDiv = document.getElementById('uploadStatistics');
        const previewContainer = document.getElementById('dataPreviewContainer');
        
        // 显示统计信息
        let statisticsHtml = '<div class="row">';
        
        if (result.statistics) {
            const stats = result.statistics;
            statisticsHtml += `
                <div class="col-md-3">
                    <div class="text-center">
                        <h4 class="text-primary">${stats.total_rows || stats.total || 0}</h4>
                        <p class="mb-0">总行数</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="text-center">
                        <h4 class="text-success">${stats.valid_rows || stats.inserted || 0}</h4>
                        <p class="mb-0">有效行数</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="text-center">
                        <h4 class="text-warning">${stats.invalid_rows || stats.updated || 0}</h4>
                        <p class="mb-0">错误行数</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="text-center">
                        <h4 class="text-info">${stats.skipped || 0}</h4>
                        <p class="mb-0">跳过行数</p>
                    </div>
                </div>
            `;
        }
        
        statisticsHtml += '</div>';
        statisticsDiv.innerHTML = statisticsHtml;
        
        // 显示预览数据
        if (result.preview_data && result.preview_data.length > 0) {
            this.showDataPreview(result.preview_data);
            previewContainer.style.display = 'block';
        } else {
            previewContainer.style.display = 'none';
        }
        
        resultsDiv.style.display = 'block';
    }
    
    showDataPreview(previewData) {
        const tableHead = document.getElementById('previewTableHead');
        const tableBody = document.getElementById('previewTableBody');
        
        if (previewData.length === 0) return;
        
        // 构建表头
        const firstRow = previewData[0];
        const columns = Object.keys(firstRow.data || {});
        
        let headHtml = '<tr><th>行号</th>';
        columns.forEach(col => {
            headHtml += `<th>${col}</th>`;
        });
        headHtml += '<th>状态</th></tr>';
        tableHead.innerHTML = headHtml;
        
        // 构建表体
        let bodyHtml = '';
        previewData.forEach(row => {
            const rowClass = row.valid ? '' : 'table-danger';
            bodyHtml += `<tr class="${rowClass}">`;
            bodyHtml += `<td>${row.row_number}</td>`;
            
            columns.forEach(col => {
                const value = row.data[col] || '';
                bodyHtml += `<td>${value}</td>`;
            });
            
            const statusBadge = row.valid 
                ? '<span class="badge bg-success">有效</span>'
                : `<span class="badge bg-danger" title="${row.errors ? row.errors.join(', ') : ''}">错误</span>`;
            bodyHtml += `<td>${statusBadge}</td>`;
            bodyHtml += '</tr>';
        });
        
        tableBody.innerHTML = bodyHtml;
    }
    
    clearUploadForm() {
        document.getElementById('uploadForm').reset();
        document.getElementById('uploadResults').style.display = 'none';
        document.getElementById('dataPreviewContainer').style.display = 'none';
    }
    
    setUploadButtonLoading(loading) {
        const uploadBtn = document.getElementById('uploadBtn');
        const btnText = uploadBtn.querySelector('.btn-text');
        const spinner = uploadBtn.querySelector('.spinner-border');
        
        if (loading) {
            uploadBtn.disabled = true;
            btnText.style.display = 'none';
            spinner.classList.remove('d-none');
        } else {
            uploadBtn.disabled = false;
            btnText.style.display = 'inline';
            spinner.classList.add('d-none');
        }
    }
    
    async loadManifests(page = 1) {
        try {
            this.showLoading();
            
            const searchQuery = document.getElementById('searchQuery').value;
            const transportFilter = document.getElementById('transportFilter').value;
            const customerFilter = document.getElementById('customerFilter').value;
            
            const params = new URLSearchParams({
                page: page,
                limit: 20
            });
            
            if (searchQuery) params.append('q', searchQuery);
            if (transportFilter) params.append('transport_code', transportFilter);
            if (customerFilter) params.append('customer_code', customerFilter);
            
            const response = await this.apiRequest(`/api/v1/admin/manifest/search?${params}`);
            
            if (response.success) {
                this.manifests = response.data;
                this.currentPage = response.pagination.page;
                this.totalPages = response.pagination.total_pages;
                this.renderManifestsTable();
                this.renderPagination();
            } else {
                this.showError('加载理货单列表失败');
            }
        } catch (error) {
            console.error('Load manifests failed:', error);
            this.showError('加载理货单列表失败');
        } finally {
            this.hideLoading();
        }
    }
    
    renderManifestsTable() {
        const tbody = document.getElementById('manifestsTableBody');
        
        if (this.manifests.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center py-4">暂无数据</td></tr>';
            return;
        }
        
        let html = '';
        this.manifests.forEach(manifest => {
            html += `
                <tr>
                    <td>
                        <input type="checkbox" class="form-check-input manifest-checkbox" value="${manifest.id}">
                    </td>
                    <td>${manifest.tracking_number}</td>
                    <td>${manifest.package_number || '-'}</td>
                    <td>${manifest.manifest_date || '-'}</td>
                    <td>${manifest.transport_code}</td>
                    <td>${manifest.customer_code}</td>
                    <td>${manifest.goods_code}</td>
                    <td>${manifest.weight || '-'}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary me-1" onclick="adminDashboard.editManifest(${manifest.id})">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="adminDashboard.deleteManifest(${manifest.id})">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        
        tbody.innerHTML = html;
        
        // 更新批量删除按钮状态
        this.updateBatchDeleteButton();
        
        // 添加复选框事件监听器
        document.querySelectorAll('.manifest-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateBatchDeleteButton();
            });
        });
    }
    
    renderPagination() {
        const paginationContainer = document.getElementById('paginationContainer');
        const pagination = document.getElementById('pagination');
        
        if (this.totalPages <= 1) {
            paginationContainer.style.display = 'none';
            return;
        }
        
        let html = '';
        
        // 上一页
        if (this.currentPage > 1) {
            html += `<li class="page-item"><a class="page-link" href="#" onclick="adminDashboard.loadManifests(${this.currentPage - 1})">上一页</a></li>`;
        }
        
        // 页码
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(this.totalPages, this.currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            const activeClass = i === this.currentPage ? 'active' : '';
            html += `<li class="page-item ${activeClass}"><a class="page-link" href="#" onclick="adminDashboard.loadManifests(${i})">${i}</a></li>`;
        }
        
        // 下一页
        if (this.currentPage < this.totalPages) {
            html += `<li class="page-item"><a class="page-link" href="#" onclick="adminDashboard.loadManifests(${this.currentPage + 1})">下一页</a></li>`;
        }
        
        pagination.innerHTML = html;
        paginationContainer.style.display = 'block';
    }
    
    searchManifests() {
        this.loadManifests(1);
    }
    
    toggleSelectAll(checked) {
        document.querySelectorAll('.manifest-checkbox').forEach(checkbox => {
            checkbox.checked = checked;
        });
        this.updateBatchDeleteButton();
    }
    
    updateBatchDeleteButton() {
        const checkedBoxes = document.querySelectorAll('.manifest-checkbox:checked');
        const batchDeleteBtn = document.getElementById('batchDeleteBtn');
        
        if (checkedBoxes.length > 0) {
            batchDeleteBtn.style.display = 'inline-block';
        } else {
            batchDeleteBtn.style.display = 'none';
        }
    }
    
    async editManifest(manifestId) {
        try {
            const response = await this.apiRequest(`/api/v1/admin/manifest/${manifestId}`);
            
            if (response.success) {
                this.populateEditForm(response.data);
                const modal = new bootstrap.Modal(document.getElementById('editManifestModal'));
                modal.show();
            } else {
                this.showAlert('获取理货单信息失败', 'danger');
            }
        } catch (error) {
            console.error('Edit manifest failed:', error);
            this.showAlert('获取理货单信息失败', 'danger');
        }
    }
    
    populateEditForm(manifest) {
        document.getElementById('editManifestId').value = manifest.id;
        document.getElementById('editTrackingNumber').value = manifest.tracking_number;
        document.getElementById('editPackageNumber').value = manifest.package_number || '';
        document.getElementById('editManifestDate').value = manifest.manifest_date || '';
        document.getElementById('editTransportCode').value = manifest.transport_code;
        document.getElementById('editCustomerCode').value = manifest.customer_code;
        document.getElementById('editGoodsCode').value = manifest.goods_code;
        document.getElementById('editWeight').value = manifest.weight || '';
        document.getElementById('editLength').value = manifest.length || '';
        document.getElementById('editWidth').value = manifest.width || '';
        document.getElementById('editHeight').value = manifest.height || '';
        document.getElementById('editSpecialFee').value = manifest.special_fee || '';
    }
    
    async saveManifest() {
        const manifestId = document.getElementById('editManifestId').value;
        const formData = {
            tracking_number: document.getElementById('editTrackingNumber').value,
            package_number: document.getElementById('editPackageNumber').value,
            manifest_date: document.getElementById('editManifestDate').value,
            transport_code: document.getElementById('editTransportCode').value,
            customer_code: document.getElementById('editCustomerCode').value,
            goods_code: document.getElementById('editGoodsCode').value,
            weight: document.getElementById('editWeight').value,
            length: document.getElementById('editLength').value,
            width: document.getElementById('editWidth').value,
            height: document.getElementById('editHeight').value,
            special_fee: document.getElementById('editSpecialFee').value
        };
        
        try {
            const response = await this.apiRequest(`/api/v1/admin/manifest/${manifestId}`, {
                method: 'PUT',
                body: JSON.stringify(formData)
            });
            
            if (response.success) {
                this.showAlert('理货单更新成功', 'success');
                const modal = bootstrap.Modal.getInstance(document.getElementById('editManifestModal'));
                modal.hide();
                this.loadManifests(this.currentPage);
            } else {
                this.showAlert(`更新失败: ${response.errors ? response.errors.join(', ') : '未知错误'}`, 'danger');
            }
        } catch (error) {
            console.error('Save manifest failed:', error);
            this.showAlert('保存失败，请稍后重试', 'danger');
        }
    }
    
    async deleteManifest(manifestId) {
        if (!confirm('确定要删除这条理货单记录吗？')) {
            return;
        }
        
        try {
            const response = await this.apiRequest(`/api/v1/admin/manifest/${manifestId}`, {
                method: 'DELETE'
            });
            
            if (response.success) {
                this.showAlert('理货单删除成功', 'success');
                this.loadManifests(this.currentPage);
            } else {
                this.showAlert('删除失败', 'danger');
            }
        } catch (error) {
            console.error('Delete manifest failed:', error);
            this.showAlert('删除失败，请稍后重试', 'danger');
        }
    }
    
    async batchDeleteManifests() {
        const checkedBoxes = document.querySelectorAll('.manifest-checkbox:checked');
        const manifestIds = Array.from(checkedBoxes).map(cb => parseInt(cb.value));
        
        if (manifestIds.length === 0) {
            this.showAlert('请选择要删除的记录', 'warning');
            return;
        }
        
        if (!confirm(`确定要删除选中的 ${manifestIds.length} 条记录吗？`)) {
            return;
        }
        
        try {
            const response = await this.apiRequest('/api/v1/admin/manifest/batch', {
                method: 'DELETE',
                body: JSON.stringify({ manifest_ids: manifestIds })
            });
            
            if (response.success) {
                this.showAlert(`成功删除 ${manifestIds.length} 条记录`, 'success');
                this.loadManifests(this.currentPage);
            } else {
                this.showAlert('批量删除失败', 'danger');
            }
        } catch (error) {
            console.error('Batch delete failed:', error);
            this.showAlert('批量删除失败，请稍后重试', 'danger');
        }
    }
    
    async apiRequest(url, options = {}) {
        const token = localStorage.getItem('admin_token') || sessionStorage.getItem('admin_token');
        
        const defaultOptions = {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        };
        
        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };
        
        const response = await fetch(url, mergedOptions);
        
        if (response.status === 401) {
            localStorage.removeItem('admin_token');
            sessionStorage.removeItem('admin_token');
            localStorage.removeItem('admin_user');
            window.location.href = '/admin/login.html';
            return;
        }
        
        return await response.json();
    }
    
    showLoading() {
        document.getElementById('loadingOverlay').style.display = 'flex';
    }
    
    hideLoading() {
        document.getElementById('loadingOverlay').style.display = 'none';
    }
    
    showAlert(message, type) {
        const alertContainer = document.getElementById('alertContainer');
        const alertClass = type === 'success' ? 'alert-success' : 
                          type === 'danger' ? 'alert-danger' : 
                          type === 'warning' ? 'alert-warning' : 'alert-info';
        
        const alertHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        alertContainer.innerHTML = alertHtml;
        
        // 自动消失
        setTimeout(() => {
            const alert = alertContainer.querySelector('.alert');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }
    
    showError(message) {
        this.showAlert(message, 'danger');
    }
    
    logout() {
        if (confirm('确定要退出登录吗？')) {
            localStorage.removeItem('admin_token');
            sessionStorage.removeItem('admin_token');
            localStorage.removeItem('admin_user');
            window.location.href = '/admin/login.html';
        }
    }
}

// 初始化管理后台
let adminDashboard;
document.addEventListener('DOMContentLoaded', () => {
    adminDashboard = new AdminDashboard();
});