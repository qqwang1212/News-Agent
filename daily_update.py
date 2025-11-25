"""
每日自动更新脚本

该脚本整合了累积新闻获取和RSS Feed生成，适合设置为定时任务
支持GitHub Actions环境
"""

import os
import sys
import subprocess
from datetime import datetime, timezone, timedelta
import logging
import locale

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('daily_update.log', encoding='utf-8')
    ]
)

def get_system_encoding():
    """
    获取系统编码
    """
    try:
        # 尝试获取系统默认编码
        encoding = locale.getpreferredencoding()
        if not encoding:
            encoding = sys.getdefaultencoding()
        return encoding
    except:
        # 如果都失败，使用UTF-8作为默认
        return 'utf-8'

def run_script_with_fallback(script_name, description):
    """
    带有回退机制的脚本执行函数
    """
    print(f"\n{'='*60}")
    print(f"🚀 开始执行: {description}")
    print(f"{'='*60}")
    
    # 首先检查脚本文件是否存在
    if not os.path.exists(script_name):
        print(f"❌ 脚本文件不存在: {script_name}")
        return False
    
    # 方法1: 尝试UTF-8编码
    try:
        python_cmd = sys.executable
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            [python_cmd, script_name], 
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            errors='replace',
            timeout=1800,
            env=env
        )
        
        if result.returncode == 0:
            print(f"✅ {description} 执行成功")
            if result.stdout:
                print("输出:")
                print(result.stdout)
            logging.info(f"{description} 执行成功")
            return True
        else:
            print(f"❌ {description} 执行失败 (返回码: {result.returncode})")
            if result.stderr:
                print("错误信息:")
                print(result.stderr)
            if result.stdout:
                print("标准输出:")
                print(result.stdout)
            logging.error(f"{description} 执行失败: {result.stderr}")
            return False
            
    except UnicodeDecodeError as e:
        print(f"⚠️ UTF-8解码失败，尝试系统默认编码: {e}")
        
        # 方法2: 尝试系统默认编码
        try:
            system_encoding = get_system_encoding()
            print(f"   尝试使用编码: {system_encoding}")
            
            result = subprocess.run(
                [python_cmd, script_name], 
                capture_output=True, 
                text=True, 
                encoding=system_encoding,
                errors='replace',
                timeout=1800
            )
            
            if result.returncode == 0:
                print(f"✅ {description} 执行成功")
                if result.stdout:
                    print("输出:")
                    print(result.stdout)
                logging.info(f"{description} 执行成功")
                return True
            else:
                print(f"❌ {description} 执行失败")
                if result.stderr:
                    print("错误信息:")
                    print(result.stderr)
                logging.error(f"{description} 执行失败: {result.stderr}")
                return False
                
        except Exception as e2:
            print(f"❌ 系统编码也失败: {e2}")
            
            # 方法3: 使用字节模式读取
            try:
                print("   尝试字节模式...")
                result = subprocess.run(
                    [python_cmd, script_name], 
                    capture_output=True, 
                    timeout=1800
                )
                
                if result.returncode == 0:
                    print(f"✅ {description} 执行成功")
                    if result.stdout:
                        print("输出:")
                        try:
                            print(result.stdout.decode('utf-8', errors='replace'))
                        except:
                            print(result.stdout.decode('gbk', errors='replace'))
                    logging.info(f"{description} 执行成功")
                    return True
                else:
                    print(f"❌ {description} 执行失败")
                    if result.stderr:
                        print("错误信息:")
                        try:
                            print(result.stderr.decode('utf-8', errors='replace'))
                        except:
                            print(result.stderr.decode('gbk', errors='replace'))
                    logging.error(f"{description} 执行失败")
                    return False
                    
            except Exception as e3:
                print(f"❌ 所有方法都失败: {e3}")
                logging.error(f"执行 {description} 时发生异常: {e3}")
                return False
    
    except subprocess.TimeoutExpired:
        print(f"❌ {description} 执行超时")
        logging.error(f"{description} 执行超时")
        return False
    except Exception as e:
        print(f"❌ 执行 {description} 时发生异常: {e}")
        logging.error(f"执行 {description} 时发生异常: {e}")
        return False

