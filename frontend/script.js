// DOM 元素 - 获取HTML页面中的元素引用
const fileInput = document.getElementById('fileInput');           // 文件选择输入框
const uploadArea = document.getElementById('uploadArea');         // 上传区域
const previewContainer = document.getElementById('previewContainer'); // 预览容器
const resultsContainer = document.getElementById('resultsContainer'); // 结果容器
const generateBtn = document.getElementById('generateBtn');       // 生成按钮
const simpleTestBtn = document.getElementById('simpleTestBtn');   // 测试按钮
const clearBtn = document.getElementById('clearBtn');            // 清空按钮

// 新增的DOM元素
const imageMethodBtn = document.getElementById('imageMethodBtn');
const textMethodBtn = document.getElementById('textMethodBtn');
const imageUploadSection = document.getElementById('imageUploadSection');
const textInputSection = document.getElementById('textInputSection');
const textInput = document.getElementById('textInput');
const imageDescription = document.getElementById('imageDescription'); // 新增：图片描述输入框
const chatHistory = document.getElementById('chatHistory');
const imageChatHistory = document.getElementById('imageChatHistory'); // 新增：图片模式聊天历史
const imageControls = document.getElementById('imageControls');
const textControls = document.getElementById('textControls');

// 历史图片相关元素
const imageHistory = document.getElementById('imageHistory');

// 登录相关元素
const loginModal = document.getElementById('loginModal');
const registerModal = document.getElementById('registerModal');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const showRegister = document.getElementById('showRegister');
const showLogin = document.getElementById('showLogin');
const mainApp = document.getElementById('mainApp');
const welcomeText = document.getElementById('welcomeText');
const usernameDisplay = document.getElementById('usernameDisplay');
const logoutBtn = document.getElementById('logoutBtn');

// 状态管理 - 全局变量存储应用状态
let uploadedImages = [];          // 存储所有上传的图片
let selectedModel = 'creative';    // 当前选择的AI模型
let selectedStyle = 'banner';     // 当前选择的风格
let selectedImageIndices = [];    // 当前选中图片的索引数组
let currentMethod = 'image';      // 当前使用的方法：'image' 或 'text'
let currentSessionId = null;      // 当前会话ID，用于保持对话连续性
let currentImageSessionId = null; // 新增：当前图片模式会话ID
let authToken = null;             // 存储认证令牌
let currentUser = null;           // 存储当前用户信息

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();    // 初始化所有事件监听器
    initSliders();          // 初始化滑块控件
    selectDefaultOptions(); // 设置默认选项
    checkLoginStatus();     // 检查登录状态
    loadImageHistory();     // 加载历史图片
});

function initEventListeners() {
    // 文件上传相关 - 处理用户与文件的交互
    fileInput.addEventListener('change', handleFileSelect);  // 文件选择变化
    uploadArea.addEventListener('dragover', handleDragOver);  // 拖拽到区域上方
    uploadArea.addEventListener('dragleave', handleDragLeave); // 拖拽离开区域
    uploadArea.addEventListener('drop', handleDrop);         // 拖拽释放
    
    // 模型选择 - 处理模型卡片点击
    document.querySelectorAll('.model-card').forEach(card => {
        card.addEventListener('click', () => {
            // 先移除所有卡片的选中状态
            document.querySelectorAll('.model-card').forEach(c => c.classList.remove('selected'));
            // 为当前点击的卡片添加选中状态
            card.classList.add('selected');
            // 更新选中的模型值 - 从HTML的data-model属性获取
            selectedModel = card.dataset.model;  // 例如: 'creative'
        });
    });
    
    // 风格选择 - 处理风格卡片点击
    document.querySelectorAll('.style-card').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('.style-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedStyle = card.dataset.style;  // 例如: 'banner'
        });
    });
    
    // 按钮事件 - 处理功能按钮点击
    generateBtn.addEventListener('click', generateImages);      // 生成按钮
    simpleTestBtn.addEventListener('click', simpleStyleTest);  // 简单测试按钮
    clearBtn.addEventListener('click', clearAll);              // 清空按钮
    
    // 新增：生成方式切换
    imageMethodBtn.addEventListener('click', () => switchMethod('image'));
    textMethodBtn.addEventListener('click', () => switchMethod('text'));

    // 文本输入框回车键支持
    textInput.addEventListener('keydown', function(event) {
        // 检查是否按下Enter键（不按Shift键）
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault(); // 阻止默认换行行为
            console.log('回车键触发生成图片');
            generateImagesFromText(); // 调用生成函数
        }
    });

    // 图片描述输入框回车键支持
    imageDescription.addEventListener('keydown', function(event) {
        // 检查是否按下Enter键（不按Shift键）
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault(); // 阻止默认换行行为
            console.log('图片描述回车键触发生成图片');
            generateImages(); // 调用生成函数
        }
    });
    
    // 登录相关事件
    loginForm.addEventListener('submit', handleLogin);
    registerForm.addEventListener('submit', handleRegister);
    showRegister.addEventListener('click', () => {
        loginModal.style.display = 'none';
        registerModal.style.display = 'flex';
    });
    showLogin.addEventListener('click', () => {
        registerModal.style.display = 'none';
        loginModal.style.display = 'flex';
    });
    logoutBtn.addEventListener('click', handleLogout);
}

