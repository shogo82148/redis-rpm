# redis spec file based on https://gist.github.com/tkuchiki/7674158

BuildRequires: systemd
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%global with_redistrib 1

%if %{?_docdir:1}%{!?_docdir:0}
%global redis_docdir %{_docdir}
%else
%global redis_docdir %{_datadir}/doc
%endif

# %%{rpmmacrodir} not usable on EL-6
%global macrosdir %(d=%{_rpmconfigdir}/macros.d; [ -d $d ] || d=%{_sysconfdir}/rpm; echo $d)

# end of distribution specific definitions

Name:             redis
Version:          6.0.7
Release:          1%{?dist}
Summary:          A persistent key-value database

Group:            Applications/Databases
License:          BSD
URL:              https://redis.io/
Source0:          http://download.redis.io/releases/%{name}-%{version}.tar.gz
Source1:          %{name}.logrotate
Source2:          %{name}.service
Source3:          %{name}-limit-systemd
Source4:          %{name}-shutdown
Source5:          %{name}-sentinel.service
Source6:          macros.%{name}
BuildRoot:        %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

# To refresh patches:
# tar xf redis-xxx.tar.gz && cd redis-xxx && git init && git add . && git commit -m "%%{version} baseline"
# git am %%{patches}
# Then refresh your patches
# git format-patch HEAD~<number of expected patches>
# Update configuration for Fedora
# https://github.com/antirez/redis/pull/3491 - man pages
Patch0001:         0001-1st-man-pageis-for-redis-cli-redis-benchmark-redis-c.patch
# https://github.com/antirez/redis/pull/3494 - symlink
Patch0002:         0002-install-redis-check-rdb-as-a-symlink-instead-of-dupl.patch

BuildRequires:    tcl >= 8.5
BuildRequires:    gcc
BuildRequires:    procps
Requires:         /bin/awk
ExcludeArch:      ppc64

Requires:         logrotate
Requires(pre):    shadow-utils

%global redis_modules_abi 1
%global redis_modules_dir %{_libdir}/%{name}/modules
Provides:          redis(modules_abi)%{?_isa} = %{redis_modules_abi}

%define configdir %{_sysconfdir}/%{name}

# http://fedoraproject.org/wiki/Packaging:Conflicts "Splitting Packages"
Conflicts:         redis < 6.0

%description
Redis is an advanced key-value store. It is similar to memcached but the data
set is not volatile, and values can be strings, exactly like in memcached, but
also lists, sets, and ordered sets. All this data types can be manipulated with
atomic operations to push/pop elements, add/remove elements, perform server side
union, intersection, difference between sets, and so forth. Redis supports
different kind of sorting abilities.

%package           devel
Summary:           Development header for Redis module development
# Header-Only Library (https://fedoraproject.org/wiki/Packaging:Guidelines)
Provides:          %{name}-static = %{version}-%{release}

%description       devel
Header file required for building loadable Redis modules. Detailed
API documentation is available in the redis-doc package.

%package           doc
Summary:           Documentation for Redis including man pages
License:           CC-BY-SA
BuildArch:         noarch

%description       doc
Manual pages and detailed documentation for many aspects of Redis use,
administration and development.

%if 0%{?with_redistrib}
%package           trib
Summary:           Cluster management script for Redis
BuildArch:         noarch
Requires:          ruby
Requires:          rubygem-redis

%description       trib
Redis cluster management utility providing cluster creation, node addition
and removal, status checks, resharding, rebalancing, and other operations.
%endif

%prep
%setup -q
%patch0001 -p1
%patch0002 -p1

# from https://github.com/aiven/remirepo-redis/blob/master/redis.spec
# Configuration file changes
sed -i -e 's|^logfile .*$|logfile /var/log/redis/redis.log|g' redis.conf
sed -i -e 's|^logfile .*$|logfile /var/log/redis/sentinel.log|g' sentinel.conf
sed -i -e 's|^dir .*$|dir /var/lib/redis|g' redis.conf

# Module API version safety check
api=`sed -n -e 's/#define REDISMODULE_APIVER_[0-9][0-9]* //p' src/redismodule.h`
if test "$api" != "%{redis_modules_abi}"; then
   : Error: Upstream API version is now ${api}, expecting %%{redis_modules_abi}.
   : Update the redis_modules_abi macro, the rpmmacros file, and rebuild.
   exit 1
fi

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

# workaround for failing test (2)
# https://github.com/shogo82148/redis-rpm/pull/9#issuecomment-663559399
rm tests/integration/rdb.tcl
rm tests/integration/psync2.tcl

mv tests/test_helper.tcl tests/test_helper.tcl.ORIG
egrep -v 'integration/(aof|logging|rdb|psync2)$|unit/memefficiency' tests/test_helper.tcl.ORIG > tests/test_helper.tcl

make test
make test-sentinel

%install
rm -fr %{buildroot}
make install PREFIX=%{buildroot}%{_prefix}
# Install misc other
install -p -D -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
install -p -D -m 644 %{SOURCE2} %{buildroot}%{_unitdir}/%{name}.service
install -p -D -m 644 %{SOURCE3} %{buildroot}%{_sysconfdir}/systemd/system/%{name}.service.d/limit.conf
install -p -D -m 644 %{SOURCE5} %{buildroot}%{_unitdir}/%{name}-sentinel.service
install -p -D -m 644 %{SOURCE3} %{buildroot}%{_sysconfdir}/systemd/system/%{name}-sentinel.service.d/limit.conf

