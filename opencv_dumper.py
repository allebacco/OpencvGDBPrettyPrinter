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


def qdump__cv__Mat(self, value):
    self.putNumChild(1)

    depth_names = ['CV_8U', 'CV_8S', 'CV_16U', 'CV_16S', 'CV_32S', 'CV_32F', 'CV_64F', 'undefined']
    depth_type = ['unsigned char', 'char', 'unsigned short', 'short', 'int', 'float', 'double', 'void']
    #depth_py_type = ['B', 'b', 'H', 'h', 'i', 'f', 'd', 'i']
    depth_byte_size = [1, 1, 2, 2, 4, 4, 8, 8]

    flags = int(value['flags'])
    depth = flags & 7
    channels = 1 + (flags >> 3) & 63
    depth = min(depth, 7)
    cv_type_name = depth_names[depth]
    cv_type = depth_type[depth]
    #cv_py_type = depth_py_type[depth]

    cv_type_name += 'C%d' % channels

    rows = int(value['rows'])
    cols = int(value['cols'])
    #self.putValue(r"OpenCV image", encoding=0)
    self.putValue('%dx%d %s' % (cols, rows, cv_type_name))

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
                self.putNumChild(size)
                if self.isExpanded():
                    with Children(self, size, childType=vals_type):
                        s = 0
                        for i in range(0, rows):
                            for j in range(0, cols):
                                # Limit output to improve performance
                                if s > size:
                                    break
                                # Handle multiple channels
                                for c in range(0, channels):
                                    v = (p + i * cols * channels + j * channels + c).dereference()
                                    with SubItem(self, s):
                                        self.putName("[%3d,%3d][%d]" % (i, j, c))
                                        self.putValue(v)
                                s = s + 1

                            # Limit output to improve performance
                            if s > size:
                                break

            #self.putSubItem('dataend', value['dataend'])
            dataend = 0
            with SubItem(self, 'dataend'):
                p = value['dataend'].cast(self.lookupType('unsigned char').pointer())
                dataend = int(p)
                self.putValue('0x%X' % dataend)
                self.putType('unsigned char*')
                self.putNumChild(0)

            #self.putSubItem('datastart', value['datastart'])
            datastart = 0
            with SubItem(self, 'datastart'):
                p = value['datastart'].cast(self.lookupType('unsigned char').pointer())
                datastart = int(p)
                self.putValue('0x%X' % datastart)
                self.putType('unsigned char*')
                self.putNumChild(0)

            #self.putSubItem('datalimit', value['datalimit'])
            with SubItem(self, 'datalimit'):
                p = value['datalimit'].cast(self.lookupType('unsigned char').pointer())
                datalimit = int(p)
                self.putValue('0x%X' % datalimit)
                self.putType('unsigned char*')
                self.putNumChild(0)

            # Put metadata to improve output informations
            data_byte_size = depth_byte_size[depth]
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
