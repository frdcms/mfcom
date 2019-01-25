# How to install/upgrade/remove mfcom metwork package (with internet access)

[//]: # (automatically generated from https://github.com/metwork-framework/resources/blob/master/cookiecutter/_%7B%7Bcookiecutter.repo%7D%7D/.metwork-framework/install_a_metwork_package.md)

## Prerequisites

You must:

- have configured the metwork yum repository. Please see [the corresponding document](configure_metwork_repo.md) document to do that.
- have an internet access on this computer

## Install mfcom metwork package

## Full installation

You just have to execute the following command (as `root` user):

```
yum install metwork-mfcom
```

## Minimal installation

If you prefer to start with a minimal installation, you have to execute the following command
(as `root` user):

```
yum install metwork-mfcom-minimal
```

## Addons

### Dependencies addons

```
# To install some devtools
yum install metwork-mfext-devtools

# To install some scientific libraries
yum install metwork-mfext-scientific

# To install python2 support
# (including corresponding scientific and devtools addons)
yum install metwork-mfext-python2
```







## Uninstall mfcom metwork package


To uninstall mfcom metwork package, use the following command (still as `root` user):



```
yum remove "metwork-mfcom*"
```

## Upgrade mfcom metwork package

To upgrade mfcom metwork package, use the following commands (still as `root` user):



```
# We upgrade mfcom metwork package
yum upgrade "metwork-mfcom*"
```



## Uninstall all metwork packages

To uninstall all metwork packages, use following root commands:

```
# We stop metwork services
service metwork stop

# we remove metwork packages
yum remove "metwork-*"
```

## Upgrade all metwork packages

The same idea applies to upgrade.

For example, to upgrade all metwork packages on a computer, use following root commands:

```
# We stop metwork services
service metwork stop

# We upgrade metwork packages
yum upgrade "metwork-*"

# We start metwork services
service metwork start
```
