
import os
import sys
from app import app, db, Wiki, WikiPage, User, WikiPageHistory
from flask import template_rendered, render_template
from flask_login import login_user

# --- 模拟 Flask 请求上下文 ---
def test_wiki_contributors_and_view_page():
    print("Starting test...")
    
    with app.app_context():
        # 1. 确保有一个测试用户
        user = User.query.first()
        if not user:
            print("Creating test user...")
            user = User(username="test_user", email="test@example.com", password_hash="hash")
            db.session.add(user)
            db.session.commit()
        print(f"Using user: {user.username} (ID: {user.id})")

        # 2. 确保有一个测试 Wiki
        wiki = Wiki.query.first()
        if not wiki:
            print("Creating test Wiki...")
            wiki = Wiki(title="Test Wiki", created_by_id=user.id)
            db.session.add(wiki)
            db.session.commit()
        print(f"Using wiki: {wiki.title} (ID: {wiki.id})")

        # 3. 确保有一个测试 Page
        page = WikiPage.query.filter_by(wiki_id=wiki.id).first()
        if not page:
            print("Creating test WikiPage...")
            page = WikiPage(wiki_id=wiki.id, title="Test Page", slug="test-page", content_md="# Test Content")
            db.session.add(page)
            db.session.commit()
        print(f"Using page: {page.title} (Slug: {page.slug})")

        # 4. 模拟请求上下文
        with app.test_request_context(f"/wikis/{wiki.id}/pages/{page.slug}"):
            # 模拟登录
            login_user(user)
            
            # --- 测试 wiki_contributors 函数逻辑 (复刻 app.py 代码) ---
            print("\n--- Testing wiki_contributors logic ---")
            try:
                page_ids = db.session.query(WikiPage.id).filter_by(wiki_id=wiki.id).all()
                page_ids = [p[0] for p in page_ids]
                print(f"Page IDs: {page_ids}")
                
                contributors = []
                if page_ids:
                    contributors = db.session.query(
                        User, 
                        db.func.count(WikiPageHistory.id).label('edit_count')
                    ).join(
                        WikiPageHistory, WikiPageHistory.user_id == User.id
                    ).filter(
                        WikiPageHistory.page_id.in_(page_ids)
                    ).group_by(
                        User.id
                    ).order_by(
                        db.text('edit_count DESC')
                    ).all()
                print(f"Contributors found: {len(contributors)}")
                for c in contributors:
                    print(f"  - {c[0].username}: {c[1]} edits")
            except Exception as e:
                print(f"!!! Error in wiki_contributors logic: {e}")
                import traceback
                traceback.print_exc()

            # --- 测试 view_page 渲染 ---
            print("\n--- Testing view_page rendering ---")
            try:
                # 准备渲染所需变量
                all_pages = WikiPage.query.filter_by(wiki_id=wiki.id).all()
                sorted_pages = all_pages # 简化排序
                html = "<h1>Test Content</h1>"
                is_subscribed = False
                can_edit = True
                
                # 尝试渲染
                rendered = render_template(
                    "wiki/view_page.html",
                    wiki=wiki,
                    page=page,
                    pages=sorted_pages,
                    html=html,
                    can_edit=can_edit,
                    is_subscribed=is_subscribed,
                    contributors=contributors
                )
                print("Render successful!")
                print(f"Rendered length: {len(rendered)}")
            except Exception as e:
                print(f"!!! Error rendering view_page.html: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    try:
        test_wiki_contributors_and_view_page()
    except Exception as e:
        print(f"Global error: {e}")
