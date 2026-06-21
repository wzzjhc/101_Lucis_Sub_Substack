import os
import re
import shutil
import sys
import webbrowser
import ctypes
import time 
from datetime import datetime
from urllib.parse import unquote, urlparse
from bs4 import BeautifulSoup

# 引入 PyQt6 核心组件
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QKeyEvent, QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QLineEdit, QTextEdit, 
    QFileDialog, QMessageBox, QFrame, QScrollArea, QDialog, QGraphicsDropShadowEffect, QCheckBox
)


from PyQt6.QtGui import QTextDocumentFragment
import re

class SmartWhiteTextEdit(QTextEdit):
    """ 智能文本框：无论复制什么格式，其中的中英文、数字、符号一律强制洗成白色 """
    def insertFromMimeData(self, source):
        # 1. 优先获取纯文本内容（这样能直接剥离网页自带的恶心颜色和背景）
        text_content = source.text()
        
        if text_content:
            # 2. 将文本中的特殊 HTML 字符（如 <, >, &）进行转义，防止破坏 HTML 结构
            safe_text = (text_content
                         .replace("&", "&amp;")
                         .replace("<", "&lt;")
                         .replace(">", "&gt;")
                         .replace("\n", "<br>")) # 保留回车换行
            
            # 3. 使用标准暗黑模式高亮样式包裹，强制所有常规字符（中英数标点）变成纯白色
            # color: #ffffff !important 确保拥有最高优先级，不被任何其他样式覆盖
            html_content = f'<div style="color: #ffffff !important; font-family: sans-serif;">{safe_text}</div>'
            
            # 4. 将处理好的白色富文本片段插入到光标所在位置
            fragment = QTextDocumentFragment.fromHtml(html_content)
            self.textCursor().insertFragment(fragment)
        else:
            # 如果是其他不带文本的数据（如纯图片），走默认流程
            super().insertFromMimeData(source)











# ==============================================================================
#  【核心动态路径支持】解决 GitHub 打包及 PyInstaller 单文件释放路径问题
# ==============================================================================
def resource_path(relative_path):
    """ 获取程序运行时的绝对路径（兼容 PyInstaller 打包后的临时释放路径） """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ==============================================================================
#  【路径精简算法】只显示文件名和上级文件夹名
# ==============================================================================
def get_short_path_display(full_path):
    """ 将全局路径转换为 '上级文件夹/文件名' 的格式 """
    if not full_path:
        return ""
    normalized_path = os.path.normpath(full_path)
    base_name = os.path.basename(normalized_path)
    parent_dir = os.path.basename(os.path.dirname(normalized_path))
    if parent_dir:
        return f".../{parent_dir}/{base_name}"
    return base_name


# ==============================================================================
#  【高保真实心色彩 + 物理阴影立体感】QSS 视觉引擎
# ==============================================================================
QSS_STYLE = """
QMainWindow {
    background-color: #0b1329; 
}
#CentralContainer {
    border: 2px solid #1e293b;
    background-color: #0b1329;
}
QTabWidget::pane {
    border: 2px solid #1d4ed8;
    background: #0f172a; 
    border-radius: 12px;
}
QTabBar::tab {
    background: #1e293b;
    color: #94a3b8;
    padding: 12px 24px;
    font-size: 13px;
    font-weight: bold;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 4px;
}
QTabBar::tab:hover {
    background: #2563eb;
    color: #ffffff;
}
QTabBar::tab:selected {
    background: #2563eb; 
    color: #ffffff;
    border: 1px solid #60a5fa;
    border-bottom: none;
}

QFrame#CardFrame {
    background: #141b2d; 
    border: 2px solid #1e293b; 
    border-radius: 12px;
}

QLineEdit, QTextEdit {
    background-color: #020617; 
    border: 2px solid #3b82f6; 
    border-radius: 8px;
    padding: 8px;
    color: #ffffff; 
    font-size: 14px;
}
QLineEdit:disabled, QTextEdit:disabled {
    background-color: #0f172a;
    border-color: #1e293b;
    color: #64748b;
}

QLabel#DropZoneClickable {
    background: #020617;
    border: 2px dashed #3b82f6;
    border-radius: 10px;
    color: #38bdf8; 
    font-weight: bold;
    font-size: 13px;
}

QCheckBox {
    color: #38bdf8;
    font-size: 14px;
    font-weight: bold;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #3b82f6;
    border-radius: 4px;
    background: #020617;
}
QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #60a5fa;
}

/* 顶部辅助小按钮 */
QPushButton#BtnMin { background-color: #1e293b; color: white; border: none; border-radius: 6px; }
QPushButton#BtnMin:hover { background-color: #334155; }
QPushButton#BtnClose { background-color: #991b1b; color: white; border: none; border-radius: 6px; }
QPushButton#BtnClose:hover { background-color: #ef4444; }

/* 统一控制所有系统内置弹窗提示的字体颜色 */
QMessageBox QLabel {
    color: #000000 !important;
}
QMessageBox QPushButton {
    color: #000000 !important;
    background-color: #e2e8f0;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 5px 12px;
}
QMessageBox QPushButton:hover {
    background-color: #cbd5e1;
}

/* 按钮全面五彩斑斓化 + 物理反馈压实下沉效果 */
QPushButton#BtnBlue {
    background-color: #2563eb; color: #ffffff !important; font-weight: bold; font-size: 14px;
    border: 1px solid #3b82f6; border-radius: 8px; padding: 10px 15px;
}
QPushButton#BtnBlue:hover { background-color: #1d4ed8; border-color: #60a5fa; }
QPushButton#BtnBlue:pressed { background-color: #1e40af; padding-top: 12px; padding-bottom: 8px; }
QPushButton#BtnBlue:disabled { background-color: #1e293b; color: #64748b; border: none; }

QPushButton#BtnOrange {
    background-color: #ea580c; color: #ffffff !important; font-weight: bold; font-size: 14px;
    border: 1px solid #f97316; border-radius: 8px; padding: 10px 15px;
}
QPushButton#BtnOrange:hover { background-color: #c2410c; border-color: #ffaa66; }
QPushButton#BtnOrange:pressed { background-color: #9a3412; padding-top: 12px; padding-bottom: 8px; }
QPushButton#BtnOrange:disabled { background-color: #1e293b; color: #64748b; border: none; }

QPushButton#BtnMint {
    background-color: #059669; color: #ffffff !important; font-weight: bold; font-size: 14px;
    border: 1px solid #10b981; border-radius: 8px; padding: 10px 15px;
}
QPushButton#BtnMint:hover { background-color: #047857; border-color: #34d399; }
QPushButton#BtnMint:pressed { background-color: #065f46; padding-top: 12px; padding-bottom: 8px; }
QPushButton#BtnMint:disabled { background-color: #1e293b; color: #64748b; border: none; }

QPushButton#BtnPurple {
    background-color: #7c3aed; color: #ffffff !important; font-weight: bold; font-size: 14px;
    border: 1px solid #8b5cf6; border-radius: 8px; padding: 10px 15px;
}
QPushButton#BtnPurple:hover { background-color: #6d28d9; border-color: #a78bfa; }
QPushButton#BtnPurple:pressed { background-color: #5b21b6; padding-top: 12px; padding-bottom: 8px; }
QPushButton#BtnPurple:disabled { background-color: #1e293b; color: #64748b; border: none; }

QPushButton#BtnRed {
    background-color: #dc2626; color: #ffffff !important; font-weight: bold; font-size: 14px;
    border: 1px solid #ef4444; border-radius: 8px; padding: 10px 15px;
}
QPushButton#BtnRed:hover { background-color: #b91c1c; border-color: #fca5a5; }
QPushButton#BtnRed:pressed { background-color: #991b1b; padding-top: 12px; padding-bottom: 8px; }
QPushButton#BtnRed:disabled { background-color: #1e293b; color: #64748b; border: none; }

QPushButton#BtnDark {
    background-color: #334155; color: #ffffff !important; font-weight: bold; font-size: 14px;
    border: 1px solid #475569; border-radius: 8px; padding: 10px 15px;
}
QPushButton#BtnDark:hover { background-color: #475569; border-color: #64748b; }
QPushButton#BtnDark:pressed { background-color: #1e293b; padding-top: 12px; padding-bottom: 8px; }

QLabel { color: #ffffff; font-size: 13px; }
QLabel#TitleLabel { font-size: 19px; font-weight: bold; color: #ffffff; }
QLabel#SubTitleLabel { font-size: 11px; color: #60a5fa; }
QLabel#SectionTitle { font-size: 14px; font-weight: bold; color: #38bdf8; }
"""

