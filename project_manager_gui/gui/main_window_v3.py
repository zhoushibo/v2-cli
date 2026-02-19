# -*- coding: utf-8 -*-
"""
Main Window v3 - With Service Manager
OpenClaw Control Center
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QStatusBar, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from .dashboard import Dashboard
from .project_list import ProjectList
from .service_manager import ServiceManagerPanel
from core.health_checker import HealthChecker
from core.project_manager import ProjectManager
from core.state_reader import get_projects_with_completion


class MainWindow(QMainWindow):
    """Main window with dashboard, projects, and service manager"""
    
    def __init__(self, project_manager: ProjectManager):
        super().__init__()
        self.project_manager = project_manager
        self.health_checker = HealthChecker()
        
        self.init_ui()
        self.configure_services()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("OpenClaw Control Center")
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        central_widget.setLayout(main_layout)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 0;
            }
            QTabBar::tab {
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #f5f5f5;
            }
        """)
        
        # Dashboard tab
        self.dashboard = Dashboard(self.health_checker)
        # Configure default services for dashboard
        default_services = {
            "Gateway": {
                "type": "websocket",
                "port": 8001,
                "url": "ws://127.0.0.1:8001",
                "description": "统一 AI Provider Gateway (6 个 Provider)"
            },
            "Knowledge Base": {
                "type": "web",
                "port": 8501,
                "url": "http://localhost:8501",
                "description": "知识库管理系统 (ChromaDB + FTS5)"
            },
            "V2 Learning": {
                "type": "module",
                "port": None,
                "url": None,
                "description": "V2 学习系统 (3 Worker 并发)"
            }
        }
        self.dashboard.configure_services(default_services)
        self.tabs.addTab(self.dashboard, "📊 仪表盘")
        
        # Service Manager tab
        self.service_manager = ServiceManagerPanel()
        self.tabs.addTab(self.service_manager, "🔧 服务管理")
        
        # Project Management tab
        self.project_list = ProjectList()
        self.project_list.project_manager = self.project_manager
        
        # Load projects from STATE.json with completion data
        projects = get_projects_with_completion()
        self.project_list.update_projects(projects)
        self.tabs.addTab(self.project_list, "📁 项目管理")
        
        main_layout.addWidget(self.tabs)
        
        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪 | Gateway:8001 | 知识库:8501")
    
    def configure_services(self):
        """Configure services"""
        self.statusBar.showMessage("正在初始化服务...")
        
        # Check if services are running
        QTimer.singleShot(1000, self.check_initial_status)
    
    def check_initial_status(self):
        """Check initial service status"""
        from services.gateway_service import GatewayService, KnowledgeBaseService
        
        gateway = GatewayService()
        kb = KnowledgeBaseService()
        
        running_services = []
        if gateway.is_running():
            running_services.append("Gateway")
        if kb.is_running():
            running_services.append("知识库 Web UI")
        
        if running_services:
            msg = f"已运行：{', '.join(running_services)}"
        else:
            msg = "就绪 | 所有服务已停止"
        
        self.statusBar.showMessage(msg)
        
        # Show welcome message if no services running
        if not running_services:
            QMessageBox.information(
                self,
                "欢迎",
                "欢迎使用 OpenClaw Control Center！\n\n"
                "切换到「服务管理」标签页启动服务：\n"
                "• Gateway 服务 (端口 8001)\n"
                "• 知识库 Web UI (端口 8501)\n\n"
                "或者在「仪表盘」查看系统状态。"
            )
    
    def closeEvent(self, event):
        """Handle window close"""
        reply = QMessageBox.question(
            self,
            '确认退出',
            "确定要关闭 OpenClaw Control Center 吗？\n\n"
            "注意：正在运行的服务不会自动停止。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
