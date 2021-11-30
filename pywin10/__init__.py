# -*- coding: UTF-8 -*-
"""
@Project ：pywin10
@File ：__init__.py.py
@Author ：Gao yongxian
@Date ：2021/11/30 13:01
@contact: g1695698547@163.com
"""

# 参考项目（Pywin32项目下有丰富的Demo）：https://github.com/Travis-Sun/pywin32
# Pywin32的在线文档：http://timgolden.me.uk/pywin32-docs/win32.html
# Pywin32的离线文档：https://gaoyongxian.lanzoui.com/iNCGWx0p5ad

# 当前仅封装 一级菜单 多级菜单 普通菜单项 带icon的菜单项
# 如果想要实现 特殊菜单项（MFS_CHECKED(选择)、MFS_GRAYED(禁用)、MFT_RIGHTJUSTIFY(显示在右边)）,请参考Pywin32项目下的demo文件，自行编写。

import struct
import threading
import time
import win32api
import os
import win32con
from win32con import WM_USER
from win32gui import *
from win32gui_struct import PackMENUITEMINFO


class TaskBarIcon:
    """
    创建任务栏图标
    实现：右键菜单，通知提示
    """

    def __init__(self, icon: str = None, hover_text: str = "TaskBarIcon", menu_style: str = "normal",
                 menu_options: list = None, left_click=None, double_click=None):
        """
        Args:
            icon: 图标文件路径
            hover_text: 鼠标停留在图标上显示的文字
            menu_style: 菜单风格是否显示图标（normal，or iconic）
            menu_options: 右键菜单.菜单项格式:["菜单项名称","菜单项图标路径或None",回调函数或者子菜单列表,id数字(随便写不要重复即可)]
            left_click: 左键单击回调函数
            double_click: 左键双击回调函数
        """
        # 传参
        self.icon = icon
        self.hover_text = hover_text
        self.menu_options = menu_options
        self.menu_style = menu_style
        self.left_click = left_click
        self.double_click = double_click

        # 设置窗体的类名，标题，消息名称。默认设置就好，一般不需要管。
        self.window_title = self.window_class = self.window_message = "TaskBarIconDemo"

        # 定义新的窗口消息，该消息保证在整个系统中是唯一的。消息值可以是在发送或发布消息时使用。
        msg_TaskbarRestart = RegisterWindowMessage(self.window_message)

        # 定义消息回调
        message_map = {
            msg_TaskbarRestart: self.OnRestart,
            win32con.WM_DESTROY: self.OnDestroy,
            win32con.WM_COMMAND: self.OnCommand,
            win32con.WM_USER + 20: self.OnTaskbarNotify,
            # owner-draw related handlers.
            win32con.WM_MEASUREITEM: self.OnMeasureItem,
            win32con.WM_DRAWITEM: self.OnDrawItem,
        }

        # Register the Window class.
        wc = WNDCLASS()
        # Returns the handle of an already loaded DLL.
        self.hinst = wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = self.window_class
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wc.hCursor = win32api.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32con.COLOR_WINDOW
        wc.lpfnWndProc = message_map  # could also specify a wndproc.
        # Don't blow up if class already registered to make testing easier
        try:
            classAtom = RegisterClass(wc)
        except:
            print("WinError.ERROR_CLASS_ALREADY_EXISTS")

        # Creates a new window.
        self.hwnd = CreateWindow(
            self.window_class,
            self.window_title,
            win32con.WS_OVERLAPPED | win32con.WS_SYSMENU,
            0, 0, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT,
            0, 0, self.hinst, None)
        UpdateWindow(self.hwnd)

        # iconic模式下的菜单设置
        # Load up some information about menus needed by our owner-draw code.The font to use on the menu.
        ncm = SystemParametersInfo(win32con.SPI_GETNONCLIENTMETRICS)
        self.font_menu = CreateFontIndirect(ncm['lfMenuFont'])
        # spacing for our ownerdraw menus - not sure exactly what constants should be used (and if you owner-draw all
        # items on the menu, it doesn't matter!)
        self.menu_icon_height = win32api.GetSystemMetrics(win32con.SM_CYMENU) - 4
        self.menu_icon_width = self.menu_icon_height
        # space from end of icon to start of text.
        self.icon_x_pad = 7

        self.menu_item_map = {}
        self.hmenu = CreatePopupMenu()

        # Finally, create the menu
        self.CreateMenu(menu=self.hmenu, menu_options=self.menu_options)

        # notify 通知线程
        self._thread = None

        # 设置菜单图标
        if icon is not None and os.path.isfile(icon):
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            self.hicon = LoadImage(self.hinst, icon, win32con.IMAGE_ICON, 0, 0, icon_flags)
        else:
            print("Icon is None")
            self.hicon = LoadIcon(0, win32con.IDI_APPLICATION)
        self._DoCreateIcons()

        # Runs a message loop until a WM_QUIT message is received.
        # 注意这是死循环，类似与tkinter中的mainloop,放到线程里面执行.
        # PumpMessages()

    def _DoCreateIcons(self):
        """设置后台图标"""
        nid = (self.hwnd, 0, NIF_ICON | NIF_MESSAGE | NIF_TIP, win32con.WM_USER + 20,
               self.hicon, self.hover_text)
        try:
            # Adds, removes or modifies a taskbar icon.
            Shell_NotifyIcon(NIM_ADD, nid)
        except:
            # This is common when windows is starting, and this code is hit before the taskbar has been created.
            print("error:Failed to add the taskbar icon - is explorer running?")
            # but keep running anyway - when explorer starts, we get the TaskbarCreated message.

    def OnRestart(self, hwnd, msg, wparam, lparam):
        self._DoCreateIcons()

    def OnDestroy(self, hwnd, msg, wparam, lparam):
        """
        退出后台程序: 外部通过调用 win32gui.DestroyWindow(hwnd) 来退出程序
        """
        # We need to arrange to a WM_QUIT message to be sent to our PumpMessages() loop.
        nid = (self.hwnd, 0)
        Shell_NotifyIcon(NIM_DELETE, nid)
        PostQuitMessage(0)  # Terminate the app.

    def OnTaskbarNotify(self, hwnd, msg, wparam, lparam):
        """
        实际上最主要的就三种：左键，右键，双击左键
        """
        if lparam == win32con.WM_LBUTTONUP:
            # print("You clicked me.")
            if self.left_click is not None:
                if type(self.left_click) == tuple:
                    if len(self.left_click) == 2:
                        self.left_click[0](*self.left_click[1])
                    else:
                        self.left_click[0]()
                else:
                    self.left_click()
            else:
                pass
        elif lparam == win32con.WM_LBUTTONDBLCLK:
            # print("You double-clicked me.")
            if self.double_click is not None:
                if type(self.double_click) == tuple:
                    if len(self.double_click) == 2:
                        self.double_click[0](*self.double_click[1])
                    else:
                        self.double_click[0]()
                else:
                    self.double_click()
            else:
                pass
        elif lparam == win32con.WM_RBUTTONUP:
            # print("You right clicked me.")
            # display the menu at the cursor pos.
            pos = GetCursorPos()
            # See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winui/menus_0hdi.asp
            SetForegroundWindow(self.hwnd)
            TrackPopupMenu(self.hmenu, win32con.TPM_LEFTALIGN, pos[0], pos[1], 0, self.hwnd, None)
            PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)

        return 1

    def OnCommand(self, hwnd, msg, wparam, lparam):
        """
        回调函数：根据id来判断
        """
        # An interface to the win32api LOWORD macro.
        id = win32api.LOWORD(wparam)
        if self.menu_item_map[id][2] is not None:
            if type(self.menu_item_map[id][2]) == tuple:
                if len(self.menu_item_map[id][2]) == 2:
                    self.menu_item_map[id][2][0](*self.menu_item_map[id][2][1])
                else:
                    self.menu_item_map[id][2][0]()
            else:
                self.menu_item_map[id][2]()
        else:
            pass
            # print(self.menu_item_map[id][0], ":没有设置回调函数")

    def OnMeasureItem(self, hwnd, msg, wparam, lparam):
        """
        Owner-draw related functions.  We only have 1 owner-draw item, but we pretend we have more than that :)
        """
        # Last item of MEASUREITEMSTRUCT is a ULONG_PTR
        fmt = "5iP"
        buf = PyMakeBuffer(struct.calcsize(fmt), lparam)
        data = struct.unpack(fmt, buf)
        ctlType, ctlID, itemID, itemWidth, itemHeight, itemData = data

        text, hicon, func, index = self.menu_item_map[itemData]
        if text is None:
            # Only drawing icon due to HBMMENU_CALLBACK
            cx = self.menu_icon_width
            cy = self.menu_icon_height
        else:
            # drawing the lot!
            dc = GetDC(hwnd)
            oldFont = SelectObject(dc, self.font_menu)
            cx, cy = GetTextExtentPoint32(dc, text)
            SelectObject(dc, oldFont)
            ReleaseDC(hwnd, dc)

            cx += win32api.GetSystemMetrics(win32con.SM_CXMENUCHECK)
            cx += self.menu_icon_width + self.icon_x_pad

            cy = win32api.GetSystemMetrics(win32con.SM_CYMENU)

        new_data = struct.pack(fmt, ctlType, ctlID, itemID, cx, cy, itemData)
        PySetMemory(lparam, new_data)
        return True

    def OnDrawItem(self, hwnd, msg, wparam, lparam):
        # lparam is a DRAWITEMSTRUCT
        fmt = "5i2P4iP"
        data = struct.unpack(fmt, PyGetMemory(lparam, struct.calcsize(fmt)))
        ctlType, ctlID, itemID, itemAction, itemState, hwndItem, \
        hDC, left, top, right, bot, itemData = data

        rect = left, top, right, bot

        text, hicon, _, _ = self.menu_item_map[itemData]

        if text is None:
            # This means the menu-item had HBMMENU_CALLBACK - so all we
            # draw is the icon.  rect is the entire area we should use.
            DrawIconEx(hDC, left, top, hicon, right - left, bot - top,
                       0, 0, win32con.DI_NORMAL)
        else:
            # If the user has selected the item, use the selected
            # text and background colors to display the item.
            selected = itemState & win32con.ODS_SELECTED
            if selected:
                crText = SetTextColor(hDC, GetSysColor(win32con.COLOR_HIGHLIGHTTEXT))
                crBkgnd = SetBkColor(hDC, GetSysColor(win32con.COLOR_HIGHLIGHT))

            each_pad = self.icon_x_pad // 2
            x_icon = left + win32api.GetSystemMetrics(win32con.SM_CXMENUCHECK) + each_pad
            x_text = x_icon + self.menu_icon_width + each_pad

            # Draw text first, specifying a complete rect to fill - this sets
            # up the background (but overwrites anything else already there!)
            # Select the font, draw it, and restore the previous font.
            hfontOld = SelectObject(hDC, self.font_menu)
            ExtTextOut(hDC, x_text, top + 2, win32con.ETO_OPAQUE, rect, text)
            SelectObject(hDC, hfontOld)

            # Icon image next.  Icons are transparent - no need to handle
            # selection specially
            if hicon is not None and type(hicon) == int:
                DrawIconEx(hDC, x_icon, top + 2, hicon,
                           self.menu_icon_width, self.menu_icon_height,
                           0, 0, win32con.DI_NORMAL)
            else:
                # print(text,":当前选项设置icon失败")
                pass

            # Return the text and background colors to their
            # normal state (not selected).
            if selected:
                SetTextColor(hDC, crText)
                SetBkColor(hDC, crBkgnd)

    def CreateMenu(self, menu=None, menu_options=None):
        """设置菜单"""
        if self.menu_style == "normal" and menu_options is not None:
            for item in menu_options:
                self.menu_item_map[item[3]] = item

                if item[0] == "分隔符":
                    InsertMenu(menu, 0, win32con.MF_BYPOSITION, win32con.MF_SEPARATOR, None)
                    continue

                if type(item[2]) == list:
                    # print("当前是submenu")
                    submenu = CreatePopupMenu()
                    self.CreateMenu(submenu, item[2])
                    item, extras = PackMENUITEMINFO(text=item[0], hSubMenu=submenu, wID=item[3])
                    InsertMenuItem(menu, 0, 1, item)
                    continue

                item, extras = PackMENUITEMINFO(text=item[0], wID=item[3])

                InsertMenuItem(menu, 0, 1, item)

        elif self.menu_style == "iconic" and menu_options is not None:
            for item in menu_options:
                self.menu_item_map[item[3]] = item
                # Owner-draw menus mainly from:
                # http://windowssdk.msdn.microsoft.com/en-us/library/ms647558.aspx
                # and:
                # http://www.codeguru.com/cpp/controls/menu/bitmappedmenus/article.php/c165

                # Create one with an icon - this is *lots* more work - we do it
                # owner-draw!  The primary reason is to handle transparency better -
                # converting to a bitmap causes the background to be incorrect when
                # the menu item is selected.  I can't see a simpler way.
                # First, load the icon we want to use.
                ico_x = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
                ico_y = win32api.GetSystemMetrics(win32con.SM_CYSMICON)

                if self.menu_item_map[item[3]][1]:
                    try:
                        hicon = LoadImage(0, self.menu_item_map[item[3]][1], win32con.IMAGE_ICON, ico_x, ico_y,
                                          win32con.LR_LOADFROMFILE)
                        self.menu_item_map[item[3]][1] = hicon
                    except:
                        print(self.menu_item_map[item[3]][1], ":没找到文件,文件名称是否正确?")

                if item[0] == "分隔符":
                    InsertMenu(menu, 0, win32con.MF_BYPOSITION, win32con.MF_SEPARATOR, None)
                    continue

                if type(item[2]) == list:
                    # print("当前是submenu")
                    sub_menu = CreatePopupMenu()
                    self.CreateMenu(sub_menu, item[2])

                    item, extras = PackMENUITEMINFO(
                        fType=win32con.MFT_OWNERDRAW,
                        dwItemData=item[3],
                        wID=item[3],
                        hSubMenu=sub_menu)
                    InsertMenuItem(menu, 0, 1, item)
                    continue

                item, extras = PackMENUITEMINFO(
                    fType=win32con.MFT_OWNERDRAW,
                    dwItemData=item[3],
                    wID=item[3])
                InsertMenuItem(menu, 0, 1, item)

        else:
            pass

    def notification_active(self):
        """是否正在有通知显示"""
        if self._thread is not None and self._thread.is_alive():
            # We have an active notification, let is finish we don't spam them
            return True
        return False

    def ShowToast(self, title: str = "通知", msg: str = "请写下你的信息内容", duration: int = 0):
        """
        通知栏弹窗Toast

        Args:
            title: 标题
            msg: 内容
            duration: 通知提醒的最短时间(在这段时间内不会有新的通知替换掉它)
        """
        if self.notification_active():
            # We have an active notification, let is finish so we don't spam them
            print("当前正在展示通知中...")
            return False

        # self._thread = threading.Thread(
        #     target=Shell_NotifyIcon,
        #     args=(NIM_MODIFY, (
        #         self.hwnd,
        #         0,
        #         NIF_INFO,
        #         WM_USER + 20,
        #         self.hicon,
        #         "Balloon Tooltip",
        #         msg,
        #         duration,
        #         title)))

        self._thread = threading.Thread(
            target=self._show_toast,
            args=(title, msg, duration))
        self._thread.start()

    def _show_toast(self, title, msg, duration):
        Shell_NotifyIcon(NIM_MODIFY, (
            self.hwnd,
            0,
            NIF_INFO,
            WM_USER + 20,
            self.hicon,
            "Balloon Tooltip",
            msg,
            duration,
            title))
        time.sleep(duration)
