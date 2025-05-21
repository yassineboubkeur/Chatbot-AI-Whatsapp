#!/bin/bash

#run this command to ensure that all pg dev tool are installed

sudo apt-get install postgresql-server-dev-all


#clone the pgvector extension
git clone https://github.com/pgvector/pgvector.git


#install extension
cd pgvector
make
sudo make install
