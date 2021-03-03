SOURCE_ARCHIVE := redis-6.2.1.tar.gz
TARGZ_FILE := redis.tar.gz
IMAGE_NAME := redis-package

.PHONY: all clean amazonlinux2 centos8

all: amazonlinux2 centos8
amazonlinux2: amazonlinux2.build
centos8: centos8.build

rpmbuild/SOURCES/$(SOURCE_ARCHIVE):
	curl -SL http://download.redis.io/releases/$(SOURCE_ARCHIVE) -o rpmbuild/SOURCES/$(SOURCE_ARCHIVE)

%.build: Dockerfile.% rpmbuild/SPECS/redis.spec rpmbuild/SOURCES/$(SOURCE_ARCHIVE) \
		rpmbuild/SOURCES/0001-1st-man-pageis-for-redis-cli-redis-benchmark-redis-c.patch \
		rpmbuild/SOURCES/0002-install-redis-check-rdb-as-a-symlink-instead-of-dupl.patch \
		rpmbuild/SOURCES/macros.redis rpmbuild/SOURCES/redis-limit-systemd \
		rpmbuild/SOURCES/redis-sentinel.service rpmbuild/SOURCES/redis-shutdown \
		rpmbuild/SOURCES/redis.logrotate rpmbuild/SOURCES/redis.service
	./scripts/build.sh $*

.PHONY: upload
upload:
	./scripts/upload.pl

clean:
	rm -rf *.build.bak *.build bintray tmp Dockerfile
	docker images | grep -q $(IMAGE_NAME)-amazonlinux2 && docker rmi $(IMAGE_NAME)-amazonlinux2 || true
	docker images | grep -q $(IMAGE_NAME)-centos8 && docker rmi $(IMAGE_NAME)-centos8 || true
