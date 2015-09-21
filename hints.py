#!env python

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from functools import partial
import sys
import os
import time
from queue import LifoQueue
try:
    import ConfigParser
except:
    import configparser as ConfigParser


CWD = os.path.split(sys.argv[0])[0]
config = ConfigParser.ConfigParser()
config.read(os.path.join(CWD, 'hints.cfg'))


class Layer(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        rec = QApplication.desktop().screenGeometry()
        self.w = rec.width()
        self.h = rec.height()
        self.kv = config.get('Settings', 'keys').split(' ')
        self.ki = 0
        self.keys = self.kv[self.ki]
        self.rect = QRectF(0, 0, self.w, self.h)
        self.shortcuts = []
        self.rects = LifoQueue()
        self.query = ''

        self.resize(self.w, self.h)
        self.setStyleSheet("background:rgba(0,0,0,%s)" % config.getfloat('Settings', 'background_opacity'))
        self.setAttribute(Qt.WA_TranslucentBackground);
        self.setWindowFlags(Qt.FramelessWindowHint);
        view = QGraphicsView(self)
        scene = QGraphicsScene()
        scene.setSceneRect(0, 0, self.w, self.h)
        view.setScene(scene)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);
        view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff);

        self.setCentralWidget(view)
        self.scene = scene
        self.drawLines()
        self.esc = QShortcut(QKeySequence('Esc'), self)
        self.esc.activated.connect(lambda: os.system('xdotool mousemove %s' % config.get('Settings', 'mouse_home_coords')))
        self.back = QShortcut(QKeySequence('Backspace'), self)
        self.back.activated.connect(self.goBack)

    def goBack(self):
        if not self.query:
            return
        self.query = self.query[:-1]
        self.setArea(self.rects.get(), True)

    def setPointer(self, rect):
        os.system('xdotool mousemove %s %s' % (rect.center().x()+self.pos().x()-10, rect.center().y()+self.pos().y()-10))
        self.scene.addEllipse(rect.center().x()+self.pos().x()-2, rect.center().y()+self.pos().y()-2, 4, 4, QPen(QColor('blue')), QBrush(QColor('blue')))

    def clickHere(self, rect):
        self.showMinimized()
        time.sleep(0.3)
        os.system('xdotool mousemove %s %s; xdotool click 1' % (rect.center().x()+self.pos().x()-10, rect.center().y()+self.pos().y()-10))
        time.sleep(0.3)
        os.system('xdotool mousemove %s' % config.get('Settings', 'mouse_home_coords'))
        sys.exit()

    def getArea(self, k, direction):
        rect = self.rect
        i = self.keys.index(k)
        c = len(self.keys)
        y = rect.topLeft().y()
        x = rect.topLeft().x()

        if direction == 'hor':
            new_rect = QRectF(rect.width()/c*i+x, y, rect.width()/c, rect.height())
        else:
            new_rect = QRectF(x, rect.height()/c*i+y, rect.width(), rect.height()/c)
        return new_rect

    def selectArea(self, hint, rect):
        self.query += hint
        self.setArea(rect)

    def setArea(self, new_rect, back=False):
        if not new_rect:
            return
        if not back:
            self.rects.put(self.rect)
        self.rect = new_rect
        self.drawLines()

    def drawLines(self):
        for sh in self.shortcuts:
            sh.activated.disconnect()
            sh.setKey('')
            sh.setEnabled(False)
        self.shortcuts = []
        self.scene.clear()
        rect = self.rect
        c = len(self.keys)
        direction = 'hor' if rect.width() > rect.height() else 'vert'
        if (direction == 'hor' and rect.width()/c < 60) or (direction == 'vert' and rect.height()/c < 60):
            if c > 2:
                self.ki += 1
        else:
            if c < len(self.kv[0]):
                self.ki -= 1
        self.keys = self.kv[self.ki]
        c = len(self.keys)
        color = QColor(config.get('Settings', 'lines_color'))
        fontColor = QColor(config.get('Settings', 'text_color'))
        pen = QPen(color)
        if rect.width() > 100:
            fsize = rect.width()/c/2
        elif rect.width() > 50:
            fsize = 24
        else:
            fsize = 18
        font = QFont('Sans', fsize)
        pen.setWidth(2)

        self.scene.addRect(rect, pen, QBrush())

        for n, k in enumerate(self.keys):
            if direction == 'hor':
                x = n*rect.width()/c+rect.topLeft().x()
                self.scene.addLine(x, rect.topLeft().y(), x, rect.height()+rect.topLeft().y(), pen)
                hint = self.scene.addText(k, font)
                if rect.height() > 150:
                    hint.setPos(x+rect.width()/c/2 - rect.width()/c/8, rect.height()/2+rect.topLeft().y()-fsize)
                else:
                    hint.setPos(x+rect.width()/c/2 - rect.width()/c/8, rect.height()*2+rect.topLeft().y()-fsize)
            else:
                x = rect.topLeft().x()
                y = n*rect.height()/c
                self.scene.addLine(x, y+rect.topLeft().y(), x+rect.width(), y+rect.topLeft().y(), pen)
                hint = self.scene.addText(k, font)
                if rect.width() > 100:
                    hint.setPos(x+rect.width()/2 - rect.width()/c/4, y+rect.height()/c/2+rect.topLeft().y() - 20)
                else:
                    hint.setPos(x+rect.width()*1.3 - rect.width()/c/4, y+rect.height()/c/2+rect.topLeft().y() - 20)
            hint.setDefaultTextColor(fontColor)
            shortcut = QShortcut(QKeySequence(k), self)
            shortcut.activated.connect(partial(self.selectArea, k, self.getArea(k, direction)))
            self.shortcuts.append(shortcut)
            shortcut = QShortcut(QKeySequence('Ctrl+%s' % k), self)
            shortcut.activated.connect(partial(self.clickHere, self.getArea(k, direction)))
            self.shortcuts.append(shortcut)
            shortcut = QShortcut(QKeySequence('Shift+%s' % k), self)
            shortcut.activated.connect(partial(self.setPointer, self.getArea(k, direction)))
            self.shortcuts.append(shortcut)
        q = self.scene.addText(self.query, QFont('Sans', config.getint('Settings', 'query_font_size')))
        q.setPos(self.w/2 - q.boundingRect().width()/2, 100)
        q.setDefaultTextColor(QColor(config.get('Settings', 'query_color')))

app = QApplication(sys.argv)
layer = Layer()
layer.show()
app.exec_()
sys.exit()
