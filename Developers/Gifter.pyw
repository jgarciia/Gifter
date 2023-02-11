import importlib
import subprocess
from tkinter import *
from tkinter import filedialog as fd
import PIL.Image as pl
import PIL.ImageTk as plk
import pystray
from PIL import ImageSequence
import math

#create the window
root = Tk()
root.resizable(False, False)
root['bg'] = '#F0F0F0'
root.wm_attributes('-transparentcolor', root['bg']) #make window transparent
root.attributes('-fullscreen',True)
root.attributes("-topmost", True) #place the window on top of every app
root.update_idletasks()
root.overrideredirect(True)
root.iconphoto(False, PhotoImage(file="icon.png")) #Select the icon displayed fro the app

strayIcon = pl.open("icon.png") #Icon for the stray
default = {'id': None, 'name': '', 'path': '', 'resize': 100, 'width': 0, 'height': 0, 'frameCnt': 0, 'speed': 120, 'positionX': 0, 'positionY': 0} #Default values given when adding a new gif 
selectedGif = {} #gif being used right now
ind = 0 #Number of the Gif's current frame
label = Label(root) #Label where the Gif will be displayed
frames = [] #Array with each frame the gif has
modifyWindowActive = False #Verify if the modify Window is opened, if so, the window will just be updated instead of open another one
savedId = None #variable used to return to the last settings the gif had if the cancel button is pressed on the modify window

def openSavedGifs():
    global gifs
    with open("gifterdb.txt") as f:
        gifs = eval(f.read())

def updateIcon(item): #Function to stop and update the StrayIcon
    icon.visible = False
    icon.stop()
    if item == 'close':
        subprocess.call('taskkill /f /im Gifter.exe & exit', shell=True)
        root.destroy()
    else:
        openSavedGifs()
        updateMenu()
    
def animation(): # Function to update the frames
    global ind
    if len(frames) > 0:
        ind = 0 if ind == selectedGif['frameCnt'] else ind + 1 #Restart the animation 
        label.configure(image=frames[ind])
    root.after(selectedGif['speed'] if len(selectedGif) > 0 else 300, animation) #Change to the next frame, depending of the speed selected when the gif is created

def searchById(gifId): #Update the required variables searching by the id of the gif 
    global selectedGif
    for index, i in enumerate(gifs):
        if i['id'] == gifId:
            selectedGif = i #Refresh the actual Gif values to the new selected by gifId
            return index #Return the index that the GifId belongs to. (look gifterdb.txt to get more information)

def activate(gifId): #Activate gif animation
    global frames, ind
    searchById(gifId)
    ind = 0

    frames = [plk.PhotoImage(i.convert("RGBA").resize((math.floor(selectedGif['width'] * (selectedGif['resize'] / 100)), math.floor(selectedGif['height'] * (selectedGif['resize'] / 100))))) for i in ImageSequence.Iterator(pl.open(f"./gifs/{selectedGif['path']}"))]
    label.place(x=selectedGif['positionX'], y=selectedGif['positionY'])
    label.bind('<Button-3>', lambda event : littleMenu())

    return frames

def modifyGif(gifId): #Modify gif values
    global savedId, container
    savedId = gifId
    activate(gifId)
    addWindow(True)

def deleteGif(gifId): #Function called when delete Button is pressed on the StrayIcon
    global frames

    frames = [] if len(selectedGif) > 0 and selectedGif['id'] == gifId else frames #Stop the animation if the deleted gif is playing else continue animation
    getGif = searchById(gifId)

    with open("gifterdb.txt") as f:
        lines = f.readlines() #insert every line of the gifterdb.txt file into an array 

    with open("gifterdb.txt", "w") as f:
        for number, line in enumerate(lines):
            if number != getGif+1: #Rewrite the full gifterdb file except the selected gifId line 
                f.write(line)
    
    #reload the gifterdb module and the strayIcon to display changes
    updateIcon('update')
    
def openGif(addLabel): #Get the name of the selected gif to add it to the colection
    global ind, frames, selectedGif
    getPath = fd.askopenfilename(title='File selector', initialdir='./gifs', filetypes=[('', '.gif')]).split("/")[-1]
    if getPath != "":
        ind = 0
        selectedGif['path'] = getPath
        selectedGif['width'], selectedGif['height'] = pl.open(f"./gifs/{getPath}").size
        addLabel.config(text = getPath)
        frames = [plk.PhotoImage(i.convert("RGBA").resize((math.floor(selectedGif['width']*(selectedGif['resize']/100)),math.floor(selectedGif['height']*(selectedGif['resize']/100))))) for i in ImageSequence.Iterator(pl.open(f"./gifs/{selectedGif['path']}"))]
        selectedGif['frameCnt'] = len(frames) - 1

