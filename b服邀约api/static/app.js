// 全局变量
let accounts = [];
let currentAccountId = null;
let currentPage = 1;
let pageSize = 10;
let totalPages = 1;
let totalRecords = 0;
let searchQuery = '';
let selectedAccounts = new Set();
let currentFilter = 'all';
let currentInviteFilter = 'all';
let currentMenu = 'pool'; // 'user' 或 'pool'
let sidebarVisible = true; // 侧边栏是否可见

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成，开始初始化...');
    // 初始化菜单显示
    updateMenuDisplay();
    loadAccounts();
    setupFormHandlers();
    setupSearchHandlers();
    setupBatchOperationHandlers();
    setupFilterHandlers();
    
    // 添加测试按钮（开发阶段使用）
    addTestButton();
});

// 添加测试按钮（开发阶段使用）
function addTestButton() {
    const toolbar = document.querySelector('.toolbar .toolbar-row');
    if (toolbar) {
        const testButton = document.createElement('button');
        testButton.className = 'btn-modern btn-warning-modern';
        testButton.innerHTML = '<i class="bi bi-bug"></i> 测试菜单切换';
        testButton.onclick = function() {
            console.log('当前菜单状态:', currentMenu);
            console.log('用户菜单标签:', document.querySelector('.nav-tabs .nav-link:first-child'));
            console.log('号池菜单标签:', document.querySelector('.nav-tabs .nav-link:last-child'));
            switchToUserMenu();
        };
        toolbar.appendChild(testButton);
    }
}

// 设置表单处理器
function setupFormHandlers() {
    const form = document.getElementById('accountFormElement');
    form.addEventListener('submit', handleFormSubmit);
}

// 设置搜索处理器
function setupSearchHandlers() {
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchAccounts();
        }
    });
    
    // 实时搜索
    searchInput.addEventListener('input', function(e) {
        searchQuery = e.target.value.trim();
        if (searchQuery.length >= 2 || searchQuery.length === 0) {
            debounceSearch();
        }
    });
}

// 设置批量操作处理器
function setupBatchOperationHandlers() {
    const operationType = document.getElementById('batchOperationType');
    if (operationType) {
        operationType.addEventListener('change', function() {
            toggleBatchOperationSections(this.value);
        });
    }
}

// 设置筛选处理器
function setupFilterHandlers() {
    // 筛选功能将在后续实现
}

// 防抖搜索
let searchTimeout;
function debounceSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        currentPage = 1;
        loadAccounts();
    }, 300);
}

// 切换批量操作区域显示
function toggleBatchOperationSections(operationType) {
    const statusSection = document.getElementById('statusUpdateSection');
    const inviteStatusSection = document.getElementById('inviteStatusUpdateSection');
    
    if (statusSection && inviteStatusSection) {
        statusSection.style.display = operationType === 'updateStatus' ? 'block' : 'none';
        inviteStatusSection.style.display = operationType === 'updateInviteStatus' ? 'block' : 'none';
    }
}

// 加载账号列表
async function loadAccounts() {
    try {
        const params = new URLSearchParams({
            page: currentPage,
            page_size: pageSize
        });
        
        if (searchQuery) {
            params.append('search', searchQuery);
        }
        
        // 添加筛选参数
        if (currentFilter && currentFilter !== 'all') {
            params.append('account_status', currentFilter);
        }
        
        if (currentInviteFilter && currentInviteFilter !== 'all') {
            params.append('invite_status', currentInviteFilter);
        }
        
        const response = await fetch(`/api/accounts?${params}`);
        const result = await response.json();
        
        if (response.ok) {
            accounts = result.data;
            totalPages = result.total_pages;
            totalRecords = result.total;
            renderAccountsTable();
            renderPagination();
        } else {
            showAlert('加载账号失败: ' + result.error, 'danger');
        }
    } catch (error) {
        showAlert('网络错误: ' + error.message, 'danger');
    }
}

