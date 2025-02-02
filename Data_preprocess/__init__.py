# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        Object bounding box label tool
# Purpose:     Label object bboxes for ImageNet Detection data
# Author:      Qiushi
# Created:     06/06/2014

#
#---------------------------------------------------------------------------
from __future__ import division
from tkinter import *
#import tkMessageBox
from PIL import Image, ImageTk
import os
import glob
import random
import shutil

# colors for the bboxes
COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']
# image sizes for the examples
SIZE = 256, 256

classLabels=['Alternaria_Boltch', 'Brown_Spot','Mosaic','Grey_Spot', 'Rust']

class LabelTool():
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("LableTools")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width = False, height = False)

        # initialize global state
        self.imageDir = ''
        self.imageList= []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.imagename = ''
        self.labelfilename = ''
        self.tkimg = None

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None
        self.currentClass = ''

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        self.label = Label(self.frame, text = "dirName:")
        self.label.grid(row = 0, column = 0, sticky = E)
        self.entry = Entry(self.frame)
        self.entry.grid(row = 0, column = 1, sticky = W+E)
        self.ldBtn = Button(self.frame, text = "load", command = self.loadDir)
        self.ldBtn.grid(row = 0, column = 2, sticky = W+E)

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<Escape>", self.cancelBBox)  # press <Espace> to cancel current bbox
        self.parent.bind("s", self.cancelBBox)
        self.parent.bind("a", self.prevImage) # press 'a' to go backforward
        self.parent.bind("d", self.nextImage) # press 'd' to go forward
        self.mainPanel.grid(row = 1, column = 1, rowspan = 4, sticky = W+N)

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text = 'Bounding boxes:')
        self.lb1.grid(row = 1, column = 2,  sticky = W+N)
        self.listbox = Listbox(self.frame, width = 22, height = 12)
        self.listbox.grid(row = 2, column = 2, sticky = N)
        self.btnDel = Button(self.frame, text = 'delete', command = self.delBBox)
        self.btnDel.grid(row = 3, column = 2, sticky = W+E+N)
        self.btnClear = Button(self.frame, text = 'clear', command = self.clearBBox)
        self.btnClear.grid(row = 4, column = 2, sticky = W+E+N)
        
        #select class type
        self.classPanel = Frame(self.frame)
        self.classPanel.grid(row = 5, column = 1, columnspan = 10, sticky = W+E)
        label = Label(self.classPanel, text = 'class:')
        label.grid(row = 5, column = 1,  sticky = W+N)
       
        self.classbox = Listbox(self.classPanel,  width = 4, height = 2)
        self.classbox.grid(row = 5,column = 2)
        for each in range(len(classLabels)):
            function = 'select' + classLabels[each]
            print (classLabels[each])
            btnMat = Button(self.classPanel, text = classLabels[each], command = getattr(self, function))
            btnMat.grid(row = 5, column = each + 3)
        
        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row = 6, column = 1, columnspan = 2, sticky = W+E)
        self.prevBtn = Button(self.ctrPanel, text='<< formal', width = 10, command = self.prevImage)
        self.prevBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.nextBtn = Button(self.ctrPanel, text='next >>', width = 10, command = self.nextImage)
        self.nextBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.progLabel = Label(self.ctrPanel, text = "progress:     /    ")
        self.progLabel.pack(side = LEFT, padx = 5)
        self.tmpLabel = Label(self.ctrPanel, text = "jump.")
        self.tmpLabel.pack(side = LEFT, padx = 5)
        self.idxEntry = Entry(self.ctrPanel, width = 5)
        self.idxEntry.pack(side = LEFT)
        self.goBtn = Button(self.ctrPanel, text = 'Go', command = self.gotoImage)
        self.goBtn.pack(side = LEFT)

        # example pannel for illustration
        self.egPanel = Frame(self.frame, border = 10)
        self.egPanel.grid(row = 1, column = 0, rowspan = 5, sticky = N)
        self.tmpLabel2 = Label(self.egPanel, text = "sample:")
        self.tmpLabel2.pack(side = TOP, pady = 5)
        self.egLabels = []
        for i in range(8):
            self.egLabels.append(Label(self.egPanel))
            self.egLabels[-1].pack(side = TOP)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side = RIGHT)

        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(10, weight = 1)

        # for debugging
