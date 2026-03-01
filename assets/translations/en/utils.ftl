# Audit actions
audit-action-registered = Registration
audit-action-subscription-created = Subscription created
audit-action-subscription-updated = Subscription updated
audit-action-subscription-deleted = Subscription deleted
audit-action-role-changed = Role changed
audit-action-blocked = Blocked
audit-action-unblocked = Unblocked
audit-action-discount-changed = Discount changed
audit-action-points-changed = Points changed
audit-action-purchase-completed = Purchase completed
audit-action-promocode-activated = Promocode activated
audit-action-referral-attached = Referral attached
audit-action-device-added = Device added
audit-action-device-removed = Device removed
audit-action-sync-from-remnawave = Sync from Remnawave
audit-action-sync-from-remnatgseller = Sync from RemnatgSeller
audit-action-give-subscription = Subscription given
audit-action-give-access = Plan access granted
audit-action-message-sent = Message sent
audit-empty = No records

# Layout
space = {" "}
empty = { "!empty!" }

# Headers
hdr-user = <b>👤 User:</b>
hdr-user-profile = <b>👤 Profile:</b>
hdr-error = <b>⚠️ Error:</b>

# Fragments
frg-user-info =
    <blockquote>
    • <b>ID</b>: <code>{ $user_id }</code>
    • <b>Name</b>: { $user_name } { $username -> 
        [0] { empty }
        *[HAS] (<a href="tg://user?id={ $user_id }">@{ $username }</a>)
    }
    </blockquote>

frg-build-info =
    { $has_build ->
    [0] { space }
    *[HAS]
    <b>🏗️ Build info:</b>
    <blockquote>
    Build time: { $time }
    Branch: { $branch } ({ $tag })
    Commit: <a href="{ $commit_url }">{ $commit }</a>
    </blockquote>
    }

frg-subscription =
    <blockquote>
    • <b>Traffic limit</b>: { $traffic_limit }
    • <b>Device limit</b>: { $device_limit }
    • <b>Remaining</b>: { $expire_time }
    </blockquote>

frg-payment-amount = { $final_amount }{ $currency } { $discount_percent ->
    [0] { space }
    *[more] { space } <strike>{ $original_amount }{ $currency }</strike> (-{ $discount_percent }%)
    }

purchase-type = { $purchase_type ->
    [NEW] Purchase
    [RENEW] Renewal
    [CHANGE] Change
    [ADD_DEVICES] Add devices
    *[OTHER] { $purchase_type }
}

payment-invoice-description-add-devices = { purchase-type } devices: { $name }
