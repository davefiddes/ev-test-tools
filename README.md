# EV Test Tools

[![Build status](../../actions/workflows/test.yml/badge.svg)](../../actions/workflows/test.yml)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ev-test-tools)
![PyPI - License](https://img.shields.io/pypi/l/ev-test-tools)

This project contains a series of desktop test tools that can be used to simulate
components used in electric vehicle conversion projects. The purpose is to allow easier
testing of integration between mass manufactured OEM components and open source projects
such as [openinverter](https://github.com/jsphuebner/stm32-sine) and
[ZombieVerter VCU](https://github.com/damienmaguire/Stm32-vcu).

## Simulators

* sbox-sim - Simulate the [BMW SBox](https://github.com/damienmaguire/BMW_SBox) including battery and contactors

## WARNING

This code is intended for low-voltage desktop use.

If this software is connected to high-voltage EV components it may be possible to cause physical damage to them, bypass safety interlocks and potentially hurt the user and anyone in the immediate vicinity.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

## Thanks

Thank you to [Angus Gratton](https://github.com/projectgus/car_hacking/) for his bench_kona project which provided the starting point for these tools.
