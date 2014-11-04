#! /usr/bin/python

'''
Alessandro Bacchini (allebacco@gmail.com)

This file contains debug dumpers / helpers / visualizers so OpenCV
classes can be more easily inspected by gdb and QtCreator.

To install in gdb, add these lines to ~/.gdbinit
```
python
exec(open('<path to opencv_dumper.py>').read())
end
```

'''

import math
import numpy as np


DEPTH_NAMES = ['CV_8U', 'CV_8S', 'CV_16U', 'CV_16S', 'CV_32S', 'CV_32F', 'CV_64F', 'undefined']
DEPTH_TYPE = ['unsigned char', 'char', 'unsigned short', 'short', 'int', 'float', 'double', 'void']
DEPTH_NP_TYPE = [np.uint8, np.int8, np.uint16, np.int16, np.int32, np.float32, np.float64, np.uint8]
DEPTH_PY_TYPE = ['B', 'b', 'H', 'h', 'i', 'f', 'd', 'i']
DEPTH_BYTE_SIZE = [1, 1, 2, 2, 4, 4, 8, 1]


def qdump__cv__Mat(self, value):
    '''
    Pretty printer function for cv::Mat class
    '''

    self.putNumChild(1)

    flags = int(value['flags'])
    depth = flags & 7
    channels = 1 + (flags >> 3) & 63
    depth = min(depth, 7)
    cv_type_name = DEPTH_NAMES[depth]
    cv_type = DEPTH_TYPE[depth]
    data_byte_size = DEPTH_BYTE_SIZE[depth]
    np_dtype = DEPTH_NP_TYPE[depth]

    cv_type_name += 'C%d' % channels

    rows = int(value['rows'])
    cols = int(value['cols'])

    value_str = '%dx%d %s' % (cols, rows, cv_type_name)
    refcount = int(value['refcount'].dereference())
    if refcount <= 0:
        value_str = 'unistantiated'
    elif refcount == 1:
        value_str += ' unique'
    else:
        value_str += ' shared'

    #self.putValue('%dx%d %s' % (cols, rows, cv_type_name))
    self.putValue(value_str)

    line_step = int(value['step']['p'][0])

    if self.isExpanded():
        with Children(self):
            with SubItem(self, 'flags'):
                self.putValue('%s (0x%X)' % (cv_type_name, flags))
                self.putType("int")
                self.putNumChild(0)
            self.putSubItem('rows', value['rows'])
            self.putSubItem('cols', value['cols'])
            self.putSubItem('allocator', value['allocator'])
            self.putSubItem('dims', value['dims'])
            self.putSubItem('refcount', value['refcount'])
            self.putSubItem('size', value['size'])
            self.putSubItem('step', value['step'])

            # Put data array
            image_data_start = int(value['data'])
            with SubItem(self, 'data'):
                vals_type = self.lookupType(cv_type)
                p = value['data'].cast(vals_type.pointer())
                size = cols*rows
                self.putValue(r'%dx%d (%d, 0x%X)' % (cols, rows, size, int(p)), encoding=0)
                self.putType(cv_type+'*')
                size = min(size, 1000)
                if cols > 0 and rows > 0:
                    self.putNumChild(size)
                else:
                    self.putNumChild(0)
                if self.isExpanded():
                    with Children(self, size, childType=vals_type):
                        s = 0
                        for i in range(0, rows):
                            for j in range(0, cols):
                                # Limit output to improve performance
                                if s > size:
                                    break
                                v = (p + i * cols * channels + j * channels)
                                d = self.readRawMemory(v, channels*data_byte_size)
                                array = np.frombuffer(d, dtype=np_dtype, count=channels)
                                array = np.array_str(array)
                                with SubItem(self, s):
                                        self.putName("[%3d,%3d]" % (i, j))
                                        self.putValue(array)
                                s = s + 1

                            # Limit output to improve performance
                            if s > size:
                                break

            dataend = 0
            with SubItem(self, 'dataend'):
                p = value['dataend'].cast(self.lookupType('unsigned char').pointer())
                dataend = int(p)
                self.putValue('0x%X' % dataend)
                self.putType('unsigned char*')
                self.putNumChild(0)

            datastart = 0
            with SubItem(self, 'datastart'):
                p = value['datastart'].cast(self.lookupType('unsigned char').pointer())
                datastart = int(p)
                self.putValue('0x%X' % datastart)
                self.putType('unsigned char*')
                self.putNumChild(0)

            with SubItem(self, 'datalimit'):
                p = value['datalimit'].cast(self.lookupType('unsigned char').pointer())
                datalimit = int(p)
                self.putValue('0x%X' % datalimit)
                self.putType('unsigned char*')
                self.putNumChild(0)

            # Put metadata to improve output informations
            
            with SubItem(self, 'stride'):
                self.putValue(str(line_step))
                self.putNumChild(0)

            # Evaluate the ROI
            initial_stride = image_data_start-datastart
            first_row = 0
            first_col = 0
            if initial_stride > 0:
                first_row = initial_stride / line_step
                first_col = int((initial_stride % line_step) / (data_byte_size*channels))
            with SubItem(self, 'roi'):
                self.putValue('[%d,%d][%dx%d]' % (first_col, first_row, cols, rows))
                self.putNumChild(4)
                if self.isExpanded():
                    with Children(self):
                        with SubItem(self, 'x'):
                            self.putName("x")
                            self.putValue(str(int(first_col)))
                        with SubItem(self, 'y'):
                            self.putName("y")
                            self.putValue(str(int(first_row)))
                        with SubItem(self, 'width'):
                            self.putName("width")
                            self.putValue(str(cols))
                        with SubItem(self, 'height'):
                            self.putName("height")
                            self.putValue(str(rows))


