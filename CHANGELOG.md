<a name="unreleased"></a>
## [Unreleased]

### Feat
- add home to plugins.list --json output
- introduce new autorestart plugin
- refactor node plugins build
- remove virtualenv sources after .plugin install

### Fix
- fix building issue with empty node plugins
- fix list metwork processes feature for dev usage (several modules as the same user)

<a name="v0.4.0"></a>
## [v0.4.0] - 2019-01-08
### Feat
- Add a "plugin succesfully created message" at the end of bootstrap_plugin.py
- add a list_metwork_processes util
- add a no-input option
- add a telegraf plugin to collect informations about metwork modules/plugins
- add get_file_size function in synutil_lua
- add new layerapi2 python wrapper
- better plugin build
- better plugin cleaning (again)
- better plugin management (with errors in pre/post scripts)
- new plugin_wrapper (with options)
- publish conf generation time as an env var

### Fix
- fix crontab exception in a basic docker container
- fix incomplete plugins removal (in some cases)
- fix list metwork processes feature for dev usage (several modules as the same user)
- fix metwork processes list
- fix missing postinstall scripts
- raise some timeouts for timeout problems on slow machines
- remove a debug message during some plugin operations
- remove a debug message in plugin_wrapper util
- rollback on plugin packaging around virtualenv

### BREAKING CHANGE

_plugins.postuninstall is renamed to
_plugins.preuninstall

