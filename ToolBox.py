# -*- coding:utf-8 -*-
import os
import re
from collections import Counter
import emoji
import requests
import webbrowser
import sys
import json
from threading import Thread
import time as _time
import random
import subprocess
import socket
from bs4 import BeautifulSoup
from prettytable import PrettyTable
from PySide2.QtGui import QColor, QFont, QIcon, QKeySequence, QPixmap, QStandardItem, QStandardItemModel, QTextCursor
from PySide2.QtCore import Signal
from PySide2.QtWidgets import QAbstractItemView, QAction, QApplication, QFileDialog, QGridLayout, QGroupBox, QInputDialog, QLabel, QLineEdit, QMainWindow, QMenu, QMenuBar, QMessageBox, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QStatusBar, QStyleFactory, QTableView, QTextEdit, QVBoxLayout
from PySide2.QtWidgets import QListWidget, QStackedWidget
from PySide2.QtWidgets import QListWidgetItem
from PySide2.QtWidgets import QWidget
from PySide2.QtWidgets import QHBoxLayout
from PySide2.QtCore import QSize, Qt

appname = '''ToolBox'''
appmessage = '''一款小小的自用的工具箱'''
author = '''ordinary-student'''
version = '''v2.1.1'''
last_update = '''2021-08-04'''
left_widget_qss = '''
QListWidget, QListView, QTreeWidget, QTreeView {
    outline: 0px;
}

QListWidget {
    min-width: 120px;
    max-width: 120px;
    color: Black;
    background: #F5F5F5;
}

QListWidget::Item:hover
{
    color:green;
}

QListWidget::Item:selected {
    color: green;
    background: #CDEDC9;
    border-left: 5px solid green;
}

HistoryPanel:hover {
    background: rgb(52, 52, 52);
}
'''
statusbar_qss = '''
QStatusBar{
    color:#003300;
    background: #88C1CD;
}
'''


class Wifi(object):
    '''WiFi类'''

    def __init__(self, ssid, idcheck, pwd, bssid, network, networktype, channel):
        '''构造函数'''
        self.ssid = ssid
        self.idcheck = idcheck
        self.pwd = pwd
        self.bssid = bssid
        self.network = network
        self.networktype = networktype
        self.channel = channel

    def toString(self) -> dict:
        '''返回一个WiFi信息字典'''
        w = {}
        w['名称'] = self.ssid
        w['身份验证'] = self.idcheck
        w['加密'] = self.pwd
        w['bssid'] = self.bssid
        w['信号'] = self.network
        w['无线电类型'] = self.networktype
        w['信道'] = self.channel
        return w

    def toList(self) -> list:
        '''返回一个WiFi信息列表'''
        return [self.ssid, self.idcheck, self.pwd, self.bssid, self.network, self.networktype, self.channel]


