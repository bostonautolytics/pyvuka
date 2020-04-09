# PyVuka

PyVuka is a command line based and scriptable data fitting program.  This software can be used for global and unlinked fitting of custom data models, data transforms, plotting, reading, and writing files.  Custom python-native modules can also be written and will be automatically imported upon deposition in the Modules directory.

This project has been supported by the Institute of Protein Innovation, Boston AutoLytics, Adimab, Microgradient Fluidics, UMass Medical School, and the University of Pennsylvania

## Installation

pip install PyVuka

## Example as PyVuka as a python Library

#### Code
```python
import PyVuka.ModuleLink.toPyVuka as pyvuka  # use PyVuka code base as a library

pvk = pyvuka.initialize_instance()  # initialize pyvuka
buffer = pvk.new_buffer()  # create new data buffer
buffer.data.x.set([0,1,2,3,4,5,6,7,8,9])  # populate x and y data vectors
buffer.data.y.set([0,0.5,1.75,3.5,4,4.85,6.2,7.1,7.9,9.3])
buffer.plot.axis.x.title.set("random int")  # add axes titles
buffer.plot.axis.y.title.set("random float")
pvk.add_buffer_to_datamatrix(buffer)  # add buffer to data matrix
pvk.run_pyvuka_command('fun 27 0')  # select function 27 (Y=mx+b) ; in app mode type 'fun' to see list of available functions
pvk.run_pyvuka_command('ap 1 1 1 1')  # alter parameters of function 27. "For buffer 1 through buffer 1, slope guess = 1, y-intercept guess = 1"
pvk.run_pyvuka_command('fit')  # fit all data in matrix with function 27
pvk.show_plot(1) # Show plot of buffer 1 on screen and save to drive
pvk.save_plot(1, "test.png")
```
#### Ouput
<img src="http://www.bostonautolytics.com/assets/img/test_show.png" alt="Saved Imaged" />
<img src="http://www.bostonautolytics.com/assets/img/test.png" alt="Saved Imaged" />

## Example of using PyVuka as a command line program

#### Code
```python
import PyVuka.app as app # Use Pyvuka as a command line app 

app.start()
```
#### Ouput
<img src="http://www.bostonautolytics.com/assets/img/test_app.png" alt="Saved Imaged" />


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
