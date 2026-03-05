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

# Menu
msg-main-menu =
    <i>🔒 Fast and reliable VPN. 24/7 support.</i>

    { hdr-user-profile }
    { frg-user }

    { hdr-subscription }
    { $status ->
    [ACTIVE]
    { frg-subscription }
    [EXPIRED]
    <blockquote>
    • Subscription expired.
    
    <i>{ $is_trial ->
    [0] Your subscription has expired. Renew it to continue using the service!
    *[1] Your free trial has ended. Get a subscription to continue using the service!
    }</i>
    </blockquote>
    [LIMITED]
    <blockquote>
    • Your traffic has been used up.

    <i>{ $is_trial ->
    [0] { $traffic_strategy ->
        [NO_RESET] Renew your subscription to reset traffic and continue!
        *[RESET] Traffic will reset in { $reset_time }. You can also renew to reset traffic.
        }
    *[1] { $traffic_strategy ->
        [NO_RESET] Get a subscription to continue!
        *[RESET] Traffic will reset in { $reset_time }. You can also get a subscription.
        }
    }</i>
    </blockquote>
    [DISABLED]
    <blockquote>
    • Your subscription is disabled.

    <i>Contact support to find out why!</i>
    </blockquote>
    *[NONE]
    <blockquote>
    • You have no active subscription.

    <i>{ $trial_available ->
    [1] 🎁 A free trial is available — press the button below to get it.
    *[0] ↘️ Go to "Subscription" to purchase access.
    }</i>
    </blockquote>
    }

msg-menu-devices =
    <b>📱 My devices</b>

    Here you can remove linked devices.
    
    <i>To add devices — press the "Add devices" button below.</i>

msg-locations-main =
    <b>🌍 Servers</b>

    Available locations for connection:

msg-locations-empty =
    <b>🌍 Servers</b>

    Server list is temporarily unavailable. Please contact support.

msg-locations-item = { $country } { $name }

msg-help-main =
    <b>❓ Help & FAQ</b>

    <b>How to connect?</b>
    <blockquote>
    After payment, press the "Connect" button and open the configuration page. Download an app (V2Ray, Clash, Nekoray, etc.) and import the config or scan the QR code.
    </blockquote>

    <b>How to add devices?</b>
    <blockquote>
    Go to "My devices" and press "Add devices". Select the number you need and pay.
    </blockquote>

    <b>Connection issues?</b>
    <blockquote>
    Check that your subscription is active and not expired. Try a different server from the "Servers" list. If that doesn't help — contact support.
    </blockquote>

    <b>Support:</b> press the "Support" button in the main menu.

# Subscription
msg-subscription-main =
    <b>💳 Subscription</b>
    { $has_subscription ->
        [1]
    <blockquote>
    • <b>Plan</b>: { $plan }
    • <b>Traffic limit</b>: { $traffic_limit }
    • <b>Device limit</b>: { $device_limit }
    • <b>Remaining</b>: { $expire_time }
    </blockquote>
        *[0] { empty }
    }
msg-subscription-plans = <b>📦 Select a plan</b>
msg-subscription-add-devices =
    <b>➕ Add devices</b>

    Select the number of devices to add — press one of the buttons below.

msg-subscription-add-devices-empty =
    <b>➕ Add devices</b>

    Adding devices is currently unavailable. Please contact support.

msg-subscription-promocode =
    <b>🎟 Promocode activation</b>

    Enter your promocode in the message below. The discount will be applied to your next purchases.

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

msg-subscription-new-success = 
    To get started with our service:
    <blockquote>
    1️⃣ Press the <code>`{ btn-subscription-connect }`</code> button above
    2️⃣ Download the app (V2Ray, Clash, Nekoray, etc.) — links in our channel
    3️⃣ Import the configuration or scan the QR code from the opened page
    </blockquote>
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
