FROM centos:centos7.9.2009
RUN yum update -y
RUN yum install epel-release -y
RUN yum install httpd httpd-devel mariadb-server mariadb-client mariadb-devel -y

RUN yum groupinstall 'Development Tools' -y
RUN yum install bzip2-devel gdbm-devel libffi-devel libuuid-devel ncurses-devel openssl openssl-devel readline-devel sqlite-devel xz-devel zlib-devel --enablerepo=epel -y

WORKDIR /tmp
RUN curl -O https://www.python.org/ftp/python/3.8.16/Python-3.8.16.tar.xz
RUN tar xf Python-3.8.16.tar.xz 
WORKDIR /tmp/Python-3.8.16
RUN ./configure --enable-optimizations
RUN make && make install
WORKDIR /tmp 
RUN rm -rf Python-3.8.16.tar.xz Python-3.8.16/

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install Django opencv-python opencv-contrib-python mysqlclient pillow psutil rquests mod-wsgi-httpd mod_wsgi
