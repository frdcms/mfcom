"""utility classes and functions for managing metwork plugins."""

import logging
import six
import glob
import os
import shutil
import hashlib
import envtpl
from mfutil import BashWrapperException, BashWrapperOrRaise, BashWrapper
from mfutil import mkdir_p_or_die, get_unique_hexa_identifier
from mfutil.layerapi2 import LayerApi2Wrapper
from configparser_extended import ExtendedConfigParser

RUNTIME_HOME = os.environ.get('MODULE_RUNTIME_HOME', '/tmp')
MFEXT_HOME = os.environ['MFEXT_HOME']
MODULE_LOWERCASE = os.environ['MODULE_LOWERCASE']
SPEC_TEMPLATE = os.path.join(MFEXT_HOME, "share", "templates", "plugin.spec")

# FIXME: doc


def plugin_name_to_layerapi2_label(plugin_name):
    return "plugin_%s@%s" % (plugin_name, MODULE_LOWERCASE)


def layerapi2_label_to_plugin_name(label):
    if (not label.startswith("plugin_")) or \
            (not label.endswith("@%s" % MODULE_LOWERCASE)):
        raise Exception("bad layerapi2_label: %s => is it really a plugin ?" %
                        label)
    return label[7:].split('@')[0]


def get_layer_home_from_plugin_name(plugin_name):
    label = plugin_name_to_layerapi2_label(plugin_name)
    return LayerApi2Wrapper.get_layer_home(label)


def layerapi2_label_file_to_plugin_name(llf_path):
    try:
        with open(llf_path, 'r') as f:
            c = f.read().strip()
    except Exception:
        raise Exception("can't read %s file" % llf_path)
    return layerapi2_label_to_plugin_name(c)


class MFUtilPluginAlreadyInstalled(Exception):
    """Exception class raised when a plugin is already installed."""

    pass


class MFUtilPluginNotInstalled(Exception):
    """Exception class raised when a plugin is not installed."""

    pass


class MFUtilPluginCantUninstall(BashWrapperException):
    """Exception class raised when we can't uninstall a plugin."""

    pass


class MFUtilPluginCantInstall(BashWrapperException):
    """Exception class raised when we can't install a plugin."""

    pass


class MFUtilPluginCantInit(BashWrapperException):
    """Exception class raised when we can't init the plugin base."""

    pass


class MFUtilPluginCantBuild(BashWrapperException):
    """Exception class raised when we can't build a plugin."""

    pass


class MFUtilPluginBaseNotInitialized(Exception):
    """Exception class raised when the plugin base is not initialized."""

    pass


class MFUtilPluginFileNotFound(Exception):
    """Exception class raised when we can't find the plugin file."""

    pass


class MFUtilPluginInvalid(Exception):
    """Exception class raised when the plugin is invalid."""

    pass


def __get_logger():
    return logging.getLogger("mfutil.plugins")


def get_plugins_base_dir():
    """Return the default plugins base directory path.

    This value correspond to: ${RUNTIME_HOME}/var/plugins value.

    Returns:
        (string): the default plugins base directory path.

    """
    return os.path.join(RUNTIME_HOME, "var", "plugins")


def _get_plugins_base_dir(plugins_base_dir=None):
    if plugins_base_dir is None:
        return get_plugins_base_dir()
    else:
        return plugins_base_dir


def _get_rpm_cmd(command, extra_args="", plugins_base_dir=None,
                 add_prefix=False):
    plugins_base_dir = _get_plugins_base_dir(plugins_base_dir)
    base = os.path.join(plugins_base_dir, "base")
    if add_prefix:
        cmd = 'layer_wrapper --layers=rpm@mfext -- rpm %s ' \
            '--dbpath %s --prefix %s %s' % \
            (command, base, plugins_base_dir, extra_args)
    else:
        cmd = 'layer_wrapper --layers=rpm@mfext -- rpm %s ' \
            '--dbpath %s %s' % \
            (command, base, extra_args)
    return cmd


def init_plugins_base(plugins_base_dir=None):
    """Initialize the plugins base.

    Args:
        plugins_base_dir (string): alternate plugins base directory
            (useful for unit tests).

    Raises:
        MFUtilPluginCantInit: if we can't init the plugin base.

    """
    plugins_base_dir = _get_plugins_base_dir(plugins_base_dir)
    shutil.rmtree(plugins_base_dir, ignore_errors=True)
    mkdir_p_or_die(plugins_base_dir)
    mkdir_p_or_die(os.path.join(plugins_base_dir, "base"))
    cmd = _get_rpm_cmd("--initdb", plugins_base_dir=plugins_base_dir)
    BashWrapperOrRaise(cmd, MFUtilPluginCantInit,
                       "can't init %s" % plugins_base_dir)


