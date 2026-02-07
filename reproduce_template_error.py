from app import app, db, User
from flask import render_template

def test_template():
    with app.app_context():
        user = User.query.first()
        if not user:
            print("No user found")
            return
            
        with app.test_request_context('/'):
            from flask_login import login_user
            login_user(user)
            
            try:
                print("Rendering profile.html...")
                stats = user.calculate_stats()
                user_badges = []
                unearned_badges = []
                recent_notes = []
                is_following = False
                is_study_partner = False
                
                html = render_template("user/profile.html", 
                                     user=user, 
                                     stats=stats, 
                                     user_badges=user_badges, 
                                     unearned_badges=unearned_badges, 
                                     recent_notes=recent_notes, 
                                     is_following=is_following, 
                                     is_study_partner=is_study_partner)
                print("Template rendered successfully.")
            except Exception as e:
                print("TEMPLATE ERROR:")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    test_template()