// 检查登录状态
function checkLoginStatus() {
    const storedToken = localStorage.getItem('authToken');
    if (storedToken) {
        // 验证令牌是否有效
        verifyToken(storedToken);
    } else {
        // 显示登录界面
        loginModal.style.display = 'flex';
    }
}

// 验证令牌
async function verifyToken(token) {
    try {
        const response = await fetch('http://localhost:5000/profile', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                // 登录有效，显示主界面
                currentUser = data.user;
                authToken = token;
                showMainApp();
            } else {
                // 令牌无效，清除本地存储
                localStorage.removeItem('authToken');
                loginModal.style.display = 'flex';
            }
        } else {
            // 令牌无效，清除本地存储
            localStorage.removeItem('authToken');
            loginModal.style.display = 'flex';
        }
    } catch (error) {
        console.error('验证令牌时出错:', error);
        localStorage.removeItem('authToken');
        loginModal.style.display = 'flex';
    }
}

// 处理登录
async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    if (!username || !password) {
        alert('请输入用户名和密码');
        return;
    }
    
    try {
        const response = await fetch('http://localhost:5000/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 登录成功
            authToken = data.token;
            currentUser = data.user;
            localStorage.setItem('authToken', authToken);
            loginModal.style.display = 'none';
            showMainApp();
        } else {
            alert(data.message || '登录失败');
        }
    } catch (error) {
        console.error('登录错误:', error);
        alert('登录失败，请检查网络连接');
    }
}

// 处理注册
async function handleRegister(e) {
    e.preventDefault();
    
    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    
    if (!username || !email || !password) {
        alert('请填写所有字段');
        return;
    }
    
    try {
        const response = await fetch('http://localhost:5000/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('注册成功，请登录');
            registerModal.style.display = 'none';
            loginModal.style.display = 'flex';
        } else {
            alert(data.message || '注册失败');
        }
    } catch (error) {
        console.error('注册错误:', error);
        alert('注册失败，请检查网络连接');
    }
}

// 显示主应用界面
function showMainApp() {
    loginModal.style.display = 'none';
    registerModal.style.display = 'none';
    mainApp.style.display = 'block';

    // 更新用户信息显示
    if (currentUser) {
        usernameDisplay.textContent = currentUser.username;
    }

    // 登录后立即加载历史图片和聊天历史
    loadImageHistory();
    loadChatHistory();
}

// 处理登出
function handleLogout() {
    if (confirm('确定要退出登录吗？')) {
        authToken = null;
        currentUser = null;
        localStorage.removeItem('authToken');
        mainApp.style.display = 'none';
        loginModal.style.display = 'flex';
    }
}

function switchMethod(method) {
    currentMethod = method;
    
    // 更新按钮样式
    if (method === 'image') {
        imageMethodBtn.classList.add('active');
        textMethodBtn.classList.remove('active');
        imageUploadSection.style.display = 'block';
        textInputSection.style.display = 'none';
        imageControls.style.display = 'block';
        textControls.style.display = 'none';
        simpleTestBtn.style.display = 'block'; // 显示简单测试按钮

        // 切换到图片模式时更新占位符
        updateImageDescriptionPlaceholder();
    } else {
        imageMethodBtn.classList.remove('active');
        textMethodBtn.classList.add('active');
        imageUploadSection.style.display = 'none';
        textInputSection.style.display = 'block';
        imageControls.style.display = 'none';
        textControls.style.display = 'block';
        simpleTestBtn.style.display = 'none'; // 隐藏简单测试按钮

        // 切换到文本模式时更新占位符
        updateTextInputPlaceholder();
    }
}

/**
 * 更新文本输入框的占位符
 * 根据是否有聊天历史来显示不同的提示
 */
function updateTextInputPlaceholder() {
    if (!textInput) return;

    // 检查是否有聊天历史（除了空状态提示以外的消息）
    const chatMessages = chatHistory.querySelectorAll('.chat-message');
    const hasChatHistory = chatMessages.length > 0;

    if (hasChatHistory) {
        textInput.placeholder = '请继续对话...';
    } else {
        textInput.placeholder = '请输入您想要生成的宣传图内容描述，例如：\'一个红色的T恤在白色背景上，旁边有促销文字\'\n提示：输入完成后按回车键或点击生成按钮即可创建图片';
    }
}

/**
 * 更新图片描述输入框的占位符
 * 根据是否有图片聊天历史来显示不同的提示
 */
