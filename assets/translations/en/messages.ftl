# RemnatgSeller
ntf-remnatgseller-info = 
    <b>💎 RemnatgSeller v{ $version }</b>

    Bot for selling VPN subscriptions. Works with Remnawave panel.

    ⭐ <i>Source code on <a href="{ $repository }">GitHub</a>. Support and updates — in our <a href="{ $community_url }">Telegram</a>.</i>

# RemnaWave
msg-remnawave-main =
    <b>🌊 RemnaWave</b>{ $version ->
        [""] 
        *[other] <i> v{ $version }</i>
    }
    
    <b>🖥️ System:</b>
    <blockquote>
    • <b>CPU</b>: { $cpu_cores } { $cpu_cores ->
    [one] core
    *[other] cores
    } { $cpu_threads } { $cpu_threads ->
    [one] thread
    *[other] threads
    }
    • <b>RAM</b>: { $ram_used } / { $ram_total } ({ $ram_used_percent }%)
    • <b>Uptime</b>: { $uptime }
    </blockquote>

msg-remnawave-users =
    <b>👥 Users</b>

    <b>📊 Statistics:</b>
    <blockquote>
    • <b>Total</b>: { $users_total }
    • <b>Active</b>: { $users_active }
    • <b>Disabled</b>: { $users_disabled }
    • <b>Limited</b>: { $users_limited }
    • <b>Expired</b>: { $users_expired }
    </blockquote>

    <b>🟢 Online:</b>
    <blockquote>
    • <b>Last day</b>: { $online_last_day }
    • <b>Last week</b>: { $online_last_week }
    • <b>Never online</b>: { $online_never }
    • <b>Online now</b>: { $online_now }
    </blockquote>

msg-remnawave-host-details =
    <b>{ $remark } ({ $status ->
    [ON] enabled
    *[OFF] disabled
    }):</b>
    <blockquote>
    • <b>Address</b>: <code>{ $address }:{ $port }</code>
    { $inbound_uuid ->
    [0] { empty }
    *[HAS] • <b>Inbound</b>: <code>{ $inbound_uuid }</code>
    }
    </blockquote>

msg-remnawave-node-details =
    <b>{ $country } { $name } ({ $status ->
    [ON] connected
    *[OFF] disconnected
    }):</b>
    <blockquote>
    • <b>Address</b>: <code>{ $address }{ $port -> 
    [0] { empty }
    *[HAS]:{ $port }
    }</code>
    • <b>Uptime (xray)</b>: { $xray_uptime }
    • <b>Users online</b>: { $users_online }
    • <b>Traffic</b>: { $traffic_used } / { $traffic_limit }
    </blockquote>

msg-remnawave-inbound-details =
    <b>🔗 { $tag }</b>
    <blockquote>
    • <b>ID</b>: <code>{ $inbound_id }</code>
    • <b>Protocol</b>: { $type } ({ $network })
    { $port ->
    [0] { empty }
    *[HAS] • <b>Port</b>: { $port }
    }
    { $security ->
    [0] { empty }
    *[HAS] • <b>Security</b>: { $security } 
    }
    </blockquote>

msg-remnawave-hosts =
    <b>🌐 Hosts</b>
    
    { $host }

msg-remnawave-nodes = 
    <b>🖥️ Nodes</b>

    { $node }

msg-remnawave-inbounds =
    <b>🔌 Inbounds</b>

    { $inbound }
