import sys

if sys.version_info[0] == 2:
    from Tkinter import *
else:
    from tkinter import *


class Application(Frame):
    def say_hi(self):
        print("hi there, everyone!")

    def createWidgets(self):
        self.QUIT = Button(self)
        self.QUIT["text"] = "QUIT"
        self.QUIT["fg"] = "red"
        self.QUIT["command"] = self.quit

        self.QUIT.pack({"side": "left"})

        self.hi_there = Button(self)
        self.hi_there["text"] = ("Hello",)
        self.hi_there["command"] = self.say_hi

        self.hi_there.pack({"side": "left"})

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()


# import humanfriendly
# print(humanfriendly)
# import pkg_resources
# for ep in pkg_resources.iter_entry_points("console_scripts"):
#    if ep.dist.project_name == "humanfriendly":
#        print("FOUND", ep.dist)
#        break
# else:
#    print ("EP for humanfriendly not found")
app = Application()
# app.mainloop()

# from fpdf import FPDF
# import PyQt5.Qt
"""
test = "test"

pdf = FPDF()
pdf.add_page()
pdf.set_font('times', size=20)
pdf.cell(0, 12, txt="Test", ln=True, align='L')
pdf.output('test.pdf')
"""
import black