class MyThread(Thread):
    '''自定义线程类'''

    def __init__(self, func, args=()):
        '''构造函数'''
        super(MyThread, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        '''运行'''
        self.result = self.func(*self.args)

    def get_result(self):
        '''获取结果'''
        try:
            return self.result
        except Exception:
            return None


class ToolBox(QMainWindow):
    '''工具箱'''
    _ping_signal = Signal(bool, str)

    def __init__(self, app: QApplication):
        '''构造函数'''
        super(ToolBox, self).__init__()
        self.app = app

        # 皮肤主题
        self.skin = 0
        self.skins = ["Fusion", "Windowsvista", "Windows"]
        # 菜单项禁用列表
        self.forbidden = [0, 1, 4]
        # 加载界面ui
        self.initUI()
        # IP合法性
        self.ipislegal = True
        # Ping请求数
        self.ping_num = 3
        self._ping_signal.connect(self.set_ui)
        # 当前页
        self.currentPageIndex = 0
        # 地址字典
        self.url_dict = {}

    def initUI(self):
        '''加载界面ui'''
        # 多网卡情况下获取本地IP
        ips = socket.gethostbyname_ex(socket.gethostname())[2]
        # 最后一个IP，一般为无线网卡IP
        self.localip = ips[-1]
        # 窗口标题
        self.setWindowTitle('工具箱--'+str(ips))
        # 设置窗口图标
        self.setWindowIcon(self.generateIcon())
        # 窗口大小
        self.resize(1000, 700)
        # 最小大小
        self.setMinimumSize(700, 500)
        # 窗口居中
        self.center()

        # 菜单栏
        self.menubar = QMenuBar(self)
        # self.menubar.setGeometry(QRect(0, 0, 800, 23))

        # 文件菜单
        self.menu_file = QMenu('文件', self.menubar)
        # 帮助菜单
        self.menu_help = QMenu('帮助', self.menubar)

        # 加载参数
        self.action_loadParams = QAction('加载参数', self.menu_file)
        self.action_loadParams.setShortcut(QKeySequence("F2"))
        self.action_loadParams.triggered.connect(self.load_params)
        # 保存参数
        self.action_saveParams = QAction('保存参数', self.menu_file)
        self.action_saveParams.setShortcut(QKeySequence("F3"))
        self.action_saveParams.triggered.connect(self.save_params)
        # 退出
        self.action_exit = QAction('退出', self.menu_file)
        self.action_exit.triggered.connect(self.close)
        # 窗口置顶
        self.action_top = QAction('窗口置顶', self.menu_help)
        self.action_top.setShortcut(QKeySequence("F5"))
        self.action_top.setCheckable(True)
        self.action_top.triggered.connect(self.set_top)
        # 换肤
        self.action_skin = QAction('换肤', self.menu_help)
        self.action_skin.setShortcut(QKeySequence("F4"))
        self.action_skin.triggered.connect(self.change_skin)
        # 关于
        self.action_about = QAction('关于', self.menu_help)
        self.action_about.setShortcut(QKeySequence("F1"))
        self.action_about.triggered.connect(self.about)

        # 文件菜单添加菜单项
        self.menu_file.addAction(self.action_loadParams)
        self.menu_file.addAction(self.action_saveParams)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_exit)
        # 帮助菜单添加菜单项
        self.menu_help.addAction(self.action_top)
        self.menu_help.addAction(self.action_skin)
        self.menu_help.addAction(self.action_about)

        # 菜单栏添加菜单
        self.menubar.addMenu(self.menu_file)
        self.menubar.addMenu(self.menu_help)
        # 设置菜单栏
        self.setMenuBar(self.menubar)

        # 创建中央容器
        self.centralwidget = QWidget(self)

        # 左侧选项列表
        self.left_widget = QListWidget(self.centralwidget)
        # 去掉边框
        self.left_widget.setFrameShape(QListWidget.NoFrame)
        # 隐藏滚动条
        self.left_widget.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.left_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # 导入QListWidget的qss样式
        self.left_widget_style = left_widget_qss
        self.left_widget.setStyleSheet(self.left_widget_style)

        # 工具列表
        self.tool_list = ['EasyPing', 'Windows Tool',
                          '文件目录对比', '文件变化监控',  '豆瓣租房信息']

        for i in self.tool_list:
            # 左侧选项的添加
            self.item = QListWidgetItem(i, self.left_widget)
            self.item.setSizeHint(QSize(30, 60))
            # 居中显示
            self.item.setTextAlignment(Qt.AlignCenter)

        # 右侧页面
        self.right_widget = QStackedWidget(self.centralwidget)

        # 创建页面
        self.initEasyPingWidget()
        self.initWindowsToolWidget()
        self.initComparedirWidget()
        self.initMonitorDirWidget()
        self.initDoubanHouseWidget()
        # 添加页面
        self.right_widget.addWidget(self.widget_easyping)
        self.right_widget.addWidget(self.widget_windowstool)
        self.right_widget.addWidget(self.widget_comparedir)
        self.right_widget.addWidget(self.widget_monitordir)
        self.right_widget.addWidget(self.widget_doubanhouse)

        # 窗口的整体布局-水平布局
        self.main_layout = QHBoxLayout(self.centralwidget)
        self.main_layout.addWidget(self.left_widget)
        self.main_layout.addWidget(self.right_widget)
        self.main_layout.setStretch(0, 0)

        # list和右侧窗口的index对应绑定
        self.left_widget.currentRowChanged.connect(
            self.show_stackedWidget)

        # 设置中央容器right_widget
        self.setCentralWidget(self.centralwidget)

        # 状态栏
        self.statusbar = QStatusBar(self)
        self.statusbar_style = statusbar_qss
        self.statusbar.setStyleSheet(self.statusbar_style)
        self.setStatusBar(self.statusbar)

    def initEasyPingWidget(self):
        '''创建EasyPing页'''
        self.widget_easyping = QWidget(self.right_widget)
        # 参数设置区域
        self.groupBox_setting = QGroupBox('设置待检测的IP范围', self.widget_easyping)

        # 起始IP
        self.lineEdit_startIP = QLineEdit(self.groupBox_setting)
        # 改变字体和大小
        font = QFont("微软雅黑", 12, QFont.Bold)
        self.lineEdit_startIP.setFont(font)
        # IP最后一点的索引
        last_point_index = self.localip.rindex('.')
        # 填写起始IP
        self.lineEdit_startIP.setText(self.localip[0:last_point_index]+'.0')
        # 绑定事件-自动填写结束IP
        self.lineEdit_startIP.textChanged.connect(self.auto_fill_endip)

        # 横条标签
        self.label_to = QLabel(' -- ')

        # 结束IP
        self.lineEdit_endIP = QLineEdit(self.groupBox_setting)
        self.lineEdit_endIP.setFont(font)
        # 填写结束IP
        self.lineEdit_endIP.setText(self.localip[0:last_point_index]+'.255')

        # ping按钮
        self.pushButton_ping = QPushButton(
            'Ping', self.groupBox_setting)
        self.pushButton_ping.setStyleSheet(
            "QPushButton:hover{color: white;background:green}")
        self.pushButton_ping.clicked.connect(self.start_ping)
        # setting按钮
        self.pushButton_setting = QPushButton(
            '设置', self.groupBox_setting)
        self.pushButton_setting.setStyleSheet(
            "QPushButton:hover{color: green}")
        self.pushButton_setting.clicked.connect(self.ping_setting)

        # 水平布局
        self.horizontalLayout_ep = QHBoxLayout(self.groupBox_setting)
        self.horizontalLayout_ep.setSpacing(10)
        self.horizontalLayout_ep.addWidget(self.lineEdit_startIP)
        self.horizontalLayout_ep.addWidget(self.label_to)
        self.horizontalLayout_ep.addWidget(self.lineEdit_endIP)
        self.horizontalLayout_ep.addWidget(self.pushButton_ping)
        self.horizontalLayout_ep.addWidget(self.pushButton_setting)

        # IP检测结果区域
        self.groupBox_ipstatus = QGroupBox('IP检测结果', self.widget_easyping)
        # 网格布局
        self.gridLayout_ip = QGridLayout(self.groupBox_ipstatus)
        self.gridLayout_ip.setContentsMargins(5, 5, 5, 5)
        self.gridLayout_ip.setSpacing(5)
        # IP标签列表
        self.iplabel_list = []
        # 结果列表
        self.result_list = []
        # 索引
        list_index = 0
        # 循环添加
        for i in range(1, 17):
            for j in range(1, 17):
                # 创建标签
                label = QLabel(str(list_index), self.groupBox_ipstatus)
                # 最小尺寸
                label.setMinimumSize(32, 15)
                # 背景色
                label.setStyleSheet("background-color: rgb(203, 203, 203);")
                # 居中
                label.setAlignment(Qt.AlignCenter)
                # 加入列表
                self.iplabel_list.append(label)
                # 添加控件
                self.gridLayout_ip.addWidget(label, i-1, j-1, 1, 1)
                list_index = list_index + 1

        # 本页垂直布局
        self.verticalLayout_ep = QVBoxLayout(self.widget_easyping)
        self.verticalLayout_ep.addWidget(self.groupBox_setting)
        self.verticalLayout_ep.addWidget(self.groupBox_ipstatus)
        self.verticalLayout_ep.setStretch(0, 1)
        self.verticalLayout_ep.setStretch(1, 20)

    def initWindowsToolWidget(self):
        '''创建Windows工具页'''
        self.widget_windowstool = QWidget(self.right_widget)
        # 命令按钮区域
        self.groupBox_cmdbtn = QGroupBox('命令', self.widget_windowstool)

        # 查看系统许可证状态按钮
        self.pushButton_syslicence = QPushButton(
            '查看系统许可证状态', self.groupBox_cmdbtn)
        self.pushButton_syslicence.setStyleSheet(
            "QPushButton:hover{color: green}")
        self.pushButton_syslicence.clicked.connect(self.syslicence)
        # 查看系统许可证状态简化版按钮
        self.pushButton_syslicence2 = QPushButton(
            '查看系统许可证状态（简化版）', self.groupBox_cmdbtn)
        self.pushButton_syslicence2.setStyleSheet(
            "QPushButton:hover{color: green}")
        self.pushButton_syslicence2.clicked.connect(self.syslicence2)
        # 查看系统激活信息按钮
        self.pushButton_sysactive = QPushButton(
            '查看系统激活信息', self.groupBox_cmdbtn)
        self.pushButton_sysactive.setStyleSheet(
            "QPushButton:hover{color: green}")
        self.pushButton_sysactive.clicked.connect(self.sysactive)
        # 清空输出区按钮
        self.pushButton_cleartext = QPushButton(
            '清空输出区', self.groupBox_cmdbtn)
        self.pushButton_cleartext.setStyleSheet(
            "QPushButton:hover{color: green}")

        # 扫描附近WiFi按钮
        self.pushButton_wifiscan = QPushButton(
            '扫描附近的WiFi', self.groupBox_cmdbtn)
        self.pushButton_wifiscan.setStyleSheet(
            "QPushButton:hover{color: blue}")
        self.pushButton_wifiscan.clicked.connect(self.wifiscan)
        # 查看WiFi密码按钮
        self.pushButton_wifipwd = QPushButton(
            '查看连接过的WiFi密码', self.groupBox_cmdbtn)
        self.pushButton_wifipwd.setStyleSheet(
            "QPushButton:hover{color: orange}")
        self.pushButton_wifipwd.clicked.connect(self.wifipwd)

        # 网格布局
        self.gridLayout = QGridLayout(self.groupBox_cmdbtn)
        # 设置间距
        self.gridLayout.setSpacing(10)
        self.gridLayout.addWidget(self.pushButton_syslicence, 0, 0)
        self.gridLayout.addWidget(self.pushButton_syslicence2, 0, 1)
        self.gridLayout.addWidget(self.pushButton_sysactive, 0, 2)
        self.gridLayout.addWidget(self.pushButton_wifiscan, 1, 0)
        self.gridLayout.addWidget(self.pushButton_wifipwd, 1, 1)
        self.gridLayout.addWidget(self.pushButton_cleartext, 1, 2)

        # 信息输出区域
        self.groupBox_outputmess = QGroupBox('输出信息', self.widget_windowstool)
        # 输出信息框
        self.textEdit_cmd = QTextEdit(self.groupBox_outputmess)
        self.pushButton_cleartext.clicked.connect(
            self.textEdit_cmd.clear)
        self.verticalLayout_cmd = QVBoxLayout(self.groupBox_outputmess)
        self.verticalLayout_cmd.addWidget(self.textEdit_cmd)

        # 本页垂直布局
        self.verticalLayout_wt = QVBoxLayout(self.widget_windowstool)
        self.verticalLayout_wt.addWidget(self.groupBox_cmdbtn)
        self.verticalLayout_wt.addWidget(self.groupBox_outputmess)
        self.verticalLayout_wt.setStretch(0, 1)
        self.verticalLayout_wt.setStretch(1, 4)

    def initComparedirWidget(self):
        '''创建文件目录对比页'''
        self.widget_comparedir = QWidget(self.right_widget)

        # 参数区域
        self.groupBox_params = QGroupBox('填写待对比的目录', self.widget_comparedir)

        # A目录标签
        self.label_adir = QLabel('A目录：', self.groupBox_params)
        # A目录输入框
        self.lineEdit_adir = QLineEdit(self.groupBox_params)
        # A目录按钮
        self.pushButton_adir = QPushButton('选择A目录', self.groupBox_params)
        self.pushButton_adir.setStyleSheet(
            "QPushButton:hover{color: green}")
        self.pushButton_adir.clicked.connect(self.select_adir)
        # 水平布局
        self.horizontalLayout_1 = QHBoxLayout()
        self.horizontalLayout_1.addWidget(self.label_adir)
        self.horizontalLayout_1.addWidget(self.lineEdit_adir)
        self.horizontalLayout_1.addWidget(self.pushButton_adir)
        self.horizontalLayout_1.setStretch(0, 1)
        self.horizontalLayout_1.setStretch(1, 8)
        self.horizontalLayout_1.setStretch(2, 1)

        # B目录标签
        self.label_bdir = QLabel('B目录：', self.groupBox_params)
        # B目录输入框
        self.lineEdit_bdir = QLineEdit(self.groupBox_params)
        # B目录按钮
        self.pushButton_bdir = QPushButton('选择B目录', self.groupBox_params)
        self.pushButton_bdir.setStyleSheet(
            "QPushButton:hover{color: green}")
        self.pushButton_bdir.clicked.connect(self.select_bdir)
        # 水平布局
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.addWidget(self.label_bdir)
        self.horizontalLayout_2.addWidget(self.lineEdit_bdir)
        self.horizontalLayout_2.addWidget(self.pushButton_bdir)
        self.horizontalLayout_2.setStretch(0, 1)
        self.horizontalLayout_2.setStretch(1, 8)
        self.horizontalLayout_2.setStretch(2, 1)

        # 填充物
        self.horizontalSpacer = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        # 开始对比按钮
        self.pushButton = QPushButton('开始对比', self.groupBox_params)
        self.pushButton.setStyleSheet(
            "QPushButton:hover{color: white;background:green}")
        self.pushButton.clicked.connect(self.compare)
        # 水平布局
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.addItem(self.horizontalSpacer)
        self.horizontalLayout_3.addWidget(self.pushButton)
        self.horizontalLayout_3.setStretch(0, 9)
        self.horizontalLayout_3.setStretch(1, 1)

        # 参数区域-垂直布局
        self.verticalLayout = QVBoxLayout(self.groupBox_params)
        self.verticalLayout.addLayout(self.horizontalLayout_1)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.verticalLayout.setStretch(0, 1)
        self.verticalLayout.setStretch(1, 1)
        self.verticalLayout.setStretch(2, 1)

        # A区域
        self.groupBox_adir = QGroupBox('A目录独有', self.widget_comparedir)
        self.textEdit_adir = QTextEdit(self.groupBox_adir)
        self.verticalLayout_a = QVBoxLayout(self.groupBox_adir)
        self.verticalLayout_a.addWidget(self.textEdit_adir)

        # B区域
        self.groupBox_bdir = QGroupBox('B目录独有', self.widget_comparedir)
        self.textEdit_bdir = QTextEdit(self.groupBox_bdir)
        self.verticalLayout_b = QVBoxLayout(self.groupBox_bdir)
        self.verticalLayout_b.addWidget(self.textEdit_bdir)

        # 本页垂直布局
        self.verticalLayout_comparedir = QVBoxLayout(self.widget_comparedir)
        self.verticalLayout_comparedir.addWidget(self.groupBox_params)
        self.verticalLayout_comparedir.addWidget(self.groupBox_adir)
        self.verticalLayout_comparedir.addWidget(self.groupBox_bdir)
        self.verticalLayout_comparedir.setStretch(0, 1)
        self.verticalLayout_comparedir.setStretch(1, 2)
        self.verticalLayout_comparedir.setStretch(2, 2)

    def initMonitorDirWidget(self):
        '''创建监控文件变化页'''
        self.widget_monitordir = QWidget(self.right_widget)
        # 参数区域
        self.groupBox_mdp = QGroupBox('填写被监控的目录和记录文件', self.widget_monitordir)

        # 被监控的目录标签
        self.label_mdir = QLabel('被监控的目录：', self.groupBox_mdp)
        # 被监控的目录输入框
        self.lineEdit_mdir = QLineEdit(self.groupBox_mdp)
        # 被监控的目录按钮
        self.pushButton_mdir = QPushButton('选择被监控的目录', self.groupBox_mdp)
        self.pushButton_mdir.setStyleSheet(
            "QPushButton:hover{color: green}")
        self.pushButton_mdir.clicked.connect(self.select_monitordir)
        # 水平布局
        self.horizontalLayout_m1 = QHBoxLayout()
        self.horizontalLayout_m1.addWidget(self.label_mdir)
        self.horizontalLayout_m1.addWidget(self.lineEdit_mdir)
        self.horizontalLayout_m1.addWidget(self.pushButton_mdir)
        self.horizontalLayout_m1.setStretch(0, 1)
        self.horizontalLayout_m1.setStretch(1, 8)
        self.horizontalLayout_m1.setStretch(2, 1)

        # 记录文件标签
        self.label_recordfile = QLabel('    记录文件：', self.groupBox_mdp)
        # 记录文件输入框
        self.lineEdit_recordfile = QLineEdit(self.groupBox_mdp)
        # 记录文件按钮
        self.pushButton_recordfile = QPushButton(
            '  选择记录文件  ', self.groupBox_mdp)
        self.pushButton_recordfile.setStyleSheet(
            "QPushButton:hover{color: green}")
        self.pushButton_recordfile.clicked.connect(self.select_recordfile)
        # 水平布局
        self.horizontalLayout_m2 = QHBoxLayout()
        self.horizontalLayout_m2.addWidget(self.label_recordfile)
        self.horizontalLayout_m2.addWidget(self.lineEdit_recordfile)
        self.horizontalLayout_m2.addWidget(self.pushButton_recordfile)
        self.horizontalLayout_m2.setStretch(0, 1)
        self.horizontalLayout_m2.setStretch(1, 8)
        self.horizontalLayout_m2.setStretch(2, 1)

        # 填充物
        self.horizontalSpacer_m = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        # 清空输出按钮
        self.pushButton_clear = QPushButton(
            '    清空输出    ', self.groupBox_mdp)
        self.pushButton_clear.setStyleSheet(
            "QPushButton:hover{color:green}")
        self.pushButton_clear.clicked.connect(self.clear_outputArea)
        # 更新记录文件按钮
        self.pushButton_refresh = QPushButton(
            '  更新记录文件  ', self.groupBox_mdp)
        self.pushButton_refresh.setStyleSheet(
            "QPushButton:hover{color:green}")
        self.pushButton_refresh.clicked.connect(self.refresh)
        # 开始对比按钮
        self.pushButton_startmonitor = QPushButton(
            '    开始对比    ', self.groupBox_mdp)
        self.pushButton_startmonitor.setStyleSheet(
            "QPushButton:hover{color:white;background:green}")
        self.pushButton_startmonitor.clicked.connect(self.start_monitor)
        # 水平布局
        self.horizontalLayout_m3 = QHBoxLayout()
        self.horizontalLayout_m3.addItem(self.horizontalSpacer_m)
        self.horizontalLayout_m3.addWidget(self.pushButton_clear)
        self.horizontalLayout_m3.addWidget(self.pushButton_refresh)
        self.horizontalLayout_m3.addWidget(self.pushButton_startmonitor)
        self.horizontalLayout_m3.setStretch(0, 7)
        self.horizontalLayout_m3.setStretch(1, 1)
        self.horizontalLayout_m3.setStretch(2, 1)
        self.horizontalLayout_m3.setStretch(3, 1)

        # 参数区域-垂直布局
        self.verticalLayout_mdp = QVBoxLayout(self.groupBox_mdp)
        self.verticalLayout_mdp.addLayout(self.horizontalLayout_m1)
        self.verticalLayout_mdp.addLayout(self.horizontalLayout_m2)
        self.verticalLayout_mdp.addLayout(self.horizontalLayout_m3)
        self.verticalLayout_mdp.setStretch(0, 1)
        self.verticalLayout_mdp.setStretch(1, 1)
        self.verticalLayout_mdp.setStretch(2, 1)

        # 被删除的文件区域
        self.groupBox_deletedfile = QGroupBox('被删除的文件', self.widget_monitordir)
        self.textEdit_deletedfile = QTextEdit(self.groupBox_deletedfile)
        self.verticalLayout_deletedfile = QVBoxLayout(
            self.groupBox_deletedfile)
        self.verticalLayout_deletedfile.addWidget(self.textEdit_deletedfile)

        # 新增文件区域
        self.groupBox_newfile = QGroupBox('新增的文件', self.widget_monitordir)
        self.textEdit_newfile = QTextEdit(self.groupBox_newfile)
        self.verticalLayout_newfile = QVBoxLayout(self.groupBox_newfile)
        self.verticalLayout_newfile.addWidget(self.textEdit_newfile)

        # 本页垂直布局
        self.verticalLayout_monitordir = QVBoxLayout(self.widget_monitordir)
        self.verticalLayout_monitordir.addWidget(self.groupBox_mdp)
        self.verticalLayout_monitordir.addWidget(self.groupBox_deletedfile)
        self.verticalLayout_monitordir.addWidget(self.groupBox_newfile)
        self.verticalLayout_monitordir.setStretch(0, 1)
        self.verticalLayout_monitordir.setStretch(1, 1)
        self.verticalLayout_monitordir.setStretch(2, 2)

    def initDoubanHouseWidget(self):
        '''创建豆瓣租房信息筛选页'''
        self.widget_doubanhouse = QWidget(self.right_widget)
        # 参数区域
        self.groupBox_top = QGroupBox(
            '填写筛选条件', self.widget_doubanhouse)

        # 筛选信息标签
        self.label_filter = QLabel('筛选信息', self.groupBox_top)
        # 筛选信息输入框
        self.lineEdit_filter = QLineEdit(self.groupBox_top)
        self.lineEdit_filter.setPlaceholderText('填写筛选条件，多个筛选条件用+号连接')
        # 改变字体和大小
        font2 = QFont("楷体", 12, QFont.Bold)
        self.lineEdit_filter.setFont(font2)
        # 水平布局
        self.horizontalLayout_top = QHBoxLayout()
        self.horizontalLayout_top.addWidget(self.label_filter)
        self.horizontalLayout_top.addWidget(self.lineEdit_filter)
        self.horizontalLayout_top.setStretch(0, 1)
        self.horizontalLayout_top.setStretch(1, 8)

        # 爬取页数标签
        self.label_page = QLabel('爬取页数', self.groupBox_top)
        self.pageBox = QSpinBox(self.groupBox_top)
        self.pageBox.setFont(font2)
        self.pageBox.setCursor(Qt.PointingHandCursor)
        self.pageBox.setMinimum(1)
        self.pageBox.setMaximum(999)

        # 填充物
        self.horizontalSpacer_c = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        # 开始爬取按钮
        self.pushButton_crawl = QPushButton('开始爬取', self.groupBox_top)
        self.pushButton_crawl.setCursor(Qt.PointingHandCursor)
        self.pushButton_crawl.setStyleSheet(
            "QPushButton:hover{color:blue;background:pink}")
        self.pushButton_crawl.clicked.connect(self.start_crawl)

        # 水平布局
        self.horizontalLayout_top2 = QHBoxLayout()
        self.horizontalLayout_top2.addWidget(self.label_page)
        self.horizontalLayout_top2.addWidget(self.pageBox)
        self.horizontalLayout_top2.addItem(self.horizontalSpacer_c)
        self.horizontalLayout_top2.addWidget(self.pushButton_crawl)
        self.horizontalLayout_top2.setStretch(0, 1)
        self.horizontalLayout_top2.setStretch(1, 1)
        self.horizontalLayout_top2.setStretch(2, 5)
        self.horizontalLayout_top2.setStretch(3, 2)

        # 参数区域-垂直布局
        self.verticalLayout_top = QVBoxLayout(self.groupBox_top)
        self.verticalLayout_top.addLayout(self.horizontalLayout_top)
        self.verticalLayout_top.addLayout(self.horizontalLayout_top2)
        self.verticalLayout_top.setStretch(0, 1)
        self.verticalLayout_top.setStretch(1, 1)

        # 结果显示区域
        self.groupBox_housemess = QGroupBox('结果显示', self.widget_doubanhouse)

        # 结果表格
        self.table = QTableView(self.groupBox_housemess)
        # 设置行列数
        self.model = QStandardItemModel(0, 2)
        # 设置表头
        self.model.setHorizontalHeaderLabels(['时间', '标题'])
        # 设置表格模式
        self.table.setModel(self.model)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setStretchLastSection(False)
        # 表格双击事件
        self.table.doubleClicked.connect(self.open_url)

        #
        self.verticalLayout_housemess = QVBoxLayout(self.groupBox_housemess)
        self.verticalLayout_housemess.setSpacing(5)
        self.verticalLayout_housemess.addWidget(self.table)

        # 本页垂直布局
        self.verticalLayout_doubanhouse = QVBoxLayout(self.widget_doubanhouse)
        self.verticalLayout_doubanhouse.addWidget(self.groupBox_top)
        self.verticalLayout_doubanhouse.addWidget(self.groupBox_housemess)
        self.verticalLayout_doubanhouse.setStretch(0, 1)
        self.verticalLayout_doubanhouse.setStretch(1, 5)

    def generateIcon(self) -> QIcon:
        '''生成图标'''
        pixmap = QPixmap(256, 256)
        # 图片颜色
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        pixmap.fill(QColor(r, g, b))
        return QIcon(pixmap)

    def set_top(self):
        '''窗口置顶'''
        # 判断勾选状态
        if self.action_top.isChecked():
            # 置顶
            self.setWindowFlags(Qt.WindowStaysOnTopHint)
        else:
            # 取消置顶
            self.setWindowFlags(Qt.Widget)
        # 显示窗口
        self.show()

    def center(self):
        '''窗口居中显示'''
        screen = self.app.primaryScreen().geometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)

    def change_skin(self):
        '''换肤'''
        self.skin = self.skin + 1
        if self.skin >= len(self.skins):
            self.skin = 0
        # 设置界面风格
        self.app.setStyle(QStyleFactory.create(self.skins[self.skin]))

    def about(self):
        '''关于'''
        # 显示弹窗
        QMessageBox.about(self, f'关于{appname}',
                          "{}<br>{}<br>author：<a href='https://github.com/ordinary-student'>{}</a><br>版本：{}<br>Last-Update：{}".format(appname, appmessage, author, version, last_update))

    def show_stackedWidget(self, index: int):
        '''显示对应的右侧页面'''
        self.right_widget.setCurrentIndex(index)
        self.currentPageIndex = index
        # 清空状态栏显示
        self.statusbar.showMessage('')
        # 判断-菜单项禁用列表
        if index in self.forbidden:
            self.action_loadParams.setEnabled(False)
            self.action_saveParams.setEnabled(False)
        else:
            self.action_loadParams.setEnabled(True)
            self.action_saveParams.setEnabled(True)

    def save_params(self):
        '''保存参数'''
        # 弹出文件选择器
        filepath, filetype = QFileDialog.getSaveFileName(
            self, "保存参数", os.getcwd(), "Json File (*.json)")

        # 判断
        if len(filepath) != 0:
            # A目录的路径
            path_a = self.lineEdit_adir.text()
            # B目录的路径
            path_b = self.lineEdit_bdir.text()
            # 被监控目录的路径
            path_mdir = self.lineEdit_mdir.text()
            # 记录文件的路径
            path_recordfile = self.lineEdit_recordfile.text()
            # 组成字典
            params = {'path_a': path_a,
                      'path_b': path_b, 'path_mdir': path_mdir, 'path_recordfile': path_recordfile}
            # 写入文件
            if not filepath.endswith('.json'):
                filepath = filepath+'.json'
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(params, f)
            # 状态栏显示
            self.statusbar.showMessage(
                '保存参数完成！参数文件路径：{}'.format(os.path.abspath(filepath)))

    def load_params(self):
        '''加载参数'''
        # 弹出文件选择器
        filepath, filetype = QFileDialog.getOpenFileName(
            self, "加载参数", os.getcwd(), "Json File (*.json)")
        # 判断
        if len(filepath) != 0:
            try:
                # 读取文件
                with open(filepath, 'r', encoding='utf-8') as f:
                    params = json.load(f)
                    # 判断当前页
                    if self.currentPageIndex == 2:
                        # A目录的路径
                        self.lineEdit_adir.setText(params['path_a'])
                        # B目录的路径
                        self.lineEdit_bdir.setText(params['path_b'])
                    elif self.currentPageIndex == 3:
                        # 被监控目录的路径
                        self.lineEdit_mdir.setText(params['path_mdir'])
                        # 记录文件的路径
                        self.lineEdit_recordfile.setText(
                            params['path_recordfile'])
                    else:
                        pass
                # 状态栏显示
                self.statusbar.showMessage(
                    '加载参数完成！参数文件路径：{}'.format(os.path.abspath(filepath)))
            except:
                # 状态栏显示
                self.statusbar.showMessage('参数文件解析出错！')
                return

    def is_ip_legal(self, ip: str) -> bool:
        '''检测IP是否合法'''
        # 检查IP地址是否合法
        pattern = r"((?:(?:25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d)))\.){3}(?:25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d)))$)"
        return re.match(pattern, ip)

    def auto_fill_endip(self):
        '''自动填写结束IP'''
        # 获取起始IP
        startip = self.lineEdit_startIP.text()
        # 检查IP地址是否合法
        self.ipislegal = self.is_ip_legal(startip)
        # 判断
        if self.ipislegal:  # 合法
            # 分割
            ip_list = startip.split('.')
            # 改写
            ip_list[3] = '255'
            # 组合
            endip = '.'.join(ip_list)
            # 填写
            self.lineEdit_endIP.setText(endip)
            # 状态栏显示
            self.statusbar.showMessage('')
        else:
            self.lineEdit_endIP.setText('')
            # 状态栏显示
            self.statusbar.showMessage('IP地址不合法！')

    def ping_setting(self):
        '''设置Ping请求数'''
        num, ok = QInputDialog.getInt(
            self, '设置', '输入Ping请求数：', self.ping_num, 1, 100, 1)
        if ok:
            self.ping_num = num

    def reset_ui(self):
        ''' 初始化窗口IP窗格为灰色背景 '''
        for item in self.iplabel_list:
            item.setStyleSheet("background-color: rgb(203, 203, 203);")

    def set_ui(self, result: bool, ip: str):
        '''设置窗口颜色 result：线程ping的结果 ip：对应的IP地址'''
        # 添加检测结果
        self.result_list.append(result)
        # 获取索引
        index = int(ip.split('.')[3])
        # 判断结果
        if result:
            # 设置背景为绿色
            self.iplabel_list[index].setStyleSheet(
                "background-color: rgb(85, 170, 127);")
        else:
            # 设置背景为红色
            self.iplabel_list[index].setStyleSheet(
                "background-color: rgb(255, 142, 119);")

        # 统计结果
        frequency = Counter(self.result_list)
        self.statusbar.showMessage(str(frequency))

    def is_ip_online(self, ip: str):
        '''检测IP是否在线'''
        # 命令
        cmd = "ping {} -n {} -w 600".format(ip, self.ping_num)
        # 执行命令
        result, error = self.popen(cmd)
        # 判断结果
        if result == 'error':
            # 出错
            # self.set_ui(False, ip)
            self._ping_signal.emit(False, ip)
        else:
            # 在线
            if 'TTL' in result.upper():
                # self.set_ui(True, ip)
                self._ping_signal.emit(True, ip)
            else:
                # self.set_ui(False, ip)
                self._ping_signal.emit(False, ip)

    def start_ping(self):
        '''开始Ping检测'''
        self.result_list = []
        self.statusbar.showMessage('检测中...')
        # 获取IP
        startip_str = self.lineEdit_startIP.text()
        endip_str = self.lineEdit_endIP.text()
        # 检查IP地址是否合法
        ipislegal = self.is_ip_legal(startip_str)
        ipislegal2 = self.is_ip_legal(endip_str)
        # 判断
        if ipislegal and ipislegal2:  # 合法
            # 初始化格子
            self.reset_ui()
            # 获取起始IP
            startip = startip_str.split('.')
            # 获取结束IP
            endip = endip_str.split('.')
            tmp_ip = startip

            # 多线程检测
            pthread_list = []
            for i in range(int(startip[3]), int(endip[3]) + 1):
                # 当前IP
                tmp_ip[3] = str(i)
                ip = '.'.join(tmp_ip)
                # 创建线程
                pthread_list.append(
                    Thread(target=self.is_ip_online, args=(ip,)))
            # 遍历启动线程
            for item in pthread_list:
                # 设置守护线程-主线程停止了，子线程也会停止
                item.setDaemon(True)
                item.start()
        else:
            # 显示弹窗
            QMessageBox.warning(self, '错误', 'IP地址不合法！')
            if not ipislegal:
                self.lineEdit_startIP.setFocus()
                self.lineEdit_startIP.selectAll()
            else:
                self.lineEdit_endIP.setFocus()
                self.lineEdit_endIP.selectAll()
            return

    def syslicence(self):
        '''查看系统许可证状态'''
        self.carryout('slmgr.vbs -dlv')

    def syslicence2(self):
        '''查看系统许可证状态（简化版）'''
        self.carryout('slmgr.vbs -dli')

    def sysactive(self):
        '''查看系统激活信息'''
        self.carryout('slmgr.vbs -xpr')

    def get_wifi_list(self) -> list[Wifi]:
        '''扫描获取附近WiFi列表'''
        # 获取WiFi列表
        result, error = self.popen('netsh wlan show networks mode=bssid')
        # 判断
        if result == 'error':
            self.statusbar.showMessage('wifi扫描出错！')
            return []

        # 根据回车分割
        alist = result.split('\n')
        # 去头去尾
        clist = alist[4:-1]
        # 分隔
        step = 11
        dlist = [clist[i:i+step] for i in range(0, len(clist), step)]

        wifi_list = []
        try:
            # 遍历
            for item in dlist:
                # 分割获取信息
                ssid = item[0].split(':')[1][1:].encode('gbk').decode("utf-8")
                idcheck = item[2].split(':')[1][1:]
                pwd = item[3].split(':')[1][1:]
                bssid = item[4][(item[4].index(':')+1):]
                network = item[5].split(':')[1][1:]
                networktype = item[6].split(':')[1][1:]
                channel = item[7].split(':')[1][1:]
                # 创建WiFi对象
                wifi = Wifi(ssid, idcheck, pwd, bssid,
                            network, networktype, channel)
                wifi_list.append(wifi)
        except:
            self.statusbar.showMessage('wifi扫描失败！')
            # 返回
            return wifi_list
        # 返回
        return wifi_list

    def wifiscan(self):
        '''扫描附近的WiFi'''
        self.statusbar.showMessage('wifi扫描中...')
        # 获取WiFi列表
        wifi_list = self.get_wifi_list()
        # 判断
        if len(wifi_list) == 0:
            return
        # 组合美化
        x = PrettyTable(["名称", "身份验证", "加密", "物理地址", "信号", "无线电类型", "信道"])
        # 遍历添加
        for i in wifi_list:
            x.add_row(i.toList())
        # 输出-换行，追加
        self.log(self.textEdit_cmd, str(x), True, True)
        self.statusbar.showMessage('wifi扫描完成！')

    def get_pwd_by_name(self, wifiname: str) -> str:
        '''根据WIFI名字获取密码'''
        pwd = '无'
        # TODO...WIFI名称有空格会获取不了密码
        # 命令行
        order = "netsh wlan show profile name={} key=clear".format(wifiname)
        # 执行命令
        result, error = self.popen(order)
        # 判断
        if result == 'error':
            self.statusbar.showMessage('wifi密码获取出错！')
            return ''
        # 根据回车分割
        alist = result.split('\n')
        # 遍历
        for a in alist:
            if '关键内容' in a:
                index = a.index(':')
                pwd = a[index+2:]
        # 返回密码
        return pwd

    def wifipwd(self):
        '''查看连接过的WiFi密码'''
        # 获取连接过的WiFi列表
        result, error = self.popen('netsh wlan show profiles')
        # 判断
        if result == 'error':
            self.statusbar.showMessage('wifi列表获取出错！')
            return

        # 根据回车分割
        alist = result.split('\n')
        # 筛选-获取所有WiFi名字
        wifiname_list = []
        for b in alist:
            if '所有用户配置文件' in b:
                wifiname_list.append(b[15:])
        # 判断
        if len(wifiname_list) == 0:
            return

        # WiFi密码键值对
        wifimap = []
        # 遍历所有WIFI
        for wifiname in wifiname_list:
            # 获取密码
            pwd = self.get_pwd_by_name(wifiname)
            # 判断
            if len(pwd) == 0:
                return
            # 加入列表
            wifimap.append((wifiname, pwd))

        # 判断
        if len(wifimap) == 0:
            return
        # 组合美化
        x = PrettyTable(["WiFi名称", "WiFi密码"])
        # 遍历添加
        for name, password in wifimap:
            x.add_row([name, password])
        # 输出-换行，追加
        self.log(self.textEdit_cmd, str(x), True, True)
        self.statusbar.showMessage('wifi获取完成！')

    def carryout(self, cmd: str):
        '''执行命令'''
        # 输出信息
        self.log(self.textEdit_cmd, cmd)
        # 执行命令
        result, error = self.popen(cmd)
        # 判断
        if len(result) != 0:
            self.log(self.textEdit_cmd, result)
        if len(error) != 0:
            self.log(self.textEdit_cmd, error)

    def select_dir(self, dir_type: str, lineEdit: QLineEdit):
        '''选择目录'''
        # 弹出文件选择器
        dirpath = QFileDialog.getExistingDirectory(
            self, "选择{}目录".format(dir_type), os.getcwd())
        # 判断
        if len(dirpath) != 0:
            # 目录的路径
            lineEdit.setText(dirpath)
            # 状态栏显示
            self.statusbar.showMessage('{}目录选择完成！'.format(dir_type))

    def select_adir(self):
        '''选择A目录'''
        self.select_dir('A', self.lineEdit_adir)

    def select_bdir(self):
        '''选择B目录'''
        self.select_dir('B', self.lineEdit_bdir)

    def select_monitordir(self):
        '''选择被监控的目录'''
        self.select_dir('被监控的', self.lineEdit_mdir)

    def select_recordfile(self):
        '''选择记录文件'''
        # 弹出文件选择器
        filepath, filetype = QFileDialog.getOpenFileName(
            self, "请选择记录文件", os.getcwd(), "TXT File (*.txt)")
        # 判断
        if filepath != '':
            # 输出路径
            self.lineEdit_recordfile.setText(filepath)
            # 状态栏显示
            self.statusbar.showMessage('记录文件选择完成！')

    def clear_outputArea(self):
        '''清空输出区'''
        self.textEdit_deletedfile.setText('')
        self.textEdit_newfile.setText('')
        # 清空状态栏显示
        self.statusbar.showMessage('')

    def start_monitor(self):
        '''遍历被监控目录与记录文件，开始对比'''
        # 获取目录路径
        path_md = self.lineEdit_mdir.text()
        path_rf = self.lineEdit_recordfile.text()
        # 判断
        if (len(path_md) != 0) and (len(path_rf) != 0):
            # 获取所有文件
            try:
                self.statusbar.showMessage('遍历被监控的目录中...')
                mlist = self.get_all(path_md)
            except:
                self.textEdit_deletedfile.setText('被监控的目录不存在！')
                return
            try:
                self.statusbar.showMessage('读取记录文件中...')
                # 读取记录文件
                with open(path_rf, 'r', encoding='utf-8') as f:
                    rlist = f.read().split('\n')
            except:
                self.textEdit_newfile.setText('记录文件不存在！')
                return

            self.statusbar.showMessage('对比中...')
            # 目录独有-新增文件
            mq = list(set(mlist).difference(set(rlist)))
            mq.sort()
            # 记录文件独有-被删除文件
            rq = list(set(rlist).difference(set(mlist)))
            rq.sort()

            # 输出
            self.textEdit_newfile.setText('')
            self.textEdit_deletedfile.setText('')
            _time.sleep(3)
            for m in mq:
                self.textEdit_newfile.append(m)
            for r in rq:
                self.textEdit_deletedfile.append(r)
            # 状态栏显示
            self.statusbar.showMessage('文件变化监控对比完成！')

    def refresh(self):
        '''更新记录文件'''
        # 获取目录路径
        path_md = self.lineEdit_mdir.text()
        path_rf = self.lineEdit_recordfile.text()
        # 判断
        if (len(path_md) != 0) and (len(path_rf) != 0):
            # 获取所有文件
            try:
                self.statusbar.showMessage('遍历被监控的目录中...')
                mlist = self.get_all(path_md)
                mlist.sort()
            except:
                self.textEdit_deletedfile.setText('被监控的目录不存在！')
                return

            self.statusbar.showMessage('记录文件更新中...')
            # 打开文件
            with open(path_rf, 'w+', encoding='utf-8') as f:
                # 写入
                f.write('\n'.join(mlist))
            # 状态栏显示
            self.statusbar.showMessage('更新记录文件完成！')

    def get_all(self, rootdir: str) -> list:
        '''获取目录所有文件'''
        # 结果集
        result_list = []
        # 列出文件夹下所有的目录与文件
        file_list = os.listdir(rootdir)
        # 遍历
        for name in file_list:
            # 获取绝对路径
            fullname = os.path.join(rootdir, name)
            # 判断是否为目录
            if os.path.isdir(fullname):
                result_list.append(fullname)
                # 递归遍历
                result_list.extend(self.get_all(fullname))
            else:
                result_list.append(fullname)
        # 返回
        return result_list

    def compare(self):
        '''A目录与B目录文件差异，开始对比'''
        # 集合
        a = []
        b = []
        # 获取目录路径
        dir_a = self.lineEdit_adir.text()
        dir_b = self.lineEdit_bdir.text()
        # 判断
        if (len(dir_a) != 0) and (len(dir_b) != 0):
            # 获取所有文件
            try:
                self.statusbar.showMessage('遍历A目录中...')
                alist = self.get_all(dir_a)
            except:
                self.textEdit_adir.setText('A目录不存在！')
                return
            try:
                self.statusbar.showMessage('遍历B目录中...')
                blist = self.get_all(dir_b)
            except:
                self.textEdit_bdir.setText('B目录不存在！')
                return

            # 去头处理
            for i in alist:
                a.append(i[len(dir_a)+1:])
            for j in blist:
                b.append(j[len(dir_b)+1:])

            # 状态栏显示
            self.statusbar.showMessage('对比中...')
            # A独有
            aq = list(set(a).difference(set(b)))
            aq.sort()
            # B独有
            bq = list(set(b).difference(set(a)))
            bq.sort()

            # 输出
            self.textEdit_adir.setText('')
            self.textEdit_bdir.setText('')
            for m in aq:
                self.textEdit_adir.append(m)
            for n in bq:
                self.textEdit_bdir.append(n)
            # 状态栏显示
            self.statusbar.showMessage('文件目录对比完成！')

    def popen(self, cmd: str) -> tuple[str, str]:
        '''执行系统命令'''
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            # 执行命令
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, shell=True, startupinfo=startupinfo,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            result = process.stdout.read()
            process.stdout.close()
            error = process.stderr.read()
            process.stderr.close()

            # 输出运行结果
            # print(result)
            # 若程序没有异常，则只输出空行
            # print(error)
        except:
            return 'error', 'error'
        # 返回运行结果
        return result, error

    def nowtime(self) -> str:
        '''当前时间'''
        return str(_time.strftime(
            '%Y-%m-%d %H:%M:%S', _time.localtime(_time.time())))

    def log(self, textEdit: QTextEdit, message: str, wrap: bool = False, add: bool = True):
        '''输出日志信息'''
        mess = "<font color='orange'>[</font><font color='blue'>"+self.nowtime() + \
            "</font><font color='orange'>]</font><font color='green'>"+message+"</font>"
        # 判断是否追加写入
        if not add:
            # 清空
            textEdit.setText('')

        # 判断首行是否换行
        if wrap:
            # 换行
            self.log(textEdit, '\n')
            # 追加写入
            textEdit.append(message)
        elif not wrap:
            # 直接写入
            textEdit.append(mess)
        # 移动光标到最底
        textEdit.moveCursor(QTextCursor.End)

    def has_network(self) -> bool:
        '''判断有无网络'''
        result, error = self.popen('ping baidu.com')
        if 'TTL' in result:
            return True
        else:
            return False

    def clear_table(self):
        '''清空结果表格'''
        # 返回表格总行数
        num = self.model.rowCount()
        # 遍历
        for i in range(num):
            # 移除第一行
            self.model.removeRow(0)

    def update_table(self,  date: str, title: str):
        '''更新表格'''
        # 添加新一行
        self.model.appendRow(
            [QStandardItem(date), QStandardItem(title)])

    def gen_urls(self, pageNum: int) -> list:
        '''生成地址链接'''
        self.statusbar.showMessage('正在生成链接...')
        # 地址头
        url_head = 'https://www.douban.com/group/gz020/discussion?start='
        # 地址集
        urls = []
        # 循环生成
        for i in range(0, pageNum):
            # 地址
            url = url_head+str(i*25)
            urls.append(url)

        # 返回地址集
        return urls

    def get_content(self, url: str) -> str:
        '''获取单页的内容'''
        # 结果
        result = ('',)
        # 添加代理头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3741.400 QQBrowser/10.5.3863.400'
        }

        try:
            # 获取结果
            result = requests.get(url=url, headers=headers, timeout=5).text
            # 解析文档
            document = BeautifulSoup(result, 'html.parser')
            # 获取标题
            td_title = document.select('td[class="title"]')

            # 遍历
            for t in td_title:
                # 获取链接
                href = t.a.get('href')
                # 获取标题
                ttl = t.a.get('title')
                # 清除表情
                title = emoji.demojize(ttl)
                # 获取日期
                date = t.parent.contents[7].get_text()
                # 结果
                r_str = date+'@@@'+title+'@@@'+href
                result = (r_str,)
        except:
            # 按钮可用
            self.pushButton_crawl.setEnabled(True)
            self.statusbar.showMessage('爬取失败！网络连接失败或网络连接超时！请检查您的网络配置！')
            return result

        # 返回结果
        return result

    def contains(self, title: str, conditions: list) -> bool:
        '''判断是否符合筛选条件'''
        # 判断长度，是否为空
        if len(conditions) == 0:
            return True
        else:
            # 遍历判断
            for condition in conditions:
                if condition in title:
                    return True
        # 返回
        return False

    def start_crawl(self):
        '''开始爬取豆瓣租房信息'''
        self.statusbar.showMessage('')
        # 获取筛选条件
        strings = self.lineEdit_filter.text()
        # 判断
        if len(strings) == 0:
            self.statusbar.showMessage('筛选条件不能为空！')
            return

        # 判断有无联网
        if not self.has_network:
            self.statusbar.showMessage('无网络！')
            return

        # 禁用按钮
        self.pushButton_crawl.setEnabled(False)
        # 结果集
        result_list = []
        # 线程集
        threads = []

        # 分割
        conditions = strings.split('+')
        # 获取页数
        pageNum = self.pageBox.value()

        # 清空表格
        self.clear_table()
        self.url_dict = {}

        # 生成链接
        urls = self.gen_urls(pageNum)

        # 获取内容信息
        for i in urls:
            thread = MyThread(self.get_content, (i,))
            threads.append(thread)

        self.statusbar.showMessage('正在爬取中...')

        # 运行线程
        for t in threads:
            t.start()

        # 等待线程结束
        for t in threads:
            t.join()

        # 获取结果
        for t in threads:
            for res in t.get_result():
                if len(res) != 0:
                    result_list.append(res)

        # 显示结果
        self.statusbar.showMessage('正在判断结果中...')
        index = 1
        for r in result_list:
            # 分割
            rr = r.split('@@@')
            if len(rr) >= 3:
                # 判断是否符合条件
                if self.contains(rr[1], conditions):
                    # 地址存入字典
                    self.url_dict[str(index)] = rr[2]
                    index = index+1
                    # 更新表格
                    self.update_table(rr[0], rr[1])

        # 按钮可用
        self.pushButton_crawl.setEnabled(True)
        self.statusbar.showMessage('爬取完成！')

    def open_url(self):
        '''打开网页'''
        # 当前行号
        currentRowNum = self.table.currentIndex().row()+1

        # 判断-选中项不为空且结果字典不为空
        if (currentRowNum != -1) and bool(self.url_dict):
            try:
                # 获取链接
                url = self.url_dict[str(currentRowNum)]
                # 打开链接
                webbrowser.open(url)
            except:
                self.statusbar.showMessage('网址链接打开失败！')
                return


if __name__ == '__main__':
    # 创建应用
    app = QApplication(sys.argv)
    # 设置界面风格
    app.setStyle(QStyleFactory.create('Fusion'))
    # 创建窗口
    mainWindow = ToolBox(app)
    # 显示
    mainWindow.show()
    # 退出
    sys.exit(app.exec_())