def check_environment():
    """
    检查运行环境
    """
    print("🔍 检查运行环境...")
    
    # 显示编码信息
    system_encoding = get_system_encoding()
    print(f"   系统编码: {system_encoding}")
    print(f"   默认编码: {sys.getdefaultencoding()}")
    print(f"   文件系统编码: {sys.getfilesystemencoding()}")

    # 检查AI相关环境变量
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if gemini_api_key:
        print(f"   🤖 Gemini API Key: 已配置 (...{gemini_api_key[-4:]})")
    else:
        print(f"   ⚠️ Gemini API Key: 未配置，将使用默认密钥")
    
    # 检查是否在GitHub Actions中运行
    is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
    if is_github_actions:
        print("📍 运行环境: GitHub Actions")
        print(f"📂 工作目录: {os.getcwd()}")
        print(f"🐍 Python版本: {sys.version}")
    else:
        print("📍 运行环境: 本地")
        print(f"📂 工作目录: {os.getcwd()}")
        print(f"🐍 Python版本: {sys.version}")
        if os.name == 'nt':
            print("💻 操作系统: Windows")
    
    # 检查必要文件 - 使用跨平台路径
    required_files = [
        "生成累积新闻.py",
        "生成累积RSS.py",
        os.path.join("RSS feed URL", "rss_feed_url.json"),
        os.path.join("src", "rss_read.py"),
        os.path.join("src", "load_rss_url.py")
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            # 显示文件大小
            try:
                size = os.path.getsize(file_path)
                print(f"   ✅ {file_path} ({size:,} bytes)")
            except:
                print(f"   ✅ {file_path}")
    
    if missing_files:
        print("❌ 缺少必要文件:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ 环境检查通过")
    return True

def create_github_pages_structure():
    """
    创建GitHub Pages需要的目录结构
    """
    print("📁 创建GitHub Pages目录结构...")
    
    # 确保feed目录存在
    if not os.path.exists('feed'):
        os.makedirs('feed')
        print("   ✅ 创建feed目录")
    
    # 确保cumulative_news目录存在
    if not os.path.exists('cumulative_news'):
        os.makedirs('cumulative_news')
        print("   ✅ 创建cumulative_news目录")
    
    # 动态生成RSS链接的index.html - 增强版
    index_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Free News Agent - 专业的RSS新闻聚合服务，提供AI、科技、财经等多领域新闻订阅源">
    <meta name="keywords" content="RSS,新闻聚合,AI新闻,科技新闻,财经新闻,News Agent">
    <meta name="author" content="Free News Agent">
    <meta property="og:title" content="Free News Agent - RSS订阅源">
    <meta property="og:description" content="专业的RSS新闻聚合服务，每日更新AI、科技、财经等领域新闻">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary">
    <title>Free News Agent - RSS订阅源</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📡</text></svg>">
    <style>
        :root {
            --primary-color: #2563eb;
            --primary-hover: #1d4ed8;
            --secondary-color: #64748b;
            --success-color: #059669;
            --warning-color: #d97706;
            --error-color: #dc2626;
            --background-color: #ffffff;
            --surface-color: #f8fafc;
            --card-color: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --text-muted: #94a3b8;
            --border-color: #e2e8f0;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            --radius-sm: 0.375rem;
            --radius-md: 0.5rem;
            --radius-lg: 0.75rem;
            --transition: all 0.2s ease-in-out;
        }

        [data-theme="dark"] {
            --background-color: #0f172a;
            --surface-color: #1e293b;
            --card-color: #334155;
            --text-primary: #f1f5f9;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;
            --border-color: #475569;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-primary);
            background-color: var(--background-color);
            transition: var(--transition);
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 1rem;
        }

        /* Header */
        .header {
            background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
            color: white;
            padding: 2rem 0;
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
        }

        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="1"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
            opacity: 0.3;
        }

        .header-content {
            position: relative;
            z-index: 1;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .header-meta {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 0.5rem;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(255, 255, 255, 0.2);
            padding: 0.5rem 1rem;
            border-radius: var(--radius-md);
            font-weight: 500;
            backdrop-filter: blur(10px);
        }

        .last-update {
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.9rem;
        }

        .theme-toggle {
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            padding: 0.5rem;
            border-radius: var(--radius-md);
            cursor: pointer;
            font-size: 1.2rem;
            transition: var(--transition);
            backdrop-filter: blur(10px);
        }

        .theme-toggle:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.05);
        }

        /* Main Content */
        .main-content {
            display: grid;
            grid-template-columns: 1fr 300px;
            gap: 2rem;
            margin-bottom: 2rem;
        }

        .feeds-section {
            background: var(--card-color);
            border-radius: var(--radius-lg);
            padding: 2rem;
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-color);
        }

        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .search-box {
            position: relative;
        }

        .search-input {
            width: 100%;
            padding: 0.75rem 1rem 0.75rem 2.5rem;
            border: 2px solid var(--border-color);
            border-radius: var(--radius-md);
            font-size: 1rem;
            background: var(--surface-color);
            color: var(--text-primary);
            transition: var(--transition);
        }

        .search-input:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }

        .search-icon {
            position: absolute;
            left: 0.75rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
        }

        .filter-tabs {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .filter-tab {
            padding: 0.75rem 1rem;
            border: 2px solid var(--border-color);
            background: var(--surface-color);
            color: var(--text-secondary);
            border-radius: var(--radius-md);
            cursor: pointer;
            transition: var(--transition);
            text-align: center;
            font-weight: 500;
        }

        .filter-tab:hover,
        .filter-tab.active {
            border-color: var(--primary-color);
            background: var(--primary-color);
            color: white;
            transform: translateY(-1px);
        }

        .stats-card {
            background: var(--surface-color);
            padding: 1.5rem;
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
        }

        .stats-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--text-primary);
        }

        .stat-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 0;
            border-bottom: 1px solid var(--border-color);
        }

        .stat-item:last-child {
            border-bottom: none;
        }

        .stat-label {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        .stat-value {
            font-weight: 600;
            color: var(--primary-color);
        }

        /* RSS Feed Cards */
        .feeds-grid {
            display: grid;
            gap: 1.5rem;
        }

        .feed-card {
            background: var(--surface-color);
            border: 2px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            transition: var(--transition);
            position: relative;
            overflow: hidden;
        }

        .feed-card:hover {
            border-color: var(--primary-color);
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        .feed-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--primary-color);
            transform: scaleY(0);
            transition: var(--transition);
        }

        .feed-card:hover::before {
            transform: scaleY(1);
        }

        .feed-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1rem;
        }

        .feed-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .feed-category {
            display: inline-block;
            background: var(--primary-color);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: var(--radius-sm);
            font-size: 0.75rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .feed-meta {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin: 1rem 0;
            padding: 1rem;
            background: var(--card-color);
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
        }

        .meta-item {
            text-align: center;
        }

        .meta-label {
            display: block;
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.25rem;
        }

        .meta-value {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text-primary);
        }

        .feed-actions {
            display: flex;
            gap: 0.75rem;
            margin-top: 1rem;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.75rem 1rem;
            border: none;
            border-radius: var(--radius-md);
            font-size: 0.9rem;
            font-weight: 500;
            text-decoration: none;
            cursor: pointer;
            transition: var(--transition);
            text-align: center;
            justify-content: center;
        }

        .btn-primary {
            background: var(--primary-color);
            color: white;
            flex: 1;
        }

        .btn-primary:hover {
            background: var(--primary-hover);
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }

        .btn-secondary {
            background: var(--surface-color);
            color: var(--text-secondary);
            border: 2px solid var(--border-color);
        }

        .btn-secondary:hover {
            border-color: var(--primary-color);
            color: var(--primary-color);
        }

        .copy-btn {
            background: var(--surface-color);
            border: 2px solid var(--border-color);
            color: var(--text-secondary);
            padding: 0.5rem;
            border-radius: var(--radius-md);
            cursor: pointer;
            transition: var(--transition);
        }

        .copy-btn:hover {
            border-color: var(--success-color);
            color: var(--success-color);
        }

        .copy-btn.copied {
            border-color: var(--success-color);
            background: var(--success-color);
            color: white;
        }

        /* Info Sections */
        .info-sections {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 3rem;
        }

        .info-card {
            background: var(--card-color);
            border-radius: var(--radius-lg);
            padding: 2rem;
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-color);
        }

        .info-card h2 {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .info-card ul {
            list-style: none;
        }

        .info-card li {
            padding: 0.75rem 0;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
        }

        .info-card li:last-child {
            border-bottom: none;
        }

        .info-card li::before {
            content: '✓';
            color: var(--success-color);
            font-weight: bold;
            flex-shrink: 0;
            margin-top: 0.1rem;
        }

        .info-card a {
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 500;
        }

        .info-card a:hover {
            text-decoration: underline;
        }

        /* Footer */
        .footer {
            margin-top: 4rem;
            padding: 2rem 0;
            border-top: 1px solid var(--border-color);
            text-align: center;
            color: var(--text-muted);
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .container {
                padding: 0 0.5rem;
            }

            .header h1 {
                font-size: 2rem;
            }

            .header-content {
                flex-direction: column;
                text-align: center;
            }

            .header-meta {
                align-items: center;
            }

            .main-content {
                grid-template-columns: 1fr;
                gap: 1.5rem;
            }

            .sidebar {
                order: -1;
            }

            .filter-tabs {
                flex-direction: row;
                overflow-x: auto;
                padding-bottom: 0.5rem;
            }

            .filter-tab {
                white-space: nowrap;
                min-width: 120px;
            }

            .feed-meta {
                grid-template-columns: 1fr;
                gap: 0.5rem;
            }

            .feed-actions {
                flex-direction: column;
            }

            .info-sections {
                grid-template-columns: 1fr;
                gap: 1.5rem;
            }

            .theme-toggle {
                position: static;
                align-self: flex-end;
            }
        }

        /* Animations */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .feed-card {
            animation: fadeInUp 0.5s ease-out;
        }

        .feed-card:nth-child(2) { animation-delay: 0.1s; }
        .feed-card:nth-child(3) { animation-delay: 0.2s; }

        /* Loading States */
        .loading {
            opacity: 0.6;
            pointer-events: none;
        }

        .loading::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 20px;
            height: 20px;
            margin: -10px 0 0 -10px;
            border: 2px solid var(--border-color);
            border-top-color: var(--primary-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Accessibility */
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }

        /* Focus styles */
        .btn:focus,
        .search-input:focus,
        .filter-tab:focus,
        .copy-btn:focus {
            outline: 2px solid var(--primary-color);
            outline-offset: 2px;
        }

        /* Print styles */
        @media print {
            .theme-toggle,
            .search-box,
            .filter-tabs,
            .feed-actions {
                display: none;
            }

            .main-content {
                grid-template-columns: 1fr;
            }

            .feed-card {
                break-inside: avoid;
                box-shadow: none;
                border: 1px solid #ccc;
            }
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="container">
            <button class="theme-toggle" onclick="toggleTheme()" aria-label="切换主题">
                <span id="theme-icon">🌙</span>
            </button>
            <div class="header-content">
                <div>
                    <h1>📡 Free News Agent</h1>
                    <p style="color: rgba(255, 255, 255, 0.9); font-size: 1.1rem; margin: 0;">专业RSS新闻聚合服务</p>
                </div>
                <div class="header-meta">
                    <div class="status-badge">
                        <span>✅</span>
                        <span>系统运行正常</span>
                    </div>
                    <p class="last-update">最后更新: LAST_UPDATE_TIME</p>
                </div>
            </div>
        </div>
    </header>

    <div class="container">
        <main class="main-content">
            <section class="feeds-section">
                <div class="search-box">
                    <span class="search-icon">🔍</span>
                    <input type="text" class="search-input" placeholder="搜索RSS源..." id="searchInput" aria-label="搜索RSS源">
                </div>

                <div class="feeds-grid" id="feedsGrid">
RSS_LINKS_PLACEHOLDER
                </div>
            </section>

            <aside class="sidebar">
                <div class="filter-tabs" role="tablist" aria-label="RSS源分类">
                    <button class="filter-tab active" data-category="all" role="tab" aria-selected="true">📊 全部源</button>
                    <button class="filter-tab" data-category="ai" role="tab" aria-selected="false">🤖 AI</button>
                    <button class="filter-tab" data-category="technology" role="tab" aria-selected="false">💻 科技</button>
                    <button class="filter-tab" data-category="finance" role="tab" aria-selected="false">💰 财经</button>
                </div>

                <div class="stats-card">
                    <h3 class="stats-title">📈 统计信息</h3>
                    <div class="stat-item">
                        <span class="stat-label">RSS源总数</span>
                        <span class="stat-value" id="totalFeeds">TOTAL_FEEDS</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">今日更新</span>
                        <span class="stat-value" id="todayUpdates">TOTAL_FEEDS</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">总文件大小</span>
                        <span class="stat-value" id="totalSize">TOTAL_SIZE</span>
                    </div>
                </div>
            </aside>
        </main>

        <div class="info-sections">
            <div class="info-card">
                <h2>📚 服务说明</h2>
                <ul>
                    <li>RSS源每日更新三次，确保内容时效性</li>
                    <li>包含累积的历史新闻，便于回顾</li>
                    <li>支持各大主流RSS阅读器</li>
                    <li>新闻来源多样化，覆盖全球资讯</li>
                    <li>集成Gemini AI，智能筛选优质内容</li>
                    <li>完全免费，无广告干扰</li>
                </ul>
            </div>

            <div class="info-card">
                <h2>🔧 技术特性</h2>
                <ul>
                    <li>基于GitHub Actions自动化部署</li>
                    <li>使用GitHub Pages提供稳定托管</li>
                    <li>RSS格式严格遵循W3C标准</li>
                    <li>全站HTTPS加密，保障安全</li>
                    <li>响应式设计，支持移动设备</li>
                    <li>开源项目，代码完全透明</li>
                </ul>
            </div>
        </div>
    </div>

    <footer class="footer">
        <div class="container">
            <p>&copy; 2024 Free News Agent. 项目主页: <a href="https://github.com/zskfree/News-Agent" target="_blank" rel="noopener">GitHub</a></p>
        </div>
    </footer>

    <script>
        // Theme toggle functionality
        function toggleTheme() {
            const body = document.body;
            const themeIcon = document.getElementById('theme-icon');
            const currentTheme = body.getAttribute('data-theme');

            if (currentTheme === 'dark') {
                body.removeAttribute('data-theme');
                themeIcon.textContent = '🌙';
                localStorage.setItem('theme', 'light');
            } else {
                body.setAttribute('data-theme', 'dark');
                themeIcon.textContent = '☀️';
                localStorage.setItem('theme', 'dark');
            }
        }

        // Initialize theme from localStorage
        function initTheme() {
            const savedTheme = localStorage.getItem('theme');
            const themeIcon = document.getElementById('theme-icon');

            if (savedTheme === 'dark') {
                document.body.setAttribute('data-theme', 'dark');
                themeIcon.textContent = '☀️';
            }
        }

        // Search functionality
        function initSearch() {
            const searchInput = document.getElementById('searchInput');
            const feedCards = document.querySelectorAll('.feed-card');

            searchInput.addEventListener('input', function() {
                const searchTerm = this.value.toLowerCase();

                feedCards.forEach(card => {
                    const title = card.querySelector('.feed-title').textContent.toLowerCase();
                    const category = card.getAttribute('data-category').toLowerCase();

                    if (title.includes(searchTerm) || category.includes(searchTerm)) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                });
            });
        }

        // Category filter functionality
        function initFilters() {
            const filterTabs = document.querySelectorAll('.filter-tab');
            const feedCards = document.querySelectorAll('.feed-card');

            filterTabs.forEach(tab => {
                tab.addEventListener('click', function() {
                    // Update active tab
                    filterTabs.forEach(t => {
                        t.classList.remove('active');
                        t.setAttribute('aria-selected', 'false');
                    });
                    this.classList.add('active');
                    this.setAttribute('aria-selected', 'true');

                    // Filter feeds
                    const category = this.getAttribute('data-category');

                    feedCards.forEach(card => {
                        if (category === 'all' || card.getAttribute('data-category') === category) {
                            card.style.display = 'block';
                        } else {
                            card.style.display = 'none';
                        }
                    });

                    // Clear search when filtering
                    document.getElementById('searchInput').value = '';
                });
            });
        }

        // Copy to clipboard functionality
        function copyToClipboard(text, button) {
            navigator.clipboard.writeText(text).then(function() {
                const originalText = button.innerHTML;
                button.innerHTML = '✓ 已复制';
                button.classList.add('copied');

                setTimeout(function() {
                    button.innerHTML = originalText;
                    button.classList.remove('copied');
                }, 2000);
            }).catch(function() {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);

                const originalText = button.innerHTML;
                button.innerHTML = '✓ 已复制';
                button.classList.add('copied');

                setTimeout(function() {
                    button.innerHTML = originalText;
                    button.classList.remove('copied');
                }, 2000);
            });
        }

        // Initialize all functionality when DOM is loaded
        document.addEventListener('DOMContentLoaded', function() {
            initTheme();
            initSearch();
            initFilters();

            // Add keyboard navigation
            document.addEventListener('keydown', function(e) {
                if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
                    e.preventDefault();
                    document.getElementById('searchInput').focus();
                }
            });
        });

        // Add smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    </script>