function updateImageDescriptionPlaceholder() {
    if (!imageDescription) return;

    // 检查是否有图片聊天历史（除了空状态提示以外的消息）
    const imageChatMessages = imageChatHistory.querySelectorAll('.chat-message');
    const hasImageChatHistory = imageChatMessages.length > 0;

    if (hasImageChatHistory) {
        imageDescription.placeholder = '请继续对话...';
    } else {
        imageDescription.placeholder = '请输入对图片的详细描述，例如：\'红色T恤在白色背景上，专业摄影效果\'';
    }
}

function initSliders() {
    // 亮度滑块
    const brightnessSlider = document.getElementById('brightness');
    const brightnessValue = document.getElementById('brightnessValue');
    brightnessSlider.addEventListener('input', () => {
        brightnessValue.textContent = brightnessSlider.value;
    });
    
    // 对比度滑块
    const contrastSlider = document.getElementById('contrast');
    const contrastValue = document.getElementById('contrastValue');
    contrastSlider.addEventListener('input', () => {
        contrastValue.textContent = contrastSlider.value;
    });
    
    // 饱和度滑块
    const saturationSlider = document.getElementById('saturation');
    const saturationValue = document.getElementById('saturationValue');
    saturationSlider.addEventListener('input', () => {
        saturationValue.textContent = saturationSlider.value;
    });
}

function selectDefaultOptions() {
    // 默认选中第一个模型和风格
    document.querySelector('.model-card[data-model="creative"]').classList.add('selected');
    document.querySelector('.style-card[data-style="banner"]').classList.add('selected');
}

// 处理文件选择
function handleFileSelect(e) {
    const files = e.target.files;  // 从文件输入框获取文件列表
    processFiles(files);
}

// 处理拖拽
function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();  // 阻止浏览器默认行为
    uploadArea.classList.remove('dragover');
    const files = e.dataTransfer.files;  // 从拖拽事件获取文件
    processFiles(files);
}

// 处理上传的文件
function processFiles(files) {
    if (!files.length) return;
    
    for (let file of files) {
        // 检查文件类型和大小
        if (!file.type.match('image/jpeg') && !file.type.match('image/png')) {
            alert('只支持 JPG 和 PNG 格式的图片！');
            continue;
        }
        
        if (file.size > 5 * 1024 * 1024) {
            alert('图片大小不能超过 5MB！');
            continue;
        }
        
        const reader = new FileReader();
        reader.onload = (e) => {
            const imageData = e.target.result;  // 获取图片的Base64数据URL
            uploadedImages.push({
                id: Date.now() + Math.random(),  // 生成唯一ID
                name: file.name,                 // 文件名
                data: imageData,                 // Base64数据
                file: file,                      // 原始File对象 - 重要！用于发送到后端
                fileUrl: imageData               // 添加图片URL用于发送到后端
            });
            updatePreview();  // 更新UI显示
        };
        reader.readAsDataURL(file);  // 将文件读取为Base64
    }
    
    fileInput.value = '';
}

// 更新预览区域
function updatePreview() {
    // 始终显示预览区域
    previewSection.style.display = 'block';
    
    // 清空容器，但保留全选按钮
    previewContainer.innerHTML = `
        <button class="btn btn-secondary" id="selectAllBtn">
            <i class="fas fa-check-double"></i> 全选/取消全选
        </button>
    `;
    
    // 重新绑定全选按钮事件
    document.getElementById('selectAllBtn').addEventListener('click', toggleSelectAll);
    
    // 如果没有上传图片，只显示全选按钮（已完成）
    if (uploadedImages.length === 0) {
        return;
    }
    
    uploadedImages.forEach((image, index) => {
        const previewItem = document.createElement('div');
        previewItem.className = 'preview-item';
        previewItem.dataset.index = index;
        
        previewItem.innerHTML = `
            <img src="${image.data}" alt="${image.name}" class="preview-img">
            <button class="remove-btn" onclick="removeImage(${index})">&times;</button>
        `;
        
        // 添加点击事件 - 实现多选功能
        previewItem.addEventListener('click', (e) => {
            // 如果点击的是删除按钮，则不处理选中逻辑
            if (e.target.classList.contains('remove-btn')) return;
            
            // 切换选中状态
            const selectedIndex = parseInt(previewItem.dataset.index);
            const selectedIdx = selectedImageIndices.indexOf(selectedIndex);
            
            if (selectedIdx === -1) {
                // 如果未选中，则添加到选中数组
                selectedImageIndices.push(selectedIndex);
                previewItem.classList.add('selected');
            } else {
                // 如果已选中，则从选中数组移除
                selectedImageIndices.splice(selectedIdx, 1);
                previewItem.classList.remove('selected');
            }
            
            // 更新全选按钮文本
            updateSelectAllButtonText();
        });
        
        // 如果当前图片在选中数组中，添加选中样式
        if (selectedImageIndices.includes(index)) {
            previewItem.classList.add('selected');
        }
        
        previewContainer.appendChild(previewItem);
    });
    
    // 初始化时更新全选按钮文本
    updateSelectAllButtonText();
}

