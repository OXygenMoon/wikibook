from app import app, db, User

def test():
    with app.app_context():
        try:
            user = User.query.first()
            if not user:
                print("No user found")
                return
            
            print(f"User: {user.username}")
            
            # Test 1: Access study_partners
            print("Testing study_partners...")
            partners = user.study_partners.all()
            print(f"Partners: {len(partners)}")
            
            # Test 2: Access followers count
            print("Testing followers count...")
            count = user.followers.count()
            print(f"Followers count: {count}")
            
            # Test 3: Calculate stats (which uses all above)
            print("Testing calculate_stats...")
            stats = user.calculate_stats()
            print("Stats calculated.")
            
        except Exception as e:
            print("ERROR CAUGHT:")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test()
