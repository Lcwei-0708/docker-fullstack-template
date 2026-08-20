<?php
// Opt-in auto-login for local development only.
// Never gate this on HTTP_Host — Host is client-controlled via the reverse proxy.
$auto_login = filter_var(getenv('PMA_AUTO_LOGIN') ?: 'false', FILTER_VALIDATE_BOOLEAN);

if ($auto_login) {
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
    // Cookie auth — requires manual login (default / production)
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
