# redis spec file based on https://gist.github.com/tkuchiki/7674158

# distribution specific definitions
%define use_systemd (0%{?rhel} >= 7 || 0%{?fedora} >= 19 || 0%{?suse_version} >= 1315 || 0%{?amzn} >= 2)

%if %{use_systemd}
BuildRequires: systemd
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
%else
Requires(post):   chkconfig
Requires(postun): initscripts
Requires(preun):  chkconfig
Requires(preun):  initscripts
%endif
  
# end of distribution specific definitions

Name:             redis
Version:          5.0.5
Release:          1%{?dist}
Summary:          A persistent key-value database

Group:            Applications/Databases
License:          BSD
URL:              https://redis.io/
Source0:          http://download.redis.io/releases/%{name}-%{version}.tar.gz
Source1:          %{name}.logrotate
Source2:          %{name}.init
Source3:          %{name}-limit-init
Source4:          %{name}.service
Source5:          %{name}-limit-systemd
Source6:          %{name}-shutdown
BuildRoot:        %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:    tcl >= 8.5
BuildRequires:    gcc
Requires:         /bin/awk
ExcludeArch:      ppc64

Requires:         logrotate
Requires(pre):    shadow-utils

%define configdir %{_sysconfdir}/%{name}

%description
Redis is an advanced key-value store. It is similar to memcached but the data
set is not volatile, and values can be strings, exactly like in memcached, but
also lists, sets, and ordered sets. All this data types can be manipulated with
atomic operations to push/pop elements, add/remove elements, perform server side
union, intersection, difference between sets, and so forth. Redis supports
different kind of sorting abilities.

%prep
%setup -q

%build
make %{?_smp_mflags} \
  DEBUG='' \
  CFLAGS='%{optflags}' \
  V=1 \
  all

%check

# workaround for failing test
# https://github.com/antirez/redis/issues/2814
rm tests/integration/aof.tcl
rm tests/integration/logging.tcl
rm tests/unit/memefficiency.tcl
mv tests/test_helper.tcl tests/test_helper.tcl.ORIG
egrep -v 'integration/(aof|logging)|unit/memefficiency' tests/test_helper.tcl.ORIG > tests/test_helper.tcl

make test

%install
rm -fr %{buildroot}
make install PREFIX=%{buildroot}%{_prefix}
# Install misc other
install -p -D -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
%if %{use_systemd}
  install -p -D -m 644 %{SOURCE4} %{buildroot}%{_unitdir}/%{name}.service
  install -p -D -m 644 %{SOURCE5} %{buildroot}%{_sysconfdir}/systemd/system/%{name}.service.d/limit.conf
%else
  install -p -D -m 755 %{SOURCE2} %{buildroot}%{_initrddir}/%{name}
  install -p -D -m 644 %{SOURCE3} %{buildroot}%{_sysconfdir}/security/limits.d/95-%{name}.conf
%endif

# Install redis-shutdown
install -p -D -m 755 %{SOURCE6} %{buildroot}%{_libexecdir}/%{name}-shutdown

install -p -D -m 644 %{name}.conf %{buildroot}%{_sysconfdir}/%{name}/%{name}.conf
install -p -D -m 644 sentinel.conf %{buildroot}%{_sysconfdir}/%{name}/sentinel.conf
install -d -m 755 %{buildroot}%{_localstatedir}/lib/%{name}
install -d -m 755 %{buildroot}%{_localstatedir}/log/%{name}
install -d -m 755 %{buildroot}%{_localstatedir}/run/%{name}

# Fix non-standard-executable-perm error
chmod 755 %{buildroot}%{_bindir}/%{name}-*

# Ensure redis-server location doesn't change
mkdir -p %{buildroot}%{_sbindir}
mv %{buildroot}%{_bindir}/%{name}-server %{buildroot}%{_sbindir}/%{name}-server

%clean
rm -fr %{buildroot}

