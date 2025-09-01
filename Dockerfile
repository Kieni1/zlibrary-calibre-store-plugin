# This Dockerfile creates a static build of the Tor binary for ARMv7 (like the Remarkable 2).
# It compiles libevent and openssl from source to ensure static linking.

# Use a Debian base image which has better support for cross-compilation.
FROM debian:bullseye-slim

# Set environment variables for easy version management and architecture targeting.
ENV ARM_ARCH=arm-linux-gnueabihf
ENV OPENSSL_VERSION=1.1.1w
ENV LIBEVENT_VERSION=2.1.12-stable
ENV ZLIB_VERSION=1.3.1
ENV TOR_VERSION=0.4.8.12

# Install necessary build tools and cross-compilation toolchains.
RUN apt-get update \
    && apt-get install -y \
    build-essential \
    automake \
    libtool \
    pkg-config \
    curl \
    xz-utils \
    git \
    && dpkg --add-architecture armhf \
    && apt-get update \
    && apt-get install -y \
    crossbuild-essential-armhf \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the destination directory for the static dependencies.
WORKDIR /usr/local/armv7-static-build

# Download, compile, and install static OpenSSL.
RUN curl -sSL --fail -O https://www.openssl.org/source/openssl-$OPENSSL_VERSION.tar.gz \
    && tar -xzf openssl-$OPENSSL_VERSION.tar.gz \
    && cd openssl-$OPENSSL_VERSION \
    && ./Configure linux-generic32 --cross-compile-prefix=arm-linux-gnueabihf- -static --prefix=/usr/local/armv7-static-build/openssl no-shared enable-threads \
    && make CFLAGS='-DOPENSSL_THREADS' LDFLAGS="-pthread" \
    && make install_sw \
    && cd ..

# Download, compile, and install static Libevent.
RUN curl -sSL --fail -O https://github.com/libevent/libevent/releases/download/release-$LIBEVENT_VERSION/libevent-$LIBEVENT_VERSION.tar.gz \
    && tar -xzf libevent-$LIBEVENT_VERSION.tar.gz \
    && cd libevent-$LIBEVENT_VERSION \
    && PKG_CONFIG_PATH=/usr/local/armv7-static-build/openssl/lib/pkgconfig \
    CFLAGS="-I/usr/local/armv7-static-build/openssl/include" \
    LDFLAGS="-L/usr/local/armv7-static-build/openssl/lib -ldl" \
    LIBS='-ldl' \
    ./configure \
    --host=$ARM_ARCH \
    --prefix=/usr/local/armv7-static-build/libevent \
    --disable-shared \
    --enable-static \
    && make \
    && make install \
    && cd ..

# Download, compile, and install static Zlib.
RUN curl -sSL --fail -O https://zlib.net/zlib-$ZLIB_VERSION.tar.gz \
    && tar -xzf zlib-$ZLIB_VERSION.tar.gz \
    && cd zlib-$ZLIB_VERSION \
    && CC=arm-linux-gnueabihf-gcc ./configure --static --prefix=/usr/local/armv7-static-build/zlib \
    && make \
    && make install \
    && cd ..

# Create the output directory to store the final compiled binary.
RUN mkdir -p /output

# Download, compile, and install static Tor.
RUN curl -sSL --fail -O https://dist.torproject.org/tor-$TOR_VERSION.tar.gz \
    && tar -xzf tor-$TOR_VERSION.tar.gz \
    && cd tor-$TOR_VERSION \
    && ./configure \
    --host=$ARM_ARCH \
    --prefix=/tor-build \
    --with-openssl-dir=/usr/local/armv7-static-build/openssl \
    --with-libevent-dir=/usr/local/armv7-static-build/libevent \
    --with-zlib-dir=/usr/local/armv7-static-build/zlib \
    --enable-static-openssl \
    --enable-static-libevent \
    --enable-static-zlib \
    --enable-static-tor \
    --disable-asciidoc --disable-manpage \
    --disable-html-manual --disable-unittests --disable-tool-name-check \
    --disable-lzma --disable-zstd \
    LDFLAGS='-static -lpthread' \
    CFLAGS='-DOPENSSL_THREADS' \
    && make -j$(nproc) \
    && make install \
    && cp /tor-build/bin/tor /output/tor

# Set the entrypoint to the /bin/bash shell.
CMD ["/bin/bash"]

