BINS=_circus.start _circus.stop _circus.status __ini_to_env.py before_start_redis before_start_nginx after_stop_nginx port_test.sh _make_and_install_crontab.sh _uninstall_crontab.sh circus_status_watcher.sh redis_status.sh config.py metwork _prepare_config.py _make_nethard_config.py _make_circus_conf _make_crontab.sh remove_empty.sh kill_remaining_processes.py bootstrap_plugin.py bootstrap_plugin.py _make_nginx_conf bootstrap_plugin.post _circusctl _install_or_update_configured_plugins.py nginx.status find_zombies_nginx_workers.py before_start_telegraf _circus_wait_watcher_stopped.sh _circus_schedule_stop_watcher.sh _install_plugin_virtualenv plugin_wrapper _plugins.preuninstall _plugins.postinstall list_metwork_processes.py telegraf_collector_metwork_module.py _nginx.reload _circus.reload
SHARES=startup_scripts_profiles.mk plugin.mk config_subdir.mk plugin_autorestart_includes plugin_autorestart_excludes

include root.mk
include $(MFEXT_HOME)/share/subdir_root.mk
include startup_scripts_profiles.mk

all:: profiles load_env $(MFCOM_HOME)/share/mfext_home

$(MFCOM_HOME)/share/mfext_home:
	echo $(MFEXT_HOME) >$@

utilities_doc:
	cat ../mfutil_python/setup.py |grep ' = mfutil.cli_tools' |awk -F '=' '{print $$1;}' |awk -F '"' '{print $$2;}' >utils.list.tmp
	cat ../mflog_python/setup.py |grep ' = .*:.*' |awk -F '=' '{print $$1;}' |awk -F '"' '{print $$2;}' >>utils.list.tmp
	echo "echo_ok" >>utils.list.tmp
	echo "echo_bold" >>utils.list.tmp
	echo "echo_warning" >>utils.list.tmp
	echo "echo_nok" >>utils.list.tmp
	echo "echo_running" >>utils.list.tmp
	echo "config.py" >>utils.list.tmp
	export UTILS="`cat utils.list.tmp |xargs`" && $(MFEXT_HOME)/bin/_make_file_from_template.sh utilities.md >../doc/utilities.md
	rm -f utils.list.tmp
