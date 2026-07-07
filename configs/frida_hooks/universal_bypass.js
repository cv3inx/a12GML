/**
 * Universal Bypass Script for Redroid A12 GML
 * Combines: SSL Pinning Bypass + Root Detection Bypass + Emulator Detection Bypass
 * 
 * Usage: frida -H 127.0.0.1:27042 -f <package> -l universal_bypass.js
 */

// ============================================================
// SSL PINNING BYPASS (Universal - covers OkHttp, HttpURLConnection, 
// TrustManager, Conscrypt, Network Security Config, WebView)
// ============================================================

Java.perform(function() {
    var X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
    var SSLContext = Java.use('javax.net.ssl.SSLContext');
    var TrustManager;

    try {
        // Custom TrustManager that accepts all certificates
        TrustManager = Java.registerClass({
            name: 'com.gml.TrustAllManager',
            implements: [X509TrustManager],
            methods: {
                checkClientTrusted: function(chain, authType) {},
                checkServerTrusted: function(chain, authType) {},
                getAcceptedIssuers: function() { return []; }
            }
        });
    } catch(e) {}

    // Hook SSLContext.init to use our TrustManager
    try {
        SSLContext.init.overload('[Ljavax.net.ssl.KeyManager;', '[Ljavax.net.ssl.TrustManager;', 'java.security.SecureRandom').implementation = function(km, tm, sr) {
            var TrustManagers = [TrustManager.$new()];
            this.init(km, TrustManagers, sr);
        };
    } catch(e) {}

    // OkHttp3 CertificatePinner bypass
    try {
        var CertificatePinner = Java.use('okhttp3.CertificatePinner');
        CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function(hostname, peerCertificates) {};
        CertificatePinner.check.overload('java.lang.String', '[Ljava.security.cert.Certificate;').implementation = function(hostname, peerCertificates) {};
    } catch(e) {}

    // OkHttp3 CertificatePinner$Builder bypass
    try {
        var CertPinnerBuilder = Java.use('okhttp3.CertificatePinner$Builder');
        CertPinnerBuilder.add.overload('java.lang.String', '[Ljava.lang.String;').implementation = function(hostname, pins) {
            return this;
        };
    } catch(e) {}

    // Conscrypt / Platform TrustManager
    try {
        var Platform = Java.use('com.android.org.conscrypt.Platform');
        Platform.checkServerTrusted.overload('javax.net.ssl.X509TrustManager', '[Ljava.security.cert.X509Certificate;', 'java.lang.String', 'com.android.org.conscrypt.AbstractConscryptSocket').implementation = function(tm, chain, authType, socket) {};
    } catch(e) {}

    // TrustManagerImpl (Android internal)
    try {
        var TrustManagerImpl = Java.use('com.android.org.conscrypt.TrustManagerImpl');
        TrustManagerImpl.verifyChain.implementation = function(untrustedChain, trustAnchorChain, host, clientAuth, ocspData, tlsSctData) {
            return untrustedChain;
        };
    } catch(e) {}

    // Network Security Config bypass
    try {
        var NetworkSecurityTrustManager = Java.use('android.security.net.config.NetworkSecurityTrustManager');
        NetworkSecurityTrustManager.checkServerTrusted.overload('[Ljava.security.cert.X509Certificate;', 'java.lang.String').implementation = function(certs, authType) {};
        NetworkSecurityTrustManager.checkServerTrusted.overload('[Ljava.security.cert.X509Certificate;', 'java.lang.String', 'java.lang.String').implementation = function(certs, authType, hostname) {
            return java.util.Arrays.asList(certs);
        };
    } catch(e) {}

    // HostnameVerifier bypass
    try {
        var HostnameVerifier = Java.use('javax.net.ssl.HostnameVerifier');
        var SSLSession = Java.use('javax.net.ssl.SSLSession');
        
        var HttpsURLConnection = Java.use('javax.net.ssl.HttpsURLConnection');
        HttpsURLConnection.setDefaultHostnameVerifier.implementation = function(hostnameVerifier) {
            return;
        };
        HttpsURLConnection.setHostnameVerifier.implementation = function(hostnameVerifier) {
            return;
        };
    } catch(e) {}

    // WebView SSL error bypass
    try {
        var WebViewClient = Java.use('android.webkit.WebViewClient');
        WebViewClient.onReceivedSslError.overload('android.webkit.WebView', 'android.webkit.SslErrorHandler', 'android.net.http.SslError').implementation = function(view, handler, error) {
            handler.proceed();
        };
    } catch(e) {}

    // Retrofit/OkHttp HostnameVerifier
    try {
        var OkHostnameVerifier = Java.use('okhttp3.internal.tls.OkHostnameVerifier');
        OkHostnameVerifier.verify.overload('java.lang.String', 'javax.net.ssl.SSLSession').implementation = function(hostname, session) { return true; };
        OkHostnameVerifier.verify.overload('java.lang.String', 'java.security.cert.X509Certificate').implementation = function(hostname, cert) { return true; };
    } catch(e) {}

    console.log('[✓] SSL Pinning Bypass loaded');
});


