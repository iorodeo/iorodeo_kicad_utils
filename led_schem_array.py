import os.path
import time

class LEDSchemArray(object):

    def __init__(self, params):
        self.LEDWireOffset = 200
        # Add parameters as attributes
        for k,v in params.iteritems():
            setattr(self, k, v)
        self.headerTemplate = HEADER_TEMPLATE
        self.schFileName = '%s.sch'%(self.name,)
        self.cmpFileName = '%s.cmp'%(self.name,)
        self.cacheFileName = '%s.cache'%(self.name,)
        self.ledData = {}

    def getLEDPos(self): 
        ledPos = {}
        for i in range(self.numParallel): 
            for j in range(self.numSeries): 
                x = self.upperLeft[0] + j*self.spacing[0]
                y = self.upperLeft[1] + i*self.spacing[1]
                ledPos[(i,j)] = (x,y)
        return ledPos

    def write(self):
        self.writeSchFile()
        self.writeCmpFile()

    def writeSchFile(self):
        with open(self.schFileName,'w') as self.schFid:
            self.writeHeader()
            self.writeArrayWires()
            self.writeLEDArray()
            self.writeFooter()

    def writeHeader(self):
        header = self.headerTemplate.replace('CACHEFILE_MARKER', self.cacheFileName)
        self.schFid.write(header)

    def writeFooter(self):
        self.schFid.write('$EndSCHEMATC\n')

    def writeArrayWires(self):
        ledPos = self.getLEDPos()

        # Create stub wires on positive and negative ends of series LEDs
        for i in range(self.numParallel):
            # Positive stubs
            x, y = ledPos[(i,0)]
            x0, y0 = x-self.LEDWireOffset, y
            x1, y1 = x0-self.stubLength, y
            self.writeWire(x0,y0,x1,y1)

            # Negative stubs
            x, y = ledPos[(i,self.numSeries-1)]
            x0, y0 = x+self.LEDWireOffset, y
            x1, y1 = x0+self.stubLength, y
            self.writeWire(x0,y0,x1,y1)

        # Create connections between positive stubs
        dx, dy = self.spacing
        for i in range(self.numParallel):
            x, y  = ledPos[(i,0)]
            x0, y0 = x-self.LEDWireOffset-self.stubLength, y
            x1, y1 = x0, y0 - dy
            self.writeWire(x0,y0,x1,y1)
            self.writeConnection(x0,y0)

        # Create connections between negative stubs
        for i in range(self.numParallel):
            x, y = ledPos[(i,self.numSeries-1)]
            x0, y0 = x+self.LEDWireOffset+self.stubLength, y
            x1, y1 = x0, y + dy
            self.writeWire(x0,y0,x1,y1)
            self.writeConnection(x0,y0)
            
        # Create connections between series LEDs
        for i in range(self.numParallel):
            for j in range(1,self.numSeries):
                pos0 = ledPos[(i,j-1)]
                pos1 = ledPos[(i,j)]
                self.writeLEDToLEDWire(pos0, pos1)

    def writeLEDToLEDWire(self,pos0, pos1):
        """
        Write wire connecting two horizontal LEDs
        """
        x0, y0 = pos0[0] + self.LEDWireOffset, pos0[1] 
        x1, y1 = pos1[0] - self.LEDWireOffset, pos1[1] 
        self.writeWire(x0,y0,x1,y1)

    def writeWire(self,x0,y0,x1,y1,printFlag=False):
        self.schFid.write('Wire Wire Line\n')
        self.schFid.write('\t%d %d %d %d\n'%(x0,y0,x1,y1))
        if printFlag == True:
            print 'Wire Wire Line\n'
            print '\t%d %d %d %d\n'%(x0,y0,x1,y1)
            
    def writeConnection(self,x,y):
        self.schFid.write('Connection ~ %d %d\n'%(x,y))

    def writeLEDArray(self):
        ledPos = self.getLEDPos()
        for k,v in ledPos.iteritems():
            i,j = k
            x,y = v 
            self.writeLED(i,j,x,y)

    def writeLED(self,i,j,x,y):
        self.schFid.write('$Comp\n')

        refStr = 'D%d,%d'%(i,j)
        self.schFid.write('L LED %s\n'%(refStr,))

        timeStamp = hex(int(time.time()))[2:]
        timeStamp = timeStamp.upper()
        self.schFid.write('U 1 1 %s\n'%(timeStamp,))

        self.schFid.write('P %d %d\n'%(x,y))

        annotationX = x - self.annotationOffset[0]
        annotationY = y - self.annotationOffset[1]
        self.schFid.write('F 0 "%s" H %d %d  50 0000 CNN\n'%(refStr,annotationX, annotationY))

        valueStr = 'LED'
        valueX = x - self.labelOffset[0]
        valueY = y - self.labelOffset[1]
        self.schFid.write('F 1 "%s" H %d %d  50 0000 CNN\n'%(valueStr,valueX, valueY)) 
        self.schFid.write('\t1    %d %d\n'%(x,y))
        self.schFid.write('\t1    0    0    -1\n')

        self.schFid.write('$EndComp\n')

        # Save info for writing .cmp file
        self.ledData[(i,j)] = {
                'reference' : refStr,
                'timeStamp' : timeStamp,
                'value'     : valueStr, 
                'module'    : self.module,
                }

    def writeCmpFile(self):
        with open(self.cmpFileName,'w') as cmpFid:
            # Write header - need to modify so that the date string is correct
            cmpFid.write('Cmp-Mod V01 Created by CVpcb (20090216-final) date = Thu 14 Jul 2011 05:35:17 PM PDT\n\n')
            for i in range(self.numParallel):
                for j in range(self.numSeries):
                    data = self.ledData[(i,j)]
                    cmpFid.write('BeginCmp\n')
                    cmpFid.write('TimeStamp = /%s;\n'%(data['timeStamp'],))
                    cmpFid.write('Reference = %s;\n'%(data['reference'],))
                    cmpFid.write('ValuerCmp = %s;\n'%(data['value'],))
                    cmpFid.write('IdModule  = %s;\n'%(data['module'],))
                    cmpFid.write('EndCmp\n\n')
            cmpFid.write('EndListe\n')


HEADER_TEMPLATE = """EESchema Schematic File Version 2  date Thu 14 Jul 2011 12:55:08 PM PDT
LIBS:power,device,transistors,conn,linear,regul,74xx,cmos4000,adc-dac,memory,xilinx,special,microcontrollers,dsp,microchip,analog_switches,motorola,texas,intel,audio,interface,digital-audio,philips,display,cypress,siliconi,opto,atmel,contrib,valves,./CACHEFILE_MARKER
EELAYER 24  0
EELAYER END
$Descr A4 11700 8267
Sheet 1 1
Title ""
Date "14 jul 2011"
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
"""

# -----------------------------------------------------------------------------
if __name__ == '__main__':

    params = {
            'name'              : 'ledarray',
            'numSeries'         : 11, 
            'numParallel'       : 15,
            'upperLeft'         : (2500,1000),
            'spacing'           : (600,400), 
            'annotationOffset'  : (0,-100), 
            'labelOffset'       : (0,100), 
            'stubLength'        : 300,
            'module'            : 'SM0805',
            }

    ledSchemArray = LEDSchemArray(params)
    ledSchemArray.write()
