
[![Build Status](https://travis-ci.com/shogo82148/redis-rpm.svg?branch=master)](https://travis-ci.com/shogo82148/redis-rpm)

# Redis Unofficial RPM package builder

This provides [Redis](https://redis.io/) RPM spec file and required files e.g. SysVinit, systemd service etc. to build RPM for Amazon Linux 2.


## How to use prebuilt RPM

This has [Bintray RPM repository](https://bintray.com/beta/#/shogo82148/redis-rpm?tab=packages) so if you'd like to just install such a prebuilt package,
please put the following text into `/etc/yum.repos.d/bintray-shogo82148-redis-rpm.repo`.

Amazon Linux 2:

```ini
#bintray-shogo82148-redis-rpm - packages by shogo82148 from Bintray
[bintray-shogo82148-redis-rpm]
name=bintray-shogo82148-redis-rpm
baseurl=https://dl.bintray.com/shogo82148/redis-rpm/amazonlinux2/$releasever/$basearch/
gpgcheck=0
repo_gpgcheck=1
enabled=1
gpgkey=https://bintray.com/user/downloadSubjectPublicKey?username=shogo82148
```

Once the file is correctly saved, you can install packages in the repository by

```
yum install redis
```

or if you use Fedora

```
dnf install redis
```

## How to build RPM

If you have a docker environment, you can build RPMs by just running

```
make
```

If you'd like to build RPM for specific distribution, please run a command like following

```
make amazonlinux2
```

## License

This is under MIT License. Please see the LICENSE file for details.
