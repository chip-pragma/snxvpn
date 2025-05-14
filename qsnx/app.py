import sys
from abc import ABC, abstractmethod
from typing import Self, Any, cast

from PySide6 import QtWidgets as qw, QtGui as qg, QtCore as qc
from PySide6.QtCore import Qt, QPointList


def _theme_pixmap(name: str, size: qc.QSize, pixel_ratio: float) -> qg.QPixmap:
    print(f'>> "{name}" ({size.width()}x{size.height()}) ^{pixel_ratio}')
    return qg.QIcon.fromTheme(name).pixmap(size, pixel_ratio)


def _all_none(*objects: Any) -> bool:
    return all(map(lambda i: i is None, objects))


def _monospaced_font() -> qg.QFont:
    return qg.QFontDatabase.systemFont(qg.QFontDatabase.SystemFont.FixedFont)


def _antialiased_painter(pd: qg.QPaintDevice, *, pen: qg.QPen = None, brush: qg.QBrush = None) -> qg.QPainter:
    p = qg.QPainter(pd)
    p.setRenderHint(qg.QPainter.RenderHint.Antialiasing, on=True)
    if pen:
        p.setPen(pen)
    if brush:
        p.setBrush(brush)
    return p


Size = qc.QSize | tuple[int, int]


class BaseWidget(qw.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayout(self._setup_ui())

    @abstractmethod
    def _setup_ui(self) -> qw.QLayout:
        pass

    def event(self, event: qc.QEvent):
        if event.type() == 222:  # DevicePixelRatioChange
            self.device_pixel_ratio_changed(event)
        return super().event(event)

    def device_pixel_ratio_changed(self, event: qc.QEvent):
        pass


class CredentialLineEdit(BaseWidget):
    _echo_icons = ('view-visible', 'view-hidden')
    _keep_icons = ('changes-allow-symbolic', 'changes-prevent-symbolic')

    echo_changed = qc.Signal(bool)
    keep_changed = qc.Signal(bool)

    def __init__(self, *args, password=True, **kwargs):
        self._password_mode = password
        super().__init__(*args, **kwargs)
        self._on_echo_mode_switched()
        self._on_keep_switched()

    def _setup_ui(self) -> qw.QLayout:
        # input
        w_input = qw.QLineEdit()
        w_input.setFont(_monospaced_font())
        _leh = w_input.sizeHint().height()
        # switcher
        w_echo = qw.QPushButton()
        w_echo.setToolTip('Echo secret')
        w_echo.setFixedSize(_leh, _leh)
        w_echo.setVisible(self._password_mode)
        w_echo.setCheckable(True)
        w_echo.clicked.connect(self._on_echo_mode_switched)
        w_echo.clicked.connect(self.echo_changed)
        # keeper
        w_keep = qw.QPushButton()
        w_keep.setToolTip('Keep and lock')
        w_keep.setFixedSize(_leh, _leh)
        w_keep.setCheckable(True)
        w_keep.clicked.connect(self._on_keep_switched)
        w_keep.clicked.connect(self.keep_changed)
        # attributes
        self._input = w_input
        self._echo_btn = w_echo
        self._keep_btn = w_keep
        # layout
        layout = qw.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(w_keep)
        layout.addWidget(w_input)
        layout.addWidget(w_echo)

        return layout

    def _on_echo_mode_switched(self):
        EM = qw.QLineEdit.EchoMode
        checked = self._echo_btn.isChecked()
        self._input.setEchoMode(EM.Normal if (not self._password_mode or checked) else EM.Password)
        self._echo_btn.setIcon(qg.QIcon.fromTheme(self._echo_icons[int(checked)]))

    def _on_keep_switched(self):
        checked = self._keep_btn.isChecked()
        self._keep_btn.setIcon(qg.QIcon.fromTheme(self._keep_icons[int(checked)]))
        self._input.setReadOnly(checked)

    def input_line_edit(self):
        return self._input

    def value(self) -> str:
        return self._input.text()


class DebugWidget(BaseWidget):
    _p_line_color = Qt.GlobalColor.darkYellow

    def paintEvent(self, event: qg.QPaintEvent):
        # init
        rect = self.rect() - qc.QMargins(0, 1, 0, 1)
        pen = qg.QPen(self._p_line_color, 1)
        brush = qg.QBrush(Qt.BrushStyle.BDiagPattern)
        brush.setColor(self._p_line_color)
        # draw
        p = _antialiased_painter(self, pen=pen, brush=brush)
        p.setRenderHint(qg.QPainter.RenderHint.Antialiasing, on=True)
        p.drawRoundedRect(rect, 6, 6)
        p.end()
        # inherited
        super().paintEvent(event)


class DebugControls(DebugWidget):
    next_page_clicked = qc.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._page_switcher = w_switcher = qw.QPushButton('Next page')
        w_switcher.clicked.connect(self.next_page_clicked)

        layout = qw.QHBoxLayout()
        layout.addWidget(w_switcher)
        layout.addStretch(2)

        self.setLayout(layout)


class PageWidget(BaseWidget):
    _offset = 0.45

    def __init__(self, *args, background: qg.QPixmap = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._bg = background

    def set_background(self, pix: qg.QPixmap | None):
        self._bg = pix

    def background(self) -> qg.QPixmap | None:
        return self._bg

    def paintEvent(self, event: qg.QPaintEvent):
        if self._bg is None:
            super().paintEvent(event)
            return
        # init
        position = self.rect().bottomRight() - self._bg.rect().bottomRight() * (1 - self._offset)
        # paint
        p = _antialiased_painter(self)
        p.setOpacity(0.05)
        p.drawPixmap(position, self._bg)
        # p.draw
        p.end()
        # inherited
        super().paintEvent(event)


class CredentialsPage(PageWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Credentials')

        lbl_login = qw.QLabel('Login')
        self._user = CredentialLineEdit(password=False)
        lbl_password = qw.QLabel('Password')
        self._password = CredentialLineEdit()

        layout = qw.QVBoxLayout()
        layout.addWidget(lbl_login)
        layout.addWidget(self._user)
        layout.addWidget(lbl_password)
        layout.addWidget(self._password)
        layout.addStretch(2)

        self.setLayout(layout)

    def device_pixel_ratio_changed(self, event: qc.QEvent):
        self.set_background(_theme_pixmap('system-user-list', qc.QSize(200, 200), self.devicePixelRatioF()))

    # def show(self):
    #     self._user.input_line_edit().setFocus()
    #     super().show()

    def clear(self):
        self._user.input_line_edit().clear()
        self._password.input_line_edit().clear()

    def user_name(self) -> str:
        return self._user.value()

    def password(self) -> str:
        return self._password.value()


class OtpPage(PageWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('One-Time Password')

        self._line_edit = w_lned = qw.QLineEdit()

        font = qg.QFont(_monospaced_font())
        font.setPointSize(20)
        font.setLetterSpacing(qg.QFont.SpacingType.PercentageSpacing, 175)
        w_lned.setFont(font)
        w_lned.setAlignment(Qt.AlignmentFlag.AlignCenter)
        w_lned.setMaxLength(6)

        # w_icon = qw.QLabel(pixmap=_theme_pixmap('alarm-symbolic', qc.QSize(32, 32), self.devicePixelRatioF()))

        layout = qw.QVBoxLayout()
        # layout.addWidget(w_icon, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(w_lned, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addStretch(2)

        self.setLayout(layout)
        self.show()

    def device_pixel_ratio_changed(self, event: qc.QEvent):
        self.set_background(_theme_pixmap('alarm-symbolic', qc.QSize(200, 200), self.devicePixelRatioF()))

    # def show(self):
    #     self._line_edit.setFocus()
    #     super().show()


class MainWindow(BaseWidget):
    def __init__(self, title: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowIcon(qg.QIcon.fromTheme('network-vpn'))
        self.setWindowTitle(title)
        self.setFixedWidth(350)

        self._credentials_page = CredentialsPage()
        self._otp_page = OtpPage()

        self._pages = w_pages = qw.QGroupBox()
        w_pages.setMinimumHeight(200)

        self._pages_layout = l_pages = qw.QStackedLayout()
        l_pages.currentChanged.connect(self._page_changed)
        l_pages.addWidget(self._credentials_page)
        l_pages.addWidget(self._otp_page)

        w_pages.setLayout(l_pages)

        l_buttons = qw.QHBoxLayout()
        l_buttons.addWidget(qw.QPushButton('Cancel'), alignment=Qt.AlignmentFlag.AlignLeft)
        l_buttons.addWidget(qw.QPushButton('Connect'), alignment=Qt.AlignmentFlag.AlignRight)
        l_buttons.addWidget(qw.QPushButton('OK'), alignment=Qt.AlignmentFlag.AlignRight)

        # debug
        self._debug_panel = DebugControls()
        self._debug_panel.next_page_clicked.connect(self._switch_page)
        # /debug

        layout = qw.QVBoxLayout()
        layout.addWidget(w_pages, stretch=2)
        layout.addLayout(l_buttons)
        layout.addWidget(self._debug_panel)

        self.setLayout(layout)
        self.show()
        layout.setSpacing(layout.contentsMargins().top())

    def _page_changed(self, index: int):
        if index == (-1):
            return
        self._pages.setTitle(self._pages_layout.widget(index).windowTitle())

    def _switch_page(self):
        next_index = (self._pages_layout.currentIndex() + 1) % self._pages_layout.count()
        self._pages_layout.setCurrentIndex(next_index)


def main():
    app = qw.QApplication(sys.argv)
    app.setStyle(qw.QStyleFactory.create('Fusion'))
    app.setApplicationVersion('1.5.2-dev')
    app.setApplicationName('qSNX')

    _ = MainWindow(f'{app.applicationName()} {app.applicationVersion()}')

    return app.exec()


if __name__ == '__main__':
    main()