// 更新全选按钮文本
function updateSelectAllButtonText() {
    const selectAllButton = document.getElementById('selectAllBtn');
    if (selectAllButton) {
        if (selectedImageIndices.length === uploadedImages.length && uploadedImages.length > 0) {
            selectAllButton.innerHTML = '<i class="fas fa-check-double"></i> 取消全选';
        } else {
            selectAllButton.innerHTML = '<i class="fas fa-check-double"></i> 全选';
        }
    }
}

// 新增：全选/取消全选功能
function toggleSelectAll() {
    if (selectedImageIndices.length === uploadedImages.length) {
        // 如果当前已全选，则取消全选
        selectedImageIndices = [];
        document.querySelectorAll('#previewContainer .preview-item').forEach(item => {
            item.classList.remove('selected');
        });
    } else {
        // 如果当前未全选，则全选
        selectedImageIndices = [];
        uploadedImages.forEach((_, index) => {
            selectedImageIndices.push(index);
        });
        document.querySelectorAll('#previewContainer .preview-item').forEach(item => {
            item.classList.add('selected');
        });
    }
    
    // 更新按钮文本
    updateSelectAllButtonText();
}

// 删除图片
function removeImage(index) {
    // 从数组中移除指定索引的图片
    uploadedImages.splice(index, 1);
    
    // 更新选中索引 - 所有大于被删除索引的选中项都要减1
    selectedImageIndices = selectedImageIndices
        .map(i => i > index ? i - 1 : i)
        .filter(i => i >= 0); // 确保索引有效
    
    updatePreview();
}

// 生成图片
async function generateImages() {
    if (currentMethod === 'image') {
        await generateImagesFromUpload();
    } else {
        await generateImagesFromText();
    }
}

// 从上传的图片生成
async function generateImagesFromUpload() {
    if (uploadedImages.length === 0) {
        alert('请先上传商品图片！');
        return;
    }
    
    if (selectedImageIndices.length === 0) {
        alert('请至少选择一张图片进行生成！');
        return;
    }
    
    // 显示加载状态
    generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 生成中...';
    generateBtn.disabled = true;

    // 获取用户输入的描述内容
    const userDescription = imageDescription.value.trim();

    // 立即添加用户输入到对话历史
    if (userDescription) {
        addImageChatMessage(userDescription, 'user');
    } else {
        addImageChatMessage(`使用图片生成新图片（无描述）`, 'user');
    }

    // 立即清空图片描述输入框，方便下次对话
    imageDescription.value = '';

    // 获取滑块值 - 从HTML控件获取用户输入
    const brightness = parseInt(document.getElementById('brightness').value);
    const contrast = parseInt(document.getElementById('contrast').value);
    const saturation = parseInt(document.getElementById('saturation').value);
    
    try {
        // 对选中的图片索引进行排序，确保按照上传顺序处理
        const sortedIndices = [...selectedImageIndices].sort((a, b) => a - b);
        
        // 对每张选中的图片进行处理
        for (const index of sortedIndices) {
            const selectedImage = uploadedImages[index];  // 获取选中的图片
            
            // 创建FormData对象 - 用于上传文件
            const formData = new FormData();
            formData.append('image', selectedImage.file);       // 图片文件
            formData.append('model', selectedModel);            // AI模型
            formData.append('style', selectedStyle);            // 风格类型
            formData.append('brightness', brightness);         // 亮度值
            formData.append('contrast', contrast);             // 对比度值
            formData.append('saturation', saturation);          // 饱和度值
            
            // 添加图片描述
            const description = imageDescription.value.trim();
            if (description) {
                formData.append('description', description);
            }
            
            // 添加认证头
            const headers = {};
            if (authToken) {
                headers['Authorization'] = `Bearer ${authToken}`;
            }
            
            // 添加当前图片会话ID
            if (currentImageSessionId) {
                formData.append('session_id', currentImageSessionId);
            }
            
            // 重要：发送HTTP请求到后端
            const response = await fetch('http://localhost:5000/generate', {
                method: 'POST',      // POST方法
                body: formData,      // 表单数据，包含文件和参数
                headers: headers     // 添加认证头
                // 注意：不需要设置Content-Type，浏览器会自动设置
            });
            
            // 检查响应状态
            if (!response.ok) {
                throw new Error('生成失败');
            }
            
            // 解析JSON响应
            const data = await response.json();
            
            // 更新当前图片会话ID（如果后端返回了新的会话ID）
            if (data.session_id) {
                currentImageSessionId = data.session_id;
            }
            
            // 添加系统成功消息到对话历史
            addImageChatMessage(`使用图片 "${selectedImage.name}" 生成了新图片`, 'system');
            
            // 显示生成结果（按生成顺序）
            displayGeneratedImage(data.image_url, selectedImage.name, false, false);
        }

        // 刷新历史图片列表
        refreshImageHistory();
    } catch (error) {
        console.error('生成错误:', error);
        alert('生成失败，请检查网络连接或稍后重试');
    } finally {
        // 恢复按钮状态
        generateBtn.innerHTML = '<i class="fas fa-bolt"></i> 生成宣传图';
        generateBtn.disabled = false;
    }
}