##        self.setImage()
##        self.loadDir()

    def loadDir(self, dbg = False):
        if not dbg:
            s = self.entry.get()
            self.parent.focus()
            self.category = int(s)
        else:
            s = r'D:\workspace\python\labelGUI'
##        if not os.path.isdir(s):
##            tkMessageBox.showerror("Error!", message = "The specified dir doesn't exist!")
##            return
    
        '''
        #********************added at 2017-04-08
        sourceImageDir = os.path.join(r'./Augumentation', '%d' %(self.category))
        sourceImageList = glob.glob(os.path.join(sourceImageDir, '*'))
        if len(sourceImageList) == 0:
            print ('源路径中没有文件，请检查路径：' + self.imageDir)
            return
        print('成功读取' + str(len(sourceImageList)) + '张图片')
        pretreatImageDir = os.path.join(r'./Pretreats','%d' %(self.category)) 
        if not os.path.exists(pretreatImageDir):
            os.mkdir(pretreatImageDir)
        for oldfile in os.listdir(pretreatImageDir):
            oldfilesrc = os.path.join(pretreatImageDir,oldfile)
            try:
                os.remove(oldfilesrc)
            except:
                pass 
        for idxx in range(len(sourceImageList)):
         #   im = Image.open(sourceImageList[idxx])
         #   print (im.format, im.size, im.mode)
         #   out = im.resize((500,500))       
         #   out.save(pretreatImageDir + r'/' + str(idxx) + ".jpg")
            shutil.copy(sourceImageList[idxx],pretreatImageDir + r'/' + str(idxx) + ".jpg")
        #********************added end
        '''
            
        # get image list
        self.imageDir = os.path.join(r'./Augumentation', '%d' %(self.category))
        #print(self.imageDir) 
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.jpg'))
        if len(self.imageList) == 0:
            print ('No .JPEG images found in the specified dir!')
            return   

        # set up output dir
        if not os.path.exists(r'./Labels'):
            os.mkdir(r'./Labels')
        self.outDir = os.path.join(r'./Labels', '%d' %(self.category))
        self.outDir2 = os.path.join(r'./Labels_not_extended', '%d' %(self.category))
        #self.outDir = r'./Lables'
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)
        
        #返回与路径匹配的列表
        labeledPicList = glob.glob(os.path.join(self.outDir, '*.txt'))
        
        for label in labeledPicList:
            data = open(label, 'r')
            if '0\n' == data.read():
                data.close()
                continue
            data.close()
            picture = label.replace('Labels', 'Images').replace('.txt', '.jpg')
            if picture in self.imageList:
                self.imageList.remove(picture)
        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)
        self.loadImage()
        #print(self.imageList)
        print ('%d images loaded from %s' %(self.total, s))

    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        self.img = Image.open(imagepath)
        self.imgSize = self.img.size
        self.tkimg = ImageTk.PhotoImage(self.img)
        self.mainPanel.config(width = max(self.tkimg.width(), 400), height = max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
        self.progLabel.config(text = "%04d/%04d" %(self.cur, self.total))

        # load labels
        self.clearBBox()
        self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        labelname = self.imagename + '.txt'
        self.labelfilename = os.path.join(self.outDir, labelname)
        bbox_cnt = 0
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename) as f:
                for (i, line) in enumerate(f):
                    if i == 0:
                        bbox_cnt = int(line.strip())
                        continue
                    tmp = [int(t.strip()) for t in line.split()]