</body>
</html>"""
    
    # 检查是否有现有的RSS文件，动态生成增强版链接
    rss_links = ""
    total_size = 0
    feed_count = 0
    
    if os.path.exists('feed'):
        if os.getenv('GITHUB_ACTIONS') == 'true':
            # 动态获取GitHub用户名和仓库名
            github_repo = os.getenv('GITHUB_REPOSITORY', 'username/News-Agent')
            if '/' in github_repo:
                username, repo_name = github_repo.split('/', 1)
            else:
                username = github_repo
                repo_name = 'News-Agent'
            base_url = f"https://{username}.github.io/{repo_name}"
        else:
            base_url = "."  # 本地预览

        # 定义增强版RSS文件映射，包含更多元数据
        # ✅ 动态加载RSS配置，支持所有分类
        from src.load_rss_url import load_rss_sources
        
        try:
            rss_sources = load_rss_sources("RSS feed URL/rss_feed_url.json")
            
            # 按分类分组
            from collections import defaultdict
            categories = defaultdict(list)
            for source in rss_sources:
                categories[source['category']].append(source)
            
            # 动态生成RSS映射
            rss_mapping = {}
            # 图标映射（可扩展）
            icon_map = {
                'AI': '🤖',
                'Technology': '💻',
                'Finance': '💰',
                'Education': '🎓'
            }
            
            for category, sources in categories.items():
                safe_category = category.lower().replace(' ', '_')
                filename = f"{safe_category}freenewsagent.xml"
                rss_mapping[filename] = {
                    'name': f'{category}',
                    'icon': icon_map.get(category, '📰'),  # 默认图标
                    'category': safe_category,
                    'description': f'{category}领域新闻聚合',
                    'sources': [s['name'] for s in sources][:5],  # 最多显示5个来源
                    'update_frequency': '每日3次'
                }
                
        except Exception as e:
            print(f"   ❌ 加载RSS配置失败: {e}")
            # 回退到硬编码
            rss_mapping = {
                'aifreenewsagent.xml': {
                    'name': 'AI-人工智能',
                    'icon': '🤖',
                    'category': 'ai',
                    'description': '人工智能领域新闻',
                    'sources': ['机器之心', '量子位'],
                    'update_frequency': '每日3次'
                }
            }


        for filename, feed_info in rss_mapping.items():
            file_path = os.path.join('feed', filename)
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                total_size += file_size
                feed_count += 1

                # 格式化文件大小
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"

                # 生成RSS源数量
                source_count = len(feed_info['sources'])

                # 生成增强版RSS卡片
                rss_links += f'''                    <div class="feed-card" data-category="{feed_info['category']}">
                        <div class="feed-header">
                            <div>
                                <h3 class="feed-title">
                                    <span>{feed_info['icon']}</span>
                                    <span>{feed_info['name']}</span>
                                </h3>
                                <span class="feed-category">{feed_info['category'].upper()}</span>
                            </div>
                        </div>

                        <p style="color: var(--text-secondary); margin-bottom: 1rem; line-height: 1.5;">
                            {feed_info['description']}
                        </p>

                        <div class="feed-meta">
                            <div class="meta-item">
                                <span class="meta-label">文件大小</span>
                                <span class="meta-value">{size_str}</span>
                            </div>
                            <div class="meta-item">
                                <span class="meta-label">新闻源</span>
                                <span class="meta-value">{source_count}个</span>
                            </div>
                        </div>

                        <div class="feed-actions">
                            <a href="{base_url}/feed/{filename}" class="btn btn-primary" target="_blank" rel="noopener">
                                📡 订阅RSS
                            </a>
                            <button class="copy-btn" onclick="copyToClipboard('{base_url}/feed/{filename}', this)" title="复制RSS地址">
                                📋
                            </button>
                        </div>

                        <details style="margin-top: 1rem;">
                            <summary style="cursor: pointer; color: var(--text-secondary); font-size: 0.9rem;">
                                📊 详细信息
                            </summary>
                            <div style="margin-top: 0.5rem; padding: 1rem; background: var(--surface-color); border-radius: var(--radius-md); font-size: 0.9rem;">
                                <p><strong>更新频率:</strong> {feed_info['update_frequency']}</p>
                                <p><strong>订阅地址:</strong> <code style="background: var(--card-color); padding: 0.2rem 0.4rem; border-radius: 3px; font-size: 0.8rem;">{base_url}/feed/{filename}</code></p>
                                <p><strong>主要来源:</strong> {', '.join(feed_info['sources'][:3])}{'...' if len(feed_info['sources']) > 3 else ''}</p>
                            </div>
                        </details>
                    </div>
'''

    if not rss_links:
        rss_links = '''                    <div class="feed-card" data-category="all">
                        <div class="feed-header">
                            <div>
                                <h3 class="feed-title">
                                    <span>⏳</span>
                                    <span>RSS源准备中</span>
                                </h3>
                            </div>
                        </div>
                        <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                            RSS文件将在首次运行后生成，请稍后刷新页面查看。
                        </p>
                        <div class="feed-actions">
                            <button class="btn btn-primary" disabled>
                                ⏳ 生成中...
                            </button>
                        </div>
                    </div>
'''
        total_size = 0
        feed_count = 0
    
    # 替换占位符 - 使用指定时区的时间和统计信息
    # 设置为中国时区 (UTC+8)
    china_tz = timezone(timedelta(hours=8))
    current_time = datetime.now(china_tz).strftime('%Y-%m-%d %H:%M:%S CST')

    # 格式化总文件大小
    if total_size < 1024:
        total_size_str = f"{total_size} B"
    elif total_size < 1024 * 1024:
        total_size_str = f"{total_size / 1024:.1f} KB"
    else:
        total_size_str = f"{total_size / (1024 * 1024):.1f} MB"

    # 替换所有占位符
    index_content = index_content.replace('LAST_UPDATE_TIME', current_time)
    index_content = index_content.replace('RSS_LINKS_PLACEHOLDER', rss_links)
    index_content = index_content.replace('TOTAL_FEEDS', str(feed_count))
    index_content = index_content.replace('TOTAL_SIZE', total_size_str)
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print("   ✅ 创建index.html")


def main():
    """
    主函数：执行每日更新流程
    """
    start_time = datetime.now()
    print("=" * 60)
    print("🕐 每日新闻更新流程开始 - 优化版")
    print("=" * 60)
    print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查环境
    if not check_environment():
        print("❌ 环境检查失败，终止执行")
        return False
    
    # 创建GitHub Pages结构
    create_github_pages_structure()
    
    success_count = 0
    total_tasks = 2
    
    # 步骤1: 更新累积新闻
    print(f"\n📝 步骤1/{total_tasks}: 更新累积新闻")
    if run_script_with_fallback("生成累积新闻.py", "更新累积新闻"):
        success_count += 1
    
    # 步骤2: 生成优化版累积RSS Feed
    print(f"\n📡 步骤2/{total_tasks}: 生成优化版累积RSS Feed")
    # 首先尝试使用优化版脚本
    if os.path.exists("生成累积RSS_优化版.py"):
        if run_script_with_fallback("生成累积RSS_优化版.py", "生成优化版累积RSS Feed"):
            success_count += 1
        else:
            # 如果优化版失败，回退到原版本
            print("⚠️ 优化版失败，尝试使用原版本...")
            if run_script_with_fallback("生成累积RSS.py", "生成累积RSS Feed"):
                success_count += 1
    else:
        # 如果没有优化版，使用原版本
        if run_script_with_fallback("生成累积RSS.py", "生成累积RSS Feed"):
            success_count += 1
    
    # 重新生成index.html以包含最新的RSS文件信息
    if success_count > 0:
        print("\n🔄 更新GitHub Pages...")
        create_github_pages_structure()
    
    # 输出最终结果
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print("📊 每日更新完成统计")
    print("=" * 60)
    print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总耗时: {duration}")
    print(f"成功任务: {success_count}/{total_tasks}")
    
    if success_count == total_tasks:
        print("🎉 所有任务执行成功！")
        
        # 检查生成的RSS文件
        if os.path.exists('feed'):
            rss_files = [f for f in os.listdir('feed') if f.endswith('.xml')]
            print(f"\n📡 生成的RSS文件 ({len(rss_files)}个):")
            for rss_file in rss_files:
                file_size = os.path.getsize(os.path.join('feed', rss_file))
                print(f"   - {rss_file} ({file_size:,} bytes)")
        
        # GitHub Actions环境提示
        if os.getenv('GITHUB_ACTIONS') == 'true':
            base_url = "https://zskksz.asia/News-Agent"
            print(f"\n🌐 网站地址: {base_url}")
            print(f"📡 RSS订阅基础地址: {base_url}/feed/")
        
        logging.info("每日更新任务完成")
        return True
    else:
        print("⚠️ 部分任务执行失败，请检查错误信息")
        if success_count > 0:
            print(f"💡 已完成 {success_count} 个任务，可以查看部分结果")
        logging.error("每日更新任务失败")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ 用户中断执行")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 执行过程中发生未预期的错误: {e}")
        logging.error(f"执行过程中发生未预期的错误: {e}")
        sys.exit(1)
