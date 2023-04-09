Steps to install Graph Tool on Ubuntu 22.10:

- download latest graph tool release (cloning repo won't work): https://graph-tool.skewed.de/download
- unzip and move to graph tool directory
- create and activate virtualenv
- `sudo apt-get install libboost-all-dev libcgal-dev libcairomm-1.0-dev libsparsehash-dev libgirepository1.0-dev`
- `pip install scipy numpy matplotlib pycairo PyGObject`
* `./configure`
* `make`
* `make install`
