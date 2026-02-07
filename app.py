import os
from datetime import datetime, timedelta, timezone
import csv
import io
import openpyxl
from flask import Flask, render_template, redirect, url_for, request, flash, abort, send_file, Response, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mistune
import uuid
import requests
from bs4 import BeautifulSoup
import json
import shutil
import time

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///wikibook.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static/uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB limit
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)  # Keep session for 30 days

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

markdown = mistune.create_markdown(escape=False, plugins=["strikethrough", "table", "url", "task_lists"])

# UTC+8 Helper
def now_utc8():
    return datetime.utcnow() + timedelta(hours=8)

def is_image_icon(s):
    if not s:
        return False
    v = s.strip().lower()
    if v.startswith("http://") or v.startswith("https://") or v.startswith("/"):
        return v.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"))
    if "." in v:
        ext = v.rsplit(".", 1)[-1]
        return ext in ["png", "jpg", "jpeg", "gif", "svg", "webp"]
    return False

def badge_icon_url(s):
    if not s:
        return ""
    v = s.strip()
    if v.startswith("http://") or v.startswith("https://") or v.startswith("/"):
        return v
    if is_image_icon(v):
        if v.startswith("uploads/"):
             return url_for("static", filename=v)
        return url_for("static", filename=f"uploads/{v}")
    return ""

app.jinja_env.filters["is_image_icon"] = is_image_icon
app.jinja_env.filters["badge_icon_url"] = badge_icon_url

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=now_utc8)
    
    # New fields for student information
    real_name = db.Column(db.String(80))
    student_id = db.Column(db.String(20), unique=True)
    department = db.Column(db.String(100))
    class_name = db.Column(db.String(100))
    
    # Badge System
    selected_badge_id = db.Column(db.Integer, db.ForeignKey("badge.id"), nullable=True)
    selected_badge = db.relationship("Badge", foreign_keys=[selected_badge_id])
    
    subscriptions = db.relationship("Subscription", backref="user", cascade="all, delete-orphan")
    editor_roles = db.relationship("WikiEditor", backref="user", cascade="all, delete-orphan")
    notes = db.relationship("Note", backref="user", cascade="all, delete-orphan")
    shared_notes = db.relationship("NoteShare", backref="user", cascade="all, delete-orphan")
    earned_badges = db.relationship("UserBadge", backref="user", cascade="all, delete-orphan")

    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def is_followed_by(self, user):
        return self.followers.filter(followers.c.follower_id == user.id).count() > 0

    @property
    def is_online(self):
        if not self.active_status or not self.active_status.last_active_at:
            return False
        return self.active_status.last_active_at > (now_utc8() - timedelta(minutes=5))

    @property
    def last_active_human(self):
        if not self.active_status or not self.active_status.last_active_at:
            return "从未上线"
        diff = now_utc8() - self.active_status.last_active_at
        seconds = diff.total_seconds()
        if seconds < 60:
            return "刚刚"
        minutes = seconds / 60
        if minutes < 60:
            return f"{int(minutes)}分钟前"
        hours = minutes / 60
        if hours < 24:
            return f"{int(hours)}小时前"
        days = hours / 24
        if days < 7:
            return f"{int(days)}天前"
        if days < 30:
            return f"{int(days/7)}周前"
        if days < 365:
            return f"{int(days/30)}个月前"
        return f"{int(days/365)}年前"

    @property
    def study_time_today_human(self):
        now = now_utc8()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        sessions = StudySession.query.filter(
            StudySession.user_id == self.id,
            StudySession.start_time >= start_of_day
        ).all()
        total_seconds = sum([(s.end_time - s.start_time).total_seconds() for s in sessions if (s.end_time - s.start_time).total_seconds() > 0])
        
        if total_seconds < 60:
            return "少于1分钟"
        m, s = divmod(total_seconds, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{int(h)}小时 {int(m)}分钟"
        else:
            return f"{int(m)}分钟"

    @property
    def latest_earned_badge(self):
        return UserBadge.query.filter_by(user_id=self.id).order_by(UserBadge.earned_at.desc()).first()

    @property
    def badges(self):
        return self.earned_badges

    @property
    def wikis(self):
        return Wiki.query.filter_by(created_by_id=self.id).all()

    @property
    def study_partners(self):
        """Return a query for users that are mutually following each other."""
        # Users I follow who also follow me
        # Subquery: IDs of people who follow me
        subquery = db.session.query(followers.c.follower_id).filter(followers.c.followed_id == self.id)
        # Filter my followed list by that subquery
        return self.followed.filter(User.id.in_(subquery))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_selected_user_badge(self):
        if not self.selected_badge_id:
            return None
        return UserBadge.query.filter_by(user_id=self.id, badge_id=self.selected_badge_id).first()

    def calculate_stats(self):
        """Calculate all detailed statistics for the user."""
        stats = {
            "wiki_count": Wiki.query.filter_by(created_by_id=self.id).count(),
            "note_count": Note.query.filter_by(user_id=self.id).count(),
            "badge_count": len(self.earned_badges),
            "study_partner_count": self.study_partners.count(),
            "following_count": self.followed.count(),
            "follower_count": self.followers.count(),
            "comment_count": Comment.query.filter_by(user_id=self.id).count(),
            "wiki_edit_count": WikiPageHistory.query.filter_by(user_id=self.id).count(),
            "streak_days": 0,
            "study_hours": 0.0,
            "night_owl_days": 0,
            "early_bird_days": 0,
            "weekend_study_hours": 0.0,
            "long_sessions": 0,
            "total_views_received": NoteViewLog.query.join(Note).filter(Note.user_id == self.id).count(),
            "share_count": NoteShare.query.join(Note).filter(Note.user_id == self.id).count()
        }

        # Study Session Analysis
        sessions = StudySession.query.filter_by(user_id=self.id).all()
        
        # 1. Study Hours
        total_seconds = sum([(s.end_time - s.start_time).total_seconds() for s in sessions if (s.end_time - s.start_time).total_seconds() > 0])
        stats["study_hours"] = round(total_seconds / 3600, 1)

        # 2. Streak
        sorted_sessions = sorted(sessions, key=lambda x: x.start_time, reverse=True)
        dates = sorted(list(set([s.start_time.date() for s in sorted_sessions])), reverse=True)
        streak = 0
        if dates:
            today = now_utc8().date()
            if dates[0] == today:
                streak = 1
                current = today
            elif dates[0] == today - timedelta(days=1):
                streak = 1
                current = today - timedelta(days=1)
            else:
                streak = 0
            if streak > 0:
                for i in range(1, len(dates)):
                    if dates[i] == current - timedelta(days=1):
                        streak += 1
                        current = dates[i]
                    else:
                        break
        stats["streak_days"] = streak

        # 3. Time Patterns
        night_days = set()
        early_days = set()
        weekend_seconds = 0
        long_count = 0

        for s in sessions:
            # Night Owl
            h = s.start_time.hour
            if h >= 23 or h < 4:
                logical_date = (s.start_time - timedelta(hours=4)).date()
                night_days.add(logical_date)
            
            # Early Bird
            if 5 <= h < 8:
                early_days.add(s.start_time.date())
            
            # Weekend
            if s.start_time.weekday() in [5, 6]:
                duration = (s.end_time - s.start_time).total_seconds()
                if duration > 0:
                    weekend_seconds += duration
            
            # Long Session
            duration = (s.end_time - s.start_time).total_seconds()
            if duration >= 7200:
                long_count += 1
        
        stats["night_owl_days"] = len(night_days)
        stats["early_bird_days"] = len(early_days)
        stats["weekend_study_hours"] = round(weekend_seconds / 3600, 1)
        stats["long_sessions"] = long_count

        return stats

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=now_utc8)
    type = db.Column(db.String(50), default='system') # system, friend_login, friend_achievement
    link = db.Column(db.String(200), nullable=True)

    user = db.relationship("User", backref=db.backref("notifications", lazy="dynamic", cascade="all, delete-orphan"))

class SystemAnnouncement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False) # Markdown
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=now_utc8)
    updated_at = db.Column(db.DateTime, default=now_utc8, onupdate=now_utc8)
    is_active = db.Column(db.Boolean, default=True)

    creator = db.relationship("User", backref="created_announcements")

class UserAnnouncementConfirmation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    announcement_id = db.Column(db.Integer, db.ForeignKey('system_announcement.id'), nullable=False)
    confirmed_at = db.Column(db.DateTime, default=now_utc8)
    
    user = db.relationship("User", backref="announcement_confirmations")
    announcement = db.relationship("SystemAnnouncement", backref="confirmations")

class AnnouncementFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=now_utc8)
    
    uploader = db.relationship("User", backref="uploaded_announcement_files")

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(255), nullable=False) # Emoji or FontAwesome class
    condition_type = db.Column(db.String(50), nullable=False) # streak_days, study_hours, featured_count, note_count
    condition_value = db.Column(db.Integer, nullable=False)
    is_hidden = db.Column(db.Boolean, default=False) # Hidden badges won't show conditions until earned
    sticker_count = db.Column(db.Integer, default=1) # Number of stickers this badge provides
    total_limit = db.Column(db.Integer, nullable=True) # Max number of users who can earn this badge (Null = infinite)
    issued_count = db.Column(db.Integer, default=0) # Current number of users who earned this
    start_time = db.Column(db.DateTime, nullable=True) # For time-limited badges
    end_time = db.Column(db.DateTime, nullable=True) # For time-limited badges
    created_at = db.Column(db.DateTime, default=now_utc8)
    
    users = db.relationship("UserBadge", backref="badge_info", lazy="dynamic")

class UserBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey("badge.id"), nullable=False)
    earned_at = db.Column(db.DateTime, default=now_utc8)
    
    badge = db.relationship("Badge")

class Wiki(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=now_utc8)
    pages = db.relationship("WikiPage", backref="wiki", cascade="all, delete-orphan")
    subscriptions = db.relationship("Subscription", backref="wiki", cascade="all, delete-orphan")
    editors = db.relationship("WikiEditor", backref="wiki", cascade="all, delete-orphan")

