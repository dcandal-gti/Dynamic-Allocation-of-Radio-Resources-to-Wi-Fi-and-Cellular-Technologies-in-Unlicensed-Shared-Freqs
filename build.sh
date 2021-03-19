#!/bin/bash

## Prerequisites
sudo apt-get install g++ python3 python3-dev pkg-config sqlite3 python3-setuptools git qt5-default mercurial gir1.2-goocanvas-2.0 python-gi python-gi-cairo python-pygraphviz python3-gi python3-gi-cairo python3-pygraphviz gir1.2-gtk-3.0 ipython ipython3 openmpi-bin openmpi-common openmpi-doc libopenmpi-dev autoconf cvs bzr unrar gdb valgrind uncrustify doxygen graphviz imagemagick texlive texlive-extra-utils texlive-latex-extra texlive-font-utils dvipng latexmk python3-sphinx dia gsl-bin libgsl-dev libgsl23 libgslcblas0 tcpdump sqlite sqlite3 libsqlite3-dev libxml2 libxml2-dev cmake libc6-dev libc6-dev-i386 libclang-6.0-dev llvm-6.0-dev automake libgtk-3-dev vtun lxc uml-utilities libboost-signals-dev libboost-filesystem-dev python3-pip
python3 -m pip install --user cxxfilt
pip3 install distro
sudo apt-get install python-dev python3-dev

## Install
echo "export BAKE_HOME=`pwd`/bake" >> ~/.bashrc
echo "PATH=$PATH:$BAKE_HOME" >> ~/.bashrc
echo "PYTHONPATH=$PYTHONPATH:$BAKE_HOME" >> ~/.bashrc
source ~/.bashrc
./build.py --enable-examples
