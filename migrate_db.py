from app import app, db
from sqlalchemy import text

def refresh_schema():
    with app.app_context():
        print("正在强制刷新 UserActiveStatus 表...")
        # 为了不影响核心数据（笔记、用户），我们只删除并重建状态表和新功能表
        temp_tables = [
            'user_active_status', 
            'wiki_folder', 
            'wall_sticker', 
            'sticker_wall', 
            'pomodoro_record',
            'wall_classes',
            'wall_groups',
            'wall_users'
        ]
        
        with db.engine.connect() as conn:
            for table in temp_tables:
                conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
            conn.commit()
        
        print("正在根据最新代码重建所有缺失的表...")
        db.create_all()
        print("✅ 数据库结构同步完成！")

if __name__ == '__main__':
    refresh_schema()