def qdump__cv__RotatedRect(self, value):
    '''
    Pretty printer function for cv::RotatedRect class
    '''

    self.putNumChild(1)

    angle = float(value['angle'])
    x = float(value['center']['x'])
    y = float(value['center']['y'])
    width = float(value['size']['width'])
    height = float(value['size']['height'])

    self.putValue('[%.2f, %.2f][%.2fx%.2f, %.2f]' % (x, y, width, height, angle))

    if self.isExpanded():
        with Children(self):
            self.putSubItem('angle', value['angle'])
            self.putSubItem('center', value['center'])
            self.putSubItem('size', value['size'])
            with SubItem(self, 'area'):
                self.putValue('%.2f' % (width*height))
                self.putNumChild(0)

            # Put metadata to improve output informations
            angle_rad = angle * math.pi / 180.
            b = math.cos(angle_rad) * 0.5
            a = math.sin(angle_rad) * 0.5
            p0 = (x - a*height - b*width, y + b*height - a*width)
            p1 = (x + a*height - b*width, y - b*height - a*width)
            p2 = (2*x - p0[0], 2*y - p0[1])
            p3 = (2*x - p1[0], 2*y - p1[1])
            points = [p0, p1, p2, p3]
            with SubItem(self, 'points'):
                self.putValue('[x, y]')
                self.putNumChild(1)
                if self.isExpanded():
                    with Children(self):
                        for i, p in enumerate(points):
                            name = '[%d]' % i
                            with SubItem(self, name):
                                #self.putName(name)
                                self.putValue(str('[%.2f, %.2f]' % p))
                                self.putType('cv::Point2f')
                                self.putNumChild(0)

            with SubItem(self, 'boundingrect'):
                tl = (min(p0[0], p1[0], p2[0], p3[0]),
                      min(p0[1], p1[1], p2[1], p3[1]))
                br = (max(p0[0], p1[0], p2[0], p3[0]),
                      max(p0[1], p1[1], p2[1], p3[1]))
                rWidth = br[0] - tl[0]
                rHeight = br[1] - tl[1]

                self.putValue('[%.2f, %.2f][%.2fx%.2f]' % (tl[0], tl[1], rWidth, rHeight))
                self.putNumChild(1)
                if self.isExpanded():
                    with Children(self):
                        with SubItem(self, 'top left'):
                            self.putValue(str('[%.2f, %.2f]' % tl))
                            self.putType('cv::Point2f')
                            self.putNumChild(0)
                        with SubItem(self, 'bottom right'):
                            self.putValue(str('[%.2f, %.2f]' % br))
                            self.putType('cv::Point2f')
                            self.putNumChild(0)
                        with SubItem(self, 'size'):
                            self.putValue(str('[%.2f, %.2f]' % (rWidth, rHeight)))
                            self.putType('cv::Sizef')
                            self.putNumChild(0)
                        with SubItem(self, 'area'):
                            self.putValue('%.2f' % (rWidth*rHeight))
                            self.putNumChild(0)


def qdump__cv__Point_(self, value):
    '''
    Pretty printer function for cv::Point_<Tp> class
    '''
    self.putNumChild(2)

    try:
        x = float(value['x'])
        y = float(value['y'])
        outValue = '[%.2f, %.2f]' % (x, y)
    except:
        x = int(value['x'])
        y = int(value['y'])
        outValue = '[%d, %d]' % (x, y)

    innerType = self.templateArgument(value.type, 0)

    self.putValue(outValue)
    if self.isExpanded():
        with Children(self):
            self.putSubItem('x', value['x'].cast(innerType))
            self.putSubItem('y', value['y'].cast(innerType))
            with SubItem(self, 'module'):
                self.putValue('%.2f' % (math.sqrt(x*x+y*y)))
                self.putNumChild(0)
            with SubItem(self, 'angle'):
                x = float(x)
                y = float(y)
                anglestr = '%.2f' % (math.degrees(math.atan2(y, x)))
                self.putValue(anglestr)
                self.putNumChild(0)


def qdump__cv__Rect_(self, value):
    '''
    Pretty printer function for cv::Rect_<Tp> class
    '''
    self.putNumChild(2)

    try:
        x = float(value['x'])
        y = float(value['y'])
        width = float(value['width'])
        height = float(value['height'])
        outValue = '[%.2f, %.2f][%.2fx%.2f]' % (x, y, width, height)
    except:
        x = int(value['x'])
        y = int(value['y'])
        width = int(value['width'])
        height = int(value['height'])
        outValue = '[%d, %d][%dx%d]' % (x, y, width, height)

    innerType = self.templateArgument(value.type, 0)

    self.putValue(outValue)
    if self.isExpanded():
        with Children(self):
            self.putSubItem('x', value['x'].cast(innerType))
            self.putSubItem('y', value['y'].cast(innerType))
            self.putSubItem('width', value['width'].cast(innerType))
            self.putSubItem('height', value['height'].cast(innerType))
            self.putSubItem('area', '%.2f' % (width*height))
            with SubItem(self, 'area'):
                self.putValue('%.2f' % (width*height))
                self.putNumChild(0)


def qdump__cv__Size_(self, value):
    '''
    Pretty printer function for cv::Size_<Tp> class
    '''
    self.putNumChild(2)

    try:
        width = float(value['width'])
        height = float(value['height'])
        outValue = '%.2fx%.2f' % (width, height)
    except:
        width = int(value['width'])
        height = int(value['height'])
        outValue = '%dx%d' % (width, height)

    innerType = self.templateArgument(value.type, 0)

    self.putValue(outValue)
    if self.isExpanded():
        with Children(self):
            self.putSubItem('width', value['width'].cast(innerType))
            self.putSubItem('height', value['height'].cast(innerType))