##                    print tmp
                    self.bboxList.append(tuple(tmp))
                    tmpId = self.mainPanel.create_rectangle(tmp[0], tmp[1], \
                                                            tmp[2], tmp[3], \
                                                            width = 2, \
                                                            outline = COLORS[(len(self.bboxList)-1) % len(COLORS)])
                    self.bboxIdList.append(tmpId)
                    self.listbox.insert(END, '(%d, %d) -> (%d, %d)' %(tmp[0], tmp[1], tmp[2], tmp[3]))
                    self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])

    def saveImage(self):
        with open(self.labelfilename, 'w') as f:
            f.write('%d\n' %len(self.bboxList))
            for bbox in self.bboxList:
                f.write(' '.join(map(str, bbox)) + '\n')
        print ('Image No. %d saved' %(self.cur))


    def mouseClick(self, event):
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
            #self.STATE['x'], self.STATE['y'] = self.imgSize[0], self.imgSize[1]
        else:
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
            if x2 > self.imgSize[0]:
                x2 = self.imgSize[0]
            if y2 > self.imgSize[1]:
                y2 = self.imgSize[1]                
            self.bboxList.append((self.currentClass, x1, y1, x2, y2))
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            self.listbox.insert(END, '(%d, %d) -> (%d, %d)' %(x1, y1, x2, y2))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
        self.STATE['click'] = 1 - self.STATE['click']

    def mouseMove(self, event):
        self.disp.config(text = 'x: %d, y: %d' %(event.x, event.y))
        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width = 2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width = 2)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
                                                            event.x, event.y, \
                                                            width = 2, \
                                                            outline = COLORS[len(self.bboxList) % len(COLORS)])

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []
        
    def selectAlternaria_Boltch(self):
        self.currentClass = 'Alternaria_Boltch'
        self.classbox.delete(0,END)
        self.classbox.insert(0, 'Alternaria_Boltch')
        self.classbox.itemconfig(0,fg = COLORS[0])
        
    def selectMosaic(self):
        self.currentClass = 'Mosaic'
        self.classbox.delete(0,END)
        self.classbox.insert(0, 'Mosaic')
        self.classbox.itemconfig(0,fg = COLORS[0])
        
    def selectRust(self):
        self.currentClass = 'Rust'
        self.classbox.delete(0,END)
        self.classbox.insert(0, 'Rust')
        self.classbox.itemconfig(0,fg = COLORS[0])
    def selectBrown_Spot(self):
        self.currentClass = 'Brown_Spot'
        self.classbox.delete(0,END)
        self.classbox.insert(0, 'Brown_Spot')
        self.classbox.itemconfig(0,fg = COLORS[0])
    def selectGrey_Spot(self):
        self.currentClass = 'Grey_Spot'
        self.classbox.delete(0,END)
        self.classbox.insert(0, 'Grey_Spot')
        self.classbox.itemconfig(0,fg = COLORS[0])
    
   

    def prevImage(self, event = None):
        self.saveImage()
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def saveImage2(self,type="same"):
        if "same"==type:
            with open(self.labelfilename, 'w') as f:
                f.write('%d\n' %len(self.bboxList))
                for bbox in self.bboxList:
                    f.write(' '.join(map(str, bbox)) + '\n')
            print ('Image No. %d saved' %(self.cur))
            
        if "flip1"==type:
            with open(self.labelfilename, 'w') as f:
                f.write('%d\n' %len(self.bboxList))
                for bbox in self.bboxList:
                    name,x1,y1,x2,y2 = bbox
                    x1 = 512 - x1
                    x2 = 512 - x2
                    x1, x2 = min(x1,x2), max(x1,x2)
                    y1, y2 = min(y1, y2 ), max(y1, y2)
                    bbox = (name,x1,y1,x2,y2)
                    f.write(' '.join(map(str, bbox)) + '\n')
            print ('Image No. %d saved' %(self.cur))
    
        if "flip2"==type:
            with open(self.labelfilename, 'w') as f:
                f.write('%d\n' %len(self.bboxList))
                for bbox in self.bboxList:
                    name,x1,y1,x2,y2 = bbox
                    y1 = 512 - y1
                    y2 = 512 - y2
                    x1, x2 = min(x1,x2), max(x1,x2)
                    y1, y2 = min(y1,y2), max(y1,y2)
                    bbox = (name,x1,y1,x2,y2)
                    f.write(' '.join(map(str, bbox)) + '\n')
            print ('Image No. %d saved' %(self.cur))
            
        if "rotate1"==type:
            with open(self.labelfilename, 'w') as f:
                f.write('%d\n' %len(self.bboxList))
                for bbox in self.bboxList:
                    name,x1,y1,x2,y2 = bbox
                    px1 = x1
                    px2 = x2
                    x1 = y1
                    x2 = y2
                    y1 = 512 - px2
                    y2 = 512 - px1
                    x1, x2 = min(x1,x2), max(x1,x2)
                    y1, y2 = min(y1,y2), max(y1,y2)
                    bbox = (name,x1,y1,x2,y2)
                    f.write(' '.join(map(str, bbox)) + '\n')
            print ('Image No. %d saved' %(self.cur))

        if "rotate2"==type:
            with open(self.labelfilename, 'w') as f:
                f.write('%d\n' %len(self.bboxList))
                for bbox in self.bboxList:
                    name,x1,y1,x2,y2 = bbox
                    x1 = 512-x1
                    x2 = 512-x2
                    y1 = 512-y1
                    y2 = 512-y2

                    x1, x2 = min(x1,x2), max(x1,x2)
                    y1, y2 = min(y1,y2), max(y1,y2)
                    bbox = (name,x1,y1,x2,y2)
                    f.write(' '.join(map(str, bbox)) + '\n')
            print ('Image No. %d saved' %(self.cur))
            
        if "rotate3"==type:
            with open(self.labelfilename, 'w') as f:
                f.write('%d\n' %len(self.bboxList))
                for bbox in self.bboxList:
                    name,x1,y1,x2,y2 = bbox
                    px1 = x1
                    px2 = x2
                    x1 = 512 - y2
                    x2 = 512 - y1
                    y1 = px1
                    y2 = px2
                    x1, x2 = min(x1,x2), max(x1,x2)
                    y1, y2 = min(y1,y2), max(y1,y2)
                    bbox = (name,x1,y1,x2,y2)
                    f.write(' '.join(map(str, bbox)) + '\n')
            print ('Image No. %d saved' %(self.cur))
   
 
    def loadImage2(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        # load labels
        #self.clearBBox()
        self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        labelname = self.imagename + '.txt'
        self.labelfilename = os.path.join(self.outDir, labelname)
 
    def nextImage(self, event = None):
        self.saveImage()
        if self.cur < self.total:
            
            #brightness_1
            self.cur += 1
            self.loadImage2()            
            self.saveImage2("same")
            #brightness_2
            self.cur += 1
            self.loadImage2()            
            self.saveImage2("same")
            
            #contrast_1
            self.cur += 1
            self.loadImage2()            
            self.saveImage2("same")     
            
            #contrast_2
            self.cur += 1
            self.loadImage2()            
            self.saveImage2("same")
            
            #flip_1
            self.cur += 1
            self.loadImage2()            
            self.saveImage2("flip1")                     
            
            #flip_2
            self.cur += 1
            self.loadImage2()            
            self.saveImage2("flip2")     

            #gaussian_1
            self.cur += 1
            self.loadImage2()            
            self.saveImage2("same")  

            #rotate_1
            self.cur += 1
            self.loadImage2()            
            self.saveImage2("rotate1") 
            
        
            #rotate_2
            self.cur += 1
            self.loadImage2()            
            self.saveImage2("rotate2")
            
            #rotate_3
            self.cur += 1
            self.loadImage2()            
            self.saveImage2("rotate3") 
            
            #sharpness_1
            self.cur += 1
            self.loadImage2()            
            self.saveImage2("same")   

            #sharpness_2
            self.cur += 1
            self.loadImage2()            
            self.saveImage2("same")                                    
            
            '''
            '''
            if self.cur < self.total:
                self.cur += 1
                self.loadImage()

    def gotoImage(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.saveImage()
            self.cur = idx
            self.loadImage()

##    def setImage(self, imagepath = r'test2.png'):
##        self.img = Image.open(imagepath)
##        self.tkimg = ImageTk.PhotoImage(self.img)
##        self.mainPanel.config(width = self.tkimg.width())
##        self.mainPanel.config(height = self.tkimg.height())
##        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)

if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.mainloop()