def is_plugins_base_initialized(plugins_base_dir=None):
    """Return True is the plugins base is already initialized for the module.

    You can pass a plugins_base_dir as argument but you don't have to do that,
    except for unit testing.

    The plugins base dir is stored by default in :
    ${MODULE_RUNTIME_HOME}/var/plugins

    Args:
        plugins_base_dir (string): alternate plugins base directory.

    Returns:
        boolean: True if the base is initialized.

    """
    plugins_base_dir = _get_plugins_base_dir(plugins_base_dir)
    return os.path.isfile(os.path.join(plugins_base_dir, "base", "Name"))


def _assert_plugins_base_initialized(plugins_base_dir=None):
    if not is_plugins_base_initialized(plugins_base_dir=plugins_base_dir):
        raise MFUtilPluginBaseNotInitialized()


def get_installed_plugins(plugins_base_dir=None):
    _assert_plugins_base_initialized(plugins_base_dir)
    plugins_base_dir = _get_plugins_base_dir(plugins_base_dir)
    frmt = "%{name}~~~%{version}~~~%{release}\\n"
    cmd = _get_rpm_cmd('-qa', '--qf "%s"' % frmt,
                       plugins_base_dir=plugins_base_dir)
    x = BashWrapperOrRaise(cmd)
    tmp = x.stdout.split('\n')
    result = []
    for line in tmp:
        tmp2 = line.split('~~~')
        if len(tmp2) == 3:
            home = get_layer_home_from_plugin_name(tmp2[0])
            if home:
                result.append({'name': tmp2[0],
                               'version': tmp2[1],
                               'release': tmp2[2],
                               'home': home})
    for tmp in os.listdir(plugins_base_dir):
        directory_name = tmp.strip()
        if directory_name == 'base':
            continue
        llf = os.path.join(plugins_base_dir, directory_name,
                           ".layerapi2_label")
        if not os.path.isfile(llf):
            __get_logger().warning("missing %s file for installed "
                                   "plugin directory" % llf)
            continue
        name = layerapi2_label_file_to_plugin_name(llf)
        directory = os.path.join(plugins_base_dir, directory_name)
        if os.path.islink(directory):
            result.append({'name': name,
                           'version': 'dev_link',
                           'release': 'dev_link',
                           'home': directory})
    return result


def uninstall_plugin(name, plugins_base_dir=None,
                     ignore_errors=False, quiet=False):
    _assert_plugins_base_initialized(plugins_base_dir)
    plugins_base_dir = _get_plugins_base_dir(plugins_base_dir)
    infos = get_plugin_info(name, mode="name",
                            plugins_base_dir=plugins_base_dir)
    if infos is None:
        raise MFUtilPluginNotInstalled("plugin %s is not installed" % name)
    version = infos['metadatas']['version']
    release = infos['metadatas']['release']
    home = infos.get('home', None)
    if release == 'dev_link':
        preuninstall_status = _preuninstall_plugin(name, version, release,
                                                   quiet=quiet)
        if not preuninstall_status and not ignore_errors:
            raise MFUtilPluginCantUninstall("can't uninstall plugin %s" % name)
        if home:
            os.unlink(home)
        return
    preuninstall_status = _preuninstall_plugin(name, version, release)
    if not preuninstall_status and not ignore_errors:
        raise MFUtilPluginCantUninstall("can't uninstall plugin %s" % name)
    cmd = _get_rpm_cmd('-e --noscripts %s' % name,
                       plugins_base_dir=plugins_base_dir, add_prefix=False)
    try:
        x = BashWrapperOrRaise(cmd, MFUtilPluginCantUninstall,
                               "can't uninstall %s" % name)
    except MFUtilPluginCantUninstall:
        if not ignore_errors:
            raise
    if home:
        shutil.rmtree(home, ignore_errors=True)
    infos = get_plugin_info(name, mode="name",
                            plugins_base_dir=plugins_base_dir)
    if infos is not None:
        raise MFUtilPluginCantUninstall("can't uninstall plugin %s" % name,
                                        bash_wrapper=x)
    if home and os.path.exists(home):
        raise MFUtilPluginCantUninstall("can't uninstall plugin %s "
                                        "(directory still here)" % name)


def _postinstall_plugin(name, version, release, quiet=False):
    res = BashWrapper("_plugins.postinstall %s %s %s" %
                      (name, version, release))
    if not res:
        if not quiet:
            __get_logger().warning("error during postinstall: %s", res)
        return False
    return True


