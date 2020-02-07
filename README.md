# PyVuka

PyVuka is a command line based and scriptable data fitting program.  This software can be used for global and unlinked fitting of custom data models, data transforms, plotting, reading, and writing files.  Custom python-native modules can also be written and will be automatically imported upon deposition in the Modules directory.

## Installation

Manual installation requires anaconda python 3.6

## Example as PyVuka as a python Library

#### Code
```python
# use PyVuka code base as a library
import ModuleLink.toPyVuka as pvk

# initialize pyvuka
pvk.initialize_instance()
# create new data buffer
buffer = pvk.new_buffer()
# populate x and y data vectors
buffer.data.x.set([0,1,2,3,4,5,6,7,8,9])
buffer.data.y.set([0,0.5,1.75,3.5,4,4.85,6.2,7.1,7.9,9.3])
# add axes titles
buffer.plot.axis.x.title.set("random int")
buffer.plot.axis.y.title.set("random float")
# add buffer to data matrix
pvk.add_buffer_to_datamatrix(buffer)
# select function 27 (Y=mx+b)
pvk.run_pyvuka_command('fun 27 0')
# alter function 27 parameters. "For buffer 1 through buffer 1, slope guess = 1, y-intercept guess = 1"
pvk.run_pyvuka_command('ap 1 1 1 1')
# fit all data in matrix with function 27
pvk.run_pyvuka_command('fit')
# Show plot on screen and save to drive
pvk.show_plot(1)
pvk.save_plot(1, "test.png")
```
#### Ouput
<img src="https://www.bostonautolytics.com/assets/img/test_show.png" alt="Saved Imaged" />
<img src="https://www.bostonautolytics.com/assets/img/test.png" alt="Saved Imaged" />

## Example of using PyVuka as a command line program

#### Code
```python
# Use Pyvuka as a command line app
import PyVuka.pyvuka as app

app.start()
```
#### Ouput
<img src="https://www.bostonautolytics.com/assets/img/test_app.png" alt="Saved Imaged" />


## License
Copyright (c) 2020 BostonAutoLytics LLC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to use
this software freely for personal and research use ONLY. This license does
NOT PERMIT uses including resale, modify, merge, publish, distribute,
sublicense, and/or selling copies in part or in-whole of this software.
Re-sale or inclusion in commercial software is subject to licensing agreements
made with Boston AutoLytics, LLC.
For more information e-mail info@BostonAutoLytics.com

PERSONAL USE:
    This software may be used and modified without restriction.

RESEARCH USE:
    If this software is used to generate results published in an
    academic journal or similar professional publication, please cite in-line
    with the version number being used. Example: "Data was fit with a 2:1 binding
    model using the python package PyVuka v.1.0 (Boston AutoLytics, LLC)".  This
    software may be included in-whole or in-part within publicly available and
    non-commercial distributions. Inclusion in products that are sold require
    a licensing agreement (contact: info@BostonAutoLytics.com).

COMMERCIAL USE:
    PROHIBITED WITHOUT LICENSING AGREEMENT. Contact: info@BostonAutoLytics.com

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
