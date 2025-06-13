# # Python program to create 
# # a file explorer in Tkinter
 
# # import all components
# # from the tkinter library
# from tkinter import *
 
# # import filedialog module
# from tkinter import filedialog
 
# # Function for opening the 
# # file explorer window
# def browseFiles():
#     filename = filedialog.askopenfilename(initialdir = "../../", title = "Select a File", filetypes =(("mat files", "*.m*"), ("all files", "*.*")))
#     file_list = filename.split('/')
#     # print(f"filename: {type(filename)}\n{filename.split('/')}")
     

#     # Change label contents
#     # label_file_explorer.configure(text="File Opened: "+filename)
#     ## name of the selected file is printed
#     label_file_explorer.configure(text=file_list[-1])
     
     
                                                                                                 
# # Create the root window
# window = Tk()
 
# # Set window title
# window.title('File Explorer')
 
# # Set window size
# window.geometry("300x300")
 
# #Set window background color
# window.config(background = "white")
 
# # Create a File Explorer label
# label_file_explorer = Label(window, text = "select a matlab (legacy) file\n(h-reflex data)", width = 30, height = 2, fg = "blue")
 
     
# button_explore = Button(window, text = "Browse Files", command = browseFiles) 
 
# button_exit = Button(window, text = "Exit", command = exit) 
 
# # Grid method is chosen for placing
# # the widgets at respective positions 
# # in a table like structure by
# # specifying rows and columns
# label_file_explorer.grid(column = 1, row = 1)
 
# button_explore.grid(column = 1, row = 2)
 
# button_exit.grid(column = 1,row = 3)
 
# # Let the window wait for any events
# window.mainloop()

import matplotlib.pyplot as plt


def on_enter_axes(event):
    print('enter_axes', event.inaxes)
    event.inaxes.patch.set_facecolor('yellow')
    event.canvas.draw()


def on_leave_axes(event):
    print('leave_axes', event.inaxes)
    event.inaxes.patch.set_facecolor('white')
    event.canvas.draw()


def on_enter_figure(event):
    print('enter_figure', event.canvas.figure)
    event.canvas.figure.patch.set_facecolor('red')
    event.canvas.draw()


def on_leave_figure(event):
    print('leave_figure', event.canvas.figure)
    event.canvas.figure.patch.set_facecolor('grey')
    event.canvas.draw()


fig, axs = plt.subplots(2, 1)
fig.suptitle('mouse hover over figure or Axes to trigger events')

fig.canvas.mpl_connect('figure_enter_event', on_enter_figure)
fig.canvas.mpl_connect('figure_leave_event', on_leave_figure)
fig.canvas.mpl_connect('axes_enter_event', on_enter_axes)
fig.canvas.mpl_connect('axes_leave_event', on_leave_axes)

plt.show()