// 从文本生成
async function generateImagesFromText() {
    const textContent = textInput.value.trim();
    if (!textContent) {
        alert('请输入宣传内容描述！');
        return;
    }

    // 立即清空输入框，提供即时反馈
    textInput.value = '';
    
    // 显示加载状态
    generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 生成中...';
    generateBtn.disabled = true;
    
    // 获取文本生成选项
    const promptType = document.getElementById('textPrompt').value;
    const imageSize = document.getElementById('imageSize').value;

    console.log('文本生成参数:', { promptType, imageSize });
    
    try {
        // 记录对话历史
        addChatMessage(textContent, 'user');
        
        // 添加认证头
        const headers = {
            'Content-Type': 'application/json'
        };
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        // 模拟API请求 - 实际项目中需要替换为真实的API
        const response = await fetch('http://localhost:5000/generate-from-text', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                prompt: textContent,
                prompt_type: promptType,
                image_size: imageSize,
                session_id: currentSessionId  // 发送当前会话ID
            })
        });
        
        if (!response.ok) {
            throw new Error('生成失败');
        }
        
        const data = await response.json();
        
        // 更新当前会话ID（如果后端返回了新的会话ID）
        if (data.session_id) {
            currentSessionId = data.session_id;
        }
        
        // 显示生成结果（最新生成的在前面）
        displayGeneratedImage(data.image_url, `文本生成_${new Date().getTime()}`, false, true);
        
        // 记录生成历史
        addChatMessage(`已生成图片: ${textContent}`, 'system');

        // 刷新历史图片列表和聊天历史
        refreshImageHistory();
        refreshChatHistory();
    } catch (error) {
        console.error('文本生成错误:', error);
        alert('生成失败，请检查网络连接或稍后重试');
    } finally {
        // 恢复按钮状态
        generateBtn.innerHTML = '<i class="fas fa-bolt"></i> 生成宣传图';
        generateBtn.disabled = false;
    }
}

// 添加对话消息 - 为文本模式
function addChatMessage(content, sender) {
    // 移除空状态提示
    const emptyChat = chatHistory.querySelector('.empty-chat');
    if (emptyChat) {
        emptyChat.remove();
    }
    
    const messageElement = document.createElement('div');
    messageElement.className = `chat-message ${sender}`;
    
    const timestamp = new Date().toLocaleTimeString();
    
    messageElement.innerHTML = `
        <div class="message-content">${content}</div>
        <div class="message-time">${timestamp}</div>
    `;
    
    chatHistory.appendChild(messageElement);
    
    // 滚动到底部
    chatHistory.scrollTop = chatHistory.scrollHeight;

    // 更新文本输入框占位符
    updateTextInputPlaceholder();
}

// 新增：添加图片模式对话消息
function addImageChatMessage(content, sender) {
    // 移除空状态提示
    const emptyChat = imageChatHistory.querySelector('.empty-chat');
    if (emptyChat) {
        emptyChat.remove();
    }
    
    const messageElement = document.createElement('div');
    messageElement.className = `chat-message ${sender}`;
    
    const timestamp = new Date().toLocaleTimeString();
    
    messageElement.innerHTML = `
        <div class="message-content">${content}</div>
        <div class="message-time">${timestamp}</div>
    `;
    
    imageChatHistory.appendChild(messageElement);

    // 滚动到底部
    imageChatHistory.scrollTop = imageChatHistory.scrollHeight;

    // 更新图片描述输入框占位符
    updateImageDescriptionPlaceholder();
}

