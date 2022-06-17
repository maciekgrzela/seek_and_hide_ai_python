import tkinter
from tkinter import *
import agent

root = Tk()
root.title('EatTheMeat - Select game level')
root.geometry("1065x900")

background_image = tkinter.PhotoImage(file="./EatTheMeat_select_ai_level.png")
background_label = Label(root, image=background_image)
background_label.place(x=0, y=0, relwidth=1, relheight=1)

red_button = PhotoImage(file="./EatTheMeat_red_btn.png")
yellow_button = PhotoImage(file="./EatTheMeat_yellow_btn.png")
green_button = PhotoImage(file="./EatTheMeat_green_btn.png")

def choice(level, solver):
    pop.destroy()
    root.destroy()
    agent.RunAgent(level, solver)


def train_level(level):
    global pop
    pop = Toplevel()
    pop.title('EatTheMeat - Select Optimizer Method')
    pop.geometry("1065x780")

    pop_background_image = tkinter.PhotoImage(file="./EatTheMeat_select_optimization.png")
    pop_background_label = Label(pop, image=pop_background_image)
    pop_background_label.place(x=0, y=0, relwidth=1, relheight=1)

    Button(pop, text='Adam', image=green_button, bg='white', font=('helvetica', 20, 'underline italic'), relief=FLAT, borderwidth=0, command=lambda: choice(level, 'adam'), compound=CENTER).pack(side=BOTTOM)
    Button(pop, text='SGD', image=green_button, bg='white', relief=FLAT, borderwidth=0,  command=lambda: choice(level, 'sgd'), compound=CENTER).pack(side=BOTTOM)

    pop.mainloop()


Button(root, text='35 gier', image=green_button, bg='white', relief=FLAT, borderwidth=0, command=lambda: train_level('easy'), compound=CENTER).pack(side=BOTTOM, padx=50)
Button(root, text='50 gier', image=yellow_button, bg='white', relief=FLAT, borderwidth=0, command=lambda: train_level('medium'), compound=CENTER).pack(side=BOTTOM)
Button(root, text='85 gier', image=red_button, bg='white', relief=FLAT, borderwidth=0, command=lambda: train_level('hard'), compound=CENTER).pack(side=BOTTOM)

root.mainloop()