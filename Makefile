SOURCE_ARCHIVE := redis-7.0.1.tar.gz
TARGZ_FILE := redis.tar.gz
IMAGE_NAME := redis-package

.PHONY: all clean amazonlinux2 amazonlinux2022 centos7 almalinux8 almalinux9 rockylinux8 rockylinux9

all: amazonlinux2 amazonlinux2022 centos7 almalinux8 almalinux9 rockylinux8 rockylinux9
amazonlinux2: amazonlinux2.build
amazonlinux2022: amazonlinux2022.build
centos7: centos7.build
almalinux8: almalinux8.build
almalinux9: almalinux9.build
rockylinux8: rockylinux8.build
rockylinux9: rockylinux9.build

rpmbuild/SOURCES/$(SOURCE_ARCHIVE):
	curl -SL https://download.redis.io/releases/$(SOURCE_ARCHIVE) -o rpmbuild/SOURCES/$(SOURCE_ARCHIVE)

%.build: Dockerfile.% rpmbuild/SPECS/redis.spec rpmbuild/SOURCES/$(SOURCE_ARCHIVE) \
		rpmbuild/SOURCES/0001-1st-man-pageis-for-redis-cli-redis-benchmark-redis-c.patch \
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
	docker images | grep -q $(IMAGE_NAME)-amazonlinux2022 && docker rmi $(IMAGE_NAME)-amazonlinux2022 || true
	docker images | grep -q $(IMAGE_NAME)-centos7 && docker rmi $(IMAGE_NAME)-centos7 || true
	docker images | grep -q $(IMAGE_NAME)-almalinux8 && docker rmi $(IMAGE_NAME)-almalinux8 || true
	docker images | grep -q $(IMAGE_NAME)-almalinux9 && docker rmi $(IMAGE_NAME)-almalinux9 || true
	docker images | grep -q $(IMAGE_NAME)-rockylinux8 && docker rmi $(IMAGE_NAME)-rockylinux8 || true
	docker images | grep -q $(IMAGE_NAME)-rockylinux9 && docker rmi $(IMAGE_NAME)-rockylinux9 || true
