import sys
import tempfile
import os
import sqlite3
from PyQt5 import QtCore, QtGui, QtWidgets, uic 
from os import path
from sqlite3 import Error

global fromConnection
global fromCursor
fromConnection = None
fromCursor = None

global toConnection
global toCursor
toConnection = None
toCursor = None

''' Two temporary files, simple program 
    to simple just to do one '''
tmpFile1 = f"{tempfile.gettempdir()}/tableCopyFrom.txt"
tmpFile2 = f"{tempfile.gettempdir()}/tableCopyTo.txt"

fromTMP = None
toTMP = None

''' Loads data from those temporary files
    fromTMP from Database, toTMP to Database '''
if os.path.exists(tmpFile1) == True:
    with open(tmpFile1) as f:
        thisList = list(f)
        fromTMP = thisList[0].rstrip("\n")
        fromTMP = fromTMP.strip()
if os.path.exists(tmpFile2) == True:
    with open(tmpFile2) as f:
        thisList = list(f)
        toTMP = thisList[0].rstrip("\n")
        toTMP = toTMP.strip()

class Ui(QtWidgets.QMainWindow):
    def __init__(self):     
        super(Ui, self).__init__()
        uic.loadUi('main.ui', self)
        self.fromPlainTextEdit.textChanged.connect(self.fromDrop)
        self.toPlainTextEdit.textChanged.connect(self.toDrop)
        self.fromList.clicked.connect(self.fromListClicked)
        self.copyButton.clicked.connect(self.copy)
        if fromTMP != None:
            self.fromPlainTextEdit.setPlainText(f'{fromTMP}')
        if toTMP != None:
            self.toPlainTextEdit.setPlainText(f'{toTMP}')
        self.clearButton.clicked.connect(self.clear)
        self.show()
    
    def clear(self):
        ''' self explanatory '''
        self.fromPlainTextEdit.clear()
        self.toPlainTextEdit.clear()

    
    def fromDrop(self):
        ''' drag 'n drop local file into QPlainText field and it loads '''
        self.fromPlainTextEdit.textChanged.disconnect()
        current = self.fromPlainTextEdit.toPlainText().replace("file://", "").strip()
        self.fromPlainTextEdit.setPlainText(f'{current}')
        if os.path.exists(current) == True:
            self.fromPlainTextEdit.setPlainText(f'"{current}"')
            self.loadFrom(current)
            self.updateTmpFile(tmpFile1, current)
        self.fromPlainTextEdit.textChanged.connect(self.fromDrop)

    def toDrop(self):
        ''' same as above but right side '''
        self.toPlainTextEdit.textChanged.disconnect()
        current = self.toPlainTextEdit.toPlainText().replace("file://", "").strip()
        self.toPlainTextEdit.setPlainText(f'{current}')
        if os.path.exists(current) == True:
            self.toPlainTextEdit.setPlainText(f'"{current}"')
            self.updateTmpFile(tmpFile2, current)
            self.loadTo(current)
        self.toPlainTextEdit.textChanged.connect(self.toDrop)

    def loadFrom(self, current):
        ''' once a file exists it loads their tables '''
        global fromConnection
        global fromCursor
        fromConnection = sqlite3.connect(current)
        fromCursor = fromConnection.cursor()
        fromCursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        data = fromCursor.fetchall()
        self.printLists(data, self.fromList)

    def loadTo(self, current, reLoad=True):
        ''' this could be integrated into method above, but ... 
            reLoad argument for quick refresh after copy '''
        global toConnection
        global toCursor
        if reLoad == True:
            toConnection = sqlite3.connect(current)
            toCursor = toConnection.cursor()
        toCursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        data = toCursor.fetchall()
        self.printLists(data, self.toList)

    def printLists(self, finals, printTo):
        ''' prints tables onto screen in alphabetic order '''
        printTo.clear()
        finals.sort()
        for count, i in enumerate(finals):
            if i[0] != "sqlite_sequence":
                item = printTo.addItem(i[0])
                listwidget = printTo
                item = listwidget.item(len(listwidget)-1)

    def fromListClicked(self):
        ''' this cute, this changes the button! '''
        item = self.fromList.item(self.fromList.currentRow())
        self.copyButton.setText(f"COPY {item.text()} to -->")

    def copy(self):
        ''' creates new table, drops old one if nessesary '''
        item = self.fromList.item(self.fromList.currentRow())
        listToCopy = item.text()
        tableDetails = self.getTableDetails(listToCopy)
        fromCursor.execute('select * from "{}"'.format(listToCopy))
        fetchData = fromCursor.fetchall()
        self.createTable(listToCopy, tableDetails)
        if fetchData != []:
            self.copyMore(listToCopy, fetchData)
        else: print(f"Table and columns created for {listToCopy}, though the table is empty!")

    def copyMore(self, table, data):
        ''' creates SQLite query and injects '''
        query = f"INSERT into {table} VALUES ({','.join(['?']*len(data[0]))})"
        with toConnection:
            toCursor.executemany(query, data)
        print(f"Successfully copied/replaced {table} from {self.fromPlainTextEdit.toPlainText()} to {self.toPlainTextEdit.toPlainText()}")
        self.loadTo(self.toPlainTextEdit.toPlainText(), False)
        
    def getTableDetails(self, table):
        ''' I have no clue! '''
        fromCursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='{}'".format(table,))
        return fromCursor.fetchall()
    
    def createTable(self, table, details):
        ''' Create what?! '''
        self.dropOldTable(table)
        query = f"{details[0][0]}"
        with toConnection:
            try: toCursor.execute(query)
            except Error: pass

    def updateTmpFile(self, file, data):
        ''' Does stuff to your harddrive! '''
        with open(file, "w") as f:
            f.close()
        with open(file, "a") as f:
            f.write(data)
            f.close
    
    def dropOldTable(self, table):
        ''' SQLite injection attack, google it! '''
        with toConnection:
            try: 
                toConnection.execute('drop table {}'.format(table))
                print(f"Dropping old {table}")
            except Error:
                print(f"Table not present, creating: {table}")


app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec_()
