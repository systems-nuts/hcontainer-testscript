#!/bin/bash

VERSION=5.0.4

rm -rf redis-$VERSION.tar.gz redis &> /dev/null

wget http://download.redis.io/releases/redis-$VERSION.tar.gz
tar xf redis-$VERSION.tar.gz
mv redis-$VERSION redis
cd redis
PREFIX=$PWD/prefix make -j`nproc` install
cd -

