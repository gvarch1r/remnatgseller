ntf-common =
    .rate-limited = ⚠️ <i>Too many attempts. Please wait a few seconds.</i>

ntf-device-addon =
    .prices-invalid = ❌ <i>Invalid format. One line per currency, e.g. <code>RUB 199</code>, <code>XTR 50</code>, <code>USD 2</code>.</i>
    .created = ✅ <i>Device add-on package created.</i>

ntf-subscription =
    .add-devices-not-applicable = ❌ <i>Adding devices is only available for an active paid subscription with a device limit (not during trial).</i>

    .plans-unavailable = ❌ <i>No subscription plans are available right now.</i>
    .gateways-unavailable = ❌ <i>No payment methods are available right now.</i>
    .addons-unavailable = ❌ <i>No device add-on packages are available.</i>
    .renew-plan-unavailable = ❌ <i>Your current plan cannot be renewed.</i>
    .trial-renew-not-allowed = ❌ <i>Trial cannot be renewed. Buy a paid plan from «New subscription».</i>
    .payment-creation-failed =
        ❌ <i>Could not start payment. Try another method or try again later.</i>

        <i>If it keeps failing, contact support with code: <code>{ $ref }</code></i>

ntf-promocode =
    .invalid-code = ❌ <i>Enter a promocode.</i>
    .not-found = ❌ <i>Promocode not found or inactive.</i>
    .expired = ❌ <i>This promocode has expired.</i>
    .depleted = ❌ <i>This promocode has reached its activation limit.</i>
    .already-activated = ❌ <i>You have already used this promocode.</i>
    .unsupported-type = ❌ <i>This promocode type cannot be activated in the bot.</i>
    .subscription-plan-required = ❌ <i>No subscription plan is set for this promocode.</i>
    .subscription-activate-failed = ❌ <i>Could not grant subscription. Try again or contact support.</i>
    .activated-success = ✅ <i>Promocode applied! { $percent }% discount is active.</i>
    .subscription-activated-success = ✅ <i>Promocode activated. Plan: { $plan_name }.</i>

ntf-requirement =
    .channel-join-required =
        ❇️ <b>Step 1:</b> join the channel (button below).
        <b>Step 2:</b> return here and tap «Confirm».

        Channel: promos and news.