// 简单风格测试（无需联网）
async function simpleStyleTest() {
    if (currentMethod === 'image') {
        if (uploadedImages.length === 0) {
            alert('请先上传商品图片！');
            return;
        }
        
        if (selectedImageIndices.length === 0) {
            alert('请至少选择一张图片进行测试！');
            return;
        }
        
        // 获取滑块值
        const brightness = parseInt(document.getElementById('brightness').value);
        const contrast = parseInt(document.getElementById('contrast').value);
        const saturation = parseInt(document.getElementById('saturation').value);
        
        // 对选中的图片索引进行排序，确保按照上传顺序处理
        const sortedIndices = [...selectedImageIndices].sort((a, b) => a - b);
        
        // 对每张选中的图片进行处理
        for (const index of sortedIndices) {
            const selectedImage = uploadedImages[index];
            
            // 创建canvas进行简单处理
            const img = new Image();
            img.onload = function() {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                // 设置canvas尺寸
                canvas.width = img.width;
                canvas.height = img.height;
                
                // 绘制原始图片
                ctx.drawImage(img, 0, 0);
                
                // 应用简单滤镜效果
                applyFilters(ctx, canvas.width, canvas.height, brightness, contrast, saturation);
                
                // 转换为DataURL
                const processedDataURL = canvas.toDataURL('image/jpeg', 0.9);
                
                // 显示结果
                displayGeneratedImage(processedDataURL, `test_${selectedImage.name}`, true, true);
            };
            
            img.src = selectedImage.data;
        }
    } else {
        // 文本模式下的简单测试
        const textContent = textInput.value.trim();
        if (!textContent) {
            alert('请输入宣传内容描述！');
            return;
        }
        
        // 对于文本模式，直接显示提示信息，因为文本模式不支持简单测试
        alert('文本模式下的自定义调节生成图片功能暂未实现');
    }
}

// 应用滤镜效果
function applyFilters(ctx, width, height, brightness, contrast, saturation) {
    const imageData = ctx.getImageData(0, 0, width, height);
    const data = imageData.data;
    
    // 应用亮度
    if (brightness !== 0) {
        const factor = (brightness + 100) / 100;
        for (let i = 0; i < data.length; i += 4) {
            data[i] *= factor;     // R
            data[i + 1] *= factor; // G
            data[i + 2] *= factor; // B
        }
    }
    
    // 应用对比度
    if (contrast !== 0) {
        const factor = (contrast + 100) / 100;
        const intercept = 128 * (1 - factor);
        for (let i = 0; i < data.length; i += 4) {
            data[i] = data[i] * factor + intercept;     // R
            data[i + 1] = data[i + 1] * factor + intercept; // G
            data[i + 2] = data[i + 2] * factor + intercept; // B
        }
    }
    
    // 应用饱和度
    if (saturation !== 0) {
        const factor = (saturation + 100) / 100;
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            const gray = 0.2989 * r + 0.5870 * g + 0.1140 * b;
            
            data[i] = gray + (r - gray) * factor;     // R
            data[i + 1] = gray + (g - gray) * factor; // G
            data[i + 2] = gray + (b - gray) * factor; // B
        }
    }
    
    ctx.putImageData(imageData, 0, 0);
}