def _preuninstall_plugin(name, version, release, quiet=False):
    res = BashWrapper("_plugins.preuninstall %s %s %s" %
                      (name, version, release))
    if not res:
        if not quiet:
            __get_logger().warning("error during postuninstall: %s", res)
        return False
    return True


def install_plugin(plugin_filepath, plugins_base_dir=None,
                   ignore_errors=False, quiet=False):
    _assert_plugins_base_initialized(plugins_base_dir)
    if not os.path.isfile(plugin_filepath):
        raise MFUtilPluginFileNotFound("plugin file %s not found" %
                                       plugin_filepath)
    infos = get_plugin_info(plugin_filepath, mode="file",
                            plugins_base_dir=plugins_base_dir)
    if infos is None:
        raise MFUtilPluginInvalid("invalid %s plugin" % plugin_filepath)
    name = infos['metadatas']['name']
    version = infos['metadatas']['version']
    release = infos['metadatas']['release']
    installed_infos = get_plugin_info(name, mode="name",
                                      plugins_base_dir=plugins_base_dir)
    if installed_infos is not None:
        raise MFUtilPluginAlreadyInstalled("plugin %s already installed" %
                                           name)
    cmd = _get_rpm_cmd('-Uvh --noscripts --force %s' % plugin_filepath,
                       plugins_base_dir=plugins_base_dir, add_prefix=True)
    x = BashWrapperOrRaise(cmd, MFUtilPluginCantInstall,
                           "can't install plugin %s" % name)
    infos = get_plugin_info(name, mode="name",
                            plugins_base_dir=plugins_base_dir)
    if infos is None:
        raise MFUtilPluginCantInstall("can't install plugin %s" % name,
                                      bash_wrapper=x)
    postinstall_status = _postinstall_plugin(name, version, release,
                                             quiet=quiet)
    if not postinstall_status and not ignore_errors:
        try:
            uninstall_plugin(name, plugins_base_dir, True, True)
        except Exception:
            pass


def _make_plugin_spec(dest_file, name, version, summary, license, packager,
                      vendor, url):
    with open(SPEC_TEMPLATE, "r") as f:
        template = f.read()
    extra_vars = {"NAME": name, "VERSION": version, "SUMMARY": summary,
                  "LICENSE": license, "PACKAGER": packager, "VENDOR": vendor,
                  "URL": url}
    res = envtpl.render_string(template, extra_variables=extra_vars)
    # because, you can have some template inside extra vars
    res = envtpl.render_string(res)
    with open(dest_file, "w") as f:
        f.write(res)


def develop_plugin(plugin_path, name, plugins_base_dir=None,
                   ignore_errors=False, quiet=False):
    plugin_path = os.path.abspath(plugin_path)
    plugins_base_dir = _get_plugins_base_dir(plugins_base_dir)
    shutil.rmtree(os.path.join(plugins_base_dir, name), True)
    try:
        os.symlink(plugin_path, os.path.join(plugins_base_dir, name))
    except OSError:
        if not quiet:
            __get_logger().warning(
                "plugin '%s' already installed as a symlink", name)
    postinstall_status = _postinstall_plugin(name, "dev_link", "dev_link",
                                             quiet=quiet)
    if not postinstall_status and not ignore_errors:
        try:
            uninstall_plugin(name, plugins_base_dir, True, True)
        except Exception:
            pass


def _is_dev_link_plugin(name, plugins_base_dir=None):
    home = get_layer_home_from_plugin_name(name)
    if home is None:
        return False
    plugins_base_dir = _get_plugins_base_dir(plugins_base_dir)
    return os.path.islink(home)


