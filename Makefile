SOURCE_ARCHIVE := redis-6.0.1.tar.gz
TARGZ_FILE := redis.tar.gz
IMAGE_NAME := redis-package
amazonlinux2: IMAGE_NAME := $(IMAGE_NAME)-amazonlinux2

.PHONY: all clean amazonlinux2 bintray

all: amazonlinux2 centos6 centos7 centos8
amazonlinux2: amazonlinux2.build
centos6: centos6.build
centos7: centos7.build
centos8: centos8.build

rpmbuild/SOURCES/$(SOURCE_ARCHIVE):
	curl -SL http://download.redis.io/releases/$(SOURCE_ARCHIVE) -o rpmbuild/SOURCES/$(SOURCE_ARCHIVE)

%.build: Dockerfile.% rpmbuild/SPECS/redis.spec rpmbuild/SOURCES/$(SOURCE_ARCHIVE)
	[ -d $@.bak ] && rm -rf $@.bak || :
	[ -d $@ ] && mv $@ $@.bak || :
	tar -czf - Dockerfile.$* rpmbuild | docker build --file Dockerfile.$* -t $(IMAGE_NAME) -
	docker run --name $(IMAGE_NAME)-tmp $(IMAGE_NAME)
	mkdir -p tmp
	docker wait $(IMAGE_NAME)-tmp
	docker cp $(IMAGE_NAME)-tmp:/tmp/$(TARGZ_FILE) tmp
	docker rm $(IMAGE_NAME)-tmp
	mkdir $@
	tar -xzf tmp/$(TARGZ_FILE) -C $@
	rm -rf tmp Dockerfile
	docker images | grep -q $(IMAGE_NAME) && docker rmi $(IMAGE_NAME) || true

bintray:
	./scripts/build_bintray_json.bash \
		redis \
		redis-debuginfo \
		redis-devel \
		redis-doc \
		redis-trib

clean:
	rm -rf *.build.bak *.build bintray tmp Dockerfile
	docker images | grep -q $(IMAGE_NAME)-amazonlinux2 && docker rmi $(IMAGE_NAME)-amazonlinux2 || true
	docker images | grep -q $(IMAGE_NAME)-centos6 && docker rmi $(IMAGE_NAME)-centos6 || true
	docker images | grep -q $(IMAGE_NAME)-centos7 && docker rmi $(IMAGE_NAME)-centos7 || true
	docker images | grep -q $(IMAGE_NAME)-centos8 && docker rmi $(IMAGE_NAME)-centos8 || true
