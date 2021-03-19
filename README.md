This project is a a fork from the original 'The Network Simulator, Version 3', NS-3 (https://www.nsnam.org).

It implements the required mechanisms for dynamic multiplex Wi-Fi transmissions.


## Running the simulation

After building the project (run the script 'build.sh'), type the following command from the ns-3.32 directory

```shell
./waf --run "test-uvigo --channelWidth=<BW> --wifiOnTime=<T_Wi-Fi> --laaOnTime=<T_LAA>"
```

for computing the Wi-Fi network capacity under the DTM approach. Change <BW>, <T_Wi-Fi> and <T_LAA> with the appropiate values.

In order to run the DFM simulation, run

```shell
./waf --run "test-uvigo --channelWidth=<BW> --doNotMultiplex=true"
```

setting <BW> to the channel width allocated for Wi-Fi operation.


## Computing the analytical results

The analytical scripts are located in 'analytical model'.

### Coexistence model

```shell
python3 tput_coexistence.py <N_Wi-Fi> <N_LAA> <BW> <A-MPDU_EXPONENT> <PAYLOAD_SIZE> <LAA_TX_CLASS>
```

### Wi-Fi model

```shell
python3 tput_wifi.py <N_Wi-Fi> <BW> <A-MPDU_EXPONENT> <PAYLOAD_SIZE> [<T_Wi-Fi>]
```

<T_Wi-Fi> defaults to ∞.


### LAA model

```shell
python3 tput_laa.py <N_LAA> <BW> <LAA_TX_CLASS> [<T_LAA>]
```

<T_LAA> defaults to ∞.




The Network Simulator, Version 3
================================

## Table of Contents:

1) [An overview](#an-open-source-project)
2) [Building ns-3](#building-ns-3)
3) [Running ns-3](#running-ns-3)
4) [Getting access to the ns-3 documentation](#getting-access-to-the-ns-3-documentation)
5) [Working with the development version of ns-3](#working-with-the-development-version-of-ns-3)

Note:  Much more substantial information about ns-3 can be found at
https://www.nsnam.org

## An Open Source project

ns-3 is a free open source project aiming to build a discrete-event
network simulator targeted for simulation research and education.
This is a collaborative project; we hope that
the missing pieces of the models we have not yet implemented
will be contributed by the community in an open collaboration
process.

The process of contributing to the ns-3 project varies with
the people involved, the amount of time they can invest
and the type of model they want to work on, but the current
process that the project tries to follow is described here:
https://www.nsnam.org/developers/contributing-code/

This README excerpts some details from a more extensive
tutorial that is maintained at:
https://www.nsnam.org/documentation/latest/

## Building ns-3

Run the script 'build.sh' to isntall the prerrequisites and build the project.

## Running ns-3

On recent Linux systems, once you have built ns-3 (with examples
enabled), it should be easy to run the sample programs with the
following command, such as:

```shell
./waf --run simple-global-routing
```

That program should generate a `simple-global-routing.tr` text
trace file and a set of `simple-global-routing-xx-xx.pcap` binary
pcap trace files, which can be read by `tcpdump -tt -r filename.pcap`
The program source can be found in the examples/routing directory.

## Getting access to the ns-3 documentation

Once you have verified that your build of ns-3 works by running
the simple-point-to-point example as outlined in 3) above, it is
quite likely that you will want to get started on reading
some ns-3 documentation.

All of that documentation should always be available from
the ns-3 website: https://www.nsnam.org/documentation/.

This documentation includes:

  - a tutorial

  - a reference manual

  - models in the ns-3 model library

  - a wiki for user-contributed tips: https://www.nsnam.org/wiki/

  - API documentation generated using doxygen: this is
    a reference manual, most likely not very well suited
    as introductory text:
    https://www.nsnam.org/doxygen/index.html

## Working with the development version of ns-3

If you want to download and use the development version of ns-3, you
need to use the tool `git`. A quick and dirty cheat sheet is included
in the manual, but reading through the git
tutorials found in the Internet is usually a good idea if you are not
familiar with it.

If you have successfully installed git, you can get
a copy of the development version with the following command:
```shell
git clone https://gitlab.com/nsnam/ns-3-dev.git
```

However, we recommend to follow the Gitlab guidelines for starters,
that includes creating a Gitlab account, forking the ns-3-dev project
under the new account's name, and then cloning the forked repository.
You can find more information in the [manual](https://www.nsnam.org/docs/manual/html/working-with-git.html).
