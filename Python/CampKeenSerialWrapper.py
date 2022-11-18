import time,threading,queue,serial
import CampKeenDataParsing

class CampKeenSerial(CampKeenDataParsing):
    def __init__(self,Port,Baud=115200):
        super().__init__()
        self.Run = True
        self.RecieveBuffer = ''
        self.FIFO = queue.Queue()
        self.serialPort = serial.Serial(Port)
        self.ReceiveDataThread = threading.Thread(target=self.Loopy)
        self.RecieveConditional = threading.Condition()
        self.serialPort.baudrate = Baud
        self.serialPort.bytesize = serial.EIGHTBITS
        self.serialPort.parity = serial.PARITY_NONE
        self.serialPort.stopbits = serial.STOPBITS_ONE
        self.serialPort.timeout = 1
        self.serialPort.xonxoff = False
        self.serialPort.rtscts = False

    def Init(self):
        self.SendData(self.Query('Current Port'))
        time.sleep(.1)
        self.SendData(self.Query('StreamingData'))
        time.sleep(.1)
        if self.CurrentPort == [None,'RS232']:
            self.SendData('%SETSTREAMINGDATA*RS232*ON\r')
        elif self.CurrentPort == [None,'USB']:
            self.SendData('%SETSTREAMINGDATA*USB*ON\r')
        time.sleep(.1)
        self.SendData('%UPDATEALL\r')
        time.sleep(5)
        self.SendData('%ALLDATA?\r')\

    def InitialStart(self):
        self.ReceiveDataThread.start()

    def KillitWithFire(self):
        self.Run = False
        self.RecieveConditional.acquire()
        self.RecieveConditional.notify()
        self.RecieveConditional.release()
        self.ReceiveDataThread.join()

    def Reset(self):
        self.ClosePort()
        self.ClearBuffer()
        self.FIFO = queue.Queue()

    def AddToBufferBack(self,Data):
        try:
            self.RecieveBuffer = self.RecieveBuffer + Data.decode()
            ReturnedData = self.IncomingDataParse(self.RecieveBuffer)
            self.RecieveBuffer = ReturnedData
        except Exception as E:
            print('CampKeen AddToBufferBack error',E)
            self.ClearBuffer()

    def ClearBuffer(self):
        self.RecieveBuffer = ''

    def ClosePort(self):
        self.serialPort.close()

    def SendData(self,Data):
        if isinstance(Data,str):
            Data = Data.encode()
        self.FIFO.put(Data)
        self.WriteData()

    def WriteData(self):
        try:
            while self.FIFO.empty() == False:
                WhatToSend = self.FIFO.get()
                self.serialPort.write(WhatToSend)
        except:
            pass

    def RecieveData(self):
        time.sleep(.1)
        if self.serialPort.is_open:
            response = self.serialPort.read_all()
            if response != b'':
                #print('CampKeen response',response)
                self.AddToBufferBack(response)
                self.RecieveConditional.acquire()
                self.RecieveConditional.notify()
                self.RecieveConditional.release()

    def Loopy(self):
        while self.Run:
            self.RecieveData()



#Camper = CampKeenSerial("COM4")
#Camper.InitialStart()
#Camper.Init()
#inital = time.monotonic()
#while True: 
#    time.sleep(.1)
#    if abs(time.monotonic() - inital) > .25:
#        print(Camper.EnergyMonitorStates)
 #       inital = time.monotonic()
