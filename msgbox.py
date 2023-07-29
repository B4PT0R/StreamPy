from tkinter import messagebox as mb

def msgbox(string):
	mb.showinfo('msgbox',string)
	
def askyesno(string):
	return mb.askyesno('?',string)
