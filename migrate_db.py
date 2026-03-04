from app import app, db
from sqlalchemy import text

def run_migration():
    with app.app_context():
        # 获取当前实际连接的数据库引擎信息
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"🔗 当前连接的数据库URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"📦 发现表: {tables}")
        
        if 'badge' not in tables:
            print("⚠️ 找不到 badge 表！可能是数据库还没初始化，现在自动创建...")
            db.create_all()
            print("✅ 所有缺失的表已创建完毕。")
            
        # 重新获取列信息
        columns = [c['name'] for c in inspector.get_columns('Badge')]
        
        with db.engine.connect() as conn:
            # 1. 检查并添加 serial_prefix 字段
            if 'serial_prefix' not in columns:
                print("⏳ 正在为 badge 表添加 serial_prefix 字段...")
                conn.execute(text("ALTER TABLE Badge ADD COLUMN serial_prefix VARCHAR(20) DEFAULT 'SF'"))
                conn.commit()
                print("✅ serial_prefix 字段添加成功！")
            else:
                print("⚡ serial_prefix 字段已存在，跳过添加。")
                
            # 2. 将以前的旧数据，统一刷上默认前缀 'SF'
            print("⏳ 正在清理和同步旧数据的前缀...")
            conn.execute(text("UPDATE Badge SET serial_prefix = 'SF' WHERE serial_prefix IS NULL OR serial_prefix = ''"))
            conn.commit()
            print("✅ 旧数据前缀同步完成！")

        print("🎉 所有数据库迁移与修复已成功完成！你可以安全启动项目了。")

if __name__ == '__main__':
    run_migration()