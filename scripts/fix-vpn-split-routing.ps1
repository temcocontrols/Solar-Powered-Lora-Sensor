# Run as Administrator: fixes SoftEther stealing default route / DNS
# Keeps 192.168.0.0/24 on VPN; restores normal internet via WiFi

#Requires -RunAsAdministrator

$ErrorActionPreference = 'Stop'

$vpnAlias = 'VPN - VPN Client'
$wifiAlias = 'WiFi 2'

Write-Host 'Removing VPN default routes...'
route delete 0.0.0.0 mask 0.0.0.0 192.168.0.1 2>$null
route delete 0.0.0.0 mask 0.0.0.0 10.13.87.109 2>$null

$wifi = Get-NetIPConfiguration -InterfaceAlias $wifiAlias -ErrorAction SilentlyContinue
if ($wifi.IPv4DefaultGateway) {
    $gw = $wifi.IPv4DefaultGateway.NextHop
    $ifIndex = $wifi.InterfaceIndex
    Write-Host "Adding default route via WiFi gateway $gw (if $ifIndex)..."
    route add 0.0.0.0 mask 0.0.0.0 $gw metric 10 if $ifIndex
}

Write-Host 'Deprioritizing VPN adapter...'
$vpn = Get-NetAdapter -Name $vpnAlias -ErrorAction SilentlyContinue
if ($vpn) {
    Set-NetIPInterface -InterfaceIndex $vpn.ifIndex -InterfaceMetric 5000
}

Write-Host 'Setting public DNS on WiFi...'
Set-DnsClientServerAddress -InterfaceAlias $wifiAlias -ServerAddresses ('8.8.8.8', '1.1.1.1')
Set-DnsClientServerAddress -InterfaceAlias $vpnAlias -ResetServerAddresses

Write-Host "`nDefault routes:"
route print 0.0.0.0

Write-Host "`nTesting google.com..."
Test-NetConnection google.com -WarningAction SilentlyContinue | Select-Object PingSucceeded, TcpTestSucceeded

Write-Host "`nDone. Re-run this script after each VPN connect if routes come back."
