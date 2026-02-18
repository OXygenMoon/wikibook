
import os
from app import app, db, User, Wiki, WikiPage, WikiPageHistory
from sqlalchemy import text

os.environ["DATABASE_URL"] = "sqlite:///wikibook.db"

def check_row_type():
    with app.app_context():
        wiki = Wiki.query.first()
        if not wiki: return
        all_pages = WikiPage.query.filter_by(wiki_id=wiki.id).all()
        if not all_pages: return
        page_ids_list = [pg.id for pg in all_pages]
        
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
        
        contributors = query.all()
        if contributors:
            c = contributors[0]
            print(f"Type of row: {type(c)}")
            print(f"Row content: {c}")
            try:
                print(f"Access by index 0: {c[0]}")
                print(f"Access by index 1: {c[1]}")
            except Exception as e:
                print(f"Index access failed: {e}")
                
            try:
                print(f"Access by attr edit_count: {c.edit_count}")
            except Exception as e:
                print(f"Attr edit_count access failed: {e}")
                
            try:
                print(f"Access by attr User: {c.User}")
            except Exception as e:
                print(f"Attr User access failed: {e}")

if __name__ == "__main__":
    check_row_type()