// ============================================================
// ROOT DETECTION BYPASS
// ============================================================

Java.perform(function() {
    
    // Generic file existence checks (su, magisk, supersu, etc)
    var RootFiles = ['/system/bin/su', '/system/xbin/su', '/sbin/su', '/data/local/su',
        '/system/app/Superuser.apk', '/system/app/SuperSU.apk',
        '/data/adb/magisk', '/sbin/.magisk', '/system/bin/magisk',
        '/system/xbin/daemonsu', '/data/local/tmp/frida-server', '/data/local/tmp/fs'];

    try {
        var File = Java.use('java.io.File');
        File.exists.implementation = function() {
            var path = this.getAbsolutePath();
            for (var i = 0; i < RootFiles.length; i++) {
                if (path === RootFiles[i] || path.indexOf('magisk') !== -1 || 
                    path.indexOf('supersu') !== -1 || path.indexOf('/su') !== -1) {
                    return false;
                }
            }
            return this.exists();
        };
    } catch(e) {}

    // Runtime.exec - block root commands
    try {
        var Runtime = Java.use('java.lang.Runtime');
        Runtime.exec.overload('[Ljava.lang.String;').implementation = function(commands) {
            var cmd = commands[0];
            if (cmd === 'su' || cmd.indexOf('which su') !== -1 || cmd.indexOf('magisk') !== -1) {
                throw Java.use('java.io.IOException').$new('Permission denied');
            }
            return this.exec(commands);
        };
        Runtime.exec.overload('java.lang.String').implementation = function(command) {
            if (command.indexOf('su') !== -1 || command.indexOf('magisk') !== -1 || command.indexOf('which') !== -1) {
                throw Java.use('java.io.IOException').$new('Permission denied');
            }
            return this.exec(command);
        };
    } catch(e) {}

    // PackageManager - hide root/magisk packages
    var rootPkgs = ['com.topjohnwu.magisk', 'eu.chainfire.supersu', 'com.koushikdutta.superuser',
        'com.thirdparty.superuser', 'com.noshufou.android.su', 'com.yellowes.su',
        'io.github.vvb2060.magisk', 'me.weishu.kernelsu', 'com.topjohnwu.magisk.delta'];

    try {
        var PM = Java.use('android.app.ApplicationPackageManager');
        PM.getPackageInfo.overload('java.lang.String', 'int').implementation = function(pkg, flags) {
            for (var i = 0; i < rootPkgs.length; i++) {
                if (pkg === rootPkgs[i]) {
                    throw Java.use('android.content.pm.PackageManager$NameNotFoundException').$new(pkg);
                }
            }
            return this.getPackageInfo(pkg, flags);
        };
    } catch(e) {}

    // System properties - hide root traces
    try {
        var SystemProperties = Java.use('android.os.SystemProperties');
        SystemProperties.get.overload('java.lang.String').implementation = function(key) {
            if (key === 'ro.build.tags' || key === 'ro.build.type') {
                if (key === 'ro.build.tags') return 'release-keys';
                if (key === 'ro.build.type') return 'user';
            }
            return this.get(key);
        };
    } catch(e) {}

    // Build class patches
    try {
        var Build = Java.use('android.os.Build');
        Build.TAGS.value = 'release-keys';
        Build.TYPE.value = 'user';
        Build.FINGERPRINT.value = Build.FINGERPRINT.value.replace('test-keys', 'release-keys');
    } catch(e) {}

    console.log('[✓] Root Detection Bypass loaded');
});


