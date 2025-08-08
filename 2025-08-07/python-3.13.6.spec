Name:       Python
Summary:    Version 3.13 of the python interpreter
Version:    3.13.6
Release:    1
License:    Python-2.0.1
Source0:    %{name}-%{version}.tgz
URL:        https://www.python.org

Requires: openssl readline libuuid xz
Buildrequires: openssl-devel readline-devel libuuid-devel xz-devel

%description
Python is an interpreted, interactive, object-oriented programming language. This package contains
most of the need a programmable interface and standard Python modules.

%prep
tar -xvf %{name}-%{version}.tgz

%build
mkdir build
cd build
../%{name}-%{version}/configure --prefix=/usr/local --enable-optimizations --with-openssl=/usr/
make %{?_smp_mflags}

%install
cd build
DESTDIR=$RPM_BUILD_ROOT make install

%files
%defattr(-,root,root,-)
/usr/local/
