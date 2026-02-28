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
