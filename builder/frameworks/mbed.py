from os.path import join

from SCons.Script import Import, SConscript

Import("env")

SConscript(
    join(env.PioPlatform().get_package_dir("mbed5"), "platformio",
        "platformio-build.py"))
