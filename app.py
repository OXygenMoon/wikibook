import os
from datetime import datetime, timedelta
from flask import Flask, render_template, redirect, url_for, request, flash, abort, send_file, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mistune
import uuid

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

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscriptions = db.relationship("Subscription", backref="user", cascade="all, delete-orphan")
    editor_roles = db.relationship("WikiEditor", backref="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Wiki(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
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
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WikiViewLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wiki_id = db.Column(db.Integer, db.ForeignKey("wiki.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True) # 可以记录匿名访问，如果需要
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class WikiPageHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey("wiki_page.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False)
    content_md = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship("User", backref="page_history")
    page = db.relationship("WikiPage", backref=db.backref("history", cascade="all, delete-orphan", order_by="desc(WikiPageHistory.created_at)"))

class WikiEditor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wiki_id = db.Column(db.Integer, db.ForeignKey("wiki.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wiki_id = db.Column(db.Integer, db.ForeignKey("wiki.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MarkdownStyle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    css_text = db.Column(db.Text, default="")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

@app.context_processor
def inject_helpers():
    return dict(can_view_wiki=can_view_wiki, can_edit_wiki=can_edit_wiki)

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
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not username or not email or not password:
            flash("请填写完整信息")
            return redirect(url_for("register"))
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("用户名或邮箱已存在")
            return redirect(url_for("register"))
        u = User(username=username, email=email)
        u.set_password(password)
        
        # 获取表单中的 is_admin 选项
        if request.form.get("is_admin") == "on":
            u.is_admin = True
        # 如果是第一个用户，强制设为管理员（双重保障）
        elif User.query.count() == 0:
            u.is_admin = True
            
        db.session.add(u)
        db.session.commit()
        login_user(u)
        return redirect(url_for("index"))
    return render_template("register.html")

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
        if not title or not slug:
            flash("标题与标识不能为空")
            return redirect(url_for("new_page", wiki_id=wiki_id))
        p = WikiPage(wiki_id=wiki_id, title=title, slug=slug, content_md=content_md)
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
    
    # 再次确认排序需求：
    # 负数：置顶，升序。例如：-10, -5, -1
    # 正数：普通，升序。例如：1, 2, 10
    # 所以直接 sort(key=int) 即可满足 -10 < -5 < -1 < 1 < 2 < 10
    
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
        db.session.commit()
        return redirect(url_for("view_page", wiki_id=wiki_id, slug=p.slug))
    return render_template("wiki/edit_page.html", wiki=w, page=p)

@app.route("/wikis/<int:wiki_id>/pages/<slug>/history")
@login_required
def page_history(wiki_id, slug):
    w = Wiki.query.get_or_404(wiki_id)
    p = WikiPage.query.filter_by(wiki_id=wiki_id, slug=slug).first_or_404()
    # 允许所有能看页面的人查看历史？或者仅限编辑者？
    # 假设仅限编辑者查看历史和回滚
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
        
    # 保存当前版本到历史
    current_history = WikiPageHistory(
        page_id=p.id,
        user_id=current_user.id,
        title=p.title,
        slug=p.slug,
        content_md=p.content_md
    )
    db.session.add(current_history)
    
    # 恢复旧版本
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
    
    # 订阅用户列表
    subscribers = User.query.join(Subscription).filter(Subscription.wiki_id == wiki_id).all()
    
    # 统计数据
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
    editors = db.session.query(User.username).join(WikiEditor, WikiEditor.user_id == User.id).filter(WikiEditor.wiki_id == wiki_id).all()
    return render_template("admin/manage_editors.html", wiki=w, editors=[x[0] for x in editors])

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
             return {"error": "File type not allowed"}, 400
             
        unique_filename = str(uuid.uuid4()) + ext
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], unique_filename))
        
        return {"data": {"filePath": url_for("static", filename=f"uploads/{unique_filename}")}}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5009")), debug=True)
