from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QStackedWidget, 
                             QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QFrame, QSizePolicy)
from PyQt5.QtGui import QIcon, QPainter, QMovie, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat
from PyQt5.QtCore import Qt, QSize, QTimer
from dotenv import dotenv_values
import sys
import os

# Environment and global variables setup
env_vars = dotenv_values(".env")
Assistantname = "Jarvis"  # or use env_vars.get("Assistantname")
current_dir = os.getcwd()
TempDirPath = os.path.join(current_dir, "Files")
GraphicsDirPath = os.path.join(current_dir, "Graphics")

# Ensure the required directories exist
os.makedirs(TempDirPath, exist_ok=True)
os.makedirs(GraphicsDirPath, exist_ok=True)

old_chat_message = ""

# Utility functions
def AnswerModifier(answer):
    lines = answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

def QueryModifier(query):
    new_query = query.lower().strip()
    query_words = new_query.split()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom",
                      "can you", "what's", "where's", "how's"]
    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."
    return new_query.capitalize()

def TempDirectoryPath(filename):
    return os.path.join(TempDirPath, filename)

def GraphicsDirectoryPath(filename):
    return os.path.join(GraphicsDirPath, filename)

def SetMicrophoneStatus(command):
    file_path = TempDirectoryPath('Mic.data')
    with open(file_path, "w", encoding='utf-8') as file:
        file.write(command)

def GetMicrophoneStatus():
    file_path = TempDirectoryPath('Mic.data')
    with open(file_path, "r", encoding='utf-8') as file:
        status = file.read()
    return status

def SetAssistantStatus(status):
    file_path = TempDirectoryPath('Status.data')
    with open(file_path, "w", encoding='utf-8') as file:
        file.write(status)

def GetAssistantStatus():
    file_path = TempDirectoryPath('Status.data')
    with open(file_path, "r", encoding='utf-8') as file:
        status = file.read()
    return status

def MicButtonInitialed():
    SetMicrophoneStatus("False")

def MicButtonClosed():
    SetMicrophoneStatus("True")

def ShowTextToScreen(text):
    file_path = TempDirectoryPath('Responses.data')
    with open(file_path, "w", encoding='utf-8') as file:
        file.write(text)

