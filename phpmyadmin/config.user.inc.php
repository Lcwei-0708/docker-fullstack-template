<?php
// Check if it's a local access
$is_localhost = false;

// Check IP address and Host
if (isset($_SERVER['REMOTE_ADDR'])) {
    $client_ip = $_SERVER['REMOTE_ADDR'];
    $is_localhost = in_array($client_ip, ['127.0.0.1', '::1']);
}

// Check Host header
if (isset($_SERVER['HTTP_HOST'])) {
    $host = $_SERVER['HTTP_HOST'];
    if (strpos($host, 'localhost') !== false || strpos($host, '127.0.0.1') !== false) {
        $is_localhost = true;
    }
}

// If it's local access, auto-login
if ($is_localhost) {
    $cfg['Servers'][$i]['auth_type'] = 'config';
    $cfg['Servers'][$i]['user'] = $_ENV['PMA_USER'];
    $cfg['Servers'][$i]['password'] = $_ENV['PMA_PASSWORD'];
    $cfg['Servers'][$i]['host'] = $_ENV['PMA_HOST'];
    $cfg['Servers'][$i]['port'] = '3306';
    $cfg['Servers'][$i]['compress'] = false;
    $cfg['Servers'][$i]['AllowNoPassword'] = false;
    $cfg['Servers'][$i]['connect_type'] = 'tcp';
    $cfg['Servers'][$i]['extension'] = 'mysqli';
} else {
    // External access requires manual authentication
    $cfg['Servers'][$i]['auth_type'] = 'cookie';
    $cfg['Servers'][$i]['host'] = $_ENV['PMA_HOST'];
    $cfg['Servers'][$i]['port'] = '3306';
    $cfg['Servers'][$i]['compress'] = false;
    $cfg['Servers'][$i]['AllowNoPassword'] = false;
    $cfg['Servers'][$i]['connect_type'] = 'tcp';
    $cfg['Servers'][$i]['extension'] = 'mysqli';
}

// Session timeout settings (in seconds)
$cfg['LoginCookieValidity'] = 43200;        // 12 hours - login cookie validity
$cfg['LoginCookieStore'] = 0;               // 0 = session only, >0 = store login cookie for X seconds
$cfg['LoginCookieDeleteAll'] = true;        // Delete all cookies when logging out
$cfg['SessionSavePath'] = '';               // Use default session save path
$cfg['SessionMaxTime'] = 43200;             // 12 hours - maximum session time
$cfg['SessionTimeout'] = 21600;             // 6 hours - session timeout warning

// Security settings
$cfg['LoginCookieValidityDisableWarning'] = false;  // Show warning when cookie validity is disabled
$cfg['LoginCookieRefresh'] = 1800;          // 30 minutes - refresh login cookie every X seconds
?>