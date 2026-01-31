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

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///wikibook.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static/uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB limit

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

markdown = mistune.create_markdown(escape=False, plugins=["strikethrough", "table", "url", "task_lists"])

# UTC+8 Helper
def now_utc8():
    return datetime.utcnow() + timedelta(hours=8)

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
    
    subscriptions = db.relationship("Subscription", backref="user", cascade="all, delete-orphan")
    editor_roles = db.relationship("WikiEditor", backref="user", cascade="all, delete-orphan")
    notes = db.relationship("Note", backref="user", cascade="all, delete-orphan")
    shared_notes = db.relationship("NoteShare", backref="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
        
    return render_template("index.html", wikis=wikis, pages=pages, q=q)

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
        u = User.query.filter_by(username=username).first()
        if not u or not u.check_password(password):
            flash("用户名或密码错误")
            return redirect(url_for("login"))
        login_user(u)
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
        return {"data": {"filePath": url_for("static", filename=f"uploads/{unique_filename}")}}

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
    flash(f"已分享给 {count} 位用户")
    return redirect(url_for("view_note", note_id=n.id))

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
    
    status.last_active_at = now
    status.current_path = path
    status.current_action = action
    
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
    return {"status": "ok"}

@app.context_processor
def inject_helpers():
    # Count online users (active in last 5 mins)
    online_threshold = now_utc8() - timedelta(minutes=5)
    online_count = UserActiveStatus.query.filter(UserActiveStatus.last_active_at > online_threshold).count()
    
    return dict(
        can_view_wiki=can_view_wiki, 
        can_edit_wiki=can_edit_wiki,
        online_user_count=online_count
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5009")), debug=True)