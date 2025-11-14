import tkinter as tk

func_id = None

def activate_frame():
    print("entered frame")
    global func_id
    frame.unbind("<Enter>",func_id)
    func_id = canvas.bind("<Enter>", lambda event: deactivate_frame())

def deactivate_frame():
    print("entered canvas")
    global func_id
    canvas.unbind("<Enter>",func_id)
    func_id = frame.bind("<Enter>", lambda event: activate_frame())

root   = tk.Tk()
canvas = tk.Canvas(root, height=200, width=200, bg="green")
frame  = tk.Frame(canvas, borderwidth=20, background="red")
text   = tk.Text(frame, width=5, height=1)

canvas.grid()
# frame.grid() is not called, instead frame is put into a canvas-window:
canvas.create_window(100,100, window=frame)
text.grid()

func_id = frame.bind("<Enter>", lambda event: activate_frame())

root.mainloop()


