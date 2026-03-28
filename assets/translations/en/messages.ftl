# Menu (English) — critical UX strings; other keys fall back to default locale (RU)
msg-main-menu =
    <b>Quick start:</b> «Connection» — access · «Subscription» — payment · «Support» — help.

msg-device-addons-admin =
    <b>📱 Extra device slots</b>

    { $addons_empty ->
    [1] <i>No packages yet. Use «Add package» or run DB migrations (seed).</i>
    *[0] Add packages below. In the list you can enable, disable, or delete packages.
    }
