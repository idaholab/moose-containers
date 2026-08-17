# moose-base files

Files used by `docker/base` containers.

## `install_oras.bash`

Installs oras.

### Usage

```
/bin/bash install_oras.bash <oras version> <installation directory>
```

### Used in

- `docker/base/rocky8`
- `docker/base/rocky8-cuda`
- `docker/base/rocky9`
- `docker/base/ubuntu24`
- `docker/base/ubuntu24-cuda`

## `rocky_base.bash`

Performs updates for a base rocky image and installs the base requirements.

Will make sure that the passed in rocky version is the same as the OS version.

### Usage

```
/bin/bash rocky_base.bash <rocky version>
```

### Used in

- `docker/base/rocky8`
- `docker/base/rocky8-cuda`
- `docker/base/rocky9`

## `rocky8_python.bash`

Installs a newer python for use in rocky8 containers, along with basic python dependencies for the MOOSE versioner script.

### Usage

```
/bin/bash rocky8_python.bash
```

### Used in

- `docker/base/rocky8`
- `docker/base/rocky8-cuda`

## `ubuntu_base.bash`

Performs updates for a base ubuntu image and installs the base requirements and python wth the python dependencies for the MOOSE versioner script.

### Usage

```
/bin/bash ubuntu_base.bash
```

### Used in

- `docker/base/ubuntu24`
- `docker/base/ubuntu24-cuda`