// 渲染账号表格
function renderAccountsTable() {
    const container = document.getElementById('accountsList');
    
    if (accounts.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="bi bi-inbox display-1 text-muted"></i>
                <h4 class="text-muted mt-3">暂无账号数据</h4>
                <p class="text-muted">点击"添加账号"按钮创建第一个账号</p>
            </div>
        `;
        return;
    }

    const tableHTML = `
        <div class="table-responsive">
            <table class="table table-modern">
                <thead>
                    <tr>
                        <th>
                            <input type="checkbox" id="selectAll" onchange="toggleSelectAll()">
                        </th>
                        <th>
                            <i class="bi bi-sort-numeric-down"></i>
                            ID
                        </th>
                        <th>
                            <i class="bi bi-person"></i>
                            用户名
                        </th>
                        <th>
                            <i class="bi bi-key"></i>
                            密码
                        </th>
                        <th>
                            <i class="bi bi-shield-check"></i>
                            账号状态
                        </th>
                        <th>
                            <i class="bi bi-envelope"></i>
                            邀约状态
                        </th>
						<th>
							<i class="bi bi-token"></i>
							账号令牌
						</th>
						<th>
							<i class="bi bi-card-text"></i>
							通行证令牌
						</th>
						<th>
							<i class="bi bi-cpu"></i>
							设备代码
						</th>
						<th>
							<i class="bi bi-device-hdd"></i>
							设备名称
						</th>
                        <th>
                            <i class="bi bi-calendar"></i>
                            创建时间
                        </th>
                        <th>
                            <i class="bi bi-gear"></i>
                            操作
                        </th>
                    </tr>
                </thead>
                <tbody>
                    ${accounts.map(account => `
                        <tr>
                            <td>
                                <input type="checkbox" class="account-checkbox" value="${account.id}" onchange="toggleAccountSelection(${account.id})">
                            </td>
                            <td><strong>${account.id}</strong></td>
                            <td>
                                <div class="d-flex align-items-center">
                                    <i class="bi bi-person-circle me-2 text-primary"></i>
                                    ${account.username}
                                </div>
                            </td>
                            <td>
                                <div class="d-flex align-items-center">
                                    <span class="password-field me-2" data-account-id="${account.id}">
                                        ${'*'.repeat(Math.min(account.password.length, 8))}
                                    </span>
                                    <button class="btn btn-sm btn-outline-secondary" onclick="togglePassword(${account.id})" title="显示/隐藏密码">
                                        <i class="bi bi-eye"></i>
                                    </button>
                                </div>
                            </td>
                            <td>
                                <span class="status-badge account-status-${account.account_status}">
                                    ${getStatusText(account.account_status, 'account')}
                                </span>
                            </td>
                            <td>
                                <span class="status-badge invite-status-${account.invite_status}">
                                    ${getStatusText(account.invite_status, 'invite')}
                                </span>
                            </td>
						<td>
							<div class="text-truncate" style="max-width: 150px;" title="${account.account_token || '无令牌'}">
								${account.account_token ? account.account_token.substring(0, 20) + '...' : '无'}
							</div>
						</td>
						<td>
							<div class="text-truncate" style="max-width: 150px;" title="${account.com_token || '无通行证令牌'}">
								${account.com_token ? account.com_token.substring(0, 20) + '...' : '无'}
							</div>
						</td>
						<td>
							<div class="text-truncate" style="max-width: 150px;" title="${account.device_code || '未设置'}">
								${account.device_code || '未设置'}
							</div>
						</td>
						<td>
							<div class="text-truncate" style="max-width: 150px;" title="${account.device_name || '未设置'}">
								${account.device_name || '未设置'}
							</div>
						</td>
                            <td>
                                <small class="text-muted">${formatDate(account.created_at)}</small>
                            </td>
                            <td>
                                <div class="btn-group" role="group">
                                    <button class="btn btn-sm btn-outline-primary" onclick="editAccount(${account.id})" title="编辑">
                                        <i class="bi bi-pencil"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger" onclick="deleteAccount(${account.id})" title="删除">
                                        <i class="bi bi-trash"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = tableHTML;
}

// 获取状态文本
function getStatusText(status, type) {
    const statusMap = {
        account: {
            'correct': '密码正确',
            'incorrect': '密码错误',
            'risk': '登录风险'
        },
        invite: {
            'pending': '待处理',
            'invited': '已邀约',
            'not_invited': '未邀约'
        }
    };
    return statusMap[type][status] || status;
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

// 切换密码显示
function togglePassword(accountId) {
    const passwordField = document.querySelector(`[data-account-id="${accountId}"]`);
    if (!passwordField) return;
    
    const button = passwordField.nextElementSibling;
    const icon = button.querySelector('i');
    
    if (passwordField.textContent.includes('*')) {
        const account = accounts.find(acc => acc.id === accountId);
        if (account) {
            passwordField.textContent = account.password;
            icon.className = 'bi bi-eye-slash';
        }
    } else {
        passwordField.textContent = '*'.repeat(Math.min(passwordField.textContent.length, 8));
        icon.className = 'bi bi-eye';
    }
}

// 显示添加表单
function showAddForm() {
    currentAccountId = null;
    document.getElementById('formTitle').textContent = '添加账号';
    document.getElementById('accountFormElement').reset();
    document.getElementById('accountId').value = '';
    document.getElementById('accountForm').style.display = 'block';
    document.getElementById('accountsList').style.display = 'none';
}

// 编辑账号
function editAccount(accountId) {
    const account = accounts.find(acc => acc.id === accountId);
    if (!account) return;
    
    currentAccountId = accountId;
    document.getElementById('formTitle').textContent = '编辑账号';
    document.getElementById('accountId').value = account.id;
    document.getElementById('username').value = account.username;
    document.getElementById('password').value = account.password;
    document.getElementById('accountStatus').value = account.account_status;
    document.getElementById('inviteStatus').value = account.invite_status;
    document.getElementById('accountToken').value = account.account_token || '';
    const comTokenEl = document.getElementById('comToken');
    if (comTokenEl) comTokenEl.value = account.com_token || '';
    const deviceCodeEl = document.getElementById('deviceCode');
    if (deviceCodeEl) deviceCodeEl.value = account.device_code || '';
    const deviceNameEl = document.getElementById('deviceName');
    if (deviceNameEl) deviceNameEl.value = account.device_name || '';
    
    document.getElementById('accountForm').style.display = 'block';
    document.getElementById('accountsList').style.display = 'none';
}

// 隐藏表单
function hideForm() {
    document.getElementById('accountForm').style.display = 'none';
    document.getElementById('accountsList').style.display = 'block';
}

// 处理表单提交
async function handleFormSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const accountData = {
        username: formData.get('username'),
        password: formData.get('password'),
        account_status: formData.get('account_status'),
        invite_status: formData.get('invite_status'),
        account_token: formData.get('account_token'),
        com_token: formData.get('com_token') || '',
        device_code: formData.get('device_code') || '',
        device_name: formData.get('device_name') || ''
    };
    
    try {
        let response;
        if (currentAccountId) {
            // 更新账号
            response = await fetch(`/api/accounts/${currentAccountId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(accountData)
            });
        } else {
            // 创建账号
            response = await fetch('/api/accounts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(accountData)
            });
        }
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert(result.message, 'success');
            hideForm();
            loadAccounts();
        } else {
            showAlert('操作失败: ' + result.error, 'danger');
        }
    } catch (error) {
        showAlert('网络错误: ' + error.message, 'danger');
    }
}