def build_plugin(plugin_path, plugins_base_dir=None):
    plugin_path = os.path.abspath(plugin_path)
    plugins_base_dir = _get_plugins_base_dir(plugins_base_dir)
    base = os.path.join(plugins_base_dir, "base")
    pwd = os.getcwd()
    parser = ExtendedConfigParser(config=os.environ.get('MFCONFIG', 'GENERIC'),
                                  strict=False, inheritance="im")
    with open(os.path.join(plugin_path, "config.ini"), "r") as f:
        config_content = f.read()
    if six.PY2:
        parser.read_string(config_content.decode('utf-8'))
    else:
        parser.read_string(config_content)
    name = parser['general']['name']
    version = parser['general']['version']
    summary = parser['general']['summary']
    license = parser['general']['license']
    try:
        packager = parser['general']['packager']
    except Exception:
        packager = parser['general']['maintainer']
    vendor = parser['general']['vendor']
    url = parser['general']['url']
    tmpdir = os.path.join(RUNTIME_HOME, "tmp",
                          "plugin_%s" % get_unique_hexa_identifier())
    mkdir_p_or_die(os.path.join(tmpdir, "BUILD"))
    mkdir_p_or_die(os.path.join(tmpdir, "RPMS"))
    mkdir_p_or_die(os.path.join(tmpdir, "SRPMS"))
    _make_plugin_spec(os.path.join(tmpdir, "specfile.spec"), name, version,
                      summary, license, packager, vendor, url)
    cmd = "source %s/lib/bash_utils.sh ; " % MFEXT_HOME
    cmd = cmd + "layer_load rpm@mfext ; "
    cmd = cmd + 'rpmbuild --define "_topdir %s" --define "pwd %s" ' \
        '--define "prefix %s" --dbpath %s ' \
        '-bb %s/specfile.spec' % (tmpdir, plugin_path, tmpdir,
                                  base, tmpdir)
    x = BashWrapperOrRaise(cmd, MFUtilPluginCantBuild,
                           "can't build plugin %s" % plugin_path)
    tmp = glob.glob(os.path.join(tmpdir, "RPMS", "x86_64", "*.rpm"))
    if len(tmp) == 0:
        raise MFUtilPluginCantBuild("can't find generated plugin" %
                                    plugin_path, bash_wrapper=x)
    plugin_path = tmp[0]
    new_basename = \
        os.path.basename(plugin_path).replace("x86_64.rpm",
                                              "metwork.%s.plugin" %
                                              MODULE_LOWERCASE)
    new_plugin_path = os.path.join(pwd, new_basename)
    shutil.move(plugin_path, new_plugin_path)
    shutil.rmtree(tmpdir, True)
    os.chdir(pwd)
    return new_plugin_path


def get_plugin_info(name_or_filepath, mode="auto", plugins_base_dir=None):
    plugins_base_dir = _get_plugins_base_dir(plugins_base_dir)
    _assert_plugins_base_initialized(plugins_base_dir)
    res = {}
    if mode == "auto":
        mode = "name"
        if '/' in name_or_filepath or '.' in name_or_filepath:
            mode = "file"
        else:
            if os.path.isfile(name_or_filepath):
                mode = "file"
    if mode == "file":
        cmd = _get_rpm_cmd('-qi', '-p %s' % name_or_filepath,
                           plugins_base_dir=plugins_base_dir)
    elif mode == "name":
        if _is_dev_link_plugin(name_or_filepath,
                               plugins_base_dir=plugins_base_dir):
            res['metadatas'] = {}
            res['metadatas']['name'] = name_or_filepath
            res['metadatas']['release'] = 'dev_link'
            res['metadatas']['version'] = 'dev_link'
            res['raw_metadata_output'] = 'DEV LINK'
            res['raw_files_output'] = 'DEV LINK'
            res['files'] = []
            res['home'] = get_layer_home_from_plugin_name(name_or_filepath)
            return res
        cmd = _get_rpm_cmd('-qi', name_or_filepath,
                           plugins_base_dir=plugins_base_dir)
    else:
        __get_logger().warning("unknown mode [%s]" % mode)
        return None
    metadata_output = BashWrapper(cmd)
    if not metadata_output:
        return None
    res['raw_metadata_output'] = metadata_output.stdout
    for line in metadata_output.stdout.split('\n'):
        tmp = line.strip().split(':', 1)
        if len(tmp) <= 1:
            continue
        name = tmp[0].strip().lower()
        value = tmp[1].strip()
        if 'metadatas' not in res:
            res['metadatas'] = {}
        res['metadatas'][name] = value
    if mode == "name":
        res["home"] = \
            get_layer_home_from_plugin_name(name_or_filepath)
    if mode == "file":
        cmd = _get_rpm_cmd('-ql -p %s' % name_or_filepath,
                           plugins_base_dir=plugins_base_dir)
    else:
        cmd = _get_rpm_cmd('-ql %s' % name_or_filepath,
                           plugins_base_dir=plugins_base_dir)
    files_output = BashWrapper(cmd)
    if not files_output:
        return None
    res['files'] = [x.strip() for x in files_output.stdout.split('\n')]
    res['raw_files_output'] = files_output.stdout
    return res


def get_plugin_hash(name_or_filepath, mode="auto", plugins_base_dir=None):
    infos = get_plugin_info(name_or_filepath, mode=mode,
                            plugins_base_dir=plugins_base_dir)
    if infos is None:
        return None
    sid = ", ".join([infos['metadatas'].get('build host', 'unknown'),
                     infos['metadatas'].get('build date', 'unknown'),
                     infos['metadatas'].get('size', 'unknown'),
                     infos['metadatas'].get('version', 'unknown'),
                     infos['metadatas'].get('release', 'unknown')])
    return hashlib.md5(sid.encode('utf8')).hexdigest()