def updateLabels(newValue, selectedLabel, variableName): #Update the Gif when changes are made form the Modify Window
    global frames, selectedGif
    
    selectedGif[variableName] = int(newValue.get())

    if variableName == 'positionX' or variableName == 'positionY':
        label.place(x=selectedGif['positionX'], y=selectedGif['positionY'])
    
    if variableName == 'resize' and selectedGif['path'] != '':
        frames = [plk.PhotoImage(i.convert("RGBA").resize((math.floor(selectedGif['width']*(selectedGif['resize']/100)),math.floor(selectedGif['height']*(selectedGif['resize']/100))))) for i in ImageSequence.Iterator(pl.open(f"./gifs/{selectedGif['path']}"))]
        
    selectedLabel.config(text=selectedGif[variableName])

def motion(event, container, XLabel, YLabel, XBar, YBar): # Gets the mouse position and moves the Gif to the position until it detects the click event
    global selectedGif
    root['bg'] = '#303030' #Change Window background
    selectedGif['positionX'], selectedGif['positionY'] = event.x+10, event.y+10
    container.pack_forget() #Hides the modify Window when the mouse position is being detected
    label.place_configure(x=selectedGif['positionX'], y=selectedGif['positionY']) #update label position according to mouse position
    XLabel.configure(text=selectedGif['positionX']) #update the label on the modifyWindow for the X Value
    YLabel.configure(text=selectedGif['positionY'])
    XBar.set(selectedGif['positionX']) #update the slider on the modifyWindow for the X Value
    YBar.set(selectedGif['positionY'])
    root.bind('<Button-1>', lambda event : click(container)) #calls the funtion click() when the click is detected

def click(container): #Restarts everything to normal when the click is detected on the motion() function
    root['bg'] = '#F0F0F0'
    root.unbind('<Button-1>')
    root.unbind('<Motion>')
    container.pack(expand=1)

def saveGifConfig(container, name, update): #Save changes on the gifterdb.txt File when adding a new Gif or when the gif was modified
    global selectedGif, modifyWindowActive
    modifyWindowActive = False
    selectedGif['name'] = name.split("\n")[0]

    with open("gifterdb.txt") as f:
        lines = f.readlines()

    with open("gifterdb.txt", "w") as f:
        if update:
            index = searchById(selectedGif['id'])
            lines[index + 1] = f"   {selectedGif},\n"
        else:
            selectedGif['id'] = gifs[-1]['id'] + 1 if len(gifs) > 0 else 0
            lines.insert(len(gifs)+1, f"   {selectedGif},\n")

        f.write("".join(lines))
        container.destroy()
    
    updateIcon('update')

def cancel(container): #return everything to how it was before calling the mofify() function
    global frames, modifyWindowActive
    modifyWindowActive = False

    container.destroy()
    openSavedGifs()
    frames = activate(savedId) if savedId != None else []
    
def littleMenu(): #Menu that appears when left click is made over the gif active right now
    containerTest = Frame(root, width=450, height=500, bg='#303030')
    containerTest.place(x=selectedGif['positionX'], y=selectedGif['positionY'])
    modifyButton = Button(containerTest, text='Modify', activebackground="gray", fg="white", bg="gray", command = lambda: modifyGif(selectedGif['id']))
    modifyButton.pack()
    exitButton = Button(containerTest, text='Exit', activebackground="gray", fg="white", bg="gray", width=6, command= lambda: updateIcon('close'))
    exitButton.pack()

    root.after(2000, lambda: containerTest.destroy()) #Remove the menu after 2 seconds