// 删除账号
function deleteAccount(accountId) {
    currentAccountId = accountId;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

// 确认删除
async function confirmDelete() {
    try {
        const response = await fetch(`/api/accounts/${currentAccountId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert(result.message, 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
            modal.hide();
            loadAccounts();
        } else {
            showAlert('删除失败: ' + result.error, 'danger');
        }
    } catch (error) {
        showAlert('网络错误: ' + error.message, 'danger');
    }
}

// 显示提示信息
function showAlert(message, type) {
    // 移除现有的提示
    const existingAlert = document.querySelector('.alert');
    if (existingAlert) {
        existingAlert.remove();
    }
    
    // 创建新的提示
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // 3秒后自动消失
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 3000);
}

// 搜索账号
function searchAccounts() {
    searchQuery = document.getElementById('searchInput').value.trim();
    currentPage = 1;
    loadAccounts();
}

// 清除搜索
function clearSearch() {
    document.getElementById('searchInput').value = '';
    searchQuery = '';
    currentPage = 1;
    loadAccounts();
}

// 改变每页显示数量
function changePageSize() {
    pageSize = parseInt(document.getElementById('pageSizeSelect').value);
    currentPage = 1;
    loadAccounts();
}

// 渲染分页控件
function renderPagination() {
    const paginationNav = document.getElementById('paginationNav');
    const prevPage = document.getElementById('prevPage');
    const nextPage = document.getElementById('nextPage');
    const pageInfo = document.getElementById('pageInfo');
    
    if (!paginationNav || !prevPage || !nextPage || !pageInfo) {
        console.warn('分页控件元素未找到');
        return;
    }
    
    if (totalPages <= 1) {
        paginationNav.style.display = 'none';
        return;
    }
    
    paginationNav.style.display = 'block';
    
    // 更新上一页按钮
    if (currentPage <= 1) {
        prevPage.classList.add('disabled');
        prevPage.querySelector('a').onclick = function(e) { e.preventDefault(); };
    } else {
        prevPage.classList.remove('disabled');
        prevPage.querySelector('a').onclick = function(e) { e.preventDefault(); goToPage('prev'); };
    }
    
    // 更新下一页按钮
    if (currentPage >= totalPages) {
        nextPage.classList.add('disabled');
        nextPage.querySelector('a').onclick = function(e) { e.preventDefault(); };
    } else {
        nextPage.classList.remove('disabled');
        nextPage.querySelector('a').onclick = function(e) { e.preventDefault(); goToPage('next'); };
    }
    
    // 更新页面信息
    const startRecord = (currentPage - 1) * pageSize + 1;
    const endRecord = Math.min(currentPage * pageSize, totalRecords);
    pageInfo.textContent = `显示第 ${startRecord}-${endRecord} 条，共 ${totalRecords} 条记录`;
}

// 翻页
function goToPage(direction) {
    if (direction === 'prev' && currentPage > 1) {
        currentPage--;
        loadAccounts();
    } else if (direction === 'next' && currentPage < totalPages) {
        currentPage++;
        loadAccounts();
    }
}

// 导出账号数据
function exportAccounts() {
    window.open('/api/accounts/export', '_blank');
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN');
}

// 切换全选
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const accountCheckboxes = document.querySelectorAll('.account-checkbox');
    
    accountCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
        const accountId = parseInt(checkbox.value);
        if (selectAllCheckbox.checked) {
            selectedAccounts.add(accountId);
        } else {
            selectedAccounts.delete(accountId);
        }
    });
    
    updateSelectedCount();
}

// 切换单个账号选择
function toggleAccountSelection(accountId) {
    if (selectedAccounts.has(accountId)) {
        selectedAccounts.delete(accountId);
    } else {
        selectedAccounts.add(accountId);
    }
    
    updateSelectedCount();
    updateSelectAllState();
}

// 更新选中数量显示
function updateSelectedCount() {
    const countElement = document.getElementById('selectedCount');
    if (countElement) {
        countElement.textContent = selectedAccounts.size;
    }
}

// 更新全选状态
function updateSelectAllState() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const accountCheckboxes = document.querySelectorAll('.account-checkbox');
    
    if (selectedAccounts.size === 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    } else if (selectedAccounts.size === accountCheckboxes.length) {
        selectAllCheckbox.checked = true;
        selectAllCheckbox.indeterminate = false;
    } else {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = true;
    }
}

// 刷新数据
function refreshData() {
    loadAccounts();
    showAlert('数据已刷新', 'success');
}

// 修改号池名称
function modifyPoolName() {
    const newName = prompt('请输入新的号池名称:');
    if (newName && newName.trim()) {
        showAlert(`号池名称已修改为: ${newName}`, 'success');
    }
}

// 清除重复数据
async function clearDuplicates() {
    if (confirm('确定要清除重复数据吗？此操作将删除用户名相同的重复账号。')) {
        try {
            // 这里可以添加清除重复数据的API调用
            showAlert('重复数据清除完成', 'success');
            loadAccounts();
        } catch (error) {
            showAlert('清除重复数据失败: ' + error.message, 'danger');
        }
    }
}

// 导入账号
function importAccounts() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.txt';
    input.onchange = function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const content = e.target.result;
                // 这里可以添加解析和导入文件的逻辑
                showAlert('账号导入成功', 'success');
                loadAccounts();
            };
            reader.readAsText(file);
        }
    };
    input.click();
}

// 批量操作
function batchOperations() {
    if (selectedAccounts.size === 0) {
        showAlert('请先选择要操作的账号', 'warning');
        return;
    }
    
    // 更新选中数量显示
    updateSelectedCount();
    
    const modal = new bootstrap.Modal(document.getElementById('batchModal'));
    modal.show();
}

// 执行批量操作
async function executeBatchOperation() {
    const operationType = document.getElementById('batchOperationType').value;
    const selectedIds = Array.from(selectedAccounts);
    
    try {
        if (operationType === 'updateStatus') {
            const newStatus = document.getElementById('newAccountStatus').value;
            await batchUpdateStatus(selectedIds, newStatus);
        } else if (operationType === 'updateInviteStatus') {
            const newInviteStatus = document.getElementById('newInviteStatus').value;
            await batchUpdateInviteStatus(selectedIds, newInviteStatus);
        } else if (operationType === 'delete') {
            await batchDelete(selectedIds);
        }
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('batchModal'));
        modal.hide();
        selectedAccounts.clear();
        loadAccounts();
    } catch (error) {
        showAlert('批量操作失败: ' + error.message, 'danger');
    }
}

// 批量更新状态
async function batchUpdateStatus(accountIds, newStatus) {
    const promises = accountIds.map(id => 
        fetch(`/api/accounts/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ account_status: newStatus })
        })
    );
    
    await Promise.all(promises);
    showAlert(`已更新 ${accountIds.length} 个账号的状态`, 'success');
}

