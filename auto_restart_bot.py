from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
import winreg
import os
import shutil

class MiniAutoStartManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AutoStart Alert")
        self.setGeometry(200, 200, 300, 100)
        self.setStyleSheet("background-color: #2C2C2C; color: #FFFFFF;")
        self.layout = QVBoxLayout()
        self.label = QLabel("Monitoring new autostart entries...")
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

        # Tray icon setup with custom icon
        self.tray_icon = QSystemTrayIcon(QIcon(r"D:\proecte\foto.ico"), self)
        self.tray_icon.setToolTip("AutoStart Manager")
        self.tray_icon.show()

        # Tray menu
        tray_menu = QMenu()
        exit_action = tray_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        self.tray_icon.setContextMenu(tray_menu)

        # Save previous entries to compare
        self.previous_entries = set(self.get_registry_autostart_entries())

        # Timer to check for new entries
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_new_entries)
        self.timer.start(5000)  # Check every 5 seconds

        # Add this program to autostart and ensure desktop shortcut
        exe_path = os.path.abspath(__file__)
        self.add_to_autostart("AutoStart Manager", exe_path)
        self.ensure_desktop_shortcut("AutoStart Manager", exe_path)

    def get_registry_autostart_entries(self):
        entries = set()
        reg_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run")
        ]
        for hive, path in reg_paths:
            try:
                with winreg.OpenKey(hive, path, 0, winreg.KEY_READ) as reg_key:
                    i = 0
                    while True:
                        try:
                            name, _, _ = winreg.EnumValue(reg_key, i)
                            entries.add(name)
                            i += 1
                        except OSError:
                            break
            except Exception as e:
                print(f"Error reading registry: {e}")
        return entries

    def check_new_entries(self):
        current_entries = set(self.get_registry_autostart_entries())
        new_entries = current_entries - self.previous_entries

        for entry in new_entries:
            self.tray_icon.showMessage(
                "New AutoStart Entry",
                f"A new program '{entry}' has been added to autostart. Allow it?",
                QSystemTrayIcon.Information,
                5000
            )

            # Create a QMessageBox that always appears on top
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("New AutoStart Entry")
            msg_box.setText(f"A new program '{entry}' has been added to autostart. Allow it?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setWindowModality(Qt.ApplicationModal)
            msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowStaysOnTopHint)

            reply = msg_box.exec_()
            if reply == QMessageBox.No:
                self.remove_registry_autostart_item(entry)

        self.previous_entries = current_entries

    def remove_registry_autostart_item(self, name):
        reg_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run")
        ]
        for hive, path in reg_paths:
            try:
                with winreg.OpenKey(hive, path, 0, winreg.KEY_WRITE) as reg_key:
                    winreg.DeleteValue(reg_key, name)
                    print(f"Removed {name} from {path}")
                    return True
            except FileNotFoundError:
                continue
            except Exception as e:
                print(f"Error removing {name}: {e}")
        return False

    def add_to_autostart(self, app_name, exe_path):
        """Добавляет приложение в автозагрузку."""
        reg_path = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE) as reg_key:
                winreg.SetValueEx(reg_key, app_name, 0, winreg.REG_SZ, exe_path)
                print(f"{app_name} added to autostart successfully.")
                return True
        except Exception as e:
            print(f"Error adding {app_name} to autostart: {e}")
            return False

    def ensure_desktop_shortcut(self, app_name, exe_path):
        """Создает ярлык программы на рабочем столе."""
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcut_path = os.path.join(desktop_path, f"{app_name}.lnk")

        if not os.path.exists(shortcut_path):
            try:
                import pythoncom
                from win32com.client import Dispatch

                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortcut(shortcut_path)
                shortcut.TargetPath = exe_path
                shortcut.WorkingDirectory = os.path.dirname(exe_path)
                shortcut.IconLocation = r"D:\proecte\foto.ico"
                shortcut.save()
                print(f"Shortcut created at {shortcut_path}")
            except Exception as e:
                print(f"Error creating desktop shortcut: {e}")

if __name__ == "__main__":
    app = QApplication([])
    manager = MiniAutoStartManager()
    manager.show()
    app.exec()
