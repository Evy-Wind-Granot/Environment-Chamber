from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QApplication,QLabel,QMainWindow,QWidget,QGridLayout,QLineEdit,QPushButton,QMessageBox, QProgressBar, QFrame
import adafruit_ads1x15.ads1115 as ADS
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QIntValidator, QPen,QPainter
#Graph
from pyqtgraph.Qt import QtGui
import pyqtgraph as pg
#Numpy
import numpy as np
import math
import busio
import board
#System 
import sys
import datetime
import time
from pathlib import Path
#RaspberryPi GPIO
import RPi.GPIO as GPIO
#File saving stuff
import csv
#Adafruit 1115 board (sensors on boxes 2 and 3)
from adafruit_ads1x15.analog_in import AnalogIn
i2c = busio.I2C(board.SCL, board.SDA)
adc1 = ADS.ADS1115(i2c, address = 0x48)
adc2 = ADS.ADS1115(i2c, address = 0x49)
chan0 = AnalogIn(adc1, ADS.P0)
chan1 = AnalogIn(adc1, ADS.P1)
chan2 = AnalogIn(adc1, ADS.P2)
chan3 = AnalogIn(adc1, ADS.P3)
chan4 = AnalogIn(adc2, ADS.P0)
chan5 = AnalogIn(adc2, ADS.P1)
chan6 = AnalogIn(adc2, ADS.P2)
chan7 = AnalogIn(adc2, ADS.P3)
#Adafruit Humidity sensor (BME 280) (Inside box 1)
from adafruit_bme280 import basic as adafruit_bme280 
i2c = busio.I2C(board.SCL, board.SDA)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

# initialize the pumps        
class Pump():
    def __init__(self, en, in1, in2):
        super(Pump, self).__init__()
        self.en = en
        self.in1 = in1
        self.in2 = in2
        
        #This is the GPIO set up configuration 
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.en,GPIO.OUT)
        GPIO.setup(self.in1,GPIO.OUT)
        GPIO.setup(self.in2,GPIO.OUT)
        GPIO.output(self.in1,GPIO.LOW)
        GPIO.output(self.in2,GPIO.LOW)
        GPIO.output(self.en,GPIO.HIGH)
    
    #Calling this function onto a pump (ex. "pump14.turnOn()") will turn on the pump
    def turnOn(self):
        GPIO.output(self.in1,GPIO.HIGH)
    
    #Calling this function onto a pump (ex. "pump14.turnOff()") will turn off the pump
    def turnOff(self):
        GPIO.output(self.in1,GPIO.LOW)
        
#This class is made to set all of the pins of the pumps on the RPi
class Maker(QWidget):
    def __init__(self):
        super(Maker, self).__init__()
    def initializeItAll(self):
        #pump1 + pump4, hence 14
        self.enbp14 = 13
        self.in3p14 = 19
        self.in4p14 = 26
        #pump2
        self.enap2 = 23
        self.in1p2 = 24
        self.in2p2 = 25
        #pump3 
        self.enap3 = 21
        self.in1p3 = 20
        self.in2p3 = 16
        #humidifer
        self.enh = 11
        self.in1h = 9
        self.in2h = 10
       
        #Naming each of the pumps assigning their respective GPIO pin stuff
        self.pump14 = Pump(self.enbp14, self.in3p14, self.in4p14) # pumps box1 -> box1
        self.pump2 = Pump(self.enap2, self.in1p2, self.in2p2) # pump box 1 -> box2
        self.pump3 = Pump(self.enap3, self.in1p3, self.in2p3) # pump box2 -> box3     
        self.humid = Pump(self.enh, self.in1h, self.in2h) # humidifier (in box1)

