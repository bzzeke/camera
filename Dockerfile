FROM alpine:3.10

RUN \
	echo http://nl.alpinelinux.org/alpine/edge/testing >> /etc/apk/repositories && \
	apk update && \
	apk add \
	bash \
	tzdata \
	libass \
	libstdc++ \
	libpng \
	libjpeg \
	xvidcore \
	x264-libs \
	x265 \
	libvpx \
	libvorbis \
	opus \
	lame \
	# fdk-aac \
	jasper-libs \
	freetype \
	python3 \
	gstreamer \
    gst-plugins-base \
	gst-plugins-good \
	gst-plugins-bad \
    gst-libav \
    gstreamer-vaapi \
	libffi \
	hdf5 \
	llvm8-libs

# Install build tools
RUN	apk add --virtual build-deps \
	coreutils \
	# fdk-aac-dev \
	freetype-dev \
	x264-dev \
	x265-dev \
	yasm \
	yasm-dev \
	libogg-dev \
	libvorbis-dev \
	opus-dev \
	libvpx-dev \
	lame-dev \
	xvidcore-dev \
	libass-dev \
	openssl-dev \
	musl-dev \
	make \
	cmake \
	gcc \
	g++ \
	build-base \
	libjpeg-turbo-dev \
	libpng-dev \
	clang-dev \
	clang \
	linux-headers \
	git \
	curl \
	perl \
	python3-dev \
    gstreamer-dev \
    gst-plugins-base-dev \
	gst-plugins-bad-dev \
	glib \
	ffmpeg-dev \
	libc-dev \
	libffi-dev \
	llvm8-dev \
	hdf5-dev

# FFmpeg
RUN	export SRC=/usr \
	export FFMPEG_VERSION=4.1.3 \
	DIR=$(mktemp -d) && cd ${DIR} && \
	curl -Os http://ffmpeg.org/releases/ffmpeg-${FFMPEG_VERSION}.tar.gz && \
	tar xzvf ffmpeg-${FFMPEG_VERSION}.tar.gz && \
	cd ffmpeg-${FFMPEG_VERSION} && \
	./configure --prefix="${SRC}" --extra-cflags="-I${SRC}/include" --extra-ldflags="-L${SRC}/lib" --bindir="${SRC}/bin" \
		--extra-libs=-ldl --enable-version3 --enable-libmp3lame --enable-pthreads --enable-libx264 --enable-libxvid --enable-gpl \
		--enable-postproc --enable-nonfree --enable-avresample --disable-debug --enable-small --enable-openssl \
		--enable-libx265 --enable-libopus --enable-libvorbis --enable-libvpx --enable-libfreetype --enable-libass \
		--enable-shared --enable-pic --disable-logging && \
	make -j8 && \
	make install && \
	make distclean && \
	hash -r && \
	cd /tmp && \
	rm -rf ${DIR}

# PIP
RUN	pip3 install --no-cache-dir \
	Cython \
	numpy \
	Pillow \
	av \
	pyzmq \
	pickledb

RUN	pip3 install --no-cache-dir	matplotlib
RUN	pip3 install --no-cache-dir numba
RUN pip3 install https://github.com/AfsmNGhr/alpine-tensorflow/releases/download/tensorflow-1.13.2/tensorflow-1.13.2-cp37-cp37m-linux_x86_64.whl
# RUN pip3 install https://storage.googleapis.com/intel-optimized-tensorflow/intel_tensorflow-1.14.0-cp37-cp37m-manylinux1_x86_64.whl

## OpenCV
RUN	export OPENCV_VERSION=3.4.6 \
	export PYTHON_VERSION=`python3 -c 'import platform; print(".".join(platform.python_version_tuple()[:2]))'` \
	export CC=/usr/bin/clang \
	export CXX=/usr/bin/clang++ && \
	# Contrib
	CONTRIB_DIR=$(mktemp -d) && cd ${CONTRIB_DIR} && \
	curl -SL -O https://github.com/opencv/opencv_contrib/archive/${OPENCV_VERSION}.tar.gz && \
	tar xzvf ${OPENCV_VERSION}.tar.gz && \
	DIR=$(mktemp -d) && cd ${DIR} && \
	curl -SL -O https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.tar.gz && \
	tar xzvf ${OPENCV_VERSION}.tar.gz && \
	cd opencv-${OPENCV_VERSION} && \
	sed -i "s/av_log_set_level(AV_LOG_ERROR);/av_log_set_level(AV_LOG_QUIET);/g" modules/videoio/src/cap_ffmpeg_impl.hpp && \
	mkdir build && \
	cd build && \
	cmake \
		-D WITH_GSTREAMER=ON \
		-D WITH_FFMPEG=ON \
	    -D OPENCV_EXTRA_MODULES_PATH=${CONTRIB_DIR}/opencv_contrib-${OPENCV_VERSION}/modules \
		-D CMAKE_BUILD_TYPE=RELEASE \
		-D INSTALL_C_EXAMPLES=OFF \
		-D INSTALL_PYTHON_EXAMPLES=OFF \
		-D CMAKE_INSTALL_PREFIX=/usr \
		-D BUILD_EXAMPLES=OFF \
		-D BUILD_opencv_python3=ON \
		-D PYTHON_DEFAULT_EXECUTABLE=/usr/bin/python3 \
		-D PYTHON_INCLUDE_DIRS=/usr/include/python${PYTHON_VERSION}m \
		-D PYTHON_EXECUTABLE=/usr/bin/python${PYTHON_VERSION} \
		-D PYTHON_LIBRARY=/usr/lib/libpython${PYTHON_VERSION}m.so \
		.. && \
	make -j8 && \
	make install && \
	cd /tmp && \
	rm -rf ${DIR}

# Detector
ADD app/rt /tmp/rt
RUN cd /tmp/rt && make
RUN cp /tmp/rt/bounding_boxes/bin/libmotion_detector_optimization.so /usr/lib
RUN rm -fr /tmp/rt

# Cleaning up
RUN	apk del build-deps && \
	rm -rf /var/cache/apk/*

WORKDIR /app
VOLUME /app

#run gst-inspect to avoid gst segfault
# CMD ["python3", "-u", "/app/main.py"]
CMD ["sh"]