// 显示生成的图片
function displayGeneratedImage(imageUrl, originalName, isTest = false, prepend = false) {
    // 移除空状态提示
    const emptyResults = resultsContainer.querySelector('.empty-results');
    if (emptyResults) {
        emptyResults.remove();
    }
    
    // 创建结果项
    const resultItem = document.createElement('div');
    resultItem.className = 'result-item';
    
    const timestamp = new Date().toLocaleTimeString();
    const resultName = isTest ? `测试_${originalName}` : `生成_${originalName}`;
    
    resultItem.innerHTML = `
        <img src="${imageUrl}" alt="${resultName}" class="result-img">
        <button class="download-btn">
            <i class="fas fa-download"></i> 下载
        </button>
        <div style="padding: 10px; font-size: 0.8rem; color: #666;">
            <div>${resultName}</div>
            <div>${timestamp}</div>
        </div>
    `;

    // 为下载按钮添加事件监听器
    const downloadBtn = resultItem.querySelector('.download-btn');
    downloadBtn.addEventListener('click', () => {
        downloadImage(imageUrl, resultName);
    });
    
    // 添加到结果容器
    if (prepend) {
        // 新图片显示在前面（用于文本生成）
        if (resultsContainer.firstChild) {
            resultsContainer.insertBefore(resultItem, resultsContainer.firstChild);
        } else {
    resultsContainer.appendChild(resultItem);
        }
    } else {
        // 按照生成顺序显示（用于图片上传）
        resultsContainer.appendChild(resultItem);
    }
    
    // 滚动到结果区域
    resultItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// 下载图片
function downloadImage(dataUrl, filename) {
    try {
    const link = document.createElement('a');
    link.href = dataUrl;

        // 确保文件名有正确的扩展名
        if (!filename.toLowerCase().endsWith('.png')) {
            filename += '.png';
        }

    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

        console.log('图片下载成功:', filename);
    } catch (error) {
        console.error('下载图片失败:', error);
        alert('下载失败，请稍后重试');
    }
}

// 清空所有
function clearAll() {
    if (!confirm('确定要清空所有上传的图片和生成结果吗？')) {
        return;
    }
    
    uploadedImages = [];
    selectedImageIndices = [];
    
    // 清空文本输入
    textInput.value = '';
    
    // 清空对话历史
    chatHistory.innerHTML = '<div class="empty-chat"><i class="fas fa-comment-slash"></i><p>暂无生成记录</p></div>';
    
    // 重置会话ID
    currentSessionId = null;

    // 更新文本输入框占位符
    updateTextInputPlaceholder();
    // 更新图片描述输入框占位符
    updateImageDescriptionPlaceholder();

    // 更新界面
    updatePreview();
    resultsContainer.innerHTML = `
        <div class="empty-results">
            <i class="fas fa-image"></i>
            <p>生成的宣传图将显示在这里</p>
        </div>
    `;
    
    // 重置滑块
    document.getElementById('brightness').value = 0;
    document.getElementById('contrast').value = 0;
    document.getElementById('saturation').value = 0;
    document.getElementById('brightnessValue').textContent = '0';
    document.getElementById('contrastValue').textContent = '0';
    document.getElementById('saturationValue').textContent = '0';
    
    // 重置选择
    document.querySelectorAll('.model-card, .style-card').forEach(card => {
        card.classList.remove('selected');
    });
    selectDefaultOptions();
}

// ========== 历史图片功能 ==========

/**
 * 加载用户的历史图片
 * 从后端获取用户的生成记录并显示
 */
async function loadImageHistory() {
    if (!authToken) {
        console.log('用户未登录，跳过加载历史图片');
        return;
    }

    try {
        const response = await fetch('http://localhost:5000/user/generation_records?limit=50', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (!response.ok) {
            throw new Error('获取历史图片失败');
        }

        const data = await response.json();
        displayImageHistory(data.records || []);

    } catch (error) {
        console.error('加载历史图片失败:', error);
        imageHistory.innerHTML = `
            <div class="empty-images">
                <i class="fas fa-exclamation-triangle"></i>
                <p>加载历史图片失败</p>
            </div>
        `;
    }
}

/**
 * 显示历史图片列表
 * @param {Array} records - 历史图片记录数组
 */
function displayImageHistory(records) {
    if (!records || records.length === 0) {
        imageHistory.innerHTML = `
            <div class="empty-images">
                <i class="fas fa-image"></i>
                <p>暂无历史图片</p>
            </div>
        `;
        return;
    }

    // 创建图片网格
    const grid = document.createElement('div');
    grid.className = 'image-history-grid';

    records.forEach(record => {
        const imageItem = createImageHistoryItem(record);
        grid.appendChild(imageItem);
    });

    imageHistory.innerHTML = '';
    imageHistory.appendChild(grid);

    console.log(`显示 ${records.length} 张历史图片`);
}

/**
 * 创建历史图片项
 * @param {Object} record - 图片记录数据
 * @returns {HTMLElement} 图片项元素
 */
function createImageHistoryItem(record) {
    const item = document.createElement('div');
    item.className = 'history-image-item';

    // 格式化时间显示 - 显示具体且准确的时间
    const createdDate = new Date(record.created_at).toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });

    // 截取提示词显示
    const shortPrompt = record.prompt ?
        (record.prompt.length > 30 ? record.prompt.substring(0, 30) + '...' : record.prompt) :
        '无提示词';

    item.innerHTML = `
        <img src="${record.image_url}" alt="历史图片" class="history-image" loading="lazy">
        <div class="history-image-info">
            <div class="history-image-date">${createdDate}</div>
            <div class="history-image-prompt">${shortPrompt}</div>
        </div>
        <button class="download-btn" onclick="downloadImage('${record.image_url}', '${record.id}')">
            <i class="fas fa-download"></i>
        </button>
    `;

    // 点击图片查看大图
    const img = item.querySelector('.history-image');
    img.addEventListener('click', () => viewImage(record.image_url, record.prompt));

    return item;
}

/**
 * 下载图片
 * @param {string} imageUrl - 图片URL
 * @param {string} imageId - 图片ID
 */
function downloadImage(imageUrl, imageId) {
    event.stopPropagation(); // 阻止事件冒泡

    try {
        // 创建下载链接
        const link = document.createElement('a');
        link.href = imageUrl;
        link.download = `generated_image_${imageId}.png`;
        link.target = '_blank';

        // 添加到DOM并点击
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        console.log('图片下载成功:', imageId);

    } catch (error) {
        console.error('下载图片失败:', error);
        alert('下载失败，请稍后重试');
    }
}

/**
 * 查看大图
 * @param {string} imageUrl - 图片URL
 * @param {string} prompt - 提示词
 */
function viewImage(imageUrl, prompt) {
    // 创建模态框显示大图
    const modal = document.createElement('div');
    modal.className = 'image-modal';
    modal.innerHTML = `
        <div class="image-modal-content">
            <img src="${imageUrl}" alt="大图查看" class="large-image">
            <div class="image-modal-info">
                <p><strong>提示词：</strong>${prompt || '无'}</p>
                <button onclick="this.closest('.image-modal').remove()">关闭</button>
            </div>
        </div>
    `;

    // 点击背景关闭
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });

    document.body.appendChild(modal);
}

/**
 * 加载聊天历史
 * 在用户登录后自动加载最近10条记录
 */