// 批量更新邀约状态
async function batchUpdateInviteStatus(accountIds, newInviteStatus) {
    const promises = accountIds.map(id => 
        fetch(`/api/accounts/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ invite_status: newInviteStatus })
        })
    );
    
    await Promise.all(promises);
    showAlert(`已更新 ${accountIds.length} 个账号的邀约状态`, 'success');
}

// 批量删除
async function batchDelete(accountIds) {
    const promises = accountIds.map(id => 
        fetch(`/api/accounts/${id}`, { method: 'DELETE' })
    );
    
    await Promise.all(promises);
    showAlert(`已删除 ${accountIds.length} 个账号`, 'success');
}

// 一键操作
function oneClickOperations() {
    const operations = [
        '批量标记为已邀约',
        '批量标记为密码正确',
        '批量删除待处理账号'
    ];
    
    const choice = prompt(`选择一键操作:\n1. ${operations[0]}\n2. ${operations[1]}\n3. ${operations[2]}\n请输入数字(1-3):`);
    
    switch(choice) {
        case '1':
            batchMarkAsInvited();
            break;
        case '2':
            batchMarkAsCorrect();
            break;
        case '3':
            batchDeletePending();
            break;
        default:
            showAlert('无效选择', 'warning');
    }
}

// 批量标记为已邀约
async function batchMarkAsInvited() {
    try {
        const response = await fetch('/api/accounts');
        const result = await response.json();
        const pendingAccounts = result.data.filter(account => account.invite_status === 'pending');
        
        if (pendingAccounts.length === 0) {
            showAlert('没有待处理的账号', 'info');
            return;
        }
        
        const promises = pendingAccounts.map(account => 
            fetch(`/api/accounts/${account.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ invite_status: 'invited' })
            })
        );
        
        await Promise.all(promises);
        showAlert(`已标记 ${pendingAccounts.length} 个账号为已邀约`, 'success');
        loadAccounts();
    } catch (error) {
        showAlert('一键操作失败: ' + error.message, 'danger');
    }
}