#this is just a splash screen, doesn't really do anything, just to add some professionalism
class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Loading...')
        self.setFixedSize(1100,500)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.counter = 0
        self.n = 300#total instance
        self.initUI()
        self.timer = QTimer()
        self.timer.timeout.connect(self.loading)
        self.timer.start(5)#control over speed
        
    def initUI(self):
        layout = QGridLayout()
        self.setLayout(layout)
        
        self.frame = QFrame()
        layout.addWidget(self.frame)
        self.labelTitle = QLabel(self.frame)
        self.labelTitle.setObjectName('LabelTitle')
        
        #center the label title object
        self.labelTitle.resize(self.width() - 10, 150)
        self.labelTitle.move(0,40)
        self.labelTitle.setText('Preparing Interface')
        self.labelTitle.setAlignment(Qt.AlignCenter)
        
        self.labelDescription = QLabel(self.frame)
        self.labelDescription.resize(self.width() - 10, 50)
        self.labelDescription.move(0, self.labelTitle.height())
        self.labelDescription.setObjectName('labeldesc')
        self.labelDescription.setAlignment(Qt.AlignCenter)
        
        self.progressBar = QProgressBar(self.frame)
        self.progressBar.resize(self.width()-200-10,50)
        self.progressBar.move(100,self.labelDescription.y() + 130)
        self.progressBar.setFormat('%p%')
        self.progressBar.setTextVisible(True)
        self.progressBar.setRange(0, self.n)
        self.progressBar.setValue(20)
        
        self.labelLoading = QLabel(self.frame)
        self.labelLoading.resize(self.width()-10, 50)
        self.labelLoading.move(0,self.progressBar.y() + 70)
        self.labelLoading.setObjectName('LabelLoading')
        self.labelLoading.setAlignment(Qt.AlignCenter)
        self.labelLoading.setText('Loading...')
        
    def loading(self):
        self.progressBar.setValue(self.counter)
        
        if self.counter >= self.n:
            self.timer.stop()
            self.close()
            time.sleep(1)
            self.window = Window()
            self.window.show()
        self.counter += 1
#end of the Splash screen code
        
