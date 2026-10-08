# HACS migration

The repository already uses the custom-integration layout
`custom_components/herald/`. Add it as a HACS custom repository of type Integration,
install, restart Home Assistant, then add or reload the config entry.

For an existing manual installation, preserve configuration and a backup of the
installed component first. Verify HACS installed the intended version and the
frontend assets before removing any separate manual deployment process. Do not
remove the active `custom_components/herald/` directory after HACS has installed it.
Default HACS catalog inclusion is a separate publication step.
