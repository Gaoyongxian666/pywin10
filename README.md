# Welcome to pywin10

### 简介

`pywin10`基于**pywin32**,封装了菜单,通知功能.可以搭配**tkinter**,方便使用.

### 安装

    pip install pywin10

### 效果

![预览图](https://pic.imgdb.cn/item/61a5c59b2ab3f51d91cf1f17.png)  

![预览图](https://pic.imgdb.cn/item/61a5c59b2ab3f51d91cf1f1e.png)  

![预览图](https://pic.imgdb.cn/item/61a5c59b2ab3f51d91cf1f23.png) 

### 开始

    import threading
    import tkinter
    import win32gui
    from pywin10 import TaskBarIcon
    
    
    class MainWindow:
        def __init__(self):
            self.root = tkinter.Tk()
    
            # 开启常驻后台线程
            backend_thread = threading.Thread(target=self.backend)
            backend_thread.setDaemon(True)
            backend_thread.start()
    
            # 设置当点击窗体时弹出通知
            self.root.bind('<ButtonPress-1>', self._on_tap)
            # 自定义关闭按钮
            self.root.protocol("WM_DELETE_WINDOW", self._close)
    
            self.root.mainloop()
    
        def _on_tap(self, event):
            self.t.ShowToast()
    
        def _close(self):
            self.t.ShowToast(title="最小化", msg="窗口已经最小化到图标")
            self.root.withdraw()
    
        def _show(self):
            self.root.deiconify()
    
        def ding(self, *args):
            print("ding 接收参数:", args)
    
        def _left_click(self, *args):
            print("_left_click 接收参数:", args)
    
        def exit(self):
            # 退出 TaskBarIcon
            win32gui.DestroyWindow(self.t.hwnd)
            # 退出 Tkinter
            self.root.destroy()
    
        def backend(self):
            # TaskBarIcon 里面的参数全部都不是必须的,即便self.t = TaskBarIcon(),你一样可以发送通知等.
            self.t = TaskBarIcon(
                left_click=(self._left_click, (1, 2)),  # 左键单击回调函数,可以不设置(如果想要传参,这样写(func,(arg1,arg2)))
                double_click=self._show,  # 左键双击回调函数,可以不设置(如果不想传参,直接写函数名称)
                icon="python.ico",  # 设置图标,可以不设置
                hover_text="TaskBarIcon",  # 设置悬浮在小图标显示的文字,可以不设置
                menu_options=[  #可以不设置
                    ['退出', "退出.ico", self.exit, 1],  # 菜单项格式:["菜单项名称","菜单项图标路径或None",回调函数或者子菜单列表,id数字(随便写不要重复即可)]
                    ["分隔符", None, None, 111],
                    ['顶一顶', "ding.ico", (self.ding, (1, 2, 3)), 44],
                    ['日历', "日历.ico", None, 3],
                    ['主页', "主页.ico", self._show, 2],
                    ["分隔符", None, None, 7],
                    ["更多选项", "编辑.ico", [
                        ['使用说明', "等待文件.ico", None, 25],
                        ["分隔符", None, None, 17],
                        ['hello', "github.ico", None, 16],
                        ['hello2', "github.ico", None, 1116],
                    ], 4],
                ],
                menu_style="normal"  # 设置右键菜单的模式,可以不设置:normal(不展示图标),iconic(展示图标)
            )
            # 注意这是死循环，类似与tkinter中的mainloop,
            # 因为都是死循环,所以与mainloop会冲突,放到线程里面执行.
            win32gui.PumpMessages()
    
    
    if __name__ == '__main__':
        MainWindow()