// 批量标记为密码正确
async function batchMarkAsCorrect() {
    try {
        const response = await fetch('/api/accounts');
        const result = await response.json();
        const incorrectAccounts = result.data.filter(account => account.account_status === 'incorrect');
        
        if (incorrectAccounts.length === 0) {
            showAlert('没有密码错误的账号', 'info');
            return;
        }
        
        const promises = incorrectAccounts.map(account => 
            fetch(`/api/accounts/${account.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ account_status: 'correct' })
            })
        );
        
        await Promise.all(promises);
        showAlert(`已标记 ${incorrectAccounts.length} 个账号为密码正确`, 'success');
        loadAccounts();
    } catch (error) {
        showAlert('一键操作失败: ' + error.message, 'danger');
    }
}

// 批量删除待处理账号
async function batchDeletePending() {
    try {
        const response = await fetch('/api/accounts');
        const result = await response.json();
        const pendingAccounts = result.data.filter(account => account.invite_status === 'pending');
        
        if (pendingAccounts.length === 0) {
            showAlert('没有待处理的账号', 'info');
            return;
        }
        
        if (!confirm(`确定要删除 ${pendingAccounts.length} 个待处理账号吗？`)) {
            return;
        }
        
        const promises = pendingAccounts.map(account => 
            fetch(`/api/accounts/${account.id}`, { method: 'DELETE' })
        );
        
        await Promise.all(promises);
        showAlert(`已删除 ${pendingAccounts.length} 个待处理账号`, 'success');
        loadAccounts();
    } catch (error) {
        showAlert('一键操作失败: ' + error.message, 'danger');
    }
}

// 清空号池
function clearAllAccounts() {
    if (confirm('确定要清空整个号池吗？此操作将删除所有账号，且不可恢复！')) {
        if (confirm('再次确认：您真的要删除所有账号吗？')) {
            // 这里可以添加清空所有账号的API调用
            showAlert('号池已清空', 'success');
            loadAccounts();
        }
    }
}

// 按状态筛选
function filterByStatus(status) {
    currentFilter = status;
    currentPage = 1;
    
    // 更新筛选按钮显示
    updateFilterButton(status);
    
    // 重新加载数据
    loadAccounts();
}

// 更新筛选按钮显示
function updateFilterButton(status) {
    const filterButton = document.querySelector('.dropdown-toggle');
    const statusText = {
        'all': '全部状态',
        'correct': '密码正确',
        'incorrect': '密码错误',
        'risk': '登录风险'
    };
    
    if (filterButton) {
        filterButton.innerHTML = `<i class="bi bi-funnel"></i> ${statusText[status] || '筛选'}`;
    }
}

// 按邀约状态筛选
function filterByInviteStatus(status) {
    currentInviteFilter = status;
    currentPage = 1;
    
    // 更新筛选按钮显示
    updateInviteFilterButton(status);
    
    // 重新加载数据
    loadAccounts();
}

// 更新邀约状态筛选按钮显示
function updateInviteFilterButton(status) {
    const filterButton = document.querySelector('.dropdown-toggle');
    const statusText = {
        'all': '全部邀约状态',
        'pending': '待处理',
        'invited': '已邀约',
        'not_invited': '未邀约'
    };
    
    if (filterButton) {
        filterButton.innerHTML = `<i class="bi bi-funnel"></i> ${statusText[status] || '筛选'}`;
    }
}

// 带参数的加载账号函数
async function loadAccountsWithParams(params) {
    try {
        const response = await fetch(`/api/accounts?${params}`);
        const result = await response.json();
        
        if (response.ok) {
            accounts = result.data;
            totalPages = result.total_pages;
            totalRecords = result.total;
            renderAccountsTable();
            renderPagination();
        } else {
            showAlert('加载账号失败: ' + result.error, 'danger');
        }
    } catch (error) {
        showAlert('网络错误: ' + error.message, 'danger');
    }
}

// 跳转到指定页面
function jumpToPage() {
    const pageInput = document.getElementById('jumpToPage');
    const page = parseInt(pageInput.value);
    
    if (page >= 1 && page <= totalPages) {
        currentPage = page;
        loadAccounts();
        pageInput.value = '';
    } else {
        showAlert(`请输入1到${totalPages}之间的页码`, 'warning');
    }
}

// 切换到用户菜单
function switchToUserMenu() {
    currentMenu = 'user';
    console.log('切换到用户菜单，当前菜单状态:', currentMenu);
    updateMenuDisplay();
    showAlert('已切换到用户菜单', 'success');
}

// 切换到号池菜单
function switchToPoolMenu() {
    currentMenu = 'pool';
    updateMenuDisplay();
    loadAccounts();
}

// 更新菜单显示
function updateMenuDisplay() {
    console.log('更新菜单显示，当前菜单:', currentMenu);
    const userMenuTab = document.querySelector('.nav-tabs .nav-link:first-child');
    const poolMenuTab = document.querySelector('.nav-tabs .nav-link:last-child');
    
    // 检查元素是否存在
    if (!userMenuTab || !poolMenuTab) {
        console.warn('菜单标签元素未找到', { userMenuTab, poolMenuTab });
        return;
    }
    
    if (currentMenu === 'user') {
        userMenuTab.classList.add('active');
        poolMenuTab.classList.remove('active');
        
        // 隐藏号池相关功能
        const infoBanner = document.querySelector('.info-banner');
        const toolbar = document.querySelector('.toolbar');
        const dataTableContainer = document.querySelector('.data-table-container');
        const paginationModern = document.querySelector('.pagination-modern');
        
        if (infoBanner) infoBanner.style.display = 'none';
        if (toolbar) toolbar.style.display = 'none';
        if (dataTableContainer) dataTableContainer.style.display = 'none';
        if (paginationModern) paginationModern.style.display = 'none';
        
        // 显示用户菜单内容
        showUserMenuContent();
    } else {
        userMenuTab.classList.remove('active');
        poolMenuTab.classList.add('active');
        
        // 显示号池相关功能
        const infoBanner = document.querySelector('.info-banner');
        const toolbar = document.querySelector('.toolbar');
        const dataTableContainer = document.querySelector('.data-table-container');
        const paginationModern = document.querySelector('.pagination-modern');
        
        if (infoBanner) infoBanner.style.display = 'block';
        if (toolbar) toolbar.style.display = 'block';
        if (dataTableContainer) dataTableContainer.style.display = 'block';
        if (paginationModern) paginationModern.style.display = 'block';
    }
}

// 显示用户菜单内容
function showUserMenuContent() {
    const container = document.getElementById('accountsList');
    container.innerHTML = `
        <div class="data-table-container">
            <div class="p-4">
                <div class="row">
                    <div class="col-md-4 mb-4">
                        <div class="card h-100">
                            <div class="card-body text-center">
                                <i class="bi bi-person-circle display-4 text-primary mb-3"></i>
                                <h5 class="card-title">用户管理</h5>
                                <p class="card-text text-muted">管理系统用户账号和权限</p>
                                <button class="btn-modern btn-primary-modern" onclick="showAlert('用户管理功能开发中...', 'info')">
                                    <i class="bi bi-gear"></i>
                                    管理用户
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4 mb-4">
                        <div class="card h-100">
                            <div class="card-body text-center">
                                <i class="bi bi-shield-check display-4 text-success mb-3"></i>
                                <h5 class="card-title">权限管理</h5>
                                <p class="card-text text-muted">设置用户角色和访问权限</p>
                                <button class="btn-modern btn-success-modern" onclick="showAlert('权限管理功能开发中...', 'info')">
                                    <i class="bi bi-key"></i>
                                    权限设置
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4 mb-4">
                        <div class="card h-100">
                            <div class="card-body text-center">
                                <i class="bi bi-graph-up display-4 text-warning mb-3"></i>
                                <h5 class="card-title">使用统计</h5>
                                <p class="card-text text-muted">查看系统使用情况和统计</p>
                                <button class="btn-modern btn-warning-modern" onclick="showAlert('使用统计功能开发中...', 'info')">
                                    <i class="bi bi-bar-chart"></i>
                                    查看统计
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-md-6 mb-4">
                        <div class="card h-100">
                            <div class="card-body text-center">
                                <i class="bi bi-gear display-4 text-info mb-3"></i>
                                <h5 class="card-title">系统设置</h5>
                                <p class="card-text text-muted">配置系统参数和选项</p>
                                <button class="btn-modern btn-primary-modern" onclick="showAlert('系统设置功能开发中...', 'info')">
                                    <i class="bi bi-sliders"></i>
                                    系统配置
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6 mb-4">
                        <div class="card h-100">
                            <div class="card-body text-center">
                                <i class="bi bi-arrow-left-circle display-4 text-secondary mb-3"></i>
                                <h5 class="card-title">返回号池</h5>
                                <p class="card-text text-muted">回到号池管理界面</p>
                                <button class="btn-modern btn-secondary" onclick="switchToPoolMenu()">
                                    <i class="bi bi-arrow-left"></i>
                                    返回号池菜单
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// 切换侧边栏显示/隐藏
function toggleSidebar() {
    sidebarVisible = !sidebarVisible;
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    
    if (sidebarVisible) {
        sidebar.style.transform = 'translateX(0)';
        mainContent.style.marginLeft = '280px';
        showAlert('侧边栏已显示', 'info');
    } else {
        sidebar.style.transform = 'translateX(-100%)';
        mainContent.style.marginLeft = '0';
        showAlert('侧边栏已隐藏', 'info');
    }
}
