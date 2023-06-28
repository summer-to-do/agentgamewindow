from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                               QWidget, QLineEdit, QPushButton, QTabWidget, QFileDialog,
                               QTextEdit, QSplitter, QListWidget, QListWidgetItem)
from PySide6.QtGui import QGuiApplication, QImageReader, QTextCursor
from PySide6.QtCore import Slot, Qt
from queue import Queue
from PySide6.QtCore import Qt, QUrl, QMimeData, QPointF, QRectF
from PySide6.QtGui import QClipboard, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtPrintSupport import QPrinter
import threading
import sys
import fitz  # PyMuPDF
from PySide6.QtGui import QPixmap, QImage,QPen

# class PdfViewer(QGraphicsView):
#     def __init__(self, parent=None):
#         super().__init__(parent)

#         self.doc = None
#         self.current_page = 0
#         self.pages_data = []
#         self.selection_rect = None

#         self.scene = QGraphicsScene(self)
#         self.setScene(self.scene)

#     def load_pdf(self, filename):
#         self.doc = fitz.open(filename)

#         self.pages_data = []
#         for i in range(len(self.doc)):
#             page = self.doc.load_page(i)
#             pix = page.get_pixmap()
#             img = QImage(pix.samples, pix.width, pix.height, QImage.Format_RGB888)
#             self.pages_data.append(img)

#         self.scene.clear()
#         self.show_page(self.current_page)

#         # 创建选择区域，宽度为页面宽度，高度为页面的1/10
#         page_width = self.pages_data[self.current_page].width()
#         page_height = self.pages_data[self.current_page].height()
#         rect_height = page_height / 10
#         pen = QPen(Qt.black)
#         pen.setWidth()
#         self.selection_rect = self.scene.addRect(0, 0, page_width*3, rect_height, QPen(Qt.black))

#     def mousePressEvent(self, event):
#         self.start_pos = event.pos()

#     def mouseMoveEvent(self, event):
#         # 当鼠标移动时，更新选择区域的位置
#         self.selection_rect.setY(event.pos().y())

#     def mouseReleaseEvent(self, event):
#         pass  # 不需要在鼠标释放时做任何事情

#     def show_page(self, page_number):
#         pixmap = QPixmap.fromImage(self.pages_data[page_number])
#         item = QGraphicsPixmapItem(pixmap)
#         self.scene.clear()
#         self.scene.addItem(item)

#     def next_page(self):
#         if self.current_page < len(self.pages_data) - 1:
#             self.current_page += 1
#             self.show_page(self.current_page)

#     def prev_page(self):
#         if self.current_page > 0:
#             self.current_page -= 1
#             self.show_page(self.current_page)

#     def snapshot_selection(self):
#         rect = self.selection_rect.rect()
#         pixmap = self.scene.items()[1].pixmap().copy(rect.toRect())

#         # 将 QPixmap 转换为 QImage
#         image = pixmap.toImage()

#         clipboard = QApplication.clipboard()
#         clipboard.setImage(image)