// ============================================================
// EMULATOR DETECTION BYPASS
// ============================================================

Java.perform(function() {

    // Build fields that leak emulator
    try {
        var Build = Java.use('android.os.Build');
        // These get overwritten by spoof_device.sh but in case they aren't:
        if (Build.HARDWARE.value === 'redroid' || Build.HARDWARE.value === 'goldfish' || Build.HARDWARE.value === 'ranchu') {
            Build.HARDWARE.value = 'qcom';
        }
        if (Build.MODEL.value.indexOf('sdk') !== -1 || Build.MODEL.value.indexOf('emulator') !== -1 || Build.MODEL.value.indexOf('redroid') !== -1) {
            Build.MODEL.value = 'SM-G991B';
        }
        if (Build.MANUFACTURER.value === 'Genymotion' || Build.MANUFACTURER.value === 'unknown' || Build.MANUFACTURER.value === 'redroid') {
            Build.MANUFACTURER.value = 'samsung';
        }
        if (Build.BRAND.value === 'generic' || Build.BRAND.value === 'redroid') {
            Build.BRAND.value = 'samsung';
        }
        if (Build.DEVICE.value === 'generic' || Build.DEVICE.value.indexOf('redroid') !== -1) {
            Build.DEVICE.value = 'o1s';
        }
        if (Build.PRODUCT.value === 'sdk' || Build.PRODUCT.value.indexOf('redroid') !== -1) {
            Build.PRODUCT.value = 'o1sxeea';
        }
        Build.BOARD.value = Build.BOARD.value.indexOf('goldfish') !== -1 ? 'universal2100' : Build.BOARD.value;
        Build.HOST.value = 'SWDG4521';
    } catch(e) {}

    // TelephonyManager - fake operator info
    try {
        var TelephonyManager = Java.use('android.telephony.TelephonyManager');
        TelephonyManager.getNetworkOperatorName.implementation = function() { return 'T-Mobile'; };
        TelephonyManager.getSimOperatorName.implementation = function() { return 'T-Mobile'; };
        TelephonyManager.getNetworkOperator.implementation = function() { return '310260'; };
        TelephonyManager.getSimOperator.implementation = function() { return '310260'; };
        TelephonyManager.getLine1Number.implementation = function() { return ''; };
        TelephonyManager.getDeviceId.overload().implementation = function() { return ''; };
        TelephonyManager.getSubscriberId.implementation = function() { return ''; };
        TelephonyManager.getPhoneType.implementation = function() { return 1; }; // GSM
        TelephonyManager.getNetworkType.implementation = function() { return 13; }; // LTE
    } catch(e) {}

    // Sensors - emulators often have no/fake sensors
    try {
        var SensorManager = Java.use('android.hardware.SensorManager');
        // Don't patch getSensorList to return empty - some apps crash
        // Instead we let the existing sensors through
    } catch(e) {}

    // Settings.Secure - ADB enabled detection
    try {
        var Settings$Secure = Java.use('android.provider.Settings$Secure');
        var orig_getString = Settings$Secure.getString;
        Settings$Secure.getString.overload('android.content.ContentResolver', 'java.lang.String').implementation = function(resolver, name) {
            if (name === 'adb_enabled') return '0';
            if (name === 'development_settings_enabled') return '0';
            return orig_getString.call(this, resolver, name);
        };
    } catch(e) {}

    // System properties that leak emulator
    try {
        var SystemProperties = Java.use('android.os.SystemProperties');
        var orig_get = SystemProperties.get.overload('java.lang.String', 'java.lang.String');
        orig_get.implementation = function(key, def) {
            // Hide emulator-specific props
            if (key === 'ro.kernel.qemu' || key === 'ro.boot.qemu') return '0';
            if (key === 'init.svc.qemud' || key === 'init.svc.qemu-props') return '';
            if (key === 'ro.hardware.egl') return 'mali';
            if (key === 'ro.hardware.vulkan') return 'mali';
            if (key === 'qemu.hw.mainkeys') return '';
            if (key === 'ro.boot.hardware') {
                var val = orig_get.call(this, key, def);
                return (val === 'redroid' || val === 'goldfish' || val === 'ranchu') ? 'qcom' : val;
            }
            return orig_get.call(this, key, def);
        };
    } catch(e) {}

    // File checks for emulator artifacts
    try {
        var File = Java.use('java.io.File');
        var emuFiles = ['/dev/socket/qemud', '/dev/qemu_pipe', '/system/lib/libc_malloc_debug_qemu.so',
            '/sys/qemu_trace', '/system/bin/qemu-props', '/dev/goldfish_pipe',
            '/system/lib/libdroid4x.so', '/system/bin/windroyed', '/system/bin/nox-prop'];
        
        var origExists = File.exists;
        File.exists.implementation = function() {
            var path = this.getAbsolutePath();
            for (var i = 0; i < emuFiles.length; i++) {
                if (path === emuFiles[i]) return false;
            }
            return origExists.call(this);
        };
    } catch(e) {}

    // IP address checks (10.0.2.x = emulator)
    try {
        var InetAddress = Java.use('java.net.InetAddress');
        // Don't override - could break networking
    } catch(e) {}

    console.log('[✓] Emulator Detection Bypass loaded');
});