def addWindow(update): #Window to create or modify the Gifs
    global selectedGif, savedGif, container, modifyWindowActive

    container.destroy() if modifyWindowActive else '' #Destroy the modify Window in case the window is already active (Container variable belongs to function addWindow() )
    modifyWindowActive = True
    selectedGif = default if len(selectedGif) == 0 else selectedGif
    label.place(x=selectedGif['positionX'], y=selectedGif['positionY'])
    speedBar = DoubleVar()
    positionXBar = DoubleVar()
    positionYBar = DoubleVar()
    resizeBar = DoubleVar()

    container = Frame(root, width=450, height=500, bg='#303030')
    container.pack(expand=1)
    container.pack_propagate(0)

    Label(container, text="Name:", bg='#303030', fg="white").place(x=40, y=30)
    nameBox = Text(container, bg="gray", fg="white", height=1, width=26)
    nameBox.place(x=100, y= 30)
    nameBox.insert(END, selectedGif['name']) if update else ""

    Label(container, text="Gif: ", fg="white", bg='#303030').place(x=47, y=71)
    addLabel = Label(container, text=f"{selectedGif['path'] if update else ''}", bg="gray", fg="white", width=30)
    addLabel.place(x=100, y=71)
    addButton = Button(container,text='Choose gif', activebackground="gray", fg="white", bg="gray", width=10, padx=5, command = lambda: openGif(addLabel))
    addButton.place(x=337, y=70)

    Label(container, text="Speed:", bg='#303030', fg="white").place(x=40, y=115)
    slideValue = Label(container, text=selectedGif['speed'], bg='#303030', fg="white")
    slideValue.place(x=335, y=115)
    speedSlide = Scale(container, variable=speedBar, from_=1, to_=300, orient=HORIZONTAL, showvalue=0, activebackground="gray", highlightbackground = "gray", highlightcolor="gray", troughcolor="gray", bg="gray", length=210, command= lambda a: updateLabels(speedBar, slideValue, 'speed'))
    speedSlide.place(x=100, y=115)
    speedBar.set(selectedGif['speed'])

    Label(container, text="Resize: ", bg="#303030", fg="white").place(x=40, y=160)
    resizeValue = Label(container, text=f"{selectedGif['resize'] if update else 100}", bg="#303030", fg="white")
    resizeValue.place(x=335, y=160)
    resizeSlide = Scale(container, variable=resizeBar, from_=50, to_=400, orient=HORIZONTAL, showvalue=0, activebackground="gray", highlightbackground = "gray", highlightcolor="gray", troughcolor="gray", bg="gray", length=200, command= lambda a: updateLabels(resizeBar, resizeValue, 'resize'))
    resizeSlide.place(x=110, y=160)
    resizeBar.set(selectedGif['resize'])

    Label(container, text="Position X: ", bg="#303030", fg="white").place(x=40, y=205)
    positionXValue = Label(container, text=f"{selectedGif['positionX'] if update else ''}", bg="#303030", fg="white")
    positionXValue.place(x=335, y=205)
    positionXSlide = Scale(container, variable=positionXBar, from_=-200, to_=3840, orient=HORIZONTAL, showvalue=0, activebackground="gray", highlightbackground = "gray", highlightcolor="gray", troughcolor="gray", bg="gray", length=200, command= lambda a: updateLabels(positionXBar, positionXValue, 'positionX'))
    positionXSlide.place(x=110, y=205)
    positionXBar.set(selectedGif['positionX'])

    Label(container, text="Position Y: ", bg="#303030", fg="white").place(x=40, y=250)
    positionYValue = Label(container, text=f"{selectedGif['positionY'] if update else ''}", bg="#303030", fg="white")
    positionYValue.place(x=335, y=250)
    positionYSlide = Scale(container, variable=positionYBar, from_=-200, to_=2160, orient=HORIZONTAL, showvalue=0, activebackground="gray", highlightbackground = "gray", highlightcolor="gray", troughcolor="gray", bg="gray", length=200, command= lambda a: updateLabels(positionYBar, positionYValue, 'positionY'))
    positionYSlide.place(x=110, y=250)
    positionYBar.set(selectedGif['positionY'])

    positionChange = Button(container, text="Change", fg="white", activebackground="gray", bg="gray", padx=17, command= lambda: root.bind('<Motion>', lambda event : motion(event, container, positionXValue, positionYValue, positionXBar, positionYBar)))
    positionChange.place(x=340, y=290)

    saveButton = Button(container,text='Save', fg="white", activebackground="gray", bg="gray", width=10, padx=5, command = lambda: saveGifConfig(container, nameBox.get("1.0", END), update))
    saveButton.place(x=240, y=430)

    cancelButton = Button(container,text='Cancel', fg="white", activebackground="gray", bg="gray", width=10, padx=5, command = lambda: cancel(container))
    cancelButton.place(x=337, y=430)

def updateMenu(): #Creates the StrayIcon
    global icon
    iconString = "pystray.Icon('Neural', strayIcon, 'gifter', menu=pystray.Menu(pystray.MenuItem('Add', lambda icon, item: addWindow(False)),"

    if len(gifs) > 0:
        iconString += "pystray.MenuItem('Change', pystray.Menu("

        for i in gifs:
            iconString += f"pystray.MenuItem('{i['name']}', pystray.Menu(pystray.MenuItem('Activate', lambda icon, item: activate({i['id']})), pystray.MenuItem('Modify', lambda icon, item: modifyGif({i['id']})), pystray.MenuItem('Delete', lambda icon, item: deleteGif({i['id']})))),"

        iconString += ")),"

    iconString += "pystray.MenuItem('Exit', lambda icon, item: updateIcon('close'))))"

    icon = eval(iconString)
    icon.run_detached()
    
# Final variables
openSavedGifs()
updateMenu()
root.bind('<Alt-F4>', lambda event: updateIcon('close')) #Make sure the alt + f4 combinations removes the StrayIcon and the Tkinter window 
root.after(0, animation)
root.mainloop()