class PdfViewer(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.doc = None
        self.current_page = 0
        self.pages_data = []
        self.selection_rect = None
        self.selection_rects = []  # 存储每一页的方框

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

    def load_pdf(self, filename):
        self.doc = fitz.open(filename)

        self.pages_data = []
        for i in range(len(self.doc)):
            page = self.doc.load_page(i)
            pix = page.get_pixmap()
            img = QImage(pix.samples, pix.width, pix.height, QImage.Format_RGB888)
            self.pages_data.append(img)

        self.scene.clear()
        self.show_page(self.current_page)

    def create_selection_rect(self, page_number):
        page_width = self.pages_data[page_number].width()
        page_height = self.pages_data[page_number].height()
        rect_height = page_height / 10
        pen = QPen(Qt.black)
        pen.setWidth(10)
        selection_rect = self.scene.addRect(0, 0, page_width * 3, rect_height, pen)
        selection_rect.setFlag(QGraphicsPixmapItem.ItemIsMovable)
        selection_rect.setFlag(QGraphicsPixmapItem.ItemIsSelectable)
        self.selection_rects.append(selection_rect)

    def show_page(self, page_number):
        pixmap = QPixmap.fromImage(self.pages_data[page_number])
        item = QGraphicsPixmapItem(pixmap)
        self.scene.clear()
        self.scene.addItem(item)

        # 检查当前页是否有对应的方框，如果没有则创建
        if len(self.selection_rects) <= page_number:
            self.create_selection_rect(page_number)

        # 显示当前页的方框
        self.scene.addItem(self.selection_rects[page_number])

    def next_page(self):
        if self.current_page < len(self.pages_data) - 1:
            self.current_page += 1
            self.show_page(self.current_page)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.show_page(self.current_page)

    def snapshot_selection(self):
        rect = self.selection_rects[self.current_page].rect()
        pixmap = self.scene.items()[1].pixmap().copy(rect.toRect())

        # 将 QPixmap 转换为 QImage
        image = pixmap.toImage()

        clipboard = QApplication.clipboard()
        clipboard.setImage(image)




class ImageSupportingTextEdit(QTextEdit):
    def insert_image(self, image_path):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertImage(image_path)
        cursor.insertText("\n")

    def insert_image_from_clipboard(self):
        clipboard = QGuiApplication.clipboard()
        if clipboard.mimeData().hasImage():
            image = clipboard.image()
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.insertImage(image)
            cursor.insertText("\n")

class ChatWindow(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title

        # 创建一个垂直布局
        layout = QVBoxLayout()

        # 创建一个文本框用于显示聊天记录
        self.text_edit = ImageSupportingTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        # 创建一个文本输入框用于输入消息
        self.line_edit = QLineEdit()
        layout.addWidget(self.line_edit)

        # 创建一个发送按钮
        self.send_button = QPushButton('发送')
        self.send_button.clicked.connect(self.send_message)
        layout.addWidget(self.send_button)

        # 设置布局
        self.setLayout(layout)

    @Slot()
    def send_message(self):
        message = self.line_edit.text()
        if message == "看证据！":
            self.text_edit.append('我: ')
            self.text_edit.insert_image_from_clipboard()
        elif message.startswith("/image "):
            image_path = message[7:]
            self.text_edit.insert_image(image_path)
        else:
            self.text_edit.append('我: ' + message)
        self.line_edit.clear()

    def receive_message(self, message):
        if message.startswith("/image "):
            image_path = message[7:]
            self.text_edit.insert_image(image_path)
        else:
            self.text_edit.append(message)

class MainWindow(QMainWindow):
    def __init__(self, parent=None, message_queue=None):
        super().__init__(parent)
        self.message_queue = message_queue

        self.setWindowTitle('Chat Windows')

        main_splitter = QSplitter()

        # 创建一个垂直布局
        pdf_layout = QVBoxLayout()

        self.pdf_viewer = PdfViewer()
        self.pdf_viewer.load_pdf("1.pdf")

        self.snapshot_button = QPushButton('Snapshot')
        self.snapshot_button.clicked.connect(self.pdf_viewer.snapshot_selection)

        self.next_button = QPushButton('Next Page')
        self.next_button.clicked.connect(self.pdf_viewer.next_page)

        self.prev_button = QPushButton('Previous Page')
        self.prev_button.clicked.connect(self.pdf_viewer.prev_page)

        # 将PDF查看器和按钮添加到布局中
        pdf_layout.addWidget(self.pdf_viewer)
        pdf_layout.addWidget(self.next_button)
        pdf_layout.addWidget(self.prev_button)
        pdf_layout.addWidget(self.snapshot_button)
        # 创建一个小部件来包含PDF查看器和按钮，并设置其布局
        pdf_widget = QWidget()
        pdf_widget.setLayout(pdf_layout)
        main_splitter.addWidget(pdf_widget)
        
        self.list_widget = QListWidget()
        self.list_widget.currentItemChanged.connect(self.switch_chat)
        main_splitter.addWidget(self.list_widget)

        self.tab_widget = QTabWidget()
        self.tab_widget.tabBar().hide()

        self.chat_window1 = ChatWindow("???")
        self.list_widget.addItem(QListWidgetItem("???"))
        self.tab_widget.addTab(self.chat_window1, "???")

        self.chat_window2 = ChatWindow("ECHO")
        self.list_widget.addItem(QListWidgetItem("ECHO"))
        self.tab_widget.addTab(self.chat_window2, "ECHO")

        main_splitter.addWidget(self.tab_widget)

        # 设置初始大小比例
        main_splitter.setSizes([500, 50,300])

        self.setCentralWidget(main_splitter)

        self.thread = threading.Thread(target=self.check_message_queue, daemon=True)
        self.thread.start()

    @Slot(QListWidgetItem, QListWidgetItem)
    def switch_chat(self, current, previous):
        if current is not None:
            self.tab_widget.setCurrentIndex(self.list_widget.row(current))

    def check_message_queue(self):
        while True:
            if not self.message_queue.empty():
                target, message = self.message_queue.get()
                if target == "1":
                    self.chat_window1.receive_message(message)
                    self.list_widget.item(0).setBackground(Qt.red)
                elif target == "2":
                    self.chat_window2.receive_message(message)
                    self.list_widget.item(1).setBackground(Qt.red)

def backend_process(message_queue):
    while True:
        target = input("Enter target chat (Chat 1 or Chat 2): ")
        message = input("Enter your message: ")
        message_queue.put((target, message))

if __name__ == '__main__':
    message_queue = Queue()

    backend_thread = threading.Thread(target=backend_process, args=(message_queue,), daemon=True)
    backend_thread.start()

    app = QApplication(sys.argv)
    window = MainWindow(message_queue=message_queue)
    window.show()
    sys.exit(app.exec())
