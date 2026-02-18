
import os
import sys
from app import app, db, User, Wiki, WikiPage, WikiPageHistory
from sqlalchemy import text

# 设置环境变量以使用正确的数据库
os.environ["DATABASE_URL"] = "sqlite:///wikibook.db"

def debug_view_page_internal():
    with app.app_context():
        # 1. 获取一个 Wiki
        wiki = Wiki.query.first()
        if not wiki:
            print("No wiki found")
            return
        
        print(f"Checking Wiki ID: {wiki.id}")
        
        # 2. 获取所有页面
        all_pages = WikiPage.query.filter_by(wiki_id=wiki.id).all()
        print(f"Total pages: {len(all_pages)}")
        
        if not all_pages:
            print("No pages in this wiki")
            return

        # 3. 模拟 contributors 查询逻辑
        try:
            page_ids_list = [pg.id for pg in all_pages]
            print(f"Page IDs: {page_ids_list}")
            
            query = db.session.query(
                User, 
                db.func.count(WikiPageHistory.id).label('edit_count')
            ).join(
                WikiPageHistory, WikiPageHistory.user_id == User.id
            ).filter(
                WikiPageHistory.page_id.in_(page_ids_list)
            ).group_by(
                User.id
            ).order_by(
                text('edit_count DESC')
            )
            
            print("Executing contributors query...")
            contributors = query.all()
            print(f"Contributors found: {len(contributors)}")
            
            for i, c in enumerate(contributors):
                user = c[0]
                count = c[1] # 或 c.edit_count
                print(f"  Contributor {i}: User={user}, Count={count}")
                if user:
                    print(f"    Username: {user.username}")
                else:
                    print("    User object is None!")
                    
        except Exception as e:
            print(f"Error in contributors query: {e}")
            import traceback
            traceback.print_exc()

def test_request_with_client():
    with app.test_client() as client:
        with app.app_context():
            user = User.query.first()
            if not user: return
            
            with client.session_transaction() as sess:
                sess['_user_id'] = str(user.id)
                sess['_fresh'] = True
                
            wiki = Wiki.query.first()
            if not wiki: return
            page = WikiPage.query.filter_by(wiki_id=wiki.id).first()
            if not page: return
            
            print(f"\n--- Requesting /wikis/{wiki.id}/pages/{page.slug} ---")
            try:
                resp = client.get(f"/wikis/{wiki.id}/pages/{page.slug}")
                print(f"Response Status: {resp.status_code}")
                if resp.status_code == 500:
                    print("Request failed with 500")
            except Exception as e:
                print(f"Request exception: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    print("--- Debugging Internal Logic ---")
    debug_view_page_internal()
    print("\n--- Testing Request ---")
    test_request_with_client()