// ============================================================
// FRIDA DETECTION BYPASS
// ============================================================

Java.perform(function() {

    // Hide frida-related strings from memory scanning
    try {
        var Runtime = Java.use('java.lang.Runtime');
        var origExec = Runtime.exec.overload('java.lang.String');
        origExec.implementation = function(cmd) {
            if (cmd.indexOf('frida') !== -1 || cmd.indexOf('gum-js-loop') !== -1 || 
                cmd.indexOf('gmain') !== -1 || cmd.indexOf('linjector') !== -1) {
                throw Java.use('java.io.IOException').$new('not found');
            }
            return origExec.call(this, cmd);
        };
    } catch(e) {}

    // Port-based frida detection (27042, 27043)
    try {
        var Socket = Java.use('java.net.Socket');
        Socket.$init.overload('java.lang.String', 'int').implementation = function(host, port) {
            if (port === 27042 || port === 27043) {
                throw Java.use('java.net.ConnectException').$new('Connection refused');
            }
            this.$init(host, port);
        };
    } catch(e) {}

    // /proc/self/maps scanning (apps look for frida-agent)
    try {
        var BufferedReader = Java.use('java.io.BufferedReader');
        BufferedReader.readLine.implementation = function() {
            var line = this.readLine();
            if (line !== null && (line.indexOf('frida') !== -1 || line.indexOf('gum-js') !== -1 || 
                line.indexOf('gmain') !== -1)) {
                return this.readLine(); // Skip frida-related lines
            }
            return line;
        };
    } catch(e) {}

    console.log('[✓] Frida Detection Bypass loaded');
});

console.log('');
console.log('╔══════════════════════════════════════════╗');
console.log('║  Universal Bypass Script Active          ║');
console.log('║  ✓ SSL Pinning Bypass                   ║');
console.log('║  ✓ Root Detection Bypass                ║');
console.log('║  ✓ Emulator Detection Bypass            ║');
console.log('║  ✓ Frida Detection Bypass               ║');
console.log('╚══════════════════════════════════════════╝');
