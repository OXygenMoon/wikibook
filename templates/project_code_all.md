# 项目代码汇总

- **生成时间**: 2026-02-16 10:28:40
- **根目录**: `/root/projects/wikibook/templates`

---

## 📄 packer.py

```python
import os
from datetime import datetime

def generate_markdown_report(output_filename="project_code.md"):
    """
    递归读取代码文件，并写入到一个 Markdown 文档中。
    """
    # 1. 配置：定义需要包含的文件后缀
    allowed_extensions = {
        '.py', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.go', '.rs',
        '.js', '.ts', '.jsx', '.tsx', '.vue', '.html', '.css', '.scss', '.less',
        '.json', '.xml', '.yaml', '.yml', '.toml', '.sql', '.sh', '.bat',
        '.md', '.txt', 'Dockerfile', 'Makefile', 'Jenkinsfile'
    }

    # 2. 配置：定义需要忽略的目录
    ignored_dirs = {
        '.git', '.idea', '.vscode', '__pycache__', 
        'venv', 'env', '.venv', 'node_modules', 
        'dist', 'build', 'target', 'bin', 'obj',
        '.DS_Store', 'migrations'
    }

    # 映射文件后缀到 Markdown 代码块语言标识 (提升阅读体验)
    ext_lang_map = {
        '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
        '.java': 'java', '.c': 'c', '.cpp': 'cpp', '.sh': 'bash',
        '.html': 'html', '.css': 'css', '.json': 'json', '.sql': 'sql',
        '.md': 'markdown', '.yml': 'yaml', '.yaml': 'yaml',
        '.go': 'go', '.rs': 'rust'
    }

    cwd = os.getcwd()
    file_list = [] # 用于存储处理过的文件路径，生成目录用
    
    print(f"📂 正在扫描目录: {cwd} ...")

    # 打开输出文件准备写入
    with open(output_filename, 'w', encoding='utf-8') as out_f:
        
        # 写入文档头部信息
        out_f.write(f"# 项目代码汇总\n\n")
        out_f.write(f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        out_f.write(f"- **根目录**: `{cwd}`\n\n")
        out_f.write("---\n\n")
        
        # 先记录位置，稍后在这里补全目录（或者简单起见，我们在最后打印目录，或此处先占位）
        # 这里我们采用直接遍历写入内容的方式
        
        total_files = 0
        
        for root, dirs, files in os.walk(cwd):
            # 过滤忽略的目录
            dirs[:] = [d for d in dirs if d not in ignored_dirs]

            for file in files:
                _, ext = os.path.splitext(file)
                
                # 检查是否为代码文件
                if ext.lower() in allowed_extensions or file in allowed_extensions:
                    if file == output_filename or file == "code2md.py": # 排除自身和输出文件
                        continue

                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, cwd)
                    
                    try:
                        # 尝试读取文件内容
                        with open(file_path, 'r', encoding='utf-8') as code_f:
                            content = code_f.read()
                            
                            # 获取对应的 markdown 语言标签，默认使用后缀名（去掉.）
                            lang_tag = ext_lang_map.get(ext.lower(), ext.lstrip('.'))
                            
                            # --- 写入 Markdown ---
                            # 1. 文件路径标题
                            out_f.write(f"## 📄 {rel_path}\n\n")
                            # 2. 代码块
                            out_f.write(f"```{lang_tag}\n")
                            out_f.write(content)
                            # 确保代码块结尾换行
                            if not content.endswith('\n'):
                                out_f.write("\n") 
                            out_f.write("```\n\n")
                            
                            print(f"   ✅ 已写入: {rel_path}")
                            file_list.append(rel_path)
                            total_files += 1

                    except UnicodeDecodeError:
                        print(f"   ⚠️ 跳过二进制或非UTF-8文件: {rel_path}")
                    except Exception as e:
                        print(f"   ❌ 读取错误 {rel_path}: {e}")

        # 在文末（或文首）添加文件清单
        out_f.write("\n---\n\n## 📚 包含的文件清单\n\n")
        for p in file_list:
            out_f.write(f"- {p}\n")

    print("-" * 30)
    print(f"🎉 转换完成！")
    print(f"📝 输出文件: {output_filename}")
    print(f"📊 共包含 {total_files} 个代码文件")

if __name__ == '__main__':
    generate_markdown_report("project_code_all.md")
```

## 📄 index.html

```html
{% extends "base.html" %}

{% block extra_css %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/sticker.css') }}">
{% endblock %}

{% block content %}
{# --- 只有在访问特定用户的 sticker 页面时显示 --- #}
{% if target_user and target_user.id != current_user.id %}
<div class="fixed top-6 left-1/2 -translate-x-1/2 z-[100] bg-stone-900/60 backdrop-blur-md text-white px-6 py-3 rounded-full shadow-2xl flex items-center gap-4 pointer-events-auto border border-white/10 animate-fade-in-down ring-1 ring-white/5">
    <div class="relative flex h-3 w-3">
      <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
      <span class="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
    </div>
    <span class="text-sm font-medium tracking-wide">
        正在参观 
        <span class="font-black text-lg bg-clip-text text-transparent bg-gradient-to-r from-pink-500 via-red-500 to-yellow-500 animate-gradient-x mx-1">
            {{ target_user.username }}
        </span> 
        的贴纸板
    </span>
    <a href="{{ url_for('my_following') }}" class="ml-2 w-6 h-6 flex items-center justify-center rounded-full bg-white/10 hover:bg-white/20 hover:scale-110 transition-all text-xs border border-white/10">✕</a>
</div>
{% endif %}

<!-- <div class="border-black border-[1px] rounded-3xl max-w-7xl mx-auto space-y-12 pb-12 relative pointer-events-none"> -->
    <div class="rounded-3xl max-w-7xl mx-auto space-y-12 pb-12 relative pointer-events-none">
    <div class="relative text-center space-y-8 py-16 bg-gradient-to-b from-primary/5 to-transparent rounded-3xl group/hero pointer-events-none">
        <div class="space-y-4 pointer-events-auto">
            <h1 class="text-4xl lg:text-5xl font-extrabold text-stone-800 tracking-tight">
                探索知识的 <span class="text-primary">WikiBook</span>
            </h1>
            <p class="text-lg text-stone-500 max-w-2xl mx-auto">
                构建、分享与协作。在这里发现有价值的文档，或创建属于你的知识库。
            </p>
        </div>

        <div class="max-w-2xl mx-auto px-4 relative z-20 pointer-events-auto">
            <form action="{{ url_for('index') }}" method="get" class="relative group">
                <input type="text" name="q" value="{{ q or '' }}" 
                    class="input input-lg w-full pl-12 pr-4 bg-white shadow-lg border-stone-200 focus:border-primary focus:ring-4 focus:ring-primary/10 rounded-full transition-all duration-300" 
                    placeholder="搜索 Wiki 或文章内容...">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 absolute left-4 top-1/2 -translate-y-1/2 text-stone-400 group-focus-within:text-primary transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
            </form>
        </div>

        <div id="sticker-drop-zone" class="hidden absolute left-0 right-0 -bottom-12 z-10 h-24 transition-all duration-500 animate-fade-in-up pointer-events-none">
            <div class="w-full h-full border-2 border-dashed border-stone-300/60 rounded-3xl p-4 flex flex-col items-center justify-center text-center bg-white/90 backdrop-blur-sm hover:bg-stone-50 transition-colors shadow-sm">
                <div class="p-2 rounded-full bg-stone-100 mb-2 text-primary">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                    </svg>
                </div>
                <h3 class="text-sm font-bold text-stone-600">拖拽贴纸到这里</h3>
                <p class="text-[10px] text-stone-400 mt-0.5">贴纸将固定在首页背景上</p>
            </div>
        </div>
    </div>

    <div class="relative z-30 bg-white rounded-3xl shadow-sm border border-stone-100 p-8 lg:p-12 pointer-events-auto">
        {% if q %}
            <div class="space-y-12">
                <section>
                    <div class="flex items-center gap-3 mb-6">
                        <div class="w-1 h-6 bg-primary rounded-full"></div>
                        <h2 class="text-xl font-bold text-stone-800">Wiki 匹配结果</h2>
                        {% if not wikis %}<span class="text-sm text-stone-400 font-normal">无匹配</span>{% endif %}
                    </div>
                    {% if wikis %}
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {% for w in wikis %}
                        <a href="{{ url_for('wiki_detail', wiki_id=w.id) }}" class="liquid-card hover:shadow-xl transition-all duration-300 border border-stone-100/50 group h-full rounded-2xl" 
                           style="--bg-color: {{ w.bg_color or '#ffffff' }}; color: {{ w.fg_color or '#1f2937' }}; --grain-opacity: {{ w.pattern if w.pattern and w.pattern[0].isdigit() else '0.05' }}; --blur-level: {{ w.blur_level or 60 }}px; {% if w.gradient_color %}--bg-image: {% if 'circle' in (w.gradient_direction or '') %}radial-gradient({{ w.gradient_direction }}, {{ w.bg_color }}, {{ w.gradient_color }}){% else %}linear-gradient({{ w.gradient_direction or 'to bottom right' }}, {{ w.bg_color }}, {{ w.gradient_color }}){% endif %};{% endif %}">
                            
                            <div class="liquid-noise"></div>
                            
                            <div class="card-body p-5 relative z-10">
                                <div class="flex items-start justify-between">
                                    <div class="w-10 h-10 rounded-lg bg-primary/10 text-primary flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                                        <span class="font-bold text-lg">{{ w.title[0]|upper }}</span>
                                    </div>
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 opacity-60 group-hover:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                                    </svg>
                                </div>
                                <h3 class="card-title group-hover:opacity-80 transition-colors">{{ w.title }}</h3>
                                <p class="text-sm opacity-80 line-clamp-2">{{ w.description or '暂无描述' }}</p>
                                <div class="mt-4 flex items-center gap-4 text-xs opacity-60 font-medium">
                                    <span class="flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor"><path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z"/></svg> {{ w.pages|length }} 篇</span>
                                    <span class="flex items-center gap-1"><svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/></svg> {{ w.created_by.username if w.created_by else 'Unknown' }}</span>
                                </div>
                            </div>
                        </a>
                        {% endfor %}
                    </div>
                    {% endif %}
                </section>

                <section>
                    <div class="flex items-center gap-3 mb-6">
                        <div class="w-1 h-6 bg-secondary rounded-full"></div>
                        <h2 class="text-xl font-bold text-stone-800">文章匹配结果</h2>
                        {% if not pages %}<span class="text-sm text-stone-400 font-normal">无匹配</span>{% endif %}
                    </div>
                    {% if pages %}
                    <div class="grid grid-cols-1 gap-4">
                        {% for p in pages %}
                        <a href="{{ url_for('view_page', wiki_id=p.wiki.id, slug=p.slug) }}" class="flex flex-col md:flex-row gap-4 p-4 rounded-xl hover:bg-stone-50 transition-colors border border-transparent hover:border-stone-100 group">
                            <div class="flex-1 min-w-0">
                                <div class="flex items-center gap-2 mb-1">
                                    <span class="badge badge-sm badge-ghost">{{ p.wiki.title }}</span>
                                    <h3 class="font-bold text-lg text-stone-800 group-hover:text-primary transition-colors truncate">{{ p.title }}</h3>
                                </div>
                                <p class="text-sm text-stone-500 line-clamp-2">{{ p.content_md[:200] }}...</p>
                            </div>
                            <div class="flex items-center gap-4 text-xs text-stone-400 flex-shrink-0 md:self-center">
                                <span>{{ p.updated_at.strftime('%Y-%m-%d') }}</span>
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-stone-300 group-hover:text-primary transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                                </svg>
                            </div>
                        </a>
                        {% endfor %}
                    </div>
                    {% endif %}
                </section>
            </div>

        {% else %}
            
            <div class="flex items-center justify-between mb-8">
                <div class="flex items-center gap-3">
                    <div class="w-1 h-6 bg-primary rounded-full"></div>
                    <h2 class="text-2xl font-bold text-stone-800">精选 Wiki</h2>
                </div>
                {% if current_user.is_admin %}
                <a href="{{ url_for('create_wiki') }}" class="btn btn-primary btn-sm gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
                    创建新 Wiki
                </a>
                {% endif %}
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {% for w in wikis %}
                <a href="{{ url_for('wiki_detail', wiki_id=w.id) }}" class="liquid-card hover:shadow-xl transition-all duration-300 border border-stone-100/50 group h-full rounded-2xl" 
                   style="--bg-color: {{ w.bg_color or '#ffffff' }}; color: {{ w.fg_color or '#1f2937' }}; --grain-opacity: {{ w.pattern if w.pattern and w.pattern[0].isdigit() else '0.05' }}; --blur-level: {{ w.blur_level or 60 }}px; {% if w.gradient_color %}--bg-image: {% if 'circle' in (w.gradient_direction or '') %}radial-gradient({{ w.gradient_direction }}, {{ w.bg_color }}, {{ w.gradient_color }}){% else %}linear-gradient({{ w.gradient_direction or 'to bottom right' }}, {{ w.bg_color }}, {{ w.gradient_color }}){% endif %};{% endif %}">
                    
                    <div class="liquid-noise"></div>
                    
                    <div class="card-body p-5 relative z-10">
                        <div class="flex items-center gap-2 mb-3">
                            <div class="avatar placeholder">
                                <div class="bg-primary/10 text-primary rounded-full w-8 h-8 backdrop-blur-md bg-white/40 shadow-sm border-black border-white/20">
                                    <span class="text-xs font-bold">{{ w.title[0]|upper }}</span>
                                </div>
                            </div>
                            <div class="min-w-0 flex-1">
                                <div class="text-base font-bold group-hover:opacity-80 transition-colors truncate tracking-tight" title="{{ w.title }}">{{ w.title }}</div>
                                <div class="text-[10px] opacity-60 font-medium">{{ w.created_at.strftime('%Y-%m-%d') }}</div>
                            </div>
                        </div>
                        
                        <p class="text-sm opacity-80 line-clamp-3 mb-4 flex-grow leading-relaxed font-medium">
                            {{ w.description or '暂无描述' }}
                        </p>
                        
                        <div class="flex items-center text-xs opacity-60 pt-3 border-t border-current/10 font-medium">
                            <div class="flex items-center gap-3">
                                <span class="flex items-center gap-1" title="文章数">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor"><path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z"/></svg>
                                    {{ w.pages|length }} 篇
                                </span>
                                <span class="flex items-center gap-1" title="订阅数">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor"><path d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" /></svg>
                                    {{ w.subscriptions|length }} 人
                                </span>
                            </div>
                        </div>
                    </div>
                </a>
                {% endfor %}
            </div>
        {% endif %}
    </div>
</div>

{% endblock %}

{% block scripts %}
<script>
    // 在这里添加处理贴纸拖拽逻辑的 JS 代码
    // 或者引用外部 JS 文件
</script>
{% endblock %}
```

## 📄 online_users.html

```html
{% extends "base.html" %}

{% block content %}
<div class="fixed inset-0 -z-10 overflow-hidden bg-base-100">
    <div class="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-primary/10 rounded-full blur-[100px] animate-blob mix-blend-multiply opacity-40"></div>
    <div class="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-secondary/10 rounded-full blur-[100px] animate-blob animation-delay-4000 mix-blend-multiply opacity-40"></div>
</div>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 animate-fade-in">
    
    <div class="flex items-center justify-between mb-10">
        <div>
            <h1 class="text-3xl font-black tracking-tight flex items-center gap-3">
                在线大厅
                <div class="relative flex h-3 w-3">
                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                  <span class="relative inline-flex rounded-full h-3 w-3 bg-success"></span>
                </div>
            </h1>
            <p class="text-base-content/60 mt-1 font-medium">此刻共有 <span class="text-primary font-bold font-mono text-lg">{{ users|length }}</span> 位学友在线</p>
        </div>
        
        <a href="{{ url_for('online_users') }}" class="btn btn-ghost btn-circle hover:bg-base-200 hover:rotate-180 transition-transform duration-500">
            <i class="fas fa-sync-alt"></i>
        </a>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {% for status in users %}
        <div class="group relative rounded-2xl transition-all duration-300 hover:-translate-y-1">
            <div class="absolute -inset-0.5 bg-gradient-to-br from-primary/20 to-secondary/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity blur-sm"></div>
            
            <div class="relative h-full card bg-base-100/60 backdrop-blur-xl border border-white/10 dark:border-white/5 shadow-sm group-hover:shadow-xl transition-all overflow-visible">
                <div class="card-body p-5">
                    
                    <div class="flex justify-between items-start">
                        <a href="{{ url_for('public_profile', user_id=status.user.id) }}" class="relative inline-block">
                            <div class="avatar placeholder">
                                <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-100 to-white dark:from-base-300 dark:to-base-100 text-base-content shadow-inner border border-white/20 group-hover:scale-105 transition-transform duration-300">
                                    <span class="text-xl font-black">{{ status.user.username[0] | upper }}</span>
                                </div>
                            </div>
                            <div class="absolute -bottom-1 -right-1 w-4 h-4 bg-success border-2 border-white dark:border-base-100 rounded-full"></div>
                        </a>

                        {% if status.user.selected_badge %}
                        <div class="group/badge relative">
                            <div class="w-8 h-8 rounded-full bg-base-200/50 flex items-center justify-center cursor-help transition-transform hover:scale-110 hover:bg-base-200">
                                {% set _icon = status.user.selected_badge.icon %}
                                {% if _icon|is_image_icon %}
                                    <img src="{{ _icon|badge_icon_url }}" class="w-5 h-5 object-contain" alt="badge">
                                {% else %}
                                    <span class="text-base">{{ _icon }}</span>
                                {% endif %}
                            </div>
                            
                            <div class="absolute right-0 top-full mt-2 w-64 p-0 bg-white dark:bg-base-200 rounded-xl shadow-2xl border border-base-200 invisible opacity-0 translate-y-2 group-hover/badge:visible group-hover/badge:opacity-100 group-hover/badge:translate-y-0 transition-all duration-200 z-50">
                                <div class="p-4 text-center">
                                    <div class="w-12 h-12 mx-auto bg-base-100 rounded-full flex items-center justify-center mb-2 shadow-sm">
                                        {% if _icon|is_image_icon %}
                                            <img src="{{ _icon|badge_icon_url }}" class="w-8 h-8 object-contain">
                                        {% else %}
                                            <span class="text-2xl">{{ _icon }}</span>
                                        {% endif %}
                                    </div>
                                    <h3 class="font-bold text-base-content">{{ status.user.selected_badge.name }}</h3>
                                    <p class="text-xs text-base-content/60 mt-1">{{ status.user.selected_badge.description }}</p>
                                </div>
                                <div class="h-1 w-full bg-gradient-to-r from-primary/50 to-secondary/50 rounded-b-xl"></div>
                            </div>
                        </div>
                        {% endif %}
                    </div>

                    <div class="mt-3">
                        <a href="{{ url_for('public_profile', user_id=status.user.id) }}" class="block group-hover:text-primary transition-colors">
                            <h2 class="text-lg font-bold truncate">{{ status.user.username }}</h2>
                        </a>
                        
                        <div class="mt-2 inline-flex items-center gap-2 px-2.5 py-1 rounded-lg bg-base-200/50 border border-base-200/50 max-w-full">
                            <div class="w-1.5 h-1.5 rounded-full bg-primary/50 animate-pulse"></div>
                            <span class="text-xs font-medium text-base-content/70 truncate max-w-[120px]" title="{{ status.current_action }}">
                                {{ status.current_action or '发呆中...' }}
                            </span>
                        </div>
                    </div>

                    <div class="mt-5 pt-4 border-t border-base-content/5 flex items-center justify-between">
                        <div class="text-xs text-base-content/40 font-mono flex items-center gap-1" title="最后活跃时间">
                            <i class="far fa-clock"></i>
                            {{ status.last_active_at.strftime('%H:%M') }}
                        </div>

                        {% if status.user.id != current_user.id %}
                            <div class="flex items-center">
                                {% if current_user.is_following(status.user) %}
                                    <form action="{{ url_for('unfollow_user', user_id=status.user.id) }}" method="POST">
                                        <button class="btn btn-xs btn-ghost text-base-content/40 hover:text-error hover:bg-error/10 gap-1 transition-all">
                                            <span class="text-xs">已关注</span>
                                        </button>
                                    </form>
                                {% else %}
                                    <form action="{{ url_for('follow_user', user_id=status.user.id) }}" method="POST">
                                        <button class="btn btn-xs btn-primary btn-outline gap-1 hover:shadow-md hover:scale-105 transition-all">
                                            <i class="fas fa-plus text-[10px]"></i> 关注
                                        </button>
                                    </form>
                                {% endif %}
                            </div>
                        {% else %}
                             <span class="badge badge-xs badge-ghost opacity-50">我</span>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
        {% else %}
        <div class="col-span-full flex flex-col items-center justify-center py-20 text-center">
            <div class="w-24 h-24 bg-base-200/50 rounded-full flex items-center justify-center mb-4">
                <i class="fas fa-wind text-4xl text-base-content/20"></i>
            </div>
            <h3 class="text-lg font-bold text-base-content/60">暂时没有人在线</h3>
            <p class="text-sm text-base-content/40 mt-1">也许大家都去睡觉了...</p>
        </div>
        {% endfor %}
    </div>
</div>

<style>
    /* 简单的淡入动画 */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .animate-fade-in {
        animation: fadeIn 0.6s ease-out forwards;
    }
    
    /* 背景动画 (复用) */
    @keyframes blob {
        0% { transform: translate(0px, 0px) scale(1); }
        33% { transform: translate(30px, -50px) scale(1.1); }
        66% { transform: translate(-20px, 20px) scale(0.9); }
        100% { transform: translate(0px, 0px) scale(1); }
    }
    .animate-blob {
        animation: blob 7s infinite;
    }
    .animation-delay-4000 {
        animation-delay: 4s;
    }
</style>
{% endblock %}
```

## 📄 register.html

```html
{% extends "base.html" %}

{% block content %}
<div class="min-h-[calc(100vh-10rem)] flex items-center justify-center">
  <div class="card w-full max-w-sm bg-base-100 shadow-xl border border-base-200">
    <div class="card-body">
      <div class="text-center mb-6">
        <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-lg shadow-orange-100 mx-auto mb-4 transform -rotate-3">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-base-content">创建账号</h2>
        <p class="text-sm text-base-content/60 mt-1">加入 WikiBook 开启知识之旅</p>
      </div>
      
      <form method="post" class="flex flex-col gap-3">
        <div class="form-control">
          <label class="label py-1">
            <span class="label-text font-medium">用户名</span>
          </label>
          <div class="relative">
            <input type="text" name="username" placeholder="设置用户名" class="input input-bordered w-full pl-10" required />
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 absolute left-3 top-1/2 -translate-y-1/2 text-base-content/40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
        </div>

        <div class="form-control">
          <label class="label py-1">
            <span class="label-text font-medium">邮箱</span>
          </label>
          <div class="relative">
            <input type="email" name="email" placeholder="example@email.com" class="input input-bordered w-full pl-10" required />
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 absolute left-3 top-1/2 -translate-y-1/2 text-base-content/40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
        </div>
        
        <div class="form-control">
          <label class="label py-1">
            <span class="label-text font-medium">密码</span>
          </label>
          <div class="relative">
            <input type="password" name="password" placeholder="设置密码" class="input input-bordered w-full pl-10" required />
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 absolute left-3 top-1/2 -translate-y-1/2 text-base-content/40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
        </div>

        <div class="form-control bg-base-200/50 rounded-lg p-3 mt-1">
          <label class="label cursor-pointer justify-start gap-3 p-0">
            <input type="checkbox" name="is_admin" class="checkbox checkbox-sm checkbox-primary" />
            <span class="label-text font-medium">注册为管理员</span> 
          </label>
          <p class="text-xs text-warning mt-1 ml-8">注意：仅供开发测试使用，生产环境请勿勾选。</p>
        </div>
        
        <div class="form-control mt-4">
          <button class="btn btn-primary shadow-lg shadow-primary/30" type="submit">注 册</button>
        </div>
      </form>
      
      <div class="text-center text-sm mt-4 text-base-content/60">
        已有账号? <a href="{{ url_for('login') }}" class="link link-primary font-medium hover:text-primary-focus transition-colors">去登录</a>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

## 📄 base.html

```html
<!DOCTYPE html>
{% set is_book_mode = request.path.startswith('/book') %}
<html lang="zh-CN">
<script>
    // 立即执行主题检查，防止闪烁
    (function() {
        const savedTheme = localStorage.getItem('theme');
        const isBookMode = window.location.pathname.startsWith('/book');
        // 定义你的亮色和暗色主题
        const lightTheme = isBookMode ? 'winter' : 'cupcake';
        const darkTheme = 'business'; // 'business' 是 DaisyUI 一个很棒的深色商务主题

        if (savedTheme === 'dark') {
            document.documentElement.setAttribute('data-theme', darkTheme);
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.setAttribute('data-theme', lightTheme);
            document.documentElement.classList.remove('dark');
        }
    })();
</script>
<head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{% endblock %} - WikiBook</title>

    <link href="{{ url_for('static', filename='css/daisyui.full.css') }}" rel="stylesheet" type="text/css" />
    <script src="{{ url_for('static', filename='js/tailwindcss.js') }}"></script>
    
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/all.min.css') }}">
    
    <link rel="stylesheet" href="{{ url_for('static', filename='css/easymde.min.css') }}">
    <script src="{{ url_for('static', filename='js/easymde.min.js') }}"></script>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/link-card.css') }}">
    <script src="{{ url_for('static', filename='js/link-card.js') }}"></script>
    
    <link rel="stylesheet" href="{{ url_for('static', filename='css/atom-one-dark.min.css') }}">
    <script src="{{ url_for('static', filename='js/highlight.min.js') }}"></script>
    <script>hljs.highlightAll();</script>

    <style>
        /* --- Theme Variables (CSS 变量代替硬编码 Jinja 判断) --- */
        :root {
            /* 默认 Wiki 模式 (Amber/Orange) */
            --theme-primary: #ea580c; /* Orange-600 */
            --theme-primary-hover: #d97706; /* Amber-600 */
            --theme-bg-sidebar: #faf7f5;
            --toggle-bg: #f59e0b;
        }

        /* 修复 CSS 语法错误：将 Jinja 逻辑移出 CSS 块或确保正确闭合 */
        {% if is_book_mode %}
        :root {
            /* Book 模式 (Indigo/Purple) */
            --theme-primary: #4f46e5; /* Indigo-600 */
            --theme-primary-hover: #4338ca; /* Indigo-700 */
            --theme-bg-sidebar: #f5f7fa;
            --toggle-bg: #4f46e5;
        }
        {% endif %}

        /* --- Scrollbar --- */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #9ca3af; }

        /* --- EasyMDE Overrides --- */
        .EasyMDEContainer { background-color: white; border-radius: 0.5rem; overflow: hidden; }
        .editor-toolbar { border-color: #d1d5db; border-radius: 0.5rem 0.5rem 0 0; }
        .CodeMirror { border-color: #d1d5db; border-radius: 0 0 0.5rem 0.5rem; min-height: 400px; }
        .editor-statusbar { display: none; }

        /* --- Sidebar Menu Items --- */
        .sidebar-transition { transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
        
        .menu-item {
            position: relative;
            transition: all 0.2s ease;
            color: #57534e;
            border-radius: 0.75rem;
        }
        .menu-item:hover {
            background-color: #ffffff;
            color: var(--theme-primary);
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        .menu-item.active {
            background-color: #ffffff !important;
            color: var(--theme-primary-hover) !important;
            font-weight: 700;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }
        .menu-item.active::before {
            content: ''; position: absolute; left: 0.75rem; top: 50%; transform: translateY(-50%);
            height: 6px; width: 6px; border-radius: 50%;
            background-color: var(--theme-primary-hover);
        }
        .menu-section-title {
            font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;
            color: #a8a29e; font-weight: 800; padding: 1.5rem 1rem 0.5rem 1rem;
        }

        /* --- Layout --- */
        @media (min-width: 1024px) { .main-content { margin-left: 16rem; } }

        /* --- Toggle Switch --- */
        .mode-toggle-label {
            position: relative; display: flex; align-items: center; justify-content: space-between;
            width: 100%; height: 2rem; border-radius: 9999px;
            background-color: #f3f4f6; border: 1px solid #e5e7eb; cursor: pointer; padding: 0.25rem;
        }
        .mode-toggle-slider {
            position: absolute; top: 0.25rem; bottom: 0.25rem; left: 0.25rem;
            width: calc(50% - 0.25rem); border-radius: 9999px;
            background-color: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, background-color 0.3s;
        }
        /* Logic handled by CSS variable for color, JS logic for position */
        {% if is_book_mode %}
        .mode-toggle-slider { transform: translateX(100%); background-color: var(--toggle-bg); }
        .text-book { color: white !important; }
        {% else %}
        .mode-toggle-slider { transform: translateX(0); background-color: var(--toggle-bg); }
        .text-wiki { color: white !important; }
        {% endif %}

        .mode-text { z-index: 10; flex: 1; text-align: center; font-size: 0.75rem; font-weight: 600; color: #6b7280; transition: color 0.3s; }

        /* --- Badge & UI --- */
        .badge-icon-container { transition: transform 0.2s; }
        .badge-icon-container:hover { transform: scale(1.1); background-color: rgba(0,0,0,0.1); }

        /* --- Arc-like Liquid Grain Card --- */
        .liquid-card {
            position: relative;
            overflow: hidden;
            background-color: var(--bg-color, #ffffff);
            /* Important: background-image must override background-color if set */
            background-image: var(--bg-image, none);
            transition: transform 0.4s cubic-bezier(0.25, 1, 0.5, 1), box-shadow 0.4s ease;
            transform-style: preserve-3d;
            isolation: isolate; /* Create new stacking context */
        }
        
        .liquid-card::before, .liquid-card::after {
            content: '';
            position: absolute;
            border-radius: 50%;
            /* Use blur-level variable */
            filter: blur(var(--blur-level, 60px));
            z-index: -1;
            transition: all 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
            pointer-events: none;
            mix-blend-mode: normal;
        }
        /* Blob 1: Main Gradient Accent */
        .liquid-card::before {
            width: 140%;
            height: 140%;
            top: -20%;
            left: -20%;
            background: radial-gradient(circle at center, var(--blob-color-1, rgba(255, 100, 100, 0.15)), transparent 60%);
            transform: translate(var(--blob-1-x, 0), var(--blob-1-y, 0));
        }

        /* Blob 2: Secondary Gradient Accent */
        .liquid-card::after {
            width: 140%;
            height: 140%;
            bottom: -20%;
            right: -20%;
            background: radial-gradient(circle at center, var(--blob-color-2, rgba(100, 100, 255, 0.15)), transparent 60%);
            transform: translate(var(--blob-2-x, 0), var(--blob-2-y, 0));
        }

        /* High-Quality Grain Overlay (Arc-style) */
        .liquid-noise {
            position: absolute;
            inset: 0;
            z-index: 10;
            opacity: var(--grain-opacity, 0.05); /* Default lower for subtlety */
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='1'/%3E%3C/svg%3E");
            pointer-events: none;
            mix-blend-mode: overlay; /* Soft Light or Overlay for better blending */
            filter: contrast(120%) brightness(100%); /* Enhance grain pop */
        }

        .liquid-card:hover {
            box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.1), 0 0 0 1px rgba(0,0,0,0.05); /* Subtle depth */
        }
    </style>
    {% block extra_css %}{% endblock %}
</head>
<body class="bg-base-200 text-base-content font-sans">
    {% macro render_menu_item(endpoint, label, icon_d, badge=None, extra_active_endpoints=[]) %}
        {% set is_active = request.endpoint == endpoint or request.endpoint in extra_active_endpoints %}
        <li>
            <a href="{{ url_for(endpoint) }}" class="menu-item flex items-center gap-3 px-3 py-3 {{ 'active' if is_active else '' }}">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="{{ icon_d }}" />
                </svg>
                <span class="truncate flex-1">{{ label }}</span>
                {% if badge %}
                    <span class="badge badge-xs badge-ghost">{{ badge }}</span>
                {% endif %}
            </a>
        </li>
    {% endmacro %}

    <div id="mobile-navbar" class="lg:hidden navbar bg-base-100/90 backdrop-blur-md shadow-sm fixed top-0 w-full transition-transform duration-300 z-50">
        <div class="navbar-start">
            <button id="mobile-menu-btn" class="btn btn-ghost btn-circle" aria-label="Menu">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" /></svg>
            </button>
        </div>
        <div class="navbar-center">
            <a href="{{ url_for('index') }}" class="text-xl font-bold bg-gradient-to-r {% if is_book_mode %}from-indigo-500 to-purple-600{% else %}from-amber-500 to-orange-600{% endif %} bg-clip-text text-transparent relative group">
                W<span class="relative inline-block">i<span id="announcement-dot" class="absolute -top-0.5 -right-0.5 w-2 h-2 bg-red-500 rounded-full hidden cursor-pointer z-50 ring-1 ring-white" onclick="app.announcements.showHistory(event)"></span></span>kiBook
            </a>
        </div>
        <div class="navbar-end">
            {% if current_user.is_authenticated %}
            <a href="{{ url_for('online_users') }}" class="btn btn-ghost btn-sm gap-2 normal-case">
                <div class="badge badge-success badge-xs animate-pulse"></div>
                <span class="text-xs">{{ online_user_count }}</span>
            </a>
            {% endif %}
        </div>
    </div>

    <div id="sidebar-overlay" class="fixed inset-0 bg-black/40 backdrop-blur-sm hidden lg:hidden transition-opacity z-[51]"></div>

    <aside id="sidebar" style="background-color: var(--theme-bg-sidebar);" class="fixed left-0 top-0 h-screen w-64 border-r-[3px] border-stone-200/60 shadow-xl sidebar-transition transform -translate-x-full lg:translate-x-0 flex flex-col z-[52]">
        
        <div class="h-20 flex items-center px-6 border-b border-stone-200/50 flex-shrink-0">
            <div class="w-full">
                <div class="mode-toggle-label" onclick="window.location.href='{{ url_for('index') if is_book_mode else url_for('book_index') }}'">
                    <div class="mode-toggle-slider"></div>
                    <span class="mode-text text-wiki">Wiki</span>
                    <span class="mode-text text-book">Book</span>
                </div>
            </div>
        </div>

        <nav class="flex-1 overflow-y-auto sidebar-content px-4 py-4">
            {% block sidebar_menu %}
                {% if not is_book_mode %}
                    <div class="menu-section-title">发现</div>
                    <ul class="space-y-1">
                        {{ render_menu_item('index', 'Wiki 广场', 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10') }}
                    </ul>

                    {% if current_user.is_authenticated %}
                        {% if current_user.subscriptions %}
                        <div class="menu-section-title flex justify-between items-center group cursor-pointer">
                            <span>我的订阅</span>
                            <span class="badge badge-xs badge-ghost group-hover:bg-stone-200 transition-colors">{{ current_user.subscriptions|length }}</span>
                        </div>

                        <ul class="space-y-2 mt-1"> {% for sub in current_user.subscriptions %}
                            {% set is_active = request.view_args and request.view_args.get('wiki_id') == sub.wiki.id and request.endpoint in ['wiki_detail', 'view_page', 'edit_page', 'new_page'] %}
                            
                            {% set bg_colors = ['bg-red-50 text-red-600', 'bg-orange-50 text-orange-600', 'bg-amber-50 text-amber-600', 'bg-green-50 text-green-600', 'bg-teal-50 text-teal-600', 'bg-blue-50 text-blue-600', 'bg-indigo-50 text-indigo-600', 'bg-purple-50 text-purple-600', 'bg-pink-50 text-pink-600'] %}
                            {% set icon_bg = bg_colors[(sub.wiki.id) % 9] %}

                            <li>
                                <a href="{{ url_for('wiki_detail', wiki_id=sub.wiki.id) }}" 
                                class="group relative flex items-start gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 border border-transparent 
                                        {{ 'bg-white border-stone-200/60 shadow-sm' if is_active else 'hover:bg-white hover:shadow-sm hover:border-stone-100' }}">
                                    
                                    <div class="w-8 h-8 rounded-[0.6rem] shrink-0 grid place-items-center overflow-hidden border border-black/5 
                                                {{ icon_bg if not sub.wiki.icon_url else 'bg-white' }} shadow-sm group-hover:scale-105 transition-transform duration-200">
                                        
                                        {% if sub.wiki.icon %}
                                            {% if sub.wiki.icon.startswith('http') or sub.wiki.icon.startswith('/') %}
                                                <img src="{{ sub.wiki.icon }}" class="w-full h-full object-cover" alt="icon">
                                            {% else %}
                                                <span class="text-sm font-bold select-none">{{ sub.wiki.icon }}</span>
                                            {% endif %}
                                        {% else %}
                                            <span class="text-xs font-bold select-none">{{ sub.wiki.title[0] }}</span>
                                        {% endif %}
                                    </div>

                                    <div class="flex-1 min-w-0 flex flex-col justify-center h-8">
                                        <span class="text-[0.85rem] leading-tight font-medium text-stone-600 group-hover:text-stone-900 
                                                    {{ 'text-stone-900 font-bold' if is_active else '' }}
                                                    line-clamp-2 break-words" 
                                            title="{{ sub.wiki.title }}">
                                            {{ sub.wiki.title }}
                                        </span>
                                    </div>

                                    {% if is_active %}
                                    <div class="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1/2 w-1 h-4 bg-primary rounded-r-full"></div>
                                    {% endif %}
                                </a>
                            </li>
                            {% endfor %}
                        </ul>
                        {% endif %}

                        {% if current_user.is_admin %}
                            {% set admin_endpoints = ['manage_announcements', 'manage_users', 'create_wiki', 'edit_markdown_css'] %}
                            {% set is_admin_expanded = request.endpoint in admin_endpoints %}

                            <details class="group" {{ 'open' if is_admin_expanded else '' }}>
                                
                                <summary class="menu-section-title flex items-center justify-between cursor-pointer select-none list-none hover:text-stone-600 transition-colors">
                                    <span>管理控制台</span>
                                    
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 transition-transform duration-200 group-open:rotate-180 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                                    </svg>
                                </summary>

                                <ul class="space-y-1 mt-1 animate-slide-down">
                                    {{ render_menu_item('manage_announcements', '系统通知', 'M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z') }}
                                    
                                    {{ render_menu_item('manage_users', '用户管理', 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z') }}
                                    
                                    {{ render_menu_item('create_wiki', '新建 Wiki', 'M12 4v16m8-8H4') }}
                                    
                                    {{ render_menu_item('edit_markdown_css', 'Markdown 样式', 'M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01') }}
                                </ul>
                            </details>
                        {% endif %}
                    {% endif %}
                
                {% else %}
                    <div class="menu-section-title">Book</div>
                    <ul class="space-y-1">
                        {{ render_menu_item('book_index', '我的笔记', 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253') }}
                        {{ render_menu_item('book_calendar', '日历视图', 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z') }}
                        {{ render_menu_item('book_received', '收到笔记', 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z') }}
                        {{ render_menu_item('new_note', '新建笔记', 'M12 4v16m8-8H4') }}
                    </ul>
                {% endif %}
            {% endblock %}
        </nav>

        <div class="p-4 border-t border-stone-200/50 bg-[#faf7f5]/50 backdrop-blur-sm">
            {% if current_user.is_authenticated %}
                {% set style_class = ['bg-rose-100 text-rose-700', 'bg-orange-100 text-orange-700', 'bg-emerald-100 text-emerald-700', 'bg-cyan-100 text-cyan-700', 'bg-blue-100 text-blue-700', 'bg-violet-100 text-violet-700', 'bg-fuchsia-100 text-fuchsia-700'][(current_user.id) % 7] %}
                
                <div class="flex items-center gap-3 w-full p-3 bg-white rounded-xl shadow-sm border border-stone-100">
                    <div class="avatar placeholder">
                        <div class="{{ style_class }} w-9 h-9 rounded-full grid place-items-center ring-2 ring-stone-50 border border-current/20">
                            <span class="text-sm font-bold leading-none select-none">{{ current_user.username[0] | upper }}</span>
                        </div>
                    </div>
                    <div class="flex-1 min-w-0 text-left cursor-pointer group" onclick="window.location.href='{{ url_for('user_profile') }}'">
                        <div class="flex items-center gap-1">
                            <p class="text-sm font-bold text-stone-700 truncate group-hover:text-primary transition-colors">{{ current_user.username }}</p>
                            {% if current_user.selected_badge %}
                                <div class="badge-icon-container w-5 h-5" title="{{ current_user.selected_badge.name }}">
                                    {% if current_user.selected_badge.icon|is_image_icon %}
                                        <img src="{{ current_user.selected_badge.icon|badge_icon_url }}" alt="badge">
                                    {% else %}
                                        <span class="text-xs">{{ current_user.selected_badge.icon }}</span>
                                    {% endif %}
                                </div>
                            {% endif %}
                        </div>
                        <p class="text-xs text-stone-400 truncate">{{ '管理员' if current_user.is_admin else '用户' }}</p>
                    </div>
                    <a href="{{ url_for('logout') }}" class="btn btn-ghost btn-xs btn-square text-stone-400 hover:text-red-500 transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
                    </a>
                </div>
            {% else %}
                <a href="{{ url_for('login') }}" class="btn btn-primary w-full text-white shadow-lg shadow-primary/30">立即登录</a>
            {% endif %}
        </div>
    </aside>

    <main class="min-h-screen main-content pt-16 lg:pt-0 transition-all duration-300 relative flex flex-col bg-stone-50">
        {% if current_user.is_authenticated %}
        <div class="hidden lg:flex fixed top-6 right-8 z-40">
            <a href="{{ url_for('online_users') }}" class="btn btn-sm gap-2 normal-case glass shadow-md text-stone-600 bg-white/80 hover:bg-white border/50">
                <div class="badge badge-success badge-xs animate-pulse"></div>
                <span class="font-medium">{{ online_user_count }} 人在线</span>
            </a>
        </div>
        {% endif %}
        
        <div class="flex-1 p-2 lg:p-4">
            <div class="min-h-[calc(100vh-6rem)] lg:min-h-[calc(100vh-2rem)] bg-white/60 border-[1px] border-black shadow-xl shadow-stone-200/40 rounded-[2rem] relative backdrop-blur-xl overflow-hidden">
                <div class="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-white to-transparent pointer-events-none z-0"></div>
                
                <div class="p-4 sm:p-6 lg:p-10 relative z-10">
                    {% block content %}{% endblock %}
                </div>
            </div>
        </div>
    </main>

    <div id="toast-container" class="fixed bottom-6 right-6 flex flex-col gap-3 pointer-events-none z-[60]">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                <div data-category="{{ category }}" class="server-toast hidden">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    </div>

    <!-- Back to Top Button -->
    <button id="back-to-top" onclick="window.scrollTo({top: 0, behavior: 'smooth'})" 
            class="fixed bottom-24 right-6 btn btn-circle btn-primary shadow-lg z-40 opacity-0 pointer-events-none translate-y-10 transition-all duration-300"
            aria-label="Back to top">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18" />
        </svg>
    </button>

    <dialog id="announcement_modal" class="modal">
        <div class="modal-box w-11/12 max-w-3xl border border-stone-200 shadow-2xl">
            <h3 id="ann_modal_title" class="font-bold text-2xl mb-4 text-stone-800"></h3>
            <div id="ann_modal_content" class="prose max-w-none text-stone-600"></div>
            <div class="modal-action">
                <button class="btn btn-primary" onclick="app.announcements.confirm()">我已收到</button>
            </div>
        </div>
    </dialog>

    <dialog id="history_modal" class="modal">
        <div class="modal-box w-11/12 max-w-3xl border border-stone-200 shadow-2xl h-[80vh] flex flex-col p-0">
            <div class="p-6 border-b border-stone-100 flex justify-between items-center bg-stone-50/50">
                <h3 class="font-bold text-xl text-stone-800 flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    历史公告
                </h3>
                <form method="dialog"><button class="btn btn-sm btn-circle btn-ghost">✕</button></form>
            </div>
            <div id="history_list" class="flex-1 overflow-y-auto p-6 flex flex-col gap-4"></div>
        </div>
        <form method="dialog" class="modal-backdrop"><button>close</button></form>
    </dialog>
    
    {% block scripts %}{% endblock %}
    
    <script>
        /**
         * App Global Module
         * Encapsulates logic to prevent global namespace pollution
         */
        const app = {
            init() {
                this.sidebar.init();
                this.toast.init();
                this.backToTop.init();
                {% if current_user.is_authenticated %}
                this.heartbeat.init();
                this.announcements.init();
                {% endif %}
            },

            // --- Back to Top Logic ---
            backToTop: {
                el: document.getElementById('back-to-top'),
                
                init() {
                    if (!this.el) return;
                    window.addEventListener('scroll', () => {
                        const show = window.scrollY > 300;
                        this.el.classList.toggle('opacity-0', !show);
                        this.el.classList.toggle('pointer-events-none', !show);
                        this.el.classList.toggle('translate-y-10', !show);
                    }, { passive: true });
                }
            },

            // --- Sidebar Logic ---
            sidebar: {
                el: document.getElementById('sidebar'),
                overlay: document.getElementById('sidebar-overlay'),
                mobileBtn: document.getElementById('mobile-menu-btn'),
                mobileNavbar: document.getElementById('mobile-navbar'),

                init() {
                    this.mobileBtn?.addEventListener('click', () => this.toggle());
                    this.overlay?.addEventListener('click', () => this.toggle());
                    
                    // Mobile Navbar Auto-hide on scroll
                    let lastScroll = 0;
                    window.addEventListener('scroll', () => {
                        const currentScroll = window.scrollY;
                        if (currentScroll > 50 && currentScroll > lastScroll && !this.el.classList.contains('translate-x-0')) {
                            this.mobileNavbar?.classList.add('-translate-y-full');
                        } else {
                            this.mobileNavbar?.classList.remove('-translate-y-full');
                        }
                        lastScroll = currentScroll;
                    }, { passive: true });
                },

                toggle() {
                    if (this.el.classList.contains('-translate-x-full')) {
                        this.el.classList.remove('-translate-x-full');
                        this.overlay.classList.remove('hidden');
                    } else {
                        this.el.classList.add('-translate-x-full');
                        this.overlay.classList.add('hidden');
                    }
                }
            },

            // --- Toast Logic ---
            toast: {
                container: document.getElementById('toast-container'),
                
                init() {
                    // Load server-side messages
                    document.querySelectorAll('.server-toast').forEach((el, idx) => {
                        setTimeout(() => this.show(el.textContent, el.dataset.category), idx * 200);
                    });
                },

                show(message, type = 'info', link = null) {
                    const el = document.createElement('div');
                    const iconMap = {
                        success: '<i class="fas fa-check-circle text-green-400"></i>',
                        error: '<i class="fas fa-times-circle text-red-400"></i>',
                        warning: '<i class="fas fa-exclamation-triangle text-yellow-400"></i>',
                        info: '<i class="fas fa-info-circle text-blue-400"></i>'
                    };

                    el.className = `pointer-events-auto bg-stone-900/80 backdrop-blur-md text-white border border-white/10 ring-1 ring-white/5 shadow-xl rounded-2xl p-4 min-w-[320px] max-w-[400px] flex items-start gap-3 transition-all duration-500 translate-y-10 opacity-0`;
                    
                    if (link) {
                        el.classList.add('cursor-pointer', 'hover:bg-stone-800');
                        el.onclick = (e) => !e.target.closest('button') && (window.location.href = link);
                    }

                    el.innerHTML = `
                        <div class="mt-0.5 text-lg">${iconMap[type] || iconMap.info}</div>
                        <div class="flex-1 text-sm font-medium leading-relaxed">${message}</div>
                        <button onclick="this.parentElement.remove()" class="btn btn-xs btn-ghost btn-circle text-white/50 hover:text-white">✕</button>
                    `;

                    this.container.appendChild(el);
                    requestAnimationFrame(() => el.classList.remove('translate-y-10', 'opacity-0'));
                    setTimeout(() => {
                        el.style.opacity = '0';
                        el.style.transform = 'translateY(10px)';
                        setTimeout(() => el.remove(), 300);
                    }, 4000);
                }
            },

            {% if current_user.is_authenticated %}
            // --- Heartbeat Logic ---
            heartbeat: {
                lastTime: 0,
                interval: 30000,
                
                init() {
                    this.send();
                    // Throttle user activity events
                    ['mousedown', 'keydown', 'touchstart'].forEach(evt => {
                        window.addEventListener(evt, () => this.schedule(), { passive: true });
                    });
                    document.addEventListener('visibilitychange', () => !document.hidden && this.send());
                },

                schedule() {
                    if (Date.now() - this.lastTime > this.interval) this.send();
                },

                send() {
                    if (document.hidden) return;
                    this.lastTime = Date.now();
                    
                    fetch('/api/heartbeat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ path: window.location.pathname })
                    })
                    .then(r => r.json())
                    .then(data => {
                        if (data.notifications?.length) {
                            data.notifications.forEach(n => app.toast.show(n.message, 'info', n.link));
                            fetch('/api/notifications/read/all', { method: 'POST' });
                        }
                    })
                    .catch(() => {}); // Silent fail
                }
            },

            // --- Announcements Logic ---
            announcements: {
                currentId: null,

                init() {
                    this.check();
                },

                check() {
                    fetch('/api/announcements/check')
                        .then(r => r.json())
                        .then(data => {
                            const dot = document.getElementById('announcement-dot');
                            if (dot) dot.classList.toggle('hidden', !data.has_history);
                            
                            if (data.has_unconfirmed) {
                                this.currentId = data.announcement.id;
                                document.getElementById('ann_modal_title').textContent = data.announcement.title;
                                document.getElementById('ann_modal_content').innerHTML = data.announcement.html;
                                setTimeout(() => document.getElementById('announcement_modal').showModal(), 1000);
                            }
                        })
                        .catch(console.error);
                },

                confirm() {
                    if (!this.currentId) return;
                    const btn = document.querySelector('#announcement_modal .btn-primary');
                    btn.disabled = true;
                    
                    fetch(`/api/announcements/${this.currentId}/confirm`, { method: 'POST' })
                        .then(r => r.json())
                        .then(data => {
                            if (data.success) {
                                document.getElementById('announcement_modal').close();
                                document.getElementById('announcement-dot').classList.remove('hidden');
                                app.toast.show('已确认收到通知', 'success');
                            }
                        })
                        .finally(() => btn.disabled = false);
                },

                showHistory(e) {
                    e?.preventDefault();
                    e?.stopPropagation();
                    const list = document.getElementById('history_list');
                    document.getElementById('history_modal').showModal();
                    list.innerHTML = '<div class="grid place-items-center h-full"><span class="loading loading-spinner"></span></div>';

                    fetch('/api/announcements/history')
                        .then(r => r.json())
                        .then(data => {
                            list.innerHTML = '';
                            if (!data.announcements?.length) {
                                list.innerHTML = '<div class="text-center text-stone-400 py-10">暂无历史公告</div>';
                                return;
                            }
                            data.announcements.forEach(ann => {
                                const el = document.createElement('div');
                                el.className = 'collapse collapse-arrow bg-white border border-stone-200 rounded-xl';
                                el.innerHTML = `
                                    <input type="checkbox" />
                                    <div class="collapse-title font-medium flex justify-between pr-12">
                                        <span>${ann.title}</span>
                                        <div class="flex items-center gap-2">
                                            ${!ann.is_confirmed ? '<span class="badge badge-xs badge-error">未读</span>' : ''}
                                            <span class="text-xs text-stone-400 font-mono">${ann.created_at}</span>
                                        </div>
                                    </div>
                                    <div class="collapse-content border-t border-stone-100 bg-stone-50/50 pt-4 prose max-w-none text-sm">${ann.html}</div>
                                `;
                                list.appendChild(el);
                            });
                        });
                }
            }
            {% endif %}
        };

        // Boot
        document.addEventListener('DOMContentLoaded', () => {
            app.init();
        });
    </script>
</body>
</html>
```

## 📄 login.html

```html
{% extends "base.html" %}

{% block content %}
<div class="min-h-[calc(100vh-10rem)] flex items-center justify-center">
  <div class="card w-full max-w-sm bg-base-100 shadow-xl border border-base-200">
    <div class="card-body">
      <div class="text-center mb-6">
        <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-lg shadow-orange-100 mx-auto mb-4 transform -rotate-3">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-base-content">欢迎回来</h2>
        <p class="text-sm text-base-content/60 mt-1">登录 WikiBook 管理您的知识库</p>
      </div>
      
      <form method="post" class="flex flex-col gap-4">
        <div class="form-control">
          <label class="label">
            <span class="label-text font-medium">用户名</span>
          </label>
          <div class="relative">
            <input type="text" name="username" placeholder="请输入用户名" class="input input-bordered w-full pl-10" required />
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 absolute left-3 top-1/2 -translate-y-1/2 text-base-content/40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
        </div>
        
        <div class="form-control">
          <label class="label">
            <span class="label-text font-medium">密码</span>
          </label>
          <div class="relative">
            <input type="password" name="password" placeholder="请输入密码" class="input input-bordered w-full pl-10" required />
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 absolute left-3 top-1/2 -translate-y-1/2 text-base-content/40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
        </div>
        
        <div class="form-control">
          <label class="label cursor-pointer justify-start gap-2">
            <input type="checkbox" name="remember" class="checkbox checkbox-sm checkbox-primary" checked />
            <span class="label-text">记住我 (30天内免登录)</span>
          </label>
        </div>

        <div class="form-control mt-6">
          <button class="btn btn-primary shadow-lg shadow-primary/30" type="submit">登 录</button>
        </div>
      </form>
      
      <!-- 
      <div class="text-center text-sm mt-6 text-base-content/60">
        还没有账号? <a href="{{ url_for('register') }}" class="link link-primary font-medium hover:text-primary-focus transition-colors">立即注册</a>
      </div>
      -->
    </div>
  </div>
</div>
{% endblock %}
```

## 📄 book/my_notes.html

```html
{% extends "base.html" %}

{% block title %}我的笔记{% endblock %}

{% block scripts %}
<script src="{{ url_for('static', filename='js/echarts.min.js') }}"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('heatmap-container');
    const yearSelect = document.getElementById('heatmap-year-select');
    
    if (!container) return;
    
    let allData = [];
    let charts = []; // Store chart instances
    
    // Fetch data
    fetch('{{ url_for("get_heatmap_data") }}')
        .then(response => response.json())
        .then(res => {
            allData = res.data;
            
            // Extract years
            const years = new Set();
            const currentYear = new Date().getFullYear();
            
            years.add(currentYear);
            allData.forEach(item => {
                const year = new Date(item[0]).getFullYear();
                years.add(year);
            });
            
            const sortedYears = Array.from(years).sort((a, b) => b - a);
            
            yearSelect.innerHTML = '';
            sortedYears.forEach(year => {
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year + '年';
                if (year === currentYear) option.selected = true;
                yearSelect.appendChild(option);
            });
            
            if (sortedYears.length > 0) {
                yearSelect.classList.remove('hidden');
                initCharts(yearSelect.value);
            }
            
            yearSelect.addEventListener('change', function() {
                initCharts(this.value);
            });
            
            window.addEventListener('resize', function() {
                charts.forEach(c => c.resize());
            });
        })
        .catch(err => console.error('Error loading heatmap data:', err));
        
    function initCharts(year) {
        // Clear container and instances
        container.innerHTML = '';
        charts.forEach(c => c.dispose());
        charts = [];
        
        // Create 12 months
         for (let m = 1; m <= 12; m++) {
             const monthDiv = document.createElement('div');
             // Height enough for title + 5-6 weeks
             // 5 weeks * 13px + gaps + title ~ 100px
             // Width: max 6 weeks * (13 + 3) = 96px. Let's use 100px to be safe.
             monthDiv.style.height = '120px'; 
             monthDiv.style.width = '80px'; 
             monthDiv.style.flex = '0 0 auto'; // Prevent shrinking/growing
             container.appendChild(monthDiv);
             
             renderMonthChart(monthDiv, year, m);
         }
     }

     function renderMonthChart(dom, year, month) {
         const myChart = echarts.init(dom);
         charts.push(myChart);
         
         // Calculate date range for this month
         // Month is 1-based
         const startDate = new Date(year, month - 1, 1);
         const endDate = new Date(year, month, 0); // Last day of current month
         
         const startStr = echarts.format.formatTime('yyyy-MM-dd', startDate);
         const endStr = echarts.format.formatTime('yyyy-MM-dd', endDate);
         
         // Prepare data
         // Filter allData for this month only? No, ECharts calendar handles range automatically.
         // But for better performance/logic, we pass filled data.
         
         // To ensure we fill 0s for the specific month
         const dateMap = new Map(allData.map(item => [item[0], item[1]]));
         const filledData = [];
         
         let curr = new Date(startDate);
         while (curr <= endDate) {
             const dateStr = echarts.format.formatTime('yyyy-MM-dd', curr);
             const count = dateMap.get(dateStr) || 0;
             filledData.push([dateStr, count]);
             curr.setDate(curr.getDate() + 1);
         }
 
         const option = {
             tooltip: {
                 position: 'top',
                 formatter: function (p) {
                     const format = echarts.format.formatTime('yyyy-MM-dd', p.data[0]);
                     return format + ': 活跃度 ' + p.data[1];
                 }
             },
             visualMap: {
                 min: 0,
                 max: 20,
                 calculable: false,
                 show: false,
                 inRange: {
                     color: ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39']
                 }
             },
             calendar: {
                 top: 20,
                 left: 'center', // Center in the 100px box
                 cellSize: [13, 13],
                 range: [startStr, endStr],
                 itemStyle: {
                     borderWidth: 3,
                     borderColor: '#fff',
                     borderRadius: 2
                 },
                 yearLabel: { show: false },
                 // Only show month name as title
                 dayLabel: { show: false }, 
                 monthLabel: { 
                     show: true,
                     nameMap: 'cn',
                     position: 'start', // Put at top
                     color: '#374151',
                     fontSize: 14,
                     fontWeight: 'bold',
                     margin: 5
                 },
                 splitLine: { show: false }
             },
             series: {
                 type: 'heatmap',
                 coordinateSystem: 'calendar',
                 data: filledData,
                 itemStyle: {
                     // Inherits from calendar.itemStyle
                 }
             }
         };
         
         myChart.setOption(option);
     }
});
</script>
{% endblock %}

{% block content %}
<div class="space-y-8">
    <!-- Header & Stats -->
    <div class="bg-base-100 rounded-3xl p-8 shadow-sm border border-base-200">
        <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-8">
            <div>
                <h1 class="text-3xl font-extrabold text-base-content tracking-tight">我的笔记空间</h1>
                <p class="text-base-content/60 mt-2">管理您的个人知识库与阅读数据</p>
            </div>
            <a href="{{ url_for('new_note') }}" class="btn btn-primary gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
                新建笔记
            </a>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div class="stats shadow bg-base-100 border border-base-200">
                <div class="stat">
                    <div class="stat-title">我的笔记</div>
                    <div class="stat-value text-primary">{{ notes|length }}</div>
                    <div class="stat-desc">累计创建</div>
                </div>
            </div>
            
            <div class="stats shadow bg-base-100 border border-base-200">
                <div class="stat">
                    <div class="stat-title">总学习时长</div>
                    <div class="stat-value text-secondary text-2xl">{{ stats.total_formatted }}</div>
                    <div class="stat-desc">今日: {{ stats.today_formatted }}</div>
                </div>
            </div>

            <div class="stats shadow bg-base-100 border border-base-200">
                <div class="stat">
                    <div class="stat-title">阅读量</div>
                    <div class="stat-value text-accent">{{ stats.total_reads }}</div>
                    <div class="stat-desc">累计阅读笔记</div>
                </div>
            </div>

            <div class="stats shadow bg-base-100 border border-base-200">
                <div class="stat">
                    <div class="stat-title">影响力</div>
                    <div class="stat-value text-info">{{ stats.total_views_received }}</div>
                    <div class="stat-desc">被阅读次数</div>
                </div>
            </div>
        </div>
        
        <!-- Activity Heatmap -->
        <div class="card bg-base-100 shadow-sm border border-base-200 mb-8">
            <div class="card-body p-6">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="card-title text-lg">学习活跃度</h3>
                    <select id="heatmap-year-select" class="select select-sm select-bordered w-32 hidden">
                        <!-- Options populated by JS -->
                    </select>
                </div>
                <!-- Responsive Flex Layout for Monthly Heatmaps -->
                <!-- Use flex-wrap to allow wrapping on narrow screens.
                     Gap set to 13px as requested.
                     justify-start to align items to the left. -->
                <div id="heatmap-container" class="flex flex-wrap gap-[1px] justify-center">
                    <!-- 12 Divs will be injected here -->
                </div>
            </div>
        </div>

        <!-- 详细学习时长统计 -->
        <div class="collapse collapse-arrow border border-base-200 bg-base-100 rounded-box mb-8">
            <input type="checkbox" /> 
            <div class="collapse-title text-xl font-medium flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                学习时长统计详情
            </div>
            <div class="collapse-content"> 
                <div class="overflow-x-auto">
                    <table class="table w-full">
                        <thead>
                            <tr>
                                <th>时间段</th>
                                <th>时长</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td>今日</td><td class="font-bold">{{ stats.today_formatted }}</td></tr>
                            <tr><td>最近一周</td><td>{{ stats.week_formatted }}</td></tr>
                            <tr><td>最近一月</td><td>{{ stats.month_formatted }}</td></tr>
                            <tr><td>最近三月</td><td>{{ stats.three_months_formatted }}</td></tr>
                            <tr><td>最近半年</td><td>{{ stats.six_months_formatted }}</td></tr>
                            <tr><td>最近一年</td><td>{{ stats.year_formatted }}</td></tr>
                            <tr><td>总计</td><td class="text-primary font-bold">{{ stats.total_formatted }}</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- Search & List -->
    <div>
        <div class="flex flex-col md:flex-row justify-between items-center gap-4 mb-6">
            <h2 class="text-xl font-bold text-base-content flex items-center gap-2">
                全部笔记列表
                <span class="badge badge-lg badge-ghost">{{ notes|length }}</span>
            </h2>
            
            <!-- 整合的搜索与快速笔记栏 -->
            <div class="relative group w-full md:w-96">
                <input type="text" id="quickInput" name="q" value="{{ q }}" 
                    class="input input-bordered w-full pl-4 pr-32 bg-base-100 focus:border-primary focus:ring-2 focus:ring-primary/10 rounded-xl transition-all" 
                    placeholder="输入内容搜索或生成笔记...">
                
                <div class="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                    <button type="button" onclick="quickCreate()" class="btn btn-xs btn-ghost text-primary hover:bg-primary/10" title="生成快速笔记">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
                        <span class="hidden sm:inline">生成</span>
                    </button>
                    <div class="w-px h-4 bg-base-300"></div>
                    <button type="button" onclick="doSearch()" class="btn btn-xs btn-ghost hover:bg-base-200" title="搜索">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                        <span class="hidden sm:inline">搜索</span>
                    </button>
                </div>
            </div>
        </div>

        <script>
        function doSearch() {
            const val = document.getElementById('quickInput').value.trim();
            window.location.href = "{{ url_for('my_notes') }}?q=" + encodeURIComponent(val);
        }

        async function quickCreate() {
            const val = document.getElementById('quickInput').value.trim();
            if (!val) {
                alert('请输入内容');
                return;
            }
            
            try {
                const btn = event.currentTarget;
                const originalText = btn.innerHTML;
                btn.disabled = true;
                btn.innerHTML = '<span class="loading loading-spinner loading-xs"></span>';
                
                const response = await fetch("{{ url_for('quick_create_note') }}", {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ content: val })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    window.location.href = "/book/notes/" + data.note_id;
                } else {
                    alert('创建失败: ' + (data.error || '未知错误'));
                    btn.disabled = false;
                    btn.innerHTML = originalText;
                }
            } catch (error) {
                console.error('Error:', error);
                alert('请求出错');
                // Restore button state
                const btn = event.currentTarget; // This might fail if event is lost, but simple alert is enough
                window.location.reload();
            }
        }
        
        // Enter key handler
        document.getElementById('quickInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                doSearch();
            }
        });
        </script>

        {% if notes %}
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {% for note in notes %}
                <a href="{{ url_for('view_note', note_id=note.id) }}" class="card bg-base-100 shadow-sm hover:shadow-md transition-all border border-base-200 group h-full">
                    <div class="card-body p-5">
                        <div class="flex justify-between items-start mb-2">
                            <h3 class="card-title text-lg group-hover:text-primary transition-colors line-clamp-1">{{ note.title }}</h3>
                            {% if note.is_featured %}
                            <span class="badge badge-xs badge-warning flex-shrink-0">精选</span>
                            {% endif %}
                        </div>
                        <p class="text-sm text-base-content/60 line-clamp-3 flex-grow">
                            {{ note.content_md | striptags }}
                        </p>
                        <div class="flex items-center justify-between mt-4 pt-3 border-t border-base-200/50 text-xs text-base-content/40">
                            <span>{{ note.updated_at.strftime('%Y-%m-%d %H:%M') }}</span>
                            {% if note.shares %}
                            <span class="flex items-center gap-1" title="已分享给 {{ note.shares|length }} 人">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" /></svg>
                                {{ note.shares|length }}
                            </span>
                            {% endif %}
                        </div>
                    </div>
                </a>
                {% endfor %}
            </div>
        {% else %}
            <div class="text-center py-20 bg-base-100 rounded-3xl border border-base-200 border-dashed">
                <div class="bg-base-200/50 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-base-content/30" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
                </div>
                <h3 class="text-lg font-bold text-base-content/70">
                    {% if q %}没有找到匹配的笔记{% else %}暂时没有笔记{% endif %}
                </h3>
                <p class="text-sm text-base-content/50 mt-1">
                    {% if q %}尝试换个关键词搜索{% else %}记录下您的第一个想法吧{% endif %}
                </p>
                {% if not q %}
                <a href="{{ url_for('new_note') }}" class="btn btn-primary mt-6">新建笔记</a>
                {% endif %}
            </div>
        {% endif %}
    </div>
</div>
{% endblock %}
```

## 📄 book/index.html

```html
{% extends "base.html" %}

{% block title %}Book 首页{% endblock %}

{% block extra_css %}
{% endblock %}

{% block content %}
<div class="text-center space-y-8 py-12 bg-gradient-to-b from-primary/5 to-transparent rounded-3xl mb-8 relative z-10">
    <div class="flex items-center justify-center gap-4 relative">
        <h1 class="text-4xl lg:text-5xl font-extrabold text-base-content tracking-tight">
            知识笔记库 <span class="text-primary">WikiBook</span>
        </h1>
        
        <!-- Last Edited Note Shortcut -->
        {% if last_note %}
        <div class="absolute left-1/2 ml-[180px] lg:ml-[220px] top-1/2 -translate-y-1/2" title="继续编辑: {{ last_note.title }}">
            <a href="{{ url_for('view_note', note_id=last_note.id) }}" class="w-12 h-12 rounded-full bg-white shadow-lg border border-primary/20 flex items-center justify-center hover:scale-110 transition-transform group relative">
                <span class="text-2xl">{{ last_note.icon or '📝' }}</span>
                <span class="absolute left-full ml-3 px-2 py-1 bg-base-300 text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap shadow-sm pointer-events-none">
                    {{ last_note.title }}
                </span>
            </a>
        </div>
        {% endif %}
    </div>
    
    <p class="text-lg text-base-content/60 max-w-2xl mx-auto mt-4">
        探索精选笔记，记录学习心得，与同学分享知识点滴。
    </p>

    <div class="max-w-2xl mx-auto px-4 relative z-50 mt-8">
        <div class="relative group">
            <input type="text" id="quickInput" name="q" value="{{ q }}" 
                oninput="handleSearchInput(this.value)"
                class="input input-lg w-full pl-12 pr-32 bg-white shadow-xl border-stone-200 focus:border-primary focus:ring-4 focus:ring-primary/10 rounded-full transition-all duration-300" 
                placeholder="搜索笔记内容或生成快速笔记..." autocomplete="off">
            
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 absolute left-4 top-1/2 -translate-y-1/2 text-stone-400 group-focus-within:text-primary transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>

            <div class="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                <button type="button" onclick="quickCreate()" class="btn btn-sm btn-ghost text-primary hover:bg-primary/10 rounded-full" title="生成快速笔记">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
                    <span class="hidden sm:inline">快速笔记</span>
                </button>
                <div class="w-px h-6 bg-base-300"></div>
                <button type="button" onclick="doSearch()" class="btn btn-sm btn-ghost hover:bg-base-200 rounded-full" title="搜索">
                    <span class="hidden sm:inline">搜索</span>
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 sm:hidden" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                </button>
            </div>

            <!-- Instant Search Dropdown -->
            <div id="instantSearchResults" class="absolute top-full left-0 right-0 mt-2 bg-base-100 rounded-2xl shadow-2xl border border-base-200 hidden overflow-hidden transition-all text-left">
                <!-- Results injected via JS -->
            </div>
        </div>
    </div>
</div>

<div class="flex justify-between items-center mb-6 px-1">
    <h2 class="text-xl font-bold text-base-content flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21L10.714 14.143 5 12l5.714-2.143L13 3z" /></svg>
        精选笔记
    </h2>
    <div class="flex gap-2">
        <a href="{{ url_for('my_notes') }}" class="btn btn-sm btn-ghost gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
            我的统计
        </a>
        <a href="{{ url_for('new_note') }}" class="btn btn-sm btn-primary gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
            新建笔记
        </a>
    </div>
</div>

{% if not q %}
    <!-- Featured Notes -->
    {% if featured_notes %}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
        {% for note in featured_notes %}
        <a href="{{ url_for('view_note', note_id=note.id) }}" class="card bg-base-100 shadow-sm hover:shadow-lg transition-all border border-base-200 group h-full">
            <div class="card-body p-5">
                <div class="flex items-center gap-2 mb-3">
                    <div class="avatar placeholder">
                        <div class="bg-primary/10 text-primary rounded-full w-8 h-8">
                            <span class="text-xs font-bold">{{ note.user.username[0] | upper }}</span>
                        </div>
                    </div>
                    <div>
                        <div class="text-xs font-bold text-base-content/80">{{ note.user.username }}</div>
                        <div class="text-[10px] text-base-content/40">{{ note.updated_at.strftime('%Y-%m-%d') }}</div>
                    </div>
                    <div class="ml-auto badge badge-xs badge-warning gap-1">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>
                        精选
                    </div>
                </div>
                
                <h3 class="card-title text-lg mb-2 group-hover:text-primary transition-colors line-clamp-1">{{ note.title }}</h3>
                <p class="text-sm text-base-content/60 line-clamp-3 mb-4 flex-grow">
                    {{ note.content_md | striptags }}
                </p>
                
                <div class="flex items-center text-xs text-base-content/40 pt-3 border-t border-base-200/50">
                    <span class="flex items-center gap-1">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        阅读笔记
                    </span>
                </div>
            </div>
        </a>
        {% endfor %}
    </div>
    {% elif not my_notes and not shared_notes %}
    <div class="text-center py-12 mb-8">
        <div class="bg-base-200/50 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-base-content/30" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
        </div>
        <h3 class="text-lg font-bold text-base-content/70">暂无精选笔记</h3>
        <p class="text-sm text-base-content/50 mt-1">管理员尚未推荐任何笔记</p>
    </div>
    {% endif %}

    <div class="divider text-base-content/30 text-sm font-medium my-8">个人空间</div>

    <!-- Tabs -->
    <div class="flex justify-center mb-8">
        <div class="tabs tabs-boxed bg-base-100 p-1 rounded-xl border border-base-200 inline-flex shadow-sm">
            <a class="tab tab-lg px-8 rounded-lg transition-all tab-active bg-white shadow-sm font-bold" id="tab-my" onclick="switchTab('my')">
                我的笔记
                <span class="ml-2 badge badge-sm badge-ghost">{{ my_notes|length }}</span>
            </a>
            <a class="tab tab-lg px-8 rounded-lg transition-all font-medium text-base-content/70 hover:bg-base-200/50" id="tab-shared" onclick="switchTab('shared')">
                收到笔记
                <span class="ml-2 badge badge-sm badge-ghost">{{ shared_notes|length }}</span>
            </a>
        </div>
    </div>

    <!-- My Notes -->
    <div id="content-my" class="animate-fade-in">
        {% if my_notes %}
            <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {% for note in my_notes %}
                <a href="{{ url_for('view_note', note_id=note.id) }}" class="card bg-base-100 shadow-sm hover:shadow-xl transition-all duration-300 border border-base-200 group h-full">
                    <div class="h-2 bg-gradient-to-r from-primary/40 to-secondary/40"></div>
                    <div class="card-body p-5">
                        <div class="flex justify-between items-start mb-2">
                            <div class="flex items-center gap-2">
                                <div class="w-8 h-8 rounded-lg bg-base-200 flex items-center justify-center text-lg">
                                    {{ note.icon or '📝' }}
                                </div>
                                <span class="text-xs text-base-content/40 font-mono">{{ note.updated_at.strftime('%m-%d') }}</span>
                            </div>
                            <div class="flex gap-1">
                                {% for tag in note.tags[:2] %}
                                    <span class="badge badge-xs badge-outline opacity-70">{{ tag.name }}</span>
                                {% endfor %}
                            </div>
                        </div>

                        <h3 class="card-title text-lg font-bold group-hover:text-primary transition-colors line-clamp-1 mb-1">{{ note.title }}</h3>
                        <p class="text-sm text-base-content/60 line-clamp-3 leading-relaxed">
                            {{ note.content_md | striptags }}
                        </p>
                        
                        <div class="card-actions justify-end mt-4 pt-3 border-t border-base-100 items-center">
                            {% if note.is_featured %}
                            <div class="badge badge-xs badge-warning" title="已设为精选">精选</div>
                            {% endif %}
                            {% if note.shares %}
                            <div class="badge badge-xs badge-ghost gap-1" title="已分享给 {{ note.shares|length }} 人">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" /></svg>
                                {{ note.shares|length }}
                            </div>
                            {% endif %}
                        </div>
                    </div>
                </a>
                {% endfor %}
            </div>
        {% else %}
            <div class="text-center py-16 bg-base-100 rounded-3xl border border-dashed border-base-300">
                <div class="w-16 h-16 bg-base-200 rounded-full flex items-center justify-center mx-auto mb-4 text-3xl">📝</div>
                <h3 class="font-bold text-lg opacity-70">还没有笔记</h3>
                <p class="text-sm opacity-50 mb-6">记录下你的第一个灵感吧</p>
                <a href="{{ url_for('new_note') }}" class="btn btn-primary btn-sm">创建笔记</a>
            </div>
        {% endif %}
    </div>

    <!-- Shared Notes -->
    <div id="content-shared" class="hidden animate-fade-in">
        {% if shared_notes %}
            <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {% for note in shared_notes %}
                <a href="{{ url_for('view_note', note_id=note.id) }}" class="card bg-base-100 shadow-sm hover:shadow-xl transition-all duration-300 border border-base-200 group h-full">
                    <div class="h-2 bg-gradient-to-r from-secondary/40 to-accent/40"></div>
                    <div class="card-body p-5">
                        <div class="flex justify-between items-start mb-2">
                            <div class="flex items-center gap-2">
                                <div class="w-8 h-8 rounded-lg bg-base-200 flex items-center justify-center text-lg">
                                    {{ note.icon or '📬' }}
                                </div>
                                <div class="flex flex-col">
                                    <span class="text-xs font-bold text-base-content/80">{{ note.user.username }}</span>
                                    <span class="text-[10px] text-base-content/40 font-mono">分享于 {{ note.updated_at.strftime('%m-%d') }}</span>
                                </div>
                            </div>
                            <div class="flex gap-1">
                                {% for tag in note.tags[:2] %}
                                    <span class="badge badge-xs badge-outline opacity-70">{{ tag.name }}</span>
                                {% endfor %}
                            </div>
                        </div>

                        <h3 class="card-title text-lg font-bold group-hover:text-primary transition-colors line-clamp-1 mb-1">{{ note.title }}</h3>
                        <p class="text-sm text-base-content/60 line-clamp-3 leading-relaxed">
                            {{ note.content_md | striptags }}
                        </p>
                    </div>
                </a>
                {% endfor %}
            </div>
        {% else %}
            <div class="text-center py-16 bg-base-100 rounded-3xl border border-dashed border-base-300">
                <div class="w-16 h-16 bg-base-200 rounded-full flex items-center justify-center mx-auto mb-4 text-3xl">📭</div>
                <h3 class="font-bold text-lg opacity-70">暂时没有收到笔记</h3>
                <p class="text-sm opacity-50 mb-6">同学分享的笔记会出现在这里</p>
            </div>
        {% endif %}
    </div>

{% else %}
    <!-- Search Results View -->
    <div class="space-y-12 mb-12">
        <div class="text-center">
            <h2 class="text-2xl font-bold text-base-content">
                搜索结果：<span class="text-primary">"{{ q }}"</span>
            </h2>
            <p class="text-base-content/60 mt-2">
                共找到 {{ title_matches|length + content_matches|length }} 条匹配结果
            </p>
        </div>
        
        <div class="space-y-6">
            <h3 class="text-xl font-bold text-base-content/80 flex items-center gap-2 border-b border-base-200 pb-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" /></svg>
                标题匹配
                <span class="badge badge-ghost">{{ title_matches|length }}</span>
            </h3>
            {% if title_matches %}
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {% for note in title_matches %}
                    <a href="{{ url_for('view_note', note_id=note.id) }}" class="card bg-base-100 shadow-sm hover:shadow-md transition-all border border-base-200 group">
                        <div class="card-body p-5">
                            <div class="flex items-center gap-2 mb-2">
                                {% if note.source_type == 'my' %}
                                    <div class="badge badge-xs badge-primary">我的</div>
                                {% else %}
                                    <div class="badge badge-xs badge-secondary">来自 {{ note.user.username }}</div>
                                {% endif %}
                                <span class="text-xs text-base-content/40 ml-auto">{{ note.updated_at.strftime('%Y-%m-%d') }}</span>
                            </div>
                            <h3 class="card-title text-lg group-hover:text-primary transition-colors">
                                {{ note.title | replace(q, '<mark class="bg-yellow-200 rounded-sm px-0.5">' + q + '</mark>') | safe }}
                            </h3>
                            <p class="text-sm text-base-content/60 line-clamp-2 mt-2">
                                {{ note.content_md | striptags }}
                            </p>
                        </div>
                    </a>
                    {% endfor %}
                </div>
            {% else %}
                <p class="text-base-content/40 italic pl-4">没有匹配的标题</p>
            {% endif %}
        </div>

        <div class="space-y-6">
            <h3 class="text-xl font-bold text-base-content/80 flex items-center gap-2 border-b border-base-200 pb-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                内容匹配
                <span class="badge badge-ghost">{{ content_matches|length }}</span>
            </h3>
            {% if content_matches %}
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {% for note in content_matches %}
                    <a href="{{ url_for('view_note', note_id=note.id) }}" class="card bg-base-100 shadow-sm hover:shadow-md transition-all border border-base-200 group">
                        <div class="card-body p-5">
                            <div class="flex items-center gap-2 mb-2">
                                {% if note.source_type == 'my' %}
                                    <div class="badge badge-xs badge-primary">我的</div>
                                {% else %}
                                    <div class="badge badge-xs badge-secondary">来自 {{ note.user.username }}</div>
                                {% endif %}
                                <span class="text-xs text-base-content/40 ml-auto">{{ note.updated_at.strftime('%Y-%m-%d') }}</span>
                            </div>
                            <h3 class="card-title text-lg group-hover:text-primary transition-colors">{{ note.title }}</h3>
                            <p class="text-sm text-base-content/60 line-clamp-2 mt-2">
                                {{ note.content_md | striptags | replace(q, '<mark class="bg-yellow-200 rounded-sm px-0.5">' + q + '</mark>') | safe }}
                            </p>
                        </div>
                    </a>
                    {% endfor %}
                </div>
            {% else %}
                <p class="text-base-content/40 italic pl-4">没有匹配的内容</p>
            {% endif %}
        </div>
    </div>
{% endif %}

{% endblock %}

{% block scripts %}
<script>
let searchTimeout;

function handleSearchInput(val) {
    clearTimeout(searchTimeout);
    const resultsDiv = document.getElementById('instantSearchResults');
    
    if (!val.trim()) {
        resultsDiv.classList.add('hidden');
        resultsDiv.innerHTML = '';
        return;
    }

    searchTimeout = setTimeout(async () => {
        try {
            const response = await fetch(`/api/notes/search?q=${encodeURIComponent(val)}`);
            const data = await response.json();
            
            if (data.results && data.results.length > 0) {
                resultsDiv.innerHTML = data.results.map(item => `
                    <a href="/book/notes/${item.id}" class="flex items-center gap-3 p-4 hover:bg-base-100 border-b border-base-100 last:border-0 transition-colors cursor-pointer group">
                        <div class="w-8 h-8 rounded bg-primary/10 flex items-center justify-center text-lg">
                            ${item.icon || (item.type === 'my' ? '📝' : '📬')}
                        </div>
                        <div class="flex-1 min-w-0">
                            <h4 class="font-bold text-sm text-base-content truncate group-hover:text-primary">${item.title}</h4>
                            <p class="text-xs text-base-content/50 truncate">
                                ${item.type === 'my' ? '我的笔记' : `来自 ${item.user}`}
                            </p>
                        </div>
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-base-content/30 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                        </svg>
                    </a>
                `).join('');
                resultsDiv.classList.remove('hidden');
            } else {
                resultsDiv.innerHTML = `
                    <div class="p-4 text-center text-sm text-base-content/50">
                        没有找到相关笔记，按回车搜索更多
                    </div>
                `;
                resultsDiv.classList.remove('hidden');
            }
        } catch (e) {
            console.error(e);
        }
    }, 300);
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    const container = document.querySelector('.relative.group');
    const resultsDiv = document.getElementById('instantSearchResults');
    if (container && !container.contains(e.target) && resultsDiv) {
        resultsDiv.classList.add('hidden');
    }
});

function switchTab(tab) {
    // Update Tabs
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('tab-active', 'bg-white', 'shadow-sm'));
    document.getElementById(`tab-${tab}`).classList.add('tab-active', 'bg-white', 'shadow-sm');
    
    // Update Content
    document.getElementById('content-my').classList.add('hidden');
    document.getElementById('content-shared').classList.add('hidden');
    document.getElementById(`content-${tab}`).classList.remove('hidden');
}

function doSearch() {
    const val = document.getElementById('quickInput').value.trim();
    window.location.href = "{{ url_for('book_index') }}?q=" + encodeURIComponent(val);
}

async function quickCreate() {
    const val = document.getElementById('quickInput').value.trim();
    if (!val) {
        alert('请输入内容');
        return;
    }
    
    try {
        const btn = event.currentTarget;
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="loading loading-spinner loading-xs"></span>';
        
        const response = await fetch("{{ url_for('quick_create_note') }}", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content: val })
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.location.href = "/book/notes/" + data.note_id;
        } else {
            alert('创建失败: ' + (data.error || '未知错误'));
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    } catch (error) {
        console.error('Error:', error);
        alert('请求出错');
        window.location.reload();
    }
}

// Enter key handler
document.getElementById('quickInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        doSearch();
    }
});
</script>
{% endblock %}
```

## 📄 book/new_note.html

```html
{% extends "base.html" %}

{% block title %}新建笔记{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/vendor/github.min.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/vendor/easymde.min.css') }}">

<style>
    /* =========================================
       EasyMDE 容器样式 (复用 Wiki 逻辑)
       ========================================= */
    .EasyMDEContainer {
        display: flex;
        flex-direction: column;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        /* 适配笔记页面：自动计算高度，填满屏幕剩余空间 */
        height: calc(100vh - 320px); 
        min-height: 400px;
    }

    /* 全屏模式修正 */
    .EasyMDEContainer.fullscreen {
        height: 100vh !important;
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        z-index: 99999 !important;
        border-radius: 0 !important;
        border: none !important;
    }

    /* 工具栏样式 */
    .editor-toolbar {
        flex-shrink: 0;
        border: none !important;
        border-bottom: 1px solid #e5e7eb !important;
        background-color: #f9fafb;
        border-radius: 0.5rem 0.5rem 0 0;
        padding: 0.5rem !important;
        white-space: nowrap;
        overflow-x: auto;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .EasyMDEContainer.fullscreen .editor-toolbar { border-radius: 0; }
    .editor-toolbar::-webkit-scrollbar { height: 0; }

    /* 编辑区样式 */
    .CodeMirror {
        flex-grow: 1;
        height: auto !important;
        border: none !important;
        border-radius: 0 0 0.5rem 0.5rem;
        font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
        font-size: 15px; /* 笔记字体稍微大一点点 */
        line-height: 1.7;
        background: #fff;
        padding: 10px;
    }
    .CodeMirror-scroll { min-height: 100% !important; }

    /* 预览区样式 */
    .editor-preview-side {
        border: none !important;
        border-left: 1px solid #e5e7eb !important;
        background-color: #fafaf9;
        position: absolute;
        bottom: 0;
        right: 0;
        top: 50px;
        height: auto !important;
        z-index: 50;
    }

    /* 分屏布局控制 (左右各50%) */
    .EasyMDEContainer.sided--no-fullscreen .CodeMirror { width: 50% !important; }
    .EasyMDEContainer.sided--no-fullscreen .editor-preview-side {
        width: 50% !important;
        top: 61px !important;
        display: block !important;
    }
    
    /* 修复公式间距 */
    .editor-preview-side p { margin: 0.5em 0; }
</style>
{% endblock %}

{% block content %}
<div class="max-w-6xl mx-auto px-4">
    <div class="flex items-center gap-2 text-sm text-base-content/60 mb-6 pt-4">
        <a href="{{ url_for('book_index') }}" class="hover:text-primary transition-colors">我的笔记</a>
        <span>/</span>
        <span class="text-base-content/80 font-medium">新建笔记</span>
    </div>

    <div class="card bg-base-100 shadow-xl border border-base-200 overflow-hidden">
        <div class="card-body p-0">
            <form method="post" class="flex flex-col">
                
                <div class="p-6 border-b border-base-200 bg-base-100/50 space-y-4">
                    <input type="text" name="title" placeholder="输入笔记标题..." class="input input-ghost text-2xl font-bold w-full focus:bg-transparent px-0 placeholder:text-base-content/30 border-none focus:outline-none" required autofocus />
                    <input type="text" name="tags" placeholder="标签 (用逗号分隔，如: 想法, 待办)" class="input input-sm input-ghost w-full focus:bg-transparent px-0 placeholder:text-base-content/30 text-stone-500" />
                </div>
                
                <div class="p-4 bg-base-50 flex-1">
                    <textarea id="markdown-editor" name="content_md"></textarea>
                </div>
                
                <div class="p-4 border-t border-base-200 bg-base-100 flex justify-between items-center z-10">
                    <a href="{{ url_for('book_index') }}" class="btn btn-ghost text-stone-500">取消</a>
                    <button type="submit" class="btn btn-primary px-8 gap-2 shadow-md shadow-primary/20">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-4 4m0 0l-4-4m4 4V4" /></svg>
                        保存笔记
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src="{{ url_for('static', filename='js/vendor/polyfill.min.js') }}"></script>
<script id="MathJax-script" async src="{{ url_for('static', filename='js/vendor/tex-mml-chtml.js') }}"></script>
<script src="{{ url_for('static', filename='js/vendor/highlight.min.js') }}"></script>
<script src="{{ url_for('static', filename='js/vendor/easymde.min.js') }}"></script>

<script>
    document.addEventListener('DOMContentLoaded', () => {
        hljs.highlightAll();
    });

    const easyMDE = new EasyMDE({
        element: document.getElementById('markdown-editor'),
        
        // 核心配置：允许分屏，禁止全屏分屏(使用嵌入式)
        sideBySideFullscreen: false, 
        syncSideBySidePreviewScroll: true,
        status: ["lines", "words", "cursor"], // 显示底部状态栏
        
        // 工具栏 (与 Wiki 保持一致，去除了 table)
        toolbar: [
            "bold", "italic", "strikethrough", "heading", "|", 
            "quote", "unordered-list", "ordered-list", "|", 
            "link", "image", "upload-image", "code", "|",  
            "preview", "side-by-side", "fullscreen", "|",
            "guide"
        ],

        // 图片上传配置
        uploadImage: true,
        imageUploadEndpoint: "{{ url_for('upload_file') }}",
        imagePathAbsolute: true,
        imageCSRFToken: "", 
        imageMaxSize: 1024 * 1024 * 16,
        imageAccept: "image/png, image/jpeg, image/gif, image/webp",
        imageTexts: {
            sbInit: "上传图片",
            sbOnDragEnter: "松开上传",
            sbOnDragLeave: "取消",
            sbProgress: "上传中...",
            sbOnUploaded: "成功",
            sizeUnits: "b,kb,mb"
        },
        errorCallback: (msg) => alert("上传失败: " + msg),

        // 渲染预览 (MathJax + Highlight)
        previewRender: function(plainText) {
            const preview = document.getElementsByClassName("editor-preview-side")[0];
            preview.innerHTML = this.parent.markdown(plainText);
            preview.querySelectorAll('pre code').forEach((block) => hljs.highlightElement(block));
            if (typeof MathJax !== 'undefined') MathJax.typesetPromise([preview]);
            return preview.innerHTML;
        },
    });

    // 自动开启分屏
    setTimeout(function() {
        if (!easyMDE.isSideBySideActive()) {
            easyMDE.toggleSideBySide();
        }
        // 强制刷新
        if(easyMDE.codemirror) easyMDE.codemirror.refresh();
    }, 200);
</script>
{% endblock %}
```

## 📄 book/received.html

```html
{% extends "base.html" %}

{% block title %}收到笔记{% endblock %}

{% block content %}
<div class="flex justify-between items-center mb-8">
    <div>
        <h1 class="text-3xl font-bold text-base-content tracking-tight">收到笔记</h1>
        <p class="text-base-content/60 mt-2">查看其他用户分享给您的笔记</p>
    </div>
</div>

<div class="space-y-4">
    {% if note_shares %}
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {% for share in note_shares %}
            {% set note = share.note %}
            <div class="card bg-base-100 shadow-sm hover:shadow-md transition-all border border-base-200 group">
                <div class="card-body p-5">
                    <div class="flex items-center gap-3 mb-2">
                        <div class="avatar placeholder">
                            <div class="bg-neutral-focus text-neutral-content rounded-full w-6 h-6">
                                <span class="text-xs">{{ note.user.username[0] | upper }}</span>
                            </div>
                        </div>
                        <span class="text-xs font-bold text-base-content/60">{{ note.user.username }} 分享</span>
                        <span class="text-[10px] text-base-content/40 ml-auto">{{ note.updated_at.strftime('%Y-%m-%d') }}</span>
                    </div>
                    <a href="{{ url_for('view_note', note_id=note.id) }}" class="block">
                        <h3 class="card-title text-lg group-hover:text-primary transition-colors">{{ note.title }}</h3>
                        <p class="text-sm text-base-content/60 line-clamp-2 mt-2">
                            {{ note.content_md | striptags }}
                        </p>
                    </a>
                    <div class="flex gap-2 mt-4">
                        <button onclick="delete_share({{ share.id }})" class="btn btn-sm btn-ghost btn-error">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                            删除
                        </button>
                        <button onclick="convert_note({{ share.id }}, '{{ note.title }}', '{{ note.user.username }}')" class="btn btn-sm btn-ghost btn-primary">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                            </svg>
                            转换为自己的笔记
                        </button>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    {% else %}
        <div class="text-center py-12 bg-base-100 rounded-xl border border-base-200 border-dashed">
            <p class="text-base-content/40">暂时没有收到分享的笔记</p>
        </div>
    {% endif %}
</div>

<script>
function delete_share(shareId) {
    if (confirm('确定要删除这条分享记录吗？')) {
        fetch(`/book/share/${shareId}/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('删除失败: ' + (data.error || '未知错误'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('请求发生错误');
        });
    }
}

function convert_note(shareId, noteTitle, senderName) {
    if (confirm(`确定要将笔记"${noteTitle}"转换为自己的笔记吗？\n新的笔记标题将包含发送人姓名。`)) {
        fetch(`/book/share/${shareId}/convert`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('转换成功！');
                location.reload();
            } else {
                alert('转换失败: ' + (data.error || '未知错误'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('请求发生错误');
        });
    }
}
</script>
{% endblock %}
```

## 📄 book/calendar.html

```html
{% extends "base.html" %}

{% block title %}日历视图{% endblock %}

{% block extra_css %}
<script src="{{ url_for('static', filename='js/fullcalendar.min.js') }}"></script>
<style>
    /* FullCalendar Customization */
    :root {
        --fc-border-color: #e5e7eb;
        --fc-button-bg-color: white;
        --fc-button-border-color: #e5e7eb;
        --fc-button-text-color: #374151;
        --fc-button-hover-bg-color: #f3f4f6;
        --fc-button-hover-border-color: #d1d5db;
        --fc-button-active-bg-color: #e5e7eb;
        --fc-button-active-border-color: #d1d5db;
        --fc-event-bg-color: #4f46e5;
        --fc-event-border-color: #4f46e5;
        --fc-today-bg-color: #f0fdf4;
    }

    .fc {
        font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, sans-serif;
    }

    .fc-toolbar-title {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: #1f2937;
    }
    
    .fc-toolbar {
        margin-bottom: 0.5rem !important;
    }
    
    .fc-button {
        padding: 0.2rem 0.5rem !important;
        font-size: 0.85rem !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        font-weight: 500 !important;
        text-transform: capitalize;
        transition: all 0.2s !important;
    }

    .fc-button:focus {
        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2) !important;
    }
    
    .fc-daygrid-day-frame {
        min-height: 80px !important; /* Reduce min height */
    }

    .fc-daygrid-day {
        transition: background-color 0.2s;
    }

    .fc-daygrid-day:hover {
        background-color: #f9fafb;
    }

    .fc-event {
        cursor: pointer;
        border-radius: 4px;
        padding: 2px 4px;
        font-size: 0.85rem;
        transition: transform 0.1s, box-shadow 0.1s;
    }

    .fc-event:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    /* Snapshot Modal Animation */
    @keyframes modal-pop {
        0% { transform: scale(0.9); opacity: 0; }
        100% { transform: scale(1); opacity: 1; }
    }
    
    .modal-box.animate-pop {
        animation: modal-pop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    
    /* Timeline styles */
    .timeline-container {
        position: relative;
        padding-left: 2rem;
    }
    .timeline-line {
        position: absolute;
        left: 0.5rem;
        top: 0;
        bottom: 0;
        width: 2px;
        background: #e5e7eb;
    }
    .timeline-item {
        position: relative;
        margin-bottom: 2rem;
    }
    .timeline-dot {
        position: absolute;
        left: -1.85rem;
        top: 0.25rem;
        width: 1rem;
        height: 1rem;
        border-radius: 50%;
        background: #4f46e5;
        border: 2px solid white;
        box-shadow: 0 0 0 2px #e0e7ff;
    }
</style>
{% endblock %}

{% block content %}
<div class="flex flex-col gap-6">
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
            <h1 class="text-3xl font-bold text-base-content tracking-tight">日历时光机</h1>
            <p class="text-base-content/60 mt-2">点击日期快速创建笔记，或筛选查看特定主题</p>
        </div>
        
        <!-- Tag Filter -->
        <div class="form-control w-full md:w-auto">
            <div class="input-group">
                <select id="tag-filter" class="select select-bordered w-full md:w-48">
                    <option value="">所有标签</option>
                    <!-- Tags will be populated via JS -->
                </select>
            </div>
        </div>
    </div>

    <!-- Calendar View -->
    <div id="calendar-view" class="card bg-base-100 shadow-xl border border-base-200">
        <div class="card-body p-6">
            <div id='calendar'></div>
        </div>
    </div>
</div>

<!-- Note Snapshot Modal -->
<dialog id="note_snapshot_modal" class="modal">
    <div class="modal-box w-11/12 max-w-2xl bg-white/90 backdrop-blur-md border border-white/20 shadow-2xl animate-pop">
        <form method="dialog">
            <button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">✕</button>
        </form>
        <div id="snapshot-content">
            <!-- Content injected via JS -->
            <div class="h-48 bg-gray-100 rounded-lg animate-pulse mb-4"></div>
            <div class="h-4 bg-gray-100 rounded animate-pulse w-3/4 mb-2"></div>
            <div class="h-4 bg-gray-100 rounded animate-pulse w-1/2"></div>
        </div>
        <div class="modal-action">
            <a id="view-full-note" href="#" class="btn btn-primary btn-sm">查看完整笔记</a>
        </div>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>

<!-- Quick Create Modal -->
<dialog id="quick_create_modal" class="modal">
    <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">新建笔记</h3>
        <p class="text-sm text-base-content/60 mb-4">创建于: <span id="create-date-display" class="font-mono font-bold"></span></p>
        
        <form id="quick-create-form" method="dialog">
            <input type="hidden" id="create-date-input">
            <div class="form-control w-full mb-4">
                <label class="label">
                    <span class="label-text">笔记标题</span>
                </label>
                <input type="text" id="new-note-title" class="input input-bordered w-full" placeholder="例如：今日学习总结" />
            </div>
            
            <div class="form-control w-full mb-6">
                <label class="label">
                    <span class="label-text">内容摘要</span>
                </label>
                <textarea id="new-note-content" class="textarea textarea-bordered h-24" placeholder="写点什么..."></textarea>
            </div>
            
            <div class="modal-action">
                <button class="btn btn-ghost">取消</button>
                <button type="button" class="btn btn-primary" onclick="submitQuickNote()">创建笔记</button>
            </div>
        </form>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>

{% endblock %}

{% block scripts %}
<script>
    let calendar;
    let allEvents = [];
    
    // Tag colors mapping - Low Saturation (Pastel-like)
    const tagColors = [
        '#fca5a5', // Red 300
        '#fdba74', // Orange 300
        '#fcd34d', // Amber 300
        '#bef264', // Lime 300
        '#6ee7b7', // Emerald 300
        '#67e8f9', // Cyan 300
        '#93c5fd', // Blue 300
        '#a5b4fc', // Indigo 300
        '#c4b5fd', // Violet 300
        '#f0abfc', // Fuchsia 300
        '#fda4af'  // Rose 300
    ];
    // Text color for better contrast on pastel backgrounds
    const tagTextColors = '#1f2937'; // Gray 800
    const tagColorMap = new Map();

    document.addEventListener('DOMContentLoaded', function() {
        const calendarEl = document.getElementById('calendar');
        const tagFilter = document.getElementById('tag-filter');
        
        calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            locale: 'zh-cn',
            height: 'auto', // Auto height
            contentHeight: 600, // Limit content height
            aspectRatio: 1.8, // Increase aspect ratio to make it shorter
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,listMonth'
            },
            buttonText: {
                today: '今天',
                month: '月视图',
                list: '列表'
            },
            events: '/api/notes/calendar',
            eventClick: function(info) {
                showSnapshot(info.event);
            },
            dateClick: function(info) {
                showQuickCreate(info.dateStr);
            },
            eventDidMount: function(info) {
                // Color coding logic
                const tags = info.event.extendedProps.tags;
                if (tags && tags.length > 0) {
                    const primaryTag = tags[0];
                    if (!tagColorMap.has(primaryTag)) {
                        // Assign a random color from palette based on hash or sequence
                        const colorIndex = tagColorMap.size % tagColors.length;
                        tagColorMap.set(primaryTag, tagColors[colorIndex]);
                    }
                    info.el.style.backgroundColor = tagColorMap.get(primaryTag);
                    info.el.style.borderColor = tagColorMap.get(primaryTag);
                    info.el.style.color = tagTextColors; // Dark text for pastel background
                }
                
                info.el.title = info.event.title;
            },
            loading: function(isLoading) {
                if (!isLoading) {
                    // Data loaded
                    // Use setTimeout to ensure getEvents returns data
                    setTimeout(() => {
                        const events = calendar.getEvents();
                        console.log('Events loaded:', events.length);
                        populateTagFilter(events);
                    }, 100);
                }
            }
        });
        
        calendar.render();
        
        // Tag Filter Logic
        tagFilter.addEventListener('change', function() {
            const selectedTag = this.value;
            const currentEvents = calendar.getEvents();
            currentEvents.forEach(e => {
                const tags = e.extendedProps.tags || [];
                let shouldShow = true;
                if (selectedTag && !tags.includes(selectedTag)) {
                    shouldShow = false;
                }
                e.setProp('display', shouldShow ? 'auto' : 'none');
            });
        });
    });

    function populateTagFilter(events) {
        const tagFilter = document.getElementById('tag-filter');
        
        // Always rebuild to ensure we have all tags
        // Save current selection
        const currentSelection = tagFilter.value;
        
        // Clear existing options except first
        while (tagFilter.options.length > 1) {
            tagFilter.remove(1);
        }
        
        const uniqueTags = new Set();
        
        events.forEach(e => {
            const tags = e.extendedProps.tags || [];
            tags.forEach(t => uniqueTags.add(t));
        });
        
        console.log('Unique tags found:', uniqueTags);
        
        if (uniqueTags.size === 0) {
            // Optional: add a disabled option saying "No tags found"
            return;
        }
        
        Array.from(uniqueTags).sort().forEach(tag => {
            const option = document.createElement('option');
            option.value = tag;
            option.textContent = tag;
            tagFilter.appendChild(option);
        });
        
        // Restore selection if valid
        if (currentSelection && uniqueTags.has(currentSelection)) {
            tagFilter.value = currentSelection;
        }
    }

    function showSnapshot(event) {
        const modal = document.getElementById('note_snapshot_modal');
        const contentDiv = document.getElementById('snapshot-content');
        const viewBtn = document.getElementById('view-full-note');
        const props = event.extendedProps;

        viewBtn.href = `/book/notes/${event.id}`;
        
        let tagsHtml = '';
        if (props.tags && props.tags.length > 0) {
            tagsHtml = `<div class="flex gap-2 mt-2 mb-4">
                ${props.tags.map(tag => {
                    const color = tagColorMap.get(tag) || '#374151'; // Fallback color
                    // Use style for custom color
                    return `<span class="badge badge-sm border-0 text-white" style="background-color: ${color}">${tag}</span>`;
                }).join('')}
            </div>`;
        }

        contentDiv.innerHTML = `
            <div class="text-sm text-base-content/50 mb-1">${props.created_at}</div>
            <h3 class="text-2xl font-bold mb-2">${event.title}</h3>
            ${tagsHtml}
            <div class="p-4 bg-base-200/50 rounded-lg text-base-content/80 text-sm leading-relaxed max-h-60 overflow-y-auto">
                ${props.content || '<span class="italic text-base-content/40">暂无预览内容</span>'}
            </div>
        `;

        modal.showModal();
    }
    
    function showQuickCreate(dateStr) {
        const modal = document.getElementById('quick_create_modal');
        const dateDisplay = document.getElementById('create-date-display');
        const dateInput = document.getElementById('create-date-input');
        const titleInput = document.getElementById('new-note-title');
        
        dateDisplay.textContent = dateStr;
        dateInput.value = dateStr;
        
        // Pre-fill title with date
        titleInput.value = `${dateStr} 随记`;
        
        modal.showModal();
    }
    
    function submitQuickNote() {
        const dateStr = document.getElementById('create-date-input').value;
        const title = document.getElementById('new-note-title').value;
        const content = document.getElementById('new-note-content').value;
        
        if (!title) {
            alert('请输入标题');
            return;
        }
        
        // Reuse quick create endpoint but need to support custom title and content
        // The current endpoint /book/notes/quick_create uses timestamp as title.
        // Let's create a new one or modify existing?
        // Let's use the standard new note endpoint or modify quick_create logic.
        // Actually, quick_create_note in app.py takes content and generates title.
        // Let's use /book/notes/new (POST) but it's form data and redirects.
        // Better to add a JSON endpoint or update quick_create.
        // Let's call a new endpoint logic via fetch using the existing /book/notes/quick_create 
        // BUT wait, quick_create generates its own title.
        // I should probably use the standard form submission via JS to /book/notes/new?
        // Or modify app.py to accept title in quick_create?
        
        // Plan: Submit to /book/notes/new as form data using fetch to avoid redirect page load if possible,
        // or just let it redirect.
        // But user might want to stay on calendar.
        // Let's update app.py to support title in quick_create_note.
        
        fetch('/book/notes/quick_create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: title,
                content: content
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Add event to calendar immediately
                calendar.addEvent({
                    id: data.note_id,
                    title: title,
                    start: dateStr,
                    extendedProps: {
                        content: content,
                        tags: [], // No tags for quick create yet
                        created_at: dateStr + ' ' + new Date().toTimeString().split(' ')[0].substring(0,5)
                    }
                });
                
                document.getElementById('quick_create_modal').close();
                // Clear form
                document.getElementById('new-note-title').value = '';
                document.getElementById('new-note-content').value = '';
            } else {
                alert('创建失败: ' + data.error);
            }
        })
        .catch(err => {
            console.error(err);
            alert('创建失败，请重试');
        });
    }
</script>
{% endblock %}
```

## 📄 book/edit_note.html

```html
{% extends "base.html" %}

{% block title %}编辑笔记 - {{ note.title }}{% endblock %}

{% block content %}
<style>
    /* EasyMDE Customization */
    .EasyMDEContainer {
        height: 100%;
        display: flex;
        flex-direction: column;
        border: none !important;
        background-color: transparent;
    }
    
    .editor-toolbar {
        border: none !important;
        border-bottom: 1px solid hsl(var(--b2)) !important;
        background-color: hsl(var(--b1)) !important;
        border-radius: 0 !important;
        padding: 0.5rem 1rem !important;
        opacity: 0.8;
        transition: opacity 0.2s;
    }
    
    .editor-toolbar:hover {
        opacity: 1;
    }
    
    .editor-toolbar button {
        border-radius: 0.5rem !important;
        transition: all 0.2s !important;
        color: hsl(var(--bc) / 0.6) !important;
    }
    
    .editor-toolbar button:hover, .editor-toolbar button.active {
        background-color: hsl(var(--b2)) !important;
        border-color: transparent !important;
        color: hsl(var(--p)) !important;
    }

    .CodeMirror {
        flex: 1;
        height: auto !important;
        border: none !important;
        border-radius: 0 !important;
        background-color: transparent !important;
        padding: 1rem !important;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
        color: hsl(var(--bc)) !important;
    }

    .CodeMirror-scroll {
        min-height: 100% !important;
    }

    .editor-preview {
        background-color: hsl(var(--b1)) !important;
        padding: 2rem !important;
    }

    /* Fullscreen mode fixes */
    .EasyMDEContainer.fullscreen {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        z-index: 9999 !important;
    }
</style>

<div class="max-w-5xl mx-auto">
    <div class="flex items-center gap-2 text-sm text-base-content/60 mb-6">
        <a href="{{ url_for('book_index') }}" class="hover:text-primary">我的笔记</a>
        <span>/</span>
        <a href="{{ url_for('view_note', note_id=note.id) }}" class="hover:text-primary truncate max-w-[200px]">{{ note.title }}</a>
        <span>/</span>
        <span class="text-base-content/80">编辑</span>
    </div>

    <div class="card bg-base-100 shadow-xl border border-base-200 overflow-hidden">
        <div class="card-body p-0">
            <form method="post" class="flex flex-col h-[calc(100vh-12rem)]">
                <div class="p-6 border-b border-base-200 bg-base-100 space-y-4">
                    <input type="text" name="title" value="{{ note.title }}" placeholder="输入笔记标题..." class="input input-ghost text-2xl font-bold w-full focus:bg-transparent px-0 placeholder:text-base-content/30" required />
                    <input type="text" name="tags" value="{{ note.tags | map(attribute='name') | join(', ') }}" placeholder="标签 (用逗号分隔)" class="input input-sm input-ghost w-full focus:bg-transparent px-0 placeholder:text-base-content/30" />
                    
                    <div class="form-control w-full max-w-xs">
                        <label class="label cursor-pointer justify-start gap-4 p-0">
                          <span class="label-text text-base-content/60">允许评论</span> 
                          <input type="checkbox" name="comment_enabled" class="toggle toggle-xs toggle-primary" {% if note.comment_enabled %}checked{% endif %} />
                        </label>
                    </div>
                </div>
                
                <div class="flex-1 overflow-hidden relative bg-base-100">
                    <textarea id="markdown-editor" name="content_md" class="hidden">{{ note.content_md }}</textarea>
                </div>
                
                <div class="p-4 border-t border-base-200 bg-base-100 flex justify-between items-center z-10">
                    <a href="{{ url_for('view_note', note_id=note.id) }}" class="btn btn-ghost">取消</a>
                    <button type="submit" class="btn btn-primary px-8">保存更改</button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    const easyMDE = new EasyMDE({
        element: document.getElementById('markdown-editor'),
        spellChecker: false,
        placeholder: "在此输入笔记内容...",
        status: false,
        minHeight: "100%",
        toolbar: ["bold", "italic", "heading", "|", "quote", "unordered-list", "ordered-list", "|", "link", "image", "|", "preview", "side-by-side", "fullscreen"],
    });
    // Fix for full height
    easyMDE.codemirror.setSize("100%", "100%");
</script>
{% endblock %}
```

## 📄 book/view_note.html

```html
{% extends "base.html" %}

{% block title %}{{ note.title }}{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{{ url_for('markdown_css') }}">
<style>
    .toc-link {
        display: block;
        padding: 0.25rem 0.5rem;
        font-size: 0.875rem;
        color: #57534e;
        border-left: 2px solid transparent;
        transition: all 0.2s;
    }
    .toc-link:hover {
        color: #ea580c;
        background-color: #faf7f5;
    }
    .toc-link.active {
        color: #ea580c;
        border-left-color: #ea580c;
        font-weight: 500;
    }
    .toc-h1 { margin-left: 0; }
    .toc-h2 { margin-left: 1rem; }
    .toc-h3 { margin-left: 2rem; }
</style>
{% endblock %}

{% block content %}
<div class="flex flex-col lg:flex-row gap-6">
    <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 text-sm text-base-content/60 mb-6">
            <a href="{{ url_for('book_index') }}" class="hover:text-primary">我的笔记</a>
            <span>/</span>
            <span class="text-base-content/80 truncate max-w-[300px]">{{ note.title }}</span>
        </div>

        <div class="card bg-base-100 shadow-xl border border-base-200">
            <div class="card-body p-8">
                <div class="flex items-start justify-between mb-6 pb-6 border-b border-base-200">
                    <div>
                        <h1 class="text-3xl font-bold text-base-content mb-2">{{ note.title }}</h1>
                        <div class="flex flex-wrap items-center gap-4 text-sm text-base-content/60">
                            <span class="flex items-center gap-1">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
                                {{ note.user.username }}
                            </span>
                            <span class="flex items-center gap-1">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                {{ note.updated_at.strftime('%Y-%m-%d %H:%M') }}
                            </span>
                            {% if note.tags %}
                            <span class="flex items-center gap-2">
                                {% for tag in note.tags %}
                                <span class="badge badge-sm badge-outline">{{ tag.name }}</span>
                                {% endfor %}
                            </span>
                            {% endif %}
                        </div>
                    </div>
                    
                    {% if is_owner %}
                    <div class="flex gap-2">
                        <a href="{{ url_for('edit_note', note_id=note.id) }}" class="btn btn-ghost btn-sm gap-2">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                            编辑
                        </a>
                        <button onclick="delete_modal.showModal()" class="btn btn-ghost btn-sm text-error">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                        </button>
                    </div>
                    {% endif %}
                </div>
                
                <div class="prose prose-stone max-w-none">
                    {{ html | safe }}
                </div>
            </div>
        </div>

        <!-- 评论区 -->
        {% if note.comment_enabled %}
        <div class="card bg-base-100 shadow-xl border border-base-200 mt-6">
            <div class="card-body p-8">
                <h3 class="text-lg font-bold text-base-content mb-4 flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" /></svg>
                    评论 ({{ note.comments|length }})
                </h3>
                
                <div class="space-y-6 mb-8">
                    {% for comment in note.comments %}
                    <div class="flex gap-4 group">
                        <div class="avatar placeholder">
                            <div class="bg-neutral-focus text-neutral-content rounded-full w-10 h-10">
                                <span class="text-sm">{{ comment.user.username[0] | upper }}</span>
                            </div>
                        </div>
                        <div class="flex-1">
                            <div class="flex items-center gap-2 mb-1">
                                <span class="font-bold text-sm">{{ comment.user.username }}</span>
                                <span class="text-xs text-base-content/40">{{ comment.created_at.strftime('%Y-%m-%d %H:%M') }}</span>
                                
                                {% if current_user.is_admin or current_user.id == comment.user_id or is_owner %}
                                <form action="{{ url_for('delete_comment', comment_id=comment.id) }}" method="post" class="ml-auto opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button type="submit" class="btn btn-ghost btn-xs text-error" title="删除评论" onclick="return confirm('确定要删除这条评论吗？')">
                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                                    </button>
                                </form>
                                {% endif %}
                            </div>
                            <div class="p-3 bg-base-200 rounded-lg rounded-tl-none text-sm whitespace-pre-wrap">{{ comment.content }}</div>
                        </div>
                    </div>
                    {% else %}
                    <div class="text-center py-8 text-base-content/40 italic">
                        暂无评论，快来抢沙发吧~
                    </div>
                    {% endfor %}
                </div>
                
                <form action="{{ url_for('comment_note', note_id=note.id) }}" method="post" class="flex gap-4">
                    <div class="avatar placeholder">
                        <div class="bg-primary text-primary-content rounded-full w-10 h-10">
                            <span class="text-sm">{{ current_user.username[0] | upper }}</span>
                        </div>
                    </div>
                    <div class="flex-1 flex gap-2">
                        <textarea name="content" class="textarea textarea-bordered w-full h-20 resize-none" placeholder="写下你的想法..." required></textarea>
                        <button type="submit" class="btn btn-primary h-auto">发表</button>
                    </div>
                </form>
            </div>
        </div>
        {% endif %}
    </div>

    <!-- 侧边栏：目录 + 分享信息 -->
    <div class="w-full lg:w-72 flex-shrink-0 pt-[3.25rem]">
        <div class="sticky top-6 flex flex-col gap-6 max-h-[calc(100vh-3rem)] overflow-y-auto hide-scrollbar">
            
            <!-- 笔记目录卡片 -->
            <div class="card bg-base-100 shadow-xl border border-base-200 flex-shrink-0">
                <div class="card-body p-4">
                    <h3 class="font-bold text-stone-700 mb-2 px-2 flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" /></svg>
                        笔记目录
                    </h3>
                    <nav id="toc-container" class="space-y-1 max-h-[40vh] overflow-y-auto">
                        <!-- TOC will be injected here via JS -->
                    </nav>
                </div>
            </div>

            {% if is_owner %}
            <div class="card bg-base-100 shadow-xl border border-base-200">
                <div class="card-body p-5">
                    <h3 class="card-title text-sm uppercase tracking-wide text-base-content/50 mb-4">分享设置</h3>
                    
                    {% if note.shares %}
                    <div class="mb-4">
                        <div class="text-xs font-bold mb-2">已分享给：</div>
                        <div class="flex flex-wrap gap-2">
                            {% for share in note.shares %}
                            <div class="badge badge-ghost gap-1 pl-1 pr-2">
                                <div class="w-4 h-4 rounded-full bg-neutral-focus text-neutral-content flex items-center justify-center text-[10px]">{{ share.user.username[0]|upper }}</div>
                                {{ share.user.username }}
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endif %}

                    <button onclick="share_modal.showModal()" class="btn btn-outline btn-primary btn-sm w-full gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" /></svg>
                        分享笔记
                    </button>
                </div>
            </div>
            {% endif %}
        </div>
    </div>
</div>

<!-- 删除确认弹窗 -->
<dialog id="delete_modal" class="modal">
    <div class="modal-box">
        <h3 class="font-bold text-lg">确认删除</h3>
        <p class="py-4">确定要删除这篇笔记吗？此操作无法撤销。</p>
        <div class="modal-action">
            <form action="{{ url_for('delete_note', note_id=note.id) }}" method="post">
                <button type="submit" class="btn btn-error">确认删除</button>
            </form>
            <form method="dialog">
                <button class="btn">取消</button>
            </form>
        </div>
    </div>
</dialog>

<!-- 分享弹窗 -->
<dialog id="share_modal" class="modal">
    <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">分享笔记</h3>
        <p class="text-sm text-base-content/60 mb-4">选择要分享的用户（可多选）</p>
        
        <form action="{{ url_for('share_note', note_id=note.id) }}" method="post">
            <div class="max-h-60 overflow-y-auto border border-base-200 rounded-lg divide-y divide-base-200 mb-6">
                {% for user in all_users %}
                <label class="label cursor-pointer px-4 hover:bg-base-100">
                    <span class="label-text flex items-center gap-2">
                        <div class="avatar placeholder">
                            <div class="bg-neutral-focus text-neutral-content rounded-full w-6 h-6">
                                <span class="text-xs">{{ user.username[0] | upper }}</span>
                            </div>
                        </div>
                        {{ user.username }}
                        {% if user.is_admin %}
                        <span class="badge badge-xs badge-ghost">管理员</span>
                        {% endif %}
                    </span> 
                    <input type="checkbox" name="user_ids" value="{{ user.id }}" class="checkbox checkbox-primary checkbox-sm" />
                </label>
                {% endfor %}
            </div>
            
            <div class="modal-action">
                <button type="submit" class="btn btn-primary">确认分享</button>
                <form method="dialog">
                    <button class="btn" type="button" onclick="share_modal.close()">取消</button>
                </form>
            </div>
        </form>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>
{% endblock %}

{% block scripts %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Code block copy button
    document.querySelectorAll('pre code').forEach((block) => {
        // Highlight.js might have already processed the block, so we target the pre
        const pre = block.parentNode;
        
        // Create wrapper
        const wrapper = document.createElement('div');
        wrapper.className = 'relative group';
        pre.parentNode.insertBefore(wrapper, pre);
        wrapper.appendChild(pre);
        
        // Create button
        const button = document.createElement('button');
        button.className = 'absolute top-2 right-2 p-1.5 rounded-lg bg-white/10 text-white/70 hover:bg-white/20 hover:text-white transition-all opacity-0 group-hover:opacity-100 focus:opacity-100';
        button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>';
        button.title = '复制';
        
        // Copy functionality
        button.addEventListener('click', async () => {
            const code = block.textContent; // Get raw code
            try {
                await navigator.clipboard.writeText(code);
                const originalIcon = button.innerHTML;
                button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>';
                setTimeout(() => {
                    button.innerHTML = originalIcon;
                }, 2000);
            } catch (err) {
                console.error('Failed to copy!', err);
            }
        });
        
        wrapper.appendChild(button);
    });

    // Table of Contents
    const content = document.querySelector('.prose');
    const tocContainer = document.getElementById('toc-container');
    
    if (content && tocContainer) {
        const headers = content.querySelectorAll('h1, h2, h3');
        
        if (headers.length === 0) {
            tocContainer.innerHTML = '<p class="px-2 text-xs text-stone-400 italic">暂无目录</p>';
        } else {
            headers.forEach((header, index) => {
                // Add ID to header if not present
                if (!header.id) {
                    header.id = 'heading-' + index;
                }

                const link = document.createElement('a');
                link.href = '#' + header.id;
                link.textContent = header.textContent;
                link.className = 'toc-link toc-' + header.tagName.toLowerCase();
                
                // Smooth scroll
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    header.scrollIntoView({ behavior: 'smooth' });
                    // Update active state
                    document.querySelectorAll('.toc-link').forEach(l => l.classList.remove('active'));
                    link.classList.add('active');
                });

                tocContainer.appendChild(link);
            });

            // Scroll spy
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const id = entry.target.id;
                        document.querySelectorAll('.toc-link').forEach(link => {
                            if (link.getAttribute('href') === '#' + id) {
                                link.classList.add('active');
                            } else {
                                link.classList.remove('active');
                            }
                        });
                    }
                });
            }, { rootMargin: '-100px 0px -66%' });

            headers.forEach(header => observer.observe(header));
        }
    }
});
</script>
{% endblock %}
```

## 📄 partials/notes_heatmap.html

```html
<div class="w-full">
  <div class="flex justify-between items-center mb-3">
    <h3 class="text-base font-bold">学习活跃度</h3>
    <select id="heatmap-year-select" class="select select-xs select-bordered w-24 hidden">
      <!-- 由脚本填充年份 -->
    </select>
  </div>
  <div id="heatmap-container" class="flex flex-wrap gap-[1px] justify-start">
    <!-- 月度热力图容器由脚本注入 -->
  </div>
</div>
```

## 📄 user/achievement_book.html

```html
{% extends "base.html" %}

{% block title %}{{ user.username }} 的成就册{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    /* --- 1. 全局与基础样式 --- */
    :root {
        --primary-warm: #f59e0b;
        --bg-warm: #fffbeb;
    }
    
    .hide-scrollbar::-webkit-scrollbar { display: none; }
    .hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }

    /* 动画 */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .animate-card {
        animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    /* --- 2. 列表页卡片样式 --- */
    .badge-card {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        transform-style: preserve-3d;
        cursor: pointer;
        background: #ffffff;
        border-radius: 1rem;
        overflow: hidden;
    }
    
    /* 已获得 */
    .badge-card.unlocked {
        border: 1px solid #fcd34d; /* 默认金边，会被稀有度样式覆盖 */
        box-shadow: 0 4px 6px -1px rgba(245, 158, 11, 0.1), 0 2px 4px -1px rgba(245, 158, 11, 0.06);
    }
    .badge-card.unlocked:hover {
        transform: translateY(-6px) scale(1.02);
        box-shadow: 0 20px 25px -5px rgba(245, 158, 11, 0.2);
    }
    
    /* 未获得 */
    .badge-card.locked {
        filter: grayscale(100%);
        opacity: 0.8;
        background-color: #fafaf9;
        border: 1px dashed #d6d3d1;
    }
    .badge-card.locked:hover {
        opacity: 1;
        transform: translateY(-2px);
        background-color: #fff;
    }

    .card-body { padding: 1.25rem; display: flex; flex-direction: column; align-items: center; text-align: center; height: 100%; }

    /* --- 3. 弹窗 3D 卡片样式 --- */
    #badge-modal .modal-box {
        background: transparent;
        box-shadow: none;
        overflow: visible;
        max-width: 420px;
        perspective: 1000px;
        padding: 0;
    }

    .collectible-card {
        position: relative;
        width: 100%;
        background: #fff;
        border-radius: 24px;
        transform-style: preserve-3d;
        transition: transform 0.1s ease-out;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    }
    
    .modal[open] .collectible-card {
        animation: cardPop 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
    }
    @keyframes cardPop {
        0% { opacity: 0; transform: scale(0.5) translateY(50px) rotateX(10deg); }
        100% { opacity: 1; transform: scale(1) translateY(0) rotateX(0); }
    }

    .holo-shine {
        position: absolute; inset: 0;
        background: linear-gradient(135deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.4) 50%, rgba(255,255,255,0) 100%);
        opacity: 0; pointer-events: none; z-index: 50; transition: opacity 0.2s;
    }

    .card-pattern-bg {
        background-color: #fffbeb;
        background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23f59e0b' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
    }

    .circular-chart { display: block; margin: 0 auto; max-width: 100%; max-height: 250px; }
    .circle-bg { fill: none; stroke: #fed7aa; stroke-width: 3.8; } 
    .circle { fill: none; stroke-width: 2.8; stroke-linecap: round; animation: progress 1s ease-out forwards; }
    @keyframes progress { 0% { stroke-dasharray: 0 100; } }

    /* --- 4. 优化后的稀有度视觉效果 (流光溢彩) --- */
    
    /* 流光动画定义 */
    @keyframes gradient-flow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* 基础标签样式 */
    .badge-tag {
        display: inline-block; padding: 3px 8px; border-radius: 6px; 
        font-size: 10px; font-weight: 900; letter-spacing: 0.05em;
        text-transform: uppercase; color: #fff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        background-size: 200% 200%;
        animation: gradient-flow 4s ease infinite;
        text-shadow: 0 1px 1px rgba(0,0,0,0.1);
    }

    /* 1. 普通 (Common) - 银灰极光 */
    .rarity-common .badge-tag {
        background-image: linear-gradient(135deg, #94a3b8, #cbd5e1, #64748b);
    }
    .badge-card.rarity-common.unlocked { border: 1px solid #cbd5e1; }

    /* 2. 稀有 (Rare) - 深海冰蓝 */
    .rarity-rare .badge-tag {
        background-image: linear-gradient(135deg, #3b82f6, #60a5fa, #2563eb);
    }
    .badge-card.rarity-rare.unlocked { border: 1px solid #93c5fd; box-shadow: 0 4px 10px rgba(59, 130, 246, 0.15); }

    /* 3. 史诗 (Epic) - 霓虹紫韵 */
    .rarity-epic .badge-tag {
        background-image: linear-gradient(135deg, #a855f7, #d946ef, #7e22ce);
    }
    .badge-card.rarity-epic.unlocked { border: 1px solid #d8b4fe; box-shadow: 0 4px 10px rgba(168, 85, 247, 0.15); }

    /* 4. 传说 (Legendary) - 烈焰流金 */
    .rarity-legendary .badge-tag {
        background-image: linear-gradient(135deg, #f59e0b, #fbbf24, #d97706, #f59e0b);
        animation: gradient-flow 3s linear infinite; /* 传说级流动更快 */
    }
    .badge-card.rarity-legendary.unlocked { 
        border: 1px solid #fcd34d; 
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.25); 
    }

    /* 按钮加载状态优化 */
    .btn-generating {
        position: relative;
        pointer-events: none;
        overflow: hidden;
        background-image: linear-gradient(45deg, #f59e0b, #fbbf24, #f59e0b);
        background-size: 200% 200%;
        animation: gradient-flow 2s linear infinite;
        border: none;
        color: white !important;
    }
</style>
<script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
{% endblock %}

{% block content %}
<div id="achievement-book-container" class="max-w-[1400px] mx-auto px-4 sm:px-6 py-8 min-h-screen bg-[#fdfcf8]">
    
    <div class="bg-white rounded-3xl shadow-sm border border-orange-100 p-6 md:p-8 mb-10 relative overflow-hidden">
        <div class="absolute top-0 right-0 w-80 h-80 bg-orange-100 rounded-full blur-3xl opacity-60 -mr-20 -mt-20 pointer-events-none"></div>
        <div class="absolute bottom-0 left-0 w-64 h-64 bg-amber-100 rounded-full blur-3xl opacity-60 -ml-16 -mb-16 pointer-events-none"></div>

        <div class="relative z-10 flex flex-col md:flex-row items-center justify-between gap-8">
            <div class="flex items-start gap-5 w-full md:w-auto">
                <a href="{{ url_for('public_profile', user_id=user.id) }}" class="btn btn-circle btn-ghost bg-stone-50 hover:bg-orange-50 text-stone-500 hover:text-orange-600 transition-all">
                    <i class="fas fa-arrow-left"></i>
                </a>
                <div>
                    <h1 class="text-3xl md:text-4xl font-black text-stone-800 tracking-tight flex items-center gap-3">
                        <span class="text-transparent bg-clip-text bg-gradient-to-r from-amber-600 to-orange-500">成就图鉴</span>
                        <span class="text-xs bg-orange-100 text-orange-700 px-2.5 py-1 rounded-full font-bold align-top mt-1 border border-orange-200" id="total-badge-count">0</span>
                    </h1>
                    <p class="text-stone-500 mt-2 text-sm md:text-base max-w-lg font-medium">
                        每一枚徽章都是一段闪光的旅程。继续探索，点亮你的荣誉墙。
                    </p>
                </div>
            </div>

            <div class="flex items-center gap-6 bg-white/60 backdrop-blur-md p-3 pr-6 rounded-2xl border border-orange-100 shadow-sm">
                <div class="relative w-16 h-16">
                    <svg viewBox="0 0 36 36" class="circular-chart text-amber-500">
                        <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                        <path class="circle" stroke-dasharray="0, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" id="progress-circle" stroke="currentColor" />
                    </svg>
                    <div class="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-amber-600">
                        <span id="completion-rate">0%</span>
                    </div>
                </div>
                <div>
                    <div class="text-[10px] text-stone-400 uppercase font-bold tracking-wider mb-0.5">收集进度</div>
                    <div class="text-xl font-black text-stone-800">
                        <span id="unlocked-count" class="text-amber-600">0</span>
                        <span class="text-stone-300 text-lg mx-0.5">/</span>
                        <span id="total-count" class="text-stone-400 text-lg">0</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="sticky top-20 z-30 bg-[#fdfcf8]/90 backdrop-blur-md py-2 -mx-4 px-4 md:mx-0 md:px-0 mb-6 rounded-xl md:bg-transparent md:backdrop-blur-none md:static">
        <div class="flex justify-start md:justify-center overflow-x-auto hide-scrollbar">
            <div class="bg-white p-1.5 rounded-2xl shadow-sm border border-stone-100 flex gap-1" id="category-tabs"></div>
        </div>
    </div>

    <div id="achievements-grid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pb-20">
    </div>
    
    <div id="empty-state" class="hidden flex-col items-center justify-center py-20 text-center">
        <div class="w-24 h-24 bg-orange-50 rounded-full flex items-center justify-center mb-4 text-orange-200 text-4xl border border-orange-100">
            <i class="fas fa-trophy"></i>
        </div>
        <h3 class="text-lg font-bold text-stone-600">暂无相关成就</h3>
    </div>
</div>

<dialog id="badge-modal" class="modal modal-bottom sm:modal-middle backdrop-blur-sm">
    <div class="modal-box bg-transparent shadow-none overflow-visible p-0 w-auto max-w-lg">
        <form method="dialog">
            <button class="btn btn-sm btn-circle btn-ghost absolute -right-2 -top-10 md:-right-12 md:top-0 text-white/80 hover:text-white hover:bg-white/20 z-50 text-lg">✕</button>
        </form>

        <div class="collectible-card" id="card-3d-container">
            <div class="holo-shine" id="holo-layer"></div>

            <div class="relative h-48 card-pattern-bg flex flex-col items-center justify-center overflow-hidden border-b border-orange-50">
                <div class="absolute inset-0 bg-gradient-to-b from-transparent to-white/60"></div>
                <div id="modal-status-badge" class="absolute top-4 right-4 z-20"></div>
                
                <div class="absolute top-4 left-4 z-20">
                    <span id="modal-rarity-tag" class="badge-tag"></span>
                </div>

                <div class="relative z-10 w-32 h-32 transform transition-transform duration-500">
                    <div class="absolute inset-0 bg-orange-400/20 blur-2xl rounded-full scale-75" id="icon-glow"></div>
                    <div id="modal-icon-container" class="w-full h-full flex items-center justify-center drop-shadow-2xl"></div>
                </div>
            </div>

            <div class="p-6 bg-white relative z-10">
                <div class="text-center mb-6">
                    <h3 class="font-900 text-3xl text-stone-800 tracking-tight mb-2" id="modal-title"></h3>
                    <div class="h-1 w-12 bg-orange-400 mx-auto rounded-full mb-3"></div>
                    <p class="text-[10px] text-stone-400 uppercase tracking-wider font-bold mb-2" id="modal-rarity-text"></p>
                    <p class="text-stone-500 text-sm leading-relaxed px-2 font-medium" id="modal-desc"></p>
                </div>

                <div class="grid grid-cols-2 gap-3 mb-4">
                    <div class="bg-stone-50 rounded-xl p-3 border border-stone-100 flex flex-col items-center justify-center text-center">
                        <span class="text-[10px] text-stone-400 font-bold uppercase mb-1">解锁条件</span>
                        <span class="text-xs font-bold text-stone-700" id="modal-condition"></span>
                    </div>
                    <div class="bg-orange-50 rounded-xl p-3 border border-orange-100 flex flex-col items-center justify-center text-center">
                        <span class="text-[10px] text-orange-400 font-bold uppercase mb-1">获得奖励</span>
                        <span class="text-xs font-bold text-orange-700" id="modal-sticker-count"></span>
                    </div>
                </div>

                <div id="modal-date-container" class="text-center pt-2 border-t border-stone-100 hidden">
                    <p class="text-[10px] text-stone-400 uppercase tracking-wide font-bold">
                        解锁于 <span id="modal-date" class="text-orange-500 ml-1"></span>
                    </p>
                </div>
                
                <div id="modal-share-container" class="hidden"></div>
            </div>
        </div>
        
        <p class="text-center text-white/50 text-xs mt-4 font-medium tracking-wider">
            <i class="fas fa-mouse-pointer mr-1"></i> 移动鼠标欣赏卡片细节
        </p>
    </div>
    
    <form method="dialog" class="modal-backdrop bg-stone-900/60 backdrop-blur-sm">
        <button>close</button>
    </form>
</dialog>

<script>
    // --- 稀有度中英文映射 ---
    const RARITY_MAP = {
        'common': '普通',
        'rare': '稀有',
        'epic': '史诗',
        'legendary': '传说'
    };

    // --- 数据注入 ---
    const TOTAL_USERS = {{ total_users }};
    const SERVER_DATA = {
        categories: [
            { id: 'all', name: '全部' },
            {% for cat in categories %}
            { id: '{{ cat }}', name: '{{ cat }}' }{{ "," if not loop.last }}
            {% endfor %}
        ],
        achievements: [
            // 已获得
            {% for ub in user_badges %}
            {
                "id": {{ ub.badge.id }}, "name": "{{ ub.badge.name }}",
                "description": "{{ ub.badge.description|replace('"', '\\"') }}",
                "category": "{{ ub.badge.category or '一般' }}",
                "rarity": "{{ ub.badge.rarity or 'common' }}",
                "isSecret": {{ 'true' if ub.badge.is_secret else 'false' }},
                "issuedCount": {{ ub.badge.issued_count }},
                "condition": "{{ ub.badge|badge_condition_text }}",
                "isUnlocked": true, "unlockDate": "{{ ub.earned_at.strftime('%Y-%m-%d') }}",
                "stickerCount": {{ ub.badge.sticker_count or 1 }}, 
                "isImage": {{ 'true' if ub.badge.icon|is_image_icon else 'false' }},
                "iconUrl": "{{ ub.badge.icon|badge_icon_url }}",
                "iconText": "{{ ub.badge.icon if not ub.badge.icon|is_image_icon else '' }}"
            },
            {% endfor %}
            // 未获得
            {% for b in unearned_badges %}
            {
                "id": {{ b.id }}, "name": "{{ b.name }}",
                "description": "{{ b.description|replace('"', '\\"') }}",
                "category": "{{ b.category or '一般' }}",
                "rarity": "{{ b.rarity or 'common' }}",
                "isSecret": {{ 'true' if b.is_secret else 'false' }},
                "issuedCount": {{ b.issued_count }},
                "condition": "{{ b|badge_condition_text }}",
                "isUnlocked": false, "unlockDate": null,
                "stickerCount": {{ b.sticker_count or 1 }},
                "isImage": {{ 'true' if b.icon|is_image_icon else 'false' }},
                "iconUrl": "{{ b.icon|badge_icon_url }}",
                "iconText": "{{ b.icon if not b.icon|is_image_icon else '' }}"
            }{{ "," if not loop.last }}
            {% endfor %}
        ]
    };

    document.addEventListener('DOMContentLoaded', () => {
        const grid = document.getElementById('achievements-grid');
        const tabsContainer = document.getElementById('category-tabs');
        const emptyState = document.getElementById('empty-state');
        const modal = document.getElementById('badge-modal');
        
        // 3D 交互逻辑 (保持不变)
        const cardContainer = document.getElementById('card-3d-container');
        const holoLayer = document.getElementById('holo-layer');
        let isHovering = false;

        cardContainer.addEventListener('mouseenter', () => { isHovering = true; });
        cardContainer.addEventListener('mouseleave', () => {
            isHovering = false;
            cardContainer.style.transform = `rotateX(0deg) rotateY(0deg)`;
            holoLayer.style.opacity = '0';
        });

        cardContainer.addEventListener('mousemove', (e) => {
            if (!isHovering) return;
            const rect = cardContainer.getBoundingClientRect();
            const x = e.clientX - rect.left; 
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const percentX = (x - centerX) / centerX;
            const percentY = (y - centerY) / centerY;
            const rotateX = percentY * -10; 
            const rotateY = percentX * 10;
            cardContainer.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
            if(cardContainer.classList.contains('is-unlocked')) {
                holoLayer.style.opacity = '1';
                holoLayer.style.transform = `translate(${percentX * 40}px, ${percentY * 40}px)`;
            }
        });

        initStats();
        renderTabs();
        renderGrid('all');

        function initStats() {
            const total = SERVER_DATA.achievements.length;
            const unlocked = SERVER_DATA.achievements.filter(a => a.isUnlocked).length;
            const rate = total === 0 ? 0 : Math.round((unlocked / total) * 100);
            document.getElementById('total-badge-count').innerText = total;
            document.getElementById('unlocked-count').innerText = unlocked;
            document.getElementById('total-count').innerText = total;
            document.getElementById('completion-rate').innerText = `${rate}%`;
            setTimeout(() => {
                document.getElementById('progress-circle').setAttribute('stroke-dasharray', `${rate}, 100`);
            }, 100);
        }

        function renderTabs() {
            tabsContainer.innerHTML = SERVER_DATA.categories.map(cat => `
                <button onclick="filterAchievements('${cat.id}')" 
                    class="px-4 py-2 rounded-xl text-sm font-bold transition-all duration-300 tab-btn ${cat.id === 'all' ? 'bg-amber-500 text-white shadow-md shadow-orange-200' : 'text-stone-500 hover:bg-stone-50 hover:text-stone-800'}" 
                    data-id="${cat.id}">${cat.name}</button>
            `).join('');
        }

        window.filterAchievements = function(categoryId) {
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.className = btn.dataset.id === categoryId 
                    ? 'px-4 py-2 rounded-xl text-sm font-bold transition-all duration-300 tab-btn bg-amber-500 text-white shadow-md shadow-orange-200 transform scale-105'
                    : 'px-4 py-2 rounded-xl text-sm font-bold transition-all duration-300 tab-btn text-stone-500 hover:bg-stone-50 hover:text-stone-800';
            });
            renderGrid(categoryId);
        };

window.openBadgeDetail = function(id) {
    const item = SERVER_DATA.achievements.find(a => a.id === id);
    if (!item) return;

    // --- 辅助函数：安全设置文本 ---
    function setSafeText(id, text) {
        const el = document.getElementById(id);
        if (el) el.innerText = text;
        else console.warn(`找不到 ID: ${id}`);
    }
    
    // --- 辅助函数：安全设置HTML ---
    function setSafeHtml(id, html) {
        const el = document.getElementById(id);
        if (el) el.innerHTML = html;
    }

    const isSecretLocked = !item.isUnlocked && item.isSecret;
    
    // 1. 填充基础信息
    setSafeText('modal-title', isSecretLocked ? "???" : item.name);
    setSafeText('modal-category', item.category);
    setSafeText('modal-desc', isSecretLocked ? "继续探索以揭示此成就" : (item.description || '暂无描述'));
    setSafeText('modal-condition', isSecretLocked ? "???" : item.condition);
    setSafeText('modal-sticker-count', `+${item.stickerCount} 贴纸`);

    // 2. 填充稀有度和持有率 (这里是你报错的地方)
    // 确保 TOTAL_USERS 有值，防止除以0
    const safeTotalUsers = (typeof TOTAL_USERS !== 'undefined' && TOTAL_USERS > 0) ? TOTAL_USERS : 1;
    const percentage = ((item.issuedCount / safeTotalUsers) * 100).toFixed(1);
    
    setSafeText('modal-rarity-text', `全站仅有 ${percentage}% 的用户拥有此徽章`);
    
    const cnRarity = RARITY_MAP[item.rarity] || '普通';
    setSafeText('modal-rarity-tag', cnRarity);

    // 3. 填充图标
    const iconContainer = document.getElementById('modal-icon-container');
    if (iconContainer) {
        if (isSecretLocked) {
             iconContainer.innerHTML = `<span class="text-7xl drop-shadow-md">❓</span>`;
        } else if (item.isImage) {
            iconContainer.innerHTML = `<img src="${item.iconUrl}" class="w-24 h-24 object-contain drop-shadow-xl" crossOrigin="anonymous">`;
        } else {
            iconContainer.innerHTML = `<span class="text-7xl drop-shadow-md">${item.iconText}</span>`;
        }
    }

    // 4. 样式处理
    const card3d = document.getElementById('card-3d-container');
    const statusBadge = document.getElementById('modal-status-badge');
    const glow = document.getElementById('icon-glow');
    const dateContainer = document.getElementById('modal-date-container');

    if (card3d) {
        card3d.classList.remove('rarity-common', 'rarity-rare', 'rarity-epic', 'rarity-legendary');
        card3d.classList.add(`rarity-${item.rarity}`);
    }

    if (item.isUnlocked) {
        if (card3d) {
            card3d.classList.add('is-unlocked');
            card3d.classList.remove('grayscale');
        }
        if (statusBadge) statusBadge.innerHTML = `<div class="bg-amber-500 text-white text-[10px] font-bold px-2 py-1 rounded shadow-lg flex items-center gap-1"><i class="fas fa-check-circle"></i> 已获得</div>`;
        if (glow) glow.style.opacity = '1';
        if (dateContainer) {
            dateContainer.classList.remove('hidden');
            const dateSpan = document.getElementById('modal-date');
            if (dateSpan) dateSpan.innerText = item.unlockDate;
        }
        if (iconContainer) iconContainer.style.filter = 'none';
    } else {
        if (card3d) {
            card3d.classList.remove('is-unlocked');
            card3d.classList.add('grayscale');
        }
        if (statusBadge) statusBadge.innerHTML = `<div class="bg-stone-400 text-white text-[10px] font-bold px-2 py-1 rounded shadow-lg flex items-center gap-1"><i class="fas fa-lock"></i> 待解锁</div>`;
        if (glow) glow.style.opacity = '0';
        if (dateContainer) dateContainer.classList.add('hidden');
        if (iconContainer) iconContainer.style.filter = 'grayscale(100%) opacity(0.6)';
    }
    
    // 5. 分享按钮
    const shareBtnContainer = document.getElementById('modal-share-container');
    if (shareBtnContainer) {
        if (item.isUnlocked) {
            shareBtnContainer.innerHTML = `<button onclick="generateShareCard()" class="btn btn-sm btn-outline btn-warning w-full gap-2 mt-4 hover:scale-105 transition-transform"><i class="fas fa-share-alt"></i> 生成分享卡片</button>`;
            shareBtnContainer.classList.remove('hidden');
        } else {
            shareBtnContainer.classList.add('hidden');
        }
    }

    modal.showModal();
};
        // --- 核心优化：更精致的生成逻辑 ---
        window.generateShareCard = function() {
            const card = document.getElementById('card-3d-container');
            const btn = document.querySelector('#modal-share-container button');
            const originalHtml = btn.innerHTML;
            
            // 1. 设置加载状态：固定宽度防止跳动，使用动画背景
            const btnWidth = btn.offsetWidth;
            btn.style.width = `${btnWidth}px`;
            btn.classList.add('btn-generating'); // 添加流光背景类
            btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> 正在绘图...';
            btn.disabled = true;

            // 2. 准备截图：移除 3D 变换以获得清晰平面的图像
            const originalTransform = card.style.transform;
            card.style.transform = 'none';
            
            // 稍微延迟一下，确保 UI 更新和 transforms 清除完成
            setTimeout(() => {
                html2canvas(card, {
                    backgroundColor: null, // 透明背景
                    scale: 3,              // 提高分辨率，让文字更清晰
                    useCORS: true,         // 允许跨域图片
                    logging: false,
                    allowTaint: true
                }).then(canvas => {
                    // 恢复状态
                    card.style.transform = originalTransform;
                    
                    const link = document.createElement('a');
                    link.download = `my-achievement-${Date.now()}.png`;
                    link.href = canvas.toDataURL('image/png');
                    link.click();
                    
                    // 恢复按钮（延迟一点点，增加“完成”的仪式感）
                    setTimeout(() => {
                        btn.innerHTML = `<i class="fas fa-check"></i> 保存成功`;
                        btn.classList.remove('btn-generating');
                        setTimeout(() => {
                            btn.innerHTML = originalHtml;
                            btn.style.width = 'auto';
                            btn.disabled = false;
                        }, 1500);
                    }, 500);

                }).catch(err => {
                    console.error(err);
                    card.style.transform = originalTransform;
                    btn.innerHTML = '<i class="fas fa-times"></i> 生成失败';
                    btn.classList.remove('btn-generating');
                    btn.disabled = false;
                });
            }, 300); // 300ms 延迟
        };

        function renderGrid(filter) {
            grid.innerHTML = '';
            const items = SERVER_DATA.achievements
                .filter(item => filter === 'all' || item.category === filter)
                .sort((a, b) => (a.isUnlocked === b.isUnlocked) ? 0 : a.isUnlocked ? -1 : 1);

            if (items.length === 0) {
                emptyState.classList.remove('hidden'); emptyState.classList.add('flex');
            } else {
                emptyState.classList.add('hidden'); emptyState.classList.remove('flex');
            }

            items.forEach((item, index) => {
                const card = document.createElement('div');
                card.style.animationDelay = `${index * 30}ms`;
                card.onclick = function() { window.openBadgeDetail(item.id); };
                
                const isSecretLocked = !item.isUnlocked && item.isSecret;
                const displayName = isSecretLocked ? "???" : item.name;
                const displayDesc = isSecretLocked ? "继续探索以揭示此成就" : (item.description || '暂无描述');
                const displayCondition = isSecretLocked ? "???" : item.condition;
                const displayIcon = isSecretLocked ? "?" : (item.iconText || '🏅');

                const iconHtml = (item.isImage && !isSecretLocked)
                    ? `<img src="${item.iconUrl}" class="w-16 h-16 object-contain drop-shadow-md" loading="lazy">` 
                    : `<span class="text-4xl text-stone-700">${displayIcon}</span>`;

                const statusClass = item.isUnlocked ? 'unlocked' : 'locked';
                const statusBadge = item.isUnlocked
                    ? `<span class="absolute top-3 right-3 bg-white/90 backdrop-blur text-amber-600 text-[10px] font-bold px-2 py-1 rounded-full border border-amber-100 shadow-sm"><i class="fas fa-check"></i></span>`
                    : `<span class="absolute top-3 right-3 bg-stone-200/50 text-stone-400 text-[10px] font-bold px-2 py-1 rounded-full"><i class="fas fa-lock"></i></span>`;
                
                const rarityClass = `rarity-${item.rarity}`;
                
                // 将英文稀有度转为中文
                const cnRarity = RARITY_MAP[item.rarity] || '普通';

                card.className = `card badge-card relative animate-card ${statusClass} ${rarityClass}`;
                card.innerHTML = `
                    <div class="card-body relative z-10">
                        ${statusBadge}
                        <div class="absolute top-3 left-3 badge-tag">${cnRarity}</div>
                        
                        <div class="icon-wrapper w-20 h-20 rounded-full bg-gradient-to-tr from-white to-stone-50 flex items-center justify-center mb-3 ring-1 ring-stone-100 shadow-[inset_0_2px_4px_rgba(0,0,0,0.05)]">
                            ${iconHtml}
                        </div>
                        
                        <h2 class="text-base font-bold text-stone-800 mb-1 leading-tight truncate w-full">${displayName}</h2>
                        
                        <p class="text-xs text-stone-500 leading-relaxed line-clamp-2 h-[2.5em] w-full mb-2">
                            ${displayDesc}
                        </p>
                        
                        <div class="pt-2 border-t border-stone-100/50 w-full mt-auto">
                            <p class="text-[10px] font-mono font-bold truncate ${item.isUnlocked ? 'text-amber-600' : 'text-stone-400'} opacity-80">
                                ${displayCondition}
                            </p>
                        </div>
                    </div>
                    ${item.isUnlocked ? '<div class="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-amber-50/20 pointer-events-none"></div>' : ''}
                `;
                grid.appendChild(card);
            });
        }
    });
</script>
{% endblock %}
```

## 📄 user/my_badges.html

```html
{% extends "base.html" %}

{% block title %}我的成就{% endblock %}

{% block content %}
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    
    <div class="text-center mb-12">
        <h1 class="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary tracking-tight">我的成就墙</h1>
        <p class="text-base-content/60 mt-3 text-lg">记录您的每一个高光时刻，见证成长的足迹</p>
    </div>

    <div class="flex items-center gap-3 mb-6">
        <div class="p-2 bg-primary/10 rounded-lg text-primary">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        </div>
        <h2 class="text-xl font-bold text-base-content">已囊括的荣耀</h2>
        <span class="badge badge-primary badge-outline">{{ user_badges|length if user_badges else 0 }}</span>
    </div>

    {% if user_badges %}
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 mb-16">
            {% for ub in user_badges %}
            {% if ub.badge %}
            {% set is_equipped = current_user.selected_badge_id == ub.badge.id %}
            
            <div class="card bg-base-100 shadow-xl border {{ 'border-primary ring-2 ring-primary/20' if is_equipped else 'border-base-200' }} hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 h-full">
                <div class="card-body p-6 relative overflow-hidden">
                    
                    <div class="absolute -right-6 -top-6 w-32 h-32 bg-gradient-to-br from-primary/10 to-transparent rounded-full blur-2xl"></div>

                    <div class="flex items-start gap-5 relative z-10">
                        <div class="flex-shrink-0 w-16 h-16 rounded-2xl {{ 'bg-primary text-primary-content shadow-lg shadow-primary/30' if is_equipped else 'bg-base-200 text-base-content/80' }} flex items-center justify-center text-4xl transform transition-transform group-hover:scale-110">
                            {% set _icon = ub.badge.icon %}
                            {% if _icon|is_image_icon %}
                                <img src="{{ _icon|badge_icon_url }}" class="w-12 h-12 object-contain" alt="{{ ub.badge.name }}">
                            {% else %}
                                {{ _icon }}
                            {% endif %}
                        </div>

                        <div class="flex-1 min-w-0">
                            <div class="flex justify-between items-start">
                                <h3 class="font-bold text-lg {{ 'text-primary' if is_equipped else 'text-base-content' }} truncate pr-2">
                                    {{ ub.badge.name }}
                                </h3>
                                {% if is_equipped %}
                                    <span class="badge badge-primary badge-sm shadow-sm gap-1">
                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" /></svg>
                                        佩戴中
                                    </span>
                                {% endif %}
                            </div>
                            <p class="text-sm text-base-content/70 mt-1 line-clamp-2 min-h-[2.5em]">{{ ub.badge.description }}</p>
                            
                            <div class="flex items-center justify-between mt-4 pt-4 border-t border-base-200/50">
                                <span class="text-xs text-base-content/40 font-mono">
                                    解锁于 {{ ub.earned_at.strftime('%Y-%m-%d') }}
                                </span>
                                
                                <div class="card-actions">
                                    {% if is_equipped %}
                                        <button onclick="equipBadge(null)" class="btn btn-xs btn-ghost text-base-content/50 hover:text-error hover:bg-error/10 transition-colors">
                                            卸下徽章
                                        </button>
                                    {% else %}
                                        <button onclick="equipBadge({{ ub.badge.id }})" class="btn btn-sm btn-primary btn-outline gap-2 px-4">
                                            佩戴
                                        </button>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}
            {% endfor %}
        </div>
    {% else %}
        <div class="flex flex-col items-center justify-center py-16 bg-base-100 rounded-3xl border border-dashed border-base-300 mb-16">
            <div class="w-24 h-24 bg-base-200 rounded-full flex items-center justify-center text-4xl mb-4 grayscale opacity-50">🏆</div>
            <h3 class="text-lg font-bold text-base-content/70">暂无成就</h3>
            <p class="text-base-content/50 text-sm mt-1">伟大的旅程始于足下，去探索并解锁您的第一个成就吧！</p>
        </div>
    {% endif %}

    <div class="flex items-center gap-3 mb-6">
        <div class="p-2 bg-base-200 rounded-lg text-base-content/60">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
        </div>
        <h2 class="text-xl font-bold text-base-content/70">探索中的奥秘</h2>
        <span class="badge badge-ghost">{{ unearned_badges|length if unearned_badges else 0 }}</span>
    </div>

    {% if unearned_badges %}
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            {% for badge in unearned_badges %}
            <div class="card bg-base-100/40 border border-base-200 border-dashed hover:border-base-300 hover:bg-base-100 transition-all duration-300 group">
                <div class="card-body p-5">
                    <div class="flex items-center gap-4">
                        <div class="w-14 h-14 rounded-xl bg-base-200/50 flex items-center justify-center text-3xl opacity-40 group-hover:opacity-60 transition-opacity grayscale group-hover:grayscale-0 relative">
                            {% if not badge.is_hidden %}
                                {% set _icon = badge.icon %}
                                {% if _icon|is_image_icon %}
                                    <img src="{{ _icon|badge_icon_url }}" class="w-10 h-10 object-contain" alt="{{ badge.name }}">
                                {% else %}
                                    {{ _icon }}
                                {% endif %}
                            {% else %}
                                🔒
                            {% endif %}
                            {% if badge.is_hidden %}
                                <div class="absolute inset-0 flex items-center justify-center bg-base-300/80 rounded-xl backdrop-blur-[1px]">
                                    <span class="text-xl">?</span>
                                </div>
                            {% endif %}
                        </div>

                        <div class="flex-1 min-w-0">
                            <h3 class="font-bold text-base text-base-content/60 group-hover:text-base-content/80 transition-colors">
                                {{ badge.name if not badge.is_hidden else '神秘成就' }}
                            </h3>
                            
                            {% if badge.is_hidden %}
                                <div class="mt-2 text-xs text-base-content/40 italic">
                                    这是一个隐藏成就，继续探索吧...
                                </div>
                            {% else %}
                                <p class="text-sm text-base-content/40 mt-1 line-clamp-1">{{ badge.description }}</p>
                                
                                <div class="flex flex-wrap gap-2 mt-3">
                                    <div class="inline-flex items-center px-2.5 py-1 rounded-md bg-base-200/60 text-xs font-medium text-base-content/60">
                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 mr-1.5 opacity-70" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd" /></svg>
                                        目标: 
                                        {% if badge.condition_type == 'streak_days' %}连续打卡 {{ badge.condition_value }} 天
                                        {% elif badge.condition_type == 'study_hours' %}学习 {{ badge.condition_value }} 小时
                                        {% elif badge.condition_type == 'note_count' %}创建 {{ badge.condition_value }} 篇笔记
                                        {% elif badge.condition_type == 'featured_count' %}获得 {{ badge.condition_value }} 次精选
                                        {% elif badge.condition_type == 'wiki_edit_count' %}编辑 Wiki {{ badge.condition_value }} 次
                                        {% elif badge.condition_type == 'wiki_create_count' %}创建 Wiki 词条 {{ badge.condition_value }} 个
                                        {% elif badge.condition_type == 'comment_count' %}发布 {{ badge.condition_value }} 条评论
                                        {% elif badge.condition_type == 'night_owl_sessions' %}深夜学习 {{ badge.condition_value }} 天
                                        {% elif badge.condition_type == 'early_bird' %}早起学习 {{ badge.condition_value }} 天
                                        {% elif badge.condition_type == 'weekend_warrior' %}周末累计学习 {{ badge.condition_value }} 小时
                                        {% elif badge.condition_type == 'long_session_count' %}深度专注(>2h) {{ badge.condition_value }} 次
                                        {% elif badge.condition_type == 'share_count' %}分享笔记 {{ badge.condition_value }} 次
                                        {% elif badge.condition_type == 'total_views_received' %}笔记被阅读 {{ badge.condition_value }} 次
                                        {% else %}{{ badge.condition_value }}{% endif %}
                                    </div>
                                    
                                    {% if badge.total_limit is not none %}
                                        {% set remaining = badge.total_limit - badge.issued_count %}
                                        <div class="inline-flex items-center px-2.5 py-1 rounded-md {{ 'bg-error/10 text-error' if remaining <= 0 else 'bg-warning/10 text-warning' }} text-xs font-medium">
                                            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                            {% if remaining <= 0 %}
                                                已抢光 ({{ badge.issued_count }}/{{ badge.total_limit }})
                                            {% else %}
                                                剩余: {{ remaining }}
                                            {% endif %}
                                        </div>
                                    {% endif %}
                                    
                                    {% if badge.sticker_count > 1 %}
                                    <div class="inline-flex items-center px-2.5 py-1 rounded-md bg-info/10 text-info text-xs font-medium">
                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" /></svg>
                                        x{{ badge.sticker_count }} 贴纸
                                    </div>
                                    {% endif %}
                                </div>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    {% else %}
        <div class="alert alert-success shadow-lg">
            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <div>
                <h3 class="font-bold">大满贯！</h3>
                <div class="text-xs">太棒了！您已经解锁了当前版本的所有成就！</div>
            </div>
        </div>
    {% endif %}

</div>
{% endblock %}

{% block scripts %}
<script>
function equipBadge(badgeId) {
    // 添加一个简单的加载状态反馈，虽然页面会刷新，但能防止误触
    const btns = document.querySelectorAll('button');
    btns.forEach(btn => btn.classList.add('loading', 'disabled'));

    fetch('/user/badges/equip', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ badge_id: badgeId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 使用 reload 可能会有些生硬，如果可以的话，建议后端返回新的HTML片段
            // 但为了保持原有逻辑，这里维持 reload
            location.reload();
        } else {
            alert(data.error || '操作失败');
            btns.forEach(btn => btn.classList.remove('loading', 'disabled'));
        }
    })
    .catch(err => {
        console.error(err);
        alert('网络错误');
        btns.forEach(btn => btn.classList.remove('loading', 'disabled'));
    });
}
</script>
{% endblock %}
```

## 📄 user/following.html

```html
{% extends "base.html" %}

{% block title %}我的社交圈{% endblock %}

{% block content %}
<!-- Animated Background -->
<div class="fixed inset-0 -z-10 overflow-hidden bg-base-100">
    <div class="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-primary/5 rounded-full blur-[100px] animate-blob mix-blend-multiply opacity-30"></div>
    <div class="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-secondary/5 rounded-full blur-[100px] animate-blob animation-delay-4000 mix-blend-multiply opacity-30"></div>
</div>

<div class="max-w-5xl mx-auto px-4 py-10 animate-fade-in space-y-12">
    
    <!-- Header -->
    <div class="flex flex-col md:flex-row items-center justify-between gap-6">
        <div class="flex items-center gap-4 w-full md:w-auto">
            <a href="{{ url_for('public_profile', user_id=current_user.id) }}" class="btn btn-circle btn-ghost hover:bg-base-200">
                <i class="fas fa-arrow-left text-lg"></i>
            </a>
            <div>
                <h1 class="text-3xl font-black text-base-content tracking-tight">我的社交圈</h1>
                <p class="text-sm text-base-content/60 mt-1">管理您的学友和关注列表</p>
            </div>
        </div>

        <!-- Search Filter -->
        <div class="relative w-full md:w-72">
            <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-base-content/40">
                <i class="fas fa-search"></i>
            </span>
            <input type="text" id="user-search" placeholder="搜索用户..." class="input input-bordered w-full pl-10 pr-10 rounded-xl bg-base-100/50 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all">
            <button id="clear-search" class="absolute inset-y-0 right-0 pr-3 flex items-center text-base-content/40 hover:text-base-content hidden cursor-pointer transition-colors">
                <i class="fas fa-times-circle"></i>
            </button>
        </div>
    </div>

    <!-- 1. Study Partners Section (VIP Area) -->
    <div class="space-y-6">
        <div class="flex items-center gap-3 pb-2 border-b border-base-content/5">
            <div class="p-2 bg-gradient-to-br from-amber-100 to-amber-50 text-amber-600 rounded-lg shadow-sm">
                <i class="fas fa-crown"></i>
            </div>
            <h2 class="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-amber-600 to-orange-600">我的学友</h2>
            <span class="badge badge-warning badge-sm font-mono shadow-sm">{{ partners|length }}</span>
        </div>
        
        {% if partners %}
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6" id="partners-grid">
            {% for user in partners %}
            <!-- VIP Partner Card -->
            <div class="card bg-base-100/80 backdrop-blur-xl border border-amber-500/20 shadow-lg hover:shadow-xl hover:-translate-y-1 hover:border-amber-500/40 transition-all duration-300 group user-card relative overflow-hidden" data-username="{{ user.username }}">
                <!-- Golden Glow -->
                <div class="absolute top-0 right-0 w-32 h-32 bg-amber-500/5 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>
                
                <div class="card-body p-6">
                    <div class="flex items-start justify-between gap-4">
                        <!-- Rainbow Avatar -->
                        <a href="{{ url_for('public_profile', user_id=user.id) }}" class="relative">
                            <div class="avatar placeholder">
                                {% set avatar_styles = [
                                    'bg-gradient-to-br from-rose-100 to-rose-200 text-rose-600',
                                    'bg-gradient-to-br from-orange-100 to-orange-200 text-orange-600',
                                    'bg-gradient-to-br from-emerald-100 to-emerald-200 text-emerald-600',
                                    'bg-gradient-to-br from-cyan-100 to-cyan-200 text-cyan-600',
                                    'bg-gradient-to-br from-blue-100 to-blue-200 text-blue-600',
                                    'bg-gradient-to-br from-violet-100 to-violet-200 text-violet-600',
                                    'bg-gradient-to-br from-fuchsia-100 to-fuchsia-200 text-fuchsia-600'
                                ] %}
                                {% set style_class = avatar_styles[(user.id) % 7] %}
                                <div class="w-16 h-16 rounded-full ring-4 ring-base-100 shadow-md {{ style_class }} grid place-items-center text-2xl font-black group-hover:rotate-6 transition-transform">
                                    {{ user.username[0] | upper }}
                                </div>
                            </div>
                            <!-- Online Status Ring -->
                            <div class="absolute -bottom-1 -right-1 w-5 h-5 bg-base-100 rounded-full flex items-center justify-center">
                                <span class="relative flex h-3 w-3">
                                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                                  <span class="relative inline-flex rounded-full h-3 w-3 bg-success"></span>
                                </span>
                            </div>
                        </a>

                        <!-- Actions Dropdown -->
                        <div class="dropdown dropdown-end">
                            <label tabindex="0" class="btn btn-ghost btn-sm btn-circle text-base-content/40 hover:text-base-content hover:bg-base-200">
                                <i class="fas fa-ellipsis-h"></i>
                            </label>
                            <ul tabindex="0" class="dropdown-content menu p-2 shadow-lg bg-base-100 rounded-xl w-40 border border-base-content/5 z-20">
                                <li>
                                    <form action="{{ url_for('unfollow_user', user_id=user.id) }}" method="POST" onsubmit="return confirm('取消关注后，你们将不再是学友关系。确定吗？');" class="w-full">
                                        <button type="submit" class="text-error hover:bg-error/10 w-full text-left flex gap-2">
                                            <i class="fas fa-user-minus"></i> 取消关注
                                        </button>
                                    </form>
                                </li>
                            </ul>
                        </div>
                    </div>

                    <!-- Info -->
                    <div class="mt-3">
                        <div class="flex items-center gap-2">
                            <a href="{{ url_for('public_profile', user_id=user.id) }}" class="font-extrabold text-xl truncate hover:text-primary transition-colors">{{ user.username }}</a>
                            <span class="badge badge-sm badge-ghost font-mono opacity-60">Lv.{{ (user.badges|length // 3) + 1 }}</span>
                        </div>
                        
                        <!-- Status Line -->
                        <div class="text-xs font-medium mt-2 flex items-center gap-2">
                            {% if user.is_online %}
                                <div class="flex items-center gap-1.5 text-success bg-success/10 px-2 py-0.5 rounded-full border border-success/20">
                                    <span class="relative flex h-2 w-2">
                                      <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                                      <span class="relative inline-flex rounded-full h-2 w-2 bg-success"></span>
                                    </span>
                                    <span>在线 · 今日专注 {{ user.study_time_today_human }}</span>
                                </div>
                            {% else %}
                                <div class="flex items-center gap-1.5 text-base-content/50 bg-base-200/50 px-2 py-0.5 rounded-full border border-base-content/5">
                                    <span class="w-2 h-2 rounded-full bg-base-300"></span>
                                    <span>离线 · {{ user.last_active_human }}活跃</span>
                                </div>
                            {% endif %}
                        </div>

                        <!-- Recent Achievement -->
                        {% if user.latest_earned_badge %}
                        <div class="mt-4 flex items-center gap-3 bg-base-100/50 rounded-xl p-2 border border-base-content/5 group/badge hover:bg-white hover:shadow-sm transition-all cursor-default">
                            <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-100 flex items-center justify-center shrink-0">
                                {% if user.latest_earned_badge.badge.icon|is_image_icon %}
                                    <img src="{{ user.latest_earned_badge.badge.icon|badge_icon_url }}" class="w-6 h-6 object-contain">
                                {% else %}
                                    <span class="text-lg">{{ user.latest_earned_badge.badge.icon }}</span>
                                {% endif %}
                            </div>
                            <div class="min-w-0 flex-1">
                                <div class="text-[10px] text-base-content/40 uppercase font-bold leading-none mb-1">近期成就</div>
                                <div class="text-xs font-bold truncate text-base-content/80 group-hover/badge:text-primary transition-colors">{{ user.latest_earned_badge.badge.name }}</div>
                            </div>
                        </div>
                        {% else %}
                        <div class="mt-4 h-[58px]"></div> <!-- Spacer to align cards if no achievement -->
                        {% endif %}
                    </div>

                    <!-- Detailed Stats -->
                    <div class="grid grid-cols-3 gap-2 mt-4 p-3 bg-base-50/50 rounded-xl border border-base-content/5">
                        <div class="flex flex-col items-center">
                            <span class="text-[10px] text-base-content/40 uppercase font-bold">徽章</span>
                            <span class="font-mono font-bold text-lg text-base-content/80">{{ user.badges|length }}</span>
                        </div>
                        <div class="flex flex-col items-center border-l border-base-content/5">
                            <span class="text-[10px] text-base-content/40 uppercase font-bold">笔记</span>
                            <span class="font-mono font-bold text-lg text-base-content/80">{{ user.notes|length }}</span>
                        </div>
                        <div class="flex flex-col items-center border-l border-base-content/5">
                            <span class="text-[10px] text-base-content/40 uppercase font-bold">获赞</span>
                            <span class="font-mono font-bold text-lg text-base-content/80">{{ user.wikis|length * 5 + user.notes|length * 2 }}</span> <!-- Simple calc for demo -->
                        </div>
                    </div>

                    <!-- Call to Actions -->
                    <div class="mt-5 grid grid-cols-2 gap-3">
                        <a href="{{ url_for('public_profile', user_id=user.id) }}" class="btn btn-sm btn-ghost bg-base-200/50 hover:bg-base-200 gap-2 group/btn">
                            <i class="fas fa-shapes text-base-content/40 group-hover/btn:text-primary transition-colors"></i> 参观贴纸
                        </a>
                        <a href="{{ url_for('public_profile', user_id=user.id) }}" class="btn btn-sm btn-ghost bg-base-200/50 hover:bg-base-200 gap-2 group/btn">
                            <i class="fas fa-chart-line text-base-content/40 group-hover/btn:text-primary transition-colors"></i> 详细动态
                        </a>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="flex flex-col items-center justify-center py-16 bg-base-50/50 rounded-2xl border border-dashed border-base-content/10 text-base-content/40">
            <div class="w-16 h-16 bg-amber-50 rounded-full flex items-center justify-center mb-4 text-2xl text-amber-500">
                <i class="fas fa-crown opacity-50"></i>
            </div>
            <p class="font-medium">还没有互相关注的学友</p>
            <p class="text-xs mt-1 opacity-60">找到志同道合的伙伴，一起进步</p>
            <a href="{{ url_for('online_users') }}" class="btn btn-sm btn-primary btn-outline mt-4 gap-2">
                <i class="fas fa-search"></i> 发现学友
            </a>
        </div>
        {% endif %}
    </div>

    <!-- 2. Following Section (Compact List) -->
    <div class="space-y-6">
        <div class="flex items-center gap-3 pb-2 border-b border-base-content/5">
            <div class="p-2 bg-base-200 text-base-content/70 rounded-lg">
                <i class="fas fa-eye"></i>
            </div>
            <h2 class="text-xl font-bold">关注列表</h2>
            <span class="badge badge-ghost badge-sm font-mono">{{ following|length }}</span>
        </div>
        
        {% if following %}
        <div class="flex flex-col gap-3" id="following-list">
            {% for user in following %}
            <!-- Compact Following Row -->
            <div class="group flex items-center gap-4 p-3 rounded-xl bg-base-100/40 border border-base-content/5 hover:bg-white hover:shadow-md hover:border-base-content/10 transition-all duration-200 user-card" data-username="{{ user.username }}">
                <!-- Small Rainbow Avatar -->
                <a href="{{ url_for('public_profile', user_id=user.id) }}" class="avatar placeholder shrink-0">
                    {% set avatar_styles = [
                        'bg-gradient-to-br from-rose-100 to-rose-200 text-rose-600',
                        'bg-gradient-to-br from-orange-100 to-orange-200 text-orange-600',
                        'bg-gradient-to-br from-emerald-100 to-emerald-200 text-emerald-600',
                        'bg-gradient-to-br from-cyan-100 to-cyan-200 text-cyan-600',
                        'bg-gradient-to-br from-blue-100 to-blue-200 text-blue-600',
                        'bg-gradient-to-br from-violet-100 to-violet-200 text-violet-600',
                        'bg-gradient-to-br from-fuchsia-100 to-fuchsia-200 text-fuchsia-600'
                    ] %}
                    {% set style_class = avatar_styles[(user.id) % 7] %}
                    <div class="w-10 h-10 rounded-full {{ style_class }} text-sm font-bold grid place-items-center">
                        {{ user.username[0] | upper }}
                    </div>
                </a>
                
                <div class="flex-1 min-w-0 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                        <a href="{{ url_for('public_profile', user_id=user.id) }}" class="font-bold hover:text-primary transition-colors truncate">{{ user.username }}</a>
                        <div class="text-xs text-base-content/40 truncate font-mono">
                            关注于 {{ user.created_at.strftime('%Y-%m-%d') }}
                        </div>
                    </div>
                    
                    <!-- Twitter-style Unfollow Button -->
                    <form action="{{ url_for('unfollow_user', user_id=user.id) }}" method="POST" onsubmit="event.stopPropagation(); return confirm('确定取消关注吗？');">
                        <button type="submit" class="btn btn-sm w-24 btn-outline border-base-content/20 hover:border-error hover:bg-error hover:text-white group/btn transition-all">
                            <span class="group-hover/btn:hidden text-xs font-bold text-base-content/60">Following</span>
                            <span class="hidden group-hover/btn:inline text-xs font-bold">Unfollow</span>
                        </button>
                    </form>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="text-center py-12 bg-base-50/50 rounded-2xl border border-dashed border-base-content/10 text-base-content/40">
            <p>暂无其他关注</p>
        </div>
        {% endif %}
    </div>

    <!-- Empty Search State -->
    <div id="search-empty-state" class="hidden flex-col items-center justify-center py-20 text-center animate-fade-in">
        <div class="w-24 h-24 bg-base-200/50 rounded-full flex items-center justify-center mb-6">
            <i class="fas fa-search text-4xl text-base-content/20"></i>
        </div>
        <h3 class="text-lg font-bold text-base-content/60">没有找到相关用户</h3>
        <p class="text-sm text-base-content/40 mt-2">换个关键词试试看？</p>
        <button onclick="document.getElementById('clear-search').click()" class="btn btn-ghost btn-sm text-primary mt-4">清除搜索</button>
    </div>
</div>

<script>
    // Enhanced Search Logic
    const searchInput = document.getElementById('user-search');
    const clearBtn = document.getElementById('clear-search');
    const emptyState = document.getElementById('search-empty-state');
    const partnersSection = document.querySelector('.space-y-6:nth-of-type(2)'); // Adjust selector based on DOM
    const followingSection = document.querySelector('.space-y-6:nth-of-type(3)');

    searchInput.addEventListener('input', function(e) {
        const term = e.target.value.toLowerCase().trim();
        const cards = document.querySelectorAll('.user-card');
        let hasVisible = false;
        
        // Toggle Clear Button
        if (term.length > 0) {
            clearBtn.classList.remove('hidden');
        } else {
            clearBtn.classList.add('hidden');
        }

        cards.forEach(card => {
            const username = card.getAttribute('data-username').toLowerCase();
            if (username.includes(term)) {
                card.style.display = ''; // Reset to default (block/flex)
                card.classList.remove('hidden');
                hasVisible = true;
            } else {
                card.classList.add('hidden');
            }
        });

        // Show/Hide Empty State
        if (!hasVisible && term.length > 0) {
            emptyState.classList.remove('hidden');
            emptyState.style.display = 'flex';
        } else {
            emptyState.classList.add('hidden');
            emptyState.style.display = 'none';
        }
    });

    // Clear Search
    clearBtn.addEventListener('click', () => {
        searchInput.value = '';
        searchInput.dispatchEvent(new Event('input'));
        searchInput.focus();
    });
</script>
{% endblock %}
```

## 📄 user/profile.html

```html
{% extends "base.html" %}

{% block title %}{{ user.username }} 的主页{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<link rel="stylesheet" href="{{ url_for('static', filename='css/sticker.css') }}">
<style>
    /* === 1. 贴纸装饰区动效 === */
    #profile-sticker-header {
        position: relative;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        background-image: radial-gradient(#e5e7eb 1px, transparent 1px);
        background-size: 20px 20px;
    }
    
    /* 贴纸画布绝对定位 */
    #sticker-canvas {
        position: absolute !important; 
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 20;
        pointer-events: auto;
        overflow: hidden;
    }

    /* 拖拽激活时的视觉反馈 */
    #profile-sticker-header.drag-active {
        background-color: #f5f5f4;
        border-color: #818cf8;
        box-shadow: inset 0 0 30px rgba(79, 70, 229, 0.05);
    }
    #profile-sticker-header.drag-active .drop-hint {
        opacity: 1;
        transform: scale(1);
    }

    /* === 2. 徽章网格 (6列 x 3行 = 18个) === */
    .badge-grid-page {
        display: grid;
        grid-template-columns: repeat(6, 1fr); 
        grid-template-rows: repeat(3, 1fr);    
        gap: 0.5rem;
        width: 100%;
        height: 100%;
        animation: fadeIn 0.3s ease-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(5px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .animate-fade-in {
        animation: fadeIn 0.5s ease-out forwards;
    }
</style>
{% endblock %}

{% block content %}

<div id="profile-sticker-header" class="relative w-full h-[220px] sm:h-[300px] lg:h-[380px] -mt-6 mb-8 group z-0 overflow-hidden bg-white border-b border-stone-200">
    
    <div class="drop-hint absolute inset-6 border-2 border-dashed border-indigo-400 rounded-3xl flex flex-col items-center justify-center bg-white/90 backdrop-blur-sm z-30 opacity-0 transform scale-95 transition-all duration-300 pointer-events-none text-indigo-500">
        <i class="fas fa-magic text-5xl mb-3 animate-bounce"></i>
        <span class="font-bold tracking-widest uppercase text-lg">松开鼠标放置贴纸</span>
    </div>
    
    <div class="absolute inset-0 flex items-center justify-center opacity-30 group-hover:opacity-0 transition-opacity duration-500 pointer-events-none z-10">
        <span class="text-xs font-bold tracking-[0.3em] text-stone-400 uppercase">STICKER DECORATION ZONE</span>
    </div>
    
    <div id="sticker-canvas"></div>

    <div class="absolute bottom-0 left-0 w-full h-24 bg-gradient-to-t from-stone-50 via-stone-50/80 to-transparent z-10 pointer-events-none"></div>
</div>

<div class="max-w-[1400px] mx-auto px-6 pb-12 relative z-40 animate-fade-in -mt-12 lg:-mt-20">
    
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">

        <aside class="lg:col-span-3 space-y-6">
            
            <div class="bg-white rounded-[2rem] p-8 border border-stone-200 shadow-xl shadow-stone-200/40 flex flex-col items-center relative overflow-hidden">
                <div class="avatar placeholder mb-5 transform transition-transform hover:scale-105 duration-300">
                    <div class="w-36 h-36 rounded-full bg-stone-50 text-stone-300 ring-4 ring-white shadow-lg grid place-items-center text-6xl font-black select-none">
                        <span>{{ user.username[0] | upper }}</span>
                    </div>
                    <div class="absolute bottom-2 right-2 w-7 h-7 bg-white rounded-full flex items-center justify-center">
                        <div class="w-5 h-5 bg-emerald-500 rounded-full border-[3px] border-white animate-pulse"></div>
                    </div>
                </div>
                
                <h1 class="text-2xl font-black text-stone-800 tracking-tight">{{ user.username }}</h1>
                <p class="text-stone-400 font-bold text-sm mt-1 bg-stone-50 px-3 py-1 rounded-full">@{{ user.username }}</p>
            </div>

            <div class="bg-white rounded-[2rem] border border-stone-200 shadow-sm overflow-hidden">
                <div class="p-6">
                    <div class="flex justify-between items-center mb-6">
                        <div class="text-center flex-1 cursor-pointer group" onclick="window.location.href='{{ url_for('my_following') }}'">
                            <div class="text-xl font-black text-stone-800 group-hover:text-indigo-600 transition-colors">{{ stats.study_partner_count }}</div>
                            <div class="text-[10px] text-stone-400 font-bold uppercase mt-1">学友</div>
                        </div>
                        <div class="w-px h-8 bg-stone-100"></div>
                        <div class="text-center flex-1 cursor-pointer group" onclick="window.location.href='{{ url_for('my_following') }}'">
                            <div class="text-xl font-black text-stone-800 group-hover:text-indigo-600 transition-colors">{{ stats.following_count }}</div>
                            <div class="text-[10px] text-stone-400 font-bold uppercase mt-1">关注</div>
                        </div>
                        <div class="w-px h-8 bg-stone-100"></div>
                        <div class="text-center flex-1 cursor-pointer group" onclick="window.location.href='{{ url_for('my_following') }}'">
                            <div class="text-xl font-black text-stone-800 group-hover:text-indigo-600 transition-colors">{{ stats.follower_count }}</div>
                            <div class="text-[10px] text-stone-400 font-bold uppercase mt-1">粉丝</div>
                        </div>
                    </div>

                    <div class="pt-4 border-t border-stone-100">
                    {% if user.id != current_user.id %}
                        {% if is_following %}
                            <form action="{{ url_for('unfollow_user', user_id=user.id) }}" method="POST">
                                <button type="submit" class="btn btn-block btn-outline border-stone-200 hover:bg-red-50 hover:text-red-500 hover:border-red-200 text-stone-500 h-11 min-h-0 rounded-xl font-bold">取消关注</button>
                            </form>
                        {% else %}
                            <form action="{{ url_for('follow_user', user_id=user.id) }}" method="POST">
                                <button type="submit" class="btn btn-block btn-primary text-white shadow-lg shadow-primary/20 h-11 min-h-0 rounded-xl font-bold">关注</button>
                            </form>
                        {% endif %}
                    {% else %}
                        <a href="{{ url_for('my_following') }}" class="btn btn-block btn-neutral bg-stone-800 hover:bg-stone-700 text-white border-none h-11 min-h-0 rounded-xl font-bold">管理关注</a>
                    {% endif %}
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-[2rem] p-6 border border-stone-200 shadow-sm">
                <div class="flex items-center gap-2 mb-5 pb-2 border-b border-stone-100">
                    <div class="w-1.5 h-4 bg-indigo-500 rounded-full"></div>
                    <h3 class="font-bold text-stone-800 text-sm">学习数据</h3>
                </div>
                
                <div class="grid grid-cols-2 gap-3">
                    <div class="bg-stone-50 p-3 rounded-2xl border border-stone-100 text-center group hover:bg-white hover:shadow-md transition-all duration-300">
                        <div class="text-[10px] text-stone-400 uppercase font-bold mb-1">等级</div>
                        <div class="text-xl font-black text-stone-700 group-hover:text-indigo-600">Lv.{{ (user_badges|length // 3) + 1 }}</div>
                    </div>
                    <div class="bg-stone-50 p-3 rounded-2xl border border-stone-100 text-center group hover:bg-white hover:shadow-md transition-all duration-300">
                        <div class="text-[10px] text-stone-400 uppercase font-bold mb-1">连续打卡</div>
                        <div class="text-xl font-black text-stone-700 group-hover:text-orange-500">{{ stats.streak_days }} <span class="text-xs font-normal text-stone-400">天</span></div>
                    </div>
                    <div class="bg-stone-50 p-3 rounded-2xl border border-stone-100 text-center group hover:bg-white hover:shadow-md transition-all duration-300">
                        <div class="text-[10px] text-stone-400 uppercase font-bold mb-1">学习时长</div>
                        <div class="text-xl font-black text-stone-700 group-hover:text-emerald-600">{{ stats.study_hours }} <span class="text-xs font-normal text-stone-400">h</span></div>
                    </div>
                    <div class="bg-stone-50 p-3 rounded-2xl border border-stone-100 text-center group hover:bg-white hover:shadow-md transition-all duration-300">
                        <div class="text-[10px] text-stone-400 uppercase font-bold mb-1">贡献度</div>
                        <div class="text-xl font-black text-stone-700 group-hover:text-blue-600">{{ stats.wiki_edit_count }}</div>
                    </div>
                </div>
            </div>

        </aside>

        <main class="lg:col-span-9 space-y-6">
            
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
                
                <div class="lg:col-span-4 bg-white rounded-[2rem] border border-stone-200 shadow-sm p-8 flex flex-col h-[400px] relative overflow-hidden">
                    <div class="absolute -top-4 -right-4 p-8 opacity-[0.04]">
                        <i class="fas fa-quote-right text-9xl text-black"></i>
                    </div>
                    
                    <div class="flex items-center gap-3 mb-6">
                        <div class="w-1.5 h-6 bg-stone-800 rounded-full"></div>
                        <h3 class="font-bold text-stone-800 text-lg">学习概况</h3>
                    </div>

                    <div class="relative z-10 flex-1 flex flex-col">
                        <div class="text-stone-600 space-y-6 leading-relaxed">
                            <div>
                                <p class="text-3xl font-bold text-stone-800 mb-2">Hello! 👋</p>
                                <p class="text-sm text-stone-500">这里是 <strong>{{ user.username }}</strong> 的知识库。</p>
                            </div>
                            <div class="space-y-3 pt-4">
                                <div class="space-y-1">
                                    <div class="flex items-center justify-between text-sm">
                                        <span class="text-stone-400 font-medium">笔记创作</span>
                                        <span class="font-bold text-stone-800">{{ stats.note_count }} 篇</span>
                                    </div>
                                    <div class="w-full bg-stone-100 rounded-full h-2 overflow-hidden">
                                        <div class="bg-indigo-500 h-2 rounded-full" style="width: {{ [stats.note_count, 100]|min }}%"></div>
                                    </div>
                                </div>
                                <div class="space-y-1">
                                    <div class="flex items-center justify-between text-sm">
                                        <span class="text-stone-400 font-medium">Wiki 参与</span>
                                        <span class="font-bold text-stone-800">{{ stats.wiki_count }} 个</span>
                                    </div>
                                    <div class="w-full bg-stone-100 rounded-full h-2 overflow-hidden">
                                        <div class="bg-emerald-500 h-2 rounded-full" style="width: {{ [stats.wiki_count * 5, 100]|min }}%"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="lg:col-span-8 bg-white rounded-[2rem] border border-stone-200 shadow-sm p-8 flex flex-col h-[400px]">
                    <div class="flex justify-between items-center mb-6">
                        <div class="flex items-center gap-3">
                            <div class="w-1.5 h-6 bg-orange-500 rounded-full"></div>
                            <h3 class="font-bold text-stone-800 text-lg">成就徽章</h3>
                        </div>
                        <div class="flex items-center gap-3">
                            <span class="badge badge-sm badge-ghost font-mono text-stone-400">{{ user_badges|length }} 获得</span>
                            <div class="flex gap-1" id="badge-controls">
                                <button onclick="changeBadgePage(-1)" class="w-7 h-7 rounded-full bg-stone-100 text-stone-500 hover:bg-stone-800 hover:text-white transition-all flex items-center justify-center disabled:opacity-20">
                                    <i class="fas fa-chevron-left text-[10px]"></i>
                                </button>
                                <button onclick="changeBadgePage(1)" class="w-7 h-7 rounded-full bg-stone-100 text-stone-500 hover:bg-stone-800 hover:text-white transition-all flex items-center justify-center disabled:opacity-20">
                                    <i class="fas fa-chevron-right text-[10px]"></i>
                                </button>
                            </div>
                            <a href="{{ url_for('achievement_book', user_id=user.id) }}" class="w-7 h-7 rounded-full bg-indigo-50 text-indigo-500 hover:bg-indigo-600 hover:text-white transition-all flex items-center justify-center ml-1 tooltip tooltip-left" data-tip="成就册">
                                <i class="fas fa-book-open text-[10px]"></i>
                            </a>
                        </div>
                    </div>
                    
                    <div class="relative flex-1 w-full overflow-hidden">
                        <div id="badge-pages-container" class="w-full h-full">
                            {% for ub in user_badges %}
                                <div class="badge-item hidden" 
                                     data-id="{{ ub.badge.id }}"
                                     data-name="{{ ub.badge.name }}"
                                     data-icon="{{ ub.badge.icon }}"
                                     data-icon-is-image="{{ ub.badge.icon|is_image_icon }}"
                                     data-icon-url="{{ ub.badge.icon|badge_icon_url }}"
                                     data-is-equipped="{{ 1 if user.selected_badge_id == ub.badge.id else 0 }}">
                                </div>
                            {% endfor %}
                            {% if not user_badges %}
                                <div class="flex h-full items-center justify-center text-stone-400 text-sm bg-stone-50/50 rounded-2xl border border-dashed border-stone-200 flex-col gap-3">
                                    <i class="fas fa-medal text-4xl opacity-20"></i>
                                    <span>暂无成就，继续加油！</span>
                                </div>
                            {% endif %}
                        </div>
                    </div>
                    
                    <div class="mt-2 text-center">
                        <div id="badge-page-dots" class="inline-flex gap-1.5 justify-center"></div>
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-[2rem] border border-stone-200 shadow-sm p-8">
                <div class="flex items-center justify-between mb-6 border-b border-stone-50 pb-4">
                    <div class="flex items-center gap-3">
                        <div class="w-1.5 h-6 bg-stone-800 rounded-full"></div>
                        <h3 class="font-bold text-stone-800 text-lg">热门笔记</h3>
                    </div>
                    <a href="{{ url_for('book_index') }}" class="text-xs font-bold text-stone-400 hover:text-indigo-600 transition-colors bg-stone-50 px-3 py-1 rounded-full">查看全部</a>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {% if recent_notes %}
                        {% for note in recent_notes[:6] %}
                        <a href="{{ url_for('view_note', note_id=note.id) }}" class="card bg-stone-50/50 hover:bg-white hover:shadow-lg hover:shadow-indigo-100/50 border border-stone-100 hover:border-indigo-100 transition-all duration-300 group rounded-2xl">
                            <div class="card-body p-5">
                                <div class="flex justify-between items-start mb-3">
                                    <div class="flex items-center gap-3 w-full overflow-hidden">
                                        <div class="w-8 h-8 rounded-lg bg-white text-stone-400 flex items-center justify-center shadow-sm group-hover:text-indigo-500 group-hover:scale-110 transition-transform">
                                            <i class="far fa-file-alt"></i>
                                        </div>
                                        <h4 class="font-bold text-stone-700 group-hover:text-indigo-600 truncate flex-1 transition-colors">{{ note.title }}</h4>
                                    </div>
                                    {% if note.is_featured %}
                                        <span class="badge badge-xs badge-warning uppercase text-[9px] font-bold shrink-0">精选</span>
                                    {% endif %}
                                </div>
                                
                                <p class="text-sm text-stone-500 line-clamp-2 h-10 leading-relaxed font-normal mb-2 opacity-80">
                                    {{ note.content_md | striptags | truncate(80) or '暂无预览内容...' }}
                                </p>
                                
                                <div class="flex items-center justify-between mt-auto pt-3 border-t border-stone-200/50">
                                    <div class="flex items-center gap-1.5 text-xs text-stone-400 font-mono bg-white px-2 py-1 rounded border border-stone-100">
                                        <span class="w-1.5 h-1.5 rounded-full bg-yellow-400"></span>
                                        <span>Markdown</span>
                                    </div>
                                    <div class="flex items-center gap-4 text-xs text-stone-400 font-medium">
                                        <span class="flex items-center gap-1 group-hover:text-indigo-600 transition-colors">
                                            <i class="far fa-eye"></i> 阅读 {{ note.view_count }}
                                        </span>
                                        <span class="flex items-center gap-1 group-hover:text-indigo-600 transition-colors">
                                            <i class="fas fa-share-alt"></i> 分享 {{ note.shares|length }}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </a>
                        {% endfor %}
                    {% else %}
                        <div class="col-span-full py-16 text-center border-2 border-dashed border-stone-200 rounded-2xl bg-stone-50/30">
                            <i class="far fa-folder-open text-3xl text-stone-300 mb-2"></i>
                            <p class="text-stone-400 font-medium">暂无公开笔记</p>
                        </div>
                    {% endif %}
                </div>
            </div>

        </main>
    </div>
</div>

{% if current_user.is_authenticated %}
<button id="sticker-fab" class="sticker-fab btn btn-circle btn-lg fixed bottom-8 right-8 z-50 bg-stone-900/90 backdrop-blur-md text-white shadow-2xl border border-white/10 hover:scale-110 transition-all duration-300">
    <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
</button>
<div id="sticker-drawer" class="sticker-drawer">
    <div class="sticker-drawer-header">
        <h3 class="font-bold text-lg">我的贴纸库</h3>
        <div class="flex gap-2">
            <button id="sticker-publish-btn" class="btn btn-secondary btn-sm">发布快照</button>
            <button id="sticker-save-btn" class="btn btn-primary btn-sm">保存</button>
            <button id="sticker-close-btn" class="btn btn-ghost btn-sm btn-circle">✕</button>
        </div>
    </div>
    <div class="sticker-drawer-body">
        <div class="sticker-grid">
            {% for ub in current_user.earned_badges %}
                {% set usage = get_badge_usage(current_user.id, ub.badge.id) %}
                {% set limit = ub.badge.sticker_count %}
                <div class="sticker-option p-2 rounded-lg hover:bg-base-200 cursor-pointer transition-all flex flex-col items-center gap-2 group relative"
                     data-badge-id="{{ ub.badge.id }}"
                     data-badge-icon="{{ ub.badge.icon|badge_icon_url if ub.badge.icon|is_image_icon else ub.badge.icon }}"
                     data-sticker-limit="{{ limit }}"
                     data-used-count="{{ usage }}">
                    <div class="text-3xl transition-transform group-hover:scale-110 relative">
                    {% if ub.badge.icon|is_image_icon %}
                    <img src="{{ ub.badge.icon|badge_icon_url }}" class="w-10 h-10 object-contain drop-shadow-sm" alt="{{ ub.badge.name }}">
                    {% else %}
                    {{ ub.badge.icon }}
                    {% endif %}
                    
                    <!-- Usage Badge -->
                    <div class="absolute -bottom-2 -right-2 badge badge-xs badge-neutral bg-opacity-90 border-none text-[10px] px-1 scale-90 sticker-count-badge">
                        {{ usage }}/{{ limit }}
                    </div>
                </div>
                <span class="text-xs text-center w-full truncate px-1 opacity-70 group-hover:opacity-100">{{ ub.badge.name }}</span>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
{% endif %}

{% endblock %}

{% block scripts %}
<script src="{{ url_for('static', filename='js/sticker.js') }}"></script>
<script>
    // === 1. 贴纸区域交互逻辑 ===
    const stickerHeader = document.getElementById('profile-sticker-header');
    if(stickerHeader) {
        stickerHeader.addEventListener('dragenter', () => stickerHeader.classList.add('drag-active'));
        stickerHeader.addEventListener('dragleave', (e) => {
            if (!stickerHeader.contains(e.relatedTarget)) stickerHeader.classList.remove('drag-active');
        });
        stickerHeader.addEventListener('drop', () => stickerHeader.classList.remove('drag-active'));
    }
    
    // 初始化贴纸管理器 (Profile 模式)
    document.addEventListener('DOMContentLoaded', () => {
        {% if user.id != current_user.id %}
             // Visitor Mode: View target user's stickers (Read-Only)
             new StickerManager('profile', {{ user.id }}, true);
        {% else %}
             // Owner Mode: View/Edit my own stickers
             new StickerManager('profile');
        {% endif %}
    });

    // === 2. 徽章翻页逻辑 (6列 x 3行 = 18个) ===
    const ITEMS_PER_PAGE = 18; 
    let currentBadgePage = 1;
    let totalBadgePages = 1;
    let badgeData = [];

    function initBadges() {
        const items = document.querySelectorAll('.badge-item');
        items.forEach(item => {
            badgeData.push({
                id: item.dataset.id,
                name: item.dataset.name,
                icon: item.dataset.icon,
                isImage: item.dataset.iconIsImage === 'True',
                url: item.dataset.iconUrl,
                isEquipped: item.dataset.isEquipped === '1'
            });
        });

        totalBadgePages = Math.ceil(badgeData.length / ITEMS_PER_PAGE) || 1;
        if (badgeData.length > 0) renderBadgePage(1);
        updateBadgeControls();
    }

    function renderBadgePage(page) {
        currentBadgePage = page;
        const container = document.getElementById('badge-pages-container');
        const dotsContainer = document.getElementById('badge-page-dots');
        
        container.innerHTML = '';
        const pageDiv = document.createElement('div');
        pageDiv.className = 'badge-grid-page';

        const start = (page - 1) * ITEMS_PER_PAGE;
        const end = start + ITEMS_PER_PAGE;
        const pageItems = badgeData.slice(start, end);

        pageItems.forEach(badge => {
            const wrapper = document.createElement('div');
            wrapper.className = 'tooltip w-full h-full';
            wrapper.setAttribute('data-tip', badge.name);
            
            let content = badge.isImage 
                ? `<img src="${badge.url}" class="w-2/3 h-2/3 object-contain drop-shadow-sm transition-transform group-hover:scale-110">`
                : `<span class="text-xl transition-transform group-hover:scale-110">${badge.icon}</span>`;

            let equippedIndicator = badge.isEquipped ? 
                `<div class="absolute -top-1 -right-1 w-2.5 h-2.5 bg-indigo-600 rounded-full border-2 border-white check-indicator shadow-sm"></div>` : '';

            const isOwner = {{ 'true' if user.id == current_user.id else 'false' }};
            const clickAttr = isOwner ? `onclick="quickEquipBadge(${badge.id}, this)"` : '';
            
            wrapper.innerHTML = `
                <button ${clickAttr} 
                    class="w-full h-full rounded-xl bg-stone-50 border border-stone-200 hover:border-indigo-400 hover:bg-indigo-50 transition-all relative group flex items-center justify-center cursor-${isOwner ? 'pointer' : 'default'}">
                    ${content}
                    ${equippedIndicator}
                </button>
            `;
            pageDiv.appendChild(wrapper);
        });

        // 补全空白网格保持布局稳定
        const remaining = ITEMS_PER_PAGE - pageItems.length;
        for (let i = 0; i < remaining; i++) {
            const empty = document.createElement('div');
            empty.className = 'w-full h-full rounded-xl bg-stone-50/20 border border-dashed border-stone-100';
            pageDiv.appendChild(empty);
        }

        container.appendChild(pageDiv);
        
        if (dotsContainer) {
            dotsContainer.innerHTML = '';
            for(let i=1; i<=totalBadgePages; i++) {
                const dot = document.createElement('div');
                dot.className = `w-1.5 h-1.5 rounded-full transition-colors ${i === currentBadgePage ? 'bg-stone-800' : 'bg-stone-300'}`;
                dotsContainer.appendChild(dot);
            }
        }
        updateBadgeControls();
    }

    function changeBadgePage(delta) {
        const newPage = currentBadgePage + delta;
        if (newPage >= 1 && newPage <= totalBadgePages) renderBadgePage(newPage);
    }

    function updateBadgeControls() {
        const prevBtn = document.querySelector('#badge-controls button:first-child');
        const nextBtn = document.querySelector('#badge-controls button:last-child');
        if (prevBtn) prevBtn.disabled = currentBadgePage === 1;
        if (nextBtn) nextBtn.disabled = currentBadgePage === totalBadgePages;
    }

    function quickEquipBadge(badgeId, btnElement) {
        const btn = btnElement.querySelector('button') || btnElement;
        btn.style.transform = 'scale(0.9)';
        setTimeout(() => btn.style.transform = '', 150);

        fetch('/user/badges/equip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ badge_id: badgeId })
        }).then(res => res.json()).then(data => {
            if (data.success) {
                if(typeof showGlobalToast === 'function') showGlobalToast('徽章佩戴成功！', 'success');
                setTimeout(() => window.location.reload(), 300);
            }
        });
    }

    document.addEventListener('DOMContentLoaded', initBadges);

    // === 修复贴纸按钮定位问题 ===
    document.addEventListener("DOMContentLoaded", function() {
        // 获取按钮和抽屉元素
        const fab = document.getElementById('sticker-fab');
        const drawer = document.getElementById('sticker-drawer');
        
        // 将它们移动到 document.body 的最末尾，脱离任何可能有 transform 的父容器
        if (fab) document.body.appendChild(fab);
        if (drawer) document.body.appendChild(drawer);
    });
</script>
{% endblock %}
```

## 📄 admin/create_wiki.html

```html
{% extends "base.html" %}

{% block title %}创建 Wiki{% endblock %}

{% block content %}
<div class="max-w-3xl mx-auto animate-fade-in">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs mb-6 text-stone-500">
        <ul>
            <li><a href="{{ url_for('index') }}">首页</a></li>
            <li>管理</li>
            <li class="font-bold text-stone-700">创建 Wiki</li>
        </ul>
    </div>

    <div class="card bg-white border border-stone-200 shadow-xl shadow-stone-200/20 overflow-hidden">
        <!-- Header -->
        <div class="px-8 py-6 border-b border-stone-100 bg-stone-50/30 flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                <i class="fas fa-book-medical text-2xl"></i>
            </div>
            <div>
                <h2 class="card-title text-2xl text-stone-800">创建新的知识库</h2>
                <p class="text-sm text-stone-500 mt-1">创建一个全新的 Wiki 空间来组织和分享文档</p>
            </div>
        </div>

        <div class="card-body p-8">
            <form method="post" class="space-y-6">
                <!-- Title Input -->
                <div class="form-control">
                    <label class="label">
                        <span class="label-text font-bold text-stone-700">Wiki 名称</span>
                        <span class="label-text-alt text-error">* 必填</span>
                    </label>
                    <div class="relative">
                        <input type="text" name="title" placeholder="例如：Python 进阶教程" 
                               class="input input-bordered w-full pl-10 focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all" 
                               required autofocus />
                        <i class="fas fa-heading absolute left-3.5 top-1/2 -translate-y-1/2 text-stone-400"></i>
                    </div>
                    <label class="label">
                        <span class="label-text-alt text-stone-400">起一个简短且具有描述性的名称</span>
                    </label>
                </div>

                <!-- Description Input -->
                <div class="form-control">
                    <label class="label">
                        <span class="label-text font-bold text-stone-700">简介描述</span>
                    </label>
                    <div class="relative">
                        <textarea name="description" 
                                  class="textarea textarea-bordered h-32 w-full pl-10 pt-3 focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all text-base leading-relaxed" 
                                  placeholder="简要介绍这个 Wiki 的主要内容和目标受众..."></textarea>
                        <i class="fas fa-align-left absolute left-3.5 top-3.5 text-stone-400"></i>
                    </div>
                </div>

                <!-- Appearance Settings -->
                <div class="bg-stone-50 rounded-xl p-4 border border-stone-100">
                    <h3 class="text-sm font-bold text-stone-600 mb-3 flex items-center gap-2">
                        <i class="fas fa-palette text-purple-500"></i> 外观设置
                    </h3>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="form-control">
                            <label class="label"><span class="label-text font-medium">背景颜色</span></label>
                            <div class="flex items-center gap-2">
                                <input type="color" name="bg_color" value="#ffffff" class="h-10 w-full cursor-pointer rounded-lg border border-stone-200 p-1" />
                            </div>
                        </div>
                        <div class="form-control">
                            <label class="label"><span class="label-text font-medium">前景/纹理颜色</span></label>
                            <div class="flex items-center gap-2">
                                <input type="color" name="fg_color" value="#1f2937" class="h-10 w-full cursor-pointer rounded-lg border border-stone-200 p-1" />
                            </div>
                        </div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                        <div class="form-control">
                            <label class="label"><span class="label-text font-medium">渐变颜色 (可选)</span></label>
                            <div class="flex items-center gap-2">
                                <input type="color" name="gradient_color" value="#ffffff" class="h-10 w-full cursor-pointer rounded-lg border border-stone-200 p-1" />
                            </div>
                            <p class="text-xs text-stone-400 mt-1">设置背景渐变的第二种颜色，与背景色混合。</p>
                        </div>
                        <div class="form-control">
                            <label class="label"><span class="label-text font-medium">渐变方向/类型</span></label>
                            <select name="gradient_direction" class="select select-bordered w-full h-10 min-h-0">
                                <option value="to bottom right" selected>↘ 右下 (默认)</option>
                                <option value="to right">→ 向右</option>
                                <option value="to bottom">↓ 向下</option>
                                <option value="to bottom left">↙ 左下</option>
                                <option value="to left">← 向左</option>
                                <option value="to top left">↖ 左上</option>
                                <option value="to top">↑ 向上</option>
                                <option value="to top right">↗ 右上</option>
                                <option value="circle at center">◉ 径向 (中心)</option>
                            </select>
                        </div>
                    </div>

                    <div class="form-control mt-4">
                        <label class="label"><span class="label-text font-medium">背景模糊度 (高斯模糊)</span></label>
                        <div class="flex items-center gap-4">
                            <span class="text-xs text-stone-400">清晰</span>
                            <input type="range" name="blur_level" min="0" max="100" step="1" value="60" class="range range-primary range-sm" />
                            <span class="text-xs text-stone-400">模糊</span>
                        </div>
                        <p class="text-xs text-stone-400 mt-2">调整卡片背景的高斯模糊程度。</p>
                    </div>

                    <div class="form-control mt-4">
                        <label class="label"><span class="label-text font-medium">Arc 风格颗粒度</span></label>
                        <div class="flex items-center gap-4">
                            <span class="text-xs text-stone-400">细腻</span>
                            <input type="range" name="pattern" min="0" max="0.3" step="0.01" value="0.05" class="range range-primary range-sm" />
                            <span class="text-xs text-stone-400">粗糙</span>
                        </div>
                        <p class="text-xs text-stone-400 mt-2">调整表面噪点的强度，营造 Arc 浏览器的纸质/磨砂质感。</p>
                    </div>
                </div>

                <!-- Initialization Options -->
                <div class="bg-stone-50 rounded-xl p-4 border border-stone-100">
                    <h3 class="text-sm font-bold text-stone-600 mb-3 flex items-center gap-2">
                        <i class="fas fa-magic text-amber-500"></i> 初始化选项
                    </h3>
                    <div class="form-control">
                        <label class="label cursor-pointer justify-start gap-3">
                            <input type="checkbox" name="init_home" class="checkbox checkbox-primary checkbox-sm" checked />
                            <span class="label-text text-stone-600">自动创建首页 (Home)</span>
                        </label>
                        <p class="text-xs text-stone-400 pl-8">勾选后将自动创建一个包含简介内容的初始页面。</p>
                    </div>
                </div>

                <!-- Actions -->
                <div class="card-actions justify-end pt-4 mt-4 border-t border-stone-100">
                    <a href="{{ url_for('index') }}" class="btn btn-ghost text-stone-500 hover:bg-stone-100">取消</a>
                    <button type="submit" class="btn btn-primary px-8 gap-2 shadow-lg shadow-primary/20">
                        <i class="fas fa-plus"></i>
                        立即创建
                    </button>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Tips -->
    <div class="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
        <div class="p-4 rounded-xl bg-white border border-stone-100 shadow-sm">
            <div class="w-8 h-8 mx-auto bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mb-2">
                <i class="fas fa-layer-group"></i>
            </div>
            <h4 class="text-sm font-bold text-stone-700">结构化组织</h4>
            <p class="text-xs text-stone-400 mt-1">支持多级目录和标签分类</p>
        </div>
        <div class="p-4 rounded-xl bg-white border border-stone-100 shadow-sm">
            <div class="w-8 h-8 mx-auto bg-green-50 text-green-500 rounded-full flex items-center justify-center mb-2">
                <i class="fas fa-users"></i>
            </div>
            <h4 class="text-sm font-bold text-stone-700">协作编辑</h4>
            <p class="text-xs text-stone-400 mt-1">邀请他人共同维护文档</p>
        </div>
        <div class="p-4 rounded-xl bg-white border border-stone-100 shadow-sm">
            <div class="w-8 h-8 mx-auto bg-purple-50 text-purple-500 rounded-full flex items-center justify-center mb-2">
                <i class="fab fa-markdown"></i>
            </div>
            <h4 class="text-sm font-bold text-stone-700">Markdown</h4>
            <p class="text-xs text-stone-400 mt-1">支持标准的 Markdown 语法</p>
        </div>
    </div>
</div>
{% endblock %}
```

## 📄 admin/wiki_files.html

```html
{% extends "base.html" %}

{% block title %}媒体库 - {{ wiki.title }}{% endblock %}

{% block sidebar_menu %}
    {% include "wiki/sidebar.html" %}
{% endblock %}

{% block content %}
<div class="fixed inset-0 -z-10 overflow-hidden bg-base-100 pointer-events-none">
    <div class="absolute top-[20%] right-[10%] w-[400px] h-[400px] bg-primary/5 rounded-full blur-[80px] animate-blob mix-blend-multiply opacity-60"></div>
    <div class="absolute bottom-[10%] left-[20%] w-[400px] h-[400px] bg-secondary/5 rounded-full blur-[80px] animate-blob animation-delay-2000 mix-blend-multiply opacity-60"></div>
</div>

<div class="max-w-7xl mx-auto px-4 py-8 animate-fade-in">
    <div class="flex items-center justify-between mb-8">
        <div>
            <h1 class="text-3xl font-black tracking-tight flex items-center gap-2">
                <i class="fas fa-images text-primary/80"></i>
                媒体库
            </h1>
            <p class="text-sm text-base-content/50 mt-1 font-mono">Wiki: {{ wiki.title }} (共 {{ files|length }} 个文件)</p>
        </div>
        <a href="{{ url_for('wiki_detail', wiki_id=wiki.id) }}" class="btn btn-ghost gap-2 group">
            <i class="fas fa-arrow-left group-hover:-translate-x-1 transition-transform"></i>
            返回文档
        </a>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        <div class="lg:col-span-4 lg:sticky lg:top-8 z-10">
            <div class="card bg-base-100/60 backdrop-blur-xl border border-base-content/5 shadow-xl overflow-hidden">
                <div class="card-body p-6">
                    <h2 class="font-bold text-lg mb-4 flex items-center gap-2">
                        <span class="w-2 h-6 bg-primary rounded-full"></span>
                        上传新素材
                    </h2>
                    
                    <div class="form-control w-full">
                        <label for="fileInput" id="dropZone" class="flex flex-col items-center justify-center w-full h-48 border-2 border-dashed border-base-content/20 rounded-2xl cursor-pointer bg-base-50/50 hover:bg-base-100 hover:border-primary transition-all duration-300 group">
                            <div id="uploadPrompt" class="flex flex-col items-center justify-center pt-5 pb-6 text-center">
                                <div class="p-3 bg-base-200 rounded-full mb-3 group-hover:scale-110 transition-transform text-primary">
                                    <i class="fas fa-cloud-upload-alt text-2xl"></i>
                                </div>
                                <p class="mb-1 text-sm font-bold text-base-content/70">点击或拖拽文件至此</p>
                                <p class="text-xs text-base-content/40">支持 JPG, PNG, GIF, WEBP</p>
                            </div>
                            <div id="previewContainer" class="hidden w-full h-full p-2 relative">
                                <img id="imagePreview" class="w-full h-full object-contain rounded-xl" />
                                <div class="absolute inset-0 flex items-center justify-center bg-black/40 rounded-xl opacity-0 hover:opacity-100 transition-opacity">
                                    <span class="text-white text-xs font-bold">点击更换</span>
                                </div>
                            </div>
                            <input type="file" id="fileInput" class="hidden" accept="image/*" onchange="handleFileSelect(this)" />
                        </label>
                    </div>
                    
                    <div class="mt-4 space-y-3">
                        <div id="uploadProgress" class="w-full bg-base-200 rounded-full h-1.5 overflow-hidden hidden">
                            <div id="progressBar" class="bg-primary h-1.5 rounded-full transition-all duration-300" style="width: 0%"></div>
                        </div>

                        <button id="uploadBtn" class="btn btn-primary w-full shadow-lg shadow-primary/20" onclick="uploadFile()" disabled>
                            <i class="fas fa-upload"></i> 开始上传
                        </button>
                    </div>

                    <div class="mt-4 p-3 bg-blue-50/50 text-blue-600 rounded-xl text-xs flex gap-2 items-start border border-blue-100">
                        <i class="fas fa-lightbulb mt-0.5"></i>
                        <span>提示：上传后，鼠标悬停图片即可看到复制按钮。</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="lg:col-span-8">
            {% if files %}
            <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                {% for file in files %}
                <div class="group relative aspect-square rounded-2xl overflow-hidden bg-base-200 border border-base-content/5 shadow-sm hover:shadow-xl transition-all duration-300">
                    
                    <img src="{{ file.file_path }}" alt="{{ file.filename }}" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" loading="lazy" />
                    
                    <div class="absolute top-2 left-2 z-20">
                        <span class="badge badge-xs font-mono bg-black/40 text-white border-none backdrop-blur-md">
                            {{ file.uploaded_at.strftime('%Y-%m-%d') }}
                        </span>
                    </div>

                    <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end">
                        
                        <div class="p-3 bg-gradient-to-t from-black/90 via-black/60 to-transparent translate-y-4 group-hover:translate-y-0 transition-transform duration-300">
                            <div class="mb-3 px-1">
                                <p class="text-xs text-white/90 font-bold truncate" title="{{ file.filename }}">{{ file.filename }}</p>
                                <p class="text-[10px] text-white/60 truncate">by {{ file.uploader.username }}</p>
                            </div>

                            <div class="flex gap-2">
                                <button onclick="copyMdCode('![{{ file.filename }}]({{ file.file_path }})')" class="btn btn-sm btn-primary flex-1 gap-2 shadow-lg border-none text-white font-bold">
                                    <i class="fas fa-link"></i> 复制引用
                                </button>
                                
                                <form action="{{ url_for('delete_wiki_file', wiki_id=wiki.id, file_id=file.id) }}" method="post" onsubmit="return confirm('⚠️ 警告：删除后，所有引用此图片的地方都将失效。\n\n确定要删除吗？');">
                                    <button type="submit" class="btn btn-sm btn-square btn-error bg-red-500 border-none text-white hover:bg-red-600" title="删除文件">
                                        <i class="fas fa-trash-alt"></i>
                                    </button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="flex flex-col items-center justify-center h-96 bg-base-100/50 rounded-3xl border-2 border-dashed border-base-content/10">
                <div class="w-20 h-20 bg-base-200 rounded-full flex items-center justify-center mb-4">
                    <i class="far fa-images text-3xl text-base-content/30"></i>
                </div>
                <h3 class="font-bold text-base-content/60">媒体库为空</h3>
                <p class="text-sm text-base-content/40 mt-1">从左侧上传您的第一张图片</p>
            </div>
            {% endif %}
        </div>
    </div>
</div>

<script>
    // 1. File Selection & Preview Logic
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    const previewContainer = document.getElementById('previewContainer');
    const uploadPrompt = document.getElementById('uploadPrompt');
    const imagePreview = document.getElementById('imagePreview');

    function handleFileSelect(input) {
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                imagePreview.src = e.target.result;
                uploadPrompt.classList.add('hidden');
                previewContainer.classList.remove('hidden');
                uploadBtn.disabled = false;
                uploadBtn.innerHTML = `<i class="fas fa-upload"></i> 确认上传 (${(input.files[0].size / 1024).toFixed(1)} KB)`;
            }
            reader.readAsDataURL(input.files[0]);
        }
    }

    // Drag and Drop Support
    const dropZone = document.getElementById('dropZone');
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('border-primary', 'bg-primary/5'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('border-primary', 'bg-primary/5'), false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;
        handleFileSelect(fileInput);
    }, false);

    // 2. Upload Logic
    async function uploadFile() {
        const file = fileInput.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('image', file);
        const progressBar = document.getElementById('progressBar');
        const progressContainer = document.getElementById('uploadProgress');

        try {
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<span class="loading loading-spinner loading-xs"></span> 上传中...';
            progressContainer.classList.remove('hidden');
            
            progressBar.style.width = '70%';

            const response = await fetch("{{ url_for('upload_wiki_file', wiki_id=wiki.id) }}", {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                progressBar.style.width = '100%';
                setTimeout(() => window.location.reload(), 500);
            } else {
                showGlobalToast(result.error || '上传失败', 'error');
                resetUploadUI();
            }
        } catch (error) {
            console.error('Error:', error);
            showGlobalToast('网络错误', 'error');
            resetUploadUI();
        }

    }

    function resetUploadUI() {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = '<i class="fas fa-upload"></i> 重试上传';
        document.getElementById('uploadProgress').classList.add('hidden');
    }

    // 3. Copy & Toast Logic
    // showToast Removed: Using global showGlobalToast from base.html

    function copyMdCode(code) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(code)
                .then(() => showGlobalToast('已复制 Markdown 引用代码', 'success'))
                .catch(() => showGlobalToast('复制失败', 'error'));
        } else {
            const ta = document.createElement('textarea');
            ta.value = code;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            showGlobalToast('已复制 Markdown 引用代码', 'success');
        }
    }
</script>
{% endblock %}
```

## 📄 admin/manage_announcements.html

```html
{% extends "base.html" %}

{% block title %}系统通知管理{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <div class="flex justify-between items-center mb-8">
        <div>
            <h1 class="text-2xl font-bold text-stone-800">系统通知管理</h1>
            <p class="text-stone-500 mt-1">发布全员通知，查看确认状态</p>
        </div>
        
        <div class="flex gap-2">
            <a href="{{ url_for('manage_announcement_files') }}" class="btn btn-ghost gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                文件管理
            </a>
            <a href="{{ url_for('new_announcement') }}" class="btn btn-primary gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
                发布新通知
            </a>
        </div>
    </div>

    <div class="card bg-base-100 shadow-sm border border-stone-200">
        <div class="overflow-x-auto">
            <table class="table">
                <thead>
                    <tr class="bg-stone-50 text-stone-600">
                        <th>ID</th>
                        <th>标题</th>
                        <th>状态</th>
                        <th>创建者</th>
                        <th>发布时间</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    {% for ann in announcements %}
                    <tr class="hover:bg-stone-50/50">
                        <td class="font-mono text-sm text-stone-400">#{{ ann.id }}</td>
                        <td>
                            <div class="font-medium text-stone-700">{{ ann.title }}</div>
                        </td>
                        <td>
                            {% if ann.is_active %}
                            <div class="badge badge-success badge-outline gap-1">启用</div>
                            {% else %}
                            <div class="badge badge-ghost gap-1">已停用</div>
                            {% endif %}
                        </td>
                        <td class="text-stone-500">{{ ann.creator.username }}</td>
                        <td class="text-stone-500 text-sm">{{ ann.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
                        <td>
                            <div class="flex gap-2">
                                <a href="{{ url_for('announcement_stats', id=ann.id) }}" class="btn btn-xs btn-ghost" title="查看统计">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
                                </a>
                                <a href="{{ url_for('edit_announcement_route', id=ann.id) }}" class="btn btn-xs btn-ghost" title="编辑">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                                </a>
                                <form action="{{ url_for('delete_announcement', id=ann.id) }}" method="post" onsubmit="return confirm('确定要删除吗？确认记录也将被删除');" class="inline">
                                    <button type="submit" class="btn btn-xs btn-ghost text-error" title="删除">
                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                                    </button>
                                </form>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}
```

## 📄 admin/announcement_stats.html

```html
{% extends "base.html" %}

{% block title %}通知统计{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <div class="flex items-center gap-2 mb-8">
        <a href="{{ url_for('manage_announcements') }}" class="btn btn-circle btn-ghost btn-sm">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
        </a>
        <h1 class="text-2xl font-bold text-stone-800">通知统计: {{ announcement.title }}</h1>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <!-- Confirmed Users -->
        <div class="card bg-base-100 shadow-sm border border-stone-200">
            <div class="card-body">
                <h2 class="card-title text-success mb-4">
                    已确认 ({{ confirmed_users|length }})
                </h2>
                <div class="overflow-y-auto max-h-[600px]">
                    <table class="table table-compact w-full">
                        <thead>
                            <tr>
                                <th>用户</th>
                                <th>确认时间</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for user in confirmed_users %}
                            <tr>
                                <td>
                                    <div class="flex items-center gap-2">
                                        <div class="avatar placeholder">
                                            <div class="bg-neutral-focus text-neutral-content rounded-full w-8">
                                                <span class="text-xs">{{ user.username[0]|upper }}</span>
                                            </div>
                                        </div>
                                        <div>
                                            <div class="font-bold">{{ user.username }}</div>
                                            <div class="text-xs opacity-50">{{ user.real_name or '' }}</div>
                                        </div>
                                    </div>
                                </td>
                                <td class="text-sm font-mono text-stone-500">{{ user.confirmed_at.strftime('%Y-%m-%d %H:%M') }}</td>
                            </tr>
                            {% else %}
                            <tr><td colspan="2" class="text-center text-stone-400 py-4">暂无用户确认</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Unconfirmed Users -->
        <div class="card bg-base-100 shadow-sm border border-stone-200">
            <div class="card-body">
                <h2 class="card-title text-warning mb-4">
                    未确认 ({{ unconfirmed_users|length }})
                </h2>
                <div class="overflow-y-auto max-h-[600px]">
                    <table class="table table-compact w-full">
                        <thead>
                            <tr>
                                <th>用户</th>
                                <th>注册时间</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for user in unconfirmed_users %}
                            <tr>
                                <td>
                                    <div class="flex items-center gap-2">
                                        <div class="avatar placeholder">
                                            <div class="bg-stone-200 text-stone-600 rounded-full w-8">
                                                <span class="text-xs">{{ user.username[0]|upper }}</span>
                                            </div>
                                        </div>
                                        <div>
                                            <div class="font-bold">{{ user.username }}</div>
                                            <div class="text-xs opacity-50">{{ user.real_name or '' }}</div>
                                        </div>
                                    </div>
                                </td>
                                <td class="text-sm font-mono text-stone-500">{{ user.created_at.strftime('%Y-%m-%d') }}</td>
                            </tr>
                            {% else %}
                            <tr><td colspan="2" class="text-center text-stone-400 py-4">所有用户已确认</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

## 📄 admin/edit_wiki.html

```html
{% extends "base.html" %}

{% block title %}编辑 Wiki - {{ wiki.title }}{% endblock %}

{% block sidebar_menu %}
    {% include "wiki/sidebar.html" %}
{% endblock %}

{% block content %}
<div class="max-w-4xl mx-auto">
    <div class="flex items-center justify-between mb-8">
        <h1 class="text-3xl font-bold">编辑 Wiki</h1>
        <a href="{{ url_for('wiki_detail', wiki_id=wiki.id) }}" class="btn btn-ghost btn-sm">返回 Wiki</a>
    </div>

    <div class="grid grid-cols-1 gap-8">
        <!-- 编辑表单 -->
        <div class="space-y-6">
            <div class="card bg-base-100 shadow-xl border border-base-200">
                <div class="card-body">
                    <form method="post" class="space-y-4">
                        <div class="form-control w-full">
                            <label class="label">
                                <span class="label-text font-medium">Wiki 标题</span>
                            </label>
                            <input type="text" name="title" class="input input-bordered w-full" value="{{ wiki.title }}" required />
                        </div>
                        
                        <div class="form-control w-full">
                            <label class="label">
                                <span class="label-text font-medium">描述</span>
                            </label>
                            <textarea name="description" class="textarea textarea-bordered h-32" placeholder="简短描述这个 Wiki 的内容...">{{ wiki.description }}</textarea>
                        </div>

                        <!-- Appearance Settings -->
                        <div class="bg-base-200/50 rounded-xl p-4 border border-base-200">
                            <h3 class="text-sm font-bold text-base-content/70 mb-3 flex items-center gap-2">
                                <i class="fas fa-palette text-purple-500"></i> 外观设置
                            </h3>
                            
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div class="form-control">
                                    <label class="label"><span class="label-text font-medium">背景颜色</span></label>
                                    <div class="flex items-center gap-2">
                                        <input type="color" name="bg_color" value="{{ wiki.bg_color or '#ffffff' }}" class="h-10 w-full cursor-pointer rounded-lg border border-base-300 p-1" />
                                    </div>
                                </div>
                                <div class="form-control">
                                    <label class="label"><span class="label-text font-medium">前景/纹理颜色</span></label>
                                    <div class="flex items-center gap-2">
                                        <input type="color" name="fg_color" value="{{ wiki.fg_color or '#1f2937' }}" class="h-10 w-full cursor-pointer rounded-lg border border-base-300 p-1" />
                                    </div>
                                </div>
                            </div>

                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                                <div class="form-control">
                                    <label class="label"><span class="label-text font-medium">渐变颜色 (可选)</span></label>
                                    <div class="flex items-center gap-2">
                                        <input type="color" name="gradient_color" value="{{ wiki.gradient_color or wiki.bg_color or '#ffffff' }}" class="h-10 w-full cursor-pointer rounded-lg border border-base-300 p-1" />
                                    </div>
                                    <p class="text-xs text-base-content/60 mt-1">设置背景渐变的第二种颜色。</p>
                                </div>
                                <div class="form-control">
                                    <label class="label"><span class="label-text font-medium">渐变方向/类型</span></label>
                                    <select name="gradient_direction" class="select select-bordered w-full h-10 min-h-0">
                                        <option value="to bottom right" {% if wiki.gradient_direction == 'to bottom right' %}selected{% endif %}>↘ 右下 (默认)</option>
                                        <option value="to right" {% if wiki.gradient_direction == 'to right' %}selected{% endif %}>→ 向右</option>
                                        <option value="to bottom" {% if wiki.gradient_direction == 'to bottom' %}selected{% endif %}>↓ 向下</option>
                                        <option value="to bottom left" {% if wiki.gradient_direction == 'to bottom left' %}selected{% endif %}>↙ 左下</option>
                                        <option value="to left" {% if wiki.gradient_direction == 'to left' %}selected{% endif %}>← 向左</option>
                                        <option value="to top left" {% if wiki.gradient_direction == 'to top left' %}selected{% endif %}>↖ 左上</option>
                                        <option value="to top" {% if wiki.gradient_direction == 'to top' %}selected{% endif %}>↑ 向上</option>
                                        <option value="to top right" {% if wiki.gradient_direction == 'to top right' %}selected{% endif %}>↗ 右上</option>
                                        <option value="circle at center" {% if wiki.gradient_direction == 'circle at center' %}selected{% endif %}>◉ 径向 (中心)</option>
                                    </select>
                                </div>
                            </div>

                            <div class="form-control mt-4">
                                <label class="label"><span class="label-text font-medium">背景模糊度 (高斯模糊)</span></label>
                                <div class="flex items-center gap-4">
                                    <span class="text-xs text-base-content/60">清晰</span>
                                    <input type="range" name="blur_level" min="0" max="100" step="1" value="{{ wiki.blur_level }}" class="range range-primary range-sm" />
                                    <span class="text-xs text-base-content/60">模糊</span>
                                </div>
                                <p class="text-xs text-base-content/60 mt-2">调整卡片背景的高斯模糊程度。</p>
                            </div>

                            <div class="form-control mt-4">
                                <label class="label"><span class="label-text font-medium">Arc 风格颗粒度</span></label>
                                <div class="flex items-center gap-4">
                                    <span class="text-xs text-base-content/60">细腻</span>
                                    <input type="range" name="pattern" min="0" max="0.3" step="0.01" value="{{ wiki.pattern if wiki.pattern and wiki.pattern[0].isdigit() else '0.05' }}" class="range range-primary range-sm" />
                                    <span class="text-xs text-base-content/60">粗糙</span>
                                </div>
                                <p class="text-xs text-base-content/60 mt-2">调整表面噪点的强度，营造 Arc 浏览器的纸质/磨砂质感。</p>
                            </div>
                        </div>

                        <div class="card-actions justify-end mt-4">
                            <button type="submit" class="btn btn-primary">保存修改</button>
                        </div>
                    </form>
                </div>
            </div>

            <!-- Danger Zone -->
            <div class="card bg-base-100 shadow-xl border border-error/20">
                <div class="card-body">
                    <h2 class="card-title text-error">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        危险区域
                    </h2>
                    <p class="text-sm text-base-content/70">删除 Wiki 是不可逆的操作。所有页面、文件和历史记录都将被删除。但在删除前，系统会自动为您备份数据。</p>
                    <div class="card-actions justify-end mt-4">
                        <button onclick="delete_wiki_modal.showModal()" class="btn btn-error btn-outline">删除 Wiki</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Delete Modal -->
<dialog id="delete_wiki_modal" class="modal">
    <div class="modal-box">
        <h3 class="font-bold text-lg text-error">确认删除 Wiki?</h3>
        <p class="py-4">您确定要删除 <strong>{{ wiki.title }}</strong> 吗？<br>此操作无法撤销。系统将在删除前自动备份数据。</p>
        <div class="modal-action">
            <form method="dialog">
                <button class="btn">取消</button>
            </form>
            <form action="{{ url_for('delete_wiki', wiki_id=wiki.id) }}" method="post">
                <button type="submit" class="btn btn-error">确认删除</button>
            </form>
        </div>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>
{% endblock %}
```

## 📄 admin/manage_users.html

```html
{% extends "base.html" %}

{% block title %}用户管理{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <div class="flex justify-between items-center mb-8">
        <div>
            <h1 class="text-2xl font-bold text-stone-800">用户管理</h1>
            <p class="text-stone-500 mt-1">管理系统用户、导入账号及权限分配</p>
        </div>
        
        <div class="flex gap-2">
            <!-- 导入用户模态框触发按钮 -->
            <button onclick="import_modal.showModal()" class="btn btn-primary gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                导入用户
            </button>
        </div>
    </div>

    <!-- 用户列表 -->
    <div class="card bg-base-100 shadow-sm border border-stone-200">
        <div class="overflow-x-auto">
            <table class="table">
                <thead>
                    <tr class="bg-stone-50 text-stone-600">
                        <th>ID</th>
                        <th>用户名</th>
                        <th>邮箱</th>
                        <th>注册时间</th>
                        <th>角色</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    {% for user in users %}
                    <tr class="hover:bg-stone-50/50">
                        <td class="font-mono text-sm text-stone-400">#{{ user.id }}</td>
                        <td>
                            <div class="font-medium text-stone-700">{{ user.username }}</div>
                        </td>
                        <td class="text-stone-500">{{ user.email }}</td>
                        <td class="text-stone-500 text-sm">{{ user.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
                        <td>
                            {% if user.is_admin %}
                            <div class="badge badge-primary badge-outline gap-1">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
                                管理员
                            </div>
                            {% else %}
                            <div class="badge badge-ghost gap-1">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
                                普通用户
                            </div>
                            {% endif %}
                        </td>
                        <td>
                            {% if user.id != current_user.id %}
                            <div class="dropdown dropdown-left dropdown-end">
                                <label tabindex="0" class="btn btn-ghost btn-xs">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" /></svg>
                                </label>
                                <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-40 border border-stone-100">
                                    <li>
                                        <form action="{{ url_for('update_user_role', user_id=user.id) }}" method="post" class="w-full p-0">
                                            {% if user.is_admin %}
                                            <input type="hidden" name="role" value="user">
                                            <button type="submit" class="w-full text-left px-4 py-2 text-error hover:bg-error/10 rounded-lg">取消管理员</button>
                                            {% else %}
                                            <input type="hidden" name="role" value="admin">
                                            <button type="submit" class="w-full text-left px-4 py-2 text-primary hover:bg-primary/10 rounded-lg">设为管理员</button>
                                            {% endif %}
                                        </form>
                                    </li>
                                </ul>
                            </div>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- 导入用户模态框 -->
<dialog id="import_modal" class="modal">
    <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">导入用户</h3>
        
        <div class="alert alert-info text-sm mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            <div>
                <div class="font-bold">导入说明</div>
                <div class="text-xs">
                    请上传 CSV 或 Excel 文件，包含列：username, password, permission, email, real_name, student_id, department, class_name。<br>
                    其中 permission 填 admin 为管理员，其他为普通用户。
                </div>
            </div>
        </div>

        <form action="{{ url_for('import_users') }}" method="post" enctype="multipart/form-data" class="flex flex-col gap-4">
            <div class="form-control w-full">
                <label class="label">
                    <span class="label-text">选择 CSV / Excel 文件</span>
                    <a href="{{ url_for('download_user_template') }}" class="label-text-alt link link-primary">下载模板</a>
                </label>
                <input type="file" name="file" accept=".csv, .xlsx, .xls" class="file-input file-input-bordered w-full" required />
            </div>
            
            <div class="modal-action">
                <button type="submit" class="btn btn-primary">开始导入</button>
                <button type="button" class="btn" onclick="import_modal.close()">取消</button>
            </div>
        </form>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>
{% endblock %}
```

## 📄 admin/manage_badges.html

```html
{% extends "base.html" %}

{% block title %}徽章管理{% endblock %}

{% block content %}

{# --- 1. 逻辑处理：提取所有存在的分类 --- #}
{% set all_categories = [] %}
{% for badge in badges %}
    {# 如果没有分类，归为'一般' #}
    {% set _ = all_categories.append(badge.category if badge.category else '一般') %}
{% endfor %}
{# 去重 #}
{% set unique_categories = all_categories|unique|list|sort %}

<div class="space-y-8">
    <div class="flex flex-col md:flex-row justify-between items-end md:items-center gap-4">
        <div>
            <h1 class="text-3xl font-bold text-base-content tracking-tight">徽章管理</h1>
            <p class="text-base-content/60 mt-1">创建独特的成就体系，激励用户持续探索</p>
        </div>
        <button onclick="document.getElementById('create_modal').showModal()" class="btn btn-primary shadow-md gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
            新建徽章
        </button>
    </div>

    <div class="stats shadow w-full bg-base-100 border border-base-200">
        <div class="stat">
            <div class="stat-figure text-primary">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="inline-block w-8 h-8 stroke-current"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
            </div>
            <div class="stat-title">徽章总数</div>
            <div class="stat-value" id="total_badge_count">{{ badges|length }}</div>
            <div class="stat-desc">所有已创建的成就</div>
        </div>
        
        <div class="stat">
            <div class="stat-figure text-secondary">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="inline-block w-8 h-8 stroke-current"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>
            </div>
            <div class="stat-title">累计发放</div>
            <div class="stat-value text-secondary">
                {% set ns = namespace(count=0) %}
                {% for b in badges %}{% set ns.count = ns.count + b.issued_count %}{% endfor %}
                {{ ns.count }}
            </div>
            <div class="stat-desc">人次</div>
        </div>
        
        <div class="stat">
            <div class="stat-figure text-accent">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="inline-block w-8 h-8 stroke-current"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
            </div>
            <div class="stat-title">分类数量</div>
            <div class="stat-value text-accent">{{ unique_categories|length }}</div>
            <div class="stat-desc">现有徽章类型</div>
        </div>
    </div>

    {# --- 2. 新增：分类筛选栏 --- #}
    {% if unique_categories %}
    <div class="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-hide">
        <span class="text-sm font-bold text-base-content/50 mr-2 flex-shrink-0">筛选:</span>
        
        <button onclick="filterBadges('all', this)" class="btn btn-sm btn-active filter-btn flex-shrink-0" data-cat="all">
            全部
            <span class="badge badge-xs badge-ghost ml-1">{{ badges|length }}</span>
        </button>

        {% for cat in unique_categories %}
            {# 计算该分类下的数量 #}
            {% set count = badges|selectattr('category', 'equalto', cat)|list|length %}
            {% if not count and cat == '一般' %}
                 {# 处理 category 为 None 的情况 #}
                 {% set count = badges|selectattr('category', 'none')|list|length %}
            {% endif %}
            
            <button onclick="filterBadges('{{ cat }}', this)" class="btn btn-sm btn-ghost filter-btn flex-shrink-0" data-cat="{{ cat }}">
                {{ cat }}
                <span class="badge badge-xs badge-ghost ml-1">{{ count }}</span>
            </button>
        {% endfor %}
    </div>
    {% endif %}

    {% if badges %}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6" id="badge_grid">
            {% for badge in badges %}
            
            {# --- 3. 核心修改：增加 data-category 属性 --- #}
            <div class="card bg-base-100 shadow-sm border border-base-200 hover:shadow-md transition-shadow group relative badge-card" 
                 data-category="{{ badge.category or '一般' }}">
                 
                {% if badge.is_hidden %}
                <div class="absolute top-2 right-2 badge badge-warning badge-sm gap-1 z-10 opacity-80">
                    隐藏
                </div>
                {% endif %}

                <div class="card-body p-5 items-center text-center">
                    <div class="w-16 h-16 mb-2 flex items-center justify-center rounded-full bg-base-200/50 group-hover:scale-110 transition-transform duration-300">
                        {% set _icon = badge.icon %}
                        {% if _icon|is_image_icon %}
                            <img src="{{ _icon|badge_icon_url }}" class="w-12 h-12 object-contain drop-shadow-sm" alt="{{ badge.name }}">
                        {% else %}
                            <span class="text-4xl filter drop-shadow-sm">{{ _icon }}</span>
                        {% endif %}
                    </div>

                    <h2 class="card-title text-base-content">{{ badge.name }}</h2>
                    <div class="badge badge-outline badge-sm text-xs opacity-70 mb-2">{{ badge.category or '一般' }}</div>
                    <p class="text-sm text-base-content/60 line-clamp-2 h-10 w-full">{{ badge.description }}</p>

                    <div class="w-full grid grid-cols-2 gap-2 my-3 text-xs text-base-content/70 bg-base-200/30 p-2 rounded-lg">
                        <div class="flex flex-col">
                            <span class="opacity-50 text-[10px] uppercase">获得人数</span>
                            <span class="font-bold">{{ badge.issued_count }}</span>
                        </div>
                        <div class="flex flex-col">
                            <span class="opacity-50 text-[10px] uppercase">限量</span>
                            <span class="font-bold {{ 'text-warning' if badge.total_limit else '' }}">
                                {{ badge.total_limit if badge.total_limit is not none else '∞' }}
                            </span>
                        </div>
                    </div>

                    <div class="w-full flex justify-between items-center text-xs px-1 mb-4">
                        <span class="flex items-center gap-1" title="触发条件">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                            <span class="font-mono opacity-80">{{ badge.condition_type }}</span>
                        </span>
                        <span class="flex items-center gap-1" title="贴纸奖励">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" /></svg>
                            x{{ badge.sticker_count }}
                        </span>
                    </div>

                    <div class="card-actions w-full justify-between items-center pt-2 border-t border-base-200">
                        <div class="flex gap-2">
                            <a href="{{ url_for('edit_badge', badge_id=badge.id) }}" class="btn btn-xs btn-ghost tooltip" data-tip="编辑">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                            </a>
                            <form method="post" action="{{ url_for('delete_badge', badge_id=badge.id) }}" onsubmit="return confirm('确定要删除这个徽章吗？此操作无法撤销。')">
                                <button type="submit" class="btn btn-xs btn-ghost text-error tooltip" data-tip="删除">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                                </button>
                            </form>
                        </div>
                        
                        {% if badge.condition_type == 'manual' %}
                        <button onclick="openAwardModal({{ badge.id }}, '{{ badge.name }}')" class="btn btn-xs btn-primary">手动发放</button>
                        {% endif %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <div id="no_filter_results" class="hidden py-12 text-center bg-base-100 border border-base-200 rounded-lg border-dashed">
            <p class="text-base-content/40">该分类下暂无徽章</p>
        </div>
        
    {% else %}
        <div class="hero bg-base-100 rounded-box border border-base-200 py-12">
            <div class="hero-content text-center">
                <div class="max-w-md">
                    <div class="text-6xl mb-4">🏆</div>
                    <h1 class="text-2xl font-bold">暂无徽章</h1>
                    <p class="py-6 text-base-content/60">目前还没有创建任何徽章。创建一个新徽章来开始激励您的用户吧！</p>
                    <button onclick="document.getElementById('create_modal').showModal()" class="btn btn-primary">创建第一个徽章</button>
                </div>
            </div>
        </div>
    {% endif %}
</div>

{% include "admin/partials/badge_modals.html" ignore missing %}
{# 注意：因为没有分文件，这里直接复制你原来文件底部的 Modal 代码即可，为了简洁我略过了 Modal 部分的重复代码，请保留你原有的 Modal 代码 #}

<dialog id="create_modal" class="modal modal-bottom sm:modal-middle">
    <div class="modal-box w-11/12 max-w-2xl">
        <form method="dialog">
            <button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">✕</button>
        </form>
        
        <h3 class="font-bold text-lg mb-6 flex items-center gap-2">
            <span class="w-1 h-6 bg-primary rounded-full"></span>
            新建徽章
        </h3>
        
        <form method="post" class="flex flex-col gap-5" enctype="multipart/form-data">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="form-control">
                    <label class="label"><span class="label-text font-medium">徽章名称</span></label>
                    <input type="text" name="name" class="input input-bordered" placeholder="例如：阅读达人" required />
                </div>
                <div class="form-control">
                    <label class="label"><span class="label-text font-medium">分类标签</span></label>
                    <input type="text" name="category" class="input input-bordered" value="一般" list="category-list" />
                    <datalist id="category-list">
                        <option value="一般"><option value="学习"><option value="社交"><option value="创作"><option value="活动">
                    </datalist>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="form-control">
                    <label class="label"><span class="label-text font-medium">稀有度</span></label>
                    <select name="rarity" class="select select-bordered w-full">
                        <option value="common" selected>Common (普通)</option>
                        <option value="rare">Rare (稀有)</option>
                        <option value="epic">Epic (史诗)</option>
                        <option value="legendary">Legendary (传说)</option>
                    </select>
                </div>
                <div class="form-control">
                    <label class="label"><span class="label-text font-medium">神秘成就</span></label>
                    <label class="label cursor-pointer justify-start gap-3 bg-base-100 border border-base-200 p-3 rounded-lg">
                        <input type="checkbox" name="is_secret" class="checkbox checkbox-secondary" />
                        <span class="label-text">未解锁时完全保密 (???)</span>
                    </label>
                </div>
            </div>

            <div class="form-control">
                <label class="label"><span class="label-text font-medium">图标</span></label>
                <input type="file" name="icon_file" accept="image/*" class="file-input file-input-bordered w-full" required />
                <label class="label"><span class="label-text-alt text-base-content/50">支持 PNG, JPG, GIF, WebP</span></label>
            </div>

            <div class="form-control">
                <label class="label"><span class="label-text font-medium">描述</span></label>
                <textarea name="description" class="textarea textarea-bordered h-20" placeholder="简单描述获取条件或徽章含义"></textarea>
            </div>

            <div class="divider text-xs text-base-content/30 my-0">规则设置</div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 bg-base-200/50 p-4 rounded-lg">
                <div class="form-control md:col-span-2">
                    <label class="label"><span class="label-text font-medium">触发条件类型</span></label>
                    <select name="condition_type" class="select select-bordered w-full" required onchange="toggleConditionInputs(this)">
                        <option value="manual">手动发放 (管理员分配)</option>
                        <option value="all_users">全员获取 (新老用户)</option>
                        <option value="login_days_in_range">限时登录天数 (指定时间段内)</option>
                        <option value="streak_days">连续打卡天数</option>
                        <option value="study_hours">累计学习小时数</option>
                        <option value="note_count">累计笔记数量</option>
                        <option value="featured_count">累计精选笔记数量</option>
                        <option value="wiki_edit_count">Wiki 编辑次数</option>
                        <option value="wiki_create_count">Wiki 创建次数</option>
                        <option value="comment_count">评论发布数量</option>
                        <option value="share_count">分享笔记次数</option>
                        <option value="total_views_received">笔记被阅读次数 (影响力)</option>
                        <option value="night_owl_sessions">深夜学习天数 (23:00-04:00)</option>
                        <option value="early_bird">早起鸟 (05:00-08:00)</option>
                        <option value="weekend_warrior">周末卷王 (周六日累计小时)</option>
                        <option value="long_session_count">深度专注次数 (单次>2小时)</option>
                    </select>
                </div>

                <div class="form-control" id="condition_value_group">
                    <label class="label"><span class="label-text font-medium">条件阈值</span></label>
                    <div class="join">
                        <input type="number" name="condition_value" class="input input-bordered join-item w-full" placeholder="0" />
                        <span class="btn btn-disabled join-item text-xs font-normal">次/天/个</span>
                    </div>
                </div>

                <div class="form-control">
                    <label class="label"><span class="label-text font-medium">条件描述（可选）</span></label>
                    <input type="text" name="custom_condition_text" class="input input-bordered" placeholder="例如：连续7天早起打卡" />
                    <label class="label"><span class="label-text-alt">如果填写，将在成就卡片上优先显示此文本，否则自动生成</span></label>
                </div>

                <div class="form-control">
                    <label class="label"><span class="label-text font-medium">贴纸奖励</span></label>
                    <input type="number" name="sticker_count" class="input input-bordered" value="1" min="1" />
                </div>

                <div class="form-control">
                    <label class="label">
                        <span class="label-text font-medium">发行限量</span>
                        <span class="tooltip tooltip-right" data-tip="留空表示无限量"><span class="badge badge-xs badge-ghost">?</span></span>
                    </label>
                    <input type="number" name="total_limit" class="input input-bordered" placeholder="∞" />
                </div>

                <div class="form-control">
                    <label class="label cursor-pointer justify-start gap-3 mt-4">
                        <input type="checkbox" name="is_hidden" class="checkbox checkbox-warning" />
                        <span class="label-text font-medium">作为隐藏成就</span>
                    </label>
                </div>

                <div class="form-control md:col-span-2 hidden" id="time_range_group">
                    <label class="label"><span class="label-text font-medium">有效时间范围</span></label>
                    <div class="flex gap-2">
                        <input type="date" name="start_time" class="input input-bordered w-1/2" />
                        <span class="self-center">-</span>
                        <input type="date" name="end_time" class="input input-bordered w-1/2" />
                    </div>
                </div>
            </div>

            <div class="modal-action">
                <button type="submit" class="btn btn-primary px-8">立即创建</button>
            </div>
        </form>
    </div>
</dialog>

<dialog id="award_modal" class="modal">
  <div class="modal-box w-11/12 max-w-lg h-[600px] flex flex-col">
    <div class="flex justify-between items-center mb-4">
        <h3 class="font-bold text-lg">发放徽章: <span id="award_badge_name" class="text-primary"></span></h3>
        <form method="dialog"><button class="btn btn-sm btn-circle btn-ghost">✕</button></form>
    </div>
    
    <div class="form-control mb-4">
        <div class="input-group">
            <span class="bg-base-200 px-3 flex items-center border border-r-0 border-base-300 rounded-l-lg">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
            </span>
            <input type="text" id="user_search" class="input input-bordered w-full" placeholder="搜索用户名..." onkeyup="filterUsers()">
        </div>
    </div>

    <p class="text-sm text-base-content/60 mb-2">请勾选要发放的用户：</p>
    
    <div class="flex-1 overflow-y-auto border border-base-300 rounded-lg p-2 bg-base-100 shadow-inner" id="user_list_container">
        {% for user in users %}
        <label class="label cursor-pointer justify-start gap-3 hover:bg-base-200 rounded p-2 transition-colors user-row">
            <input type="checkbox" class="checkbox checkbox-primary user-checkbox" value="{{ user.id }}" />
            <div class="flex flex-col">
                <span class="label-text font-medium user-name">{{ user.username }}</span>
                <span class="text-xs text-base-content/40">{{ user.email }}</span>
            </div>
        </label>
        {% endfor %}
        <div id="no_users_msg" class="hidden text-center py-8 text-base-content/40">没有找到匹配的用户</div>
    </div>

    <div class="modal-action border-t border-base-200 pt-4 mt-0">
        <div class="flex-1 text-sm self-center text-base-content/50">已选 <span id="selected_count">0</span> 人</div>
        <button class="btn" onclick="document.getElementById('award_modal').close()">取消</button>
        <button class="btn btn-primary" onclick="submitAward()">确认发放</button>
    </div>
  </div>
</dialog>

{% endblock %}

{% block scripts %}
<script>
// --- 新增：前端筛选逻辑 ---
function filterBadges(category, btnElement) {
    const cards = document.querySelectorAll('.badge-card');
    const btns = document.querySelectorAll('.filter-btn');
    const emptyMsg = document.getElementById('no_filter_results');
    let visibleCount = 0;

    // 1. 更新按钮状态
    btns.forEach(btn => {
        if (btn === btnElement) {
            btn.classList.remove('btn-ghost');
            btn.classList.add('btn-active');
        } else {
            btn.classList.add('btn-ghost');
            btn.classList.remove('btn-active');
        }
    });

    // 2. 筛选卡片
    cards.forEach(card => {
        const cardCat = card.getAttribute('data-category');
        if (category === 'all' || cardCat === category) {
            card.style.display = ''; // 恢复 Grid 默认布局 (block/flex等)
            // 添加淡入动画效果
            card.classList.add('animate-fade-in');
            setTimeout(() => card.classList.remove('animate-fade-in'), 500);
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });

    // 3. 处理空状态
    if (visibleCount === 0) {
        emptyMsg.classList.remove('hidden');
    } else {
        emptyMsg.classList.add('hidden');
    }
}

// 保留原有的 Modal 逻辑
function toggleConditionInputs(select) {
    const val = select.value;
    const timeGroup = document.getElementById('time_range_group');
    const valueGroup = document.getElementById('condition_value_group');
    
    if (val === 'login_days_in_range') {
        timeGroup.classList.remove('hidden');
        valueGroup.classList.remove('hidden');
    } else if (val === 'all_users' || val === 'manual') {
        timeGroup.classList.add('hidden');
        valueGroup.classList.add('hidden');
    } else {
        timeGroup.classList.add('hidden');
        valueGroup.classList.remove('hidden');
    }
}

let currentBadgeId = null;

function openAwardModal(badgeId, badgeName) {
    currentBadgeId = badgeId;
    document.getElementById('award_badge_name').innerText = badgeName;
    document.getElementById('user_search').value = '';
    filterUsers();
    document.querySelectorAll('.user-checkbox').forEach(cb => cb.checked = false);
    updateSelectedCount();
    document.getElementById('award_modal').showModal();
}

function filterUsers() {
    const input = document.getElementById('user_search');
    const filter = input.value.toLowerCase();
    const rows = document.getElementsByClassName('user-row');
    let hasVisible = false;

    for (let i = 0; i < rows.length; i++) {
        const nameSpan = rows[i].querySelector('.user-name');
        const txtValue = nameSpan.textContent || nameSpan.innerText;
        if (txtValue.toLowerCase().indexOf(filter) > -1) {
            rows[i].style.display = "";
            hasVisible = true;
        } else {
            rows[i].style.display = "none";
        }
    }
    document.getElementById('no_users_msg').style.display = hasVisible ? 'none' : 'block';
}

document.getElementById('user_list_container').addEventListener('change', function(e) {
    if (e.target.classList.contains('user-checkbox')) {
        updateSelectedCount();
    }
});

function updateSelectedCount() {
    const count = document.querySelectorAll('.user-checkbox:checked').length;
    document.getElementById('selected_count').innerText = count;
}

async function submitAward() {
    if (!currentBadgeId) return;
    const selectedUsers = Array.from(document.querySelectorAll('.user-checkbox:checked')).map(cb => cb.value);
    
    if (!selectedUsers.length) {
        alert('请至少选择一个用户');
        return;
    }
    
    const btn = document.querySelector('#award_modal .btn-primary');
    const originalText = btn.innerText;
    btn.setAttribute('disabled', 'disabled');
    btn.innerText = '发放中...';
    
    try {
        const res = await fetch(`/admin/badges/${currentBadgeId}/award`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_ids: selectedUsers })
        });
        const data = await res.json();
        
        if (data.success) {
            document.getElementById('award_modal').close();
            alert(`✅ 成功发放给 ${data.count} 位用户`);
            location.reload();
        } else {
            alert('❌ ' + (data.error || '发放失败'));
        }
    } catch (e) {
        alert('❌ 网络或服务器错误');
    } finally {
        btn.removeAttribute('disabled');
        btn.innerText = originalText;
    }
}
</script>

<style>
/* 简单的淡入动画 */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in {
    animation: fadeIn 0.3s ease-out forwards;
}
/* 隐藏滚动条但保留功能 */
.scrollbar-hide::-webkit-scrollbar {
    display: none;
}
.scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
}
</style>
{% endblock %}
```

## 📄 admin/manage_editors.html

```html
{% extends "base.html" %}

{% block sidebar_menu %}
    {% include "wiki/sidebar.html" %}
{% endblock %}

{% block content %}
<div class="max-w-2xl mx-auto card bg-base-100 shadow">
  <div class="card-body">
    <div class="flex items-center justify-between mb-4">
        <h2 class="card-title">编辑授权 - {{ wiki.title }}</h2>
        <a href="{{ url_for('wiki_detail', wiki_id=wiki.id) }}" class="btn btn-ghost btn-sm">返回 Wiki</a>
    </div>
    <form method="post" class="flex items-center gap-2 mb-8">
      <input class="input input-bordered w-full" name="username" placeholder="输入用户名以添加编辑者..." required>
      <button class="btn btn-primary whitespace-nowrap" type="submit">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
        添加
      </button>
    </form>
    
    <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-base-content/70" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
        当前编辑者 ({{ editors|length }})
    </h3>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      {% for user in editors %}
      <div class="card bg-base-200 border border-base-300 compact">
        <div class="card-body flex-row items-center justify-between p-4">
            <div class="flex items-center gap-3 overflow-hidden">
                <div class="avatar placeholder">
                    <div class="bg-neutral text-neutral-content rounded-full w-10">
                        <span class="text-lg">{{ user.username[0]|upper }}</span>
                    </div>
                </div>
                <div class="flex flex-col min-w-0">
                    <span class="font-bold truncate">{{ user.username }}</span>
                    <span class="text-xs text-base-content/60 truncate">{{ user.email }}</span>
                </div>
            </div>
            
            {% if user.id != wiki.created_by_id %}
            <form action="{{ url_for('remove_editor', wiki_id=wiki.id, user_id=user.id) }}" method="post" onsubmit="return confirm('确定要移除该用户的编辑权限吗？');">
                <button type="submit" class="btn btn-ghost btn-square btn-sm text-error hover:bg-error/10" title="移除权限">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
            </form>
            {% else %}
            <div class="badge badge-sm badge-ghost" title="创建者不可移除">创建者</div>
            {% endif %}
        </div>
      </div>
      {% else %}
      <div class="col-span-full text-center py-12 text-base-content/40 bg-base-200/50 rounded-lg border border-dashed border-base-300">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-2 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
          <p>暂无其他编辑者</p>
      </div>
      {% endfor %}
    </div>
  </div>
</div>
{% endblock %}
```

## 📄 admin/wiki_stats.html

```html
{% extends "base.html" %}

{% block sidebar_menu %}
    {% include "wiki/sidebar.html" %}
{% endblock %}

{% block content %}
<div class="max-w-7xl mx-auto space-y-6">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-3xl font-bold text-stone-800">Wiki 数据统计</h1>
            <p class="text-stone-500 mt-2">
                <span class="font-bold">{{ wiki.title }}</span> 的订阅与浏览情况
            </p>
        </div>
        <a href="{{ url_for('wiki_detail', wiki_id=wiki.id) }}" class="btn btn-ghost btn-sm">返回 Wiki</a>
    </div>

    <div class="card bg-base-100 shadow-sm border border-stone-100">
        <div class="card-body">
            <h2 class="card-title text-stone-700 mb-4 flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" /></svg>
                最近 14 天浏览趋势
            </h2>
            <div class="w-full h-64">
                <canvas id="viewsChart"></canvas>
            </div>
        </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="card bg-base-100 shadow-sm border border-stone-100">
            <div class="card-body">
                <h2 class="card-title text-stone-700 mb-4 flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                    详细浏览次数
                </h2>
                <div class="overflow-x-auto">
                    <table class="table table-zebra w-full table-sm">
                        <thead>
                            <tr>
                                <th>时间范围</th>
                                <th class="text-right">浏览量</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td>过去 1 小时</td><td class="text-right font-mono">{{ view_stats['1h'] }}</td></tr>
                            <tr><td>过去 12 小时</td><td class="text-right font-mono">{{ view_stats['12h'] }}</td></tr>
                            <tr><td>过去 24 小时</td><td class="text-right font-mono">{{ view_stats['1d'] }}</td></tr>
                            <tr><td>过去 7 天</td><td class="text-right font-mono">{{ view_stats['1w'] }}</td></tr>
                            <tr><td>过去 30 天</td><td class="text-right font-mono">{{ view_stats['1m'] }}</td></tr>
                            <tr><td>过去 90 天</td><td class="text-right font-mono">{{ view_stats['3m'] }}</td></tr>
                            <tr><td>过去 180 天</td><td class="text-right font-mono">{{ view_stats['6m'] }}</td></tr>
                            <tr><td>过去 1 年</td><td class="text-right font-mono">{{ view_stats['1y'] }}</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="card bg-base-100 shadow-sm border border-stone-100">
            <div class="card-body">
                <h2 class="card-title text-stone-700 mb-4 flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
                    新增订阅人数
                </h2>
                <div class="overflow-x-auto">
                    <table class="table table-zebra w-full table-sm">
                        <thead>
                            <tr>
                                <th>时间范围</th>
                                <th class="text-right">新增人数</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td>过去 1 小时</td><td class="text-right font-mono">{{ sub_stats['1h'] }}</td></tr>
                            <tr><td>过去 12 小时</td><td class="text-right font-mono">{{ sub_stats['12h'] }}</td></tr>
                            <tr><td>过去 24 小时</td><td class="text-right font-mono">{{ sub_stats['1d'] }}</td></tr>
                            <tr><td>过去 7 天</td><td class="text-right font-mono">{{ sub_stats['1w'] }}</td></tr>
                            <tr><td>过去 30 天</td><td class="text-right font-mono">{{ sub_stats['1m'] }}</td></tr>
                            <tr><td>过去 90 天</td><td class="text-right font-mono">{{ sub_stats['3m'] }}</td></tr>
                            <tr><td>过去 180 天</td><td class="text-right font-mono">{{ sub_stats['6m'] }}</td></tr>
                            <tr><td>过去 1 年</td><td class="text-right font-mono">{{ sub_stats['1y'] }}</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <div class="card bg-base-100 shadow-sm border border-stone-100">
        <div class="card-body">
            <h2 class="card-title text-stone-700 mb-4 flex items-center justify-between">
                <div class="flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
                    当前订阅用户列表
                </div>
                <div class="badge badge-lg">{{ subscribers|length }} 人</div>
            </h2>
            
            {% if subscribers %}
            <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {% for user in subscribers %}
                <div class="flex items-center gap-3 p-3 bg-base-200 rounded-lg hover:bg-base-300 transition-colors">
                    <div class="avatar placeholder">
                        <div class="bg-neutral text-neutral-content rounded-full w-8">
                            <span class="text-xs">{{ user.username[0]|upper }}</span>
                        </div>
                    </div>
                    <div class="flex flex-col min-w-0">
                        <span class="font-bold truncate text-sm" title="{{ user.username }}">{{ user.username }}</span>
                        <span class="text-xs text-stone-500 truncate" title="{{ user.email }}">{{ user.email }}</span>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="text-center py-8 text-stone-400">
                暂无订阅用户
            </div>
            {% endif %}
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
    document.addEventListener('DOMContentLoaded', function() {
        const ctx = document.getElementById('viewsChart').getContext('2d');
        
        // 从后端获取的数据
        const labels = {{ chart_labels | tojson }};
        const data = {{ chart_data | tojson }};

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '每日浏览量',
                    data: data,
                    borderColor: '#ea580c', // Orange-600 (primary color)
                    backgroundColor: 'rgba(234, 88, 12, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3, // 平滑曲线
                    pointBackgroundColor: '#fff',
                    pointBorderColor: '#ea580c',
                    pointHoverBackgroundColor: '#ea580c',
                    pointHoverBorderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(255, 255, 255, 0.9)',
                        titleColor: '#1c1917',
                        bodyColor: '#57534e',
                        borderColor: '#e7e5e4',
                        borderWidth: 1,
                        padding: 10
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: '#f5f5f4'
                        },
                        ticks: {
                            precision: 0 // 只显示整数
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    });
</script>
{% endblock %}
```

## 📄 admin/markdown_css.html

```html
{% extends "base.html" %}
{% block content %}
<div class="max-w-3xl mx-auto card bg-base-100 shadow">
  <div class="card-body">
    <h2 class="card-title">编辑Markdown样式</h2>
    <p class="text-base-content/70">选择器兼容Typora（如 .typora-export, .markdown-body 等）。</p>
    <form method="post" class="flex flex-col gap-4">
      <textarea class="textarea textarea-bordered min-h-96 font-mono" name="css_text" placeholder="CSS">{{ css_text }}</textarea>
      <button class="btn btn-primary" type="submit">保存</button>
    </form>
    <div class="mt-4">
      <a class="btn btn-outline" href="{{ url_for('index') }}">返回首页</a>
    </div>
  </div>
</div>
{% endblock %}
```

## 📄 admin/edit_announcement.html

```html
{% extends "base.html" %}

{% block title %}{% if announcement %}编辑通知{% else %}发布新通知{% endif %}{% endblock %}

{% block content %}
<div class="max-w-4xl mx-auto card bg-base-100 shadow border border-stone-200">
  <div class="card-body">
    <h2 class="card-title text-2xl mb-4">{% if announcement %}编辑通知{% else %}发布新通知{% endif %}</h2>
    <form method="post" class="flex flex-col gap-6">
      <div class="form-control">
          <label class="label">
              <span class="label-text font-bold">通知标题</span>
          </label>
          <input class="input input-bordered w-full" name="title" value="{{ announcement.title if announcement else '' }}" placeholder="输入标题" required>
      </div>
      
      {% if announcement %}
      <div class="form-control">
        <label class="label cursor-pointer justify-start gap-4">
          <span class="label-text font-bold">状态</span> 
          <input type="checkbox" name="is_active" class="toggle toggle-success" {% if announcement.is_active %}checked{% endif %} />
          <span class="label-text text-stone-500">启用 (停用后用户无法看到)</span>
        </label>
      </div>
      {% endif %}

      <div class="form-control">
          <label class="label">
              <span class="label-text font-bold">通知内容</span>
          </label>
          <textarea id="md-editor" name="content" placeholder="输入Markdown内容">{{ announcement.content if announcement else '' }}</textarea>
      </div>
      
      <div class="flex justify-between items-center mt-4">
          <button class="btn btn-primary px-8" type="submit">{% if announcement %}保存更新{% else %}立即发布{% endif %}</button>
          <a class="btn btn-ghost" href="{{ url_for('manage_announcements') }}">返回列表</a>
      </div>
    </form>
  </div>
</div>
{% endblock %}

{% block scripts %}
<script>
  const easyMDE = new EasyMDE({
    element: document.getElementById('md-editor'),
    minHeight: "400px",
    uploadImage: true,
    imageUploadEndpoint: "{{ url_for('upload_file') }}",
    imagePathAbsolute: true,
    imageMaxSize: 1024 * 1024 * 16, // 16MB
    imageAccept: "image/png, image/jpeg, image/gif, image/webp",
    imageTexts: {
        sbInit: "拖拽图片到这里或点击上传",
        sbOnDragEnter: "松开上传",
        sbOnDragLeave: "拖拽图片到这里或点击上传",
        sbProgress: "上传中...",
        sbOnUploaded: "上传成功",
        sizeUnits: "b,kb,mb"
    },
    errorCallback: function(errorMessage) {
        alert("上传失败: " + errorMessage);
    }
  });
</script>
{% endblock %}
```

## 📄 admin/announcement_files.html

```html
{% extends "base.html" %}

{% block title %}通知文件管理{% endblock %}

{% block content %}
<div class="max-w-7xl mx-auto px-4 py-8">
    <div class="flex items-center justify-between mb-8">
        <h1 class="text-3xl font-bold text-stone-800">通知文件管理</h1>
        <a href="{{ url_for('manage_announcements') }}" class="btn btn-ghost btn-sm">返回通知列表</a>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- 上传区域 -->
        <div class="lg:col-span-1 space-y-6">
            <div class="card bg-base-100 shadow-xl border border-stone-200">
                <div class="card-body">
                    <h2 class="card-title text-lg mb-4">上传新文件</h2>
                    
                    <div class="form-control w-full">
                        <input type="file" id="fileInput" class="file-input file-input-bordered w-full" accept="image/*" />
                    </div>
                    
                    <button id="uploadBtn" class="btn btn-secondary w-full mt-4" onclick="uploadFile()">
                        上传文件
                    </button>
                    
                    <div id="uploadProgress" class="hidden w-full bg-stone-200 rounded-full h-2.5 mt-4">
                        <div class="bg-blue-600 h-2.5 rounded-full" style="width: 0%"></div>
                    </div>

                    <div class="alert alert-info shadow-sm text-sm mt-4 bg-blue-50 text-blue-800 border-blue-100">
                        <div>
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current flex-shrink-0 w-6 h-6"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                            <span>支持 JPG, PNG, GIF, WEBP 格式图片。上传后点击右侧"引用"即可在通知中使用。</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 文件列表 -->
        <div class="lg:col-span-2">
            <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                {% for file in files %}
                <div class="card bg-base-100 shadow-sm border border-stone-200 group">
                    <figure class="px-4 pt-4 bg-stone-100 h-32 flex items-center justify-center relative overflow-hidden rounded-t-xl">
                        <img src="{{ file.file_path }}" alt="{{ file.filename }}" class="max-h-full max-w-full object-contain transition-transform group-hover:scale-105" />
                        <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                            <a href="{{ file.file_path }}" target="_blank" class="btn btn-circle btn-sm btn-ghost text-white" title="查看原图">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                            </a>
                        </div>
                    </figure>
                    <div class="card-body p-4">
                        <h3 class="font-bold text-sm truncate mb-1 text-stone-700" title="{{ file.filename }}">{{ file.filename }}</h3>
                        <p class="text-xs text-stone-400 mb-3">
                            {{ file.uploaded_at.strftime('%Y-%m-%d') }} by {{ file.uploader.username }}
                        </p>
                        
                        <div class="flex items-center justify-between">
                            <button type="button" class="btn btn-xs btn-outline btn-primary gap-1" onclick="copyMdCode('![{{ file.filename }}]({{ file.file_path }})')">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" /></svg>
                                引用
                            </button>
                            
                            <form action="{{ url_for('delete_announcement_file', file_id=file.id) }}" method="post" onsubmit="return confirm('确定要删除这个文件吗？引用该文件的通知可能会显示错误。');">
                                <button type="submit" class="btn btn-xs btn-ghost text-error" title="删除">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
                {% else %}
                <div class="col-span-full text-center py-12 text-stone-400 bg-stone-50 rounded-lg border border-dashed border-stone-300">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-2 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                    <p>暂无文件，请从左侧上传</p>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</div>

<script>
async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('请先选择文件');
        return;
    }

    const formData = new FormData();
    formData.append('image', file);

    try {
        uploadBtn.disabled = true;
        uploadBtn.textContent = '上传中...';
        
        const response = await fetch("{{ url_for('upload_announcement_file') }}", {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Reload page to show new file
            window.location.reload();
        } else {
            alert('上传失败: ' + (result.error || '未知错误'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('上传出错，请重试');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = '上传文件';
    }
}

function copyMdCode(code) {
    // Helper to show toast
    const showToast = () => {
        const toast = document.createElement('div');
        toast.className = 'toast toast-top toast-center z-50';
        toast.innerHTML = `
            <div class="alert alert-success">
                <span>已复制引用代码！</span>
            </div>
        `;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.remove();
        }, 2000);
    };

    // Try modern API first
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(code)
            .then(showToast)
            .catch(err => {
                console.error('Clipboard API failed:', err);
                fallbackCopy(code, showToast);
            });
    } else {
        fallbackCopy(code, showToast);
    }
}

function fallbackCopy(text, onSuccess) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    
    // Ensure textarea is not visible but part of DOM
    textarea.style.position = 'fixed';
    textarea.style.left = '-9999px';
    textarea.style.top = '0';
    document.body.appendChild(textarea);
    
    textarea.focus();
    textarea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            onSuccess();
        } else {
            alert('复制失败，请手动复制: ' + text);
        }
    } catch (err) {
        console.error('Fallback copy failed:', err);
        alert('复制失败，请手动复制: ' + text);
    }
    
    document.body.removeChild(textarea);
}
</script>
{% endblock %}
```

## 📄 admin/edit_badge.html

```html
{% extends "base.html" %}

{% block title %}编辑徽章 - {{ badge.name }}{% endblock %}

{% block content %}
<div class="max-w-5xl mx-auto">
    <div class="text-sm breadcrumbs mb-4 text-base-content/60">
        <ul>
            <li><a href="{{ url_for('manage_badges') }}">徽章管理</a></li>
            <li>编辑徽章</li>
            <li class="font-bold">{{ badge.name }}</li>
        </ul>
    </div>

    <form method="post" enctype="multipart/form-data" class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        <div class="lg:col-span-1 space-y-6">
            <div class="card bg-base-100 shadow-sm border border-base-200">
                <div class="card-body items-center text-center">
                    <h3 class="card-title text-sm opacity-60 uppercase mb-4">视觉外观</h3>
                    
                    <div class="relative group cursor-pointer" onclick="document.getElementById('icon_upload').click()">
                        <div class="avatar placeholder">
                            <div class="w-32 h-32 rounded-full bg-base-200 ring ring-base-200 ring-offset-base-100 ring-offset-2 overflow-hidden">
                                <img id="icon_preview" src="{{ badge.icon|badge_icon_url }}" class="object-contain w-full h-full p-4 transition-opacity duration-300" />
                            </div>
                        </div>
                        <div class="absolute inset-0 flex items-center justify-center bg-black/50 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                            <span class="text-sm font-bold">点击更换</span>
                        </div>
                    </div>
                    <input type="file" id="icon_upload" name="icon_file" accept="image/*" class="hidden" onchange="previewImage(this)" />
                    <p class="text-xs text-base-content/40 mt-2">支持 JPG, PNG, GIF, WebP</p>

                    <div class="divider my-2"></div>

                    <div class="form-control w-full">
                        <label class="label"><span class="label-text font-medium">徽章名称</span></label>
                        <input type="text" name="name" class="input input-bordered w-full text-center font-bold" value="{{ badge.name }}" required />
                    </div>

                    <div class="form-control w-full">
                    <label class="label"><span class="label-text font-medium">分类标签</span></label>
                    <input type="text" name="category" class="input input-bordered w-full text-center" value="{{ badge.category or '一般' }}" list="category-list" />
                    <datalist id="category-list">
                        <option value="一般"><option value="学习"><option value="社交"><option value="创作"><option value="活动">
                    </datalist>
                </div>
                
                <div class="divider my-2"></div>
                
                <div class="form-control w-full">
                    <label class="label"><span class="label-text font-medium">稀有度</span></label>
                    <select name="rarity" class="select select-bordered w-full">
                        <option value="common" {% if badge.rarity == 'common' %}selected{% endif %}>Common (普通)</option>
                        <option value="rare" {% if badge.rarity == 'rare' %}selected{% endif %}>Rare (稀有)</option>
                        <option value="epic" {% if badge.rarity == 'epic' %}selected{% endif %}>Epic (史诗)</option>
                        <option value="legendary" {% if badge.rarity == 'legendary' %}selected{% endif %}>Legendary (传说)</option>
                    </select>
                </div>
                </div>
            </div>

            <div class="card bg-base-100 shadow-sm border border-base-200">
                <div class="card-body p-5">
                    <div class="form-control">
                        <label class="label"><span class="label-text font-medium">描述文案</span></label>
                        <textarea name="description" class="textarea textarea-bordered h-32 leading-relaxed" placeholder="描述这个徽章的含义...">{{ badge.description }}</textarea>
                    </div>
                </div>
            </div>
        </div>

        <div class="lg:col-span-2 space-y-6">
            <div class="card bg-base-100 shadow-sm border border-base-200">
                <div class="card-body">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="card-title text-lg">发放规则配置</h3>
                        {% if badge.is_hidden %}
                        <div class="badge badge-warning gap-1">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" /></svg>
                            隐藏状态
                        </div>
                        {% else %}
                        <div class="badge badge-success badge-outline gap-1">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                            公开可见
                        </div>
                        {% endif %}
                    </div>

                    <div class="bg-base-200/50 p-4 rounded-xl space-y-4">
                        <div class="form-control">
                            <label class="label"><span class="label-text font-medium">触发条件类型</span></label>
                            <select name="condition_type" class="select select-bordered w-full" required onchange="toggleConditionInputs(this)">
                                <option value="manual" {% if badge.condition_type == 'manual' %}selected{% endif %}>手动发放 (管理员分配)</option>
                                <option value="all_users" {% if badge.condition_type == 'all_users' %}selected{% endif %}>全员获取 (新老用户)</option>
                                <option value="login_days_in_range" {% if badge.condition_type == 'login_days_in_range' %}selected{% endif %}>限时登录天数</option>
                                <option value="streak_days" {% if badge.condition_type == 'streak_days' %}selected{% endif %}>连续打卡天数</option>
                                <option value="study_hours" {% if badge.condition_type == 'study_hours' %}selected{% endif %}>累计学习小时数</option>
                                <option value="note_count" {% if badge.condition_type == 'note_count' %}selected{% endif %}>累计笔记数量</option>
                                <option value="featured_count" {% if badge.condition_type == 'featured_count' %}selected{% endif %}>累计精选笔记数量</option>
                                <option value="wiki_edit_count" {% if badge.condition_type == 'wiki_edit_count' %}selected{% endif %}>Wiki 编辑次数</option>
                                <option value="wiki_create_count" {% if badge.condition_type == 'wiki_create_count' %}selected{% endif %}>Wiki 创建次数</option>
                                <option value="comment_count" {% if badge.condition_type == 'comment_count' %}selected{% endif %}>评论发布数量</option>
                                <option value="night_owl_sessions" {% if badge.condition_type == 'night_owl_sessions' %}selected{% endif %}>深夜学习天数</option>
                                <option value="early_bird" {% if badge.condition_type == 'early_bird' %}selected{% endif %}>早起鸟天数</option>
                                <option value="weekend_warrior" {% if badge.condition_type == 'weekend_warrior' %}selected{% endif %}>周末卷王 (小时)</option>
                                <option value="long_session_count" {% if badge.condition_type == 'long_session_count' %}selected{% endif %}>深度专注次数</option>
                                <option value="share_count" {% if badge.condition_type == 'share_count' %}selected{% endif %}>分享笔记次数</option>
                                <option value="total_views_received" {% if badge.condition_type == 'total_views_received' %}selected{% endif %}>笔记被阅读次数</option>
                            </select>
                        </div>

                        <div class="form-control" id="condition_value_group">
                            <label class="label"><span class="label-text font-medium">条件阈值</span></label>
                            <input type="number" name="condition_value" class="input input-bordered" value="{{ badge.condition_value }}" placeholder="例如：10" />
                            <label class="label"><span class="label-text-alt text-base-content/60">达到此数值时自动发放</span></label>
                        </div>

                        <div class="form-control">
                            <label class="label"><span class="label-text font-medium">条件描述（可选）</span></label>
                            <input type="text" name="custom_condition_text" class="input input-bordered" value="{{ badge.custom_condition_text or '' }}" placeholder="例如：连续7天早起打卡" />
                            <label class="label"><span class="label-text-alt text-base-content/60">如果填写，将在成就卡片上优先显示此文本，否则自动生成</span></label>
                        </div>

                        <div class="form-control hidden" id="time_range_group">
                            <label class="label"><span class="label-text font-medium">有效时间段</span></label>
                            <div class="flex flex-col sm:flex-row gap-2">
                                <input type="date" name="start_time" class="input input-bordered w-full" value="{{ badge.start_time.strftime('%Y-%m-%d') if badge.start_time else '' }}" />
                                <span class="hidden sm:inline self-center font-bold text-base-content/30">→</span>
                                <input type="date" name="end_time" class="input input-bordered w-full" value="{{ badge.end_time.strftime('%Y-%m-%d') if badge.end_time else '' }}" />
                            </div>
                        </div>
                    </div>

                    <div class="divider">限制与奖励</div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div class="form-control">
                            <label class="label"><span class="label-text font-medium">贴纸奖励数</span></label>
                            <div class="join">
                                <button type="button" class="btn join-item" onclick="this.nextElementSibling.stepDown()">-</button>
                                <input type="number" name="sticker_count" class="input input-bordered join-item w-full text-center" value="{{ badge.sticker_count or 1 }}" min="1" />
                                <button type="button" class="btn join-item" onclick="this.previousElementSibling.stepUp()">+</button>
                            </div>
                        </div>
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text font-medium">发行限量</span>
                                <span class="label-text-alt">当前已发: <span class="font-mono font-bold">{{ badge.issued_count }}</span></span>
                            </label>
                            <input type="number" name="total_limit" class="input input-bordered" value="{{ badge.total_limit if badge.total_limit is not none else '' }}" placeholder="留空为无限量" />
                        </div>
                    </div>

                    <div class="form-control mt-6 space-y-3">
                        <label class="label cursor-pointer justify-start gap-3 bg-base-100 border border-base-200 p-3 rounded-lg hover:border-warning transition-colors">
                            <input type="checkbox" name="is_hidden" class="checkbox checkbox-warning" {% if badge.is_hidden %}checked{% endif %} />
                            <div>
                                <span class="label-text font-medium">设置为隐藏成就</span>
                                <p class="text-xs text-base-content/50">用户在获得该徽章之前，无法在列表中看到它的条件。</p>
                            </div>
                        </label>
                        
                        <label class="label cursor-pointer justify-start gap-3 bg-base-100 border border-base-200 p-3 rounded-lg hover:border-secondary transition-colors">
                            <input type="checkbox" name="is_secret" class="checkbox checkbox-secondary" {% if badge.is_secret %}checked{% endif %} />
                            <div>
                                <span class="label-text font-medium">设置为神秘成就</span>
                                <p class="text-xs text-base-content/50">未解锁时完全保密（图标问号，标题???，描述隐藏）。</p>
                            </div>
                        </label>
                    </div>
                </div>
            </div>

            <div class="card bg-base-100 shadow-sm border border-base-200">
                <div class="card-body p-5">
                    <div class="alert alert-info shadow-none bg-info/10 text-info-content text-sm mb-4">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        <span>保存修改后，系统将自动重新计算所有用户的达成情况。</span>
                    </div>
                    
                    <div class="flex justify-between items-center">
                        <button type="button" class="btn btn-ghost text-error btn-sm hover:bg-error/10" onclick="document.getElementById('delete_modal').showModal()">
                            删除徽章
                        </button>
                        <div class="flex gap-3">
                            <a href="{{ url_for('manage_badges') }}" class="btn btn-ghost">取消</a>
                            <button type="submit" class="btn btn-primary px-8">保存更改</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </form>
</div>

<dialog id="delete_modal" class="modal">
  <div class="modal-box">
    <h3 class="font-bold text-lg text-error">删除确认</h3>
    <p class="py-4">您确定要删除徽章 <strong>{{ badge.name }}</strong> 吗？<br>此操作将从所有已获得该徽章的用户中移除它，且无法撤销。</p>
    <div class="modal-action">
      <form method="dialog">
        <button class="btn">取消</button>
      </form>
      <form method="post" action="{{ url_for('delete_badge', badge_id=badge.id) }}">
        <button type="submit" class="btn btn-error">确认删除</button>
      </form>
    </div>
  </div>
</dialog>

{% endblock %}

{% block scripts %}
<script>
// 图片预览逻辑
function previewImage(input) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('icon_preview').src = e.target.result;
        }
        reader.readAsDataURL(input.files[0]);
    }
}

// 联动逻辑（保持一致）
function toggleConditionInputs(select) {
    const val = select.value;
    const timeGroup = document.getElementById('time_range_group');
    const valueGroup = document.getElementById('condition_value_group');
    
    if (val === 'login_days_in_range') {
        timeGroup.classList.remove('hidden');
        valueGroup.classList.remove('hidden');
    } else if (val === 'all_users' || val === 'manual') {
        timeGroup.classList.add('hidden');
        valueGroup.classList.add('hidden');
    } else {
        timeGroup.classList.add('hidden');
        valueGroup.classList.remove('hidden');
    }
}

// 初始化状态
document.addEventListener('DOMContentLoaded', () => {
    const select = document.querySelector('select[name="condition_type"]');
    if (select) toggleConditionInputs(select);
});
</script>
{% endblock %}
```

## 📄 wiki/new_page.html

```html
{% extends "base.html" %}

{% block extra_css %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/vendor/github.min.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/vendor/easymde.min.css') }}">

<style>
    /* =========================================
       1. EasyMDE 容器主样式 (核心修复)
       ========================================= */
    .EasyMDEContainer {
        display: flex;
        flex-direction: column;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        /* 默认固定高度：这里控制整体编辑器有多高 */
        height: 600px; 
    }

    /* 当编辑器进入【全屏模式】时 */
    .EasyMDEContainer.fullscreen {
        height: 100vh !important; /* 撑满屏幕高度 */
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        z-index: 99999 !important; /* 确保盖住所有侧边栏和顶栏 */
        border-radius: 0 !important;
    }

    /* =========================================
       2. 工具栏样式
       ========================================= */
    .editor-toolbar {
        flex-shrink: 0; /* 禁止工具栏被压缩 */
        border: none !important;
        border-bottom: 1px solid #e5e7eb !important;
        background-color: #f9fafb;
        border-radius: 0.5rem 0.5rem 0 0;
        padding: 0.5rem !important;
        
        /* 强制单行显示，支持横向滚动 */
        white-space: nowrap;
        overflow-x: auto;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    /* 全屏时去掉圆角 */
    .EasyMDEContainer.fullscreen .editor-toolbar {
        border-radius: 0;
    }

    /* 隐藏工具栏滚动条 */
    .editor-toolbar::-webkit-scrollbar { height: 0; }

    /* =========================================
       3. 编辑区 (CodeMirror) 样式
       ========================================= */
    .CodeMirror {
        flex-grow: 1; /* 自动填满剩余高度 */
        height: auto !important; /* 覆盖默认高度，让 Flexbox 接管 */
        border: none !important;
        border-radius: 0 0 0.5rem 0.5rem;
        font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
        font-size: 14px;
        line-height: 1.6;
        background: #fff;
    }
    
    /* 内部滚动条区域 */
    .CodeMirror-scroll {
        min-height: 100% !important;
    }

    /* =========================================
       4. 分屏预览区 (Side by Side) 样式
       ========================================= */
    /* 默认状态下的预览区 */
    .editor-preview-side {
        border: none !important;
        border-left: 1px solid #e5e7eb !important;
        background-color: #fafaf9;
        position: absolute;
        bottom: 0;
        right: 0;
        top: 50px; /* 预留工具栏高度，JS会自动微调但CSS做保底 */
        height: auto !important; /* 跟随容器 */
        z-index: 50;
    }

    /* 【关键修复】：当激活分屏模式且非全屏时 (.sided--no-fullscreen)
       强制 CodeMirror 和 预览区 并排且各占 50% 
    */
    .EasyMDEContainer.sided--no-fullscreen .CodeMirror {
        width: 50% !important;
    }
    
    .EasyMDEContainer.sided--no-fullscreen .editor-preview-side {
        width: 50% !important;
        top: 61px !important; /* 修正顶部距离，对应工具栏高度 */
        display: block !important;
    }

    /* 修复公式间距 */
    .editor-preview-side p { margin: 0.5em 0; }
</style>
{% endblock %}

{% block sidebar_menu %}
    {% include "wiki/sidebar.html" %}
{% endblock %}

{% block content %}
<div class="w-full max-w-[98%] 2xl:max-w-7xl mx-auto flex flex-col gap-6">
    
    <div class="flex items-center justify-between">
        <h2 class="text-2xl font-bold text-stone-800">新建页面</h2>
        <a href="{{ url_for('wiki_detail', wiki_id=wiki.id) }}" class="btn btn-ghost btn-sm gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
            返回 Wiki
        </a>
    </div>

    <div class="card bg-base-100 shadow-sm border border-stone-100">
        <div class="card-body p-4 sm:p-6">
            <form method="post" class="flex flex-col gap-5">
                <div class="flex flex-col md:flex-row gap-4">
                    <div class="form-control flex-1">
                        <input class="input input-bordered w-full focus:input-primary font-bold text-lg" name="title" placeholder="在此输入页面标题..." required>
                    </div>
                    <div class="form-control w-full md:w-32">
                        <input class="input input-bordered w-full text-center" name="slug" type="number" step="1" placeholder="排序ID" title="数字越小越靠前" required>
                    </div>
                </div>
                
                <div class="form-control">
                    <input class="input input-bordered w-full text-sm" name="tags" placeholder="标签 (例如：算法, 笔记)，用逗号分隔">
                </div>

                <div class="form-control">
                    <textarea id="md-editor" name="content_md"></textarea>
                </div>

                <div class="flex justify-end pt-2">
                    <button class="btn btn-primary px-8 gap-2" type="submit">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-4 4m0 0l-4-4m4 4V4" /></svg>
                        保存页面
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src="{{ url_for('static', filename='js/vendor/polyfill.min.js') }}"></script>
<script id="MathJax-script" async src="{{ url_for('static', filename='js/vendor/tex-mml-chtml.js') }}"></script>
<script src="{{ url_for('static', filename='js/vendor/highlight.min.js') }}"></script>
<script src="{{ url_for('static', filename='js/vendor/easymde.min.js') }}"></script>

<script>
  document.addEventListener('DOMContentLoaded', () => {
      hljs.highlightAll();
  });

  const easyMDE = new EasyMDE({
    element: document.getElementById('md-editor'),
    // 不要在 JS 里写 minHeight/maxHeight 了，完全交给 CSS 控制
    // 这样 Fullscreen 才能生效
    
    // 允许分屏
    sideBySideFullscreen: false, 
    syncSideBySidePreviewScroll: true,
    
    toolbar: [
        "bold", "italic", "strikethrough", "heading", "|", 
        "quote", "unordered-list", "ordered-list", "|", 
        "link", "image", "upload-image", "code", "|",  
        "preview", "side-by-side", "fullscreen", "|", // side-by-side 和 fullscreen 都会正常工作
        "guide"
    ],

    uploadImage: true,
    imageUploadEndpoint: "{{ url_for('upload_file') }}",
    imagePathAbsolute: true,
    imageCSRFToken: "", 
    imageMaxSize: 1024 * 1024 * 16,
    imageAccept: "image/png, image/jpeg, image/gif, image/webp",
    imageTexts: {
        sbInit: "上传图片",
        sbOnDragEnter: "松开上传",
        sbOnDragLeave: "取消",
        sbProgress: "上传中...",
        sbOnUploaded: "成功",
        sizeUnits: "b,kb,mb"
    },
    errorCallback: (msg) => alert("上传失败: " + msg),

    previewRender: function(plainText) {
        const preview = document.getElementsByClassName("editor-preview-side")[0];
        preview.innerHTML = this.parent.markdown(plainText);
        preview.querySelectorAll('pre code').forEach((block) => hljs.highlightElement(block));
        if (typeof MathJax !== 'undefined') MathJax.typesetPromise([preview]);
        return preview.innerHTML;
    },
  });

  // 页面加载后自动开启分屏
  // 延迟一点以确保 CSS 布局计算完成
  setTimeout(function() {
      if (!easyMDE.isSideBySideActive()) {
          easyMDE.toggleSideBySide();
      }
  }, 200);

</script>
{% endblock %}
```

## 📄 wiki/contributors.html

```html
{% extends "base.html" %}

{% block title %}{{ wiki.title }} - 贡献者{% endblock %}

{% block sidebar_menu %}
    {% include "wiki/sidebar.html" %}
{% endblock %}

{% block content %}
<div class="min-h-screen bg-stone-50/50 p-4 md:p-8">
    <div class="max-w-5xl mx-auto space-y-8">
        
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div class="flex items-center gap-4">
                <a href="{{ url_for('wiki_detail', wiki_id=wiki.id) }}" class="btn btn-circle btn-ghost btn-sm text-stone-500 hover:bg-stone-200 hover:text-stone-800 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
                </a>
                <div>
                    <h1 class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-stone-800 to-stone-600">
                        贡献者风云榜
                    </h1>
                    <p class="text-stone-500 text-sm mt-1">感谢所有为 "{{ wiki.title }}" 添砖加瓦的伙伴们</p>
                </div>
            </div>
            
            <div class="flex gap-2">
                <div class="badge badge-lg badge-ghost gap-2 pl-1.5">
                    <span class="bg-primary/10 text-primary p-1 rounded-full">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" viewBox="0 0 20 20" fill="currentColor"><path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" /></svg>
                    </span>
                    {{ contributors|length }} 人参与
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="col-span-1 md:col-span-2 card bg-base-100 shadow-xl border border-stone-100 overflow-hidden relative">
                <div class="absolute top-0 right-0 p-4 opacity-10">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-32 w-32" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                </div>
                <div class="card-body flex-row items-center gap-6 z-10">
                    <div class="avatar placeholder online">
                        <div class="bg-neutral text-neutral-content rounded-full w-20 h-20 ring ring-primary ring-offset-base-100 ring-offset-2 shadow-lg">
                            <span class="text-3xl font-bold">
                                {{ wiki.created_by.username[0]|upper if wiki.created_by and wiki.created_by.username else '?' }}
                            </span>
                        </div>
                    </div>
                    <div>
                        <div class="badge badge-primary badge-outline mb-2">Wiki 发起人</div>
                        <h2 class="card-title text-2xl font-bold">{{ wiki.created_by.username if wiki.created_by else 'Unknown' }}</h2>
                        <p class="text-stone-500 text-sm flex items-center gap-1 mt-1">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                            创建于 {{ wiki.created_at.strftime('%Y-%m-%d') }}
                        </p>
                    </div>
                </div>
            </div>

            <div class="card bg-base-100 shadow-xl border border-stone-100">
                <div class="card-body">
                    <h3 class="card-title text-sm uppercase text-stone-400 font-bold tracking-wider mb-4">核心数据</h3>
                    <div class="flex items-end justify-between border-b border-stone-100 pb-4 mb-4 last:border-0 last:pb-0 last:mb-0">
                        <div>
                            <p class="text-stone-500 text-xs font-semibold">总编辑次数</p>
                            <p class="text-3xl font-black text-stone-800 mt-1">{{ contributors|map(attribute='edit_count')|sum }}</p>
                        </div>
                        <div class="p-3 bg-stone-50 rounded-xl text-stone-400">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="bg-base-100 rounded-3xl shadow-xl border border-stone-100 overflow-hidden">
            <div class="p-6 border-b border-stone-100 flex justify-between items-center bg-stone-50/30">
                <h3 class="font-bold text-lg text-stone-700">贡献排行</h3>
                <span class="text-xs text-stone-400 font-mono bg-stone-100 px-2 py-1 rounded">TOP {{ contributors|length }}</span>
            </div>
            
            <div class="overflow-x-auto">
                <table class="table w-full">
                    <thead>
                        <tr class="text-stone-400 border-stone-100">
                            <th class="bg-transparent w-16 text-center">排名</th>
                            <th class="bg-transparent pl-6">用户</th>
                            <th class="bg-transparent text-right pr-8">编辑数</th>
                            <th class="bg-transparent w-1/4">贡献度</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% set total_edits = contributors|map(attribute='edit_count')|sum %}
                        {% for c in contributors %}
                        <tr class="hover:bg-stone-50 transition-colors group border-stone-100">
                            <td class="text-center font-bold text-lg">
                                {% if loop.index == 1 %}
                                    <div class="mx-auto w-8 h-8 grid place-items-center bg-yellow-100 text-yellow-600 rounded-full">🥇</div>
                                {% elif loop.index == 2 %}
                                    <div class="mx-auto w-8 h-8 grid place-items-center bg-gray-100 text-gray-500 rounded-full">🥈</div>
                                {% elif loop.index == 3 %}
                                    <div class="mx-auto w-8 h-8 grid place-items-center bg-orange-100 text-orange-700 rounded-full">🥉</div>
                                {% else %}
                                    <span class="text-stone-400 text-sm font-mono">#{{ loop.index }}</span>
                                {% endif %}
                            </td>
                            
                            <td class="pl-6">
                                <div class="flex items-center gap-4">
                                    <div class="avatar placeholder">
                                        <div class="mask mask-squircle w-10 h-10 bg-gradient-to-br from-stone-200 to-stone-300 text-stone-600 font-bold shadow-sm group-hover:scale-105 transition-transform">
                                            <span>{{ c[0].username[0]|upper if c[0] and c[0].username else '?' }}</span>
                                        </div>
                                    </div>
                                    <div class="flex flex-col">
                                        <div class="font-bold text-stone-700 flex items-center gap-2">
                                            {{ c[0].username if c[0] else 'Unknown' }}
                                            {% if c[0] and wiki.created_by and c[0].id == wiki.created_by.id %}
                                                <span class="badge badge-xs badge-primary badge-outline" title="创建者">Author</span>
                                            {% endif %}
                                        </div>
                                        </div>
                                </div>
                            </td>

                            <td class="text-right pr-8 font-mono font-bold text-stone-600 text-lg">
                                {{ c.edit_count }}
                            </td>

                            <td class="pr-6">
                                {% if total_edits > 0 %}
                                    {% set percent = (c.edit_count / total_edits * 100)|round(1) %}
                                    <div class="flex flex-col gap-1">
                                        <div class="flex justify-between text-xs text-stone-400 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <span>占比</span>
                                            <span>{{ percent }}%</span>
                                        </div>
                                        <progress class="progress w-full h-2 
                                            {% if loop.index == 1 %}progress-warning
                                            {% elif loop.index == 2 %}progress-secondary
                                            {% elif loop.index == 3 %}progress-accent
                                            {% else %}progress-primary opacity-40{% endif %}" 
                                            value="{{ c.edit_count }}" max="{{ total_edits }}">
                                        </progress>
                                    </div>
                                {% else %}
                                    <span class="text-stone-300">-</span>
                                {% endif %}
                            </td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="4" class="py-12">
                                <div class="flex flex-col items-center justify-center text-stone-400 gap-4">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                                    <span>暂无编辑记录，期待您的第一次贡献！</span>
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

## 📄 wiki/view_page.html

```html
{% extends "base.html" %}

{% block title %}{{ page.title if page else wiki.title }}{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{{ url_for('markdown_css') }}">
<style>
    /* 侧边栏 TOC 专用样式 */
    .toc-link {
        display: block;
        padding: 0.25rem 0.5rem 0.25rem 0.75rem;
        font-size: 0.8rem;
        color: #78716c; /* stone-500 */
        border-left: 2px solid #e7e5e4; /* stone-200 */
        transition: all 0.2s;
        text-decoration: none;
        line-height: 1.4;
    }
    .toc-link:hover {
        color: #1c1917; /* stone-900 */
        border-left-color: #a8a29e; /* stone-400 */
        background-color: rgba(0,0,0,0.02);
    }
    .toc-link.active {
        color: #ea580c; /* primary (orange) */
        border-left-color: #ea580c;
        font-weight: 600;
        background-color: transparent;
    }
    
    /* 层级缩进 */
    .toc-h1 { padding-left: 0.75rem; }
    .toc-h2 { padding-left: 1.25rem; }
    .toc-h3 { padding-left: 1.75rem; }
    
    /* 页面列表当前页高亮 */
    .page-link-active {
        background-color: #fff7ed;
        color: #ea580c;
        font-weight: 600;
        border-right: 2px solid #ea580c;
    }
</style>
{% endblock %}

{% block sidebar_menu %}
    {% include "wiki/sidebar.html" %}

    <div class="h-px bg-stone-200 my-4 mx-2"></div>

    <div class="menu-section-title flex items-center justify-between">
        <span>页面列表</span>
        <span class="bg-stone-100 text-stone-500 px-1.5 py-0.5 rounded text-[10px]">{{ pages|length }}</span>
    </div>
    
    <div class="space-y-0.5 mb-6">
        {% for p in pages %}
        <a href="{{ url_for('view_page', wiki_id=wiki.id, slug=p.slug) }}" 
           class="block px-3 py-2 text-sm rounded-lg transition-colors duration-200 truncate {{ 'page-link-active' if page and p.slug == page.slug else 'text-stone-600 hover:bg-stone-100 hover:text-stone-900' }}" 
           title="{{ p.title }}">
            {{ p.title }}
        </a>
        {% endfor %}
    </div>

    {% if page %}
    <div id="sidebar-toc-wrapper" class="hidden">
        <div class="menu-section-title">本页目录</div>
        <nav id="toc-container" class="mb-8 pr-2">
            </nav>
    </div>
    {% endif %}

{% endblock %}

{% block content %}
<div id="main-content-wrapper" class="w-full max-w-5xl mx-auto flex flex-col gap-6 transition-all duration-300 ease-in-out">
    
    <div class="card bg-base-100 shadow-sm border border-stone-100">
        <div class="card-body p-4 sm:p-5 flex-row items-start justify-between gap-4">
            <div class="flex-1 min-w-0 group relative">
                <h2 class="text-xl font-bold text-stone-800 truncate" title="{{ wiki.title }}">{{ wiki.title }}</h2>
                <p class="text-sm text-stone-500 mt-1 line-clamp-1 group-hover:line-clamp-none transition-all duration-300 bg-base-100 z-10">
                    {{ wiki.description }}
                </p>
                {% if wiki.description|length > 50 %}
                <div class="hidden group-hover:block absolute top-full left-0 mt-2 p-3 bg-stone-800 text-white text-xs rounded shadow-lg z-50 max-w-md">
                    {{ wiki.description }}
                </div>
                {% endif %}
            </div>

            <!-- Contributors Section -->
            <div class="flex items-center -space-x-2 flex-shrink-0">
                <!-- Author -->
                {% if wiki.created_by %}
                <a href="{{ url_for('wiki_contributors', wiki_id=wiki.id) }}" class="avatar tooltip tooltip-bottom" data-tip="作者: {{ wiki.created_by.username if wiki.created_by and wiki.created_by.username else 'Unknown' }}">
                    <div class="w-8 h-8 rounded-full border-2 border-white bg-primary text-primary-content text-xs font-bold flex items-center justify-center relative z-30 !flex !items-center !justify-center leading-none">
                        <span class="transform -translate-y-[1px]">{{ wiki.created_by.username[0]|upper if wiki.created_by and wiki.created_by.username else '?' }}</span>
                    </div>
                </a>
                {% endif %}
                
                <!-- Top Contributors -->
                {% for c in contributors[:2] %}
                {% if c[0] %}
                <a href="{{ url_for('wiki_contributors', wiki_id=wiki.id) }}" class="avatar tooltip tooltip-bottom" data-tip="贡献者: {{ c[0].username if c[0] and c[0].username else 'Unknown' }}">
                    <div class="w-8 h-8 rounded-full border-2 border-white bg-stone-200 text-stone-600 text-xs font-bold flex items-center justify-center hover:bg-stone-300 transition-colors relative z-20 !flex !items-center !justify-center leading-none">
                        <span class="transform -translate-y-[1px]">{{ c[0].username[0]|upper if c[0] and c[0].username else '?' }}</span>
                    </div>
                </a>
                {% endif %}
                {% endfor %}
                
                <!-- More Count -->
                {% if contributors|length > 2 %}
                <a href="{{ url_for('wiki_contributors', wiki_id=wiki.id) }}" class="avatar placeholder tooltip tooltip-bottom" data-tip="查看全部 {{ contributors|length }} 位贡献者">
                    <div class="w-8 h-8 rounded-full border-2 border-white bg-stone-100 text-stone-500 text-xs font-bold flex items-center justify-center hover:bg-stone-200 transition-colors relative z-10 !flex !items-center !justify-center leading-none">
                        <span class="transform -translate-y-[1px]">+{{ contributors|length - 2 }}</span>
                    </div>
                </a>
                {% endif %}
            </div>
        </div>
    </div>

    <div class="card bg-base-100 shadow-sm border-[3px] border-stone-200 min-h-[70vh]">
        <div class="card-body p-6 lg:p-10">
            {% if page %}
                <div class="flex items-center justify-between mb-8 pb-4 border-b border-stone-100">
                  <div class="min-w-0 flex-1 mr-4">
                    <h1 class="text-3xl font-bold text-stone-800 break-words">{{ page.title }}</h1>
                    {% if page.tags %}
                    <div class="flex items-center gap-2 mt-2 flex-wrap">
                        {% for tag in page.tags %}
                        <span class="badge badge-sm badge-outline">{{ tag.name }}</span>
                        {% endfor %}
                    </div>
                    {% endif %}
                  </div>
                  
                  <div class="flex items-center gap-1 flex-shrink-0">
                    
                    <button id="width-toggle-btn" class="btn btn-sm btn-ghost gap-1 text-stone-500 hover:text-stone-800 hidden lg:inline-flex" title="切换宽屏/窄屏">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                        </svg>
                    </button>

                    <div class="divider divider-horizontal mx-1 py-1 h-6 self-center"></div>

                    <button onclick="convert_wiki_page()" class="btn btn-sm btn-ghost gap-1 text-stone-500 hover:text-primary transition-colors" title="转换为我的笔记">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                        </svg>
                        <span class="hidden xl:inline">转为笔记</span>
                    </button>

                    {% if can_edit %}
                    <div class="dropdown dropdown-end">
                        <label tabindex="0" class="btn btn-sm btn-ghost gap-1 text-stone-500">
                            更多
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
                        </label>
                        <ul tabindex="0" class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52 border border-stone-100 z-20">
                            <li>
                                <a href="{{ url_for('edit_page', wiki_id=wiki.id, slug=page.slug) }}">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                                    编辑页面
                                </a>
                            </li>
                            <li>
                                <a href="{{ url_for('page_history', wiki_id=wiki.id, slug=page.slug) }}">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                    历史版本
                                </a>
                            </li>
                        </ul>
                    </div>
                    {% endif %}
                  </div>
                </div>
                
                <div class="flex justify-end mb-4">
                     <span class="text-xs text-stone-400">更新于 {{ page.updated_at.strftime('%Y-%m-%d') }}</span>
                </div>

                {% if not can_view_wiki(wiki.id) and not is_subscribed %}
                    <div class="alert alert-warning shadow-lg">
                        <div>
                            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                            <span>请先订阅此 Wiki 以查看完整内容。</span>
                        </div>
                    </div>
                {% else %}
                    <div class="markdown-body prose prose-stone max-w-none lg:prose-lg">
                      {{ html|safe }}
                    </div>
                    
                    {% if page.comment_enabled %}
                    <div class="border-t border-stone-100 mt-12 pt-8">
                        <h3 class="text-lg font-bold text-stone-700 mb-6 flex items-center gap-2">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" /></svg>
                            评论 ({{ page.comments|length }})
                        </h3>
                        
                        <div class="space-y-6 mb-8">
                            {% for comment in page.comments %}
                            <div class="flex gap-4 group">
                                <div class="avatar placeholder">
                                    <div class="bg-stone-200 text-stone-600 rounded-full w-10 h-10">
                                        <span class="text-sm">{{ comment.user.username[0] | upper }}</span>
                                    </div>
                                </div>
                                <div class="flex-1">
                                    <div class="flex items-center gap-2 mb-1">
                                        <span class="font-bold text-sm text-stone-700">{{ comment.user.username }}</span>
                                        <span class="text-xs text-stone-400">{{ comment.created_at.strftime('%Y-%m-%d %H:%M') }}</span>
                                        {% if current_user.is_admin or current_user.id == comment.user_id %}
                                        <form action="{{ url_for('delete_comment', comment_id=comment.id) }}" method="post" class="ml-auto opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button type="submit" class="btn btn-ghost btn-xs text-error" title="删除评论" onclick="return confirm('确定要删除这条评论吗？')">
                                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                                            </button>
                                        </form>
                                        {% endif %}
                                    </div>
                                    <div class="p-3 bg-stone-50 rounded-lg rounded-tl-none text-sm text-stone-600 whitespace-pre-wrap">{{ comment.content }}</div>
                                </div>
                            </div>
                            {% else %}
                            <div class="text-center py-8 text-stone-400 italic">暂无评论</div>
                            {% endfor %}
                        </div>
                        
                        <form action="{{ url_for('comment_wiki_page', wiki_id=wiki.id, slug=page.slug) }}" method="post" class="flex gap-4">
                            <div class="avatar placeholder">
                                <div class="bg-primary text-primary-content rounded-full w-10 h-10">
                                    <span class="text-sm">{{ current_user.username[0] | upper }}</span>
                                </div>
                            </div>
                            <div class="flex-1 flex gap-2">
                                <textarea name="content" class="textarea textarea-bordered w-full h-20 resize-none bg-stone-50 focus:bg-white" placeholder="发表评论..." required></textarea>
                                <button type="submit" class="btn btn-primary h-auto">发表</button>
                            </div>
                        </form>
                    </div>
                    {% endif %}
                {% endif %}
            {% else %}
                <div class="hero h-full">
                  <div class="hero-content text-center">
                    <div class="max-w-md">
                      <h1 class="text-3xl font-bold text-stone-300 mb-4">欢迎来到 {{ wiki.title }}</h1>
                      {% if can_edit %}
                      <p class="py-6 text-stone-500">点击左侧管理菜单创建第一个页面</p>
                      <a href="{{ url_for('new_page', wiki_id=wiki.id) }}" class="btn btn-primary">立即创建</a>
                      {% else %}
                      <p class="text-stone-400">此 Wiki 暂无内容，敬请期待。</p>
                      {% endif %}
                    </div>
                  </div>
                </div>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    // --- 核心修改点 3: 宽屏/窄屏切换逻辑 ---
    const widthBtn = document.getElementById('width-toggle-btn');
    const contentWrapper = document.getElementById('main-content-wrapper');
    
    // 图标 SVG 字符串
    const iconExpand = '<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" /></svg>';
    const iconCompress = '<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>'; 
    // 或者使用收缩箭头:
    const iconContract = '<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14H6m0 0v4m0-4l5 5m7-5h4m-4 0v4m0-4l-5 5m-7-5h-4m4 0v-4m0 4l-5-5m11 5l5-5m-5 5v-4m0 4h4" /></svg>'; // 随便找个类似的，或者用上面的笔记图标

    if (widthBtn && contentWrapper) {
        // 1. 初始化状态
        const savedMode = localStorage.getItem('wiki_width_mode');
        // 默认是窄屏 (savedMode === 'wide' 才是宽屏)
        let isWide = savedMode === 'wide';
        
        // 应用状态函数
        function applyLayout(wide) {
            if (wide) {
                // 宽屏模式：移除 max-w-5xl，设为接近全屏
                contentWrapper.classList.remove('max-w-5xl');
                contentWrapper.classList.add('max-w-[98%]'); // 或者 'max-w-none', 'px-4'
                widthBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>'; // 收缩图标
                widthBtn.setAttribute('title', '恢复窄屏');
            } else {
                // 窄屏模式 (默认)
                contentWrapper.classList.add('max-w-5xl');
                contentWrapper.classList.remove('max-w-[98%]');
                widthBtn.innerHTML = iconExpand; // 展开图标
                widthBtn.setAttribute('title', '切换宽屏');
            }
        }

        // 初始应用
        applyLayout(isWide);

        // 2. 点击事件
        widthBtn.addEventListener('click', function() {
            isWide = !isWide;
            applyLayout(isWide);
            localStorage.setItem('wiki_width_mode', isWide ? 'wide' : 'narrow');
        });
    }

    // --- 原有代码块复制功能 ---
    document.querySelectorAll('pre code').forEach((block) => {
        const pre = block.parentNode;
        const wrapper = document.createElement('div');
        wrapper.className = 'relative group';
        pre.parentNode.insertBefore(wrapper, pre);
        wrapper.appendChild(pre);
        
        const button = document.createElement('button');
        button.className = 'absolute top-2 right-2 p-1.5 rounded-lg bg-white/10 text-white/70 hover:bg-white/20 hover:text-white transition-all opacity-0 group-hover:opacity-100 focus:opacity-100';
        button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>';
        button.title = '复制';
        
        button.addEventListener('click', async () => {
            const code = block.textContent;
            try {
                await navigator.clipboard.writeText(code);
                const originalIcon = button.innerHTML;
                button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>';
                setTimeout(() => { button.innerHTML = originalIcon; }, 2000);
            } catch (err) { console.error('Failed to copy!', err); }
        });
        wrapper.appendChild(button);
    });

    // --- 原有 TOC 生成逻辑 ---
    const content = document.querySelector('.markdown-body');
    const tocContainer = document.getElementById('toc-container');
    const tocWrapper = document.getElementById('sidebar-toc-wrapper');
    
    if (content && tocContainer) {
        const headers = content.querySelectorAll('h1, h2, h3');
        if (headers.length > 0) {
            if (tocWrapper) tocWrapper.classList.remove('hidden');
            const tocLinks = [];
            headers.forEach((header, index) => {
                if (!header.id) header.id = 'heading-' + index;
                const link = document.createElement('a');
                link.href = '#' + header.id;
                link.textContent = header.textContent;
                link.className = 'toc-link toc-' + header.tagName.toLowerCase();
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    header.scrollIntoView({ behavior: 'smooth' });
                    updateTOCVisibility(index);
                });
                tocContainer.appendChild(link);
                tocLinks.push(link);
            });
            function updateTOCVisibility(activeIndex) {
                tocLinks.forEach((link, idx) => {
                    if (idx === activeIndex) {
                        link.classList.add('active');
                        if (idx > 0 && idx < tocLinks.length - 1) {
                             const rect = link.getBoundingClientRect();
                             const navRect = document.querySelector('#sidebar nav').getBoundingClientRect();
                             if (rect.bottom > navRect.bottom || rect.top < navRect.top) {
                                 link.scrollIntoView({ behavior: 'smooth', block: 'center' });
                             }
                        }
                    } else {
                        link.classList.remove('active');
                    }
                });
            }
            updateTOCVisibility(0);
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const id = entry.target.id;
                        const index = Array.from(headers).findIndex(h => h.id === id);
                        if (index !== -1) updateTOCVisibility(index);
                    }
                });
            }, { rootMargin: '-100px 0px -66%' });
            headers.forEach(header => observer.observe(header));
        }
    }
});

function convert_wiki_page() {
    if (confirm('确定要将当前页面内容转换为您的个人笔记吗？')) {
        fetch("{{ url_for('convert_wiki_page', wiki_id=wiki.id, slug=page.slug) }}", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (confirm('转换成功！是否现在查看该笔记？')) {
                    window.location.href = `/book/notes/${data.note_id}`;
                }
            } else {
                alert('转换失败: ' + (data.error || '未知错误'));
            }
        })
        .catch(error => { console.error('Error:', error); alert('请求发生错误'); });
    }
}
</script>
{% endblock %}
```

## 📄 wiki/sidebar.html

```html
<div class="px-2 py-4">
    
    <div class="menu-section-title">发现</div>
    <ul class="space-y-1 mb-4">
        <li>
            <a href="{{ url_for('index') }}" class="menu-item flex items-center gap-3 px-3 py-2 text-stone-600 hover:text-orange-600 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                <span class="font-bold truncate">返回广场</span>
            </a>
        </li>
    </ul>

    {% if can_edit_wiki(wiki.id) %}
        {% set manage_endpoints = ['new_page', 'edit_wiki', 'manage_files', 'manage_editors', 'wiki_stats'] %}
        {% set is_manage_expanded = request.endpoint in manage_endpoints %}

        <details class="group" {{ 'open' if is_manage_expanded else '' }}>
            <summary class="menu-section-title flex items-center justify-between cursor-pointer select-none list-none hover:text-stone-600 transition-colors">
                <span>Wiki 管理</span>
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 transition-transform duration-200 group-open:rotate-180 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
            </summary>

            <ul class="space-y-1 mt-1 animate-slide-down">
                <li>
                    <a href="{{ url_for('new_page', wiki_id=wiki.id) }}" class="menu-item flex items-center gap-3 px-3 py-2 {{ 'active' if request.endpoint == 'new_page' else '' }}">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
                        <span>新建页面</span>
                    </a>
                </li>
                <li>
                    <a href="{{ url_for('edit_wiki', wiki_id=wiki.id) }}" class="menu-item flex items-center gap-3 px-3 py-2 {{ 'active' if request.endpoint == 'edit_wiki' else '' }}">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                        <span>Wiki 设置</span>
                    </a>
                </li>
                <li>
                    <a href="{{ url_for('manage_files', wiki_id=wiki.id) }}" class="menu-item flex items-center gap-3 px-3 py-2 {{ 'active' if request.endpoint == 'manage_files' else '' }}">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                        <span>文件管理</span>
                    </a>
                </li>
                
                {% if current_user.is_admin %}
                <li>
                    <a href="{{ url_for('manage_editors', wiki_id=wiki.id) }}" class="menu-item flex items-center gap-3 px-3 py-2 {{ 'active' if request.endpoint == 'manage_editors' else '' }}">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
                        <span>编辑授权</span>
                    </a>
                </li>
                <li>
                    <a href="{{ url_for('wiki_stats', wiki_id=wiki.id) }}" class="menu-item flex items-center gap-3 px-3 py-2 {{ 'active' if request.endpoint == 'wiki_stats' else '' }}">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
                        <span>统计数据</span>
                    </a>
                </li>
                {% endif %}
            </ul>
        </details>
    {% endif %}

    <div class="menu-section-title">操作</div>
    <ul class="space-y-1">
        <li>
            {# 假设这里有一个变量 is_subscribed 已经在上下文中 #}
            {# 修正了原代码中 form 标签的闭合位置逻辑 #}
            <form action="{{ url_for('subscribe_wiki', wiki_id=wiki.id, next=request.full_path) }}" method="post" class="w-full">
                {% if is_subscribed %}
                <button type="submit" class="menu-item flex items-center gap-3 px-3 py-2 w-full text-left hover:text-red-600 group hover:bg-red-50 hover:border-red-100">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-green-500 group-hover:text-red-500 transition-colors" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                    </svg>
                    <span class="group-hover:hidden">已订阅</span>
                    <span class="hidden group-hover:inline text-red-600 font-medium">取消订阅</span>
                </button>
                {% else %}
                <button type="submit" class="menu-item flex items-center gap-3 px-3 py-2 w-full text-left">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" /></svg>
                    <span>订阅 Wiki</span>
                </button>
                {% endif %}
            </form>
        </li>
    </ul>
</div>
```

## 📄 wiki/edit_page.html

```html
{% extends "base.html" %}
{% block content %}
<div class="max-w-7xl mx-auto card bg-base-100 shadow">
  <div class="card-body">
    <h2 class="card-title">编辑页面</h2>
    <form method="post" class="flex flex-col gap-4">
      <div class="flex gap-4">
          <input class="input input-bordered flex-1" name="title" value="{{ page.title }}" placeholder="标题" required>
          <input class="input input-bordered flex-1" name="slug" value="{{ page.slug }}" type="number" step="1" placeholder="标识（整数，负数置顶）" required>
      </div>
      <input class="input input-bordered w-full" name="tags" value="{{ page.tags | map(attribute='name') | join(', ') }}" placeholder="标签 (用逗号分隔)">
      
      <div class="form-control">
        <label class="label cursor-pointer justify-start gap-4">
          <span class="label-text">允许评论</span> 
          <input type="checkbox" name="comment_enabled" class="toggle toggle-primary" {% if page.comment_enabled %}checked{% endif %} />
        </label>
      </div>

      <textarea id="md-editor" name="content_md" placeholder="Markdown内容">{{ page.content_md }}</textarea>
      
      <div class="flex justify-between items-center mt-4">
          <button class="btn btn-primary px-8" type="submit">保存修改</button>
          <button type="button" class="btn btn-error btn-outline" onclick="delete_modal.showModal()">删除页面</button>
      </div>
    </form>
    
    <div class="mt-4">
      <a class="btn btn-ghost" href="{{ url_for('view_page', wiki_id=wiki.id, slug=page.slug) }}">返回阅读</a>
    </div>
  </div>
</div>

<!-- 删除确认弹窗 -->
<dialog id="delete_modal" class="modal">
  <div class="modal-box">
    <h3 class="font-bold text-lg text-error">确认删除</h3>
    <p class="py-4">您确定要删除页面 "<strong>{{ page.title }}</strong>" 吗？此操作无法撤销。</p>
    <div class="modal-action">
      <form method="dialog">
        <button class="btn">取消</button>
      </form>
      <form action="{{ url_for('delete_page', wiki_id=wiki.id, slug=page.slug) }}" method="post">
        <button class="btn btn-error">确认删除</button>
      </form>
    </div>
  </div>
</dialog>
{% endblock %}

{% block scripts %}
<script>
  const easyMDE = new EasyMDE({
    element: document.getElementById('md-editor'),
    minHeight: "400px",
    uploadImage: true,
    imageUploadEndpoint: "{{ url_for('upload_file') }}",
    imagePathAbsolute: true,
    imageCSRFToken: "", // 如果使用了CSRF保护，请在此处填入token
    imageMaxSize: 1024 * 1024 * 16, // 16MB
    imageAccept: "image/png, image/jpeg, image/gif, image/webp",
    imageTexts: {
        sbInit: "拖拽图片到这里或点击上传",
        sbOnDragEnter: "松开上传",
        sbOnDragLeave: "拖拽图片到这里或点击上传",
        sbProgress: "上传中...",
        sbOnUploaded: "上传成功",
        sizeUnits: "b,kb,mb"
    },
    errorCallback: function(errorMessage) {
        alert("上传失败: " + errorMessage);
    }
  });
</script>
{% endblock %}
```

## 📄 wiki/page_history.html

```html
{% extends "base.html" %}

{% block content %}
<div class="max-w-5xl mx-auto space-y-6">
    <!-- 头部信息 -->
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-3xl font-bold text-stone-800">历史版本</h1>
            <p class="text-stone-500 mt-2">
                页面：<span class="font-bold">{{ page.title }}</span>
            </p>
        </div>
        <a href="{{ url_for('view_page', wiki_id=wiki.id, slug=page.slug) }}" class="btn btn-ghost">返回阅读</a>
    </div>

    <!-- 历史记录列表 -->
    <div class="card bg-base-100 shadow-sm border border-stone-100">
        <div class="card-body">
            {% if page.history %}
            <div class="overflow-x-auto">
                <table class="table table-zebra w-full">
                    <thead>
                        <tr>
                            <th>版本时间</th>
                            <th>修改人</th>
                            <th>标题</th>
                            <th>标识 (Slug)</th>
                            <th class="text-right">操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for h in page.history %}
                        <tr>
                            <td class="font-mono text-sm">{{ h.created_at.strftime('%Y-%m-%d %H:%M:%S') }}</td>
                            <td>
                                <div class="flex items-center gap-2">
                                    <div class="avatar placeholder">
                                        <div class="bg-neutral-focus text-neutral-content rounded-full w-6 h-6">
                                            <span class="text-xs">{{ h.user.username[0]|upper }}</span>
                                        </div>
                                    </div>
                                    {{ h.user.username }}
                                </div>
                            </td>
                            <td>{{ h.title }}</td>
                            <td>{{ h.slug }}</td>
                            <td class="text-right">
                                <button class="btn btn-xs btn-warning" onclick="confirm_restore('{{ h.id }}', '{{ h.created_at.strftime('%Y-%m-%d %H:%M:%S') }}')">
                                    回滚至此版本
                                </button>
                                <!-- 隐藏的回滚表单 -->
                                <form id="restore-form-{{ h.id }}" action="{{ url_for('restore_page', wiki_id=wiki.id, slug=page.slug, history_id=h.id) }}" method="post" class="hidden"></form>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% else %}
            <div class="text-center py-8 text-stone-400">
                暂无历史版本记录
            </div>
            {% endif %}
        </div>
    </div>
</div>

<!-- 确认回滚弹窗 -->
<dialog id="restore_modal" class="modal">
  <div class="modal-box">
    <h3 class="font-bold text-lg text-warning">确认回滚</h3>
    <p class="py-4">您确定要将页面回滚到 <strong id="restore-time"></strong> 的版本吗？<br>当前版本将被保存为新的历史记录。</p>
    <div class="modal-action">
      <form method="dialog">
        <button class="btn">取消</button>
      </form>
      <button class="btn btn-warning" onclick="submit_restore()">确认回滚</button>
    </div>
  </div>
</dialog>

<script>
let currentRestoreId = null;

function confirm_restore(id, time) {
    currentRestoreId = id;
    document.getElementById('restore-time').textContent = time;
    restore_modal.showModal();
}

function submit_restore() {
    if (currentRestoreId) {
        document.getElementById('restore-form-' + currentRestoreId).submit();
    }
}
</script>
{% endblock %}
```

## 📄 wiki/detail.html

```html
{% extends "base.html" %}
{% block content %}
<div class="flex items-center justify-between mb-4">
  <div>
    <h1 class="text-2xl font-bold">{{ wiki.title }}</h1>
    <p class="text-base-content/70">{{ wiki.description }}</p>
  </div>
  <div class="flex items-center gap-2">
    {% if is_subscribed %}
    <span class="badge badge-success">已订阅</span>
    {% else %}
    <form method="post" action="{{ url_for('subscribe_wiki', wiki_id=wiki.id) }}">
      <button class="btn btn-outline btn-success" type="submit">订阅</button>
    </form>
    {% endif %}
    {% if is_editor %}
    <a class="btn btn-primary" href="{{ url_for('new_page', wiki_id=wiki.id) }}">新建页面</a>
    <a class="btn btn-outline" href="{{ url_for('manage_editors', wiki_id=wiki.id) }}">编辑授权</a>
    {% endif %}
  </div>
  </div>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    <div class="card bg-base-100 shadow">
      <div class="card-body">
        <h3 class="card-title">页面列表</h3>
        <ul class="menu">
          {% for p in pages %}
          <li><a href="{{ url_for('view_page', wiki_id=wiki.id, slug=p.slug) }}">{{ p.title }}</a></li>
          {% else %}
          <li class="text-base-content/70">暂无页面</li>
          {% endfor %}
        </ul>
      </div>
    </div>
    <div class="md:col-span-2 card bg-base-100 shadow">
      <div class="card-body">
        <p class="text-base-content/70">请选择左侧页面查看内容</p>
      </div>
    </div>
  </div>
{% endblock %}
```


---

## 📚 包含的文件清单

- packer.py
- index.html
- online_users.html
- register.html
- base.html
- login.html
- book/my_notes.html
- book/index.html
- book/new_note.html
- book/received.html
- book/calendar.html
- book/edit_note.html
- book/view_note.html
- partials/notes_heatmap.html
- user/achievement_book.html
- user/my_badges.html
- user/following.html
- user/profile.html
- admin/create_wiki.html
- admin/wiki_files.html
- admin/manage_announcements.html
- admin/announcement_stats.html
- admin/edit_wiki.html
- admin/manage_users.html
- admin/manage_badges.html
- admin/manage_editors.html
- admin/wiki_stats.html
- admin/markdown_css.html
- admin/edit_announcement.html
- admin/announcement_files.html
- admin/edit_badge.html
- wiki/new_page.html
- wiki/contributors.html
- wiki/view_page.html
- wiki/sidebar.html
- wiki/edit_page.html
- wiki/page_history.html
- wiki/detail.html