async function loadChatHistory() {
    if (!authToken) {
        console.log('用户未登录，跳过加载聊天历史');
        return;
    }

    try {
        // 直接获取最近10条聊天消息
        const response = await fetch('http://localhost:5000/history/recent-chat-messages?limit=10', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (!response.ok) {
            throw new Error('获取聊天历史失败');
        }

        const data = await response.json();
        const messages = data.messages || [];

        displayChatHistory(messages);

    } catch (error) {
        console.error('加载聊天历史失败:', error);
        // 不显示错误信息，保持界面清洁
    }
}

/**
 * 新增：加载图片模式聊天历史
 * 在用户登录后自动加载最近10条记录
 */
async function loadImageChatHistory() {
    if (!authToken) {
        console.log('用户未登录，跳过加载图片模式聊天历史');
        return;
    }

    try {
        // 直接获取最近10条图片模式聊天消息
        const response = await fetch('http://localhost:5000/history/recent-image-chat-messages?limit=10', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (!response.ok) {
            throw new Error('获取图片模式聊天历史失败');
        }

        const data = await response.json();
        const messages = data.messages || [];

        displayImageChatHistory(messages);

    } catch (error) {
        console.error('加载图片模式聊天历史失败:', error);
        // 不显示错误信息，保持界面清洁
    }
}

/**
 * 显示聊天历史（只显示最近10条记录）
 * @param {Array} messages - 聊天消息数组
 */
function displayChatHistory(messages) {
    if (!messages || messages.length === 0) {
        return;
    }

    // 按时间排序，最新的在后面（数据库已经按时间倒序返回，这里重新排序为正序显示）
    messages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    // 清空当前聊天历史
    chatHistory.innerHTML = '';

    // 显示历史消息
    messages.forEach(message => {
        // 根据消息类型确定发送者
        const sender = message.message_type === 'user' ? 'user' : 'system';
        const content = message.content || '';

        if (content.trim()) {
            // 创建消息元素
            const messageElement = document.createElement('div');
            messageElement.className = `chat-message ${sender}`;

            // 格式化时间显示
            const messageTime = new Date(message.timestamp);
            const timestamp = messageTime.toLocaleTimeString();

            messageElement.innerHTML = `
                <div class="message-content">${content}</div>
                <div class="message-time">${timestamp}</div>
            `;

            chatHistory.appendChild(messageElement);
        }
    });

    // 如果有消息，滚动到底部
    if (messages.length > 0) {
        chatHistory.scrollTop = chatHistory.scrollHeight;
        updateTextInputPlaceholder();
    } else {
        // 如果没有历史消息，显示空状态
        chatHistory.innerHTML = '<div class="empty-chat"><i class="fas fa-comment-slash"></i><p>暂无聊天记录</p></div>';
    }
}

/**
 * 新增：显示图片模式聊天历史（只显示最近10条记录）
 * @param {Array} messages - 聊天消息数组
 */
function displayImageChatHistory(messages) {
    if (!messages || messages.length === 0) {
        return;
    }

    // 按时间排序，最新的在后面（数据库已经按时间倒序返回，这里重新排序为正序显示）
    messages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    // 清空当前聊天历史
    imageChatHistory.innerHTML = '';

    // 显示历史消息
    messages.forEach(message => {
        // 根据消息类型确定发送者
        const sender = message.message_type === 'user' ? 'user' : 'system';
        const content = message.content || '';

        if (content.trim()) {
            // 创建消息元素
            const messageElement = document.createElement('div');
            messageElement.className = `chat-message ${sender}`;

            // 格式化时间显示
            const messageTime = new Date(message.timestamp);
            const timestamp = messageTime.toLocaleTimeString();

            messageElement.innerHTML = `
                <div class="message-content">${content}</div>
                <div class="message-time">${timestamp}</div>
            `;

            imageChatHistory.appendChild(messageElement);
        }
    });

    // 如果有消息，滚动到底部并更新占位符
    if (messages.length > 0) {
        imageChatHistory.scrollTop = imageChatHistory.scrollHeight;
        updateImageDescriptionPlaceholder();
    } else {
        // 如果没有历史消息，显示空状态
        imageChatHistory.innerHTML = '<div class="empty-chat"><i class="fas fa-comment-slash"></i><p>暂无图片生成对话记录</p></div>';
    }
}

/**
 * 刷新历史图片
 * 在生成新图片后调用
 */
function refreshImageHistory() {
    if (authToken) {
        loadImageHistory();
    }
}

/**
 * 刷新聊天历史
 * 在文本生成后调用
 */
function refreshChatHistory() {
    if (authToken) {
        loadChatHistory();
    }
}

/**
 * 新增：刷新图片模式聊天历史
 * 在图片生成后调用
 */
function refreshImageChatHistory() {
    if (authToken) {
        loadImageChatHistory();
    }
}