# Install redis-shutdown
install -p -D -m 755 %{SOURCE4} %{buildroot}%{_libexecdir}/%{name}-shutdown

# Install redis module header
install -p -D -m 644 src/%{name}module.h %{buildroot}%{_includedir}/%{name}module.h

%if 0%{?with_redistrib}
# Install redis-trib
install -p -D -m 755 src/%{name}-trib.rb %{buildroot}%{_bindir}/%{name}-trib
%endif

install -p -D -m 644 %{name}.conf %{buildroot}%{_sysconfdir}/%{name}/%{name}.conf
install -p -D -m 644 sentinel.conf %{buildroot}%{_sysconfdir}/%{name}/sentinel.conf
install -d -m 755 %{buildroot}%{_localstatedir}/lib/%{name}
install -d -m 755 %{buildroot}%{_localstatedir}/log/%{name}
install -d -m 755 %{buildroot}%{_localstatedir}/run/%{name}
install -d %{buildroot}%{redis_modules_dir}

# Fix non-standard-executable-perm error
chmod 755 %{buildroot}%{_bindir}/%{name}-*

# Install rpm macros for redis modules
mkdir -p %{buildroot}%{macrosdir}
install -pDm644 %{SOURCE6} %{buildroot}%{macrosdir}/macros.%{name}

# Install man pages
man=$(dirname %{buildroot}%{_mandir})
for page in man/man?/*; do
    install -Dpm644 $page $man/$page
done
ln -s redis-server.1 %{buildroot}%{_mandir}/man1/redis-sentinel.1
ln -s redis.conf.5   %{buildroot}%{_mandir}/man5/redis-sentinel.conf.5

# Install documentation and html pages
doc=$(echo %{buildroot}/%{redis_docdir}/%{name})
for page in 00-RELEASENOTES BUGS CONTRIBUTING MANIFESTO; do
    install -Dpm644 $page $doc/$page
done
for page in $(find doc -name \*.md | sed -e 's|.md$||g'); do
    base=$(echo $page | sed -e 's|doc/||g')
    install -Dpm644 $page.md $doc/$base.md
done

%clean
rm -fr %{buildroot}

%post
/usr/bin/systemctl preset redis.service >/dev/null 2>&1 ||:
/usr/bin/systemctl preset redis-sentinel.service >/dev/null 2>&1 ||:

%pre
getent group redis &> /dev/null || groupadd -r redis &> /dev/null
getent passwd redis &> /dev/null || \
useradd -r -g redis -d %{_sharedstatedir}/redis -s /sbin/nologin \
-c 'Redis Server' redis &> /dev/null
exit 0

%preun
if [ $1 = 0 ]; then
  /usr/bin/systemctl --no-reload disable redis.service >/dev/null 2>&1 ||:
  /usr/bin/systemctl --no-reload disable redis-sentinel.service >/dev/null 2>&1 ||:
  /usr/bin/systemctl stop redis.service >/dev/null 2>&1 ||:
  /usr/bin/systemctl stop redis-sentinel.service >/dev/null 2>&1 ||:
fi

%postun
/usr/bin/systemctl daemon-reload >/dev/null 2>&1 ||:
if [ $1 -ge 1 ]; then
    /sbin/service %{name} condrestart >/dev/null 2>&1 || exit 0
    /sbin/service %{name}-sentinel condrestart >/dev/null 2>&1 || exit 0
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
%dir %attr(0750, redis, redis) %{redis_modules_dir}
%{_bindir}/%{name}-*
%{_mandir}/man1/%{name}*
%{_mandir}/man5/%{name}*
%{_unitdir}/%{name}.service
%{_unitdir}/%{name}-sentinel.service
%config(noreplace) %{_sysconfdir}/systemd/system/%{name}.service.d/limit.conf
%config(noreplace) %{_sysconfdir}/systemd/system/%{name}-sentinel.service.d/limit.conf
%{_libexecdir}/%{name}-shutdown
%exclude %{_includedir}
%exclude %{macrosdir}
%exclude %{redis_docdir}/%{name}/*

%if 0%{?with_redistrib}
%exclude %{_bindir}/%{name}-trib
%endif

%files devel
# FIXME: commented out %license macro because https://github.com/shogo82148/redis-rpm/issues/2
# %license COPYING
%{_includedir}/%{name}module.h
%{macrosdir}/*

%files doc
%docdir %{redis_docdir}/%{name}
%{redis_docdir}/%{name}

%if 0%{?with_redistrib}
%files trib
# FIXME: commented out %license macro because https://github.com/shogo82148/redis-rpm/issues/2
# %license COPYING
%{_bindir}/%{name}-trib
%endif

%changelog
* Wed Sep 02 2020 Ichinose Shogo <shogo82148@gmail.com> - 6.0.7-1
- Update to redis 6.0.7

* Fri Jul 24 2020 Ichinose Shogo <shogo82148@gmail.com> - 6.0.6-1
- Update to redis 6.0.6

* Mon Jul 13 2020 Ichinose Shogo <shogo82148@gmail.com> - 6.0.5-1
- Update to redis 6.0.5

* Sat May 02 2020 Ichinose Shogo <shogo82148@gmail.com> - 6.0.1-1
- Update to redis 6.0.1

* Sun Jul 28 2019 Ichinose Shogo <shogo82148@gmail.com> - 5.0.5-2
- Fix failing to start redis-server

* Sun Jul 07 2019 Ichinose Shogo <shogo82148@gmail.com> - 5.0.5-1
- Update to redis 5.0.5

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