class WikiPage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wiki_id = db.Column(db.Integer, db.ForeignKey("wiki.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False) # 实际上现在存储的是整数
    content_md = db.Column(db.Text, default="")
    view_count = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=now_utc8, onupdate=now_utc8)
    
    comment_enabled = db.Column(db.Boolean, default=True)

    tags = db.relationship('Tag', secondary='wiki_page_tags', backref=db.backref('pages', lazy='dynamic'))
    comments = db.relationship('Comment', backref='wiki_page', cascade="all, delete-orphan", order_by="desc(Comment.created_at)")

class UserActiveStatus(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    last_active_at = db.Column(db.DateTime, default=now_utc8)
    current_path = db.Column(db.String(500), default="/")
    current_action = db.Column(db.String(200), default="")
    
    user = db.relationship("User", backref=db.backref("active_status", uselist=False))

class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    start_time = db.Column(db.DateTime, default=now_utc8)
    end_time = db.Column(db.DateTime, default=now_utc8)
    
    user = db.relationship("User", backref="study_sessions")

class WikiViewLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wiki_id = db.Column(db.Integer, db.ForeignKey("wiki.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True) # 可以记录匿名访问，如果需要
    timestamp = db.Column(db.DateTime, default=now_utc8)

class WikiPageHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey("wiki_page.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False)
    content_md = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=now_utc8)
    
    user = db.relationship("User", backref="page_history")
    page = db.relationship("WikiPage", backref=db.backref("history", cascade="all, delete-orphan", order_by="desc(WikiPageHistory.created_at)"))

class WikiEditor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wiki_id = db.Column(db.Integer, db.ForeignKey("wiki.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class WikiFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wiki_id = db.Column(db.Integer, db.ForeignKey("wiki.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=now_utc8)
    
    wiki = db.relationship("Wiki", backref=db.backref("files", cascade="all, delete-orphan"))
    uploader = db.relationship("User", backref="uploaded_files")

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wiki_id = db.Column(db.Integer, db.ForeignKey("wiki.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=now_utc8)

class MarkdownStyle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    css_text = db.Column(db.Text, default="")
    updated_at = db.Column(db.DateTime, default=now_utc8, onupdate=now_utc8)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content_md = db.Column(db.Text, default="")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=now_utc8)
    updated_at = db.Column(db.DateTime, default=now_utc8, onupdate=now_utc8)
    
    comment_enabled = db.Column(db.Boolean, default=True)

    shares = db.relationship("NoteShare", backref="note", cascade="all, delete-orphan")
    
    tags = db.relationship('Tag', secondary='note_tags', backref=db.backref('notes', lazy='dynamic'))
    comments = db.relationship('Comment', backref='note', cascade="all, delete-orphan", order_by="desc(Comment.created_at)")

    @property
    def view_count(self):
        return NoteViewLog.query.filter_by(note_id=self.id).count()

class NoteShare(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey("note.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False) # Receiver
    created_at = db.Column(db.DateTime, default=now_utc8)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

# Association tables for Tags
note_tags = db.Table('note_tags',
    db.Column('note_id', db.Integer, db.ForeignKey('note.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

wiki_page_tags = db.Table('wiki_page_tags',
    db.Column('page_id', db.Integer, db.ForeignKey('wiki_page.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=now_utc8)
    
    # Polymorphic-like association (nullable FKs)
    note_id = db.Column(db.Integer, db.ForeignKey("note.id"), nullable=True)
    wiki_page_id = db.Column(db.Integer, db.ForeignKey("wiki_page.id"), nullable=True)
    
    user = db.relationship("User", backref="comments")
    # Relationships will be defined in Note and WikiPage models for backrefs

class NoteViewLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey("note.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=now_utc8)

class UserSticker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey("badge.id"), nullable=False)
    page_type = db.Column(db.String(20), nullable=False) # 'wiki' or 'book'
    x = db.Column(db.Float, default=50.0) # Percentage
    y = db.Column(db.Float, default=50.0) # Percentage
    rotation = db.Column(db.Float, default=0.0) # Degrees
    scale = db.Column(db.Float, default=1.0)
    z_index = db.Column(db.Integer, default=1)
    
    badge = db.relationship("Badge")
    user = db.relationship("User", backref="stickers")

class StickerBoardSnapshot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    page_type = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(100), nullable=True)
    caption = db.Column(db.Text, nullable=True)
    visibility = db.Column(db.String(20), default='private') # private, followers, public
    data_json = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=now_utc8)
    likes_count = db.Column(db.Integer, default=0)
    
    user = db.relationship("User", backref="sticker_snapshots")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def can_edit_wiki(wiki_id):
    if not current_user.is_authenticated:
        return False
    if current_user.is_admin:
        return True
    return WikiEditor.query.filter_by(wiki_id=wiki_id, user_id=current_user.id).first() is not None

def can_view_wiki(wiki_id):
    if not current_user.is_authenticated:
        return False
    if current_user.is_admin:
        return True
    if can_edit_wiki(wiki_id):
        return True
    return Subscription.query.filter_by(wiki_id=wiki_id, user_id=current_user.id).first() is not None

def process_tags(tag_string):
    if not tag_string:
        return []
    # Support comma or space separation? Let's stick to comma for multi-word tags support
    # But usually space is easier. Let's support comma.
    # Replace Chinese comma
    tag_string = tag_string.replace('，', ',')
    tag_names = set([t.strip() for t in tag_string.split(',') if t.strip()])
    tags = []
    for name in tag_names:
        tag = Tag.query.filter_by(name=name).first()
        if not tag:
            tag = Tag(name=name)
            db.session.add(tag)
        tags.append(tag)
    return tags

def backup_wiki(wiki_id):
    """
    Backup wiki data to a JSON file and copy associated files.
    Returns the backup directory path.
    """
    w = Wiki.query.get(wiki_id)
    if not w:
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = os.path.join(app.root_path, "backups")
    backup_dir = os.path.join(backup_root, f"wiki_{wiki_id}_{timestamp}")
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # 1. Backup Metadata and Structure
    data = {
        "wiki": {
            "id": w.id,
            "title": w.title,
            "description": w.description,
            "created_by_id": w.created_by_id,
            "created_at": w.created_at.isoformat() if w.created_at else None
        },
        "pages": [],
        "files": [],
        "editors": [e.user_id for e in w.editors],
        "subscribers": [s.user_id for s in w.subscriptions]
    }

    # Pages
    for p in w.pages:
        page_data = {
            "id": p.id,
            "title": p.title,
            "slug": p.slug,
            "content_md": p.content_md,
            "view_count": p.view_count,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            "tags": [t.name for t in p.tags],
            "comments": [
                {
                    "user_id": c.user_id,
                    "content": c.content,
                    "created_at": c.created_at.isoformat() if c.created_at else None
                } for c in p.comments
            ],
            "history": [
                {
                    "user_id": h.user_id,
                    "title": h.title,
                    "slug": h.slug,
                    "content_md": h.content_md,
                    "created_at": h.created_at.isoformat() if h.created_at else None
                } for h in p.history
            ]
        }
        data["pages"].append(page_data)

    # Files
    files_dir = os.path.join(backup_dir, "files")
    if not os.path.exists(files_dir):
        os.makedirs(files_dir)

    for f in w.files:
        file_data = {
            "id": f.id,
            "filename": f.filename,
            "file_path": f.file_path,
            "uploaded_by_id": f.uploaded_by_id,
            "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None
        }
        data["files"].append(file_data)
        
        # Copy physical file
        # Assuming f.filename matches the file in UPLOAD_FOLDER
        # However, upload logic uses unique_filename. 
        # In upload_wiki_file: 
        # unique_filename = str(uuid.uuid4()) + ext
        # file.save(os.path.join(upload_dir, unique_filename))
        # wf = WikiFile(..., filename=filename, ...) <- This stores original filename!
        # Wait, the physical filename is NOT stored in WikiFile directly?
        # file_path stores url_for("static", filename=f"uploads/{unique_filename}")
        # So we need to extract unique_filename from file_path.
        
        try:
            # f.file_path is like /static/uploads/UUID.ext
            if "/static/uploads/" in f.file_path:
                unique_filename = f.file_path.split("/static/uploads/")[-1]
                src_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
                if os.path.exists(src_path):
                    shutil.copy2(src_path, os.path.join(files_dir, unique_filename))
        except Exception as e:
            print(f"Error copying file {f.id}: {e}")

    # Write JSON
    with open(os.path.join(backup_dir, "data.json"), "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)

    return backup_dir

@app.before_request
def ensure_db():
    with app.app_context():
        db.create_all()
        if MarkdownStyle.query.first() is None:
            s = MarkdownStyle(css_text="")
            db.session.add(s)
            db.session.commit()

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    user_id = request.args.get("user_id")
    target_user = None
    if user_id:
        if not current_user.is_authenticated:
            # 未登录用户不允许查看其他人的贴纸，重定向到登录页或返回主页
            # 这里选择忽略 user_id，直接按默认首页（无 target_user）处理
            # 也可以选择: return redirect(url_for('login'))
            pass 
        else:
            try:
                potential_target = User.query.get(int(user_id))
                if potential_target:
                    # 检查权限：是自己，或者是学友（互相关注）
                    # 注意：原始需求是“学友”，即互相关注。
                    # 如果只是关注（follower），使用 current_user.is_following(potential_target)
                    # 如果必须互相关注，需检查双向。
                    # 根据上下文，之前的API检查是 is_following。
                    # 用户新需求："应该同时存在登录用户和被查看用户的id在url中，且要计算是否是对方的学友"
                    # 我们定义“学友”为互相关注。
                    
                    if potential_target.id == current_user.id:
                        target_user = potential_target
                    else:
                        # 检查是否互相关注 (is_friend / study_partner)
                        # User模型没有直接的 is_friend 方法，但我们可以检查双向关注
                        # A follows B AND B follows A
                        if current_user.is_following(potential_target) and potential_target.is_following(current_user):
                            target_user = potential_target
                        else:
                            # 不是学友，不允许查看，target_user 保持 None
                            # 可选：flash("您和该用户不是学友关系，无法参观贴纸板")
                            pass
            except:
                pass
            
    if q:
        # 搜索 Wiki 标题
        wikis = Wiki.query.filter(Wiki.title.contains(q)).order_by(Wiki.created_at.desc()).all()
        
        # 搜索 Wiki 页面内容
        pages = WikiPage.query.filter(
            (WikiPage.title.contains(q)) | (WikiPage.content_md.contains(q))
        ).all()
    else:
        wikis = Wiki.query.order_by(Wiki.created_at.desc()).all()
        pages = []
        
    return render_template("index.html", wikis=wikis, pages=pages, q=q, target_user=target_user)

@app.route("/register", methods=["GET", "POST"])
def register():
    # 关闭注册功能
    flash("注册功能已关闭，请联系管理员")
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"  # Get remember me checkbox
        
        u = User.query.filter_by(username=username).first()
        if not u or not u.check_password(password):
            flash("用户名或密码错误")
            return redirect(url_for("login"))
            
        login_user(u, remember=remember) # Use remember me
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/admin/wikis/new", methods=["GET", "POST"])
@login_required
def create_wiki():
    if not current_user.is_admin:
        abort(403)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        if not title:
            flash("标题不能为空")
            return redirect(url_for("create_wiki"))
        w = Wiki(title=title, description=description, created_by_id=current_user.id)
        db.session.add(w)
        db.session.commit()
        
        # Check initialization options
        init_home = request.form.get("init_home") == "on"
        if init_home:
            home_page = WikiPage(
                wiki_id=w.id,
                title="欢迎",
                slug="home",
                content_md=f"# 欢迎来到 {w.title}\n\n{w.description or '这是一个新的 Wiki 知识库。'}\n\n## 开始使用\n\n- 点击右上角的编辑按钮修改此页面\n- 点击侧边栏的“新建页面”添加更多内容\n"
            )
            db.session.add(home_page)
            db.session.commit()
            
            # Create a view log for the creator
            log = WikiViewLog(wiki_id=w.id, user_id=current_user.id)
            db.session.add(log)
            db.session.commit()
            
            return redirect(url_for("view_page", wiki_id=w.id, slug="home"))
            
        return redirect(url_for("wiki_detail", wiki_id=w.id))
    return render_template("admin/create_wiki.html")

@app.route("/wikis/<int:wiki_id>")
@login_required
def wiki_detail(wiki_id):
    w = Wiki.query.get_or_404(wiki_id)
    # 详情页允许所有登录用户访问，以便订阅
    all_pages = WikiPage.query.filter_by(wiki_id=wiki_id).all()
    
    # 排序逻辑（复用）
    def page_sort_key(page):
        try:
            val = int(page.slug)
        except ValueError:
            val = 999999
        return val

    pages = sorted(all_pages, key=page_sort_key)
    
    is_editor = can_edit_wiki(wiki_id)
    is_subscribed = Subscription.query.filter_by(wiki_id=wiki_id, user_id=current_user.id).first() is not None
    
    # 如果有页面，默认显示第一个页面；否则只显示 Wiki 信息
    first_page = pages[0] if pages else None
    html = markdown(first_page.content_md or "") if first_page else ""
    
    if first_page:
        # 记录首页浏览日志
        log = WikiViewLog(wiki_id=wiki_id, user_id=current_user.id)
        db.session.add(log)
        first_page.view_count += 1
        db.session.commit()
    
    return render_template("wiki/view_page.html", wiki=w, page=first_page, pages=pages, html=html, can_edit=is_editor, is_subscribed=is_subscribed, is_home=True)

@app.route("/admin/wikis/<int:wiki_id>/edit", methods=["GET", "POST"])
@login_required
def edit_wiki(wiki_id):
    if not current_user.is_admin:
        abort(403)
    w = Wiki.query.get_or_404(wiki_id)
    if request.method == "POST":
        w.title = request.form.get("title", "").strip()
        w.description = request.form.get("description", "").strip()
        if not w.title:
            flash("标题不能为空")
            return redirect(url_for("edit_wiki", wiki_id=wiki_id))
        db.session.commit()
        flash("Wiki 信息已更新")
        return redirect(url_for("wiki_detail", wiki_id=w.id))
    return render_template("admin/edit_wiki.html", wiki=w)

@app.route("/admin/wikis/<int:wiki_id>/delete", methods=["POST"])
@login_required
def delete_wiki(wiki_id):
    if not current_user.is_admin:
        abort(403)
        
    w = Wiki.query.get_or_404(wiki_id)
    
    # Backup first
    try:
        backup_path = backup_wiki(wiki_id)
        if not backup_path:
             flash("备份失败，操作取消")
             return redirect(url_for("edit_wiki", wiki_id=wiki_id))
    except Exception as e:
        flash(f"备份过程中出错: {str(e)}")
        return redirect(url_for("edit_wiki", wiki_id=wiki_id))
        
    # Delete Wiki
    try:
        db.session.delete(w)
        db.session.commit()
        flash(f"Wiki 已删除。备份已保存至: {backup_path}")
        return redirect(url_for("index"))
    except Exception as e:
        db.session.rollback()
        flash(f"删除失败: {str(e)}")
        return redirect(url_for("edit_wiki", wiki_id=wiki_id))


@app.route("/wikis/<int:wiki_id>/subscribe", methods=["POST"])
@login_required
def subscribe_wiki(wiki_id):
    w = Wiki.query.get_or_404(wiki_id)
    sub = Subscription.query.filter_by(wiki_id=wiki_id, user_id=current_user.id).first()
    if sub:
        # 取消订阅
        db.session.delete(sub)
    else:
        # 订阅
        s = Subscription(wiki_id=wiki_id, user_id=current_user.id)
        db.session.add(s)
    db.session.commit()
    # 获取来源页面，如果未指定则重定向到详情页
    next_page = request.args.get("next")
    if not next_page:
        next_page = url_for("wiki_detail", wiki_id=wiki_id)
    return redirect(next_page)

@app.route("/wikis/<int:wiki_id>/pages/new", methods=["GET", "POST"])
@login_required
def new_page(wiki_id):
    w = Wiki.query.get_or_404(wiki_id)
    if not can_edit_wiki(wiki_id):
        abort(403)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        slug = request.form.get("slug", "").strip()
        content_md = request.form.get("content_md", "")
        tags_str = request.form.get("tags", "")
        
        if not title or not slug:
            flash("标题与标识不能为空")
            return redirect(url_for("new_page", wiki_id=wiki_id))
        p = WikiPage(wiki_id=wiki_id, title=title, slug=slug, content_md=content_md)
        
        # Process tags
        p.tags = process_tags(tags_str)
        
        db.session.add(p)
        db.session.commit()
        
        # Check badges (Wiki Create Count, Wiki Edit Count)
        check_and_award_badges(current_user)
        
        return redirect(url_for("view_page", wiki_id=wiki_id, slug=slug))
    return render_template("wiki/new_page.html", wiki=w)

@app.route("/wikis/<int:wiki_id>/pages/<slug>")
@login_required
def view_page(wiki_id, slug):
    w = Wiki.query.get_or_404(wiki_id)
    # 详情页允许所有登录用户访问，以便订阅
    p = WikiPage.query.filter_by(wiki_id=wiki_id, slug=slug).first_or_404()
    
    # 记录浏览日志
    log = WikiViewLog(wiki_id=wiki_id, user_id=current_user.id)
    db.session.add(log)
    p.view_count += 1
    db.session.commit()
    
    # 排序逻辑：
    # 1. 尝试将 slug 转换为整数
    # 2. 负数（置顶）升序：-10, -5, -1
    # 3. 正数（普通）升序：1, 2, 5, 10
    all_pages = WikiPage.query.filter_by(wiki_id=wiki_id).all()
    
    def page_sort_key(page):
        try:
            val = int(page.slug)
        except ValueError:
            val = 999999 # 非整数排在最后
        
        # 为了让负数排在正数前面，且各自内部升序
        # 负数保持原值（越小越前？不，用户说“负数为置顶, 且按照负数升序置顶”）
        # 假设用户意思是：-5, -2, -1 这样排在 1, 2, 3 前面
        # 还是 -1, -2, -5？通常置顶是数字越小越靠前，或者特定的置顶区
        # 用户原话：“负数为置顶, 且按照负数升序置顶”。即 -10 在 -1 前面。
        # 那么直接按照数值升序即可：-10 < -1 < 1 < 10
        return val

    sorted_pages = sorted(all_pages, key=page_sort_key)
    
    html = markdown(p.content_md or "")
    is_subscribed = Subscription.query.filter_by(wiki_id=wiki_id, user_id=current_user.id).first() is not None
    return render_template("wiki/view_page.html", wiki=w, page=p, pages=sorted_pages, html=html, can_edit=can_edit_wiki(wiki_id), is_subscribed=is_subscribed)

@app.route("/wikis/<int:wiki_id>/pages/<slug>/edit", methods=["GET", "POST"])
@login_required
def edit_page(wiki_id, slug):
    w = Wiki.query.get_or_404(wiki_id)
    if not can_edit_wiki(wiki_id):
        abort(403)
    p = WikiPage.query.filter_by(wiki_id=wiki_id, slug=slug).first_or_404()
    if request.method == "POST":
        # 保存历史版本
        history = WikiPageHistory(
            page_id=p.id,
            user_id=current_user.id,
            title=p.title,
            slug=p.slug,
            content_md=p.content_md
        )
        db.session.add(history)
        
        # 更新页面
        p.title = request.form.get("title", "").strip()
        p.slug = request.form.get("slug", "").strip()
        p.content_md = request.form.get("content_md", "")
        tags_str = request.form.get("tags", "")
        
        # Update tags
        p.tags = process_tags(tags_str)
        
        # Update settings
        p.comment_enabled = request.form.get("comment_enabled") == "on"
        
        db.session.commit()
        
        # Check badges
        check_and_award_badges(current_user)
        
        return redirect(url_for("view_page", wiki_id=wiki_id, slug=p.slug))
    return render_template("wiki/edit_page.html", wiki=w, page=p)

@app.route("/wikis/<int:wiki_id>/pages/<slug>/comment", methods=["POST"])
@login_required
def comment_wiki_page(wiki_id, slug):
    w = Wiki.query.get_or_404(wiki_id)
    # Check view permission
    if not can_view_wiki(wiki_id):
        abort(403)
        
    p = WikiPage.query.filter_by(wiki_id=wiki_id, slug=slug).first_or_404()
    
    content = request.form.get("content", "").strip()
    if content:
        c = Comment(content=content, user_id=current_user.id, wiki_page_id=p.id)
        db.session.add(c)
        db.session.commit()
        
        # Check badges
        check_and_award_badges(current_user)
        
        flash("评论已发表")
    else:
        flash("评论内容不能为空")
        
    return redirect(url_for("view_page", wiki_id=wiki_id, slug=slug))

@app.route("/comments/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    c = Comment.query.get_or_404(comment_id)
    
    # Check permission:
    # 1. Comment author
    # 2. Admin
    # 3. Content owner (Note or Wiki Page owner) - Logic below
    
    is_allowed = False
    
    if current_user.id == c.user_id or current_user.is_admin:
        is_allowed = True
    elif c.note_id:
        note = Note.query.get(c.note_id)
        if note and note.user_id == current_user.id:
            is_allowed = True
    elif c.wiki_page_id:
        page = WikiPage.query.get(c.wiki_page_id)
        # For wiki pages, "owner" is tricky. Let's say wiki admins/editors can delete?
        # Or specifically the wiki creator? 
        # For now let's stick to Wiki Editor permission
        if page:
             if can_edit_wiki(page.wiki_id):
                 is_allowed = True
                 
    if not is_allowed:
        abort(403)
        
    # Get redirect URL before deletion
    next_url = request.referrer
    if not next_url:
        if c.note_id:
            next_url = url_for("view_note", note_id=c.note_id)
        elif c.wiki_page_id:
            # Need to fetch page/wiki info to construct URL if referrer is missing
            page = WikiPage.query.get(c.wiki_page_id)
            if page:
                next_url = url_for("view_page", wiki_id=page.wiki_id, slug=page.slug)
            else:
                next_url = url_for("index")
        else:
            next_url = url_for("index")
            
    db.session.delete(c)
    db.session.commit()
    flash("评论已删除")
    return redirect(next_url)

@app.route("/wikis/<int:wiki_id>/pages/<slug>/history")
@login_required
def page_history(wiki_id, slug):
    w = Wiki.query.get_or_404(wiki_id)
    p = WikiPage.query.filter_by(wiki_id=wiki_id, slug=slug).first_or_404()
    if not can_edit_wiki(wiki_id):
        abort(403)
    return render_template("wiki/page_history.html", wiki=w, page=p)

@app.route("/wikis/<int:wiki_id>/pages/<slug>/history/<int:history_id>/restore", methods=["POST"])
@login_required
def restore_page(wiki_id, slug, history_id):
    if not can_edit_wiki(wiki_id):
        abort(403)
    p = WikiPage.query.filter_by(wiki_id=wiki_id, slug=slug).first_or_404()
    h = WikiPageHistory.query.get_or_404(history_id)
    
    if h.page_id != p.id:
        abort(404)
        
    current_history = WikiPageHistory(
        page_id=p.id,
        user_id=current_user.id,
        title=p.title,
        slug=p.slug,
        content_md=p.content_md
    )
    db.session.add(current_history)
    
    p.title = h.title
    p.slug = h.slug
    p.content_md = h.content_md
    db.session.commit()
    
    flash(f"已恢复到 {h.created_at.strftime('%Y-%m-%d %H:%M')} 的版本")
    return redirect(url_for("view_page", wiki_id=wiki_id, slug=p.slug))

@app.route("/wikis/<int:wiki_id>/pages/<slug>/delete", methods=["POST"])
@login_required
def delete_page(wiki_id, slug):
    w = Wiki.query.get_or_404(wiki_id)
    if not can_edit_wiki(wiki_id):
        abort(403)
    p = WikiPage.query.filter_by(wiki_id=wiki_id, slug=slug).first_or_404()
    db.session.delete(p)
    db.session.commit()
    flash("页面已删除")
    return redirect(url_for("wiki_detail", wiki_id=wiki_id))

@app.route("/admin/wikis/<int:wiki_id>/stats")
@login_required
def wiki_stats(wiki_id):
    if not current_user.is_admin:
        abort(403)
    w = Wiki.query.get_or_404(wiki_id)
    subscribers = User.query.join(Subscription).filter(Subscription.wiki_id == wiki_id).all()
    now = datetime.utcnow()
    periods = {
        "1h": now - timedelta(hours=1),
        "12h": now - timedelta(hours=12),
        "1d": now - timedelta(days=1),
        "1w": now - timedelta(weeks=1),
        "1m": now - timedelta(days=30),
        "3m": now - timedelta(days=90),
        "6m": now - timedelta(days=180),
        "1y": now - timedelta(days=365)
    }
    view_stats = {}
    sub_stats = {}
    for label, start_time in periods.items():
        view_stats[label] = WikiViewLog.query.filter(WikiViewLog.wiki_id == wiki_id, WikiViewLog.timestamp >= start_time).count()
        sub_stats[label] = Subscription.query.filter(Subscription.wiki_id == wiki_id, Subscription.created_at >= start_time).count()
    return render_template("admin/wiki_stats.html", wiki=w, subscribers=subscribers, view_stats=view_stats, sub_stats=sub_stats)

@app.route("/admin/wikis/<int:wiki_id>/editors", methods=["GET", "POST"])
@login_required
def manage_editors(wiki_id):
    if not current_user.is_admin:
        abort(403)
    w = Wiki.query.get_or_404(wiki_id)
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        u = User.query.filter_by(username=username).first()
        if not u:
            flash("用户不存在")
            return redirect(url_for("manage_editors", wiki_id=wiki_id))
        if WikiEditor.query.filter_by(wiki_id=wiki_id, user_id=u.id).first() is None:
            e = WikiEditor(wiki_id=wiki_id, user_id=u.id)
            db.session.add(e)
            db.session.commit()
        return redirect(url_for("manage_editors", wiki_id=wiki_id))
    
    # Get all users who are editors for this wiki
    editors = User.query.join(WikiEditor, WikiEditor.user_id == User.id).filter(WikiEditor.wiki_id == wiki_id).all()
    return render_template("admin/manage_editors.html", wiki=w, editors=editors)

@app.route("/admin/wikis/<int:wiki_id>/editors/<int:user_id>/remove", methods=["POST"])
@login_required
def remove_editor(wiki_id, user_id):
    if not current_user.is_admin:
        abort(403)
        
    w = Wiki.query.get_or_404(wiki_id)
    editor = WikiEditor.query.filter_by(wiki_id=wiki_id, user_id=user_id).first_or_404()
    
    # Prevent removing the creator (optional safety, but good practice)
    if user_id == w.created_by_id:
        flash("无法移除 Wiki 创建者的编辑权限")
        return redirect(url_for("manage_editors", wiki_id=wiki_id))
        
    db.session.delete(editor)
    db.session.commit()
    flash("编辑权限已移除")
    return redirect(url_for("manage_editors", wiki_id=wiki_id))

@app.route("/admin/wikis/<int:wiki_id>/files", methods=["GET", "POST"])
@login_required
def manage_files(wiki_id):
    if not can_edit_wiki(wiki_id):
        abort(403)
        
    w = Wiki.query.get_or_404(wiki_id)
    files = WikiFile.query.filter_by(wiki_id=wiki_id).order_by(WikiFile.uploaded_at.desc()).all()
    
    return render_template("admin/wiki_files.html", wiki=w, files=files)

@app.route("/admin/wikis/<int:wiki_id>/files/upload", methods=["POST"])
@login_required
def upload_wiki_file(wiki_id):
    if not can_edit_wiki(wiki_id):
        return {"error": "Permission denied"}, 403
        
    if "image" not in request.files:
        return {"error": "No file part"}, 400
    file = request.files["image"]
    if file.filename == "":
        return {"error": "No selected file"}, 400
    if file:
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
             app.logger.error(f"Upload failed: Invalid extension '{ext}' for file '{filename}'")
             return {"error": f"File type '{ext}' not allowed. Allowed: jpg, png, gif, webp"}, 400
        unique_filename = str(uuid.uuid4()) + ext
        
        # Ensure uploads directory exists
        upload_dir = app.config["UPLOAD_FOLDER"]
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            
        file.save(os.path.join(upload_dir, unique_filename))
        
        file_path = url_for("static", filename=f"uploads/{unique_filename}")
        
        # Record in DB
        wf = WikiFile(
            wiki_id=wiki_id, 
            filename=filename, 
            file_path=file_path, 
            uploaded_by_id=current_user.id
        )
        db.session.add(wf)
        db.session.commit()
        
        return {"data": {"filePath": file_path, "filename": filename}}

@app.route("/admin/wikis/<int:wiki_id>/files/<int:file_id>/delete", methods=["POST"])
@login_required
def delete_wiki_file(wiki_id, file_id):
    if not can_edit_wiki(wiki_id):
        abort(403)
        
    wf = WikiFile.query.get_or_404(file_id)
    if wf.wiki_id != wiki_id:
        abort(404)
        
    # Optional: Delete actual file from disk? 
    # For now, just remove DB record to keep it simple and safe
    # If deleting from disk, need to map URL back to file path
    
    db.session.delete(wf)
    db.session.commit()
    flash("文件已删除")
    return redirect(url_for("manage_files", wiki_id=wiki_id))

@app.route("/assets/markdown.css")
def markdown_css():
    s = MarkdownStyle.query.first()
    css = s.css_text if s else ""
    return Response(css, mimetype="text/css")

@app.route("/admin/markdown-css", methods=["GET", "POST"])
@login_required
def edit_markdown_css():
    if not current_user.is_admin:
        abort(403)
    s = MarkdownStyle.query.first()
    if request.method == "POST":
        css_text = request.form.get("css_text", "")
        s.css_text = css_text
        db.session.commit()
        return redirect(url_for("edit_markdown_css"))
    return render_template("admin/markdown_css.html", css_text=s.css_text if s else "")

@app.route("/upload", methods=["POST"])
@login_required
def upload_file():
    if "image" not in request.files:
        return {"error": "No file part"}, 400
    file = request.files["image"]
    if file.filename == "":
        return {"error": "No selected file"}, 400
    if file:
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
             app.logger.error(f"Upload failed: Invalid extension '{ext}' for file '{filename}'")
             return {"error": f"File type '{ext}' not allowed. Allowed: jpg, png, gif, webp"}, 400
        unique_filename = str(uuid.uuid4()) + ext
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], unique_filename))
        # EasyMDE expects: {"success": 1, "url": "..."}
        return {"success": 1, "url": url_for("static", filename=f"uploads/{unique_filename}")}

@app.route("/admin/users")
@login_required
def manage_users():
    if not current_user.is_admin:
        abort(403)
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/manage_users.html", users=users)

@app.route("/admin/users/template")
@login_required
def download_user_template():
    if not current_user.is_admin:
        abort(403)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "User Import Template"
    
    headers = ['username', 'password', 'permission', 'email', 'real_name', 'student_id', 'department', 'class_name']
    ws.append(headers)
    ws.append(['test_user', '123456', 'user', 'test@example.com', '张三', '20230001', '计算机系', '计科1班'])
    ws.append(['admin_user', '123456', 'admin', 'admin@example.com', '李四', '20230002', '教师组', ''])
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = make_response(output.read())
    response.headers["Content-Disposition"] = "attachment; filename=user_import_template.xlsx"
    response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return response

@app.route("/admin/users/import", methods=["POST"])
@login_required
def import_users():
    if not current_user.is_admin:
        abort(403)
    if "file" not in request.files:
        flash("未选择文件")
        return redirect(url_for("manage_users"))
    file = request.files["file"]
    if file.filename == "":
        flash("未选择文件")
        return redirect(url_for("manage_users"))
        
    filename = file.filename.lower()
    if not (filename.endswith('.csv') or filename.endswith('.xlsx') or filename.endswith('.xls')):
        flash("请上传CSV或Excel文件")
        return redirect(url_for("manage_users"))
        
    try:
        success_count = 0
        error_count = 0
        rows = []
        
        if filename.endswith('.csv'):
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_input = csv.DictReader(stream)
            rows = list(csv_input)
        else:
            # Excel file
            wb = openpyxl.load_workbook(file)
            ws = wb.active
            # Assume first row is header
            headers = [cell.value for cell in ws[1]]
            # Map headers to expected keys (handle potential whitespace or case issues)
            # But for simplicity, assume strict matching first, or lowercase matching
            header_map = {str(h).strip().lower(): i for i, h in enumerate(headers) if h}
            
            for row in ws.iter_rows(min_row=2, values_only=True):
                # Construct a dict similar to csv.DictReader
                row_data = {}
                for key, idx in header_map.items():
                    if idx < len(row):
                        row_data[key] = str(row[idx]) if row[idx] is not None else ''
                if row_data:
                    rows.append(row_data)

        for row in rows:
            # Map keys to standard keys if necessary, but template uses standard keys
            # CSV/Excel headers: username, password, permission, email, real_name, student_id, department, class_name
            
            # Helper to get value case-insensitively if needed, but template enforces keys.
            # Let's try to get values robustly
            def get_val(keys):
                for k in keys:
                    if k in row: return str(row[k]).strip()
                return ''
            
            username = get_val(['username'])
            password = get_val(['password'])
            permission = get_val(['permission']).lower()
            email = get_val(['email']).lower()
            real_name = get_val(['real_name', '姓名'])
            student_id = get_val(['student_id', '学号'])
            department = get_val(['department', '系部'])
            class_name = get_val(['class_name', '班级'])
            
            if not username or not password:
                error_count += 1
                continue
                
            # Check for duplicates (username, email, or student_id)
            query_filter = (User.username == username) | (User.email == email)
            if student_id:
                query_filter = query_filter | (User.student_id == student_id)
                
            if User.query.filter(query_filter).first():
                error_count += 1
                continue
                
            u = User(username=username, email=email)
            u.set_password(password)
            u.is_admin = (permission == 'admin')
            u.real_name = real_name
            u.student_id = student_id if student_id else None
            u.department = department
            u.class_name = class_name
            
            db.session.add(u)
            success_count += 1
        db.session.commit()
        flash(f"导入完成: 成功 {success_count} 个, 失败/重复 {error_count} 个")
    except Exception as e:
        flash(f"导入出错: {str(e)}")
    return redirect(url_for("manage_users"))

@app.route("/admin/users/<int:user_id>/role", methods=["POST"])
@login_required
def update_user_role(user_id):
    if not current_user.is_admin:
        abort(403)
    u = User.query.get_or_404(user_id)
    if u.id == current_user.id:
        flash("不能修改自己的权限")
        return redirect(url_for("manage_users"))
    role = request.form.get("role")
    if role == "admin":
        u.is_admin = True
    else:
        u.is_admin = False
    db.session.commit()
    flash(f"用户 {u.username} 权限已更新")
    return redirect(url_for("manage_users"))

@app.route("/admin/badges", methods=["GET", "POST"])
@login_required
def manage_badges():
    if not current_user.is_admin:
        abort(403)
        
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        # icon = request.form.get("icon", "").strip()
        
        # Handle file upload
        icon = ""
        if "icon_file" in request.files:
            file = request.files["icon_file"]
            if file and file.filename:
                # Validate extension (optional, but good practice)
                if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    flash("不支持的文件格式")
                    return redirect(url_for("manage_badges"))
                
                # Save file
                filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
                save_dir = os.path.join(app.root_path, "static/uploads/badges")
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                
                file.save(os.path.join(save_dir, filename))
                icon = f"/static/uploads/badges/{filename}"
        
        condition_type = request.form.get("condition_type", "").strip()
        try:
            condition_value = int(request.form.get("condition_value", 0))
        except ValueError:
            condition_value = 0
            
        try:
            sticker_count = int(request.form.get("sticker_count", 1))
        except ValueError:
            sticker_count = 1
            
        total_limit_str = request.form.get("total_limit", "").strip()
        total_limit = None
        if total_limit_str:
            try:
                total_limit = int(total_limit_str)
            except ValueError:
                pass
            
        is_hidden = request.form.get("is_hidden") == "on"
        
        # Parse dates
        start_time = None
        end_time = None
        if request.form.get("start_time"):
            try:
                start_time = datetime.strptime(request.form.get("start_time"), "%Y-%m-%d")
            except ValueError:
                pass
        if request.form.get("end_time"):
            try:
                end_time = datetime.strptime(request.form.get("end_time"), "%Y-%m-%d")
            except ValueError:
                pass
            
        if not name or not icon or not condition_type:
            flash("请填写完整信息（包括上传图标）")
            return redirect(url_for("manage_badges"))
            
        b = Badge(
            name=name,
            description=description,
            icon=icon,
            condition_type=condition_type,
            condition_value=condition_value,
            sticker_count=sticker_count,
            total_limit=total_limit,
            is_hidden=is_hidden,
            start_time=start_time,
            end_time=end_time
        )
        db.session.add(b)
        db.session.commit()
        
        # Check 'all_users' immediately
        if b.condition_type == 'all_users':
            users = User.query.all()
            # Check limit before batch add? Or just loop.
            current_count = 0
            limit_reached = False
            
            for user in users:
                if b.total_limit is not None and b.issued_count >= b.total_limit:
                    limit_reached = True
                    break
                    
                if not UserBadge.query.filter_by(user_id=user.id, badge_id=b.id).first():
                    db.session.add(UserBadge(user_id=user.id, badge_id=b.id))
                    b.issued_count += 1
                    current_count += 1
                    
            db.session.commit()
            
        flash("徽章创建成功")
        return redirect(url_for("manage_badges"))
        
    badges = Badge.query.order_by(Badge.created_at.desc()).all()
    users = User.query.all()
    return render_template("admin/manage_badges.html", badges=badges, users=users)

@app.route("/admin/badges/<int:badge_id>/edit", methods=["GET", "POST"])
@login_required
def edit_badge(badge_id):
    if not current_user.is_admin:
        abort(403)
        
    b = Badge.query.get_or_404(badge_id)
    
    if request.method == "POST":
        b.name = request.form.get("name", "").strip()
        b.description = request.form.get("description", "").strip()
        # b.icon = request.form.get("icon", "").strip()
        
        # Handle file upload
        if "icon_file" in request.files:
            file = request.files["icon_file"]
            if file and file.filename:
                # Validate extension
                if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    flash("不支持的文件格式")
                    return render_template("admin/edit_badge.html", badge=b)
                
                # Save new file
                filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
                save_dir = os.path.join(app.root_path, "static/uploads/badges")
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                
                new_path = os.path.join(save_dir, filename)
                file.save(new_path)
                
                # Delete old file if it exists and is a local file
                if b.icon and b.icon.startswith("/static/uploads/badges/"):
                    old_filename = b.icon.split("/")[-1]
                    old_path = os.path.join(save_dir, old_filename)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except OSError:
                            pass # Ignore errors during deletion
                
                b.icon = f"/static/uploads/badges/{filename}"

        b.condition_type = request.form.get("condition_type", "").strip()
        try:
            b.condition_value = int(request.form.get("condition_value", 0))
        except ValueError:
            b.condition_value = 0
            
        try:
            b.sticker_count = int(request.form.get("sticker_count", 1))
        except ValueError:
            b.sticker_count = 1
            
        total_limit_str = request.form.get("total_limit", "").strip()
        if total_limit_str:
            try:
                b.total_limit = int(total_limit_str)
            except ValueError:
                pass
        else:
            b.total_limit = None
            
        b.is_hidden = request.form.get("is_hidden") == "on"
        
        # Parse dates
        if request.form.get("start_time"):
            try:
                b.start_time = datetime.strptime(request.form.get("start_time"), "%Y-%m-%d")
            except ValueError:
                pass
        else:
            b.start_time = None
            
        if request.form.get("end_time"):
            try:
                b.end_time = datetime.strptime(request.form.get("end_time"), "%Y-%m-%d")
            except ValueError:
                pass
        else:
            b.end_time = None
        
        db.session.commit()
        
        # Check 'all_users' immediately
        if b.condition_type == 'all_users':
            users = User.query.all()
            for user in users:
                if b.total_limit is not None and b.issued_count >= b.total_limit:
                    break
                if not UserBadge.query.filter_by(user_id=user.id, badge_id=b.id).first():
                    db.session.add(UserBadge(user_id=user.id, badge_id=b.id))
                    b.issued_count += 1
            db.session.commit()
        
        # Retroactive Check: Check this badge for all users
        # This could be heavy, so ideally run in background task. 
        # For now, we iterate all users.
        
        # Skip retroactive check for manual badges
        if b.condition_type != 'manual':
            users = User.query.all()
            for user in users:
                # Use the centralized check logic
                # But check_and_award_badges only awards, doesn't revoke.
                # So we need custom logic here if we want to support revocation.
                # However, re-implementing logic is error-prone.
                # For now, let's fix the missing types in this loop.
                
                meets_condition = False
                
                if b.condition_type == 'all_users':
                    meets_condition = True
                    
                elif b.condition_type == 'login_days_in_range':
                    if b.start_time and b.end_time:
                        sessions = StudySession.query.filter(
                            StudySession.user_id == user.id,
                            StudySession.start_time >= b.start_time,
                            StudySession.start_time <= b.end_time
                        ).all()
                        login_days = set([s.start_time.date() for s in sessions])
                        meets_condition = len(login_days) >= b.condition_value
                
                elif b.condition_type == 'note_count':
                    count = Note.query.filter_by(user_id=user.id).count()
                    meets_condition = count >= b.condition_value
                elif b.condition_type == 'featured_count':
                    count = Note.query.filter_by(user_id=user.id, is_featured=True).count()
                    meets_condition = count >= b.condition_value
                elif b.condition_type == 'wiki_edit_count':
                    count = WikiPageHistory.query.filter_by(user_id=user.id).count()
                    meets_condition = count >= b.condition_value
                elif b.condition_type == 'comment_count':
                    count = Comment.query.filter_by(user_id=user.id).count()
                    meets_condition = count >= b.condition_value
                elif b.condition_type == 'night_owl_sessions':
                    # Re-calculate: Count DISTINCT "logical nights" (offset by -4 hours)
                    sessions = StudySession.query.filter_by(user_id=user.id).all()
                    night_days = set()
                    for s in sessions:
                        h = s.start_time.hour
                        if h >= 23 or h < 4:
                            logical_date = (s.start_time - timedelta(hours=4)).date()
                            night_days.add(logical_date)
                    meets_condition = len(night_days) >= b.condition_value
                
                elif b.condition_type == 'early_bird':
                    # Count distinct days with sessions between 05:00 and 08:00
                    sessions = StudySession.query.filter_by(user_id=user.id).all()
                    early_days = set()
                    for s in sessions:
                        h = s.start_time.hour
                        if 5 <= h < 8:
                            early_days.add(s.start_time.date())
                    meets_condition = len(early_days) >= b.condition_value
                 
                elif b.condition_type == 'weekend_warrior':
                    sessions = StudySession.query.filter_by(user_id=user.id).all()
                    total_seconds = 0
                    for s in sessions:
                        if s.start_time.weekday() in [5, 6]:
                            duration = (s.end_time - s.start_time).total_seconds()
                            if duration > 0:
                                total_seconds += duration
                    total_hours = total_seconds / 3600
                    meets_condition = total_hours >= b.condition_value
                 
                elif b.condition_type == 'long_session_count':
                    # Count sessions > 2 hours (7200 seconds)
                    sessions = StudySession.query.filter_by(user_id=user.id).all()
                    long_count = 0
                    for s in sessions:
                        duration = (s.end_time - s.start_time).total_seconds()
                        if duration >= 7200:
                            long_count += 1
                    meets_condition = long_count >= b.condition_value
                
                elif b.condition_type == 'share_count':
                    # We need sender. NoteShare definition: note_id, user_id (receiver).
                    # So we join Note to find sender.
                    count = NoteShare.query.join(Note).filter(Note.user_id == user.id).count()
                    meets_condition = count >= b.condition_value
                    
                elif b.condition_type == 'total_views_received':
                    # Count total views on user's notes
                    count = NoteViewLog.query.join(Note).filter(Note.user_id == user.id).count()
                    meets_condition = count >= b.condition_value
                
                elif b.condition_type == 'wiki_create_count':
                    from sqlalchemy import func
                    subquery = db.session.query(func.min(WikiPageHistory.id)).group_by(WikiPageHistory.page_id)
                    count = WikiPageHistory.query.filter(WikiPageHistory.id.in_(subquery), WikiPageHistory.user_id == user.id).count()
                    meets_condition = count >= b.condition_value

                elif b.condition_type == 'study_hours':
                    sessions = StudySession.query.filter_by(user_id=user.id).all()
                    total_seconds = sum([(s.end_time - s.start_time).total_seconds() for s in sessions if (s.end_time - s.start_time).total_seconds() > 0])
                    total_hours = total_seconds / 3600
                    meets_condition = total_hours >= b.condition_value

                elif b.condition_type == 'streak_days':
                    # Re-calculate streak
                    sessions = StudySession.query.filter_by(user_id=user.id).order_by(StudySession.start_time.desc()).all()
                    dates = sorted(list(set([s.start_time.date() for s in sessions])), reverse=True)
                    streak = 0
                    if dates:
                        today = now_utc8().date()
                        if dates[0] == today:
                            streak = 1
                            current = today
                        elif dates[0] == today - timedelta(days=1):
                            streak = 1
                            current = today - timedelta(days=1)
                        else:
                            streak = 0
                        if streak > 0:
                            for i in range(1, len(dates)):
                                if dates[i] == current - timedelta(days=1):
                                    streak += 1
                                    current = dates[i]
                                else:
                                    break
                    meets_condition = streak >= b.condition_value

            # 2. Update UserBadge status
                existing_ub = UserBadge.query.filter_by(user_id=user.id, badge_id=b.id).first()
                
                if meets_condition:
                    if not existing_ub:
                        # Check limit
                        if b.total_limit is not None and b.issued_count >= b.total_limit:
                            continue # Skip this user, limit reached
                            
                        # Award new badge
                        ub = UserBadge(user_id=user.id, badge_id=b.id)
                        db.session.add(ub)
                        b.issued_count += 1
                else:
                    if existing_ub:
                        # Revoke badge if no longer meets criteria
                        # Also unequip if equipped
                        if user.selected_badge_id == b.id:
                            user.selected_badge_id = None
                        db.session.delete(existing_ub)
                        # Should we decrement issued_count?
                        # Usually yes, if it's a dynamic count.
                        if b.issued_count > 0:
                            b.issued_count -= 1
            
            db.session.commit()
            
            flash("徽章已更新，并已重新检查所有用户的获得条件（包括撤销不满足条件的徽章）")
        else:
            flash("徽章已更新 (手动发放类型不进行自动检查)")
            
        return redirect(url_for("manage_badges"))
        
    return render_template("admin/edit_badge.html", badge=b)

@app.route("/admin/badges/<int:badge_id>/award", methods=["POST"])
@login_required
def award_badge_manually(badge_id):
    if not current_user.is_admin:
        abort(403)
        
    b = Badge.query.get_or_404(badge_id)
    if b.condition_type != 'manual':
        return jsonify({"error": "Only manual badges can be manually awarded"}), 400
        
    user_ids = request.json.get("user_ids", [])
    if not user_ids:
        return jsonify({"error": "No users selected"}), 400
        
    count = 0
    for uid in user_ids:
        user = User.query.get(uid)
        if user:
            # Check limit
            if b.total_limit is not None and b.issued_count >= b.total_limit:
                break

            # Check if already has badge
            if not UserBadge.query.filter_by(user_id=user.id, badge_id=b.id).first():
                ub = UserBadge(user_id=user.id, badge_id=b.id)
                db.session.add(ub)
                b.issued_count += 1
                count += 1
                
    db.session.commit()
    if b.total_limit is not None and b.issued_count >= b.total_limit:
        return jsonify({"success": True, "count": count, "message": "Badge limit reached"})
    return jsonify({"success": True, "count": count})

@app.route("/admin/badges/<int:badge_id>/delete", methods=["POST"])
@login_required
def delete_badge(badge_id):
    if not current_user.is_admin:
        abort(403)
    b = Badge.query.get_or_404(badge_id)
    
    # Cascade delete: Delete all UserBadges associated with this badge
    UserBadge.query.filter_by(badge_id=b.id).delete()
    
    # Also clear selected_badge_id from users who equipped it
    User.query.filter_by(selected_badge_id=b.id).update({"selected_badge_id": None})
    
    # Delete icon file if it's a local upload
    if b.icon and b.icon.startswith("/static/uploads/badges/"):
        filename = b.icon.split("/")[-1]
        file_path = os.path.join(app.root_path, "static/uploads/badges", filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

    db.session.delete(b)
    db.session.commit()
    flash("徽章已删除")
    return redirect(url_for("manage_badges"))

@app.route("/user/profile")
@login_required
def user_profile():
    return redirect(url_for('public_profile', user_id=current_user.id))

@app.route("/user/<int:user_id>")
@login_required
def public_profile(user_id):
    user = User.query.get_or_404(user_id)
    
    # Stats
    stats = user.calculate_stats()
    
    # Badges
    user_badges = UserBadge.query.filter_by(user_id=user.id).order_by(UserBadge.earned_at.desc()).all()
    earned_badge_ids = [ub.badge_id for ub in user_badges]
    all_badges = Badge.query.all()
    unearned_badges = [b for b in all_badges if b.id not in earned_badge_ids]
    
    # Recent Activity (Notes)
    recent_notes = Note.query.filter_by(user_id=user.id).order_by(Note.created_at.desc()).limit(5).all()

    # Check follow status
    is_following = current_user.is_following(user)
    is_study_partner = current_user.is_following(user) and user.is_following(current_user)

    return render_template("user/profile.html", user=user, stats=stats, user_badges=user_badges, unearned_badges=unearned_badges, recent_notes=recent_notes, is_following=is_following, is_study_partner=is_study_partner)

@app.route("/user/<int:user_id>/follow", methods=["POST"])
@login_required
def follow_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({"error": "不能关注自己"}), 400
        
    if not current_user.is_following(user):
        current_user.follow(user)
        db.session.commit()
        
        # Check for study partner (mutual follow)
        if user.is_following(current_user):
            # Notify both
            n1 = Notification(
                user_id=current_user.id,
                message=f"你和 {user.username} 成为了学友！",
                type='system',
                link=url_for('public_profile', user_id=user.id)
            )
            n2 = Notification(
                user_id=user.id,
                message=f"你和 {current_user.username} 成为了学友！",
                type='system',
                link=url_for('public_profile', user_id=current_user.id)
            )
            db.session.add_all([n1, n2])
            db.session.commit()
            flash(f"关注成功！你和 {user.username} 现在是学友了！")
        else:
            flash(f"已关注 {user.username}")
            
    return redirect(request.referrer or url_for('public_profile', user_id=user.id))

@app.route("/user/<int:user_id>/unfollow", methods=["POST"])
@login_required
def unfollow_user(user_id):
    user = User.query.get_or_404(user_id)
    if current_user.is_following(user):
        current_user.unfollow(user)
        db.session.commit()
        flash(f"已取消关注 {user.username}")
        
    return redirect(request.referrer or url_for('public_profile', user_id=user.id))

@app.route("/user/following")
@login_required
def my_following():
    # List of users I follow
    # We can also separate "Study Partners" vs "Just Following"
    
    # Study Partners (Mutual)
    partners = current_user.study_partners.all()
    partner_ids = [u.id for u in partners]
    
    # Following (excluding partners)
    following_all = current_user.followed.all()
    following_only = [u for u in following_all if u.id not in partner_ids]
    
    # Followers (who I don't follow back) - Optional, user didn't explicitly ask to see list, but good to have
    # Requirement: "自己的关注列表是可以点击查看的" -> My Following List
    
    return render_template("user/following.html", partners=partners, following=following_only)

@app.route("/api/notifications/read/all", methods=["POST"])
@login_required
def read_all_notifications():
    current_user.notifications.filter_by(is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"success": True})

@app.route("/user/badges")
@login_required
def my_badges():
    # Earned badges
    user_badges = UserBadge.query.filter_by(user_id=current_user.id).order_by(UserBadge.earned_at.desc()).all()
    earned_badge_ids = [ub.badge_id for ub in user_badges]
    
    # Unearned badges
    all_badges = Badge.query.all()
    unearned_badges = [b for b in all_badges if b.id not in earned_badge_ids]
    
    return render_template("user/my_badges.html", user_badges=user_badges, unearned_badges=unearned_badges)

@app.route("/user/badges/equip", methods=["POST"])
@login_required
def equip_badge():
    badge_id = request.json.get("badge_id")
    
    if badge_id is None:
        # Unequip
        current_user.selected_badge_id = None
        db.session.commit()
        return jsonify({"success": True, "message": "已卸下徽章"})
        
    # Check if user owns this badge
    ub = UserBadge.query.filter_by(user_id=current_user.id, badge_id=badge_id).first()
    if not ub:
        return jsonify({"success": False, "error": "您尚未获得该徽章"}), 403
        
    current_user.selected_badge_id = badge_id
    db.session.commit()
    return jsonify({"success": True, "message": "徽章佩戴成功"})

# Book Module Routes
@app.route("/book")
@login_required
def book_index():
    q = request.args.get("q", "").strip()
    
    # 精选笔记
    featured_notes = Note.query.filter_by(is_featured=True).order_by(Note.updated_at.desc()).all()
    
    if q:
        # 1. Title Matches
        my_title = Note.query.filter(
            Note.user_id == current_user.id,
            Note.title.contains(q)
        ).all()
        for n in my_title: n.source_type = 'my'
        
        shared_title = Note.query.join(NoteShare).filter(
            NoteShare.user_id == current_user.id,
            Note.title.contains(q)
        ).all()
        for n in shared_title: n.source_type = 'shared'
        
        title_matches = sorted(my_title + shared_title, key=lambda x: x.updated_at, reverse=True)
        
        # 2. Content Matches (exclude title matches)
        my_content = Note.query.filter(
            Note.user_id == current_user.id,
            Note.content_md.contains(q),
            ~Note.title.contains(q)
        ).all()
        for n in my_content: n.source_type = 'my'
        
        shared_content = Note.query.join(NoteShare).filter(
            NoteShare.user_id == current_user.id,
            Note.content_md.contains(q),
            ~Note.title.contains(q)
        ).all()
        for n in shared_content: n.source_type = 'shared'
        
        content_matches = sorted(my_content + shared_content, key=lambda x: x.updated_at, reverse=True)
        
        return render_template("book/index.html", 
                             featured_notes=featured_notes, 
                             q=q, 
                             title_matches=title_matches, 
                             content_matches=content_matches)
    else:
        my_notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.updated_at.desc()).all()
        shared_notes = Note.query.join(NoteShare).filter(NoteShare.user_id == current_user.id).order_by(NoteShare.created_at.desc()).all()
    
        return render_template("book/index.html", my_notes=my_notes, shared_notes=shared_notes, featured_notes=featured_notes, q=q)



@app.route("/book/received")
@login_required
def book_received():
    q = request.args.get("q", "").strip()
    
    if q:
        note_shares = NoteShare.query.join(Note).filter(
            NoteShare.user_id == current_user.id,
            (Note.title.contains(q)) | (Note.content_md.contains(q))
        ).order_by(NoteShare.created_at.desc()).all()
    else:
        note_shares = NoteShare.query.filter_by(user_id=current_user.id).order_by(NoteShare.created_at.desc()).all()
        
    return render_template("book/received.html", note_shares=note_shares, q=q)

@app.route("/online_users")
@login_required
def online_users():
    online_threshold = now_utc8() - timedelta(minutes=5)
    users = UserActiveStatus.query.filter(UserActiveStatus.last_active_at > online_threshold).all()
    return render_template("online_users.html", users=users)

@app.route("/book/notes")
@login_required
def my_notes():
    q = request.args.get("q", "").strip()
    
    # Base query for my notes
    query = Note.query.filter_by(user_id=current_user.id)
    
    if q:
        query = query.filter((Note.title.contains(q)) | (Note.content_md.contains(q)))
    
    notes = query.order_by(Note.updated_at.desc()).all()
    
    # Statistics
    stats = {
        "total_notes": Note.query.filter_by(user_id=current_user.id).count(),
        # 我累计阅读的笔记次数（不仅是我的笔记，也包括别人的）
        "total_reads": NoteViewLog.query.filter_by(user_id=current_user.id).count(),
        # 我的笔记被阅读的总次数（影响力）
        "total_views_received": NoteViewLog.query.join(Note).filter(Note.user_id == current_user.id).count(),
        # 我收到的分享数
        "shared_received": NoteShare.query.filter_by(user_id=current_user.id).count(),
        # Study stats
        "today": 0,
        "week": 0,
        "month": 0,
        "three_months": 0,
        "six_months": 0,
        "year": 0,
        "total": 0
    }
    
    # Calculate study stats
    now = now_utc8()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)
    three_months_start = now - timedelta(days=90)
    six_months_start = now - timedelta(days=180)
    year_start = now - timedelta(days=365)
    
    sessions = StudySession.query.filter_by(user_id=current_user.id).all()
    for s in sessions:
        duration = (s.end_time - s.start_time).total_seconds()
        if duration < 0: continue
        
        stats["total"] += duration
        
        if s.start_time >= today_start:
            stats["today"] += duration
        if s.start_time >= week_start:
            stats["week"] += duration
        if s.start_time >= month_start:
            stats["month"] += duration
        if s.start_time >= three_months_start:
            stats["three_months"] += duration
        if s.start_time >= six_months_start:
            stats["six_months"] += duration
        if s.start_time >= year_start:
            stats["year"] += duration
            
    # Convert seconds to hours/minutes string
    def format_duration(seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{int(h)}小时 {int(m)}分钟"
        elif m > 0:
            return f"{int(m)}分钟"
        else:
            return "少于1分钟"
            
    # Update stats with formatted duration, keeping original integer stats
    stats_formatted = stats.copy()
    for k in ["today", "week", "month", "three_months", "six_months", "year", "total"]:
        stats_formatted[k + "_formatted"] = format_duration(stats[k])
    
    return render_template("book/my_notes.html", notes=notes, stats=stats_formatted, q=q)

@app.route("/api/stats/heatmap")
@login_required
def get_heatmap_data():
    # Weights for different activities
    WEIGHTS = {
        'create': 5,  # Creating Note or Wiki History (Edit)
        'comment': 3,
        'session': 2,
        'view': 1
    }
    
    activity_counts = {}

    def process_query(model, date_col, weight=1):
        # Retrieve all history, not just one year
        results = db.session.query(date_col).filter(
            model.user_id == current_user.id
        ).all()
        for (dt,) in results:
            if dt:
                # Adjust to UTC+8 for correct date bucket
                # Assuming stored dates are naive and represent UTC or already UTC+8?
                # The app uses now_utc8() for defaults. 
                # If the column is DateTime, SQLAlchemy returns Python datetime objects.
                # If they were stored as UTC+8 (which they are per now_utc8), then the date part is correct.
                d = dt.strftime("%Y-%m-%d")
                activity_counts[d] = activity_counts.get(d, 0) + weight

    # 1. Notes created (High weight)
    process_query(Note, Note.created_at, WEIGHTS['create'])
    
    # 2. Comments (Medium weight)
    process_query(Comment, Comment.created_at, WEIGHTS['comment'])
    
    # 3. Wiki Edits (High weight)
    process_query(WikiPageHistory, WikiPageHistory.created_at, WEIGHTS['create'])
    
    # 4. Study Sessions (Medium weight)
    process_query(StudySession, StudySession.start_time, WEIGHTS['session'])

    # 5. Reading (Low weight)
    process_query(WikiViewLog, WikiViewLog.timestamp, WEIGHTS['view'])
    process_query(NoteViewLog, NoteViewLog.timestamp, WEIGHTS['view'])
    
    data = [[date, count] for date, count in activity_counts.items()]
    return jsonify({"data": data})

@app.route("/book/calendar")
@login_required
def book_calendar():
    return render_template("book/calendar.html")

@app.route("/api/notes/calendar")
@login_required
def get_calendar_notes():
    notes = Note.query.filter_by(user_id=current_user.id).all()
    events = []
    for note in notes:
        # Create a snippet from markdown content (strip basic md chars)
        content_preview = note.content_md[:200] if note.content_md else ""
        
        events.append({
            "id": note.id,
            "title": note.title,
            "start": note.created_at.strftime("%Y-%m-%d"),
            "extendedProps": {
                "content": content_preview,
                "tags": [t.name for t in note.tags],
                "created_at": note.created_at.strftime("%Y-%m-%d %H:%M")
            }
        })
    return jsonify(events)

@app.route("/book/notes/new", methods=["GET", "POST"])
@login_required
def new_note():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content_md = request.form.get("content_md", "")
        tags_str = request.form.get("tags", "")
        
        if not title:
            flash("标题不能为空")
            return redirect(url_for("new_note"))
            
        n = Note(title=title, content_md=content_md, user_id=current_user.id)
        
        # Process tags
        n.tags = process_tags(tags_str)
        
        db.session.add(n)
        db.session.commit()
        
        # Check badges
        check_and_award_badges(current_user)
        
        return redirect(url_for("view_note", note_id=n.id))
    return render_template("book/new_note.html")

@app.route("/book/notes/<int:note_id>")
@login_required
def view_note(note_id):
    n = Note.query.get_or_404(note_id)
    
    # Check permission (owner or shared or featured)
    is_owner = n.user_id == current_user.id
    is_shared = NoteShare.query.filter_by(note_id=note_id, user_id=current_user.id).first() is not None
    is_featured = n.is_featured
    
    if not (is_owner or is_shared or current_user.is_admin or is_featured):
        abort(403)
        
    # Record view log with debounce (e.g., 5 minutes)
    try:
        last_view = NoteViewLog.query.filter_by(note_id=note_id, user_id=current_user.id).order_by(NoteViewLog.timestamp.desc()).first()
        if not last_view or (now_utc8() - last_view.timestamp).total_seconds() > 300:
            log = NoteViewLog(note_id=note_id, user_id=current_user.id)
            db.session.add(log)
            db.session.commit()
            
            # Check badges for NOTE OWNER (Influencer badge)
            if not is_owner:
                owner = User.query.get(n.user_id)
                if owner:
                    check_and_award_badges(owner)
                    
    except Exception as e:
        # Ignore logging errors to not affect user experience
        print(f"Error logging view: {e}")
        
    html = markdown(n.content_md or "")
    all_users = User.query.filter(User.id != current_user.id).all() if is_owner or current_user.is_admin else []
    
    return render_template("book/view_note.html", note=n, html=html, is_owner=is_owner, all_users=all_users)

@app.route("/book/notes/<int:note_id>/edit", methods=["GET", "POST"])
@login_required
def edit_note(note_id):
    n = Note.query.get_or_404(note_id)
    if n.user_id != current_user.id and not current_user.is_admin:
        abort(403)
        
    if request.method == "POST":
        n.title = request.form.get("title", "").strip()
        n.content_md = request.form.get("content_md", "")
        tags_str = request.form.get("tags", "")
        
        # Update tags
        n.tags = process_tags(tags_str)
        
        # Update settings
        n.comment_enabled = request.form.get("comment_enabled") == "on"
        
        # 仅管理员可以设置精选
        if current_user.is_admin:
            n.is_featured = request.form.get("is_featured") == "on"
            
        db.session.commit()
        
        # Check badges for note owner (if admin featured it)
        owner = User.query.get(n.user_id)
        if owner:
            check_and_award_badges(owner)
            
        return redirect(url_for("view_note", note_id=n.id))
    return render_template("book/edit_note.html", note=n)

@app.route("/book/notes/<int:note_id>/comment", methods=["POST"])
@login_required
def comment_note(note_id):
    n = Note.query.get_or_404(note_id)
    # Check permission (same as view)
    is_owner = n.user_id == current_user.id
    is_shared = NoteShare.query.filter_by(note_id=note_id, user_id=current_user.id).first() is not None
    is_featured = n.is_featured
    
    if not (is_owner or is_shared or current_user.is_admin or is_featured):
        abort(403)
        
    content = request.form.get("content", "").strip()
    if content:
        c = Comment(content=content, user_id=current_user.id, note_id=n.id)
        db.session.add(c)
        db.session.commit()
        
        # Check badges
        check_and_award_badges(current_user)
        
        flash("评论已发表")
    else:
        flash("评论内容不能为空")
        
    return redirect(url_for("view_note", note_id=n.id))

@app.route("/book/notes/<int:note_id>/delete", methods=["POST"])
@login_required
def delete_note(note_id):
    n = Note.query.get_or_404(note_id)
    if n.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    db.session.delete(n)
    db.session.commit()
    flash("笔记已删除")
    return redirect(url_for("book_index"))

@app.route("/book/notes/<int:note_id>/share", methods=["POST"])
@login_required
def share_note(note_id):
    n = Note.query.get_or_404(note_id)
    if n.user_id != current_user.id and not current_user.is_admin:
        abort(403)
        
    user_ids = request.form.getlist("user_ids")
    
    # Simple logic: Add new shares, ignore existing ones
    count = 0
    for uid in user_ids:
        try:
            uid = int(uid)
            if uid == n.user_id: continue
            
            exists = NoteShare.query.filter_by(note_id=n.id, user_id=uid).first()
            if not exists:
                share = NoteShare(note_id=n.id, user_id=uid)
                db.session.add(share)
                count += 1
        except ValueError:
            continue
            
    db.session.commit()
    
    # Check badges for current user (Share count)
    check_and_award_badges(current_user)
    
    flash(f"已分享给 {count} 位用户")
    return redirect(url_for("view_note", note_id=n.id))

@app.route("/book/notes/quick_create", methods=["POST"])
@login_required
def quick_create_note():
    data = request.json
    content = data.get("content", "").strip()
    custom_title = data.get("title", "").strip()
    
    if not content and not custom_title:
        return jsonify({"success": False, "error": "内容或标题不能为空"}), 400
        
    try:
        # Title: YYYY-MM-DD HH:mm:ss if not provided
        title = custom_title if custom_title else now_utc8().strftime("%Y-%m-%d %H:%M:%S")
        n = Note(title=title, content_md=content, user_id=current_user.id)
        db.session.add(n)
        db.session.commit()
        
        # Check badges
        check_and_award_badges(current_user)
        
        return jsonify({"success": True, "note_id": n.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/book/share/<int:share_id>/delete", methods=["POST"])
@login_required
def delete_share(share_id):
    share = NoteShare.query.get_or_404(share_id)
    
    # 只能删除自己的分享记录
    if share.user_id != current_user.id:
        return jsonify({"success": False, "error": "无权删除"}), 403
    
    try:
        db.session.delete(share)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/book/share/<int:share_id>/convert", methods=["POST"])
@login_required
def convert_note(share_id):
    share = NoteShare.query.get_or_404(share_id)
    
    # 只能转换自己的分享记录
    if share.user_id != current_user.id:
        return jsonify({"success": False, "error": "无权转换"}), 403
    
    try:
        original_note = share.note
        
        # 创建新的笔记，标题包含发送人姓名
        new_title = f"来自{original_note.user.username}的笔记：{original_note.title}"
        new_note = Note(
            title=new_title,
            content_md=original_note.content_md,
            user_id=current_user.id,
            is_featured=False
        )
        
        db.session.add(new_note)
        
        # 删除分享记录
        db.session.delete(share)
        
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/wiki/<int:wiki_id>/page/<string:slug>/convert", methods=["POST"])
@login_required
def convert_wiki_page(wiki_id, slug):
    wiki = Wiki.query.get_or_404(wiki_id)
    if not can_view_wiki(wiki_id):
        return jsonify({"success": False, "error": "无权访问"}), 403
        
    page = WikiPage.query.filter_by(wiki_id=wiki_id, slug=slug).first_or_404()
    
    try:
        new_title = f"[Wiki] {page.title}"
        new_note = Note(
            title=new_title,
            content_md=page.content_md,
            user_id=current_user.id,
            is_featured=False
        )
        
        db.session.add(new_note)
        db.session.commit()
        return jsonify({"success": True, "note_id": new_note.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/link-preview")
def link_preview():
    url = request.args.get("url")
    if not url:
        return {"error": "Missing URL"}, 400
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; LinkPreviewBot/1.0)"}
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.content, "html.parser")
        
        title = soup.title.string if soup.title else ""
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"): title = og_title.get("content")
            
        description = ""
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            description = og_desc.get("content", "")
        else:
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc: description = meta_desc.get("content", "")
            
        image = ""
        og_image = soup.find("meta", property="og:image")
        if og_image:
            image = og_image.get("content", "")
            if image and not image.startswith("http"):
                from urllib.parse import urljoin
                image = urljoin(url, image)
        
        if not image:
             link_icon = soup.find("link", rel="icon") or soup.find("link", rel="shortcut icon")
             if link_icon:
                 image = link_icon.get("href", "")
                 from urllib.parse import urljoin
                 image = urljoin(url, image)

        return {
            "title": title.strip() if title else url,
            "description": description.strip()[:200] + "..." if len(description) > 200 else description.strip(),
            "image": image,
            "url": url
        }
    except Exception as e:
        # Return basic info on error
        return {
            "title": url,
            "description": "No preview available",
            "image": "",
            "url": url
        }

@app.route("/api/heartbeat", methods=["POST"])
@login_required
def heartbeat():
    path = request.json.get("path", "/")
    # Infer action
    action = "浏览页面"
    if "/edit" in path:
        action = "编辑内容"
    elif "/new" in path:
        action = "新建内容"
    elif "/notes/" in path:
        action = "查看笔记"
    elif "/pages/" in path:
        action = "查看 Wiki"
    elif "/book" in path:
        action = "浏览笔记库"
    elif "/wikis/" in path:
        action = "浏览 Wiki"
        
    now = now_utc8()
    
    # 1. Update UserActiveStatus
    status = UserActiveStatus.query.get(current_user.id)
    if not status:
        status = UserActiveStatus(user_id=current_user.id)
        db.session.add(status)
    
    # Check if user was offline (active > 5 mins ago)
    was_offline = False
    online_threshold = now - timedelta(minutes=5)
    if status.last_active_at and status.last_active_at < online_threshold:
        was_offline = True
    elif status.last_active_at is None:
        was_offline = True
    
    status.last_active_at = now
    status.current_path = path
    status.current_action = action
    
    # Notify study partners if came online
    if was_offline:
        partners = current_user.study_partners.all()
        for p in partners:
            # Avoid duplicate notifications if multiple heartbeats fire quickly?
            # Or just rely on 5 min threshold.
            n = Notification(
                user_id=p.id,
                message=f"你的学友 {current_user.username} 上线了",
                type='friend_login',
                link=url_for('public_profile', user_id=current_user.id)
            )
            db.session.add(n)
    
    # 2. Update StudySession
    # Find latest session
    session = StudySession.query.filter_by(user_id=current_user.id).order_by(StudySession.end_time.desc()).first()
    
    # If session exists and gap is small (e.g. < 5 mins), extend it
    # Else create new session
    gap_limit = timedelta(minutes=5)
    
    if session and (now - session.end_time) < gap_limit:
        session.end_time = now
    else:
        # Create new session
        session = StudySession(user_id=current_user.id, start_time=now, end_time=now)
        db.session.add(session)
        
    db.session.commit()
    
    # Check badges
    check_and_award_badges(current_user)
    
    # Get unread notifications
    notifications = []
    unread_notifs = current_user.notifications.filter_by(is_read=False).order_by(Notification.created_at.desc()).all()
    for n in unread_notifs:
        notifications.append({
            "id": n.id,
            "message": n.message,
            "type": n.type,
            "link": n.link,
            "created_at": n.created_at.strftime("%H:%M")
        })

    return {"status": "ok", "notifications": notifications}

@app.route("/api/notes/new_view", methods=["POST"])
@login_required
def log_note_view():
    # Hook for 'total_views_received' badge of the NOTE OWNER
    # Triggered when someone views a note. 
    # But currently view log is in view_note route (GET).
    # We can check badges there.
    pass

@app.context_processor
def inject_helpers():
    # Count online users (active in last 5 mins)
    online_threshold = now_utc8() - timedelta(minutes=5)
    online_count = UserActiveStatus.query.filter(UserActiveStatus.last_active_at > online_threshold).count()
    
    def get_badge_usage(user_id, badge_id):
        return UserSticker.query.filter_by(user_id=user_id, badge_id=badge_id).count()
    
    return dict(
        can_view_wiki=can_view_wiki, 
        can_edit_wiki=can_edit_wiki,
        online_user_count=online_count,
        get_badge_usage=get_badge_usage
    )

# Badge Logic Service
def check_and_award_badges(user):
    # Get all badges not yet earned by user
    earned_badge_ids = [ub.badge_id for ub in user.earned_badges]
    available_badges = Badge.query.filter(Badge.id.notin_(earned_badge_ids)).all()
    
    awarded_count = 0
    
    for badge in available_badges:
        # Skip manual badges
        if badge.condition_type == 'manual':
            continue
            
        # Check limit
        if badge.total_limit is not None and badge.issued_count >= badge.total_limit:
            continue

        earned = False
        
        if badge.condition_type == 'all_users':
            earned = True
            
        elif badge.condition_type == 'note_count':
            count = Note.query.filter_by(user_id=user.id).count()
            if count >= badge.condition_value:
                earned = True
                
        elif badge.condition_type == 'featured_count':
            count = Note.query.filter_by(user_id=user.id, is_featured=True).count()
            if count >= badge.condition_value:
                earned = True

        elif badge.condition_type == 'wiki_edit_count':
            # Count distinct WikiPageHistory entries by user
            count = WikiPageHistory.query.filter_by(user_id=user.id).count()
            if count >= badge.condition_value:
                earned = True
                
        elif badge.condition_type == 'comment_count':
            count = Comment.query.filter_by(user_id=user.id).count()
            if count >= badge.condition_value:
                earned = True
                
        elif badge.condition_type == 'night_owl_sessions':
            # Count DISTINCT "logical nights" (offset by -4 hours)
            # So 23:00 (D) to 03:59 (D+1) count as same day (D)
            sessions = StudySession.query.filter_by(user_id=user.id).all()
            night_days = set()
            for s in sessions:
                h = s.start_time.hour
                if h >= 23 or h < 4:
                    # Offset by -4 hours to group late night sessions to previous day
                    logical_date = (s.start_time - timedelta(hours=4)).date()
                    night_days.add(logical_date)
            if len(night_days) >= badge.condition_value:
                earned = True

        elif badge.condition_type == 'early_bird':
            # Count distinct days with sessions between 05:00 and 08:00
            sessions = StudySession.query.filter_by(user_id=user.id).all()
            early_days = set()
            for s in sessions:
                h = s.start_time.hour
                if 5 <= h < 8:
                    early_days.add(s.start_time.date())
            if len(early_days) >= badge.condition_value:
                earned = True

        elif badge.condition_type == 'weekend_warrior':
            # Calculate total study duration on Sat (5) and Sun (6)
            sessions = StudySession.query.filter_by(user_id=user.id).all()
            total_seconds = 0
            for s in sessions:
                # Check if start_time is on weekend
                if s.start_time.weekday() in [5, 6]:
                    duration = (s.end_time - s.start_time).total_seconds()
                    if duration > 0:
                        total_seconds += duration
            total_hours = total_seconds / 3600
            if total_hours >= badge.condition_value:
                earned = True
                
        elif badge.condition_type == 'long_session_count':
            sessions = StudySession.query.filter_by(user_id=user.id).all()
            long_count = 0
            for s in sessions:
                duration = (s.end_time - s.start_time).total_seconds()
                if duration >= 7200:
                    long_count += 1
            if long_count >= badge.condition_value:
                earned = True
                
        elif badge.condition_type == 'share_count':
            count = NoteShare.query.join(Note).filter(Note.user_id == user.id).count()
            if count >= badge.condition_value:
                earned = True
                
        elif badge.condition_type == 'total_views_received':
            count = NoteViewLog.query.join(Note).filter(Note.user_id == user.id).count()
            if count >= badge.condition_value:
                earned = True
                
        elif badge.condition_type == 'wiki_create_count':
            from sqlalchemy import func
            subquery = db.session.query(func.min(WikiPageHistory.id)).group_by(WikiPageHistory.page_id)
            count = WikiPageHistory.query.filter(WikiPageHistory.id.in_(subquery), WikiPageHistory.user_id == user.id).count()
            if count >= badge.condition_value:
                earned = True
                
        elif badge.condition_type == 'study_hours':
            # Calculate total study duration in hours
            sessions = StudySession.query.filter_by(user_id=user.id).all()
            total_seconds = sum([(s.end_time - s.start_time).total_seconds() for s in sessions if (s.end_time - s.start_time).total_seconds() > 0])
            total_hours = total_seconds / 3600
            if total_hours >= badge.condition_value:
                earned = True
                
        elif badge.condition_type == 'streak_days':
            # Calculate streak
            # Get distinct dates of study sessions, sorted desc
            # This is a bit heavy, optimize if needed
            # Use SQL distinct date
            sessions = StudySession.query.filter_by(user_id=user.id).order_by(StudySession.start_time.desc()).all()
            dates = sorted(list(set([s.start_time.date() for s in sessions])), reverse=True)
            
            streak = 0
            if dates:
                # Check if today or yesterday is present to keep streak alive
                today = now_utc8().date()
                if dates[0] == today:
                    streak = 1
                    current = today
                elif dates[0] == today - timedelta(days=1):
                    streak = 1
                    current = today - timedelta(days=1)
                else:
                    streak = 0 # Streak broken
                
                if streak > 0:
                    # Check consecutive days
                    for i in range(1, len(dates)):
                        if dates[i] == current - timedelta(days=1):
                            streak += 1
                            current = dates[i]
                        else:
                            break
            
            if streak >= badge.condition_value:
                earned = True

        elif badge.condition_type == 'login_days_in_range':
            # Count distinct days user logged in (had a session) within range
            if badge.start_time and badge.end_time:
                # Filter sessions within range
                sessions = StudySession.query.filter(
                    StudySession.user_id == user.id,
                    StudySession.start_time >= badge.start_time,
                    StudySession.start_time <= badge.end_time
                ).all()
                
                # Count distinct dates
                login_days = set([s.start_time.date() for s in sessions])
                if len(login_days) >= badge.condition_value:
                    earned = True
        
        if earned:
            ub = UserBadge(user_id=user.id, badge_id=badge.id)
            db.session.add(ub)
            badge.issued_count += 1
            awarded_count += 1
            flash(f"恭喜！您获得了新徽章：{badge.icon} {badge.name}")
            
            # Notify study partners
            partners = user.study_partners.all()
            for p in partners:
                n = Notification(
                    user_id=p.id,
                    message=f"你的学友 {user.username} 获得了 {badge.name} 徽章！",
                    type='friend_achievement',
                    link=url_for('public_profile', user_id=user.id)
                )
                db.session.add(n)
            
    if awarded_count > 0:
        db.session.commit()

# Sticker API
@app.route("/api/stickers/<page_type>", methods=["GET", "POST"])
@login_required
def api_stickers(page_type):
    if page_type not in ['wiki', 'book', 'profile']:
        return jsonify({"error": "Invalid page type"}), 400
        
    if request.method == "GET":
        target_user_id = current_user.id
        user_id_param = request.args.get('user_id')
        if user_id_param:
            try:
                target_user_id = int(user_id_param)
            except ValueError:
                pass
        
        # Permission Check for Live Board
        if target_user_id != current_user.id:
            target_user = User.query.get(target_user_id)
            if not target_user:
                return jsonify({"error": "User not found"}), 404
            
            # Check if follower (assuming Live Board is visible to followers)
            # Using is_following method: current_user.is_following(target_user)
            # BUT for Study Partner logic, we might want mutual follow?
            # User requirement: "should compute if they are study partners (mutual follow)"
            # If the index route only allows mutual follow, the API should probably enforce the same or similar.
            # Currently the index route enforces mutual follow.
            # The API currently enforces "I follow Target".
            # If I follow Target but Target doesn't follow me back (not study partner),
            # Index route sets target_user=None, so banner doesn't show.
            # BUT sticker.js might still try to load stickers?
            # StickerManager only inits if target_user is present in DOM.
            # So if Index route is strict, API being loose is okay-ish (just security in depth).
            # But let's align API to be strict too if that's what user implies.
            # "且要计算是否是对方的学友" -> This was for the index route logic.
            # Let's keep API as is (one-way follow is usually enough for "viewing", mutual is for "interaction")
            # OR, update API to match index route policy: Mutual Follow required?
            # Let's update API to require Mutual Follow to be safe and consistent.
            
            is_mutual = current_user.is_following(target_user) and target_user.is_following(current_user)
            if not is_mutual:
                 # Strict privacy for Live Board: Only self and study partners can see
                 return jsonify({"error": "Permission denied: Not study partners"}), 403

        stickers = UserSticker.query.filter_by(user_id=target_user_id, page_type=page_type).all()
        return jsonify({
            "stickers": [{
                "id": s.id,
                "badge_id": s.badge_id,
                "badge_icon": badge_icon_url(s.badge.icon) if s.badge else "",
                "x": s.x,
                "y": s.y,
                "rotation": s.rotation,
                "scale": s.scale,
                "z_index": s.z_index
            } for s in stickers]
        })
        
    elif request.method == "POST":
        data = request.json
        stickers_data = data.get("stickers", [])
        
        # Full replacement strategy for simplicity
        UserSticker.query.filter_by(user_id=current_user.id, page_type=page_type).delete()
        
        # Validate counts
        badge_counts = {}
        
        for s in stickers_data:
            badge_id = s.get("badge_id")
            # Verify user owns this badge
            ub = UserBadge.query.filter_by(user_id=current_user.id, badge_id=badge_id).first()
            if ub:
                # Check limit
                badge = ub.badge
                current_count = badge_counts.get(badge_id, 0)
                if current_count >= badge.sticker_count:
                    continue # Skip if limit reached
                    
                badge_counts[badge_id] = current_count + 1
                
                new_sticker = UserSticker(
                    user_id=current_user.id,
                    badge_id=badge_id,
                    page_type=page_type,
                    x=s.get("x", 50),
                    y=s.get("y", 50),
                    rotation=s.get("rotation", 0),
                    scale=s.get("scale", 1),
                    z_index=s.get("z_index", 1)
                )
                db.session.add(new_sticker)
        
        db.session.commit()
        return jsonify({"success": True})

@app.route("/api/stickers/<page_type>/publish", methods=["POST"])
@login_required
def api_publish_sticker_snapshot(page_type):
    if page_type not in ['wiki', 'book', 'profile']:
        return jsonify({"error": "Invalid page type"}), 400
        
    data = request.json
    if not data:
         return jsonify({"error": "无效的请求数据，请确保Content-Type为application/json"}), 400

    title = data.get("title", f"{current_user.username}的{page_type}板")
    caption = data.get("caption", "")
    visibility = data.get("visibility", "followers") # Default to followers
    
    # Get current live stickers
    current_stickers = UserSticker.query.filter_by(user_id=current_user.id, page_type=page_type).all()
    
    if not current_stickers:
        return jsonify({"error": "Cannot publish empty board"}), 400
        
    stickers_data = [{
        "badge_id": s.badge_id,
        "badge_icon": badge_icon_url(s.badge.icon) if s.badge else "",
        "x": s.x,
        "y": s.y,
        "rotation": s.rotation,
        "scale": s.scale,
        "z_index": s.z_index
    } for s in current_stickers]
    
    snapshot = StickerBoardSnapshot(
        user_id=current_user.id,
        page_type=page_type,
        title=title,
        caption=caption,
        visibility=visibility,
        data_json=stickers_data
    )
    
    try:
        db.session.add(snapshot)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"数据库错误: {str(e)}"}), 500
    
    return jsonify({"success": True, "snapshot_id": snapshot.id})

@app.route("/api/stickers/snapshots", methods=["GET"])
@login_required
def api_sticker_snapshots():
    user_id_param = request.args.get('user_id')
    target_user_id = current_user.id
    if user_id_param:
        try:
            target_user_id = int(user_id_param)
        except ValueError:
            pass
            
    query = StickerBoardSnapshot.query.filter_by(user_id=target_user_id).order_by(StickerBoardSnapshot.created_at.desc())
    
    # Permission Check
    if target_user_id != current_user.id:
        # Filter based on visibility
        # If I am a follower, I can see 'followers' and 'public'
        # If I am just a stranger, I can only see 'public'
        target_user = User.query.get(target_user_id)
        if not target_user:
            return jsonify({"error": "User not found"}), 404
            
        if current_user.is_following(target_user):
            query = query.filter(StickerBoardSnapshot.visibility.in_(['followers', 'public']))
        else:
            query = query.filter(StickerBoardSnapshot.visibility == 'public')
            
    snapshots = query.all()
    
    return jsonify({
        "snapshots": [{
            "id": s.id,
            "page_type": s.page_type,
            "title": s.title,
            "caption": s.caption,
            "created_at": s.created_at.isoformat(),
            "likes_count": s.likes_count,
            "preview_count": len(s.data_json)
        } for s in snapshots]
    })

@app.route("/api/stickers/snapshots/<int:snapshot_id>", methods=["GET"])
@login_required
def api_sticker_snapshot_detail(snapshot_id):
    snapshot = StickerBoardSnapshot.query.get_or_404(snapshot_id)
    
    # Permission Check
    if snapshot.user_id != current_user.id:
        if snapshot.visibility == 'private':
            return jsonify({"error": "Permission denied"}), 403
        if snapshot.visibility == 'followers':
            target_user = User.query.get(snapshot.user_id)
            if not current_user.is_following(target_user):
                 return jsonify({"error": "Permission denied"}), 403
                 
    return jsonify({
        "id": snapshot.id,
        "user_id": snapshot.user_id,
        "user_name": snapshot.user.username if snapshot.user else "Unknown",
        "page_type": snapshot.page_type,
        "title": snapshot.title,
        "caption": snapshot.caption,
        "created_at": snapshot.created_at.isoformat(),
        "stickers": snapshot.data_json
    })

# System Announcement Routes

@app.route("/admin/announcements")
@login_required
def manage_announcements():
    if not current_user.is_admin:
        abort(403)
    announcements = SystemAnnouncement.query.order_by(SystemAnnouncement.created_at.desc()).all()
    return render_template("admin/manage_announcements.html", announcements=announcements)

@app.route("/admin/announcements/new", methods=["GET", "POST"])
@login_required
def new_announcement():
    if not current_user.is_admin:
        abort(403)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "")
        if not title:
            flash("标题不能为空")
            return redirect(url_for("new_announcement"))
        
        sa = SystemAnnouncement(
            title=title, 
            content=content, 
            created_by_id=current_user.id
        )
        db.session.add(sa)
        db.session.commit()
        flash("通知已发布")
        return redirect(url_for("manage_announcements"))
    return render_template("admin/edit_announcement.html", announcement=None)

@app.route("/admin/announcements/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_announcement_route(id):
    if not current_user.is_admin:
        abort(403)
    sa = SystemAnnouncement.query.get_or_404(id)
    if request.method == "POST":
        sa.title = request.form.get("title", "").strip()
        sa.content = request.form.get("content", "")
        sa.is_active = request.form.get("is_active") == "on"
        db.session.commit()
        flash("通知已更新")
        return redirect(url_for("manage_announcements"))
    return render_template("admin/edit_announcement.html", announcement=sa)

@app.route("/admin/announcements/<int:id>/delete", methods=["POST"])
@login_required
def delete_announcement(id):
    if not current_user.is_admin:
        abort(403)
    sa = SystemAnnouncement.query.get_or_404(id)
    # Cascade delete confirmations
    UserAnnouncementConfirmation.query.filter_by(announcement_id=id).delete()
    db.session.delete(sa)
    db.session.commit()
    flash("通知已删除")
    return redirect(url_for("manage_announcements"))

@app.route("/admin/announcements/<int:id>/stats")
@login_required
def announcement_stats(id):
    if not current_user.is_admin:
        abort(403)
    sa = SystemAnnouncement.query.get_or_404(id)
    confirmations = UserAnnouncementConfirmation.query.filter_by(announcement_id=id).all()
    confirmed_user_ids = [c.user_id for c in confirmations]
    
    all_users = User.query.all()
    confirmed_users = []
    unconfirmed_users = []
    
    for u in all_users:
        if u.id in confirmed_user_ids:
            # Attach confirmed time
            c = next((x for x in confirmations if x.user_id == u.id), None)
            u.confirmed_at = c.confirmed_at if c else None
            confirmed_users.append(u)
        else:
            unconfirmed_users.append(u)
            
    return render_template("admin/announcement_stats.html", announcement=sa, confirmed_users=confirmed_users, unconfirmed_users=unconfirmed_users)

@app.route("/api/announcements/check")
@login_required
def check_announcements():
    # 1. Find all active announcements
    active_anns = SystemAnnouncement.query.filter_by(is_active=True).order_by(SystemAnnouncement.created_at.desc()).all()
    
    if not active_anns:
        return jsonify({"has_unconfirmed": False, "has_history": False})
        
    # 2. Check confirmations
    confirmed_ids = [c.announcement_id for c in current_user.announcement_confirmations]
    
    # 3. Find first unconfirmed
    unconfirmed = None
    for ann in active_anns:
        if ann.id not in confirmed_ids:
            unconfirmed = ann
            break # Just need the latest one or the first one? usually show latest first.
            
    has_history = len(active_anns) > 0 # Basically if any exist, history is valid.
    
    if unconfirmed:
        html = markdown(unconfirmed.content or "")
        return jsonify({
            "has_unconfirmed": True,
            "has_history": has_history,
            "announcement": {
                "id": unconfirmed.id,
                "title": unconfirmed.title,
                "html": html,
                "created_at": unconfirmed.created_at.strftime("%Y-%m-%d")
            }
        })
    else:
        return jsonify({
            "has_unconfirmed": False,
            "has_history": has_history
        })

@app.route("/api/announcements/<int:id>/confirm", methods=["POST"])
@login_required
def confirm_announcement(id):
    sa = SystemAnnouncement.query.get_or_404(id)
    if not sa.is_active:
        return jsonify({"error": "Announcement is not active"}), 400
        
    exists = UserAnnouncementConfirmation.query.filter_by(user_id=current_user.id, announcement_id=id).first()
    if not exists:
        conf = UserAnnouncementConfirmation(user_id=current_user.id, announcement_id=id)
        db.session.add(conf)
        db.session.commit()
        
    return jsonify({"success": True})

@app.route("/api/announcements/history")
@login_required
def announcement_history():
    # Return list of all active announcements
    anns = SystemAnnouncement.query.filter_by(is_active=True).order_by(SystemAnnouncement.created_at.desc()).all()
    
    data = []
    for ann in anns:
        # Check if confirmed
        is_confirmed = UserAnnouncementConfirmation.query.filter_by(user_id=current_user.id, announcement_id=ann.id).first() is not None
        html = markdown(ann.content or "")
        data.append({
            "id": ann.id,
            "title": ann.title,
            "html": html,
            "created_at": ann.created_at.strftime("%Y-%m-%d"),
            "is_confirmed": is_confirmed
        })
        
    return jsonify({"announcements": data})

@app.route("/admin/announcements/files", methods=["GET"])
@login_required
def manage_announcement_files():
    if not current_user.is_admin:
        abort(403)
    files = AnnouncementFile.query.order_by(AnnouncementFile.uploaded_at.desc()).all()
    return render_template("admin/announcement_files.html", files=files)

@app.route("/admin/announcements/files/upload", methods=["POST"])
@login_required
def upload_announcement_file():
    if not current_user.is_admin:
        return {"error": "Permission denied"}, 403
        
    if "image" not in request.files:
        return {"error": "No file part"}, 400
    file = request.files["image"]
    if file.filename == "":
        return {"error": "No selected file"}, 400
    if file:
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
             return {"error": f"File type '{ext}' not allowed. Allowed: jpg, png, gif, webp"}, 400
        unique_filename = str(uuid.uuid4()) + ext
        
        # Ensure uploads directory exists
        upload_dir = os.path.join(app.config["UPLOAD_FOLDER"], "announcements")
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            
        file.save(os.path.join(upload_dir, unique_filename))
        
        file_path = url_for("static", filename=f"uploads/announcements/{unique_filename}")
        
        # Record in DB
        af = AnnouncementFile(
            filename=filename, 
            file_path=file_path, 
            uploaded_by_id=current_user.id
        )
        db.session.add(af)
        db.session.commit()
        
        return {"data": {"filePath": file_path, "filename": filename}}

@app.route("/admin/announcements/files/<int:file_id>/delete", methods=["POST"])
@login_required
def delete_announcement_file(file_id):
    if not current_user.is_admin:
        abort(403)
        
    af = AnnouncementFile.query.get_or_404(file_id)
    
    # Optional: Delete actual file from disk
    # filename = af.file_path.split("/")[-1]
    # file_path = os.path.join(app.config["UPLOAD_FOLDER"], "announcements", filename)
    # if os.path.exists(file_path):
    #     os.remove(file_path)
    
    db.session.delete(af)
    db.session.commit()
    flash("文件已删除")
    return redirect(url_for("manage_announcement_files"))

def upgrade_db():
    """Upgrade database schema manually"""
    with app.app_context():
        # Check if Badge table has start_time column
        inspector = db.inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('badge')]
        
        if 'start_time' not in columns:
            print("Upgrading Badge table: Adding start_time column...")
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE badge ADD COLUMN start_time DATETIME"))
                conn.commit()
                
        if 'end_time' not in columns:
            print("Upgrading Badge table: Adding end_time column...")
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE badge ADD COLUMN end_time DATETIME"))
                conn.commit()

        if 'sticker_count' not in columns:
            print("Upgrading Badge table: Adding sticker_count column...")
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE badge ADD COLUMN sticker_count INTEGER DEFAULT 1"))
                conn.commit()

        if 'total_limit' not in columns:
            print("Upgrading Badge table: Adding total_limit column...")
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE badge ADD COLUMN total_limit INTEGER"))
                conn.commit()

        if 'issued_count' not in columns:
            print("Upgrading Badge table: Adding issued_count column...")
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE badge ADD COLUMN issued_count INTEGER DEFAULT 0"))
                conn.commit()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        upgrade_db() # Run upgrade check
        
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5009")), debug=True)

@app.route('/service/wiki/pages')
@login_required
def service_wiki_pages():
    wiki_id = request.args.get('wiki_id', type=int)
    ns = request.args.get('ns', default=None)
    
    if not wiki_id:
        return jsonify({'error': 'wiki_id is required'}), 400
        
    wiki = Wiki.query.get_or_404(wiki_id)
    
    if not can_view_wiki(wiki.id):
        return jsonify({'error': 'Permission denied'}), 403

    query = WikiPage.query.filter_by(wiki_id=wiki_id)
    
    if ns:
        query = query.filter(WikiPage.title.like(f"{ns}:%"))
        
    pages = query.order_by(WikiPage.updated_at.desc()).all()
    
    pages_data = []
    for p in pages:
        parts = p.title.split(':', 1)
        namespace = parts[0] if len(parts) > 1 else 'Main'
        
        pages_data.append({
            'id': p.id,
            'title': p.title,
            'slug': p.slug,
            'namespace': namespace,
            'updated_at': p.updated_at.isoformat() if p.updated_at else None
        })
        
    return jsonify({'pages': pages_data})
