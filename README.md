This repository contains the version-controlled definitions for the static base container images used in builds for [idaholab/moose](https://github.com/idaholab/moose).

## Apptainer containers

The following contains the list of container definitions that are tracked.

### moose-base/rocky-x86_64

The base image for all containers. Rocky linux with basic dependencies (python, git, vim, oras, apptainer).

### moose-hpcbase/rocky-x86_64

Base image for containers that are intended to be ran on INL HPC.

Based on `moose-base/rocky-x86_64` and adds:

- A modern compiler (currently GCC 12)
- A MPICH build to `/opt/mpich`
- An OpenMPI build to `/opt/openmpi`

### moose-hpcbase/rocky-cuda-x86_64

Base image for containers that include cuda and MPI-aware cuda.

Based on `moose-base/rocky-x86_64` and adds:

- A modern compiler (currently GCC 12)
- CUDA
- A MPICH build (cuda aware) to `/opt/mpich`
- An OpenMPI build (cuda aware) to `/opt/openmpi`
