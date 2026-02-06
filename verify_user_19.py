import sys
from app import app, db, User, UserSticker

def verify_user_relation_and_stickers(target_user_id, current_user_id):
    with app.app_context():
        target_user = User.query.get(target_user_id)
        if not target_user:
            print(f"[Error] Target user {target_user_id} not found")
            return

        print(f"=== Target User: {target_user.username} (ID: {target_user.id}) ===")

        current_user = User.query.get(current_user_id)
        if not current_user:
            print(f"[Error] Current user {current_user_id} not found")
        else:
            print(f"=== Current User: {current_user.username} (ID: {current_user.id}) ===")
            
            follows_target = current_user.is_following(target_user)
            followed_by_target = target_user.is_following(current_user)
            
            print(f"\n[Relationship Check]")
            print(f"1. Does Current follow Target? {'Yes' if follows_target else 'No'}")
            print(f"2. Does Target follow Current? {'Yes' if followed_by_target else 'No'}")
            
            is_mutual = follows_target and followed_by_target
            if is_mutual:
                print(f"==> Result: MUTUAL FOLLOW (Study Partners)")
            else:
                print(f"==> Result: NOT MUTUAL FOLLOW")

        print(f"\n[Sticker Check - User {target_user.id}]")
        stickers = UserSticker.query.filter_by(user_id=target_user.id).all()
        
        if not stickers:
            print("No stickers found for this user.")
        else:
            print(f"Found {len(stickers)} stickers:")
            print(f"{'ID':<5} {'Page':<10} {'BadgeID':<8} {'BadgeName':<20}")
            print("-" * 50)
            for s in stickers:
                badge_name = s.badge.name if s.badge else "Unknown"
                print(f"{s.id:<5} {s.page_type:<10} {s.badge_id:<8} {badge_name:<20}")

if __name__ == "__main__":
    TARGET_USER_ID = 19
    CURRENT_USER_ID = 1 
    if len(sys.argv) > 1:
        try:
            CURRENT_USER_ID = int(sys.argv[1])
        except ValueError:
            pass
    verify_user_relation_and_stickers(TARGET_USER_ID, CURRENT_USER_ID)