# ==============================================================================
#  关于说明窗体
# ==============================================================================
class AboutLinkDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.setWindowIcon(QIcon(resource_path("logo.png")))
        self.setFixedSize(480, 420)
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; border: 2px solid #2563eb; border-radius: 8px; }
            QLabel { color: #000000 !important; font-size: 13px; }
            QPushButton { background-color: #2563eb; color: white !important; font-weight: bold; border-radius: 6px; padding: 8px 16px; border: none; }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("💡 离线数据管理架构说明")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1d4ed8 !important;")
        layout.addWidget(title)

        body_text = QLabel(
            "1. <b>【数据生成】</b> subscribers页面下载好, 将HTML 拖入第一页运行，系统将自动提纯离线数据报表，并完整提取打包本地头像。<br><br>"
            "2. <b>【回写备注】</b> 将生成的订阅者表格.html表格文件拖入第二页，即可依据序号修改每个人的自定义备注、绑定关键网址、上传自拍照。<br><br>"
            "🔒 <b>【隐私声明】：</b> 本软件为本地化离线工具，不收集、不外发任何个人路径及数据隐私。【Esc+数字0=关闭程序】"
        )
        body_text.setWordWrap(True)
        layout.addWidget(body_text)
       
        self.link_label = QLabel(
            '🌐 服务官方主页: <a href="https://91tv.vip/" style="color: #2563eb; text-decoration: underline;">https://91tv.vip/</a><br>'
            '💻 GitHub 项目: <a href="https://github.com/wzzjhc/101_Lucis_Sub_Substack" style="color: #2563eb; text-decoration: underline;">【点击并跳转，在右侧Releases处下载】</a><br>'
            '☁️ 腾讯微云备用: <a href="https://share.weiyun.com/xjl1XWcT" style="color: #2563eb; text-decoration: underline;">【点击下载最新版本】</a>'
            
            
        )
        self.link_label.setOpenExternalLinks(False)
        self.link_label.linkActivated.connect(self.safely_open_url)
        layout.addWidget(self.link_label)

        self.like_label = QLabel()
        like_pixmap = QPixmap(resource_path("like.png"))
        
        if not like_pixmap.isNull():
            self.like_label.setPixmap(like_pixmap.scaled(277, 213, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.like_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.like_label)
        else:
            self.like_label.setText("（👍 点赞图片加载失败，请检查 like.png 是否存在）")
            self.like_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.like_label)

        layout.addStretch()
        close_btn = QPushButton("我知道了")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignRight)

    def safely_open_url(self, url):
        try:
            webbrowser.open(url)
        except Exception:
            QMessageBox.information(self, "跳转提示", f"系统默认浏览器唤醒失败，请手动访问：\n{url}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lucis 启明_小工具👉作者：胡家三少")
        
        icon_path = resource_path("favicon.ico")
        self.setWindowIcon(QIcon(icon_path))
        self.setFixedSize(720, 950)
        
        # ====== 📢 核心修改点：无边框且强显任务栏图标 ======
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                            Qt.WindowType.Window | 
                            Qt.WindowType.WindowSystemMenuHint |
                            Qt.WindowType.WindowMinMaxButtonsHint)
        
        self.setStyleSheet(QSS_STYLE)

        # 业务缓存槽
        self.selected_file_path = ""
        self.loaded_html_path = ""   
        self.soup_writer = None      
        self.target_tr = None        
        self.current_serial_id = ""  
        self.link_profile = ""
        self.link_substack = ""

        # 第三页动态扩展所需的独立缓存槽与控件结构体
        self.p3_files = []      # 存储文件完整路径的列表
        self.p3_frames = []     # 存储动态生成的 QFrame 容器
        self.p3_labels = []     # 存储动态生成的显示 QLabel 
        self.p3_inputs = []     # 存储动态生成的人工序号 QLineEdit

        self.pressed_keys = {}
        self.setAcceptDrops(True)
        self.drag_position = None

        self.init_ui()

    def add_button_shadow(self, button):
        """给按钮灌注物理悬浮阴影效果"""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(Qt.GlobalColor.black)
        shadow.setOffset(0, 4)
        button.setGraphicsEffect(shadow)

    def init_ui(self):
        central_container = QWidget()
        central_container.setObjectName("CentralContainer")
        self.setCentralWidget(central_container)
        
        outer_layout = QVBoxLayout(central_container)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # ==================== 顶部定制导航标题栏 ====================
        title_bar_frame = QFrame()
        title_bar_frame.setObjectName("CardFrame")
        title_bar_frame.setStyleSheet("border-radius: 0px; border-bottom: 2px solid #1e293b;")
        title_bar_layout = QHBoxLayout(title_bar_frame)
        title_bar_layout.setContentsMargins(15, 10, 15, 10)
        title_bar_layout.setSpacing(12)

        self.logo_label = QLabel()
        self.logo_label.setFixedSize(48, 48)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setStyleSheet("border: 1px solid #2563eb; background: #1e293b; border-radius: 8px;")
        
        real_logo_path = resource_path("logo.png")
        if os.path.exists(real_logo_path):
            pix = QPixmap(real_logo_path).scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(pix)
        else:
            self.logo_label.setText("LOGO")

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(1)
        title_label = QLabel("Substack订阅者数据管理")
        title_label.setObjectName("TitleLabel")
        subtitle_label = QLabel("Lucis 启明_小工具👉作者：胡家三少")
        subtitle_label.setObjectName("SubTitleLabel")
        title_vbox.addWidget(title_label)
        title_vbox.addWidget(subtitle_label)

        about_btn = QPushButton("💻")
        about_btn.setStyleSheet("QPushButton { background-color: #1e293b; border: 1px solid #3b82f6; border-radius: 6px; font-size: 16px; color: white; } QPushButton:hover { background-color: #2563eb; }")
        about_btn.setFixedSize(40, 32)
        about_btn.clicked.connect(self.show_about_dialog)

        min_btn = QPushButton("➖")
        min_btn.setObjectName("BtnMin")
        min_btn.setFixedSize(36, 32)
        min_btn.clicked.connect(self.showMinimized)

        close_btn = QPushButton("❌")
        close_btn.setObjectName("BtnClose")
        close_btn.setFixedSize(36, 32)
        close_btn.clicked.connect(self.close)

        title_bar_layout.addWidget(self.logo_label)
        title_bar_layout.addLayout(title_vbox)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(about_btn)
        title_bar_layout.addWidget(min_btn)
        title_bar_layout.addWidget(close_btn)
        outer_layout.addWidget(title_bar_frame)

        # ==================== 主控内容选项卡区 ====================
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)

        self.tabs = QTabWidget()
        content_layout.addWidget(self.tabs)
        outer_layout.addWidget(content_widget)

        self.page1 = QWidget()
        self.page2 = QWidget()
        self.page3 = QWidget() 
        self.tabs.addTab(self.page1, "📥 提取本地数据生成表格")
        self.tabs.addTab(self.page2, "✍️ 自定义备注写入修改")
        self.tabs.addTab(self.page3, "🔀 合并多个订阅者表格")

        self.setup_page1()
        self.setup_page2()
        self.setup_page3()
        
    def show_message(self, title, text, is_error=False):
        msg_box = QMessageBox() 
        msg_box.setParent(self, Qt.WindowType.Dialog)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        
        if is_error or any(word in title for word in ["错", "失败", "异常"]):
            msg_box.setIcon(QMessageBox.Icon.Critical)
        else:
            msg_box.setIcon(QMessageBox.Icon.Information)
            
        icon_path = resource_path("logo.png")
        if os.path.exists(icon_path):
            msg_box.setWindowIcon(QIcon(icon_path))
        msg_box.exec()

    def setup_page1(self):
        layout = QVBoxLayout(self.page1)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        file_frame = QFrame()
        file_frame.setObjectName("CardFrame")
        file_layout = QVBoxLayout(file_frame)
        file_layout.setContentsMargins(15, 15, 15, 15)

        sec1_title = QLabel("1. 选择 Substack 原始网页文件 (.html / .htm)")
        sec1_title.setObjectName("SectionTitle")
        file_layout.addWidget(sec1_title)

        file_hbox = QHBoxLayout()
        self.p1_drop_label = QLabel("✨ 任意拖放源 HTML 文件至此窗体内，或点击右侧选取...")
        self.p1_drop_label.setObjectName("DropZoneClickable")
        self.p1_drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.p1_drop_label.setMinimumHeight(65)
        
        p1_browse_btn = QPushButton("📂 选取源文件")
        p1_browse_btn.setObjectName("BtnBlue") 
        p1_browse_btn.setMinimumHeight(40)
        p1_browse_btn.clicked.connect(self.browse_source_file)
        self.add_button_shadow(p1_browse_btn)

        file_hbox.addWidget(self.p1_drop_label, 7)
        file_hbox.addWidget(p1_browse_btn, 3)
        file_layout.addLayout(file_hbox)
        layout.addWidget(file_frame)

        cfg_frame = QFrame()
        cfg_frame.setObjectName("CardFrame")
        cfg_layout = QVBoxLayout(cfg_frame)
        cfg_layout.setContentsMargins(15, 15, 15, 15)
        cfg_layout.setSpacing(12)

        sec2_title = QLabel("2. 自定义表格头部配置参数")
        sec2_title.setObjectName("SectionTitle")
        cfg_layout.addWidget(sec2_title)

        cfg_layout.addWidget(QLabel("下载来源网址:"))
        self.cfg_url_input = QLineEdit("https://substack.com/@样本/subscribers")
        cfg_layout.addWidget(self.cfg_url_input)

        param_hbox = QHBoxLayout()
        author_vbox = QVBoxLayout()
        author_vbox.addWidget(QLabel("博主:"))
        self.cfg_author_input = QLineEdit("某人")
        author_vbox.addWidget(self.cfg_author_input)

        date_vbox = QVBoxLayout()
        date_vbox.addWidget(QLabel("数据下载日期:"))
        self.cfg_date_input = QLineEdit(datetime.now().strftime("%Y年%m月%d日"))
        date_vbox.addWidget(self.cfg_date_input)

        param_hbox.addLayout(author_vbox)
        param_hbox.addLayout(date_vbox)
        cfg_layout.addLayout(param_hbox)
        layout.addWidget(cfg_frame)

        self.btn_start_ex = QPushButton("🚀 开始提取本地数据并打包头像")
        self.btn_start_ex.setObjectName("BtnMint") 
        self.btn_start_ex.setMinimumHeight(55)
        self.btn_start_ex.setEnabled(False)
        self.btn_start_ex.clicked.connect(self.execute_extraction)
        self.add_button_shadow(self.btn_start_ex)
        
        layout.addWidget(self.btn_start_ex)
        layout.addStretch()

    def setup_page2(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        container = QWidget()
        container.setObjectName("Page2Container")
        container.setStyleSheet("QWidget#Page2Container { background-color: #0f172a; }")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        src_frame = QFrame()
        src_frame.setObjectName("CardFrame")
        src_layout = QVBoxLayout(src_frame)
        src_layout.setContentsMargins(15, 15, 15, 15)

        sec1_title = QLabel("1. 加载生成的订阅者表格 (支持拖入)")
        sec1_title.setObjectName("SectionTitle")
        src_layout.addWidget(sec1_title)

        src_hbox = QHBoxLayout()
        self.p2_drop_label = QLabel("❌ 拖入 或 直接点击此框加载 [订阅者表格_时间戳.html]")
        self.p2_drop_label.setObjectName("DropZoneClickable")
        self.p2_drop_label.setCursor(Qt.CursorShape.PointingHandCursor) 
        self.p2_drop_label.setStyleSheet("color: #f87171; background-color: #020617; border-color: #ef4444;")
        self.p2_drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.p2_drop_label.setMinimumHeight(65)
        self.p2_drop_label.mousePressEvent = lambda e: self.browse_writer_table_file()

        self.btn_view_browser = QPushButton("🌐 查看网页")
        self.btn_view_browser.setObjectName("BtnOrange") 
        self.btn_view_browser.setMinimumHeight(45)
        self.btn_view_browser.setEnabled(False)
        self.btn_view_browser.clicked.connect(self.open_current_table_in_browser)
        self.add_button_shadow(self.btn_view_browser)

        src_hbox.addWidget(self.p2_drop_label, 7)
        src_hbox.addWidget(self.btn_view_browser, 3)
        src_layout.addLayout(src_hbox)
        layout.addWidget(src_frame)

        query_frame = QFrame()
        query_frame.setObjectName("CardFrame")
        query_layout = QVBoxLayout(query_frame)
        query_layout.setContentsMargins(15, 15, 15, 15)

        sec2_title = QLabel("2. 订阅者序号")
        sec2_title.setObjectName("SectionTitle")
        query_layout.addWidget(sec2_title)

        query_hbox = QHBoxLayout()
        self.serial_input = QLineEdit()
        self.serial_input.setPlaceholderText("请输入操作序号 (如: 1)...")
        self.serial_input.setEnabled(False)
        self.serial_input.returnPressed.connect(self.query_subscriber_by_id)

        self.btn_query = QPushButton("🔍 提取信息")
        self.btn_query.setObjectName("BtnPurple") 
        self.btn_query.setEnabled(False)
        self.btn_query.clicked.connect(self.query_subscriber_by_id)
        self.add_button_shadow(self.btn_query)

        query_hbox.addWidget(self.serial_input, 7)
        query_hbox.addWidget(self.btn_query, 3)
        query_layout.addLayout(query_hbox)
        layout.addWidget(query_frame)

        self.snapshot_frame = QFrame()
        self.snapshot_frame.setObjectName("CardFrame")
        snap_layout = QVBoxLayout(self.snapshot_frame)
        snap_layout.setContentsMargins(15, 15, 15, 15)
        snap_layout.setSpacing(10)

        sec3_title = QLabel("3. 当前订阅者数据")
        sec3_title.setObjectName("SectionTitle")
        snap_layout.addWidget(sec3_title)

        name_hbox = QHBoxLayout()
        name_hbox.addWidget(QLabel("昵称 / 姓名:"))
        self.res_name_label = QLabel("（等待加载）")
        self.res_name_label.setStyleSheet("color: #38bdf8;  font-weight: bold; font-size: 14px;")
        self.res_name_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.res_name_label.mousePressEvent = lambda e: self.open_link(1)
        name_hbox.addWidget(self.res_name_label, Qt.AlignmentFlag.AlignRight)
        snap_layout.addLayout(name_hbox)

        intro_hbox = QHBoxLayout()
        intro_hbox.addWidget(QLabel("专栏简介:"))
        self.res_intro_label = QLabel("（等待加载）")
        self.res_intro_label.setStyleSheet("color: #38bdf8; font-size: 14px;")
        self.res_intro_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.res_intro_label.mousePressEvent = lambda e: self.open_link(2)
        intro_hbox.addWidget(self.res_intro_label, Qt.AlignmentFlag.AlignRight)
        snap_layout.addLayout(intro_hbox)

        selfie_hbox = QHBoxLayout()
        selfie_hbox.addWidget(QLabel("自拍照状态:"))
        self.res_selfie_badge = QLabel("暂无图片")
        self.res_selfie_badge.setStyleSheet("background: #7f1d1d; color: #fca5a5; padding: 4px 12px; border-radius: 10px; font-weight: bold;")
        
        self.btn_upload_selfie = QPushButton("📸 上传自拍照")
        self.btn_upload_selfie.setObjectName("BtnBlue") 
        self.btn_upload_selfie.setEnabled(False)
        self.btn_upload_selfie.clicked.connect(self.upload_selfie_image)
        self.add_button_shadow(self.btn_upload_selfie)

        selfie_hbox.addWidget(self.res_selfie_badge)
        selfie_hbox.addStretch()
        selfie_hbox.addWidget(self.btn_upload_selfie)
        snap_layout.addLayout(selfie_hbox)
        layout.addWidget(self.snapshot_frame)

        self.url_frame = QFrame()
        self.url_frame.setObjectName("CardFrame")
        url_layout = QVBoxLayout(self.url_frame)
        url_layout.setContentsMargins(15, 15, 15, 15)

        sec4_title = QLabel("4. 关键网址")
        sec4_title.setObjectName("SectionTitle")
        url_layout.addWidget(sec4_title)

        url_hbox = QHBoxLayout()
        self.key_url_input = QLineEdit()
        self.key_url_input.setPlaceholderText("请输入独立跳转 URL...")
        self.key_url_input.setEnabled(False)
        
        self.btn_save_url = QPushButton("💾 保存网址")
        self.btn_save_url.setObjectName("BtnRed") 
        self.btn_save_url.setEnabled(False)
        self.btn_save_url.clicked.connect(self.submit_key_url_data)
        self.add_button_shadow(self.btn_save_url)

        url_hbox.addWidget(self.key_url_input, 7)
        url_hbox.addWidget(self.btn_save_url, 3)
        url_layout.addLayout(url_hbox)
        layout.addWidget(self.url_frame)

        self.remark_frame = QFrame()
        self.remark_frame.setObjectName("CardFrame")
        rem_layout = QVBoxLayout(self.remark_frame)
        rem_layout.setContentsMargins(15, 15, 15, 15)
        rem_layout.setSpacing(12)

        sec5_title = QLabel("5. 自定义备注介绍详情_[注意!网页上复制过来的黑色字体会看不到]")
        sec5_title.setObjectName("SectionTitle")
        rem_layout.addWidget(sec5_title)

        self.remark_textarea = SmartWhiteTextEdit() 
        
        self.remark_textarea.setPlaceholderText("编辑或输入该用户的自定义备注信息，允许直接按回车换行进行规整...")
        self.remark_textarea.setEnabled(False)
        self.remark_textarea.setMaximumHeight(90)
        rem_layout.addWidget(self.remark_textarea)
        
         

       # ================== 修改后代码 ==================
        action_hbox = QHBoxLayout()
        self.check_verify = QCheckBox("已查验/未查验)")
        self.check_verify.setEnabled(False)
        action_hbox.addWidget(self.check_verify, 3) # 适当微调权重占比

        # 放置两个保存按钮的右侧子布局
        btn_sub_hbox = QHBoxLayout()
        btn_sub_hbox.setSpacing(10) # 两个按钮之间的间距

        # 1. 原有的 保存数据 按钮
        self.btn_save_remark = QPushButton("💾 保存数据")
        self.btn_save_remark.setObjectName("BtnMint") 
        self.btn_save_remark.setEnabled(False)
       
        self.btn_save_remark.setMinimumHeight(45)
        self.btn_save_remark.clicked.connect(self.submit_remark_data)
        self.add_button_shadow(self.btn_save_remark)
        btn_sub_hbox.addWidget(self.btn_save_remark)

        # 2. 新增的 保存并提取下一位 按钮 (这里使用橘色或蓝色样式，比如 BtnOrange 或 BtnBlue)
        self.btn_save_next = QPushButton("⏩ 保存并提取下一位")
        self.btn_save_next.setObjectName("BtnOrange")  
        self.btn_save_next.setEnabled(False)
        self.btn_save_next.setMinimumHeight(45)
        self.btn_save_next.clicked.connect(self.save_and_query_next_subscriber) # 绑定新编写的方法
        self.add_button_shadow(self.btn_save_next)
        btn_sub_hbox.addWidget(self.btn_save_next)

        action_hbox.addLayout(btn_sub_hbox, 7) # 将按钮子布局加到主整行布局中
        rem_layout.addLayout(action_hbox)
        layout.addWidget(self.remark_frame)

        scroll.setWidget(container)
        page2_layout = QVBoxLayout(self.page2)
        page2_layout.setContentsMargins(0, 0, 0, 0)
        page2_layout.addWidget(scroll)

    # ==============================================================================
    #  【重构核心】选项卡3：合并多份离线订阅者报表数据
    # ==============================================================================
    def setup_page3(self):
        # 引入滚动条框架，防止后期动态增加无限多区块后界面溢出
        p3_scroll = QScrollArea()
        p3_scroll.setWidgetResizable(True)
        p3_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        p3_container = QWidget()
        p3_container.setObjectName("Page3Container")
        p3_container.setStyleSheet("QWidget#Page3Container { background-color: #0f172a; }")
        
        self.p3_scroll_layout = QVBoxLayout(p3_container)
        self.p3_scroll_layout.setContentsMargins(15, 15, 15, 15)
        self.p3_scroll_layout.setSpacing(15)

        # 🎯 需求 1：把第一页的 自定义表格头部配置参数一项 完美复制抄写到第三页的第一项
        self.p3_cfg_frame = QFrame()
        self.p3_cfg_frame.setObjectName("CardFrame")
        p3_cfg_layout = QVBoxLayout(self.p3_cfg_frame)
        p3_cfg_layout.setContentsMargins(15, 15, 15, 15)
        p3_cfg_layout.setSpacing(12)

        sec_title_p3 = QLabel("1. 自定义合并表格头部配置参数")
        sec_title_p3.setObjectName("SectionTitle")
        p3_cfg_layout.addWidget(sec_title_p3)

        p3_cfg_layout.addWidget(QLabel("合并下载来源网址:"))
        self.p3_cfg_url_input = QLineEdit("https://substack.com/@样本/subscribers")
        p3_cfg_layout.addWidget(self.p3_cfg_url_input)

        p3_param_hbox = QHBoxLayout()
        p3_author_vbox = QVBoxLayout()
        p3_author_vbox.addWidget(QLabel("合并博主:"))
        self.p3_cfg_author_input = QLineEdit("某人")
        p3_author_vbox.addWidget(self.p3_cfg_author_input)

        p3_date_vbox = QVBoxLayout()
        p3_date_vbox.addWidget(QLabel("合并数据日期:"))
        self.p3_cfg_date_input = QLineEdit(datetime.now().strftime("%Y年%m月%d日"))
        p3_date_vbox.addWidget(self.p3_cfg_date_input)

        p3_param_hbox.addLayout(p3_author_vbox)
        p3_param_hbox.addLayout(p3_date_vbox)
        p3_cfg_layout.addLayout(p3_param_hbox)
        self.p3_scroll_layout.addWidget(self.p3_cfg_frame)

        # 容器层，用于存放动态增减的文件数据区块
        self.blocks_container_widget = QWidget()
        self.blocks_layout = QVBoxLayout(self.blocks_container_widget)
        self.blocks_layout.setContentsMargins(0, 0, 0, 0)
        self.blocks_layout.setSpacing(15)
        self.p3_scroll_layout.addWidget(self.blocks_container_widget)

        # 🎯 需求 3 & 4 & 9：初始化创建 2 个默认的数据区块
        self.adjust_p3_block_count(2)

        # 动作控制按钮面板
        btn_frame = QFrame()
        btn_frame.setObjectName("CardFrame")
        btn_layout = QVBoxLayout(btn_frame)
        btn_layout.setContentsMargins(15, 15, 15, 15)

        bottom_btn_hbox = QHBoxLayout()
        bottom_btn_hbox.setSpacing(15)

        # 🎯 需求 9：点击清除重置按钮后，清除全部路径与人工序号，一切恢复为 2 个区块
        self.btn_p3_reset = QPushButton("🧹 清除重置")
        self.btn_p3_reset.setObjectName("BtnDark")
        self.btn_p3_reset.setMinimumHeight(55)
        self.btn_p3_reset.clicked.connect(self.reset_page3_fields)
        self.add_button_shadow(self.btn_p3_reset)

        self.btn_merge_action = QPushButton("🔀 开始融合")
        self.btn_merge_action.setObjectName("BtnPurple")
        self.btn_merge_action.setMinimumHeight(55)
        self.btn_merge_action.clicked.connect(self.execute_merge_logic)
        self.add_button_shadow(self.btn_merge_action)

        bottom_btn_hbox.addWidget(self.btn_p3_reset, 3)     
        bottom_btn_hbox.addWidget(self.btn_merge_action, 7)  
        btn_layout.addLayout(bottom_btn_hbox)
        self.p3_scroll_layout.addWidget(btn_frame)

        # 🎯 需求 2：把合并多份离线订阅者报表数据，这个说明移到最底部，按钮下方
        self.p3_description_label = QLabel(
            "🔀 合并说明：<br>"
            "1. 支持<b>批量无缝拖入</b>任意个网页文件、文本文档或直接拖入包含它们的<b>多级文件夹</b>。<br>"
            "2. 类似打印机页数规则输入，如：<b>1-25, 40-50, 66, 200</b>。<br>"
            "3. <b>如果范围栏留空</b>，系统会智能识别该文件中所有在第二页已被标记为<b>已查验</b>的数据进行合并。<br>"
            "4. 合并后的新表格数据，序号将自动重新从 1 开始规整排列，文件保存在第 1 个文件的相同文件夹中。"
        )
        self.p3_description_label.setStyleSheet("color: #94a3b8; line-height: 1.6; font-size: 12px; background: #020617; padding: 12px; border-radius: 8px; border: 1px solid #1e293b;")
        self.p3_description_label.setWordWrap(True)
        self.p3_scroll_layout.addWidget(self.p3_description_label)

        p3_scroll.setWidget(p3_container)
        page3_root_layout = QVBoxLayout(self.page3)
        page3_root_layout.setContentsMargins(0, 0, 0, 0)
        page3_root_layout.addWidget(p3_scroll)

    def adjust_p3_block_count(self, target_count):
        """ 动态伸缩区块数量的核心控制层 """
        current_count = len(self.p3_files)
        if current_count < target_count:
            # 补足短缺的区块数量
            for i in range(current_count, target_count):
                self.p3_files.append("")
                
                box_frame = QFrame()
                box_frame.setObjectName("CardFrame")
                box_layout = QVBoxLayout(box_frame)
                box_layout.setContentsMargins(12, 12, 12, 12)
                box_layout.setSpacing(8)

                # 动态自增标号（从 数据报表文件区块 1 开始递增）
                lbl_title = QLabel(f"📦 数据报表文件区块 {i+1}")
                lbl_title.setStyleSheet("font-weight: bold; color: #a78bfa;")
                box_layout.addWidget(lbl_title)

                hb1 = QHBoxLayout()
                drop_lbl = QLabel(f"❌ 拖入或单击此处选择第 {i+1} 份表格文件...")
                drop_lbl.setObjectName("DropZoneClickable")
                drop_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
                drop_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                drop_lbl.setMinimumHeight(50)
                drop_lbl.mousePressEvent = lambda e, idx=i: self.browse_p3_file(idx)
                
                hb1.addWidget(drop_lbl)
                box_layout.addLayout(hb1)

                hb2 = QHBoxLayout()
                hb2.addWidget(QLabel("输入提取范围 (留空则默认按已查验提取):"))
                range_input = QLineEdit()
                range_input.setPlaceholderText("例如: 1-50, 88, 120-150")
                hb2.addWidget(range_input)
                box_layout.addLayout(hb2)

                self.blocks_layout.addWidget(box_frame)
                
                self.p3_frames.append(box_frame)
                self.p3_labels.append(drop_lbl)
                self.p3_inputs.append(range_input)
                
        elif current_count > target_count:
            # 裁剪多余的区块数量
            for i in range(current_count - 1, target_count - 1, -1):
                frame_to_remove = self.p3_frames.pop()
                self.blocks_layout.removeWidget(frame_to_remove)
                frame_to_remove.deleteLater()
                
                self.p3_files.pop()
                self.p3_labels.pop()
                self.p3_inputs.pop()

    def set_p3_file_path(self, idx, file_path):
        """ 将提取到的全路径格式化绑定到对应的独立区块 UI 视图中 """
        full_clean_path = os.path.abspath(file_path.strip().strip('"').strip("'"))
        self.p3_files[idx] = full_clean_path
        short_display = get_short_path_display(full_clean_path)
        self.p3_labels[idx].setText(f"🟢 载入文件：{short_display}")
        self.p3_labels[idx].setStyleSheet("color: #34d399; border-color: #34d399; background-color: #020617; text-align: left; font-size: 13px;")

    def browse_p3_file(self, idx):
        file_path, _ = QFileDialog.getOpenFileName(self, f"选择第 {idx+1} 份数据报表", "", "HTML/Text Files (*.html *.htm *.txt);;All files (*.*)")
        if file_path:
            self.set_p3_file_path(idx, file_path)

    # 🎯 需求 9：点击清除重置按钮后，清除全部路径与人工序号，一切恢复为 2 个区块
    def reset_page3_fields(self):
        self.adjust_p3_block_count(2)  # 先恢复为2个基础块
        self.p3_files = ["", ""]
        for i, lbl in enumerate(self.p3_labels):
            lbl.setText(f"❌ 拖入或单击此处选择第 {i+1} 份表格文件...")
            lbl.setStyleSheet("color: #38bdf8; background-color: #020617; border-color: #3b82f6;")
        for inp in self.p3_inputs:
            inp.clear()
        self.p3_cfg_url_input.setText("https://substack.com/@样本/subscribers")
        self.p3_cfg_author_input.setText("某人")
        self.p3_cfg_date_input.setText(datetime.now().strftime("%Y年%m月%d日"))

    # ==============================================================================
    #  【基础框架拦截】拖放与基础关闭
    # ==============================================================================
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        self.pressed_keys[event.key()] = True
        if self.pressed_keys.get(Qt.Key.Key_Escape) and self.pressed_keys.get(Qt.Key.Key_0):
            self.close()
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        self.pressed_keys[event.key()] = False
        super().keyReleaseEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if not urls: return
        
        current_tab_idx = self.tabs.currentIndex()
        if current_tab_idx == 0:
            local_path = urls[0].toLocalFile()
            if os.path.isfile(local_path):
                self.set_source_file_path(local_path)
        elif current_tab_idx == 1:
            local_path = urls[0].toLocalFile()
            if os.path.isfile(local_path):
                self.load_writer_table_path(local_path)
                
        # 🎯 需求 6 & 7 & 8：第三页全局盲拖、多级文件夹深度扫描及动态扩容匹配算法
        elif current_tab_idx == 2:
            extracted_files = []
            
            # 遍历所有拖入的项进行深层文件夹扫描或单文件捕获
            for url in urls:
                item_path = os.path.abspath(url.toLocalFile())
                if not os.path.exists(item_path):
                    continue
                
                # 🎯 需求 8：如果用户拖入一个文件夹，就自动识别这个文件夹以及包含子文件夹下的所有htm html txt
                if os.path.isdir(item_path):
                    for root, dirs, files in os.walk(item_path):
                        for file in files:
                            if file.lower().endswith(('.html', '.htm', '.txt')):
                                extracted_files.append(os.path.join(root, file))
                else:
                    if item_path.lower().endswith(('.html', '.htm', '.txt')):
                        extracted_files.append(item_path)

            if not extracted_files:
                return

            # 🎯 需求 6 & 7：优先寻找当前空置槽位填入，如果槽位不够，自动扩增匹配
            for file_path in extracted_files:
                filled = False
                # 优先检测填补空位
                for idx, path in enumerate(self.p3_files):
                    if not path:
                        self.set_p3_file_path(idx, file_path)
                        filled = True
                        break
                
                # 槽位不够了，动态新增一个区块承载该文件
                if not filled:
                    new_idx = len(self.p3_files)
                    self.adjust_p3_block_count(new_idx + 1)
                    self.set_p3_file_path(new_idx, file_path)

    # ==============================================================================
    #  选项卡1：离线数据提取核心逻辑
    # ==============================================================================
    def browse_source_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择原始网页", "", "Substack HTML Files (*.html *.htm);;All files (*.*)")
        if file_path: self.set_source_file_path(file_path)

    def set_source_file_path(self, file_path):
        self.selected_file_path = os.path.abspath(file_path.strip().strip('"').strip("'"))
        short_display = get_short_path_display(self.selected_file_path)
        self.p1_drop_label.setText(f"🟢 已成功抓取源网页：{short_display}")
        self.p1_drop_label.setStyleSheet("color: #10b981; border-color: #10b981; background-color: #020617; font-size: 13px;")
        self.btn_start_ex.setEnabled(True)

    def copy_local_image(self, src_path_url, target_folder, new_filename):
        if not src_path_url or not src_path_url.strip() or src_path_url.startswith(("http://", "https://")):
            return ""
        try:
            clean_url = urlparse(src_path_url).path
            relative_src_path = unquote(clean_url)
            base_dir = os.path.dirname(self.selected_file_path)
            full_src_path = os.path.abspath(os.path.join(base_dir, relative_src_path))
            if os.path.exists(full_src_path) and os.path.isfile(full_src_path):
                _, ext = os.path.splitext(full_src_path)
                if not ext: ext = ".jpg"
                final_filename = f"{new_filename}{ext}"
                full_target_path = os.path.join(target_folder, final_filename)
                shutil.copy2(full_src_path, full_target_path)
                
                folder_name = os.path.basename(target_folder)
                return f"./{folder_name}/{final_filename}"
        except Exception:
            pass
        return ""

    def execute_extraction(self):
        source_url = self.cfg_url_input.text().strip()
        author_name = self.cfg_author_input.text().strip()
        record_date = self.cfg_date_input.text().strip()

        if not self.selected_file_path or not os.path.exists(self.selected_file_path):
            self.show_message("错误", "未找到选择的源网页文件！")
            return

        try:
            with open(self.selected_file_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, "html.parser")
            user_cards = soup.find_all("div", class_="personYouMayKnow-g7Alxo")
            total_num = len(user_cards)

            if total_num == 0:
                self.show_message("匹配失败", "在源网页中未发现合法的订阅者卡片数据，请确保证件源无误。")
                return

            time_stamp = time.strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.dirname(self.selected_file_path)
            
            img_dir_name = f"tou_xiang_{time_stamp}"
            img_dir = os.path.join(output_dir, img_dir_name) 
            os.makedirs(img_dir, exist_ok=True)

            subscribers_list = []
            serial_num = 1
            sub_avatar_count = 0

            for card in user_cards:
                avatar_url = ""
                img_tag = card.find("img", class_=re.compile("avatar", re.I))
                if not img_tag: img_tag = card.find("img", alt=re.compile(r"avatar|profile", re.I))
                if not img_tag: img_tag = card.find("img")
                if img_tag: avatar_url = img_tag.get("src", "")

                local_avatar = self.copy_local_image(avatar_url, img_dir, f"user_{serial_num}_avatar")

                sub_avatar_url = ""
                badge_box = card.find("div", class_="badge-jGMz0j")
                if badge_box:
                    sub_img = badge_box.find("img")
                    if sub_img: sub_avatar_url = sub_img.get("src", "")

                local_sub_avatar = ""
                if sub_avatar_url:
                    local_sub_avatar = self.copy_local_image(sub_avatar_url, img_dir, f"sub_{serial_num}_avatar")
                    if local_sub_avatar: sub_avatar_count += 1

                name_a = card.find("a", class_="link-LIBpto")
                username = name_a.get_text(strip=True) if name_a else "未知用户"
                profile_url = name_a["href"] if name_a and name_a.has_attr("href") else ""

                desc_tag = card.find("a", {"data-native": "true"})
                intro_text = desc_tag.get_text(strip=True) if desc_tag else ""
                sub_url = desc_tag["href"] if desc_tag and desc_tag.has_attr("href") else ""

                subscribers_list.append({
                    "serial": serial_num,
                    "avatar": local_avatar or avatar_url,
                    "sub_avatar": local_sub_avatar or sub_avatar_url,
                    "username": username,
                    "profile_url": profile_url,
                    "intro": intro_text,
                    "substack_url": sub_url,
                    "remark": "[备注占位]",
                    "status": "未查验"
                })
                serial_num += 1

            rows_html = ""
            for item in subscribers_list:
                avatar_html = f'<img class="avatar-img" src="{item["avatar"]}" alt="用户头像">' if item["avatar"] else "无头像"
                sub_avatar_html = f'<img class="sub-avatar-img" src="{item["sub_avatar"]}" alt="专栏头像">' if item["sub_avatar"] else ""
                name_link = f'<a target="_blank" href="{item["profile_url"]}">{item["username"]}</a>' if item["profile_url"] else item["username"]
                intro_link = f'<a target="_blank" href="{item["substack_url"]}">{item["intro"]}</a>' if item["intro"] else ""
                
                rows_html += f"""
                <tr>
                    <td class="center-col">{item["serial"]}</td>
                    <td class="center-col">{avatar_html}</td>
                    <td>{name_link}</td>
                    <td class="center-col">{sub_avatar_html}</td>
                    <td>{intro_link}</td>
                    <td class="center-col selfie-col">未上传</td>
                    <td class="center-col keyurl-col"></td>
                    <td class="remark-col">{item["remark"]}</td>
                    <td class="center-col status-col"><span class="status-badge status-unverified">{item["status"]}</span></td>
                </tr>"""

            html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>订阅名单</title>
    <style>
        table {{ border-collapse: collapse; width: 100%; margin: 30px auto; }}
        th, td {{ border: 1px #cccccc solid; padding: 12px; text-align: left; }}
        th {{ background-color: #f3f3f5; }}
        .center-col {{ text-align: center; vertical-align: middle; }}
        .avatar-img, .sub-avatar-img, .selfie-img {{ width: 40px; height: 40px; border-radius: 50%; object-fit: cover; display: inline-block; vertical-align: middle; }}
        
        .selfie-img {{ cursor: pointer; transition: transform 0.2s, border-radius 0.2s; }}
        .selfie-img:hover {{ transform: scale(1.1); }}
        
        .selfie-img.zoomed-in {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) scale(1.0);
            width: auto;
            height: auto;
            max-width: 85vw;
            max-height: 85vh;
            border-radius: 12px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            z-index: 99999;
            object-fit: contain;
            animation: fadeInImg 0.15s ease-out;
        }}

        @keyframes fadeInImg {{
            from {{ opacity: 0; transform: translate(-50%, -50%) scale(0.95); }}
            to {{ opacity: 1; transform: translate(-50%, -50%) scale(1.0); }}
        }}
        
        .lightbox-overlay {{
            display: none;
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: transparent;
            z-index: 99998;
            cursor: pointer;
        }}

        a {{ color: #0066dd; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        h2 {{ text-align: center; margin-top: 30px; }}
        .count-tip {{ text-align: center; font-size: 17px; font-weight: normal; margin: 12px 0; color: #333333; }}
        .highlight-num-red {{ color: #e11d48; font-weight: 900; font-size: 20px; }}
        .highlight-num-green {{ color: #059669; font-weight: 900; font-size: 20px; }}
        .source-info {{ text-align: center; font-size: 15px; margin: 10px 0 30px; color: #666666; }}
        td.remark-col {{ min-width: 300px; vertical-align: top; white-space: pre-wrap; word-wrap: break-word; line-height: 1.6; }}
        
        .status-badge {{ padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 12px; }}
        .status-unverified {{ background-color: #fee2e2; color: #ef4444; }}
        .status-verified {{ background-color: #d1fae5; color: #10b981; }}
    </style>
</head>
<body>
    <div id="LightboxOverlay" class="lightbox-overlay" onclick="closeAllZoomedImages()"></div>

    <h2>Substack 订阅名单数据报表</h2>
    <div class="count-tip">📊 提取总人数：<span class="highlight-num-red">{total_num}</span> 人 &nbsp;&nbsp;|&nbsp;&nbsp; 拥有专属独立专栏：<span class="highlight-num-green">{sub_avatar_count}</span> 人</div>
    <div class="source-info">
        🔗 数据源源自于：<a href="{source_url}" target="_blank">{source_url}</a>
      &nbsp;&nbsp;|&nbsp;&nbsp;   👨‍💻 博主：{author_name} &nbsp;&nbsp;|&nbsp;&nbsp; 📅 数据下载日期：{record_date}
    </div>
    <table>
        <thead>
            <tr>
                <th style="width: 60px; text-align: center;">序号</th>
                <th style="width: 90px; text-align: center;">用户头像</th>
                <th>昵称/姓名</th>
                <th style="width: 90px; text-align: center;">专栏头像</th>
                <th>专栏备注/简介</th>
                <th style="width: 90px; text-align: center;">自拍照</th>
                <th>关键网址</th>
                <th>自定义备注介绍</th>
                <th style="width: 100px; text-align: center;">是否查验</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>

    <script>
        function toggleZoomImage(imgElement) {{
            const overlay = document.getElementById('LightboxOverlay');
            if (imgElement.classList.contains('zoomed-in')) {{
                imgElement.classList.remove('zoomed-in');
                overlay.style.display = 'none';
            }} else {{
                closeAllZoomedImages();
                imgElement.classList.add('zoomed-in');
                overlay.style.display = 'block';
            }}
        }}

        function closeAllZoomedImages() {{
            const activeZooms = document.querySelectorAll('.selfie-img.zoomed-in');
            activeZooms.forEach(el => el.classList.remove('zoomed-in'));
            document.getElementById('LightboxOverlay').style.display = 'none';
        }}
    </script>
</body>
</html>"""

            output_html = html_template.format(
                total_num=total_num, sub_avatar_count=sub_avatar_count,
                source_url=source_url, author_name=author_name, record_date=record_date,
                table_rows=rows_html
            )

            output_path = os.path.join(output_dir, f"订阅者表格_{time_stamp}.html")
            with open(output_path, "w", encoding="utf-8") as out:
                out.write(output_html)

            self.show_message("完成", f"提取完毕！\n\n总人数: {total_num} 人\n专栏人数: {sub_avatar_count} 人\n\n新资源包: {img_dir_name}\n文件已存至:\n{output_path}")

        except Exception as e:
            self.show_message("异常", f"执行异常：{str(e)}")

    # ==============================================================================
    #  选项卡2：数据回刷与修改逻辑
    # ==============================================================================
    def browse_writer_table_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "加载数据报表网页", "", "HTML Data Table (*.html *.htm);;All files (*.*)")
        if file_path: self.load_writer_table_path(file_path)

    def load_writer_table_path(self, file_path):
        try:
            self.loaded_html_path = os.path.abspath(file_path.strip().strip('"').strip("'"))
            if not os.path.exists(self.loaded_html_path): return

            with open(self.loaded_html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            self.soup_writer = BeautifulSoup(html_content, "html.parser")
            if not self.soup_writer.find("tbody"):
                self.show_message("错误", "格式不正确，未发现表格 tbody 数据体。")
                return
            
            short_display = get_short_path_display(self.loaded_html_path)
            self.p2_drop_label.setText(f"🟢 数据源就绪：{short_display}")
            self.p2_drop_label.setStyleSheet("color: #34d399; border-color: #34d399; background-color: #020617; font-size: 13px;")
            
            self.btn_view_browser.setEnabled(True)
            self.serial_input.setEnabled(True)
            self.btn_query.setEnabled(True)
            self.serial_input.setFocus()
        except Exception as e:
            self.show_message("失败", f"网页解析失败：{str(e)}")

    def open_current_table_in_browser(self):
        if not self.loaded_html_path or not os.path.exists(self.loaded_html_path):
            return
        try:
            success = webbrowser.open(f"file:///{os.path.abspath(self.loaded_html_path)}")
            if not success: raise RuntimeError()
        except Exception:
            self.show_message("提示", f"调取默认浏览器失败，请自行双击该文件查看：\n\n{self.loaded_html_path}")

    def query_subscriber_by_id(self):
        if not self.soup_writer: return
        serial_id = self.serial_input.text().strip()
        if not serial_id: return

        table_rows = self.soup_writer.find("tbody").find_all("tr") if self.soup_writer.find("tbody") else []
        found = False

        for tr in table_rows:
            tds = tr.find_all("td")
            if not tds: continue
            if tds[0].get_text(strip=True) == serial_id:
                self.target_tr = tr
                self.current_serial_id = serial_id
                found = True
                
                username = tds[2].get_text(strip=True)
                intro = tds[4].get_text(strip=True)
                if not intro: intro = "（此用户无专栏介绍）"
                
                key_url_a = tds[6].find("a")
                current_key_url = key_url_a["href"] if key_url_a and key_url_a.has_attr("href") else tds[6].get_text(strip=True)
                
                current_remark_raw = ""
                if tds[7].contents:
                    content_strs = []
                    for element in tds[7].contents:
                        if element.name == 'br':
                            content_strs.append('\n')
                        else:
                            content_strs.append(element.get_text() if hasattr(element, 'get_text') else str(element))
                    current_remark_raw = "".join(content_strs)
                else:
                    current_remark_raw = tds[7].get_text()

                if current_remark_raw == "[备注占位]": current_remark_raw = ""

                has_verified = False
                if len(tds) >= 9:
                    status_text = tds[8].get_text(strip=True)
                    if "已查验" in status_text: has_verified = True

                name_a = tds[2].find("a")
                intro_a = tds[4].find("a")
                self.link_profile = name_a["href"] if name_a and name_a.has_attr("href") else ""
                self.link_substack = intro_a["href"] if intro_a and intro_a.has_attr("href") else ""
                
                self.res_name_label.setText(f"🔗 {username} (个人主页)")
                self.res_intro_label.setText(f"🔗 {intro[:25]}..." if len(intro)>25 else intro)
                
                if tds[5].find("img"):
                    self.res_selfie_badge.setText("🖼️ 已上传自拍照")
                    self.res_selfie_badge.setStyleSheet("background: #065f46; color: #34d399; padding: 4px 12px; border-radius: 10px; font-weight: bold;")
                else:
                    self.res_selfie_badge.setText("暂无图片")
                    self.res_selfie_badge.setStyleSheet("background: #7f1d1d; color: #fca5a5; padding: 4px 12px; border-radius: 10px; font-weight: bold;")

                self.key_url_input.setText(current_key_url)
                self.remark_textarea.setPlainText(current_remark_raw)
                self.check_verify.setChecked(has_verified)

                self.btn_upload_selfie.setEnabled(True)
                self.key_url_input.setEnabled(True)
                self.btn_save_url.setEnabled(True)
                self.remark_textarea.setEnabled(True)
                self.btn_save_remark.setEnabled(True)
                self.btn_save_next.setEnabled(True)  # 加上这行
                self.check_verify.setEnabled(True)
                break

        if not found:
            self.show_message("未找到", f"未在表格中寻找序号为【{serial_id}】的订阅者")
            self.clear_sub_fields()

    def clear_sub_fields(self):
        self.res_name_label.setText("（等待加载）")
        self.res_intro_label.setText("（等待加载）")
        self.res_selfie_badge.setText("暂无图片")
        self.res_selfie_badge.setStyleSheet("background: #7f1d1d; color: #fca5a5; padding: 4px 12px; border-radius: 10px;")
        self.key_url_input.clear()
        self.remark_textarea.clear()
        self.check_verify.setChecked(False)
        self.btn_upload_selfie.setEnabled(False)
        self.key_url_input.setEnabled(False)
        self.btn_save_url.setEnabled(False)
        self.remark_textarea.setEnabled(False)
        self.btn_save_remark.setEnabled(False)
        self.btn_save_next.setEnabled(False)  # 加上这行
        self.check_verify.setEnabled(False)

    def submit_key_url_data(self):
        if not self.target_tr or not self.loaded_html_path: return
        new_url = self.key_url_input.text().strip()
        try:
            tds = self.target_tr.find_all("td")
            if len(tds) >= 7:
                if new_url:
                    new_soup_a = self.soup_writer.new_tag("a", href=new_url, target="_blank")
                    new_soup_a.string = "关键网址" 
                    tds[6].string = ""
                    tds[6].append(new_soup_a)
                else:
                    tds[6].string = ""

                with open(self.loaded_html_path, "w", encoding="utf-8") as f:
                    f.write(str(self.soup_writer))
                self.show_message("成功", f"关键网址修改并同步成功！")
        except Exception as e:
            self.show_message("失败", f"保存失败：{str(e)}")

    def submit_remark_data(self):
        if not self.target_tr or not self.loaded_html_path: return
        new_remark_raw = self.remark_textarea.toPlainText()
        is_checked = self.check_verify.isChecked()
        try:
            tds = self.target_tr.find_all("td")
            if len(tds) >= 8:
                tds[7].string = "" 
                if new_remark_raw.strip():
                    lines = new_remark_raw.split('\n')
                    for i, line in enumerate(lines):
                        if i > 0: tds[7].append(self.soup_writer.new_tag("br"))
                        if line: tds[7].append(line)
                else:
                    tds[7].string = "[备注占位]"

                if len(tds) >= 9:
                    tds[8].string = ""
                    new_span = self.soup_writer.new_tag("span")
                    if is_checked:
                        new_span['class'] = "status-badge status-verified"
                        new_span.string = "已查验"
                    else:
                        new_span['class'] = "status-badge status-unverified"
                        new_span.string = "未查验"
                    tds[8].append(new_span)

                with open(self.loaded_html_path, "w", encoding="utf-8") as f:
                    f.write(str(self.soup_writer))
                self.show_message("成功", f"数据回刷并保存成功！")
                self.serial_input.setFocus()
                self.serial_input.selectAll()
        except Exception as e:
            self.show_message("失败", f"保存失败：{str(e)}")
            
            
    def save_and_query_next_subscriber(self):
            """ 保存当前数据，自动对序号+1并提取下一位订阅者信息 """
            # 1. 首先执行现有的保存逻辑
            # 注意：这里我们直接调用你原有的保存方法
            self.submit_remark_data()
            
            # 2. 获取当前文本框中的序号
            current_id_str = self.serial_input.text().strip()
            if not current_id_str:
                return
                
            try:
                # 3. 序号自动 +1
                next_id = int(current_id_str) + 1
                
                # 4. 回写到输入框中
                self.serial_input.setText(str(next_id))
                
                # 5. 自动触发查询下一位数据的逻辑
                self.query_subscriber_by_id()
                
            except ValueError:
                # 如果输入的不是纯数字（比如带字母），则无法+1，弹窗提示
                self.show_message("序号错误", "当前序号不是有效数字，无法自动递增跳转！", is_error=True)
            

    def upload_selfie_image(self):
        if not self.target_tr or not self.loaded_html_path: return
        default_dir = os.path.dirname(self.loaded_html_path)
        
        fp, _ = QFileDialog.getOpenFileName(
            self, "选择自拍照", default_dir, 
            "Image Files (*.jpg *.jpeg *.png *.webp *.gif);;All files (*.*)"
        )
        if not fp: return
        try:
            base_dir = os.path.dirname(self.loaded_html_path)
            tds = self.target_tr.find_all("td")
            folder_name = "tou_xiang"
            if len(tds) >= 2 and tds[1].find("img"):
                orig_src = tds[1].find("img").get("src", "")
                parsed_path = urlparse(orig_src).path
                path_parts = [p for p in parsed_path.split('/') if p]
                if len(path_parts) >= 2: folder_name = path_parts[-2]
                    
            img_dir = os.path.join(base_dir, folder_name)
            os.makedirs(img_dir, exist_ok=True)

            _, ext = os.path.splitext(fp)
            new_filename = f"selfie_{self.current_serial_id}{ext}"
            target_path = os.path.join(img_dir, new_filename)
            shutil.copy2(fp, target_path)

            relative_img_path = f"./{folder_name}/{new_filename}" 
            new_img_tag = self.soup_writer.new_tag("img", src=relative_img_path, alt="自拍照")
            new_img_tag['class'] = "selfie-img"
            new_img_tag['onclick'] = "toggleZoomImage(this)"

            tds[5].string = ""
            tds[5].append(new_img_tag)

            with open(self.loaded_html_path, "w", encoding="utf-8") as f:
                f.write(str(self.soup_writer))

            self.show_message("成功", "照片挂载成功！")
            self.query_subscriber_by_id() 
        except Exception as e:
            self.show_message("失败", f"挂载照片故障：{str(e)}")

    def open_link(self, type_idx):
        url = self.link_profile if type_idx == 1 else self.link_substack
        if url:
            try: webbrowser.open(url)
            except Exception: pass

    def show_about_dialog(self):
        dlg = AboutLinkDialog(self)
        dlg.exec()

    def parse_range_string(self, range_str):
        if not range_str or not range_str.strip(): return None
        target_set = set()
        clean_str = range_str.replace("，", ",").strip()
        parts = clean_str.split(",")
        for part in parts:
            part = part.strip()
            if not part: continue
            if "-" in part:
                sub_parts = part.split("-")
                if len(sub_parts) == 2:
                    try:
                        start = int(sub_parts[0].strip())
                        end = int(sub_parts[1].strip())
                        for n in range(min(start, end), max(start, end) + 1): target_set.add(n)
                    except ValueError: pass
            else:
                try: target_set.add(int(part))
                except ValueError: pass
        return target_set

    # ==============================================================================
    #  选项卡3：多表融合重构生成新报表
    # ==============================================================================
    def execute_merge_logic(self):
        valid_paths = [p for p in self.p3_files if p and os.path.exists(p)]
        if not valid_paths:
            self.show_message("合并失败", "最少需要添加 1 份有效的数据报表文件！", is_error=True)
            return

        try:
            # 读取第三页独立表格配置参数
            source_url = self.p3_cfg_url_input.text().strip()
            author_name = self.p3_cfg_author_input.text().strip()
            record_date = self.p3_cfg_date_input.text().strip()

            time_stamp = time.strftime("%Y%m%d_%H%M%S")
            base_output_dir = os.path.dirname(valid_paths[0])
            
            merged_img_dir_name = f"he_bing_{time_stamp}"
            merged_img_dir_full = os.path.join(base_output_dir, merged_img_dir_name)
            os.makedirs(merged_img_dir_full, exist_ok=True)

            merged_rows_soup_list = []
            asset_counter = 1  

            for idx, path in enumerate(self.p3_files):
                if not path or not os.path.exists(path): continue
                
                with open(path, "r", encoding="utf-8") as f:
                    file_content = f.read()
                
                loop_soup = BeautifulSoup(file_content, "html.parser")
                tbody = loop_soup.find("tbody")
                if not tbody: continue
                
                rows = tbody.find_all("tr")
                range_text = self.p3_inputs[idx].text().strip()
                allowed_set = self.parse_range_string(range_text)
                file_base_dir = os.path.dirname(path)

                for tr in rows:
                    tds = tr.find_all("td")
                    if not tds or len(tds) < 8: continue
                    
                    try: current_sid = int(tds[0].get_text(strip=True))
                    except ValueError: continue

                    if allowed_set is not None:
                        if current_sid not in allowed_set: continue
                    else:
                        if len(tds) >= 9:
                            status_txt = tds[8].get_text(strip=True)
                            if "已查验" not in status_txt: continue
                        else: continue

                    cloned_tr = BeautifulSoup(str(tr), "html.parser").find("tr")
                    
                    img_tags = cloned_tr.find_all("img")
                    for img in img_tags:
                        src_val = img.get("src", "")
                        if src_val and not src_val.startswith(("http://", "https://")):
                            clean_url_path = urlparse(src_val).path
                            path_parts = [p for p in clean_url_path.split('/') if p]
                            
                            actual_src_img_path = ""
                            if len(path_parts) >= 2:
                                folder_part = path_parts[-2]
                                file_part = path_parts[-1]
                                actual_src_img_path = os.path.abspath(os.path.join(file_base_dir, folder_part, file_part))
                            
                            if not actual_src_img_path or not os.path.exists(actual_src_img_path):
                                actual_src_img_path = os.path.abspath(os.path.join(file_base_dir, os.path.basename(clean_url_path)))

                            if os.path.exists(actual_src_img_path) and os.path.isfile(actual_src_img_path):
                                _, ext = os.path.splitext(os.path.basename(actual_src_img_path))
                                if not ext: ext = ".jpg"
                                
                                unique_img_name = f"merge_asset_{asset_counter}{ext}"
                                target_img_path = os.path.join(merged_img_dir_full, unique_img_name)
                                
                                shutil.copy2(actual_src_img_path, target_img_path)
                                asset_counter += 1
                                
                                img["src"] = f"./{merged_img_dir_name}/{unique_img_name}"
                    
                    merged_rows_soup_list.append(cloned_tr)

            if not merged_rows_soup_list:
                self.show_message("合并提示", "未找到符合筛选范围或已查验的数据，未生成新表格。")
                return

            final_rows_html = ""
            for new_id, tr_soup in enumerate(merged_rows_soup_list, start=1):
                tds = tr_soup.find_all("td")
                tds[0].string = str(new_id)
                final_rows_html += str(tr_soup) + "\n"

            final_total_num = len(merged_rows_soup_list)
            
            final_sub_count = 0
            for r in merged_rows_soup_list:
                t_tds = r.find_all("td")
                if len(t_tds) >= 4 and t_tds[3].find("img"): final_sub_count += 1

            merge_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>合并提纯订阅名单</title>
    <style>
        table {{ border-collapse: collapse; width: 100%; margin: 30px auto; }}
        th, td {{ border: 1px #cccccc solid; padding: 12px; text-align: left; }}
        th {{ background-color: #f3f3f5; }}
        .center-col {{ text-align: center; vertical-align: middle; }}
        .avatar-img, .sub-avatar-img, .selfie-img {{ width: 40px; height: 40px; border-radius: 50%; object-fit: cover; display: inline-block; vertical-align: middle; }}
        
        .selfie-img {{ cursor: pointer; transition: transform 0.2s, border-radius 0.2s; }}
        .selfie-img:hover {{ transform: scale(1.1); }}
        
        .selfie-img.zoomed-in {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) scale(1.0);
            width: auto;
            height: auto;
            max-width: 85vw;
            max-height: 85vh;
            border-radius: 12px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            z-index: 99999;
            object-fit: contain;
            animation: fadeInImg 0.15s ease-out;
        }}

        @keyframes fadeInImg {{
            from {{ opacity: 0; transform: translate(-50%, -50%) scale(0.95); }}
            to {{ opacity: 1; transform: translate(-50%, -50%) scale(1.0); }}
        }}
        
        .lightbox-overlay {{
            display: none;
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: transparent;
            z-index: 99998;
            cursor: pointer;
        }}

        a {{ color: #0066dd; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        h2 {{ text-align: center; margin-top: 30px; }}
        .count-tip {{ text-align: center; font-size: 17px; font-weight: normal; margin: 12px 0; color: #333333; }}
        .highlight-num-red {{ color: #e11d48; font-weight: 900; font-size: 20px; }}
        .highlight-num-green {{ color: #059669; font-weight: 900; font-size: 20px; }}
        .source-info {{ text-align: center; font-size: 15px; margin: 10px 0 30px; color: #666666; }}
        td.remark-col {{ min-width: 300px; vertical-align: top; white-space: pre-wrap; word-wrap: break-word; line-height: 1.6; }}
        
        .status-badge {{ padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 12px; }}
        .status-unverified {{ background-color: #fee2e2; color: #ef4444; }}
        .status-verified {{ background-color: #d1fae5; color: #10b981; }}
    </style>
</head>
<body>
    <div id="LightboxOverlay" class="lightbox-overlay" onclick="closeAllZoomedImages()"></div>

    <h2>Substack 提纯合并订阅名单大报表</h2>
    <div class="count-tip">📊 融合筛选总人数：<span class="highlight-num-red">{final_total_num}</span> 人 &nbsp;&nbsp;|&nbsp;&nbsp; 拥有专属独立专栏：<span class="highlight-num-green">{final_sub_count}</span> 人</div>
    <div class="source-info">
        🔗 数据源源自于：<a href="{source_url}" target="_blank">{source_url}</a><br>
        👨‍💻 博主：{author_name} &nbsp;&nbsp;|&nbsp;&nbsp; 📅 融合构建日期：{record_date}
    </div>
    <table>
        <thead>
            <tr>
                <th style="width: 60px; text-align: center;">序号</th>
                <th style="width: 90px; text-align: center;">用户头像</th>
                <th>昵称/姓名</th>
                <th style="width: 90px; text-align: center;">专栏头像</th>
                <th>专栏备注/简介</th>
                <th style="width: 90px; text-align: center;">自拍照</th>
                <th>关键网址</th>
                <th>自定义备注介绍</th>
                <th style="width: 100px; text-align: center;">是否查验</th>
            </tr>
        </thead>
        <tbody>
            {final_rows_html}
        </tbody>
    </table>

    <script>
        function toggleZoomImage(imgElement) {{
            const overlay = document.getElementById('LightboxOverlay');
            if (imgElement.classList.contains('zoomed-in')) {{
                imgElement.classList.remove('zoomed-in');
                overlay.style.display = 'none';
            }} else {{
                closeAllZoomedImages();
                imgElement.classList.add('zoomed-in');
                overlay.style.display = 'block';
            }}
        }}

        function closeAllZoomedImages() {{
            const activeZooms = document.querySelectorAll('.selfie-img.zoomed-in');
            activeZooms.forEach(el => el.classList.remove('zoomed-in'));
            document.getElementById('LightboxOverlay').style.display = 'none';
        }}
    </script>
</body>
</html>"""

            output_merged_path = os.path.join(base_output_dir, f"合并_订阅者名单_{time_stamp}.html")
            with open(output_merged_path, "w", encoding="utf-8") as out_m:
                out_m.write(merge_template)

            self.show_message("合并完成", f"恭喜，多表融合提纯成功！\n\n新合并资产包：{merged_img_dir_name}\n筛选融合总人数: {final_total_num} 人\n合并文件已存至:\n{output_merged_path}")

        except Exception as e:
            self.show_message("融合故障", f"合并逻辑执行异常：{str(e)}", is_error=True)


# ==============================================================================
#  【Windows 内存原子锁】确保进程全局唯一
# ==============================================================================
if __name__ == "__main__":
    if sys.platform.startswith("win"):
        # 📢 1. 强行通知 Windows 这是一个独立应用，确保无边框模式下任务栏依然独立绘制图标
        import ctypes
        myappid = 'hujiasanshao.lucis.substacktool.1.0'  # 你的专属独立应用ID描述
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        # 🔒 2. 你原有的原子锁逻辑（保持不变）
        UNIQUE_MUTEX_NAME = "101_Lucis_Sub_Substack_91TV.VIP"
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, UNIQUE_MUTEX_NAME)
        last_error = kernel32.GetLastError()
        
        if last_error == 183:
            ctypes.windll.user32.MessageBoxW(
                0, "检测到程序已在后台运行中，请不要重复启动程序！", "启动被拦截", 0x00000010 | 0x00000000  
            )
            sys.exit(0)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
