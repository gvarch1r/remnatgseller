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

# Subscription
msg-subscription-main = <b>💳 Subscription</b>
msg-subscription-plans = <b>📦 Select a plan</b>
msg-subscription-add-devices = <b>➕ Add devices</b>

    Select the number of devices to add to your subscription.

msg-subscription-details =
    <b>{ $plan }:</b>
    <blockquote>
    { $description ->
    [0] { empty }
    *[HAS]
    { $description }
    }

    • <b>Traffic limit</b>: { $traffic }
    • <b>Device limit</b>: { $devices }
    { $period ->
    [0] { empty }
    *[HAS] • <b>Duration</b>: { $period }
    }
    { $final_amount ->
    [0] { empty }
    *[HAS] • <b>Price</b>: { frg-payment-amount }
    }
    </blockquote>

msg-subscription-duration =
    <b>⏳ Select duration</b>

    { msg-subscription-details }

msg-subscription-payment-method =
    <b>💳 Select payment method</b>

    { msg-subscription-details }

msg-subscription-confirm =
    { $purchase_type ->
    [RENEW] <b>🛒 Confirm subscription renewal</b>
    [CHANGE] <b>🛒 Confirm subscription change</b>
    *[OTHER] <b>🛒 Confirm subscription purchase</b>
    }

    { msg-subscription-details }

    { $purchase_type ->
    [RENEW] <i>⚠️ Current subscription will be <u>extended</u> for the selected period.</i>
    [CHANGE] <i>⚠️ Current subscription will be <u>replaced</u> without recalculating remaining time.</i>
    *[OTHER] { empty }
    }

msg-subscription-new-success = To start using our service, click <code>`{ btn-subscription-connect }`</code> and follow the instructions!
msg-subscription-renew-success = Your subscription has been renewed for { $added_duration }.
msg-subscription-trial =
    <b>✅ Trial subscription received!</b>

    { msg-subscription-new-success }

msg-subscription-success =
    <b>✅ Payment successful!</b>

    { $purchase_type ->
    [NEW] { msg-subscription-new-success }
    [RENEW] { msg-subscription-renew-success }
    [CHANGE] { msg-subscription-change-success }
    [ADD_DEVICES] { msg-subscription-add-devices-success }
    *[OTHER] { $purchase_type }
    }

msg-subscription-add-devices-success = Added { $added_duration } devices to your subscription.
msg-subscription-change-success =
    Your subscription has been changed.

    <b>{ $plan_name }</b>
    { frg-subscription }

msg-subscription-failed =
    <b>❌ An error occurred!</b>

    Don't worry, support has been notified and will contact you shortly. We apologize for the inconvenience.

# User
msg-user-audit = <b>📋 User activity history</b>

# User statistics
msg-user-statistics =
    <b>📊 User statistics</b>

    <b>🧾 Transactions:</b>
    <blockquote>
    • Total: { $transactions_total }
    • Completed: { $transactions_completed }
    • Spent: { $spent_total }
    </blockquote>

    <b>💳 Subscriptions:</b>
    <blockquote>
    • Total issued: { $subscriptions_total }
    </blockquote>

    <b>👥 Referrals:</b>
    <blockquote>
    • Invited: { $referrals_count }
    </blockquote>
