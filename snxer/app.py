import sys
from typing import Self, Any, cast

from PySide6 import QtWidgets as qw, QtGui as qg, QtCore as qc
from PySide6.QtCore import Qt


def _theme_pixmap(name: str, w: int, h: int) -> qg.QPixmap:
    return qg.QIcon.fromTheme(name).pixmap(w, h)


def _all_none(*objects: Any) -> bool:
    return all(map(lambda i: i is None, objects))


Size = qc.QSize | tuple[int, int]


class InputForm(qw.QWidget):
    _default_size = (32, 32)
    _visible_icons = ('view-visible', 'view-hidden')

    def __init__(self, parent: qw.QWidget = None, *args,
                 text: str, icon: str, password: bool, otp_mode=False, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._show_secret = not password
        # decoration
        w_icon = self._lbl_icon = qw.QLabel(pixmap=_theme_pixmap(icon, *self._default_size))
        w_text = self._lbl_text = qw.QLabel(text)
        # credential input
        w_input = self._le_input = qw.QLineEdit()
        w_input.setFont(qg.QFontDatabase.systemFont(qg.QFontDatabase.SystemFont.FixedFont))
        # show/hide button
        w_vision = self._btn_vision = qw.QPushButton()
        w_vision.setToolTip('Switch visibility')
        w_vision.setVisible(password)
        w_vision.clicked.connect(self._switch_visibility)
        # layout
        grid = qw.QGridLayout()
        grid.addWidget(w_icon, 0, 0, 2, 1, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        grid.addWidget(w_text, 0, 1, 1, 2)
        grid.addWidget(w_input, 1, 1)
        grid.addWidget(w_vision, 1, 2)
        # apply
        self._setup_visibility()
        if otp_mode:
            self._set_otp_mode()
        self.setLayout(grid)
        self.show()

    def _switch_visibility(self):
        self._show_secret = not self._show_secret
        self._setup_visibility()

    def _setup_visibility(self):
        self._le_input.setEchoMode(qw.QLineEdit.EchoMode.Normal
                                   if self._show_secret else
                                   qw.QLineEdit.EchoMode.Password)
        self._btn_vision.setIcon(qg.QIcon.fromTheme(self._visible_icons[int(self._show_secret)]))

    def _set_otp_mode(self):
        font = qg.QFont(qg.QFontDatabase.systemFont(qg.QFontDatabase.SystemFont.FixedFont))
        font.setPointSize(20)
        font.setLetterSpacing(qg.QFont.SpacingType.PercentageSpacing, 175)
        self._le_input.setFont(font)
        self._le_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._le_input.setInputMask('000000')

    def input_line_edit(self):
        return self._le_input

    def value(self) -> str:
        return self._le_input.text()


class CredentialsPage(qw.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Credentials')

        self._user = InputForm(text='Login', icon='user', password=False)
        self._password = InputForm(text='Password', icon='object-locked', password=True)

        layout = qw.QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(2)
        layout.addWidget(self._user)
        layout.addWidget(self._password)
        layout.addStretch(2)

        self.setLayout(layout)
        self.show()

    def clear(self):
        self._user.input_line_edit().clear()
        self._password.input_line_edit().clear()

    def user_name(self) -> str:
        return self._user.value()

    def password(self) -> str:
        return self._password.value()


class MainWindow(qw.QWidget):
    def __init__(self, title: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowIcon(qg.QIcon.fromTheme('network-vpn'))
        self.setWindowTitle(title)
        self.setFixedWidth(350)

        self._pages = w_pages = qw.QGroupBox()
        w_pages.setMinimumHeight(200)

        self._credentials_page = CredentialsPage()

        self._pages_layout = l_pages = qw.QStackedLayout()
        l_pages.currentChanged.connect(self._page_changed)
        l_pages.addWidget(self._credentials_page)
        w_pages.setLayout(l_pages)
        # l_content.setCurrentIndex(0)

        l_buttons = qw.QHBoxLayout()
        l_buttons.addWidget(qw.QPushButton('Cancel'), alignment=Qt.AlignmentFlag.AlignLeft)
        l_buttons.addWidget(qw.QPushButton('Connect'), alignment=Qt.AlignmentFlag.AlignRight)
        l_buttons.addWidget(qw.QPushButton('OK'), alignment=Qt.AlignmentFlag.AlignRight)

        layout = qw.QVBoxLayout()
        layout.addWidget(w_pages, stretch=2)
        layout.addLayout(l_buttons)

        self.setLayout(layout)
        self.show()
        layout.setSpacing(layout.contentsMargins().top())

    def _page_changed(self, index: int):
        if index == (-1):
            return
        self._pages.setTitle(self._pages_layout.widget(index).windowTitle())

    # def _page_credentials(self):
    #     pass


def _setup_credential_form():
    gbx = qw.QGroupBox()
    vl = qw.QVBoxLayout()
    vl.setSpacing(0)
    vl.setContentsMargins(0, 0, 0, 0)

    inputs = (
        InputForm(text='Login:', icon='user', password=False),
        InputForm(text='Password:', icon='object-locked', password=True),
        InputForm(text='OTP:', icon='alarm-symbolic', password=False, otp_mode=True),
    )
    for w in inputs:
        vl.addWidget(w)
    vl.addStretch(2)

    gbx.setLayout(vl)
    return gbx
    # mw.show()


def main():
    app = qw.QApplication(sys.argv)
    app.setApplicationVersion('1.5.2-dev')

    _ = MainWindow(f'SNXer {app.applicationVersion()}')

    # wgt = qw.QWidget()
    # wgt.setWindowIcon(qg.QIcon.fromTheme('network-vpn'))
    # wgt.setWindowTitle(f'SNXer {app.applicationVersion()}')
    # wgt.setFixedWidth(350)
    # wgt.show()
    #
    # btn_connect = qw.QPushButton('Connect')
    # btn_connect.setMinimumWidth(120)
    #
    # vbl = qw.QVBoxLayout()
    # vbl.setSpacing(20)
    # vbl.addWidget(_setup_credential_form())
    # vbl.addWidget(btn_connect, alignment=Qt.AlignmentFlag.AlignRight)
    # wgt.setLayout(vbl)

    return app.exec()


if __name__ == '__main__':
    main()