#where the magic happens bascically does the whole code        
class Window(Maker, QWidget):
    def __init__(self):
        super(Window, self).__init__()
        #Set the window title
        self.setWindowTitle("User Input")
        #Set the Background color of the user input window
        self.setStyleSheet("background-color:#002754;")
        #Call the function that initializes the pumps so that you can call them
        self.initializeItAll()
        #User input prompts
        humidity = bme280.humidity
        self.l_h = QLabel("Current Humidity: {:.2f} %".format(humidity))
        self.l_expo = QLabel("Exposure Time(s)")
        self.l_reco = QLabel("Recovery Time(s)")
        self.l_rel = QLabel("Relative Humidity (%)")
        self.l_user = QLabel("User Name")
        self.l_samp = QLabel("Experiment Title")

        #User input text boxes
        self.expo = QLineEdit(self)
        self.reco = QLineEdit(self)
        self.rel = QLineEdit(self)
        self.user = QLineEdit(self)
        self.samp = QLineEdit(self)
        
        #Assign a name to the object to be called in CSS
        self.expo.setObjectName('expo')
        self.reco.setObjectName('reco')
        self.rel.setObjectName('rel')
        self.user.setObjectName('user')
        self.samp.setObjectName('samp')
        
        #Start & Stop button initialization
        self.start = QPushButton()
        self.stop = QPushButton()
        self.start.setText("START")
        self.stop.setText("STOP")
        self.start.clicked.connect(lambda : messageBox(self, self.expo.text(), self.reco.text(),self.rel.text(), self.user.text(), self.samp.text()))
        self.stop.clicked.connect(lambda : stopNow(self))
        
        #Doesn't allow anything but integers to be written in the expo and reco text boxes
        self.expo.setValidator(QIntValidator())
        self.reco.setValidator(QIntValidator())
        self.rel.setValidator(QIntValidator())
        self.rel.setText("0")
        self.expo.setText("0")
        self.reco.setText("0")

        #Iniitalize graphs
        self.plt1 = pg.plot(title = "Graph Box 2")
        self.plt1.addLegend()
        self.plt1.setBackground('#005493')
        self.plt2 = pg.plot(title = "Graph Box 3")
        self.plt2.addLegend()
        self.plt2.setBackground('#005493')
        #sets the lines to white
        self.plt1.getAxis('bottom').setPen('w')
        self.plt1.getAxis('left').setPen('w')
        self.plt2.getAxis('bottom').setPen('w')
        self.plt2.getAxis('left').setPen('w')
        #Sets the ticks to white
        self.plt1.getAxis('left').setTextPen('w')
        self.plt1.getAxis('bottom').setTextPen('w')
        self.plt2.getAxis('left').setTextPen('w')
        self.plt2.getAxis('bottom').setTextPen('w')
        #add widgets to layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.l_h,2,0)
        self.layout.addWidget(self.l_expo,4,0)
        self.layout.addWidget(self.l_reco,5,0)
        self.layout.addWidget(self.l_rel,6,0)
        self.layout.addWidget(self.l_user,7,0)
        self.layout.addWidget(self.l_samp,8,0)
        self.layout.addWidget(self.expo,4,1)
        self.layout.addWidget(self.reco,5,1)
        self.layout.addWidget(self.rel, 6,1)
        self.layout.addWidget(self.user,7,1)
        self.layout.addWidget(self.samp,8,1)
        self.layout.addWidget(self.start,10,0)
        self.layout.addWidget(self.stop,10,1)
        self.layout.addWidget(self.plt1,1,5,13,10)
        self.layout.addWidget(self.plt2,1,16,13,14)
        #initialize the axis
        self.plt1.setXRange(0, 20)
        self.plt1.setYRange(0, 20)
        self.plt2.setXRange(0, 20)
        self.plt2.setYRange(0, 20)
        #shows the grid lines
        #plt.showGrid(x=True,y=True)
        
        dataVector1 = []
        dataVector2 = []
        dataVector3 = []
        dataVector4 = []
        dataVector5 = []
        dataVector6 = []
        dataVector7 = []
        dataVector8 = []
        timeVector1 = []
        
        #an array of the arrays 
        arrays = [dataVector1, dataVector2, dataVector3, dataVector4, dataVector5, dataVector6, dataVector7, dataVector8, timeVector1]
        
        #Set the Legend for the graph 
        line1 = self.plt1.plot(timeVector1,dataVector1, pen = pg.mkPen('#F5AA1C', width=5), name = 'Sensor1')
        line2 = self.plt1.plot(timeVector1,dataVector2, pen = pg.mkPen('#C63527', width=5), name = 'Sensor2')
        line3 = self.plt1.plot(timeVector1,dataVector3, pen = pg.mkPen('#002754', width=5), name = 'Sensor3')
        line4 = self.plt1.plot(timeVector1,dataVector4, pen = pg.mkPen('#FF7F50', width=5), name = 'Sensor4')                     
        #Set the Legend for the graph
        line5 = self.plt2.plot(timeVector1,dataVector5, pen = pg.mkPen('#F5AA1C', width=5), name = 'Sensor5')
        line6 = self.plt2.plot(timeVector1,dataVector6, pen = pg.mkPen('#C63527', width=5), name = 'Sensor6')
        line7 = self.plt2.plot(timeVector1,dataVector7, pen = pg.mkPen('#002754', width=5), name = 'Sensor7')
        line8 = self.plt2.plot(timeVector1,dataVector8, pen = pg.mkPen('#FF7F50', width=5), name = 'Sensor8')
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda : self.update_label_text())
        self.timer.start(2000)        
                
        #Turn off all of the pumps then exit the program
        def stopNow(self):
            self.pump14.turnOff()
            self.pump2.turnOff()
            self.pump3.turnOff()
            self.humid.turnOff()
            GPIO.cleanup()
            sys.exit()
            
        def messageBox(self, expo, reco, rel, user, samp):
            humidity = bme280.humidity
            if expo == '' or int(expo) == 0 or reco == '' or int(reco) == 0 or user == '' or samp == '' or rel == '' or 15 >= int(rel) or int(rel) >= 85:
                message = QMessageBox()
                message.setWindowTitle("Missing Parameters")
                message.setText("One or more of the text fields are empty, or beyond the abilities of this device (Relative Humidity must be between 15%-85%). Please try again")
                message.setStandardButtons(QMessageBox.Ok)
                returnVal = message.exec_()
            elif (int(rel) >= 15 and int(rel) <= humidity):
                message = QMessageBox()
                message.setWindowTitle("Nitrogen Purge")
                message.setText("The selected relative humidity is less than current humidity of the box. If you would like to continue, purge the container with Nitrogen. Would you like to continue?")
                message.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                returnVal = message.exec_()
            else:
                message = QMessageBox()
                message.setWindowTitle("Check Complete - Confirm Settings?")
                text1 = "Your settings are as follows, do you wish to continue? \n"
                text2 = "Exposure time: " + str(self.expo.text()) + " seconds \n"
                text3 = "Recovery time: " + str(self.reco.text()) + " seconds \n"
                text4 = "Relative Humidity: " + str(self.rel.text()) + "% \n"
                message.setText(text1+text2+text3+text4)
                message.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                returnVal = message.exec()
            #user said "no" so run stop now          
            if returnVal == 65536:
                self.stopNow()
            elif returnVal == 16384:
                #Create a base line for the experiment then send to clean function
                start_time1 = time.time()
                self.start_time = time.time()
                self.clean_initialTimer = QtCore.QTimer()
                self.clean_initialTimer.setSingleShot(True)
                self.clean_initialTimer.timeout.connect(lambda: clean_initial())
                self.clean_initialTimer.start(100)
                
                #Runs once clean initial function timer is up then humid will run
                self.humidTimer = QtCore.QTimer()
                self.humidTimer.setSingleShot(True)
                self.humidTimer.timeout.connect(lambda: humid(self, rel))

                #Runs once humid function timer is up then pumpOn will run
                self.moverBeMovingTimer = QtCore.QTimer()
                self.moverBeMovingTimer.setSingleShot(True)
                self.moverBeMovingTimer.timeout.connect(lambda: moverBeMoving(self, expo))
                    
                #Runs once pumpOn function timer is up then pumpOff will run
                self.lastBoxTimer = QtCore.QTimer()
                self.lastBoxTimer.setSingleShot(True)
                self.lastBoxTimer.timeout.connect(lambda: lastBox(self, expo))
                
                #Runs once pumpOff function timer is up then clean_final will run
                self.cleanUpTimer = QtCore.QTimer()
                self.cleanUpTimer.setSingleShot(True)
                self.cleanUpTimer.timeout.connect(lambda: cleanUp(self, reco))
                
                #Runs once clean_final function timer is up then wrapUp will run 
                self.wrapUpTimer = QtCore.QTimer()
                self.wrapUpTimer.setSingleShot(True)
                self.wrapUpTimer.timeout.connect(lambda: wrapUp())
                
                self.stop.clicked.connect(lambda: self.stopNow())
                
                #cleans the final box from any residual substance left behind from previous experiment
                def clean_initial():
                    self.pump14.turnOn()
                    self.humidTimer.start(10000)
                    self.stop.clicked.connect(lambda: self.stopNow())            
                
                #Humidification, sends to handle_humid to update humidity (recursive 1/2)
                def humid(self, rel):
                    self.setWindowTitle("humidify")
                    self.pump14.turnOn()
                    self.humid.turnOn()
                    self.humidTimer = QTimer()
                    self.humidTimer.setSingleShot(True)
                    self.humidTimer.timeout.connect(lambda: self.handle_humid(rel))
                    self.humidTimer.start(2000)
                        
                #Turn on the pump between the humidity box and sensing box 1      
                def moverBeMoving (self, expo):
                    self.setWindowTitle("Graphing Box 2")
                    self.pump2.turnOn()
                    self.stop.clicked.connect(lambda: self.stopNow())
                    self.lastBoxTimer.start(int(expo)*1500)     
                    
                #Turn on the pump between box 2 and desiccant/box 3
                def lastBox (self, expo):
                    self.pump2.turnOff()
                    self.setWindowTitle("Graphing Box 3")
                    self.pump3.turnOn()
                    self.stop.clicked.connect(lambda: self.stopNow())
                    self.cleanUpTimer.start(int(expo)*1000)
                    
                #Once sensing is complete turn on the pump connected to box 3 and the outside world to clean the compartement    
                def cleanUp (self, reco):
                    self.pump3.turnOff()
                    self.setWindowTitle("Ending Cycle")
                    self.pump14.turnOn()
                    self.pump2.turnOn()
                    self.pump3.turnOn()
                    self.stop.clicked.connect(lambda: self.stopNow())
                    self.wrapUpTimer.start(int(reco)*1000)
                    
                #Ending code for file download and final message
                def wrapUp():
                    self.setWindowTitle("Preparing file")
                    timer1.stop()
                    self.stop.clicked.connect(lambda: self.stopNow())
                    #Date and time settings
                    current_time = datetime.datetime.now()
                    month = current_time.month
                    day = current_time.day
                    hour = current_time.hour
                    minute = current_time.minute
                    fileName = str(month) + '-' + str(day) + '-' + str(hour) + ':' + str(minute),
                    colour_count = 0                
                    with open ('/home/pi/Downloads/SensorTest-'+str(user)+'-'+str(samp)+'('+str(fileName)+')'+'.csv', 'w', newline='') as csvfile:
                        fieldnames = ['Time','Sensor1', 'Sensor2','Sensor3','Sensor4','Sensor5', 'Sensor6', 'Sensor7', 'Sensor8']
                        thewriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        thewriter.writeheader()
                        mini = min(len(arr) for arr in arrays)
                        sliced_arrays = [arr[:mini] for arr in arrays]
                
                        l = 0
                        for z in sliced_arrays[8]:
                            colour_count += thewriter.writerow({'Time':sliced_arrays[8][l], 'Sensor1':sliced_arrays[0][l],'Sensor2':sliced_arrays[1][l],'Sensor3':sliced_arrays[2][l],'Sensor4':sliced_arrays[3][l], 'Sensor5':sliced_arrays[4][l],'Sensor6':sliced_arrays[5][l],'Sensor7':sliced_arrays[6][l],'Sensor8':sliced_arrays[7][l]})
                            l +=1
                    self.pump14.turnOff()
                    self.pump2.turnOff()
                    self.pump3.turnOff()
                    self.humid.turnOff()
                    GPIO.cleanup()
                    #Message box to signify the completion of the experiment
                    message = QMessageBox()
                    message.setWindowTitle("Completion Message")
                    message.setText(user + "'s sample of " + samp + " had an exposure time of " + expo + " seconds and a recovery time of " + reco + " seconds and is now complete")
                    message.exec_()
                                    
                def update1():
                    try:
                        #The filling of the sensor and time arrays
                        timeVector1.append(time.time() - start_time1)
                        dataVector1.append(chan0.value/pow(2, 15)*6.144)
                        dataVector2.append(chan1.value/pow(2, 15)*6.144)
                        dataVector3.append(chan2.value/pow(2, 15)*6.144)
                        dataVector4.append(chan3.value/pow(2, 15)*6.144)
                        dataVector5.append(chan4.value/pow(2, 15)*6.144)
                        dataVector6.append(chan5.value/pow(2, 15)*6.144)
                        dataVector7.append(chan6.value/pow(2, 15)*6.144)
                        dataVector8.append(chan7.value/pow(2, 15)*6.144)
                    
                        mini = min(len(arr) for arr in arrays)
                        sliced_arrays = [arr[:mini] for arr in arrays]
                            
                        #The graph plotting points LIVE
                        line1 = self.plt1.plot(sliced_arrays[8],sliced_arrays[0], pen = pg.mkPen('#F5AA1C', width=5))
                        line2 = self.plt1.plot(sliced_arrays[8],sliced_arrays[1], pen = pg.mkPen('#C63527', width=5))
                        line3 = self.plt1.plot(sliced_arrays[8],sliced_arrays[2], pen = pg.mkPen('#002754', width=5))
                        line4 = self.plt1.plot(sliced_arrays[8],sliced_arrays[3], pen = pg.mkPen('#FF7F50', width=5))
                        line5 = self.plt2.plot(sliced_arrays[8],sliced_arrays[4], pen = pg.mkPen('#F5AA1C', width=5))
                        line6 = self.plt2.plot(sliced_arrays[8],sliced_arrays[5], pen = pg.mkPen('#C63527', width=5))
                        line7 = self.plt2.plot(sliced_arrays[8],sliced_arrays[6], pen = pg.mkPen('#002754', width=5))
                        line8 = self.plt2.plot(sliced_arrays[8],sliced_arrays[7], pen = pg.mkPen('#FF7F50', width=5))
                    except OSError as e:
                        i = 0#this migth make some problems, but something like this would be good 
                    self.stop.clicked.connect(lambda: self.stopNow())
                #Runs the code every 100ms or 0.1sec    
                timer1=QtCore.QTimer()
                timer1.timeout.connect(update1)
                timer1.start(100)
                
                #turns off all of the pumps and then ends program immediately
                def stopNow(self):
                    self.pump14.turnOff()
                    self.pump2.turnOff()
                    self.pump3.turnOff()
                    self.humid.turnOff()
                    GPIO.cleanup()
                    sys.exit()
    #Updates the RH on the UI before the program runs to help user decide                
    def update_label_text(self):
        try:
            humidity = bme280.humidity
            self.l_h.setText("Current Humidity: {:.2f} %".format(humidity))
        except Exception as e:
            self.l_h.setText("Current Humidity: -- %")
    
    #continuation of humid, handles the logic and the updating of on the UI (Recursive 1/2) sends back to humid if it doesn't hit "base case"
    def handle_humid(self, rel):
        try:
            humidity = bme280.humidity
            self.l_h.setText("Current Humidity: {:.2f} %".format(humidity))
            print("Humidity: {:.2f} %".format(humidity))  # delete this after
            self.stop.clicked.connect(lambda: self.stopNow())
            if humidity >= int(rel):
                self.humid.turnOff()
                self.pump14.turnOff()
                self.pump2.turnOn()#put here so that the pump turns on, for some reason it wont turn on when its in the moverBeMoving function
                self.moverBeMovingTimer.start(300)
            else:
                self.humidTimer.start(2000)  # Continue humidifying after 2 seconds
        except Exception as e:
            self.l_h.setText("Current Humidity: -- %")
            self.humidTimer.start(2000)  # Continue humidifying after 2 seconds
# end of actual program 

#Main there is also CSS to do the styling(colors, font-sizes)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet('''
        #LabelTitle {
            font-size: 60px;
            color: #93deed;
        }#LabelDesc{
            font-size: 30px;
            color: #c2ced1;
        }#LabelLoading{
            font-size: 30px;
            color: #fff;
        }QFrame{
            background-color: #002754;
            color: #DBDB0E;
            font-weight:bold;
        }QProgressBar{
            background-color: #DBDB0E;
            color: #fff;
            border-style: none;
            border-radius: 10px;
            text-align: center;
            font-size:30px;
        }QProgressBar::chunk{
            border-radius: 10px;
            background-color: #005493;
        }QMessageBox{
            background-color:#002754;
        }#START{
            color: #fff;
            font-size: 1.2em;
            font-weight:bold;
        }#STOP{
            color: #fff;
            font-size: 1.2em;
            font-weight:bold;
        }#expo{
            color: #fff;
        }#reco{
            color: #fff;
        }#user{
            color: #fff;
        }#samp{
            color: #fff;
        }#rel{
            color: #fff;
        }
    ''')
    splash = SplashScreen()
    splash.show()
    sys.exit(app.exec_())
