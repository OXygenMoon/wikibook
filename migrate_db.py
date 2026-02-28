from app import app, db
with app.app_context():
    db.create_all()
    print("✅ StickyNote 表创建成功！")