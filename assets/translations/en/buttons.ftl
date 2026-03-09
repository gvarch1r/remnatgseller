# Back
btn-back = ⬅️ Back

# Menu
btn-menu-help = ❓ Help
btn-user-audit = 📋 Audit

# Subscription
btn-subscription-new = 💸 Buy subscription
btn-subscription-renew = 🔄 Renew
btn-subscription-change = 🔃 Change
btn-subscription-add-devices = ➕ Add devices
btn-subscription-addon = +{ $device_count } devices | { $final_amount ->
    [0] Free
    *[other] { $final_amount } { $currency }
}
btn-subscription-back-addon = ⬅️ Back to selection
btn-subscription-payment-method = { gateway-type } | { $price } { $currency }
btn-subscription-pay = 💳 Pay
btn-subscription-get = 🎁 Get for free
btn-subscription-back-plans = ⬅️ Back to plan selection
btn-subscription-back-duration = ⬅️ Change duration
btn-subscription-back-payment-method = ⬅️ Change payment method
btn-subscription-connect = 🚀 Connect
btn-subscription-duration = { $period } | { $final_amount ->
    [0] 🎁
    *[HAS] { $final_amount }{ $currency }
}

# RemnaWave
btn-remnawave-users = 👥 Users
btn-remnawave-hosts = 🌐 Hosts
btn-remnawave-nodes = 🖥️ Nodes
btn-remnawave-inbounds = 🔌 Inbounds

# RemnatgSeller
btn-remnatgseller-device-addons = 📱 Device add-ons

# Device addons
btn-device-addons-create = 🆕 Add option
btn-device-addon-active = { $is_active ->
    [1] 🟢 Enabled
    *[0] 🔴 Disabled
    }