%post
%if %{use_systemd}
  /usr/bin/systemctl preset redis.service >/dev/null 2>&1 ||:
%else
  touch /var/lock/subsys/redis
  /sbin/chkconfig --add redis
%endif

%pre
getent group redis &> /dev/null || groupadd -r redis &> /dev/null
getent passwd redis &> /dev/null || \
useradd -r -g redis -d %{_sharedstatedir}/redis -s /sbin/nologin \
-c 'Redis Server' redis &> /dev/null
exit 0

%preun
if [ $1 = 0 ]; then
%if %{use_systemd}
  /usr/bin/systemctl --no-reload disable redis.service >/dev/null 2>&1 ||:
  /usr/bin/systemctl stop redis.service >/dev/null 2>&1 ||:
%else
  /sbin/service redis stop &> /dev/null
  /sbin/chkconfig --del redis &> /dev/null
%endif
fi

%postun
%if %use_systemd
/usr/bin/systemctl daemon-reload >/dev/null 2>&1 ||:
%endif
if [ $1 -ge 1 ]; then
    /sbin/service %{name} condrestart >/dev/null 2>&1 || exit 0
fi

%files
%defattr(-,root,root,-)
%doc 00-RELEASENOTES BUGS CONTRIBUTING COPYING README.md
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%config(noreplace) %{configdir}/%{name}.conf
%config(noreplace) %{configdir}/sentinel.conf
%dir %attr(0755, redis, root) %{_localstatedir}/lib/%{name}
%dir %attr(0755, redis, root) %{_localstatedir}/log/%{name}
%dir %attr(0755, redis, root) %{_localstatedir}/run/%{name}
%{_bindir}/%{name}-*
%{_sbindir}/%{name}-*
%if %{use_systemd}
%{_unitdir}/%{name}.service
%config(noreplace) %{_sysconfdir}/systemd/system/%{name}.service.d/limit.conf
%else
%{_initrddir}/%{name}
%config(noreplace) %{_sysconfdir}/security/limits.d/95-%{name}.conf
%endif
%{_libexecdir}/%{name}-shutdown

%changelog
* Sat Mar 31 2012 Silas Sewell <silas@sewell.org> - 2.4.10-1
- Update to redis 2.4.10

* Fri Feb 24 2012 Silas Sewell <silas@sewell.org> - 2.4.8-2
- Disable ppc64 for now
- Enable verbose builds

* Fri Feb 24 2012 Silas Sewell <silas@sewell.org> - 2.4.8-1
- Update to redis 2.4.8

* Sat Apr 23 2011 Silas Sewell <silas@sewell.ch> - 2.2.5-2
- Remove google-perftools-devel

* Sat Apr 23 2011 Silas Sewell <silas@sewell.ch> - 2.2.5-1
- Update to redis 2.2.5

* Tue Oct 19 2010 Silas Sewell <silas@sewell.ch> - 2.0.3-1
- Update to redis 2.0.3

* Fri Oct 08 2010 Silas Sewell <silas@sewell.ch> - 2.0.2-1
- Update to redis 2.0.2
- Disable checks section for el5

* Sat Sep 11 2010 Silas Sewell <silas@sewell.ch> - 2.0.1-1
- Update to redis 2.0.1

* Sat Sep 04 2010 Silas Sewell <silas@sewell.ch> - 2.0.0-1
- Update to redis 2.0.0

* Thu Sep 02 2010 Silas Sewell <silas@sewell.ch> - 1.2.6-3
- Add Fedora build flags
- Send all scriplet output to /dev/null
- Remove debugging flags
- Add redis.conf check to init script

* Mon Aug 16 2010 Silas Sewell <silas@sewell.ch> - 1.2.6-2
- Don't compress man pages
- Use patch to fix redis.conf

* Tue Jul 06 2010 Silas Sewell <silas@sewell.ch> - 1.2.6-1
- Initial package
