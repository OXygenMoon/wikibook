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