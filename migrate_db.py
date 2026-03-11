# 引入你的 Flask 实例和数据库实例
# 💡 注意：如果你的主文件不叫 app.py，请把这里的 app 换成你的文件名
from app import app, db 


def fix_database():
    with app.app_context():
        print("开始扫描数据库...")
        
        # db.create_all() 是无损操作：
        # 它只会创建目前数据库中【不存在】的表，绝对不会覆盖或修改【已存在】的表和数据！
        db.create_all()
        
        print("✅ 修复完成！缺失的新表（bookmark_types, user_bookmarks）已被安全创建。")
        print("老数据完好无损，现在可以重新启动 Flask 服务器了。")

if __name__ == '__main__':
    fix_database()