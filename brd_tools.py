
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
        """
        moduleLines = self.moduleDict[name]
        posFound = False
        for moduleIndex, lineData in enumerate(moduleLines):
            linesIndex, line = lineData 
            splitLine = line.split()
            if splitLine[0] == 'Po' and len(splitLine) > 3:
                splitLine[1] = '%d'%(round(10000*x),)
                splitLine[2] = '%d'%(round(10000*y),)
                splitLine[3] = '%d'%(round(ang),)
                for k, val in enumerate(splitLine):
                    if k == 0:
                        newLine = '%s'%(val,)
                    else:
                        newLine = '%s %s'%(newLine, val)
                self.lines[linesIndex] = newLine
                moduleLines[moduleIndex] = (linesIndex,newLine)
                posFound = True
                break
        # Check to see if modules was found.
        if not posFound:
            raise ValueError, 'module, %s,  position not found'%(name,)

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
                

# -----------------------------------------------------------------------------
if __name__ == '__main__':

    xNum = 11 
    yNum = 15 
    xStart = 1.0
    yStart = 1.0
    xStep = 0.3
    yStep = 0.3

    placer = ComponentPlacer('ledarray.brd')
    for i in range(0,xNum):
        for j in range(0,yNum):
            name = 'D%d,%d'%(j,i)
            x = xStart + i*xStep
            y = yStart + j*yStep
            ang = 0
            placer.setModulePos(name,x,y,ang)
    placer.write()


