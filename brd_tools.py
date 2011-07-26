"""
Copyright 2010  IO Rodeo Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from __future__ import division
import sys
import numpy

class ComponentPlacer(object):

    def __init__(self,filename):
        """
        Read the file and get list of file lines and dictionary of modules.
        """
        self.filename = filename
        self.lines = self.readFile()
        self.moduleDict = self.getModuleDict()

    def readFile(self):
        """
        Read the file and return a list of all lines.
        """
        with open(self.filename,'r') as fid:
            lines = fid.readlines()
        return lines

    def getModuleDict(self):
        """
        Get a dictionary of all modules.
        """
        inModule = False
        moduleDict = {}
        # Loop over all lines in file
        for i, line in enumerate(self.lines):
            splitLine = line.split()
            if splitLine:
                if inModule:
                    # We are in a module get lines, module reference and determine when
                    # module ends.
                    moduleLines.append((i,line))
                    if splitLine[0] == '$EndMODULE':
                        inModule = False
                        if moduleRef is not None:
                            moduleDict[moduleRef] = moduleLines
                        else:
                            raise ValueError, 'module has no reference'
                    else:
                        if splitLine[0] == 'T0':
                            moduleRef =  splitLine[-1][2:-1]
                else:
                    # We are not in module .. look for module start.
                    if splitLine[0] == '$MODULE':
                        inModule = True
                        moduleLines = [(i,line)]
                        moduleRef = None
        return moduleDict

    def setModulePos(self,name,x,y,ang):
        """
        Set position of current modules. The values for x and y should be given in inches and
        ang in degrees.

        Note, this function should really read the module template form the .mod library file.
        """
        moduleLines = self.moduleDict[name]

        # Set position of the module itself
        # 
        # Note, it might make sense to make rotations relative ... or to read 
        # The template from the .mod file. 
        # 
        posFound = False
        for moduleIndex, lineData in enumerate(moduleLines):
            linesIndex, line = lineData
            splitLine = line.split()
            if splitLine[0] == 'Po' and len(splitLine) > 3:

                # Get new positions and angle
                curX = int(splitLine[1])
                newX = round(curX + 10000*x)
                curY = int(splitLine[2])
                newY = round(curY + 10000*y)
                curAng = int(splitLine[3])
                newAng = (curAng + round(ang))%3600

                # write new position and angle
                splitLine[1] = '%d'%(round(newX),)
                splitLine[2] = '%d'%(round(newY),)
                splitLine[3] = '%d'%(round(newAng),)
                for k, val in enumerate(splitLine):
                    if k == 0:
                        newLine = '%s'%(val,)
                    else:
                        newLine = '%s %s'%(newLine, val)
                newLine = '%s\n'%(newLine,)
                self.lines[linesIndex] = newLine
                moduleLines[moduleIndex] = (linesIndex,newLine)
                posFound = True
                break
        # Check to see if modules was found - this is a kludge
        if not posFound:
            raise ValueError, 'module, %s,  position not found'%(name,)

        # Set position of pads in module
        for moduleIndex, lineData in enumerate(moduleLines):
            linesIndex, line = lineData
            splitLine = line.split()
            if splitLine[0] == 'Sh':
                curAng = int(splitLine[-1])
                newAng = (curAng + round(ang))%3600
                splitLine[-1] = '%d'%(newAng,)
                for k, val in enumerate(splitLine):
                    if k == 0:
                        newLine = '%s'%(val,)
                    else:
                        newLine = '%s %s'%(newLine, val)
                newLine = '%s\n'%(newLine,)
                self.lines[linesIndex] = newLine
                moduleLines[moduleIndex] = (linesIndex,newLine)

    def write(self,filename=None):
        """
        Write new .brd file. If filename argument is not specified the
        same name as the original file will be used.
        """
        if filename is None:
            filename = self.filename
        with open(filename,'w') as fid:
            for line in self.lines:
                fid.write(line)

    def printLines(self):
        """
        Prints all lines in the file.
        """
        for i, line in enumerate(self.lines):
            print i, line


class SegmentDrawer(object):

    def __init__(self,filename):
        """
        Read the file and get list of file lines and dictionary of modules.
        """
        self.filename = filename
        self.lines = self.readFile()
        self.getNumDrawings()
        self.getInsertPos()

    def readFile(self):
        """
        Read the file and return a list of all lines.
        """
        with open(self.filename,'r') as fid:
            lines = fid.readlines()
        return lines 

    def getNumDrawings(self):
        """
        Gets the number of drawings currently in .brd file and line number of
        the Ndraw line. 
        """
        found = False
        for i, line in enumerate(self.lines):
            lineSplit = line.split()
            if not lineSplit:
                continue
            if lineSplit[0] == 'Ndraw':
                self.numDrawings = int(lineSplit[1])
                self.numDrawingsLine = i
                found = True
                break
        if not found:
            raise ValueEror, 'number of drawings Ndraw not found in file %s'%(self.filename,)

    def getInsertPos(self):
        """
        Get line number at which to start segemnet insertion.
        """
        for i, line in enumerate(self.lines):
            lineSplit = line.split()
            if not lineSplit:
                continue
            if lineSplit[0] in ('$EndSETUP', '$EndMODULE'):
                self.insertPos = i+1

    def insertLine(self, lineStr):
        """
        Insert a line into the brd file
        """
        self.lines.insert(self.insertPos,lineStr + '\n')
        self.insertPos += 1

    def setLine(self, lineNum, lineStr):
        """
        Set the line number lineNum in the file to lineStr
        """
        self.lines[lineNum] = lineStr + '\n'

    def incrNumDrawings(self):
        """
        Increment number of drawings.
        """
        self.numDrawings += 1
        self.setLine(self.numDrawingsLine,'Ndraw %d'%(self.numDrawings,))

    def addLineSegment(self,x0,y0,x1,y1,width, layer='edges_pcb'):
        """
        Add a line segment to the brd file.
        """
        _layer = layer.lower()
        if _layer == 'edges_pcb':
            layerNum = 28
        elif _layer == 'drawing':
            layerNum = 24
        elif _layer == 'comments':
            layerNum = 25
        else:
            raise ValueError, 'unknown layer: %s'%(layer,)

        # Scale values to 1/10000 of and inch
        _x0 = 10000*x0
        _y0 = 10000*y0
        _x1 = 10000*x1
        _y1 = 10000*y1
        _width = 10000*width
        
        # Add line segment
        self.insertLine('$DRAWSEGMENT')
        self.insertLine('Po 0 %d %d %d %d %d'%(_x0, _y0, _x1, _y1, _width))
        self.insertLine('De %d 0 900 0 0'%(layerNum,))
        self.insertLine('$EndDRAWSEGMENT')

        # Update number of drawings
        self.incrNumDrawings()

    def addRectangle(self, upperRight, lowerLeft, width, layer='edges_pcb'):
        """
        Add rectange to brd file by specifying the upperRight and lowerLeft 
        corners of the board.
        """
        x0, y0 = upperRight
        x1, y1 = lowerLeft
        self.addLineSegment(x0,y0,x0,y1,width,layer=layer)
        self.addLineSegment(x0,y1,x1,y1,width,layer=layer)
        self.addLineSegment(x1,y1,x1,y0,width,layer=layer)
        self.addLineSegment(x1,y0,x0,y0,width,layer=layer)

    def addCircularNgon(self,n,center,radius,width,rotAng=0,layer='edges_pcb'):
        """
        Add circular n-gon where n is the number of sides
        """
        cx, cy = center
        t = numpy.arange(0,n)/float(n)
        rotAngRad = rotAng*numpy.pi/180.0

        xPoints = cx + radius*numpy.cos(2*numpy.pi*t + rotAngRad)
        yPoints = cy + radius*numpy.sin(2*numpy.pi*t + rotAngRad)

        for i in range(0,n):
            j = (i+1)%n
            x0 = xPoints[i]
            y0 = yPoints[i]
            x1 = xPoints[j]
            y1 = yPoints[j]
            self.addLineSegment(x0,y0,x1,y1,width,layer=layer)
        
    def write(self,filename=None):
        """
        Write new .brd file. If filename argument is not specified the
        same name as the original file will be used.
        """

        # Update the number of drawings

        if filename is None:
            filename = self.filename
        with open(filename,'w') as fid:
            for line in self.lines:
                fid.write(line)

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    import math

    if 0:
        xNum = 2 
        yNum = 1
        xStart = 1.0
        yStart = 1.0
        xStep = 0.3691
        yStep = 0.3691

        placer = ComponentPlacer('ledarray.brd')
        for i in range(0,xNum):
            for j in range(0,yNum):
                name = 'D%d,%d'%(j,i)
                x = xStart + i*xStep
                y = yStart + j*yStep
                ang = 900 
                placer.setModulePos(name,x,y,ang)
        placer.write()

    if 0:
        xNum = 20 
        yNum = 1
        xStart = 5.0
        yStart = 4.0
        radius = 2.0

        placer = ComponentPlacer('ledarray.brd')
        for i in range(0,xNum):
            ang = 3600*(float(i)/float(xNum))
            name = 'D%d,%d'%(0,i)
            x = xStart + 2.0*math.cos(ang*math.pi/1800)
            y = yStart - 2.0*math.sin(ang*math.pi/1800)
            placer.setModulePos(name,x,y,ang)
        placer.write()

    if 1:


        drawer = SegmentDrawer('ledarray.brd')

        # Add rectange
        upperRight = 1,1
        lowerLeft = 7,4
        width = 0.015

        drawer.addRectangle(upperRight, lowerLeft, width)

        # Add circular ngon
        n = 100
        center = 6,5
        radius = 2
        width = 0.015

        drawer.addCircularNgon(n,center,radius,width)
        drawer.write()

    
    if 0:
        board_filename = sys.argv[1]
        print "Placing components in %s" % (board_filename,)

        # xNum_input = 6
        # yNum_input = 96
        # xNum_output = 24
        # yNum_output = 24
        xNum_input = 4
        yNum_input = 4
        xNum_output = 4
        yNum_output = 4
        xStep = 0.3691
        yStep = 0.3691
        # xCornerRough = 10.0
        # yCornerRough = 10.0
        xCornerRough = 5.0
        yCornerRough = 5.0
        xCenter = (xNum_output - 1)/2 * xStep
        yCenter = (yNum_output - 1)/2 * yStep
        xStart = int(xCornerRough + xCenter) - xCenter
        yStart = int(yCornerRough + yCenter) - yCenter

        placer = ComponentPlacer(board_filename)
        for h in range(0,int(xNum_output/xNum_input)):
            xLow = h*xNum_input
            xHigh = xLow + xNum_input
            for i in range(xLow,xHigh):
                for j in range(0,yNum_output):
                    name0 = j + h*yNum_output
                    name1 = i - h*xNum_input
                    name = 'D%d,%d'%(name0,name1)
                    x = xStart + i*xStep
                    y = yStart + j*yStep
                    ang = 0
                    placer.setModulePos(name,x,y,ang)
        placer.write()
