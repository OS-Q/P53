import copy
import platform

from platformio.managers.platform import PlatformBase


class P53Platform(PlatformBase):

    def is_embedded(self):
        return True

    def configure_default_packages(self, variables, targets):
        if variables.get("board"):
            upload_protocol = variables.get("upload_protocol",
                                            self.board_config(
                                                variables.get("board")).get(
                                                    "upload.protocol", ""))
            if upload_protocol == "cmsis-dap":
                self.packages["tool-pyocd"]["type"] = "uploader"

        # configure J-LINK tool
        jlink_conds = [
            "jlink" in variables.get(option, "")
            for option in ("upload_protocol", "debug_tool")
        ]
        if variables.get("board"):
            board_config = self.board_config(variables.get("board"))
            jlink_conds.extend([
                "jlink" in board_config.get(key, "")
                for key in ("debug.default_tools", "upload.protocol")
            ])
        jlink_pkgname = "tool-jlink"
        if not any(jlink_conds) and jlink_pkgname in self.packages:
            del self.packages[jlink_pkgname]

        return PlatformBase.configure_default_packages(self, variables,
                                                        targets)

    def get_boards(self, id_=None):
        result = PlatformBase.get_boards(self, id_)
        if not result:
            return result
        if id_:
            return self._add_default_debug_tools(result)
        else:
            for key, value in result.items():
                result[key] = self._add_default_debug_tools(result[key])
        return result

    def _add_default_debug_tools(self, board):
        debug = board.manifest.get("debug", {})
        upload_protocols = board.manifest.get("upload", {}).get(
            "protocols", [])
        if "tools" not in debug:
            debug["tools"] = {}

        # J-Link Probe
        if "jlink" in upload_protocols:
            assert debug.get("jlink_device"), (
                "Missed J-Link Device ID for %s" % board.id)
            debug["tools"]["jlink"] = {
                "server": {
                    "package": "tool-jlink",
                    "arguments": [
                        "-singlerun",
                        "-if", "SWD",
                        "-select", "USB",
                        "-device", debug.get("jlink_device"),
                        "-port", "2331"
                    ],
                    "executable": ("JLinkGDBServerCL.exe"
                                    if platform.system() == "Windows" else
                                    "JLinkGDBServer")
                }
            }

        board.manifest["debug"] = debug
        return board

    def configure_debug_options(self, initial_debug_options, ide_data):
        debug_options = copy.deepcopy(initial_debug_options)
        server_executable = debug_options["server"]["executable"].lower()
        adapter_speed = initial_debug_options.get("speed")
        if adapter_speed:
            if "jlink" in server_executable:
                debug_options["server"]["arguments"].extend(
                    ["-speed", adapter_speed]
                )
            elif "pyocd" in debug_options["server"]["package"]:
                assert (
                    adapter_speed.isdigit()
                ), "pyOCD requires the debug frequency value in Hz, e.g. 4000"
                debug_options["server"]["arguments"].extend(
                    ["--frequency", "%d" % int(adapter_speed)]
                )

        return debug_options
