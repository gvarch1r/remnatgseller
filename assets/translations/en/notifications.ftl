# Subscription
ntf-subscription-plans-not-available = <i>❌ No plans available.</i>
ntf-subscription-addons-not-available = <i>❌ No device add-on options available.</i>
ntf-subscription-gateways-not-available = <i>❌ No payment gateways available.</i>
ntf-subscription-renew-plan-unavailable = <i>❌ Your plan is no longer available for renewal.</i>
ntf-subscription-payment-creation-failed = <i>❌ An error occurred while creating the payment. Please try again later.</i>

# Promocodes
ntf-promocode-invalid-code = <i>❌ Please enter a promocode.</i>
ntf-promocode-not-found = <i>❌ Promocode not found.</i>
ntf-promocode-activated-success = <i>✅ Promocode activated successfully! You have received a { $percent }% discount on purchases.</i>
ntf-promocode-expired = <i>❌ This promocode has expired.</i>
ntf-promocode-depleted = <i>❌ This promocode has reached its activation limit.</i>
ntf-promocode-already-activated = <i>❌ You have already activated this promocode.</i>
ntf-promocode-unsupported-type = <i>❌ This promocode type is not supported for activation.</i>

# Errors
ntf-error-lost-context = <i>⚠️ An error occurred. Dialog restarted.</i>
ntf-error-log-not-found = <i>⚠️ Error: Log file not found.</i>

# Events
ntf-event-error =
    #EventError

    <b>🔅 Event: An error occurred!</b>

    { frg-build-info }
    
    { $user -> 
    [1]
    { hdr-user }
    { frg-user-info }
    *[0] { space }
    }

    { hdr-error }
    <blockquote>
    { $error }
    </blockquote>
