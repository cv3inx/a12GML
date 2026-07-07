# Standalone Dockerfile for Redroid A12 GML
# Builds on top of official redroid with all components pre-installed
#
# Build: docker build -t redroid-gml .
# Run:   docker run -d --privileged -p 5555:5555 redroid-gml
#
# NOTE: This Dockerfile adds Frida to the image.
#       For NDK + Magisk, use build.sh which leverages redroid-script.

FROM redroid/redroid:12.0.0-latest

# Add frida-server (renamed)
ADD https://github.com/frida/frida/releases/download/17.15.3/frida-server-17.15.3-android-x86_64.xz /tmp/fs.xz
RUN unxz /tmp/fs.xz && mv /tmp/fs /data/local/tmp/fs && chmod 755 /data/local/tmp/fs

# Add mitmproxy CA cert (optional - build with: --build-arg MITM_CERT=path)
ARG MITM_CERT=""
RUN if [ -n "$MITM_CERT" ]; then \
      cp "$MITM_CERT" /system/etc/security/cacerts/ ; \
    fi

# Properties for ARM translation (applied at runtime via run.sh)
# These are just defaults; run.sh overrides them