class ChatSection(QWidget):
    def __init__(self):
        super(ChatSection, self).__init__()
        # Set an object name for proper QSS targeting
        self.setObjectName("ChatSection")
        layout = QVBoxLayout(self)
        # Use layout margins (do not use negative CSS margins)
        layout.setContentsMargins(0, 40, 40, 100)
        layout.setSpacing(0)
        
        # Chat text edit setup
        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
        self.chat_text_edit.setFrameStyle(QFrame.NoFrame)
        layout.addWidget(self.chat_text_edit)
        
        # Apply stylesheet using a proper selector
        self.setStyleSheet("""
            #ChatSection {
                background-color: black;
            }
            QScrollBar:vertical {
                border: none;
                background: black;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: white;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: black;
                height: 10px;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        layout.setSizeConstraint(QVBoxLayout.SetDefaultConstraint)
        layout.setStretch(1, 1)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Set text color for the text edit
        text_color = QColor(Qt.blue)
        text_format = QTextCharFormat()
        text_format.setForeground(text_color)
        self.chat_text_edit.setCurrentCharFormat(text_format)
        
        # GIF setup
        self.gif_label = QLabel()
        self.gif_label.setStyleSheet("border: none;")
        jarvis_gif_path = GraphicsDirectoryPath('Jarvis.gif')
        movie = QMovie(jarvis_gif_path)
        if not movie.isValid():
            print("Warning: GIF file not found:", jarvis_gif_path)
        movie.setScaledSize(QSize(480, 270))
        self.gif_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.gif_label.setMovie(movie)
        movie.start()
        
        # Label setup (CSS now uses non-negative margins)
        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size: 16px; margin-right: 195px; border: none;")
        self.label.setAlignment(Qt.AlignRight)
        
        layout.addWidget(self.gif_label)
        layout.addWidget(self.label)
        
        # Set font for chat text edit
        font = QFont()
        font.setPointSize(13)
        self.chat_text_edit.setFont(font)
        
        # Timer setup (interval 100 ms)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(100)
        
        self.chat_text_edit.viewport().installEventFilter(self)

    def loadMessages(self):
        global old_chat_message
        file_path = TempDirectoryPath('Responses.data')
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                messages = file.read()
            if messages and messages != old_chat_message:
                self.addMessage(message=messages, color='White')
                old_chat_message = messages

    def SpeechRecogText(self):
        file_path = TempDirectoryPath('Status.data')
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                messages = file.read()
            self.label.setText(messages)

    def addMessage(self, message, color):
        cursor = self.chat_text_edit.textCursor()
        char_format = QTextCharFormat()
        block_format = QTextBlockFormat()
        block_format.setTopMargin(10)
        block_format.setLeftMargin(10)
        char_format.setForeground(QColor(color))
        cursor.setCharFormat(char_format)
        cursor.setBlockFormat(block_format)
        cursor.insertText(message + "\n")
        self.chat_text_edit.setTextCursor(cursor)

class InitialScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        
        # Layout setup
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # GIF setup
        gif_label = QLabel()
        jarvis_gif_path = GraphicsDirectoryPath('Jarvis.gif')
        movie = QMovie(jarvis_gif_path)
        if not movie.isValid():
            print("Warning: GIF file not found:", jarvis_gif_path)
        movie.setScaledSize(QSize(screen_width, int(screen_width / 16 * 9)))
        gif_label.setMovie(movie)
        gif_label.setAlignment(Qt.AlignCenter)
        movie.start()
        gif_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Icon setup
        self.icon_label = QLabel()
        mic_on_path = GraphicsDirectoryPath('Mic_on.png')
        pixmap = QPixmap(mic_on_path)
        if pixmap.isNull():
            print("Warning: Image file not found:", mic_on_path)
        new_pixmap = pixmap.scaled(60, 60)
        self.icon_label.setPixmap(new_pixmap)
        self.icon_label.setFixedSize(150, 150)
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        self.toggled = True
        self.toggle_icon()  # Set initial state and update mic status
        self.icon_label.mousePressEvent = self.toggle_icon
        
        # Label setup
        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size: 16px;")
        
        # Layout assembly
        content_layout.addWidget(gif_label, alignment=Qt.AlignCenter)
        content_layout.addWidget(self.label, alignment=Qt.AlignCenter)
        content_layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
        content_layout.setContentsMargins(0, 0, 0, 150)
        
        self.setLayout(content_layout)
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)
        self.setStyleSheet("background-color: black;")
        
        # Timer setup (interval 100 ms)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(100)

    def SpeechRecogText(self):
        file_path = TempDirectoryPath('Status.data')
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                messages = file.read()
            self.label.setText(messages)

    def load_icon(self, path, width=60, height=60):
        pixmap = QPixmap(path)
        if pixmap.isNull():
            print("Warning: Image file not found:", path)
        new_pixmap = pixmap.scaled(width, height)
        self.icon_label.setPixmap(new_pixmap)

    def toggle_icon(self, event=None):
        if self.toggled:
            self.load_icon(GraphicsDirectoryPath('Mic_on.png'), 60, 60)
            MicButtonInitialed()
        else:
            self.load_icon(GraphicsDirectoryPath('Mic_off.png'), 60, 60)
            MicButtonClosed()
        self.toggled = not self.toggled

class MessageScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        
        layout = QVBoxLayout()
        label = QLabel("")
        layout.addWidget(label)
        chat_section = ChatSection()
        layout.addWidget(chat_section)
        
        self.setLayout(layout)
        self.setStyleSheet("background-color: black;")
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)

class CustomTopBar(QWidget):
    def __init__(self, parent, stacked_widget):
        super().__init__(parent)
        self.current_screen = None
        self.stacked_widget = stacked_widget
        self.initUI()

    def initUI(self):
        self.setFixedHeight(50)
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignRight)
        
        # Button setup (using simple CSS properties)
        home_button = QPushButton()
        home_icon = QIcon(GraphicsDirectoryPath("Home.png"))
        home_button.setIcon(home_icon)
        home_button.setText(" Home")
        home_button.setStyleSheet("height:40px; background-color:white; color:black;")
        
        message_button = QPushButton()
        message_icon = QIcon(GraphicsDirectoryPath("Chats.png"))
        message_button.setIcon(message_icon)
        message_button.setText(" Chat")
        message_button.setStyleSheet("height:40px; background-color:white; color:black;")
        
        minimize_button = QPushButton()
        minimize_icon = QIcon(GraphicsDirectoryPath('Minimize2.png'))
        minimize_button.setIcon(minimize_icon)
        minimize_button.setStyleSheet("background-color:white;")
        minimize_button.clicked.connect(self.minimizeWindow)
        
        self.maximize_button = QPushButton()
        self.maximize_icon = QIcon(GraphicsDirectoryPath('Maximize.png'))
        self.restore_icon = QIcon(GraphicsDirectoryPath('Minimize.png'))
        self.maximize_button.setIcon(self.maximize_icon)
        self.maximize_button.setFlat(True)
        self.maximize_button.setStyleSheet("background-color:white;")
        self.maximize_button.clicked.connect(self.maximizeWindow)
        
        close_button = QPushButton()
        close_icon = QIcon(GraphicsDirectoryPath('Close.png'))
        close_button.setIcon(close_icon)
        close_button.setStyleSheet("background-color:white;")
        close_button.clicked.connect(self.closeWindow)
        
        # Line setup
        line_frame = QFrame()
        line_frame.setFixedHeight(1)
        line_frame.setFrameShape(QFrame.HLine)
        line_frame.setFrameShadow(QFrame.Sunken)
        line_frame.setStyleSheet("border-color: black;")
        
        # Title setup
        title_label = QLabel(f" {Assistantname} AI ")
        title_label.setStyleSheet("color: black; font-size: 18px; background-color:white;")
        
        # Button connections to switch screens
        home_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        message_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        layout.addWidget(title_label)
        layout.addStretch(1)
        layout.addWidget(home_button)
        layout.addWidget(message_button)
        layout.addStretch(1)
        layout.addWidget(minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(close_button)
        layout.addWidget(line_frame)
        
        self.draggable = True
        self.offset = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)
        super().paintEvent(event)

    def minimizeWindow(self):
        self.parent().showMinimized()

    def maximizeWindow(self):
        if self.parent().isMaximized():
            self.parent().showNormal()
            self.maximize_button.setIcon(self.maximize_icon)
        else:
            self.parent().showMaximized()
            self.maximize_button.setIcon(self.restore_icon)

    def closeWindow(self):
        self.parent().close()

    def mousePressEvent(self, event):
        if self.draggable:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.draggable and self.offset:
            new_pos = event.globalPos() - self.offset
            self.parent().move(new_pos)

    def showMessageScreen(self):
        if self.current_screen is not None:
            self.current_screen.hide()
        message_screen = MessageScreen(self)
        layout = self.parent().layout()
        if layout is not None:
            layout.addWidget(message_screen)
            self.current_screen = message_screen

    def showInitialScreen(self):
        if self.current_screen is not None:
            self.current_screen.hide()
        initial_screen = InitialScreen(self)
        layout = self.parent().layout()
        if layout is not None:
            layout.addWidget(initial_screen)
            self.current_screen = initial_screen

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.initUI()

    def initUI(self):
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        
        stacked_widget = QStackedWidget(self)
        initial_screen = InitialScreen()
        message_screen = MessageScreen()
        stacked_widget.addWidget(initial_screen)
        stacked_widget.addWidget(message_screen)
        
        self.setGeometry(0, 0, screen_width, screen_height)
        self.setStyleSheet("background-color: black;")
        
        top_bar = CustomTopBar(self, stacked_widget)
        self.setMenuWidget(top_bar)
        self.setCentralWidget(stacked_widget)

def GraphicalUserInterface():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    GraphicalUserInterface()
