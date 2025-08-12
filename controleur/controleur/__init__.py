# coding=utf-8
from __future__ import absolute_import
import RPi.GPIO as GPIO
import time

#TODO Disconnect the printer BEFORE tunring it off for cleaner disconnect

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.

import octoprint.plugin


def setupGPIO():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(18, GPIO.OUT, initial=GPIO.LOW)  # ON
    GPIO.setup(23, GPIO.OUT, initial=GPIO.LOW)  # OFF
    GPIO.setup(24, GPIO.IN)                     # STATE


class ControleurPlugin(octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.SimpleApiPlugin,
    octoprint.plugin.BlueprintPlugin
):

    def __init__(self):
        self.printer_state = False  # False = Off, True = On
        setupGPIO()

    def toggle_hardware_switch(self):
        if GPIO.input(24) == 1:
            self._logger.info("Printer hardware turned OFF")
            GPIO.output(23, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(23, GPIO.LOW)
        else:
            self._logger.info("Printer hardware turned ON")
            GPIO.output(18, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(18, GPIO.LOW)
        self.printer_state = GPIO.input(24)

    def on_startup(self,*args):
        self._logger.warning("HELLO WORLD THIS IS MY PLUGIN ALERET BOMB")
    ##~~ SettingsPlugin mixin

    def get_additional_ui_data(self):
        return {
            "notifications": [
                {
                    "type": "warning",  # "info", "success", "warning", "error"
                    "title": "Controleur Plugin",
                    "text": "Something needs your attention.",
                    "dismissable": True,  # User can close it
                    "id": "controleur_warning"  # Unique ID for persistence
                }
            ]
        }


    def get_settings_defaults(self):
        return {
            # put your plugin's default settings here
        }

    ##~~ AssetPlugin mixin

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return {
            "js": ["js/controleur.js"],
            "css": ["css/controleur.css"]
        }

    ##~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "controleur": {
                "displayName": "Controleur Plugin",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "Oscar_T24",
                "repo": "controleur",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/Oscar_T24/controleur/archive/{target_version}.zip",
            }
        }

    ## API routes for frontend
    def get_api_commands(self):
        """
        All API endpoints need to be declared here otherwise octoprint will return a HTTP 400 / Bad request

        """
        return dict(
            toggle=[],
            get_state=[],
            connect_printer = [],
            finalize_off=[]
        )

    def on_api_command(self, command, data):
        if command == "toggle":
            # Current temp and state
            self.printer_state = GPIO.input(24)
            operational = self._printer.is_operational()
            temps = self._printer.get_current_temperatures()
            temp_ok = 'tool0' in temps and temps['tool0']['actual'] < 50.0

            if GPIO.input(24) == 1:
                if operational and temp_ok:
                    # Tell frontend to disconnect first
                    return {
                        "success": True,
                        "disconnect": True,
                        "state": self.printer_state,
                        "message": "Printer will be turned off after disconnect."
                    }
                else:
                    return {
                        "success": False,
                        "state": self.printer_state,
                        "message": "Cannot turn off: Printer not operational or temp too high."
                    }

            elif GPIO.input(24) == 0:  # Printer OFF → turning ON
                self.toggle_hardware_switch()
                self._logger.info("Printer power toggled ON")
                return {
                    "success": True,
                    "disconnect": False,
                    "state": self.printer_state,
                    "message": "Printer turned ON."
                }
            else :
                return {
                    "success": False,
                    "state": self.printer_state,
                    "message": "Cannot turn off: Printer's connection to octoprint could not be determined."
                }

        if command == "finalize_off":
            # Actually turn off the printer now
            self.toggle_hardware_switch()
            self._logger.info("Printer power toggled OFF")
            return {
                "success": True,
                "state": self.printer_state,
                "message": "Printer turned OFF."
            }

        if command == "get_state":
            self.printer_state = GPIO.input(24)
            return dict(state=self.printer_state)

    # to add a visual tab next to Control / Temperature etc #
    def get_template_configs(self):
        return [
            dict(type="navbar", name="Controleur", template="controleur_navbar.jinja2"),
            dict(
                type="tab",
                name="Controleur Console",
                template="controleur_tab.jinja2",
                custom_bindings=False,
                order=2  # Control has order=2, GCODE Viewer has order=3
            )
        ]

    ## Templates
    def get_template_vars(self):
        return {}

    def get_blueprints(self):
        from flask import Blueprint, jsonify, request

        blueprint = Blueprint(
            "controleur",
            __name__,
            url_prefix="/plugin/controleur"
        )

        @blueprint.route("/connect", methods=["POST"])
        def connect():
            # Trigger connection logic here on backend
            # Example: call your GPIO toggle or OctoPrint connection methods
            return jsonify(result="Connect endpoint hit")

        return [blueprint]
# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Controleur Plugin"


# Set the Python version your plugin is compatible with below. Recommended is Python 3 only for all new plugins.
# OctoPrint 1.4.0 - 1.7.x run under both Python 3 and the end-of-life Python 2.
# OctoPrint 1.8.0 onwards only supports Python 3.
__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = ControleurPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
